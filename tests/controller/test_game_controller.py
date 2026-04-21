"""Tests for the shared GameController.

These tests exercise the pure rule-application controller that the
terminal `GameSession`, the web `GameManager`, and `MatchService` all
delegate to. They do not re-test engine primitives (move generation,
checkmate detection) that are covered by `tests/rules/`; instead they
verify that `GameController` correctly *composes* those primitives into
the right `MoveOutcome` shapes.
"""

import pytest

from pychess.controller.game_controller import (
    GameController,
    GameOver,
    IllegalMove,
    MoveApplied,
    MoveOutcome,
    PromotionRequired,
)
from pychess.model.board import Board
from pychess.model.game_state import GameState
from pychess.model.piece import Color, Piece
from pychess.model.square import Square
from pychess.rules.move import Move


def sq(s: str) -> Square:
    return Square.from_algebraic(s)


def _kings_only_with(*placements) -> GameState:
    """Build a GameState with white king on e1, black king on a8, plus extras.

    placements: iterable of (algebraic, Piece, Color).
    """
    board = Board.empty()
    board = board.set(sq("e1"), Piece.KING, Color.WHITE)
    board = board.set(sq("a8"), Piece.KING, Color.BLACK)
    for alg, piece, color in placements:
        board = board.set(sq(alg), piece, color)
    return GameState.initial().with_board(board)


@pytest.fixture
def controller() -> GameController:
    return GameController()


@pytest.fixture
def initial() -> GameState:
    return GameState.initial()


# -------------------- apply_move --------------------


class TestApplyMove:
    def test_legal_move_returns_applied_outcome(self, controller, initial):
        move = Move(from_square=sq("e2"), to_square=sq("e4"))
        outcome = controller.apply_move(initial, move)

        assert outcome.ok
        assert outcome.illegal is None
        assert outcome.promotion_required is None
        assert outcome.game_over is None
        assert isinstance(outcome.applied, MoveApplied)
        assert outcome.applied.san == "e4"
        assert outcome.applied.move == move
        assert outcome.state is not initial  # new state
        assert outcome.applied.new_state is outcome.state

    def test_illegal_move_returns_illegal_outcome(self, controller, initial):
        bogus = Move(from_square=sq("e2"), to_square=sq("e5"))  # can't jump 3
        outcome = controller.apply_move(initial, bogus)

        assert not outcome.ok
        assert isinstance(outcome.illegal, IllegalMove)
        assert "Illegal move" in outcome.illegal.reason
        assert outcome.state is initial  # unchanged

    def test_move_ending_game_carries_game_over(self, controller):
        """Scholar's mate: Qxf7# should produce a GameOver with 1-0."""
        state = GameState.initial()
        # Play Scholar's mate manually via apply_move
        state = controller.apply_move(state, Move(sq("e2"), sq("e4"))).state
        state = controller.apply_move(state, Move(sq("e7"), sq("e5"))).state
        state = controller.apply_move(state, Move(sq("f1"), sq("c4"))).state
        state = controller.apply_move(state, Move(sq("b8"), sq("c6"))).state
        state = controller.apply_move(state, Move(sq("d1"), sq("h5"))).state
        state = controller.apply_move(state, Move(sq("g8"), sq("f6"))).state

        outcome = controller.apply_move(state, Move(sq("h5"), sq("f7"), is_capture=True))

        assert outcome.ok
        assert outcome.game_over is not None
        assert outcome.game_over.result == "1-0"


# -------------------- apply_from_to --------------------


class TestApplyFromTo:
    def test_legal_from_to_without_promotion(self, controller, initial):
        outcome = controller.apply_from_to(initial, sq("e2"), sq("e4"))

        assert outcome.ok
        assert outcome.applied.san == "e4"

    def test_no_matching_move_is_illegal(self, controller, initial):
        outcome = controller.apply_from_to(initial, sq("e2"), sq("e5"))

        assert outcome.illegal is not None
        assert outcome.applied is None
        assert outcome.state is initial

    def test_promotion_without_piece_returns_promotion_required(self, controller):
        state = _kings_only_with(("e7", Piece.PAWN, Color.WHITE))

        outcome = controller.apply_from_to(state, sq("e7"), sq("e8"))

        assert outcome.promotion_required is not None
        assert outcome.applied is None
        assert outcome.illegal is None
        assert outcome.state is state
        pr = outcome.promotion_required
        assert pr.from_square == sq("e7")
        assert pr.to_square == sq("e8")
        # There should be four candidate moves: Q, R, B, N
        promos = {m.promotion for m in pr.candidate_moves}
        assert promos == {Piece.QUEEN, Piece.ROOK, Piece.BISHOP, Piece.KNIGHT}

    def test_promotion_with_piece_applies_move(self, controller):
        state = _kings_only_with(("e7", Piece.PAWN, Color.WHITE))

        outcome = controller.apply_from_to(
            state, sq("e7"), sq("e8"), promotion=Piece.QUEEN
        )

        assert outcome.ok
        assert outcome.applied.move.promotion == Piece.QUEEN
        assert "=Q" in outcome.applied.san or outcome.applied.san.endswith("Q")

    def test_promotion_with_invalid_piece_is_illegal(self, controller):
        state = _kings_only_with(("e7", Piece.PAWN, Color.WHITE))

        outcome = controller.apply_from_to(
            state, sq("e7"), sq("e8"), promotion=Piece.KING
        )

        assert outcome.illegal is not None
        assert outcome.applied is None

    def test_promotion_with_underpromotion_applies_that_piece(self, controller):
        state = _kings_only_with(("e7", Piece.PAWN, Color.WHITE))

        outcome = controller.apply_from_to(
            state, sq("e7"), sq("e8"), promotion=Piece.KNIGHT
        )

        assert outcome.ok
        assert outcome.applied.move.promotion == Piece.KNIGHT


# -------------------- apply_san --------------------


class TestApplySan:
    def test_valid_san_applies_move(self, controller, initial):
        outcome = controller.apply_san(initial, "e4")

        assert outcome.ok
        assert outcome.applied.san == "e4"

    def test_malformed_san_is_illegal(self, controller, initial):
        outcome = controller.apply_san(initial, "notamove")

        assert outcome.illegal is not None
        assert outcome.state is initial

    def test_unparseable_promotion_san_is_illegal(self, controller, initial):
        # You can't promote from the initial position.
        outcome = controller.apply_san(initial, "e8=Q")

        assert outcome.illegal is not None

    def test_san_promotion_is_applied(self, controller):
        state = _kings_only_with(("e7", Piece.PAWN, Color.WHITE))

        outcome = controller.apply_san(state, "e8=Q")

        assert outcome.ok
        assert outcome.applied.move.promotion == Piece.QUEEN


# -------------------- legal_destinations --------------------


class TestLegalDestinations:
    def test_initial_pawn_has_two_destinations(self, controller, initial):
        dests = controller.legal_destinations(initial, sq("e2"))
        assert dests == {sq("e3"), sq("e4")}

    def test_empty_square_has_no_destinations(self, controller, initial):
        assert controller.legal_destinations(initial, sq("e4")) == set()

    def test_opponent_piece_has_no_destinations(self, controller, initial):
        # White to move; e7 is black's pawn.
        assert controller.legal_destinations(initial, sq("e7")) == set()


# -------------------- detect_end --------------------


class TestDetectEnd:
    def test_initial_position_is_not_ended(self, controller, initial):
        assert controller.detect_end(initial) is None

    def test_detects_checkmate(self, controller):
        """Fool's mate position."""
        state = GameState.initial()
        state = controller.apply_san(state, "f3").state
        state = controller.apply_san(state, "e5").state
        state = controller.apply_san(state, "g4").state
        state = controller.apply_san(state, "Qh4#").state

        end = controller.detect_end(state)
        assert isinstance(end, GameOver)
        assert end.result == "0-1"


# -------------------- MoveOutcome invariants --------------------


class TestOutcomeInvariants:
    def test_ok_property_only_true_for_applied(self, controller, initial):
        good = controller.apply_san(initial, "e4")
        bad = controller.apply_san(initial, "e5")
        pending = controller.apply_from_to(
            _kings_only_with(("e7", Piece.PAWN, Color.WHITE)), sq("e7"), sq("e8")
        )

        assert good.ok is True
        assert bad.ok is False
        assert pending.ok is False
