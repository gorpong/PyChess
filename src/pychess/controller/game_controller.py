"""UI-agnostic game controller.

`GameController` is the single place where rule-application logic lives for
PyChess. Both the terminal `GameSession` and the web `GameManager` delegate
move validation, SAN parsing, promotion handling, and game-end detection here.

The controller is pure with respect to I/O. It does not know about
terminals, HTTP, cookies, or browser sessions. Callers pass in a
`GameState` and a move intent; the controller returns a `MoveOutcome`
describing what happened. This is what lets `MatchService` enforce the
exact same move semantics that the local CLI and web UI apply.
"""

from dataclasses import dataclass
from typing import Optional

from pychess.model.game_state import GameState
from pychess.model.piece import Piece
from pychess.model.square import Square
from pychess.notation.pgn import _apply_san_move
from pychess.notation.san import move_to_san, san_to_move
from pychess.rules.game_logic import get_game_result
from pychess.rules.move import Move
from pychess.rules.validator import get_legal_moves


@dataclass(frozen=True)
class MoveApplied:
    """A move was successfully applied to a game state."""

    move: Move
    san: str
    new_state: GameState


@dataclass(frozen=True)
class PromotionRequired:
    """The from/to pair resolves to multiple promotion candidates.

    The caller must choose a promotion piece and retry via
    `GameController.apply_from_to(..., promotion=<Piece>)`.
    """

    from_square: Square
    to_square: Square
    candidate_moves: tuple[Move, ...]


@dataclass(frozen=True)
class IllegalMove:
    """The requested move was rejected. Contains a human-readable reason."""

    reason: str


@dataclass(frozen=True)
class GameOver:
    """The game ended after the most recent move."""

    result: str  # '1-0' | '0-1' | '1/2-1/2'


@dataclass(frozen=True)
class MoveOutcome:
    """Result of a controller call.

    Exactly one of `applied`, `promotion_required`, or `illegal` is set.
    `game_over` is populated in addition to `applied` when the move ends the game.
    `state` is the current authoritative state: the new state after a successful
    move, or the unchanged input state for illegal / promotion-pending outcomes.
    """

    state: GameState
    applied: Optional[MoveApplied] = None
    promotion_required: Optional[PromotionRequired] = None
    illegal: Optional[IllegalMove] = None
    game_over: Optional[GameOver] = None

    @property
    def ok(self) -> bool:
        return self.applied is not None


class GameController:
    """Pure rule-application orchestrator for PyChess.

    Shared by the terminal `GameSession`, the web `GameManager`, and (in later
    phases) the server-side `MatchService`. Holds no state of its own.
    """

    def apply_move(self, state: GameState, move: Move) -> MoveOutcome:
        """Apply a fully-specified `Move` (including promotion piece if any).

        The move is validated against the full legal-move generator, not just
        a king-safety check. This is strict enough for untrusted input (the
        networked server will call this path with data from remote clients).
        """
        if not self._is_fully_legal(state, move):
            return MoveOutcome(state=state, illegal=IllegalMove(f"Illegal move: {move}"))
        san = move_to_san(state, move)
        new_state = _apply_san_move(state, san, move)
        applied = MoveApplied(move=move, san=san, new_state=new_state)
        result = get_game_result(new_state)
        if result:
            return MoveOutcome(state=new_state, applied=applied, game_over=GameOver(result))
        return MoveOutcome(state=new_state, applied=applied)

    def apply_from_to(
        self,
        state: GameState,
        from_square: Square,
        to_square: Square,
        promotion: Optional[Piece] = None,
    ) -> MoveOutcome:
        """Apply a move given its source and destination squares.

        If the square pair is a legal pawn promotion, the controller returns
        `PromotionRequired` when `promotion` is not supplied, so the caller can
        prompt the user and call again with the chosen piece.
        """
        legal = get_legal_moves(state)
        matching = [
            m for m in legal if m.from_square == from_square and m.to_square == to_square
        ]
        if not matching:
            return MoveOutcome(state=state, illegal=IllegalMove("Illegal move"))

        is_promotion = len(matching) > 1 and all(m.promotion is not None for m in matching)
        if is_promotion:
            if promotion is None:
                return MoveOutcome(
                    state=state,
                    promotion_required=PromotionRequired(
                        from_square=from_square,
                        to_square=to_square,
                        candidate_moves=tuple(matching),
                    ),
                )
            chosen = next((m for m in matching if m.promotion == promotion), None)
            if chosen is None:
                return MoveOutcome(
                    state=state, illegal=IllegalMove("Invalid promotion piece")
                )
            return self.apply_move(state, chosen)

        return self.apply_move(state, matching[0])

    def apply_san(self, state: GameState, san_text: str) -> MoveOutcome:
        """Apply a move parsed from SAN text (e.g. "e4", "Nf3", "O-O", "e8=Q")."""
        try:
            move = san_to_move(state, san_text)
        except ValueError as e:
            return MoveOutcome(state=state, illegal=IllegalMove(str(e)))
        return self.apply_move(state, move)

    def legal_destinations(self, state: GameState, from_square: Square) -> set[Square]:
        """Destination squares for any legal move from `from_square` in `state`."""
        return {
            m.to_square for m in get_legal_moves(state) if m.from_square == from_square
        }

    def detect_end(self, state: GameState) -> Optional[GameOver]:
        """Return `GameOver` if the game has ended in `state`, else None."""
        result = get_game_result(state)
        return GameOver(result) if result else None

    @staticmethod
    def _is_fully_legal(state: GameState, move: Move) -> bool:
        """True iff `move` is among the generated legal moves for `state`.

        Matches on from/to/promotion. Other `Move` flags (is_capture,
        is_en_passant, is_castling) are derived by the generator, so we
        deliberately don't require the caller to set them correctly.
        """
        for legal in get_legal_moves(state):
            if (
                legal.from_square == move.from_square
                and legal.to_square == move.to_square
                and legal.promotion == move.promotion
            ):
                return True
        return False
