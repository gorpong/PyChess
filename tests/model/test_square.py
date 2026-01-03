"""Tests for Square dataclass."""

import pytest
from pychess.model.square import Square


class TestSquareConstruction:
    """Tests for Square construction and validation."""

    def test_square_from_valid_file_rank(self):
        """Square can be constructed with valid file and rank."""
        sq = Square(file="e", rank=4)
        assert sq.file == "e"
        assert sq.rank == 4

    def test_square_file_a_valid(self):
        """File 'a' is valid."""
        sq = Square(file="a", rank=1)
        assert sq.file == "a"

    def test_square_file_h_valid(self):
        """File 'h' is valid."""
        sq = Square(file="h", rank=8)
        assert sq.file == "h"

    def test_square_rank_1_valid(self):
        """Rank 1 is valid."""
        sq = Square(file="a", rank=1)
        assert sq.rank == 1

    def test_square_rank_8_valid(self):
        """Rank 8 is valid."""
        sq = Square(file="a", rank=8)
        assert sq.rank == 8

    def test_square_invalid_file_raises(self):
        """Invalid file raises ValueError."""
        with pytest.raises(ValueError):
            Square(file="i", rank=1)

    def test_square_invalid_file_uppercase_raises(self):
        """Uppercase file raises ValueError (must be lowercase)."""
        with pytest.raises(ValueError):
            Square(file="E", rank=4)

    def test_square_invalid_rank_zero_raises(self):
        """Rank 0 raises ValueError."""
        with pytest.raises(ValueError):
            Square(file="a", rank=0)

    def test_square_invalid_rank_nine_raises(self):
        """Rank 9 raises ValueError."""
        with pytest.raises(ValueError):
            Square(file="a", rank=9)

    def test_square_invalid_rank_negative_raises(self):
        """Negative rank raises ValueError."""
        with pytest.raises(ValueError):
            Square(file="a", rank=-1)


class TestSquareFromAlgebraic:
    """Tests for Square.from_algebraic() factory method."""

    def test_from_algebraic_e4(self):
        """'e4' parses to file='e', rank=4."""
        sq = Square.from_algebraic("e4")
        assert sq.file == "e"
        assert sq.rank == 4

    def test_from_algebraic_a1(self):
        """'a1' parses correctly."""
        sq = Square.from_algebraic("a1")
        assert sq.file == "a"
        assert sq.rank == 1

    def test_from_algebraic_h8(self):
        """'h8' parses correctly."""
        sq = Square.from_algebraic("h8")
        assert sq.file == "h"
        assert sq.rank == 8

    def test_from_algebraic_uppercase_file_accepted(self):
        """Uppercase file in algebraic string is normalized to lowercase."""
        sq = Square.from_algebraic("E4")
        assert sq.file == "e"
        assert sq.rank == 4

    def test_from_algebraic_empty_raises(self):
        """Empty string raises ValueError."""
        with pytest.raises(ValueError):
            Square.from_algebraic("")

    def test_from_algebraic_single_char_raises(self):
        """Single character raises ValueError."""
        with pytest.raises(ValueError):
            Square.from_algebraic("e")

    def test_from_algebraic_invalid_file_raises(self):
        """Invalid file in string raises ValueError."""
        with pytest.raises(ValueError):
            Square.from_algebraic("i4")

    def test_from_algebraic_invalid_rank_raises(self):
        """Invalid rank in string raises ValueError."""
        with pytest.raises(ValueError):
            Square.from_algebraic("e9")

    def test_from_algebraic_non_numeric_rank_raises(self):
        """Non-numeric rank raises ValueError."""
        with pytest.raises(ValueError):
            Square.from_algebraic("ex")


class TestSquareToAlgebraic:
    """Tests for Square.to_algebraic() method."""

    def test_to_algebraic_e4(self):
        """Square(e, 4) returns 'e4'."""
        sq = Square(file="e", rank=4)
        assert sq.to_algebraic() == "e4"

    def test_to_algebraic_a1(self):
        """Square(a, 1) returns 'a1'."""
        sq = Square(file="a", rank=1)
        assert sq.to_algebraic() == "a1"

    def test_to_algebraic_h8(self):
        """Square(h, 8) returns 'h8'."""
        sq = Square(file="h", rank=8)
        assert sq.to_algebraic() == "h8"


class TestSquareEquality:
    """Tests for Square equality comparison."""

    def test_same_square_equal(self):
        """Two squares with same file and rank are equal."""
        sq1 = Square(file="e", rank=4)
        sq2 = Square(file="e", rank=4)
        assert sq1 == sq2

    def test_different_file_not_equal(self):
        """Squares with different files are not equal."""
        sq1 = Square(file="e", rank=4)
        sq2 = Square(file="d", rank=4)
        assert sq1 != sq2

    def test_different_rank_not_equal(self):
        """Squares with different ranks are not equal."""
        sq1 = Square(file="e", rank=4)
        sq2 = Square(file="e", rank=5)
        assert sq1 != sq2

    def test_from_algebraic_equals_constructor(self):
        """Square from algebraic equals square from constructor."""
        sq1 = Square.from_algebraic("e4")
        sq2 = Square(file="e", rank=4)
        assert sq1 == sq2


class TestSquareHashable:
    """Tests for Square hashability (usable as dict key / in sets)."""

    def test_square_hashable(self):
        """Square can be hashed."""
        sq = Square(file="e", rank=4)
        hash(sq)  # Should not raise

    def test_same_squares_same_hash(self):
        """Equal squares have same hash."""
        sq1 = Square(file="e", rank=4)
        sq2 = Square(file="e", rank=4)
        assert hash(sq1) == hash(sq2)

    def test_square_usable_in_set(self):
        """Squares can be stored in a set."""
        squares = {Square(file="e", rank=4), Square(file="d", rank=4)}
        assert len(squares) == 2

    def test_square_usable_as_dict_key(self):
        """Squares can be used as dictionary keys."""
        d = {Square(file="e", rank=4): "pawn"}
        assert d[Square(file="e", rank=4)] == "pawn"


class TestSquareFileIndex:
    """Tests for Square.file_index property."""

    def test_file_index_a_is_0(self):
        """File 'a' has index 0."""
        sq = Square(file="a", rank=1)
        assert sq.file_index == 0

    def test_file_index_h_is_7(self):
        """File 'h' has index 7."""
        sq = Square(file="h", rank=1)
        assert sq.file_index == 7

    def test_file_index_e_is_4(self):
        """File 'e' has index 4."""
        sq = Square(file="e", rank=1)
        assert sq.file_index == 4


class TestSquareRankIndex:
    """Tests for Square.rank_index property."""

    def test_rank_index_1_is_0(self):
        """Rank 1 has index 0."""
        sq = Square(file="a", rank=1)
        assert sq.rank_index == 0

    def test_rank_index_8_is_7(self):
        """Rank 8 has index 7."""
        sq = Square(file="a", rank=8)
        assert sq.rank_index == 7


class TestSquareColor:
    """Tests for Square.is_light property."""

    def test_a1_is_dark(self):
        """a1 is a dark square."""
        sq = Square.from_algebraic("a1")
        assert sq.is_light is False

    def test_a8_is_light(self):
        """a8 is a light square."""
        sq = Square.from_algebraic("a8")
        assert sq.is_light is True

    def test_h1_is_light(self):
        """h1 is a light square."""
        sq = Square.from_algebraic("h1")
        assert sq.is_light is True

    def test_h8_is_dark(self):
        """h8 is a dark square."""
        sq = Square.from_algebraic("h8")
        assert sq.is_light is False

    def test_e4_is_light(self):
        """e4 is a light square."""
        sq = Square.from_algebraic("e4")
        assert sq.is_light is True

    def test_d4_is_dark(self):
        """d4 is a dark square."""
        sq = Square.from_algebraic("d4")
        assert sq.is_light is False


class TestSquareStr:
    """Tests for Square string representation."""

    def test_str_e4(self):
        """str(Square) returns algebraic notation."""
        sq = Square(file="e", rank=4)
        assert str(sq) == "e4"

    def test_repr_includes_square(self):
        """repr(Square) is informative."""
        sq = Square(file="e", rank=4)
        r = repr(sq)
        assert "e" in r
        assert "4" in r
