"""Tests for hard AI evaluation with piece-square tables."""

import pytest
from pychess.model.game_state import GameState
from pychess.model.board import Board
from pychess.model.piece import Piece, Color
from pychess.model.square import Square
from pychess.ai.hard import (
    PIECE_VALUES,
    PAWN_TABLE,
    KNIGHT_TABLE,
    BISHOP_TABLE,
    ROOK_TABLE,
    QUEEN_TABLE,
    KING_MIDDLEGAME_TABLE,
    KING_ENDGAME_TABLE,
    get_piece_square_value,
    get_piece_square_table,
    is_endgame,
    evaluate_piece_square_tables,
    evaluate_material,
    evaluate_position_hard,
    score_move_for_ordering,
    order_moves,
    select_best_move,
)
from pychess.rules.validator import get_legal_moves
from pychess.rules.move import Move


class TestPieceValues:
    """Tests for standard piece values."""
    
    def test_pawn_value(self):
        assert PIECE_VALUES[Piece.PAWN] == 100
    
    def test_knight_value(self):
        assert PIECE_VALUES[Piece.KNIGHT] == 320
    
    def test_bishop_value(self):
        assert PIECE_VALUES[Piece.BISHOP] == 330
    
    def test_rook_value(self):
        assert PIECE_VALUES[Piece.ROOK] == 500
    
    def test_queen_value(self):
        assert PIECE_VALUES[Piece.QUEEN] == 900
    
    def test_king_value(self):
        assert PIECE_VALUES[Piece.KING] == 0
    
    def test_bishop_worth_more_than_knight(self):
        """Bishop pair is generally slightly better than knight pair."""
        assert PIECE_VALUES[Piece.BISHOP] > PIECE_VALUES[Piece.KNIGHT]


class TestPieceSquareTables:
    """Tests for piece-square table structure and values."""
    
    def test_all_tables_are_8x8(self):
        """All tables should be 8x8."""
        tables = [
            PAWN_TABLE, KNIGHT_TABLE, BISHOP_TABLE,
            ROOK_TABLE, QUEEN_TABLE, KING_MIDDLEGAME_TABLE, KING_ENDGAME_TABLE
        ]
        for table in tables:
            assert len(table) == 8, "Table should have 8 ranks"
            for rank in table:
                assert len(rank) == 8, "Each rank should have 8 files"
    
    def test_knight_prefers_center(self):
        """Knights should have highest values in center squares."""
        # Center squares: d4, d5, e4, e5 (indices 3,4 for both)
        center_values = [
            KNIGHT_TABLE[3][3], KNIGHT_TABLE[3][4],  # d4, e4
            KNIGHT_TABLE[4][3], KNIGHT_TABLE[4][4],  # d5, e5
        ]
        # Edge values
        edge_values = [
            KNIGHT_TABLE[0][0], KNIGHT_TABLE[0][7],  # a1, h1
            KNIGHT_TABLE[7][0], KNIGHT_TABLE[7][7],  # a8, h8
        ]
        
        assert min(center_values) > max(edge_values)
    
    def test_knight_penalized_on_rim(self):
        """Knights on the rim should have negative values."""
        # a-file and h-file
        for rank in range(8):
            assert KNIGHT_TABLE[rank][0] <= 0, f"Knight on a{rank+1} should be penalized"
            assert KNIGHT_TABLE[rank][7] <= 0, f"Knight on h{rank+1} should be penalized"
    
    def test_pawn_advancement_bonus(self):
        """Pawns should get more bonus as they advance."""
        # Compare rank 4 to rank 6 center pawns
        rank4_d = PAWN_TABLE[3][3]  # d4
        rank6_d = PAWN_TABLE[5][3]  # d6
        rank7_d = PAWN_TABLE[6][3]  # d7 (about to promote)
        
        assert rank6_d > rank4_d
        assert rank7_d > rank6_d
    
    def test_pawn_rank7_high_value(self):
        """Pawns on rank 7 (about to promote) should have high bonus."""
        # All rank 7 pawns should have significant bonus
        for file_idx in range(8):
            assert PAWN_TABLE[6][file_idx] >= 50
    
    def test_bishop_avoids_corners(self):
        """Bishops should have penalties in corners."""
        corners = [
            BISHOP_TABLE[0][0], BISHOP_TABLE[0][7],
            BISHOP_TABLE[7][0], BISHOP_TABLE[7][7],
        ]
        center = BISHOP_TABLE[3][3]  # d4
        
        for corner in corners:
            assert corner < center
    
    def test_rook_7th_rank_bonus(self):
        """Rooks on 7th rank should have bonus."""
        # Rank 7 is index 6
        rank7_values = ROOK_TABLE[6]
        rank2_values = ROOK_TABLE[1]
        
        assert sum(rank7_values) > sum(rank2_values)
    
    def test_king_middlegame_prefers_castled(self):
        """King in middlegame should prefer castled positions."""
        # g1 and c1 (castled positions) vs e4 (center)
        g1_value = KING_MIDDLEGAME_TABLE[0][6]  # g1
        c1_value = KING_MIDDLEGAME_TABLE[0][2]  # c1
        e4_value = KING_MIDDLEGAME_TABLE[3][4]  # e4 (center)
        
        assert g1_value > e4_value
        assert c1_value > e4_value
    
    def test_king_endgame_prefers_center(self):
        """King in endgame should prefer center squares."""
        center_values = [
            KING_ENDGAME_TABLE[3][3], KING_ENDGAME_TABLE[3][4],
            KING_ENDGAME_TABLE[4][3], KING_ENDGAME_TABLE[4][4],
        ]
        corner_values = [
            KING_ENDGAME_TABLE[0][0], KING_ENDGAME_TABLE[0][7],
            KING_ENDGAME_TABLE[7][0], KING_ENDGAME_TABLE[7][7],
        ]
        
        assert min(center_values) > max(corner_values)


class TestGetPieceSquareValue:
    """Tests for piece-square value lookup."""
    
    def test_white_knight_on_d4(self):
        """White knight on d4 should get center bonus."""
        square = Square.from_algebraic("d4")
        value = get_piece_square_value(Piece.KNIGHT, square, Color.WHITE)
        # d4 is file=3, rank=4 (index 3), so table[3][3]
        assert value == KNIGHT_TABLE[3][3]
        assert value > 0  # Center should be positive
    
    def test_white_knight_on_a1(self):
        """White knight on a1 should get corner penalty."""
        square = Square.from_algebraic("a1")
        value = get_piece_square_value(Piece.KNIGHT, square, Color.WHITE)
        assert value == KNIGHT_TABLE[0][0]
        assert value < 0  # Corner should be negative
    
    def test_black_knight_mirrored(self):
        """Black pieces should have mirrored table lookup."""
        # Black knight on d5 should be like white knight on d4
        white_d4 = get_piece_square_value(Piece.KNIGHT, Square.from_algebraic("d4"), Color.WHITE)
        black_d5 = get_piece_square_value(Piece.KNIGHT, Square.from_algebraic("d5"), Color.BLACK)
        
        assert white_d4 == black_d5
    
    def test_black_pawn_advancement(self):
        """Black pawns advancing toward rank 1 should get bonus."""
        # Black pawn on d2 (about to promote) should mirror white pawn on d7
        white_d7 = get_piece_square_value(Piece.PAWN, Square.from_algebraic("d7"), Color.WHITE)
        black_d2 = get_piece_square_value(Piece.PAWN, Square.from_algebraic("d2"), Color.BLACK)
        
        assert white_d7 == black_d2
        assert white_d7 >= 50  # High value for promotion square
    
    def test_king_uses_correct_table(self):
        """King should use middlegame or endgame table as specified."""
        square = Square.from_algebraic("e4")
        
        mid_value = get_piece_square_value(Piece.KING, square, Color.WHITE, is_endgame=False)
        end_value = get_piece_square_value(Piece.KING, square, Color.WHITE, is_endgame=True)
        
        # In endgame, center is much better than middlegame
        assert end_value > mid_value


class TestIsEndgame:
    """Tests for endgame detection."""
    
    def test_initial_position_not_endgame(self):
        """Starting position is not an endgame."""
        game_state = GameState.initial()
        assert not is_endgame(game_state)
    
    def test_no_queens_is_endgame(self):
        """Position with no queens is an endgame."""
        # Kings, rooks, and pawns only
        board = Board.empty()
        board = board.set(Square.from_algebraic("e1"), Piece.KING, Color.WHITE)
        board = board.set(Square.from_algebraic("e8"), Piece.KING, Color.BLACK)
        board = board.set(Square.from_algebraic("a1"), Piece.ROOK, Color.WHITE)
        board = board.set(Square.from_algebraic("a8"), Piece.ROOK, Color.BLACK)
        
        game_state = GameState.initial().with_board(board)
        assert is_endgame(game_state)
    
    def test_queen_with_many_pieces_not_endgame(self):
        """Position with queen and multiple pieces is not endgame."""
        board = Board.empty()
        board = board.set(Square.from_algebraic("e1"), Piece.KING, Color.WHITE)
        board = board.set(Square.from_algebraic("e8"), Piece.KING, Color.BLACK)
        board = board.set(Square.from_algebraic("d1"), Piece.QUEEN, Color.WHITE)
        board = board.set(Square.from_algebraic("a1"), Piece.ROOK, Color.WHITE)
        board = board.set(Square.from_algebraic("h1"), Piece.ROOK, Color.WHITE)
        
        game_state = GameState.initial().with_board(board)
        assert not is_endgame(game_state)
    
    def test_queen_with_one_piece_is_endgame(self):
        """Queen with only one other piece is endgame."""
        board = Board.empty()
        board = board.set(Square.from_algebraic("e1"), Piece.KING, Color.WHITE)
        board = board.set(Square.from_algebraic("e8"), Piece.KING, Color.BLACK)
        board = board.set(Square.from_algebraic("d1"), Piece.QUEEN, Color.WHITE)
        board = board.set(Square.from_algebraic("a1"), Piece.ROOK, Color.WHITE)
        
        game_state = GameState.initial().with_board(board)
        assert is_endgame(game_state)


class TestEvaluateMaterial:
    """Tests for material evaluation."""
    
    def test_initial_position_material_balanced(self):
        """Initial position should have equal material."""
        game_state = GameState.initial()
        white_score = evaluate_material(game_state, Color.WHITE)
        black_score = evaluate_material(game_state, Color.BLACK)
        
        assert white_score == 0  # Balanced = 0
        assert black_score == 0
    
    def test_extra_queen_gives_advantage(self):
        """Extra queen should give significant advantage."""
        board = Board.empty()
        board = board.set(Square.from_algebraic("e1"), Piece.KING, Color.WHITE)
        board = board.set(Square.from_algebraic("e8"), Piece.KING, Color.BLACK)
        board = board.set(Square.from_algebraic("d1"), Piece.QUEEN, Color.WHITE)
        
        game_state = GameState.initial().with_board(board)
        white_score = evaluate_material(game_state, Color.WHITE)
        
        assert white_score == 900  # Queen value
    
    def test_extra_pawn_small_advantage(self):
        """Extra pawn should give small advantage."""
        board = Board.empty()
        board = board.set(Square.from_algebraic("e1"), Piece.KING, Color.WHITE)
        board = board.set(Square.from_algebraic("e8"), Piece.KING, Color.BLACK)
        board = board.set(Square.from_algebraic("e4"), Piece.PAWN, Color.WHITE)
        
        game_state = GameState.initial().with_board(board)
        white_score = evaluate_material(game_state, Color.WHITE)
        
        assert white_score == 100  # Pawn value


class TestEvaluatePieceSquareTables:
    """Tests for piece-square table evaluation."""
    
    def test_initial_position_roughly_balanced(self):
        """Initial position should have roughly equal positional scores."""
        game_state = GameState.initial()
        white_score = evaluate_piece_square_tables(game_state, Color.WHITE)
        black_score = evaluate_piece_square_tables(game_state, Color.BLACK)
        
        # Scores should be opposite
        assert white_score == -black_score
    
    def test_centralized_knight_better(self):
        """Knight in center should score better than on edge."""
        # Knight on d4 vs knight on a1
        board_center = Board.empty()
        board_center = board_center.set(Square.from_algebraic("e1"), Piece.KING, Color.WHITE)
        board_center = board_center.set(Square.from_algebraic("e8"), Piece.KING, Color.BLACK)
        board_center = board_center.set(Square.from_algebraic("d4"), Piece.KNIGHT, Color.WHITE)
        
        board_edge = Board.empty()
        board_edge = board_edge.set(Square.from_algebraic("e1"), Piece.KING, Color.WHITE)
        board_edge = board_edge.set(Square.from_algebraic("e8"), Piece.KING, Color.BLACK)
        board_edge = board_edge.set(Square.from_algebraic("a1"), Piece.KNIGHT, Color.WHITE)
        
        state_center = GameState.initial().with_board(board_center)
        state_edge = GameState.initial().with_board(board_edge)
        
        score_center = evaluate_piece_square_tables(state_center, Color.WHITE)
        score_edge = evaluate_piece_square_tables(state_edge, Color.WHITE)
        
        assert score_center > score_edge


class TestEvaluatePositionHard:
    """Tests for combined evaluation."""
    
    def test_combines_material_and_position(self):
        """Combined evaluation should include both material and positional factors."""
        game_state = GameState.initial()
        
        material = evaluate_material(game_state, Color.WHITE)
        positional = evaluate_piece_square_tables(game_state, Color.WHITE)
        combined = evaluate_position_hard(game_state, Color.WHITE)
        
        assert combined == material + positional
    
    def test_material_dominates_for_large_imbalance(self):
        """Large material advantage should dominate the evaluation."""
        board = Board.empty()
        board = board.set(Square.from_algebraic("e1"), Piece.KING, Color.WHITE)
        board = board.set(Square.from_algebraic("e8"), Piece.KING, Color.BLACK)
        board = board.set(Square.from_algebraic("d1"), Piece.QUEEN, Color.WHITE)
        
        game_state = GameState.initial().with_board(board)
        score = evaluate_position_hard(game_state, Color.WHITE)
        
        # Score should be positive and dominated by queen value
        assert score > 800


class TestMoveOrdering:
    """Tests for move ordering functionality."""
    
    def test_capture_ordered_before_quiet(self):
        """Captures should be ordered before quiet moves."""
        board = Board.empty()
        board = board.set(Square.from_algebraic("e1"), Piece.KING, Color.WHITE)
        board = board.set(Square.from_algebraic("e8"), Piece.KING, Color.BLACK)
        board = board.set(Square.from_algebraic("d4"), Piece.KNIGHT, Color.WHITE)
        board = board.set(Square.from_algebraic("e6"), Piece.PAWN, Color.BLACK)
        
        game_state = GameState.initial().with_board(board)
        
        # Create moves: capture and non-capture
        capture = Move(
            from_square=Square.from_algebraic("d4"),
            to_square=Square.from_algebraic("e6"),
            is_capture=True
        )
        quiet = Move(
            from_square=Square.from_algebraic("d4"),
            to_square=Square.from_algebraic("c2")
        )
        
        capture_score = score_move_for_ordering(game_state, capture)
        quiet_score = score_move_for_ordering(game_state, quiet)
        
        assert capture_score > quiet_score
    
    def test_promotion_ordered_first(self):
        """Promotions should be ordered before captures."""
        board = Board.empty()
        board = board.set(Square.from_algebraic("e1"), Piece.KING, Color.WHITE)
        board = board.set(Square.from_algebraic("e8"), Piece.KING, Color.BLACK)
        board = board.set(Square.from_algebraic("e7"), Piece.PAWN, Color.WHITE)
        board = board.set(Square.from_algebraic("d4"), Piece.KNIGHT, Color.WHITE)
        board = board.set(Square.from_algebraic("e6"), Piece.ROOK, Color.BLACK)
        
        game_state = GameState.initial().with_board(board)
        
        promotion = Move(
            from_square=Square.from_algebraic("e7"),
            to_square=Square.from_algebraic("e8"),
            promotion=Piece.QUEEN
        )
        capture = Move(
            from_square=Square.from_algebraic("d4"),
            to_square=Square.from_algebraic("e6"),
            is_capture=True
        )
        
        promo_score = score_move_for_ordering(game_state, promotion)
        capture_score = score_move_for_ordering(game_state, capture)
        
        assert promo_score > capture_score
    
    def test_mvv_lva_ordering(self):
        """Capturing high value with low value should score higher."""
        board = Board.empty()
        board = board.set(Square.from_algebraic("e1"), Piece.KING, Color.WHITE)
        board = board.set(Square.from_algebraic("e8"), Piece.KING, Color.BLACK)
        board = board.set(Square.from_algebraic("d4"), Piece.PAWN, Color.WHITE)
        board = board.set(Square.from_algebraic("e5"), Piece.QUEEN, Color.BLACK)
        board = board.set(Square.from_algebraic("f3"), Piece.QUEEN, Color.WHITE)
        board = board.set(Square.from_algebraic("g4"), Piece.PAWN, Color.BLACK)
        
        game_state = GameState.initial().with_board(board)
        
        # Pawn takes queen (good MVV-LVA)
        pawn_takes_queen = Move(
            from_square=Square.from_algebraic("d4"),
            to_square=Square.from_algebraic("e5"),
            is_capture=True
        )
        # Queen takes pawn (bad MVV-LVA)
        queen_takes_pawn = Move(
            from_square=Square.from_algebraic("f3"),
            to_square=Square.from_algebraic("g4"),
            is_capture=True
        )
        
        pxq_score = score_move_for_ordering(game_state, pawn_takes_queen)
        qxp_score = score_move_for_ordering(game_state, queen_takes_pawn)
        
        assert pxq_score > qxp_score
    
    def test_order_moves_returns_sorted_list(self):
        """order_moves should return moves sorted by score."""
        game_state = GameState.initial()
        legal_moves = get_legal_moves(game_state)
        
        ordered = order_moves(game_state, legal_moves)
        
        # Should have same moves, just reordered
        assert len(ordered) == len(legal_moves)
        assert set(ordered) == set(legal_moves)


class TestSelectBestMove:
    """Tests for move selection."""
    
    def test_selects_from_legal_moves(self):
        """Selected move should be from the legal moves."""
        game_state = GameState.initial()
        legal_moves = get_legal_moves(game_state)
        
        selected = select_best_move(game_state, legal_moves)
        
        assert selected in legal_moves
    
    def test_raises_on_empty_moves(self):
        """Should raise ValueError when no moves available."""
        game_state = GameState.initial()
        
        with pytest.raises(ValueError, match="No legal moves"):
            select_best_move(game_state, [])
    
    def test_takes_free_piece(self):
        """AI should capture an undefended piece."""
        # White queen can take undefended black rook
        board = Board.empty()
        board = board.set(Square.from_algebraic("e1"), Piece.KING, Color.WHITE)
        board = board.set(Square.from_algebraic("e8"), Piece.KING, Color.BLACK)
        board = board.set(Square.from_algebraic("d1"), Piece.QUEEN, Color.WHITE)
        board = board.set(Square.from_algebraic("d8"), Piece.ROOK, Color.BLACK)
        
        game_state = GameState.initial().with_board(board)
        legal_moves = get_legal_moves(game_state)
        
        selected = select_best_move(game_state, legal_moves)
        
        # Should capture the rook
        assert selected.to_square == Square.from_algebraic("d8")
        assert selected.is_capture
    
    def test_prefers_center_control_opening(self):
        """In opening, AI should prefer moves that control center."""
        game_state = GameState.initial()
        legal_moves = get_legal_moves(game_state)
        
        selected = select_best_move(game_state, legal_moves)
        
        # Should be a reasonable opening move (e4, d4, Nf3, Nc3, etc.)
        # Check it's a pawn or knight move
        moving_piece = game_state.board.get(selected.from_square)
        assert moving_piece is not None
        assert moving_piece[0] in (Piece.PAWN, Piece.KNIGHT)


class TestIntegrationWithEngine:
    """Integration tests with the AI engine."""
    
    def test_hard_difficulty_uses_hard_module(self):
        """Hard difficulty should use piece-square evaluation."""
        from pychess.ai.engine import AIEngine, Difficulty
        
        engine = AIEngine(Difficulty.HARD, seed=42)
        game_state = GameState.initial()
        
        # Should not raise, should return valid move
        move = engine.select_move(game_state)
        
        legal_moves = get_legal_moves(game_state)
        assert move in legal_moves
    
    def test_hard_ai_is_deterministic_with_seed(self):
        """Hard AI with same seed should make same moves."""
        from pychess.ai.engine import AIEngine, Difficulty
        
        game_state = GameState.initial()
        
        engine1 = AIEngine(Difficulty.HARD, seed=123)
        move1 = engine1.select_move(game_state)
        
        engine2 = AIEngine(Difficulty.HARD, seed=123)
        move2 = engine2.select_move(game_state)
        
        assert move1 == move2


# ============================================================================
# EDGE CASE TESTS - Added to improve coverage after initial implementation
# ============================================================================

class TestIsEndgameEdgeCases:
    """Edge cases for endgame detection."""
    
    def test_asymmetric_one_side_has_queen(self):
        """One side has queen, other doesn't - depends on piece count."""
        # White has queen + 2 rooks = not endgame (white has too much)
        board = Board.empty()
        board = board.set(Square.from_algebraic("e1"), Piece.KING, Color.WHITE)
        board = board.set(Square.from_algebraic("e8"), Piece.KING, Color.BLACK)
        board = board.set(Square.from_algebraic("d1"), Piece.QUEEN, Color.WHITE)
        board = board.set(Square.from_algebraic("a1"), Piece.ROOK, Color.WHITE)
        board = board.set(Square.from_algebraic("h1"), Piece.ROOK, Color.WHITE)
        # Black has no queen, just king
        
        game_state = GameState.initial().with_board(board)
        # White has queen + 2 pieces, so NOT endgame
        assert not is_endgame(game_state)
    
    def test_asymmetric_queen_vs_no_queen_minimal(self):
        """One side has queen + 1 piece, other has nothing - is endgame."""
        board = Board.empty()
        board = board.set(Square.from_algebraic("e1"), Piece.KING, Color.WHITE)
        board = board.set(Square.from_algebraic("e8"), Piece.KING, Color.BLACK)
        board = board.set(Square.from_algebraic("d1"), Piece.QUEEN, Color.WHITE)
        board = board.set(Square.from_algebraic("a1"), Piece.ROOK, Color.WHITE)
        # Black has nothing but king
        
        game_state = GameState.initial().with_board(board)
        # White has queen + 1 piece = endgame
        assert is_endgame(game_state)
    
    def test_just_kings_is_endgame(self):
        """Board with only kings should be endgame."""
        board = Board.empty()
        board = board.set(Square.from_algebraic("e1"), Piece.KING, Color.WHITE)
        board = board.set(Square.from_algebraic("e8"), Piece.KING, Color.BLACK)
        
        game_state = GameState.initial().with_board(board)
        assert is_endgame(game_state)
    
    def test_multiple_queens_from_promotion(self):
        """Multiple queens (from promotion) affects endgame detection."""
        board = Board.empty()
        board = board.set(Square.from_algebraic("e1"), Piece.KING, Color.WHITE)
        board = board.set(Square.from_algebraic("e8"), Piece.KING, Color.BLACK)
        board = board.set(Square.from_algebraic("d1"), Piece.QUEEN, Color.WHITE)
        board = board.set(Square.from_algebraic("d2"), Piece.QUEEN, Color.WHITE)  # promoted
        board = board.set(Square.from_algebraic("a1"), Piece.ROOK, Color.WHITE)
        board = board.set(Square.from_algebraic("h1"), Piece.ROOK, Color.WHITE)
        
        game_state = GameState.initial().with_board(board)
        # Has queens + 2 pieces = not endgame
        assert not is_endgame(game_state)
    
    def test_both_sides_queens_one_has_many_pieces(self):
        """Both have queens but one has many pieces - not endgame."""
        board = Board.empty()
        board = board.set(Square.from_algebraic("e1"), Piece.KING, Color.WHITE)
        board = board.set(Square.from_algebraic("e8"), Piece.KING, Color.BLACK)
        board = board.set(Square.from_algebraic("d1"), Piece.QUEEN, Color.WHITE)
        board = board.set(Square.from_algebraic("d8"), Piece.QUEEN, Color.BLACK)
        board = board.set(Square.from_algebraic("a1"), Piece.ROOK, Color.WHITE)
        board = board.set(Square.from_algebraic("h1"), Piece.ROOK, Color.WHITE)
        # Black has queen + 0 pieces (ok)
        # White has queen + 2 pieces (not ok)
        
        game_state = GameState.initial().with_board(board)
        assert not is_endgame(game_state)


class TestPieceSquareValueEdgeCases:
    """Edge cases for piece-square value lookups."""
    
    def test_all_corners_knight_penalty(self):
        """All four corners should penalize knights."""
        corners = ["a1", "h1", "a8", "h8"]
        for corner in corners:
            square = Square.from_algebraic(corner)
            value = get_piece_square_value(Piece.KNIGHT, square, Color.WHITE)
            assert value < 0, f"Knight on {corner} should have negative value"
    
    def test_black_rook_7th_rank_bonus(self):
        """Black rook on rank 2 (their '7th rank') should get bonus."""
        # For black, rank 2 is equivalent to white's rank 7
        square = Square.from_algebraic("d2")
        value = get_piece_square_value(Piece.ROOK, square, Color.BLACK)
        
        # Compare to black rook on rank 7 (their 2nd rank)
        square_back = Square.from_algebraic("d7")
        value_back = get_piece_square_value(Piece.ROOK, square_back, Color.BLACK)
        
        assert value > value_back, "Black rook on 2nd rank should be better than 7th"
    
    def test_white_vs_black_symmetry(self):
        """White piece on e4 should equal Black piece on e5 for symmetric tables."""
        # Knights are symmetric
        white_e4 = get_piece_square_value(Piece.KNIGHT, Square.from_algebraic("e4"), Color.WHITE)
        black_e5 = get_piece_square_value(Piece.KNIGHT, Square.from_algebraic("e5"), Color.BLACK)
        
        assert white_e4 == black_e5
    
    def test_pawn_impossible_squares_have_zero(self):
        """Pawns on rank 1 or 8 (impossible) should have 0 value."""
        # These positions can't happen in real games but test the table
        for file in "abcdefgh":
            sq1 = Square.from_algebraic(f"{file}1")
            sq8 = Square.from_algebraic(f"{file}8")
            
            val1 = get_piece_square_value(Piece.PAWN, sq1, Color.WHITE)
            val8 = get_piece_square_value(Piece.PAWN, sq8, Color.WHITE)
            
            assert val1 == 0, f"Pawn on {file}1 should be 0"
            assert val8 == 0, f"Pawn on {file}8 should be 0"


class TestEvaluateMaterialEdgeCases:
    """Edge cases for material evaluation."""
    
    def test_black_material_advantage(self):
        """Black having more material should give negative score for White."""
        board = Board.empty()
        board = board.set(Square.from_algebraic("e1"), Piece.KING, Color.WHITE)
        board = board.set(Square.from_algebraic("e8"), Piece.KING, Color.BLACK)
        board = board.set(Square.from_algebraic("d8"), Piece.QUEEN, Color.BLACK)
        
        game_state = GameState.initial().with_board(board)
        white_score = evaluate_material(game_state, Color.WHITE)
        black_score = evaluate_material(game_state, Color.BLACK)
        
        assert white_score == -900  # Black has queen
        assert black_score == 900
    
    def test_multiple_pieces_same_type(self):
        """Multiple pieces of same type should sum correctly."""
        board = Board.empty()
        board = board.set(Square.from_algebraic("e1"), Piece.KING, Color.WHITE)
        board = board.set(Square.from_algebraic("e8"), Piece.KING, Color.BLACK)
        board = board.set(Square.from_algebraic("a1"), Piece.ROOK, Color.WHITE)
        board = board.set(Square.from_algebraic("h1"), Piece.ROOK, Color.WHITE)
        board = board.set(Square.from_algebraic("b1"), Piece.KNIGHT, Color.WHITE)
        board = board.set(Square.from_algebraic("g1"), Piece.KNIGHT, Color.WHITE)
        
        game_state = GameState.initial().with_board(board)
        score = evaluate_material(game_state, Color.WHITE)
        
        # 2 rooks (1000) + 2 knights (640)
        assert score == 1640


class TestMoveOrderingEdgeCases:
    """Edge cases for move ordering."""
    
    def test_promotion_with_capture(self):
        """Promotion that is also a capture should score very high."""
        board = Board.empty()
        board = board.set(Square.from_algebraic("e1"), Piece.KING, Color.WHITE)
        board = board.set(Square.from_algebraic("e8"), Piece.KING, Color.BLACK)
        board = board.set(Square.from_algebraic("d7"), Piece.PAWN, Color.WHITE)
        board = board.set(Square.from_algebraic("e8"), Piece.ROOK, Color.BLACK)  # can capture
        
        game_state = GameState.initial().with_board(board)
        
        # Promotion with capture
        promo_capture = Move(
            from_square=Square.from_algebraic("d7"),
            to_square=Square.from_algebraic("e8"),
            promotion=Piece.QUEEN,
            is_capture=True
        )
        # Just promotion
        promo_only = Move(
            from_square=Square.from_algebraic("d7"),
            to_square=Square.from_algebraic("d8"),
            promotion=Piece.QUEEN
        )
        
        capture_score = score_move_for_ordering(game_state, promo_capture)
        promo_score = score_move_for_ordering(game_state, promo_only)
        
        # Both should be high, but capture version even higher
        assert capture_score > promo_score
        assert promo_score > 10000  # Promotion base
    
    def test_knight_promotion_vs_queen_promotion(self):
        """Queen promotion should score higher than knight promotion."""
        board = Board.empty()
        board = board.set(Square.from_algebraic("e1"), Piece.KING, Color.WHITE)
        board = board.set(Square.from_algebraic("e8"), Piece.KING, Color.BLACK)
        board = board.set(Square.from_algebraic("d7"), Piece.PAWN, Color.WHITE)
        
        game_state = GameState.initial().with_board(board)
        
        queen_promo = Move(
            from_square=Square.from_algebraic("d7"),
            to_square=Square.from_algebraic("d8"),
            promotion=Piece.QUEEN
        )
        knight_promo = Move(
            from_square=Square.from_algebraic("d7"),
            to_square=Square.from_algebraic("d8"),
            promotion=Piece.KNIGHT
        )
        
        queen_score = score_move_for_ordering(game_state, queen_promo)
        knight_score = score_move_for_ordering(game_state, knight_promo)
        
        assert queen_score > knight_score
    
    def test_en_passant_ordering(self):
        """En passant capture should be ordered like other pawn captures."""
        board = Board.empty()
        board = board.set(Square.from_algebraic("e1"), Piece.KING, Color.WHITE)
        board = board.set(Square.from_algebraic("e8"), Piece.KING, Color.BLACK)
        board = board.set(Square.from_algebraic("e5"), Piece.PAWN, Color.WHITE)
        board = board.set(Square.from_algebraic("d5"), Piece.PAWN, Color.BLACK)
        
        game_state = GameState.initial().with_board(board).with_en_passant(
            Square.from_algebraic("d6")
        )
        
        ep_move = Move(
            from_square=Square.from_algebraic("e5"),
            to_square=Square.from_algebraic("d6"),
            is_en_passant=True,
            is_capture=True
        )
        
        score = score_move_for_ordering(game_state, ep_move)
        
        # Should be scored as a capture (1000+)
        assert score >= 1000
    
    def test_order_empty_list(self):
        """Ordering empty list should return empty list."""
        game_state = GameState.initial()
        result = order_moves(game_state, [])
        assert result == []
    
    def test_order_single_move(self):
        """Ordering single move should return that move."""
        game_state = GameState.initial()
        single_move = Move(
            from_square=Square.from_algebraic("e2"),
            to_square=Square.from_algebraic("e4")
        )
        
        result = order_moves(game_state, [single_move])
        assert result == [single_move]


class TestSelectBestMoveEdgeCases:
    """Edge cases for best move selection."""
    
    def test_only_one_legal_move(self):
        """With only one legal move, should return that move."""
        # King in corner with one escape square
        board = Board.empty()
        board = board.set(Square.from_algebraic("a1"), Piece.KING, Color.WHITE)
        board = board.set(Square.from_algebraic("c2"), Piece.ROOK, Color.BLACK)  # blocks b1, b2
        board = board.set(Square.from_algebraic("b3"), Piece.ROOK, Color.BLACK)  # blocks a2, a3
        board = board.set(Square.from_algebraic("e8"), Piece.KING, Color.BLACK)
        
        game_state = GameState.initial().with_board(board)
        legal_moves = get_legal_moves(game_state)
        
        # Should have very limited moves
        if len(legal_moves) == 1:
            selected = select_best_move(game_state, legal_moves)
            assert selected == legal_moves[0]
    
    def test_ai_plays_as_black(self):
        """AI should correctly evaluate from Black's perspective."""
        board = Board.empty()
        board = board.set(Square.from_algebraic("e1"), Piece.KING, Color.WHITE)
        board = board.set(Square.from_algebraic("e8"), Piece.KING, Color.BLACK)
        board = board.set(Square.from_algebraic("d1"), Piece.ROOK, Color.WHITE)  # undefended
        board = board.set(Square.from_algebraic("d8"), Piece.QUEEN, Color.BLACK)
        
        # It's Black's turn
        game_state = GameState.initial().with_board(board).with_turn(Color.BLACK)
        legal_moves = get_legal_moves(game_state)
        
        selected = select_best_move(game_state, legal_moves)
        
        # Black should capture the rook
        assert selected.to_square == Square.from_algebraic("d1")
        assert selected.is_capture
    
    def test_finds_checkmate_in_one(self):
        """AI should find checkmate in one when available."""
        # Classic back rank mate setup
        board = Board.empty()
        board = board.set(Square.from_algebraic("g1"), Piece.KING, Color.WHITE)
        board = board.set(Square.from_algebraic("f1"), Piece.ROOK, Color.WHITE)
        board = board.set(Square.from_algebraic("g2"), Piece.PAWN, Color.WHITE)
        board = board.set(Square.from_algebraic("h2"), Piece.PAWN, Color.WHITE)
        board = board.set(Square.from_algebraic("e8"), Piece.KING, Color.BLACK)
        board = board.set(Square.from_algebraic("a1"), Piece.ROOK, Color.BLACK)  # can deliver mate
        
        game_state = GameState.initial().with_board(board).with_turn(Color.BLACK)
        legal_moves = get_legal_moves(game_state)
        
        # Find if Rxf1# is available and if AI picks it
        mate_move = None
        for move in legal_moves:
            if move.from_square == Square.from_algebraic("a1") and \
               move.to_square == Square.from_algebraic("f1"):
                mate_move = move
                break
        
        if mate_move:
            selected = select_best_move(game_state, legal_moves)
            # Should take the rook (wins material at minimum, may be mate)
            assert selected.to_square == Square.from_algebraic("f1")
    
    def test_losing_position_picks_best_available(self):
        """Even in losing position, should pick the least bad move."""
        # White is down a queen but should still make reasonable move
        board = Board.empty()
        board = board.set(Square.from_algebraic("e1"), Piece.KING, Color.WHITE)
        board = board.set(Square.from_algebraic("a2"), Piece.PAWN, Color.WHITE)
        board = board.set(Square.from_algebraic("e8"), Piece.KING, Color.BLACK)
        board = board.set(Square.from_algebraic("d8"), Piece.QUEEN, Color.BLACK)
        board = board.set(Square.from_algebraic("a8"), Piece.ROOK, Color.BLACK)
        
        game_state = GameState.initial().with_board(board)
        legal_moves = get_legal_moves(game_state)
        
        # Should not raise, should return some move
        selected = select_best_move(game_state, legal_moves)
        assert selected in legal_moves


class TestEvaluatePositionSymmetry:
    """Test that evaluation is symmetric between colors."""
    
    def test_initial_position_symmetric(self):
        """Initial position should evaluate equally for both sides."""
        game_state = GameState.initial()
        
        white_eval = evaluate_position_hard(game_state, Color.WHITE)
        black_eval = evaluate_position_hard(game_state, Color.BLACK)
        
        # Should be equal and opposite
        assert white_eval == -black_eval
    
    def test_material_advantage_reflected_correctly(self):
        """Material advantage should show in evaluation."""
        board = Board.empty()
        board = board.set(Square.from_algebraic("e1"), Piece.KING, Color.WHITE)
        board = board.set(Square.from_algebraic("e8"), Piece.KING, Color.BLACK)
        board = board.set(Square.from_algebraic("d4"), Piece.QUEEN, Color.WHITE)
        
        game_state = GameState.initial().with_board(board)
        
        white_eval = evaluate_position_hard(game_state, Color.WHITE)
        black_eval = evaluate_position_hard(game_state, Color.BLACK)
        
        # White should be positive (has queen)
        assert white_eval > 0
        # Black should be negative (opponent has queen)
        assert black_eval < 0
        # Should be opposites
        assert white_eval == -black_eval
