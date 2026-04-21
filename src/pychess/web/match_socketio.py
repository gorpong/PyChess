"""Socket.IO namespace for real-time match updates.

Each connected client joins the Socket.IO room named by the match id; all
move broadcasts target that room. The HTTP fallback (`match_routes`) also
emits into the same rooms after a successful REST move, so clients that
use the form submission stay in sync with WebSocket-native peers.

Auth is piggy-backed on the Flask session cookie: the `pychess_player_id`
set by the `/match` routes doubles as the Socket.IO identity. Sockets
presenting no cookie are rejected at connect time.
"""

from __future__ import annotations

from typing import Optional

from flask import current_app, request, session
from flask_socketio import SocketIO, emit, join_room, rooms

from pychess.match import (
    IllegalMatchMove,
    Match,
    MatchNotActive,
    MatchNotFound,
    MatchService,
    NotInMatch,
    NotYourTurn,
    PromotionPending,
)
from pychess.model.piece import Color, Piece
from pychess.model.square import Square
from pychess.rules.move import Move

NAMESPACE = "/match"

_PLAYER_COOKIE_KEY = "pychess_player_id"
_PROMOTION_PIECES = {
    "Q": Piece.QUEEN,
    "R": Piece.ROOK,
    "B": Piece.BISHOP,
    "N": Piece.KNIGHT,
}


# -------------------- payloads --------------------


def state_payload(match: Match, viewer_player_id: Optional[str]) -> dict:
    """Serialize a match for transport to a specific viewer.

    The viewer's seat is included so the client can orient the board and
    decide whether to render the move form. Seat occupancy is exposed only as
    booleans; the clients never need each other's opaque player ids.
    """
    seat = match.seat_of(viewer_player_id) if viewer_player_id else None
    return {
        "match_id": match.match_id,
        "status": match.status.value,
        "result": match.result,
        "turn": match.game_state.active_color.value,
        "your_seat": seat.value if seat else None,
        "seats": {
            "white": match.white_player_id is not None,
            "black": match.black_player_id is not None,
        },
        "move_history": list(match.game_state.move_history),
        "pending_promotion": (
            None
            if match.pending_promotion is None
            else {
                "from": _square_str(match.pending_promotion.from_square),
                "to": _square_str(match.pending_promotion.to_square),
            }
        ),
    }


def _square_str(sq: Square) -> str:
    return f"{sq.file}{sq.rank}"


# -------------------- registration --------------------


def register(socketio: SocketIO) -> None:
    """Attach match-namespace handlers to the shared SocketIO instance.

    Kept as a registration function rather than a `Namespace` subclass so
    tests can mount handlers on a freshly-built SocketIO per app without
    wrestling with class-level state.
    """

    @socketio.on("connect", namespace=NAMESPACE)
    def _on_connect(auth=None):
        player_id = session.get(_PLAYER_COOKIE_KEY)
        match_id = request.args.get("match_id")
        if not player_id or not match_id:
            # Refuse the connection: no identity or no target match.
            return False

        try:
            match = _service().get_match(match_id)
        except MatchNotFound:
            return False
        if match.seat_of(player_id) is None:
            return False

        join_room(match_id)
        emit("match_state", state_payload(match, player_id))
        emit(
            "opponent_connected",
            {},
            to=match_id,
            skip_sid=request.sid,
        )

    @socketio.on("disconnect", namespace=NAMESPACE)
    def _on_disconnect(reason=None):
        # `rooms()` in the disconnect handler still reflects membership;
        # the match_id room is everything except the sid-named default.
        for room in rooms():
            if room == request.sid:
                continue
            emit(
                "opponent_disconnected",
                {},
                to=room,
                skip_sid=request.sid,
                namespace=NAMESPACE,
            )

    @socketio.on("request_state", namespace=NAMESPACE)
    def _on_request_state(data=None):
        player_id = session.get(_PLAYER_COOKIE_KEY)
        match_id = (data or {}).get("match_id") or request.args.get("match_id")
        if not player_id or not match_id:
            emit("error", {"code": "unauthenticated", "message": "No session"})
            return
        try:
            match = _service().get_match(match_id)
        except MatchNotFound:
            emit("error", {"code": "not_found", "message": "Match not found"})
            return
        if match.seat_of(player_id) is None:
            emit("error", {"code": "forbidden", "message": "You are not in this match"})
            return
        emit("match_state", state_payload(match, player_id))

    @socketio.on("submit_move", namespace=NAMESPACE)
    def _on_submit_move(data):
        player_id = session.get(_PLAYER_COOKIE_KEY)
        match_id = (data or {}).get("match_id") or request.args.get("match_id")
        if not player_id or not match_id:
            emit("error", {"code": "unauthenticated", "message": "No session"})
            return

        try:
            frm = Square.from_algebraic(data["from"])
            to = Square.from_algebraic(data["to"])
        except (KeyError, TypeError, ValueError):
            emit("error", {"code": "bad_move", "message": "Invalid squares"})
            return

        promo_letter = (data or {}).get("promotion")
        promotion = _PROMOTION_PIECES.get(promo_letter.upper()) if promo_letter else None
        move = Move(from_square=frm, to_square=to, promotion=promotion)

        svc = _service()
        try:
            match = svc.submit_move(match_id, player_id, move)
        except MatchNotFound:
            emit("error", {"code": "not_found", "message": "Match not found"})
            return
        except NotInMatch:
            emit("error", {"code": "forbidden", "message": "You are not in this match"})
            return
        except NotYourTurn:
            emit("error", {"code": "not_your_turn", "message": "It is not your turn"})
            return
        except MatchNotActive:
            emit("error", {"code": "not_active", "message": "Match is not active"})
            return
        except PromotionPending:
            # Only the mover needs to know; the opponent will get the full
            # state once the piece is chosen.
            refreshed = svc.get_match(match_id)
            emit(
                "promotion_required",
                {
                    "from": data["from"],
                    "to": data["to"],
                },
            )
            emit("match_state", state_payload(refreshed, player_id))
            return
        except IllegalMatchMove as exc:
            emit("error", {"code": "illegal_move", "message": exc.reason})
            return

        # Success — push the new state to everyone in the room.
        broadcast_move(socketio, match)

    @socketio.on("resign", namespace=NAMESPACE)
    def _on_resign(data):
        player_id = session.get(_PLAYER_COOKIE_KEY)
        match_id = (data or {}).get("match_id") or request.args.get("match_id")
        svc = _service()
        try:
            result = svc.resign(match_id, player_id)
        except MatchNotFound:
            emit("error", {"code": "not_found", "message": "Match not found"})
            return
        except NotInMatch:
            emit("error", {"code": "forbidden", "message": "You are not in this match"})
            return
        except MatchNotActive:
            emit("error", {"code": "not_active", "message": "Match is not active"})
            return

        if result is None:
            # Match was deleted outright (resign while still waiting).
            emit("match_deleted", {"match_id": match_id}, to=match_id)
        else:
            broadcast_move(socketio, result)


# -------------------- public helpers --------------------


def broadcast_move(socketio: SocketIO, match: Match) -> None:
    """Broadcast a post-move snapshot to every viewer in the match's room.

    Sends `match_state` to each joined socket (with their own seat view)
    via one `emit` per connection would be ideal, but Flask-SocketIO's
    rooms don't expose per-member state. We emit a single viewer-agnostic
    `move_applied` event and let each client issue `request_state` if they
    want their seat-specific view refreshed. The most recent SAN plus
    game-over result cover the common case.
    """
    latest_san = match.game_state.move_history[-1] if match.game_state.move_history else None
    socketio.emit(
        "move_applied",
        {
            "match_id": match.match_id,
            "san": latest_san,
            "turn": match.game_state.active_color.value,
            "status": match.status.value,
            "result": match.result,
        },
        to=match.match_id,
        namespace=NAMESPACE,
    )


# -------------------- internals --------------------


def _service() -> MatchService:
    svc = getattr(current_app, "match_service", None)
    if svc is None:
        raise RuntimeError("MatchService is not configured on this app")
    return svc
