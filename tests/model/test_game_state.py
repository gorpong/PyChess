"""Tests for GameState dataclass."""

import pytest
from pychess.model.game_state import GameState, CastlingRights
from pychess.model.piece import Piece, Color
from pychess.model.square import Square
from pychess.model.board import Board


class TestCastlingRights:
    """Tests for CastlingRights dataclass."""

    def test_castling_rights_initial_all_true(self):
        """Initial castling rights are all True."""
        rights = CastlingRights.initial()
        assert rights.white_kingside is True
        assert rights.white_queenside is True
        assert rights.black_kingside is True
        assert rights.black_queenside is True

    def test_castling_rights_none(self):
        """Can create rights with all False."""
        rights = CastlingRights(
            white_kingside=False,
            white_queenside=False,
            black_kingside=False,
            black_queenside=False,
        )
        assert rights.white_kingside is False
        assert rights.white_queenside is False
        assert rights.black_kingside is False
        assert rights.black_queenside is False

    def test_castling_rights_immutable(self):
        """CastlingRights is immutable (frozen dataclass)."""
        rights = CastlingRights.initial()
        with pytest.raises(AttributeError):
            rights.white_kingside = False

    def test_castling_rights_can_castle_white_kingside(self):
        """can_castle returns True for white kingside when rights allow."""
        rights = CastlingRights.initial()
        assert rights.can_castle(Color.WHITE, kingside=True) is True

    def test_castling_rights_can_castle_white_queenside(self):
        """can_castle returns True for white queenside when rights allow."""
        rights = CastlingRights.initial()
        assert rights.can_castle(Color.WHITE, kingside=False) is True

    def test_castling_rights_can_castle_black_kingside(self):
        """can_castle returns True for black kingside when rights allow."""
        rights = CastlingRights.initial()
        assert rights.can_castle(Color.BLACK, kingside=True) is True

    def test_castling_rights_can_castle_black_queenside(self):
        """can_castle returns True for black queenside when rights allow."""
        rights = CastlingRights.initial()
        assert rights.can_castle(Color.BLACK, kingside=False) is True

    def test_castling_rights_revoke_white_kingside(self):
        """Can revoke white kingside castling."""
        rights = CastlingRights.initial()
        new_rights = rights.revoke(Color.WHITE, kingside=True)
        assert new_rights.white_kingside is False
        assert new_rights.white_queenside is True
        assert new_rights.black_kingside is True
        assert new_rights.black_queenside is True

    def test_castling_rights_revoke_returns_new_instance(self):
        """revoke() returns a new instance, original unchanged."""
        rights = CastlingRights.initial()
        new_rights = rights.revoke(Color.WHITE, kingside=True)
        assert rights.white_kingside is True
        assert new_rights.white_kingside is False

    def test_castling_rights_revoke_all_for_color(self):
        """Can revoke all castling for a color."""
        rights = CastlingRights.initial()
        new_rights = rights.revoke_all(Color.WHITE)
        assert new_rights.white_kingside is False
        assert new_rights.white_queenside is False
        assert new_rights.black_kingside is True
        assert new_rights.black_queenside is True


class TestGameStateInitial:
    """Tests for initial GameState."""

    def test_gamestate_initial_creates_state(self):
        """GameState.initial() creates a game state."""
        state = GameState.initial()
        assert state is not None

    def test_initial_board_is_initial_position(self):
        """Initial game state has initial board position."""
        state = GameState.initial()
        assert state.board.get(Square.from_algebraic("e1")) == (Piece.KING, Color.WHITE)
        assert state.board.get(Square.from_algebraic("e8")) == (Piece.KING, Color.BLACK)

    def test_initial_turn_is_white(self):
        """White moves first."""
        state = GameState.initial()
        assert state.turn == Color.WHITE

    def test_initial_castling_all_available(self):
        """All castling rights available initially."""
        state = GameState.initial()
        assert state.castling.white_kingside is True
        assert state.castling.white_queenside is True
        assert state.castling.black_kingside is True
        assert state.castling.black_queenside is True

    def test_initial_en_passant_is_none(self):
        """No en passant square initially."""
        state = GameState.initial()
        assert state.en_passant_square is None

    def test_initial_halfmove_clock_is_zero(self):
        """Halfmove clock starts at 0."""
        state = GameState.initial()
        assert state.halfmove_clock == 0

    def test_initial_fullmove_number_is_one(self):
        """Fullmove number starts at 1."""
        state = GameState.initial()
        assert state.fullmove_number == 1

    def test_initial_move_history_is_empty(self):
        """Move history starts empty."""
        state = GameState.initial()
        assert state.move_history == []


class TestGameStateImmutability:
    """Tests for GameState immutability."""

    def test_gamestate_is_immutable(self):
        """GameState is immutable (frozen dataclass)."""
        state = GameState.initial()
        with pytest.raises(AttributeError):
            state.turn = Color.BLACK


class TestGameStateWithMethods:
    """Tests for GameState modification methods."""

    def test_with_board(self):
        """with_board returns new state with different board."""
        state = GameState.initial()
        new_board = state.board.remove(Square.from_algebraic("e2"))
        new_state = state.with_board(new_board)
        assert new_state.board.get(Square.from_algebraic("e2")) is None
        assert state.board.get(Square.from_algebraic("e2")) is not None

    def test_with_turn(self):
        """with_turn returns new state with different turn."""
        state = GameState.initial()
        new_state = state.with_turn(Color.BLACK)
        assert new_state.turn == Color.BLACK
        assert state.turn == Color.WHITE

    def test_with_castling(self):
        """with_castling returns new state with different castling rights."""
        state = GameState.initial()
        new_castling = state.castling.revoke(Color.WHITE, kingside=True)
        new_state = state.with_castling(new_castling)
        assert new_state.castling.white_kingside is False
        assert state.castling.white_kingside is True

    def test_with_en_passant(self):
        """with_en_passant returns new state with en passant square."""
        state = GameState.initial()
        ep_square = Square.from_algebraic("e3")
        new_state = state.with_en_passant(ep_square)
        assert new_state.en_passant_square == ep_square
        assert state.en_passant_square is None

    def test_with_en_passant_none(self):
        """with_en_passant can clear en passant square."""
        state = GameState.initial()
        ep_square = Square.from_algebraic("e3")
        state_with_ep = state.with_en_passant(ep_square)
        state_cleared = state_with_ep.with_en_passant(None)
        assert state_cleared.en_passant_square is None

    def test_with_halfmove_clock(self):
        """with_halfmove_clock returns new state with different clock."""
        state = GameState.initial()
        new_state = state.with_halfmove_clock(5)
        assert new_state.halfmove_clock == 5
        assert state.halfmove_clock == 0

    def test_with_fullmove_number(self):
        """with_fullmove_number returns new state with different number."""
        state = GameState.initial()
        new_state = state.with_fullmove_number(10)
        assert new_state.fullmove_number == 10
        assert state.fullmove_number == 1

    def test_with_move_added(self):
        """with_move_added appends to move history."""
        state = GameState.initial()
        new_state = state.with_move_added("e4")
        assert new_state.move_history == ["e4"]
        assert state.move_history == []

    def test_with_move_added_preserves_previous(self):
        """with_move_added preserves previous moves."""
        state = GameState.initial()
        state = state.with_move_added("e4")
        state = state.with_move_added("e5")
        assert state.move_history == ["e4", "e5"]


class TestGameStateHelpers:
    """Tests for GameState helper methods."""

    def test_is_white_turn(self):
        """is_white_turn returns True when white to move."""
        state = GameState.initial()
        assert state.is_white_turn is True

    def test_is_black_turn(self):
        """is_white_turn returns False when black to move."""
        state = GameState.initial()
        state = state.with_turn(Color.BLACK)
        assert state.is_white_turn is False

    def test_active_color(self):
        """active_color returns current turn color."""
        state = GameState.initial()
        assert state.active_color == Color.WHITE
        state = state.with_turn(Color.BLACK)
        assert state.active_color == Color.BLACK

    def test_opponent_color(self):
        """opponent_color returns opposite of turn."""
        state = GameState.initial()
        assert state.opponent_color == Color.BLACK
        state = state.with_turn(Color.BLACK)
        assert state.opponent_color == Color.WHITE
