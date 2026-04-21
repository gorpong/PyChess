"""HTTP endpoints for networked multiplayer matches.

Routes in this blueprint are deliberately transport-thin: they collect
cookie-based player identity, delegate every write to `MatchService`,
translate the resulting exceptions into HTTP responses, and render a
board view from the calling seat's perspective.

Real-time updates (move push to the opponent without polling) are
layered on top by the Socket.IO namespace; these routes remain the
non-WebSocket fallback and the way pages are initially rendered.
"""

from __future__ import annotations

import secrets
from typing import Optional

from flask import (
    Blueprint,
    abort,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from pychess.match import (
    IllegalMatchMove,
    Match,
    MatchFull,
    MatchNotActive,
    MatchNotFound,
    MatchService,
    MatchStatus,
    NotInMatch,
    NotYourTurn,
    PromotionPending,
    SeatChoice,
)
from pychess.model.piece import Color, Piece
from pychess.model.square import Square
from pychess.rules.move import Move
from pychess.web.serializers import board_to_template_data, format_move_history

bp = Blueprint("match", __name__, url_prefix="/match")

_PLAYER_COOKIE_KEY = "pychess_player_id"

_PROMOTION_PIECES = {
    "Q": Piece.QUEEN,
    "R": Piece.ROOK,
    "B": Piece.BISHOP,
    "N": Piece.KNIGHT,
}


# -------------------- helpers --------------------


def _current_player_id() -> str:
    """Return a stable player id for this browser; create on first hit."""
    pid = session.get(_PLAYER_COOKIE_KEY)
    if not pid:
        pid = secrets.token_urlsafe(24)
        session[_PLAYER_COOKIE_KEY] = pid
        session.permanent = True
    return pid


def _service() -> MatchService:
    """Fetch the app-wide match service; raises if the app wasn't configured."""
    svc = getattr(current_app, "match_service", None)
    if svc is None:
        raise RuntimeError("MatchService is not configured on this app")
    return svc


def _render_match(match: Match, viewer_seat: Optional[Color]) -> str:
    """Render the match page from the caller's perspective.

    Callers are expected to have already verified that `viewer_seat` is not
    None; a missing seat means this browser is not one of the two players.
    """
    rows = board_to_template_data(match.game_state.board)
    if viewer_seat == Color.BLACK:
        # Show the board from Black's side.
        rows = [list(reversed(row)) for row in reversed(rows)]

    return render_template(
        "match/play.html",
        match=match,
        rows=rows,
        viewer_seat=viewer_seat.value if viewer_seat else None,
        to_move=match.game_state.active_color.value,
        is_your_turn=(
            viewer_seat is not None
            and match.game_state.active_color == viewer_seat
        ),
        move_pairs=format_move_history(match.game_state.move_history),
        can_resign=(
            viewer_seat is not None
            and match.status in (MatchStatus.WAITING, MatchStatus.ACTIVE)
        ),
    )


# -------------------- creation --------------------


@bp.get("/")
def index():
    """Landing page — Create new game or Join with invite code."""
    _current_player_id()
    return render_template("match/index.html")


@bp.post("/join")
def join_by_code():
    """Entry point for the landing-page join form: posts a code, we redirect."""
    code = (request.form.get("invite_code") or "").strip().upper()
    if not code:
        flash("Please enter an invite code", "error")
        return redirect(url_for("match.index"))
    return redirect(url_for("match.join_form", invite_code=code))


@bp.get("/new")
def new_form():
    _current_player_id()  # ensure the cookie exists before the form posts back
    return render_template("match/new.html")


@bp.post("/new")
def new_submit():
    player_id = _current_player_id()
    choice_raw = (request.form.get("seat") or "random").lower()
    try:
        seat_choice = SeatChoice(choice_raw)
    except ValueError:
        flash("Invalid seat choice", "error")
        return redirect(url_for("match.new_form"))

    match = _service().create_match(player_id, seat_choice)
    return redirect(url_for("match.play", match_id=match.match_id))


# -------------------- joining --------------------


@bp.get("/join/<invite_code>")
def join_form(invite_code: str):
    player_id = _current_player_id()
    try:
        match = _service().get_by_invite(invite_code)
    except MatchNotFound:
        abort(404, description="No match for that invite code")

    if match.status == MatchStatus.ACTIVE or match.is_full():
        if match.seat_of(player_id) is None:
            abort(403, description="This match already has two players")
        # Seated players can still use the invite URL as a rejoin shortcut.
        return redirect(url_for("match.play", match_id=match.match_id))

    return render_template("match/join.html", match=match, invite_code=invite_code)


@bp.post("/join/<invite_code>")
def join_submit(invite_code: str):
    player_id = _current_player_id()
    svc = _service()
    try:
        match = svc.join(invite_code, player_id)
    except MatchNotFound:
        abort(404, description="No match for that invite code")
    except MatchFull:
        flash("This match already has two players", "error")
        return redirect(url_for("match.join_form", invite_code=invite_code))

    return redirect(url_for("match.play", match_id=match.match_id))


# -------------------- play --------------------


@bp.get("/<match_id>")
def play(match_id: str):
    player_id = _current_player_id()
    try:
        match = _service().get_match(match_id)
    except MatchNotFound:
        abort(404, description="No such match")

    viewer_seat = match.seat_of(player_id)
    if viewer_seat is None:
        abort(403, description="You are not seated in this match")

    return _render_match(match, viewer_seat)


@bp.post("/<match_id>/move")
def submit_move(match_id: str):
    """Non-WebSocket move submission.

    Expects `from`, `to`, and optionally `promotion` (piece letter) in the
    form body. Move authorization is centralized in `MatchService`; this
    view only translates exceptions into HTTP redirects with flash messages.
    """
    player_id = _current_player_id()
    svc = _service()

    try:
        frm = Square.from_algebraic(request.form["from"])
        to = Square.from_algebraic(request.form["to"])
    except (KeyError, ValueError):
        flash("Invalid squares", "error")
        return redirect(url_for("match.play", match_id=match_id))

    promotion_letter = request.form.get("promotion")
    promotion = _PROMOTION_PIECES.get(promotion_letter.upper()) if promotion_letter else None
    move = Move(from_square=frm, to_square=to, promotion=promotion)

    try:
        updated = svc.submit_move(match_id, player_id, move)
    except MatchNotFound:
        abort(404)
    except NotInMatch:
        abort(403, description="You're not in this match")
    except MatchNotActive:
        flash("Match is not active", "error")
    except NotYourTurn:
        flash("It's not your turn", "error")
    except PromotionPending:
        flash("Promotion required — include a piece choice and submit again", "error")
    except IllegalMatchMove as exc:
        flash(exc.reason, "error")
    else:
        # Keep any WebSocket-connected peers in sync with REST-only players.
        _broadcast_move_if_socketio(updated)

    return redirect(url_for("match.play", match_id=match_id))


def _broadcast_move_if_socketio(match: Match) -> None:
    """Fire a `move_applied` Socket.IO event when the app has a SocketIO attached.

    Installed on the Flask app by `create_app`; guarded so standalone uses
    of the match blueprint (without Socket.IO) stay functional.
    """
    socketio = getattr(current_app, "socketio", None)
    if socketio is None:
        return
    from pychess.web.match_socketio import broadcast_move
    broadcast_move(socketio, match)


@bp.post("/<match_id>/resign")
def resign(match_id: str):
    player_id = _current_player_id()
    svc = _service()
    try:
        result = svc.resign(match_id, player_id)
    except MatchNotFound:
        abort(404)
    except NotInMatch:
        abort(403, description="You're not in this match")
    except MatchNotActive:
        flash("Match is already finished", "error")
        return redirect(url_for("match.play", match_id=match_id))

    if result is None:
        # Match deleted (resigned before opponent joined).
        return redirect(url_for("match.new_form"))
    return redirect(url_for("match.play", match_id=match_id))
