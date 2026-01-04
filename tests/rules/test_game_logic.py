"""Tests for game end conditions (checkmate, stalemate, draws)."""

import pytest

from pychess.model.board import Board
from pychess.model.game_state import GameState, CastlingRights
from pychess.model.piece import Piece, Color
from pychess.model.square import Square
from pychess.rules.game_logic import (
    is_checkmate,
    is_stalemate,
    is_fifty_move_rule,
    is_threefold_repetition,
    is_insufficient_material,
    get_game_result,
)


class TestIsCheckmate:
    """Tests for checkmate detection."""

    def test_initial_position_not_checkmate(self):
        """Initial position is not checkmate."""
        state = GameState.initial()
        assert not is_checkmate(state)

    def test_fools_mate(self):
        """Fool's mate - fastest possible checkmate (2 moves)."""
        # After 1. f3 e5 2. g4 Qh4#
        board = (Board.empty()
                 # White pieces
                 .set(Square.from_algebraic("a1"), Piece.ROOK, Color.WHITE)
                 .set(Square.from_algebraic("b1"), Piece.KNIGHT, Color.WHITE)
                 .set(Square.from_algebraic("c1"), Piece.BISHOP, Color.WHITE)
                 .set(Square.from_algebraic("d1"), Piece.QUEEN, Color.WHITE)
                 .set(Square.from_algebraic("e1"), Piece.KING, Color.WHITE)
                 .set(Square.from_algebraic("f1"), Piece.BISHOP, Color.WHITE)
                 .set(Square.from_algebraic("g1"), Piece.KNIGHT, Color.WHITE)
                 .set(Square.from_algebraic("h1"), Piece.ROOK, Color.WHITE)
                 .set(Square.from_algebraic("a2"), Piece.PAWN, Color.WHITE)
                 .set(Square.from_algebraic("b2"), Piece.PAWN, Color.WHITE)
                 .set(Square.from_algebraic("c2"), Piece.PAWN, Color.WHITE)
                 .set(Square.from_algebraic("d2"), Piece.PAWN, Color.WHITE)
                 .set(Square.from_algebraic("e2"), Piece.PAWN, Color.WHITE)
                 .set(Square.from_algebraic("f3"), Piece.PAWN, Color.WHITE)  # f2-f3
                 .set(Square.from_algebraic("g4"), Piece.PAWN, Color.WHITE)  # g2-g4
                 .set(Square.from_algebraic("h2"), Piece.PAWN, Color.WHITE)
                 # Black pieces
                 .set(Square.from_algebraic("a8"), Piece.ROOK, Color.BLACK)
                 .set(Square.from_algebraic("b8"), Piece.KNIGHT, Color.BLACK)
                 .set(Square.from_algebraic("c8"), Piece.BISHOP, Color.BLACK)
                 .set(Square.from_algebraic("d8"), Piece.QUEEN, Color.BLACK)  # Queen moved
                 .set(Square.from_algebraic("e8"), Piece.KING, Color.BLACK)
                 .set(Square.from_algebraic("f8"), Piece.BISHOP, Color.BLACK)
                 .set(Square.from_algebraic("g8"), Piece.KNIGHT, Color.BLACK)
                 .set(Square.from_algebraic("h8"), Piece.ROOK, Color.BLACK)
                 .set(Square.from_algebraic("a7"), Piece.PAWN, Color.BLACK)
                 .set(Square.from_algebraic("b7"), Piece.PAWN, Color.BLACK)
                 .set(Square.from_algebraic("c7"), Piece.PAWN, Color.BLACK)
                 .set(Square.from_algebraic("d7"), Piece.PAWN, Color.BLACK)
                 .set(Square.from_algebraic("e5"), Piece.PAWN, Color.BLACK)  # e7-e5
                 .set(Square.from_algebraic("f7"), Piece.PAWN, Color.BLACK)
                 .set(Square.from_algebraic("g7"), Piece.PAWN, Color.BLACK)
                 .set(Square.from_algebraic("h7"), Piece.PAWN, Color.BLACK)
                 .set(Square.from_algebraic("h4"), Piece.QUEEN, Color.BLACK))  # Qd8-h4#

        # Remove queen from d8, it's on h4
        board = board.remove(Square.from_algebraic("d8"))

        state = GameState.initial().with_board(board)
        assert is_checkmate(state)

    def test_scholars_mate(self):
        """Scholar's mate pattern - queen delivers mate supported by bishop."""
        # Classic scholar's mate position
        # Queen on f7 gives check, bishop on c4 supports, king trapped
        board = (Board.empty()
                 .set(Square.from_algebraic("e8"), Piece.KING, Color.BLACK)
                 .set(Square.from_algebraic("f7"), Piece.QUEEN, Color.WHITE)
                 .set(Square.from_algebraic("c4"), Piece.BISHOP, Color.WHITE)
                 .set(Square.from_algebraic("e1"), Piece.KING, Color.WHITE)
                 # Black pieces blocking king's escape
                 .set(Square.from_algebraic("d8"), Piece.QUEEN, Color.BLACK)  # Blocks d8
                 .set(Square.from_algebraic("d7"), Piece.PAWN, Color.BLACK)   # Blocks d7
                 .set(Square.from_algebraic("e7"), Piece.PAWN, Color.BLACK)   # Blocks e7
                 .set(Square.from_algebraic("f8"), Piece.BISHOP, Color.BLACK)) # Blocks f8

        state = GameState.initial().with_board(board).with_turn(Color.BLACK)
        assert is_checkmate(state)

    def test_back_rank_mate(self):
        """Back rank mate - rook delivers checkmate on 8th rank."""
        board = (Board.empty()
                 .set(Square.from_algebraic("e8"), Piece.KING, Color.BLACK)
                 .set(Square.from_algebraic("f8"), Piece.ROOK, Color.BLACK)
                 .set(Square.from_algebraic("g8"), Piece.ROOK, Color.BLACK)
                 .set(Square.from_algebraic("d7"), Piece.PAWN, Color.BLACK)
                 .set(Square.from_algebraic("e7"), Piece.PAWN, Color.BLACK)
                 .set(Square.from_algebraic("f7"), Piece.PAWN, Color.BLACK)
                 .set(Square.from_algebraic("a8"), Piece.ROOK, Color.WHITE)  # Delivers mate
                 .set(Square.from_algebraic("e1"), Piece.KING, Color.WHITE))

        state = GameState.initial().with_board(board).with_turn(Color.BLACK)
        assert is_checkmate(state)

    def test_smothered_mate(self):
        """Smothered mate - knight checkmates king surrounded by own pieces."""
        board = (Board.empty()
                 .set(Square.from_algebraic("h8"), Piece.KING, Color.BLACK)
                 .set(Square.from_algebraic("g8"), Piece.ROOK, Color.BLACK)
                 .set(Square.from_algebraic("h7"), Piece.PAWN, Color.BLACK)
                 .set(Square.from_algebraic("g7"), Piece.PAWN, Color.BLACK)
                 .set(Square.from_algebraic("f7"), Piece.KNIGHT, Color.WHITE)  # Delivers mate
                 .set(Square.from_algebraic("e1"), Piece.KING, Color.WHITE))

        state = GameState.initial().with_board(board).with_turn(Color.BLACK)
        assert is_checkmate(state)

    def test_not_checkmate_can_block(self):
        """Not checkmate if check can be blocked."""
        board = (Board.empty()
                 .set(Square.from_algebraic("e1"), Piece.KING, Color.WHITE)
                 .set(Square.from_algebraic("e8"), Piece.ROOK, Color.BLACK)
                 .set(Square.from_algebraic("d2"), Piece.BISHOP, Color.WHITE)  # Can block on e3
                 .set(Square.from_algebraic("a8"), Piece.KING, Color.BLACK))

        state = GameState.initial().with_board(board)
        assert not is_checkmate(state)

    def test_not_checkmate_can_capture(self):
        """Not checkmate if checking piece can be captured."""
        board = (Board.empty()
                 .set(Square.from_algebraic("e1"), Piece.KING, Color.WHITE)
                 .set(Square.from_algebraic("e2"), Piece.KNIGHT, Color.BLACK)  # Giving check
                 .set(Square.from_algebraic("d1"), Piece.QUEEN, Color.WHITE)  # Can capture knight
                 .set(Square.from_algebraic("a8"), Piece.KING, Color.BLACK))

        state = GameState.initial().with_board(board)
        assert not is_checkmate(state)


class TestIsStalemate:
    """Tests for stalemate detection."""

    def test_initial_position_not_stalemate(self):
        """Initial position is not stalemate."""
        state = GameState.initial()
        assert not is_stalemate(state)

    def test_basic_stalemate(self):
        """Basic stalemate - king has no legal moves but not in check."""
        board = (Board.empty()
                 .set(Square.from_algebraic("a8"), Piece.KING, Color.BLACK)
                 .set(Square.from_algebraic("b6"), Piece.QUEEN, Color.WHITE)
                 .set(Square.from_algebraic("c7"), Piece.KING, Color.WHITE))

        state = GameState.initial().with_board(board).with_turn(Color.BLACK)
        assert is_stalemate(state)

    def test_stalemate_king_in_corner(self):
        """Stalemate with king trapped in corner."""
        board = (Board.empty()
                 .set(Square.from_algebraic("h8"), Piece.KING, Color.BLACK)
                 .set(Square.from_algebraic("f7"), Piece.QUEEN, Color.WHITE)
                 .set(Square.from_algebraic("g6"), Piece.KING, Color.WHITE))

        state = GameState.initial().with_board(board).with_turn(Color.BLACK)
        assert is_stalemate(state)

    def test_stalemate_with_blocked_pawn(self):
        """Stalemate where side has pawn but it's blocked."""
        # Classic stalemate: King in corner, pawn blocked
        # Black king on a8, black pawn on a7 blocked by white pawn on a6
        # White queen and king control all escape squares
        board = (Board.empty()
                 .set(Square.from_algebraic("a8"), Piece.KING, Color.BLACK)
                 .set(Square.from_algebraic("a7"), Piece.PAWN, Color.BLACK)  # Blocked
                 .set(Square.from_algebraic("a6"), Piece.PAWN, Color.WHITE)  # Blocking
                 .set(Square.from_algebraic("c8"), Piece.KING, Color.WHITE)  # Controls b8, b7
                 .set(Square.from_algebraic("b5"), Piece.QUEEN, Color.WHITE))  # Controls b7, b8

        state = GameState.initial().with_board(board).with_turn(Color.BLACK)
        assert is_stalemate(state)

    def test_not_stalemate_when_in_check(self):
        """Not stalemate when in check (would be checkmate)."""
        board = (Board.empty()
                 .set(Square.from_algebraic("a8"), Piece.KING, Color.BLACK)
                 .set(Square.from_algebraic("a1"), Piece.ROOK, Color.WHITE)  # Giving check
                 .set(Square.from_algebraic("b6"), Piece.QUEEN, Color.WHITE)
                 .set(Square.from_algebraic("c7"), Piece.KING, Color.WHITE))

        state = GameState.initial().with_board(board).with_turn(Color.BLACK)
        assert not is_stalemate(state)  # This is checkmate, not stalemate


class TestIsFiftyMoveRule:
    """Tests for 50-move rule detection."""

    def test_initial_position_not_fifty_moves(self):
        """Initial position has no moves played."""
        state = GameState.initial()
        assert not is_fifty_move_rule(state)

    def test_halfmove_clock_99_not_draw(self):
        """Halfmove clock at 99 is not yet a draw."""
        state = GameState.initial().with_halfmove_clock(99)
        assert not is_fifty_move_rule(state)

    def test_halfmove_clock_100_is_draw(self):
        """Halfmove clock at 100 (50 full moves) triggers draw."""
        state = GameState.initial().with_halfmove_clock(100)
        assert is_fifty_move_rule(state)

    def test_halfmove_clock_above_100(self):
        """Halfmove clock above 100 also triggers draw."""
        state = GameState.initial().with_halfmove_clock(150)
        assert is_fifty_move_rule(state)


class TestIsThreefoldRepetition:
    """Tests for threefold repetition detection."""

    def test_initial_position_no_repetition(self):
        """Initial position has no repetition."""
        state = GameState.initial()
        assert not is_threefold_repetition(state)

    def test_position_repeated_twice_not_draw(self):
        """Position repeated twice is not yet a draw."""
        state = GameState.initial()
        # Add position to history twice
        state = state.with_position_hash_added(state.position_hash)
        assert not is_threefold_repetition(state)

    def test_position_repeated_three_times_is_draw(self):
        """Position repeated three times is a draw."""
        state = GameState.initial()
        # Add position to history three times (including current)
        state = state.with_position_hash_added(state.position_hash)
        state = state.with_position_hash_added(state.position_hash)
        assert is_threefold_repetition(state)

    def test_different_positions_no_repetition(self):
        """Different positions don't count as repetition."""
        state1 = GameState.initial()
        # Make a move to get different position
        board2 = state1.board.remove(Square.from_algebraic("e2")).set(
            Square.from_algebraic("e4"), Piece.PAWN, Color.WHITE
        )
        state2 = state1.with_board(board2)

        # Add some hashes but not repeating
        state = state1.with_position_hash_added(state1.position_hash)
        state = state.with_position_hash_added(state2.position_hash)
        assert not is_threefold_repetition(state)


class TestIsInsufficientMaterial:
    """Tests for insufficient material detection."""

    def test_initial_position_sufficient_material(self):
        """Initial position has sufficient material."""
        board = Board.initial()
        assert not is_insufficient_material(board)

    def test_king_vs_king(self):
        """K vs K is insufficient material."""
        board = (Board.empty()
                 .set(Square.from_algebraic("e1"), Piece.KING, Color.WHITE)
                 .set(Square.from_algebraic("e8"), Piece.KING, Color.BLACK))
        assert is_insufficient_material(board)

    def test_king_bishop_vs_king(self):
        """K+B vs K is insufficient material."""
        board = (Board.empty()
                 .set(Square.from_algebraic("e1"), Piece.KING, Color.WHITE)
                 .set(Square.from_algebraic("c1"), Piece.BISHOP, Color.WHITE)
                 .set(Square.from_algebraic("e8"), Piece.KING, Color.BLACK))
        assert is_insufficient_material(board)

    def test_king_knight_vs_king(self):
        """K+N vs K is insufficient material."""
        board = (Board.empty()
                 .set(Square.from_algebraic("e1"), Piece.KING, Color.WHITE)
                 .set(Square.from_algebraic("b1"), Piece.KNIGHT, Color.WHITE)
                 .set(Square.from_algebraic("e8"), Piece.KING, Color.BLACK))
        assert is_insufficient_material(board)

    def test_king_bishop_vs_king_bishop_same_color(self):
        """K+B vs K+B with same color bishops is insufficient material."""
        # Both bishops on light squares
        board = (Board.empty()
                 .set(Square.from_algebraic("e1"), Piece.KING, Color.WHITE)
                 .set(Square.from_algebraic("c1"), Piece.BISHOP, Color.WHITE)  # Dark square
                 .set(Square.from_algebraic("e8"), Piece.KING, Color.BLACK)
                 .set(Square.from_algebraic("f8"), Piece.BISHOP, Color.BLACK))  # Dark square
        assert is_insufficient_material(board)

    def test_king_bishop_vs_king_bishop_different_color(self):
        """K+B vs K+B with different color bishops has sufficient material."""
        # Bishops on different colored squares
        board = (Board.empty()
                 .set(Square.from_algebraic("e1"), Piece.KING, Color.WHITE)
                 .set(Square.from_algebraic("c1"), Piece.BISHOP, Color.WHITE)  # Dark square
                 .set(Square.from_algebraic("e8"), Piece.KING, Color.BLACK)
                 .set(Square.from_algebraic("c8"), Piece.BISHOP, Color.BLACK))  # Light square
        assert not is_insufficient_material(board)

    def test_king_rook_vs_king_sufficient(self):
        """K+R vs K has sufficient material (can checkmate)."""
        board = (Board.empty()
                 .set(Square.from_algebraic("e1"), Piece.KING, Color.WHITE)
                 .set(Square.from_algebraic("a1"), Piece.ROOK, Color.WHITE)
                 .set(Square.from_algebraic("e8"), Piece.KING, Color.BLACK))
        assert not is_insufficient_material(board)

    def test_king_queen_vs_king_sufficient(self):
        """K+Q vs K has sufficient material."""
        board = (Board.empty()
                 .set(Square.from_algebraic("e1"), Piece.KING, Color.WHITE)
                 .set(Square.from_algebraic("d1"), Piece.QUEEN, Color.WHITE)
                 .set(Square.from_algebraic("e8"), Piece.KING, Color.BLACK))
        assert not is_insufficient_material(board)

    def test_king_pawn_vs_king_sufficient(self):
        """K+P vs K has sufficient material (pawn can promote)."""
        board = (Board.empty()
                 .set(Square.from_algebraic("e1"), Piece.KING, Color.WHITE)
                 .set(Square.from_algebraic("e2"), Piece.PAWN, Color.WHITE)
                 .set(Square.from_algebraic("e8"), Piece.KING, Color.BLACK))
        assert not is_insufficient_material(board)

    def test_king_two_knights_vs_king_sufficient(self):
        """K+N+N vs K has sufficient material (can force mate in some positions)."""
        board = (Board.empty()
                 .set(Square.from_algebraic("e1"), Piece.KING, Color.WHITE)
                 .set(Square.from_algebraic("b1"), Piece.KNIGHT, Color.WHITE)
                 .set(Square.from_algebraic("g1"), Piece.KNIGHT, Color.WHITE)
                 .set(Square.from_algebraic("e8"), Piece.KING, Color.BLACK))
        # Note: K+N+N vs K cannot force checkmate, but by strict FIDE rules
        # it's not automatic insufficient material (mate is possible with help)
        # For simplicity, we'll consider it sufficient material
        assert not is_insufficient_material(board)


class TestGetGameResult:
    """Tests for game result determination."""

    def test_initial_position_ongoing(self):
        """Initial position is ongoing (no result)."""
        state = GameState.initial()
        assert get_game_result(state) is None

    def test_checkmate_white_wins(self):
        """Checkmate with black to move means white wins."""
        # Back rank mate position - black is checkmated
        board = (Board.empty()
                 .set(Square.from_algebraic("e8"), Piece.KING, Color.BLACK)
                 .set(Square.from_algebraic("f8"), Piece.ROOK, Color.BLACK)
                 .set(Square.from_algebraic("g8"), Piece.ROOK, Color.BLACK)
                 .set(Square.from_algebraic("d7"), Piece.PAWN, Color.BLACK)
                 .set(Square.from_algebraic("e7"), Piece.PAWN, Color.BLACK)
                 .set(Square.from_algebraic("f7"), Piece.PAWN, Color.BLACK)
                 .set(Square.from_algebraic("a8"), Piece.ROOK, Color.WHITE)
                 .set(Square.from_algebraic("e1"), Piece.KING, Color.WHITE))

        state = GameState.initial().with_board(board).with_turn(Color.BLACK)
        assert get_game_result(state) == "1-0"

    def test_checkmate_black_wins(self):
        """Checkmate with white to move means black wins."""
        # Back rank mate on white
        board = (Board.empty()
                 .set(Square.from_algebraic("e1"), Piece.KING, Color.WHITE)
                 .set(Square.from_algebraic("f1"), Piece.ROOK, Color.WHITE)
                 .set(Square.from_algebraic("g1"), Piece.ROOK, Color.WHITE)
                 .set(Square.from_algebraic("d2"), Piece.PAWN, Color.WHITE)
                 .set(Square.from_algebraic("e2"), Piece.PAWN, Color.WHITE)
                 .set(Square.from_algebraic("f2"), Piece.PAWN, Color.WHITE)
                 .set(Square.from_algebraic("a1"), Piece.ROOK, Color.BLACK)
                 .set(Square.from_algebraic("e8"), Piece.KING, Color.BLACK))

        state = GameState.initial().with_board(board)
        assert get_game_result(state) == "0-1"

    def test_stalemate_is_draw(self):
        """Stalemate results in draw."""
        board = (Board.empty()
                 .set(Square.from_algebraic("a8"), Piece.KING, Color.BLACK)
                 .set(Square.from_algebraic("b6"), Piece.QUEEN, Color.WHITE)
                 .set(Square.from_algebraic("c7"), Piece.KING, Color.WHITE))

        state = GameState.initial().with_board(board).with_turn(Color.BLACK)
        assert get_game_result(state) == "1/2-1/2"

    def test_fifty_move_rule_is_draw(self):
        """Fifty-move rule results in draw."""
        state = GameState.initial().with_halfmove_clock(100)
        assert get_game_result(state) == "1/2-1/2"

    def test_insufficient_material_is_draw(self):
        """Insufficient material results in draw."""
        board = (Board.empty()
                 .set(Square.from_algebraic("e1"), Piece.KING, Color.WHITE)
                 .set(Square.from_algebraic("e8"), Piece.KING, Color.BLACK))
        state = GameState.initial().with_board(board)
        assert get_game_result(state) == "1/2-1/2"

    def test_threefold_repetition_is_draw(self):
        """Threefold repetition results in draw."""
        state = GameState.initial()
        state = state.with_position_hash_added(state.position_hash)
        state = state.with_position_hash_added(state.position_hash)
        assert get_game_result(state) == "1/2-1/2"


class TestPositionHash:
    """Tests for position hashing (required for threefold repetition)."""

    def test_initial_position_has_hash(self):
        """Initial position should have a hash."""
        state = GameState.initial()
        assert hasattr(state, 'position_hash')
        assert state.position_hash is not None

    def test_same_position_same_hash(self):
        """Same position should produce same hash."""
        state1 = GameState.initial()
        state2 = GameState.initial()
        assert state1.position_hash == state2.position_hash

    def test_different_board_different_hash(self):
        """Different board positions should have different hashes."""
        state1 = GameState.initial()
        board2 = state1.board.remove(Square.from_algebraic("e2")).set(
            Square.from_algebraic("e4"), Piece.PAWN, Color.WHITE
        )
        state2 = state1.with_board(board2)
        assert state1.position_hash != state2.position_hash

    def test_different_turn_different_hash(self):
        """Same board but different turn should have different hash."""
        state1 = GameState.initial()
        state2 = state1.with_turn(Color.BLACK)
        assert state1.position_hash != state2.position_hash

    def test_different_castling_rights_different_hash(self):
        """Different castling rights should produce different hash."""
        state1 = GameState.initial()
        castling = CastlingRights(
            white_kingside=False,
            white_queenside=True,
            black_kingside=True,
            black_queenside=True
        )
        state2 = state1.with_castling(castling)
        assert state1.position_hash != state2.position_hash

    def test_different_en_passant_different_hash(self):
        """Different en passant squares should produce different hash."""
        state1 = GameState.initial()
        state2 = state1.with_en_passant(Square.from_algebraic("e3"))
        assert state1.position_hash != state2.position_hash
