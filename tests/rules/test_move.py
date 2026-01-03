"""Tests for Move dataclass."""

import pytest
from pychess.rules.move import Move
from pychess.model.square import Square
from pychess.model.piece import Piece


class TestMoveBasic:
    """Tests for basic Move construction."""

    def test_move_from_to(self):
        """Move can be created with from and to squares."""
        move = Move(
            from_square=Square.from_algebraic("e2"),
            to_square=Square.from_algebraic("e4"),
        )
        assert move.from_square == Square.from_algebraic("e2")
        assert move.to_square == Square.from_algebraic("e4")

    def test_move_immutable(self):
        """Move is immutable (frozen dataclass)."""
        move = Move(
            from_square=Square.from_algebraic("e2"),
            to_square=Square.from_algebraic("e4"),
        )
        with pytest.raises(AttributeError):
            move.from_square = Square.from_algebraic("e3")

    def test_move_default_promotion_none(self):
        """Promotion defaults to None."""
        move = Move(
            from_square=Square.from_algebraic("e2"),
            to_square=Square.from_algebraic("e4"),
        )
        assert move.promotion is None

    def test_move_default_not_castling(self):
        """is_castling defaults to False."""
        move = Move(
            from_square=Square.from_algebraic("e2"),
            to_square=Square.from_algebraic("e4"),
        )
        assert move.is_castling is False

    def test_move_default_not_en_passant(self):
        """is_en_passant defaults to False."""
        move = Move(
            from_square=Square.from_algebraic("e2"),
            to_square=Square.from_algebraic("e4"),
        )
        assert move.is_en_passant is False


class TestMovePromotion:
    """Tests for pawn promotion moves."""

    def test_move_with_promotion_queen(self):
        """Move can include promotion to queen."""
        move = Move(
            from_square=Square.from_algebraic("e7"),
            to_square=Square.from_algebraic("e8"),
            promotion=Piece.QUEEN,
        )
        assert move.promotion == Piece.QUEEN

    def test_move_with_promotion_rook(self):
        """Move can include promotion to rook."""
        move = Move(
            from_square=Square.from_algebraic("e7"),
            to_square=Square.from_algebraic("e8"),
            promotion=Piece.ROOK,
        )
        assert move.promotion == Piece.ROOK

    def test_move_with_promotion_bishop(self):
        """Move can include promotion to bishop."""
        move = Move(
            from_square=Square.from_algebraic("e7"),
            to_square=Square.from_algebraic("e8"),
            promotion=Piece.BISHOP,
        )
        assert move.promotion == Piece.BISHOP

    def test_move_with_promotion_knight(self):
        """Move can include promotion to knight."""
        move = Move(
            from_square=Square.from_algebraic("e7"),
            to_square=Square.from_algebraic("e8"),
            promotion=Piece.KNIGHT,
        )
        assert move.promotion == Piece.KNIGHT


class TestMoveCastling:
    """Tests for castling moves."""

    def test_move_white_kingside_castling(self):
        """Move can be marked as kingside castling."""
        move = Move(
            from_square=Square.from_algebraic("e1"),
            to_square=Square.from_algebraic("g1"),
            is_castling=True,
        )
        assert move.is_castling is True

    def test_move_white_queenside_castling(self):
        """Move can be marked as queenside castling."""
        move = Move(
            from_square=Square.from_algebraic("e1"),
            to_square=Square.from_algebraic("c1"),
            is_castling=True,
        )
        assert move.is_castling is True


class TestMoveEnPassant:
    """Tests for en passant moves."""

    def test_move_en_passant(self):
        """Move can be marked as en passant."""
        move = Move(
            from_square=Square.from_algebraic("e5"),
            to_square=Square.from_algebraic("d6"),
            is_en_passant=True,
        )
        assert move.is_en_passant is True


class TestMoveEquality:
    """Tests for Move equality."""

    def test_same_moves_equal(self):
        """Two moves with same squares are equal."""
        move1 = Move(
            from_square=Square.from_algebraic("e2"),
            to_square=Square.from_algebraic("e4"),
        )
        move2 = Move(
            from_square=Square.from_algebraic("e2"),
            to_square=Square.from_algebraic("e4"),
        )
        assert move1 == move2

    def test_different_from_not_equal(self):
        """Moves with different from_square are not equal."""
        move1 = Move(
            from_square=Square.from_algebraic("e2"),
            to_square=Square.from_algebraic("e4"),
        )
        move2 = Move(
            from_square=Square.from_algebraic("d2"),
            to_square=Square.from_algebraic("e4"),
        )
        assert move1 != move2

    def test_different_to_not_equal(self):
        """Moves with different to_square are not equal."""
        move1 = Move(
            from_square=Square.from_algebraic("e2"),
            to_square=Square.from_algebraic("e4"),
        )
        move2 = Move(
            from_square=Square.from_algebraic("e2"),
            to_square=Square.from_algebraic("e3"),
        )
        assert move1 != move2

    def test_different_promotion_not_equal(self):
        """Moves with different promotion are not equal."""
        move1 = Move(
            from_square=Square.from_algebraic("e7"),
            to_square=Square.from_algebraic("e8"),
            promotion=Piece.QUEEN,
        )
        move2 = Move(
            from_square=Square.from_algebraic("e7"),
            to_square=Square.from_algebraic("e8"),
            promotion=Piece.ROOK,
        )
        assert move1 != move2


class TestMoveHashable:
    """Tests for Move hashability."""

    def test_move_hashable(self):
        """Move can be hashed."""
        move = Move(
            from_square=Square.from_algebraic("e2"),
            to_square=Square.from_algebraic("e4"),
        )
        hash(move)  # Should not raise

    def test_same_moves_same_hash(self):
        """Equal moves have same hash."""
        move1 = Move(
            from_square=Square.from_algebraic("e2"),
            to_square=Square.from_algebraic("e4"),
        )
        move2 = Move(
            from_square=Square.from_algebraic("e2"),
            to_square=Square.from_algebraic("e4"),
        )
        assert hash(move1) == hash(move2)

    def test_move_usable_in_set(self):
        """Moves can be stored in a set."""
        moves = {
            Move(
                from_square=Square.from_algebraic("e2"),
                to_square=Square.from_algebraic("e4"),
            ),
            Move(
                from_square=Square.from_algebraic("d2"),
                to_square=Square.from_algebraic("d4"),
            ),
        }
        assert len(moves) == 2


class TestMoveStr:
    """Tests for Move string representation."""

    def test_move_str(self):
        """str(Move) includes from and to squares."""
        move = Move(
            from_square=Square.from_algebraic("e2"),
            to_square=Square.from_algebraic("e4"),
        )
        s = str(move)
        assert "e2" in s
        assert "e4" in s

    def test_move_repr(self):
        """repr(Move) is informative."""
        move = Move(
            from_square=Square.from_algebraic("e2"),
            to_square=Square.from_algebraic("e4"),
        )
        r = repr(move)
        assert "e2" in r
        assert "e4" in r


class TestMoveCaptureProperty:
    """Tests for Move.is_capture property."""

    def test_move_has_is_capture_property(self):
        """Move has an is_capture property."""
        move = Move(
            from_square=Square.from_algebraic("e2"),
            to_square=Square.from_algebraic("e4"),
        )
        assert hasattr(move, "is_capture")

    def test_is_capture_default_false(self):
        """is_capture defaults to False."""
        move = Move(
            from_square=Square.from_algebraic("e2"),
            to_square=Square.from_algebraic("e4"),
        )
        assert move.is_capture is False

    def test_is_capture_can_be_true(self):
        """is_capture can be set to True."""
        move = Move(
            from_square=Square.from_algebraic("e4"),
            to_square=Square.from_algebraic("d5"),
            is_capture=True,
        )
        assert move.is_capture is True
