"""Tests for move generation."""

import pytest
from pychess.rules.move_generator import MoveGenerator
from pychess.rules.move import Move
from pychess.model.board import Board
from pychess.model.piece import Piece, Color
from pychess.model.square import Square
from tests.conftest import place_piece


class TestPawnMovesWhite:
    """Tests for white pawn move generation."""

    def test_pawn_single_push_from_e2(self, empty_board):
        """White pawn on e2 can move to e3."""
        board = place_piece(empty_board, "e2", Piece.PAWN, Color.WHITE)
        moves = MoveGenerator.generate_pawn_moves(board, Square.from_algebraic("e2"), Color.WHITE)

        expected = Move(
            from_square=Square.from_algebraic("e2"),
            to_square=Square.from_algebraic("e3"),
        )
        assert expected in moves

    def test_pawn_double_push_from_e2(self, empty_board):
        """White pawn on e2 can move to e4 (initial double push)."""
        board = place_piece(empty_board, "e2", Piece.PAWN, Color.WHITE)
        moves = MoveGenerator.generate_pawn_moves(board, Square.from_algebraic("e2"), Color.WHITE)

        expected = Move(
            from_square=Square.from_algebraic("e2"),
            to_square=Square.from_algebraic("e4"),
        )
        assert expected in moves

    def test_pawn_no_double_push_from_rank_3(self, empty_board):
        """White pawn on e3 cannot double push."""
        board = place_piece(empty_board, "e3", Piece.PAWN, Color.WHITE)
        moves = MoveGenerator.generate_pawn_moves(board, Square.from_algebraic("e3"), Color.WHITE)

        double_push = Move(
            from_square=Square.from_algebraic("e3"),
            to_square=Square.from_algebraic("e5"),
        )
        assert double_push not in moves

    def test_pawn_blocked_by_own_piece(self, empty_board):
        """White pawn cannot move if blocked by own piece."""
        board = place_piece(empty_board, "e2", Piece.PAWN, Color.WHITE)
        board = place_piece(board, "e3", Piece.KNIGHT, Color.WHITE)
        moves = MoveGenerator.generate_pawn_moves(board, Square.from_algebraic("e2"), Color.WHITE)

        assert len(moves) == 0

    def test_pawn_blocked_by_opponent_piece(self, empty_board):
        """White pawn cannot push if blocked by opponent piece."""
        board = place_piece(empty_board, "e2", Piece.PAWN, Color.WHITE)
        board = place_piece(board, "e3", Piece.PAWN, Color.BLACK)
        moves = MoveGenerator.generate_pawn_moves(board, Square.from_algebraic("e2"), Color.WHITE)

        push = Move(
            from_square=Square.from_algebraic("e2"),
            to_square=Square.from_algebraic("e3"),
        )
        assert push not in moves

    def test_pawn_double_push_blocked_on_target(self, empty_board):
        """White pawn cannot double push if target square occupied."""
        board = place_piece(empty_board, "e2", Piece.PAWN, Color.WHITE)
        board = place_piece(board, "e4", Piece.PAWN, Color.BLACK)
        moves = MoveGenerator.generate_pawn_moves(board, Square.from_algebraic("e2"), Color.WHITE)

        double_push = Move(
            from_square=Square.from_algebraic("e2"),
            to_square=Square.from_algebraic("e4"),
        )
        assert double_push not in moves

    def test_pawn_double_push_blocked_on_intermediate(self, empty_board):
        """White pawn cannot double push if intermediate square occupied."""
        board = place_piece(empty_board, "e2", Piece.PAWN, Color.WHITE)
        board = place_piece(board, "e3", Piece.PAWN, Color.BLACK)
        moves = MoveGenerator.generate_pawn_moves(board, Square.from_algebraic("e2"), Color.WHITE)

        double_push = Move(
            from_square=Square.from_algebraic("e2"),
            to_square=Square.from_algebraic("e4"),
        )
        assert double_push not in moves

    def test_pawn_capture_left(self, empty_board):
        """White pawn can capture diagonally left."""
        board = place_piece(empty_board, "e4", Piece.PAWN, Color.WHITE)
        board = place_piece(board, "d5", Piece.PAWN, Color.BLACK)
        moves = MoveGenerator.generate_pawn_moves(board, Square.from_algebraic("e4"), Color.WHITE)

        expected = Move(
            from_square=Square.from_algebraic("e4"),
            to_square=Square.from_algebraic("d5"),
            is_capture=True,
        )
        assert expected in moves

    def test_pawn_capture_right(self, empty_board):
        """White pawn can capture diagonally right."""
        board = place_piece(empty_board, "e4", Piece.PAWN, Color.WHITE)
        board = place_piece(board, "f5", Piece.PAWN, Color.BLACK)
        moves = MoveGenerator.generate_pawn_moves(board, Square.from_algebraic("e4"), Color.WHITE)

        expected = Move(
            from_square=Square.from_algebraic("e4"),
            to_square=Square.from_algebraic("f5"),
            is_capture=True,
        )
        assert expected in moves

    def test_pawn_no_capture_own_piece(self, empty_board):
        """White pawn cannot capture own piece."""
        board = place_piece(empty_board, "e4", Piece.PAWN, Color.WHITE)
        board = place_piece(board, "d5", Piece.PAWN, Color.WHITE)
        moves = MoveGenerator.generate_pawn_moves(board, Square.from_algebraic("e4"), Color.WHITE)

        invalid_capture = Move(
            from_square=Square.from_algebraic("e4"),
            to_square=Square.from_algebraic("d5"),
            is_capture=True,
        )
        assert invalid_capture not in moves

    def test_pawn_no_capture_empty_square(self, empty_board):
        """White pawn cannot capture on empty diagonal."""
        board = place_piece(empty_board, "e4", Piece.PAWN, Color.WHITE)
        moves = MoveGenerator.generate_pawn_moves(board, Square.from_algebraic("e4"), Color.WHITE)

        # Should only have forward push, no diagonal moves
        for move in moves:
            assert move.to_square.file == "e"  # All moves stay in same file

    def test_pawn_promotion_single_push(self, empty_board):
        """White pawn on rank 7 generates promotion moves."""
        board = place_piece(empty_board, "e7", Piece.PAWN, Color.WHITE)
        moves = MoveGenerator.generate_pawn_moves(board, Square.from_algebraic("e7"), Color.WHITE)

        # Should generate 4 promotion moves (Q, R, B, N)
        promotion_moves = [m for m in moves if m.to_square == Square.from_algebraic("e8")]
        assert len(promotion_moves) == 4

        promotions = {m.promotion for m in promotion_moves}
        assert promotions == {Piece.QUEEN, Piece.ROOK, Piece.BISHOP, Piece.KNIGHT}

    def test_pawn_promotion_capture(self, empty_board):
        """White pawn on rank 7 can promote via capture."""
        board = place_piece(empty_board, "e7", Piece.PAWN, Color.WHITE)
        board = place_piece(board, "d8", Piece.ROOK, Color.BLACK)
        moves = MoveGenerator.generate_pawn_moves(board, Square.from_algebraic("e7"), Color.WHITE)

        # Should generate 4 promotion captures
        capture_promotions = [
            m for m in moves
            if m.to_square == Square.from_algebraic("d8") and m.is_capture
        ]
        assert len(capture_promotions) == 4

    def test_pawn_a_file_no_left_capture(self, empty_board):
        """White pawn on a-file has no left capture."""
        board = place_piece(empty_board, "a4", Piece.PAWN, Color.WHITE)
        board = place_piece(board, "b5", Piece.PAWN, Color.BLACK)  # Only right capture available
        moves = MoveGenerator.generate_pawn_moves(board, Square.from_algebraic("a4"), Color.WHITE)

        # Should have push forward and right capture only
        assert len([m for m in moves if m.is_capture]) <= 1

    def test_pawn_h_file_no_right_capture(self, empty_board):
        """White pawn on h-file has no right capture."""
        board = place_piece(empty_board, "h4", Piece.PAWN, Color.WHITE)
        board = place_piece(board, "g5", Piece.PAWN, Color.BLACK)  # Only left capture available
        moves = MoveGenerator.generate_pawn_moves(board, Square.from_algebraic("h4"), Color.WHITE)

        # Should have push forward and left capture only
        assert len([m for m in moves if m.is_capture]) <= 1


class TestPawnMovesBlack:
    """Tests for black pawn move generation."""

    def test_pawn_single_push_from_e7(self, empty_board):
        """Black pawn on e7 can move to e6."""
        board = place_piece(empty_board, "e7", Piece.PAWN, Color.BLACK)
        moves = MoveGenerator.generate_pawn_moves(board, Square.from_algebraic("e7"), Color.BLACK)

        expected = Move(
            from_square=Square.from_algebraic("e7"),
            to_square=Square.from_algebraic("e6"),
        )
        assert expected in moves

    def test_pawn_double_push_from_e7(self, empty_board):
        """Black pawn on e7 can move to e5 (initial double push)."""
        board = place_piece(empty_board, "e7", Piece.PAWN, Color.BLACK)
        moves = MoveGenerator.generate_pawn_moves(board, Square.from_algebraic("e7"), Color.BLACK)

        expected = Move(
            from_square=Square.from_algebraic("e7"),
            to_square=Square.from_algebraic("e5"),
        )
        assert expected in moves

    def test_pawn_capture_left_for_black(self, empty_board):
        """Black pawn can capture diagonally left (from black's perspective)."""
        board = place_piece(empty_board, "e5", Piece.PAWN, Color.BLACK)
        board = place_piece(board, "d4", Piece.PAWN, Color.WHITE)
        moves = MoveGenerator.generate_pawn_moves(board, Square.from_algebraic("e5"), Color.BLACK)

        expected = Move(
            from_square=Square.from_algebraic("e5"),
            to_square=Square.from_algebraic("d4"),
            is_capture=True,
        )
        assert expected in moves

    def test_pawn_capture_right_for_black(self, empty_board):
        """Black pawn can capture diagonally right (from black's perspective)."""
        board = place_piece(empty_board, "e5", Piece.PAWN, Color.BLACK)
        board = place_piece(board, "f4", Piece.PAWN, Color.WHITE)
        moves = MoveGenerator.generate_pawn_moves(board, Square.from_algebraic("e5"), Color.BLACK)

        expected = Move(
            from_square=Square.from_algebraic("e5"),
            to_square=Square.from_algebraic("f4"),
            is_capture=True,
        )
        assert expected in moves

    def test_black_pawn_promotion(self, empty_board):
        """Black pawn on rank 2 generates promotion moves."""
        board = place_piece(empty_board, "e2", Piece.PAWN, Color.BLACK)
        moves = MoveGenerator.generate_pawn_moves(board, Square.from_algebraic("e2"), Color.BLACK)

        # Should generate 4 promotion moves
        promotion_moves = [m for m in moves if m.to_square == Square.from_algebraic("e1")]
        assert len(promotion_moves) == 4


class TestPawnEnPassant:
    """Tests for en passant capture."""

    def test_en_passant_left(self, empty_board):
        """White pawn can capture en passant to the left."""
        board = place_piece(empty_board, "e5", Piece.PAWN, Color.WHITE)
        board = place_piece(board, "d5", Piece.PAWN, Color.BLACK)

        en_passant_square = Square.from_algebraic("d6")
        moves = MoveGenerator.generate_pawn_moves(
            board,
            Square.from_algebraic("e5"),
            Color.WHITE,
            en_passant_square=en_passant_square
        )

        expected = Move(
            from_square=Square.from_algebraic("e5"),
            to_square=Square.from_algebraic("d6"),
            is_en_passant=True,
            is_capture=True,
        )
        assert expected in moves

    def test_en_passant_right(self, empty_board):
        """White pawn can capture en passant to the right."""
        board = place_piece(empty_board, "e5", Piece.PAWN, Color.WHITE)
        board = place_piece(board, "f5", Piece.PAWN, Color.BLACK)

        en_passant_square = Square.from_algebraic("f6")
        moves = MoveGenerator.generate_pawn_moves(
            board,
            Square.from_algebraic("e5"),
            Color.WHITE,
            en_passant_square=en_passant_square
        )

        expected = Move(
            from_square=Square.from_algebraic("e5"),
            to_square=Square.from_algebraic("f6"),
            is_en_passant=True,
            is_capture=True,
        )
        assert expected in moves

    def test_no_en_passant_without_target_square(self, empty_board):
        """No en passant moves without en_passant_square parameter."""
        board = place_piece(empty_board, "e5", Piece.PAWN, Color.WHITE)
        board = place_piece(board, "d5", Piece.PAWN, Color.BLACK)

        moves = MoveGenerator.generate_pawn_moves(
            board,
            Square.from_algebraic("e5"),
            Color.WHITE,
            en_passant_square=None
        )

        en_passant_moves = [m for m in moves if m.is_en_passant]
        assert len(en_passant_moves) == 0

    def test_black_en_passant(self, empty_board):
        """Black pawn can capture en passant."""
        board = place_piece(empty_board, "e4", Piece.PAWN, Color.BLACK)
        board = place_piece(board, "d4", Piece.PAWN, Color.WHITE)

        en_passant_square = Square.from_algebraic("d3")
        moves = MoveGenerator.generate_pawn_moves(
            board,
            Square.from_algebraic("e4"),
            Color.BLACK,
            en_passant_square=en_passant_square
        )

        expected = Move(
            from_square=Square.from_algebraic("e4"),
            to_square=Square.from_algebraic("d3"),
            is_en_passant=True,
            is_capture=True,
        )
        assert expected in moves


class TestKnightMoves:
    """Tests for knight move generation."""

    def test_knight_center_all_moves(self, empty_board):
        """Knight in center has all 8 moves available."""
        board = place_piece(empty_board, "e4", Piece.KNIGHT, Color.WHITE)
        moves = MoveGenerator.generate_knight_moves(board, Square.from_algebraic("e4"), Color.WHITE)

        # Knight on e4 can reach: d2, f2, c3, g3, c5, g5, d6, f6
        expected_targets = [
            "d2", "f2", "c3", "g3", "c5", "g5", "d6", "f6"
        ]
        actual_targets = {m.to_square.to_algebraic() for m in moves}
        assert actual_targets == set(expected_targets)

    def test_knight_corner_limited_moves(self, empty_board):
        """Knight in corner has only 2 moves."""
        board = place_piece(empty_board, "a1", Piece.KNIGHT, Color.WHITE)
        moves = MoveGenerator.generate_knight_moves(board, Square.from_algebraic("a1"), Color.WHITE)

        # Knight on a1 can only reach b3 and c2
        assert len(moves) == 2
        targets = {m.to_square.to_algebraic() for m in moves}
        assert targets == {"b3", "c2"}

    def test_knight_blocked_by_own_piece(self, empty_board):
        """Knight cannot move to square occupied by own piece."""
        board = place_piece(empty_board, "e4", Piece.KNIGHT, Color.WHITE)
        board = place_piece(board, "d6", Piece.PAWN, Color.WHITE)
        board = place_piece(board, "f6", Piece.PAWN, Color.WHITE)
        moves = MoveGenerator.generate_knight_moves(board, Square.from_algebraic("e4"), Color.WHITE)

        # d6 and f6 should not be in moves
        targets = {m.to_square.to_algebraic() for m in moves}
        assert "d6" not in targets
        assert "f6" not in targets

    def test_knight_can_capture(self, empty_board):
        """Knight can capture opponent pieces."""
        board = place_piece(empty_board, "e4", Piece.KNIGHT, Color.WHITE)
        board = place_piece(board, "d6", Piece.PAWN, Color.BLACK)
        board = place_piece(board, "f6", Piece.PAWN, Color.BLACK)
        moves = MoveGenerator.generate_knight_moves(board, Square.from_algebraic("e4"), Color.WHITE)

        # Should have captures to d6 and f6
        d6_moves = [m for m in moves if m.to_square.to_algebraic() == "d6"]
        f6_moves = [m for m in moves if m.to_square.to_algebraic() == "f6"]

        assert len(d6_moves) == 1
        assert d6_moves[0].is_capture is True

        assert len(f6_moves) == 1
        assert f6_moves[0].is_capture is True

    def test_knight_edge_moves(self, empty_board):
        """Knight on edge has 4 moves."""
        board = place_piece(empty_board, "e1", Piece.KNIGHT, Color.WHITE)
        moves = MoveGenerator.generate_knight_moves(board, Square.from_algebraic("e1"), Color.WHITE)

        # Knight on e1 can reach: c2, g2, d3, f3
        assert len(moves) == 4
        targets = {m.to_square.to_algebraic() for m in moves}
        assert targets == {"c2", "g2", "d3", "f3"}


class TestBishopMoves:
    """Tests for bishop move generation."""

    def test_bishop_center_all_diagonals(self, empty_board):
        """Bishop in center can move along all 4 diagonals."""
        board = place_piece(empty_board, "e4", Piece.BISHOP, Color.WHITE)
        moves = MoveGenerator.generate_bishop_moves(board, Square.from_algebraic("e4"), Color.WHITE)

        # Bishop on e4 can reach:
        # NE: f5, g6, h7
        # NW: d5, c6, b7, a8
        # SE: f3, g2, h1
        # SW: d3, c2, b1
        expected = {
            "f5", "g6", "h7",
            "d5", "c6", "b7", "a8",
            "f3", "g2", "h1",
            "d3", "c2", "b1"
        }
        actual = {m.to_square.to_algebraic() for m in moves}
        assert actual == expected

    def test_bishop_corner(self, empty_board):
        """Bishop in corner has one diagonal."""
        board = place_piece(empty_board, "a1", Piece.BISHOP, Color.WHITE)
        moves = MoveGenerator.generate_bishop_moves(board, Square.from_algebraic("a1"), Color.WHITE)

        # Bishop on a1 can reach: b2, c3, d4, e5, f6, g7, h8
        expected = {"b2", "c3", "d4", "e5", "f6", "g7", "h8"}
        actual = {m.to_square.to_algebraic() for m in moves}
        assert actual == expected

    def test_bishop_blocked_by_own_piece(self, empty_board):
        """Bishop is blocked by own pieces."""
        board = place_piece(empty_board, "e4", Piece.BISHOP, Color.WHITE)
        board = place_piece(board, "f5", Piece.PAWN, Color.WHITE)
        moves = MoveGenerator.generate_bishop_moves(board, Square.from_algebraic("e4"), Color.WHITE)

        # NE diagonal blocked at f5, so no g6, h7
        targets = {m.to_square.to_algebraic() for m in moves}
        assert "f5" not in targets
        assert "g6" not in targets
        assert "h7" not in targets

    def test_bishop_can_capture(self, empty_board):
        """Bishop can capture opponent piece but not go beyond."""
        board = place_piece(empty_board, "e4", Piece.BISHOP, Color.WHITE)
        board = place_piece(board, "f5", Piece.PAWN, Color.BLACK)
        moves = MoveGenerator.generate_bishop_moves(board, Square.from_algebraic("e4"), Color.WHITE)

        # Can capture f5 but not go to g6, h7
        targets = {m.to_square.to_algebraic() for m in moves}
        assert "f5" in targets
        assert "g6" not in targets
        assert "h7" not in targets

        # Verify f5 is marked as capture
        f5_move = [m for m in moves if m.to_square.to_algebraic() == "f5"][0]
        assert f5_move.is_capture is True


class TestRookMoves:
    """Tests for rook move generation."""

    def test_rook_center_all_directions(self, empty_board):
        """Rook in center can move along all 4 orthogonal directions."""
        board = place_piece(empty_board, "e4", Piece.ROOK, Color.WHITE)
        moves = MoveGenerator.generate_rook_moves(board, Square.from_algebraic("e4"), Color.WHITE)

        # Rook on e4 can reach:
        # Up: e5, e6, e7, e8
        # Down: e3, e2, e1
        # Right: f4, g4, h4
        # Left: d4, c4, b4, a4
        expected = {
            "e5", "e6", "e7", "e8",
            "e3", "e2", "e1",
            "f4", "g4", "h4",
            "d4", "c4", "b4", "a4"
        }
        actual = {m.to_square.to_algebraic() for m in moves}
        assert actual == expected

    def test_rook_corner(self, empty_board):
        """Rook in corner has two directions."""
        board = place_piece(empty_board, "a1", Piece.ROOK, Color.WHITE)
        moves = MoveGenerator.generate_rook_moves(board, Square.from_algebraic("a1"), Color.WHITE)

        # Rook on a1 can reach:
        # Up: a2, a3, a4, a5, a6, a7, a8
        # Right: b1, c1, d1, e1, f1, g1, h1
        expected = {
            "a2", "a3", "a4", "a5", "a6", "a7", "a8",
            "b1", "c1", "d1", "e1", "f1", "g1", "h1"
        }
        actual = {m.to_square.to_algebraic() for m in moves}
        assert actual == expected

    def test_rook_blocked_by_own_piece(self, empty_board):
        """Rook is blocked by own pieces."""
        board = place_piece(empty_board, "e4", Piece.ROOK, Color.WHITE)
        board = place_piece(board, "e6", Piece.PAWN, Color.WHITE)
        moves = MoveGenerator.generate_rook_moves(board, Square.from_algebraic("e4"), Color.WHITE)

        targets = {m.to_square.to_algebraic() for m in moves}
        assert "e5" in targets
        assert "e6" not in targets
        assert "e7" not in targets
        assert "e8" not in targets

    def test_rook_can_capture(self, empty_board):
        """Rook can capture opponent piece but not go beyond."""
        board = place_piece(empty_board, "e4", Piece.ROOK, Color.WHITE)
        board = place_piece(board, "e6", Piece.PAWN, Color.BLACK)
        moves = MoveGenerator.generate_rook_moves(board, Square.from_algebraic("e4"), Color.WHITE)

        targets = {m.to_square.to_algebraic() for m in moves}
        assert "e5" in targets
        assert "e6" in targets
        assert "e7" not in targets

        # Verify e6 is marked as capture
        e6_move = [m for m in moves if m.to_square.to_algebraic() == "e6"][0]
        assert e6_move.is_capture is True


class TestQueenMoves:
    """Tests for queen move generation."""

    def test_queen_combines_bishop_and_rook(self, empty_board):
        """Queen has all bishop and rook moves combined."""
        board = place_piece(empty_board, "e4", Piece.QUEEN, Color.WHITE)
        queen_moves = MoveGenerator.generate_queen_moves(board, Square.from_algebraic("e4"), Color.WHITE)

        # Get bishop and rook moves for comparison
        bishop_moves = MoveGenerator.generate_bishop_moves(board, Square.from_algebraic("e4"), Color.WHITE)
        rook_moves = MoveGenerator.generate_rook_moves(board, Square.from_algebraic("e4"), Color.WHITE)

        queen_targets = {m.to_square.to_algebraic() for m in queen_moves}
        bishop_targets = {m.to_square.to_algebraic() for m in bishop_moves}
        rook_targets = {m.to_square.to_algebraic() for m in rook_moves}

        assert queen_targets == bishop_targets | rook_targets

    def test_queen_corner(self, empty_board):
        """Queen in corner has 21 moves (7 diagonal + 14 orthogonal)."""
        board = place_piece(empty_board, "a1", Piece.QUEEN, Color.WHITE)
        moves = MoveGenerator.generate_queen_moves(board, Square.from_algebraic("a1"), Color.WHITE)

        # 7 diagonal (b2-h8) + 7 up (a2-a8) + 7 right (b1-h1) = 21
        assert len(moves) == 21

    def test_queen_blocked(self, empty_board):
        """Queen is blocked by pieces."""
        board = place_piece(empty_board, "e4", Piece.QUEEN, Color.WHITE)
        board = place_piece(board, "e6", Piece.PAWN, Color.WHITE)
        board = place_piece(board, "g6", Piece.PAWN, Color.BLACK)
        moves = MoveGenerator.generate_queen_moves(board, Square.from_algebraic("e4"), Color.WHITE)

        targets = {m.to_square.to_algebraic() for m in moves}
        # Blocked vertically by own piece
        assert "e5" in targets
        assert "e6" not in targets
        assert "e7" not in targets
        # Can capture diagonally
        assert "f5" in targets
        assert "g6" in targets
        assert "h7" not in targets


class TestKingMoves:
    """Tests for king move generation."""

    def test_king_center_all_squares(self, empty_board):
        """King in center has 8 moves."""
        board = place_piece(empty_board, "e4", Piece.KING, Color.WHITE)
        moves = MoveGenerator.generate_king_moves(board, Square.from_algebraic("e4"), Color.WHITE)

        expected = {"d3", "e3", "f3", "d4", "f4", "d5", "e5", "f5"}
        actual = {m.to_square.to_algebraic() for m in moves}
        assert actual == expected

    def test_king_corner_limited_moves(self, empty_board):
        """King in corner has 3 moves."""
        board = place_piece(empty_board, "a1", Piece.KING, Color.WHITE)
        moves = MoveGenerator.generate_king_moves(board, Square.from_algebraic("a1"), Color.WHITE)

        expected = {"a2", "b1", "b2"}
        actual = {m.to_square.to_algebraic() for m in moves}
        assert actual == expected

    def test_king_blocked_by_own_piece(self, empty_board):
        """King cannot move to square with own piece."""
        board = place_piece(empty_board, "e4", Piece.KING, Color.WHITE)
        board = place_piece(board, "e5", Piece.PAWN, Color.WHITE)
        moves = MoveGenerator.generate_king_moves(board, Square.from_algebraic("e4"), Color.WHITE)

        targets = {m.to_square.to_algebraic() for m in moves}
        assert "e5" not in targets
        assert len(targets) == 7

    def test_king_can_capture(self, empty_board):
        """King can capture opponent piece."""
        board = place_piece(empty_board, "e4", Piece.KING, Color.WHITE)
        board = place_piece(board, "e5", Piece.PAWN, Color.BLACK)
        moves = MoveGenerator.generate_king_moves(board, Square.from_algebraic("e4"), Color.WHITE)

        e5_moves = [m for m in moves if m.to_square.to_algebraic() == "e5"]
        assert len(e5_moves) == 1
        assert e5_moves[0].is_capture is True

    def test_king_castling_kingside_white(self, empty_board):
        """King can castle kingside when conditions met."""
        board = place_piece(empty_board, "e1", Piece.KING, Color.WHITE)
        board = place_piece(board, "h1", Piece.ROOK, Color.WHITE)

        from pychess.model.game_state import CastlingRights
        castling = CastlingRights.initial()

        moves = MoveGenerator.generate_king_moves(
            board, Square.from_algebraic("e1"), Color.WHITE, castling_rights=castling
        )

        # Should have castling move to g1
        g1_moves = [m for m in moves if m.to_square.to_algebraic() == "g1"]
        assert len(g1_moves) == 1
        assert g1_moves[0].is_castling is True

    def test_king_castling_queenside_white(self, empty_board):
        """King can castle queenside when conditions met."""
        board = place_piece(empty_board, "e1", Piece.KING, Color.WHITE)
        board = place_piece(board, "a1", Piece.ROOK, Color.WHITE)

        from pychess.model.game_state import CastlingRights
        castling = CastlingRights.initial()

        moves = MoveGenerator.generate_king_moves(
            board, Square.from_algebraic("e1"), Color.WHITE, castling_rights=castling
        )

        # Should have castling move to c1
        c1_moves = [m for m in moves if m.to_square.to_algebraic() == "c1"]
        assert len(c1_moves) == 1
        assert c1_moves[0].is_castling is True

    def test_king_no_castling_without_rights(self, empty_board):
        """King cannot castle without castling rights."""
        board = place_piece(empty_board, "e1", Piece.KING, Color.WHITE)
        board = place_piece(board, "h1", Piece.ROOK, Color.WHITE)

        from pychess.model.game_state import CastlingRights
        castling = CastlingRights(
            white_kingside=False,
            white_queenside=False,
            black_kingside=True,
            black_queenside=True,
        )

        moves = MoveGenerator.generate_king_moves(
            board, Square.from_algebraic("e1"), Color.WHITE, castling_rights=castling
        )

        # Should not have castling moves
        castling_moves = [m for m in moves if m.is_castling]
        assert len(castling_moves) == 0

    def test_king_no_castling_pieces_in_way(self, empty_board):
        """King cannot castle with pieces between king and rook."""
        board = place_piece(empty_board, "e1", Piece.KING, Color.WHITE)
        board = place_piece(board, "h1", Piece.ROOK, Color.WHITE)
        board = place_piece(board, "f1", Piece.BISHOP, Color.WHITE)

        from pychess.model.game_state import CastlingRights
        castling = CastlingRights.initial()

        moves = MoveGenerator.generate_king_moves(
            board, Square.from_algebraic("e1"), Color.WHITE, castling_rights=castling
        )

        # Should not have kingside castling
        g1_castling = [m for m in moves if m.to_square.to_algebraic() == "g1" and m.is_castling]
        assert len(g1_castling) == 0

    def test_king_castling_black(self, empty_board):
        """Black king can castle."""
        board = place_piece(empty_board, "e8", Piece.KING, Color.BLACK)
        board = place_piece(board, "h8", Piece.ROOK, Color.BLACK)

        from pychess.model.game_state import CastlingRights
        castling = CastlingRights.initial()

        moves = MoveGenerator.generate_king_moves(
            board, Square.from_algebraic("e8"), Color.BLACK, castling_rights=castling
        )

        # Should have castling move to g8
        g8_moves = [m for m in moves if m.to_square.to_algebraic() == "g8"]
        assert len(g8_moves) == 1
        assert g8_moves[0].is_castling is True
