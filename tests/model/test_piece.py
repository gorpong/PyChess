"""Tests for Piece and Color enums."""

import pytest
from pychess.model.piece import Piece, Color


class TestColor:
    """Tests for Color enum."""

    def test_color_has_white(self):
        """Color enum must have WHITE."""
        assert Color.WHITE is not None

    def test_color_has_black(self):
        """Color enum must have BLACK."""
        assert Color.BLACK is not None

    def test_color_opposite_white(self):
        """WHITE.opposite() returns BLACK."""
        assert Color.WHITE.opposite() == Color.BLACK

    def test_color_opposite_black(self):
        """BLACK.opposite() returns WHITE."""
        assert Color.BLACK.opposite() == Color.WHITE

    def test_color_only_two_values(self):
        """Color enum has exactly two values."""
        assert len(Color) == 2


class TestPiece:
    """Tests for Piece enum."""

    def test_piece_has_king(self):
        """Piece enum must have KING."""
        assert Piece.KING is not None

    def test_piece_has_queen(self):
        """Piece enum must have QUEEN."""
        assert Piece.QUEEN is not None

    def test_piece_has_rook(self):
        """Piece enum must have ROOK."""
        assert Piece.ROOK is not None

    def test_piece_has_bishop(self):
        """Piece enum must have BISHOP."""
        assert Piece.BISHOP is not None

    def test_piece_has_knight(self):
        """Piece enum must have KNIGHT."""
        assert Piece.KNIGHT is not None

    def test_piece_has_pawn(self):
        """Piece enum must have PAWN."""
        assert Piece.PAWN is not None

    def test_piece_has_exactly_six_values(self):
        """Piece enum has exactly six piece types."""
        assert len(Piece) == 6

    def test_piece_san_letter_king(self):
        """King's SAN letter is 'K'."""
        assert Piece.KING.san_letter == "K"

    def test_piece_san_letter_queen(self):
        """Queen's SAN letter is 'Q'."""
        assert Piece.QUEEN.san_letter == "Q"

    def test_piece_san_letter_rook(self):
        """Rook's SAN letter is 'R'."""
        assert Piece.ROOK.san_letter == "R"

    def test_piece_san_letter_bishop(self):
        """Bishop's SAN letter is 'B'."""
        assert Piece.BISHOP.san_letter == "B"

    def test_piece_san_letter_knight(self):
        """Knight's SAN letter is 'N'."""
        assert Piece.KNIGHT.san_letter == "N"

    def test_piece_san_letter_pawn(self):
        """Pawn has empty string for SAN letter (pawns don't use letter prefix)."""
        assert Piece.PAWN.san_letter == ""

    def test_piece_from_san_letter_k(self):
        """Piece.from_san('K') returns KING."""
        assert Piece.from_san("K") == Piece.KING

    def test_piece_from_san_letter_q(self):
        """Piece.from_san('Q') returns QUEEN."""
        assert Piece.from_san("Q") == Piece.QUEEN

    def test_piece_from_san_letter_r(self):
        """Piece.from_san('R') returns ROOK."""
        assert Piece.from_san("R") == Piece.ROOK

    def test_piece_from_san_letter_b(self):
        """Piece.from_san('B') returns BISHOP."""
        assert Piece.from_san("B") == Piece.BISHOP

    def test_piece_from_san_letter_n(self):
        """Piece.from_san('N') returns KNIGHT."""
        assert Piece.from_san("N") == Piece.KNIGHT

    def test_piece_from_san_invalid_raises(self):
        """Piece.from_san with invalid letter raises ValueError."""
        with pytest.raises(ValueError):
            Piece.from_san("X")

    def test_piece_from_san_empty_raises(self):
        """Piece.from_san with empty string raises ValueError."""
        with pytest.raises(ValueError):
            Piece.from_san("")

    def test_piece_unicode_white_king(self):
        """White king has correct unicode symbol."""
        assert Piece.KING.unicode_symbol(Color.WHITE) == "\u2654"

    def test_piece_unicode_black_king(self):
        """Black king has correct unicode symbol."""
        assert Piece.KING.unicode_symbol(Color.BLACK) == "\u265a"

    def test_piece_unicode_white_queen(self):
        """White queen has correct unicode symbol."""
        assert Piece.QUEEN.unicode_symbol(Color.WHITE) == "\u2655"

    def test_piece_unicode_black_queen(self):
        """Black queen has correct unicode symbol."""
        assert Piece.QUEEN.unicode_symbol(Color.BLACK) == "\u265b"

    def test_piece_unicode_white_rook(self):
        """White rook has correct unicode symbol."""
        assert Piece.ROOK.unicode_symbol(Color.WHITE) == "\u2656"

    def test_piece_unicode_black_rook(self):
        """Black rook has correct unicode symbol."""
        assert Piece.ROOK.unicode_symbol(Color.BLACK) == "\u265c"

    def test_piece_unicode_white_bishop(self):
        """White bishop has correct unicode symbol."""
        assert Piece.BISHOP.unicode_symbol(Color.WHITE) == "\u2657"

    def test_piece_unicode_black_bishop(self):
        """Black bishop has correct unicode symbol."""
        assert Piece.BISHOP.unicode_symbol(Color.BLACK) == "\u265d"

    def test_piece_unicode_white_knight(self):
        """White knight has correct unicode symbol."""
        assert Piece.KNIGHT.unicode_symbol(Color.WHITE) == "\u2658"

    def test_piece_unicode_black_knight(self):
        """Black knight has correct unicode symbol."""
        assert Piece.KNIGHT.unicode_symbol(Color.BLACK) == "\u265e"

    def test_piece_unicode_white_pawn(self):
        """White pawn has correct unicode symbol."""
        assert Piece.PAWN.unicode_symbol(Color.WHITE) == "\u2659"

    def test_piece_unicode_black_pawn(self):
        """Black pawn has correct unicode symbol."""
        assert Piece.PAWN.unicode_symbol(Color.BLACK) == "\u265f"

    def test_piece_ascii_white_king(self):
        """White king ASCII fallback is 'K'."""
        assert Piece.KING.ascii_symbol(Color.WHITE) == "K"

    def test_piece_ascii_black_king(self):
        """Black king ASCII fallback is 'k'."""
        assert Piece.KING.ascii_symbol(Color.BLACK) == "k"

    def test_piece_ascii_white_pawn(self):
        """White pawn ASCII fallback is 'P'."""
        assert Piece.PAWN.ascii_symbol(Color.WHITE) == "P"

    def test_piece_ascii_black_pawn(self):
        """Black pawn ASCII fallback is 'p'."""
        assert Piece.PAWN.ascii_symbol(Color.BLACK) == "p"
