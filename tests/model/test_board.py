"""Tests for Board class."""

import pytest
from pychess.model.board import Board
from pychess.model.piece import Piece, Color
from pychess.model.square import Square


class TestBoardInitialPosition:
    """Tests for Board with standard initial position."""

    def test_board_initial_creates_board(self):
        """Board.initial() creates a board."""
        board = Board.initial()
        assert board is not None

    def test_initial_white_king_on_e1(self):
        """White king starts on e1."""
        board = Board.initial()
        piece, color = board.get(Square.from_algebraic("e1"))
        assert piece == Piece.KING
        assert color == Color.WHITE

    def test_initial_black_king_on_e8(self):
        """Black king starts on e8."""
        board = Board.initial()
        piece, color = board.get(Square.from_algebraic("e8"))
        assert piece == Piece.KING
        assert color == Color.BLACK

    def test_initial_white_queen_on_d1(self):
        """White queen starts on d1."""
        board = Board.initial()
        piece, color = board.get(Square.from_algebraic("d1"))
        assert piece == Piece.QUEEN
        assert color == Color.WHITE

    def test_initial_black_queen_on_d8(self):
        """Black queen starts on d8."""
        board = Board.initial()
        piece, color = board.get(Square.from_algebraic("d8"))
        assert piece == Piece.QUEEN
        assert color == Color.BLACK

    def test_initial_white_rooks(self):
        """White rooks start on a1 and h1."""
        board = Board.initial()
        for sq in ["a1", "h1"]:
            piece, color = board.get(Square.from_algebraic(sq))
            assert piece == Piece.ROOK
            assert color == Color.WHITE

    def test_initial_black_rooks(self):
        """Black rooks start on a8 and h8."""
        board = Board.initial()
        for sq in ["a8", "h8"]:
            piece, color = board.get(Square.from_algebraic(sq))
            assert piece == Piece.ROOK
            assert color == Color.BLACK

    def test_initial_white_knights(self):
        """White knights start on b1 and g1."""
        board = Board.initial()
        for sq in ["b1", "g1"]:
            piece, color = board.get(Square.from_algebraic(sq))
            assert piece == Piece.KNIGHT
            assert color == Color.WHITE

    def test_initial_black_knights(self):
        """Black knights start on b8 and g8."""
        board = Board.initial()
        for sq in ["b8", "g8"]:
            piece, color = board.get(Square.from_algebraic(sq))
            assert piece == Piece.KNIGHT
            assert color == Color.BLACK

    def test_initial_white_bishops(self):
        """White bishops start on c1 and f1."""
        board = Board.initial()
        for sq in ["c1", "f1"]:
            piece, color = board.get(Square.from_algebraic(sq))
            assert piece == Piece.BISHOP
            assert color == Color.WHITE

    def test_initial_black_bishops(self):
        """Black bishops start on c8 and f8."""
        board = Board.initial()
        for sq in ["c8", "f8"]:
            piece, color = board.get(Square.from_algebraic(sq))
            assert piece == Piece.BISHOP
            assert color == Color.BLACK

    def test_initial_white_pawns_on_rank_2(self):
        """White pawns start on all files of rank 2."""
        board = Board.initial()
        for file in "abcdefgh":
            piece, color = board.get(Square(file=file, rank=2))
            assert piece == Piece.PAWN
            assert color == Color.WHITE

    def test_initial_black_pawns_on_rank_7(self):
        """Black pawns start on all files of rank 7."""
        board = Board.initial()
        for file in "abcdefgh":
            piece, color = board.get(Square(file=file, rank=7))
            assert piece == Piece.PAWN
            assert color == Color.BLACK

    def test_initial_empty_squares_rank_3(self):
        """Rank 3 is empty in initial position."""
        board = Board.initial()
        for file in "abcdefgh":
            result = board.get(Square(file=file, rank=3))
            assert result is None

    def test_initial_empty_squares_rank_4(self):
        """Rank 4 is empty in initial position."""
        board = Board.initial()
        for file in "abcdefgh":
            result = board.get(Square(file=file, rank=4))
            assert result is None

    def test_initial_empty_squares_rank_5(self):
        """Rank 5 is empty in initial position."""
        board = Board.initial()
        for file in "abcdefgh":
            result = board.get(Square(file=file, rank=5))
            assert result is None

    def test_initial_empty_squares_rank_6(self):
        """Rank 6 is empty in initial position."""
        board = Board.initial()
        for file in "abcdefgh":
            result = board.get(Square(file=file, rank=6))
            assert result is None

    def test_initial_32_pieces_total(self):
        """Initial position has 32 pieces."""
        board = Board.initial()
        count = 0
        for file in "abcdefgh":
            for rank in range(1, 9):
                if board.get(Square(file=file, rank=rank)) is not None:
                    count += 1
        assert count == 32

    def test_initial_16_white_pieces(self):
        """Initial position has 16 white pieces."""
        board = Board.initial()
        count = 0
        for file in "abcdefgh":
            for rank in range(1, 9):
                result = board.get(Square(file=file, rank=rank))
                if result is not None and result[1] == Color.WHITE:
                    count += 1
        assert count == 16

    def test_initial_16_black_pieces(self):
        """Initial position has 16 black pieces."""
        board = Board.initial()
        count = 0
        for file in "abcdefgh":
            for rank in range(1, 9):
                result = board.get(Square(file=file, rank=rank))
                if result is not None and result[1] == Color.BLACK:
                    count += 1
        assert count == 16


class TestBoardEmpty:
    """Tests for empty Board."""

    def test_board_empty_creates_board(self):
        """Board.empty() creates a board."""
        board = Board.empty()
        assert board is not None

    def test_empty_board_all_squares_empty(self):
        """Empty board has no pieces."""
        board = Board.empty()
        for file in "abcdefgh":
            for rank in range(1, 9):
                result = board.get(Square(file=file, rank=rank))
                assert result is None


class TestBoardSetPiece:
    """Tests for Board.set() method."""

    def test_set_piece_on_empty_board(self):
        """Can set a piece on an empty square."""
        board = Board.empty()
        new_board = board.set(Square.from_algebraic("e4"), Piece.KNIGHT, Color.WHITE)
        piece, color = new_board.get(Square.from_algebraic("e4"))
        assert piece == Piece.KNIGHT
        assert color == Color.WHITE

    def test_set_does_not_modify_original(self):
        """set() returns a new board, original unchanged."""
        board = Board.empty()
        new_board = board.set(Square.from_algebraic("e4"), Piece.KNIGHT, Color.WHITE)
        assert board.get(Square.from_algebraic("e4")) is None
        assert new_board.get(Square.from_algebraic("e4")) is not None

    def test_set_replaces_existing_piece(self):
        """set() can replace an existing piece."""
        board = Board.initial()
        new_board = board.set(Square.from_algebraic("e1"), Piece.QUEEN, Color.BLACK)
        piece, color = new_board.get(Square.from_algebraic("e1"))
        assert piece == Piece.QUEEN
        assert color == Color.BLACK


class TestBoardRemovePiece:
    """Tests for Board.remove() method."""

    def test_remove_piece(self):
        """Can remove a piece from the board."""
        board = Board.initial()
        new_board = board.remove(Square.from_algebraic("e1"))
        assert new_board.get(Square.from_algebraic("e1")) is None

    def test_remove_does_not_modify_original(self):
        """remove() returns a new board, original unchanged."""
        board = Board.initial()
        new_board = board.remove(Square.from_algebraic("e1"))
        assert board.get(Square.from_algebraic("e1")) is not None
        assert new_board.get(Square.from_algebraic("e1")) is None

    def test_remove_empty_square_is_noop(self):
        """Removing from empty square returns equivalent board."""
        board = Board.empty()
        new_board = board.remove(Square.from_algebraic("e4"))
        assert new_board.get(Square.from_algebraic("e4")) is None


class TestBoardFindPieces:
    """Tests for finding pieces on the board."""

    def test_find_king_white(self):
        """Can find the white king."""
        board = Board.initial()
        squares = board.find_pieces(Piece.KING, Color.WHITE)
        assert len(squares) == 1
        assert squares[0] == Square.from_algebraic("e1")

    def test_find_king_black(self):
        """Can find the black king."""
        board = Board.initial()
        squares = board.find_pieces(Piece.KING, Color.BLACK)
        assert len(squares) == 1
        assert squares[0] == Square.from_algebraic("e8")

    def test_find_rooks_white(self):
        """Can find both white rooks."""
        board = Board.initial()
        squares = board.find_pieces(Piece.ROOK, Color.WHITE)
        assert len(squares) == 2
        assert Square.from_algebraic("a1") in squares
        assert Square.from_algebraic("h1") in squares

    def test_find_pawns_white(self):
        """Can find all eight white pawns."""
        board = Board.initial()
        squares = board.find_pieces(Piece.PAWN, Color.WHITE)
        assert len(squares) == 8

    def test_find_nonexistent_piece(self):
        """Finding piece not on board returns empty list."""
        board = Board.empty()
        squares = board.find_pieces(Piece.QUEEN, Color.WHITE)
        assert squares == []


class TestBoardGetAllPieces:
    """Tests for getting all pieces by color."""

    def test_get_all_pieces_white_initial(self):
        """Get all white pieces in initial position."""
        board = Board.initial()
        pieces = board.get_pieces_by_color(Color.WHITE)
        assert len(pieces) == 16

    def test_get_all_pieces_black_initial(self):
        """Get all black pieces in initial position."""
        board = Board.initial()
        pieces = board.get_pieces_by_color(Color.BLACK)
        assert len(pieces) == 16

    def test_get_all_pieces_returns_square_and_piece(self):
        """get_pieces_by_color returns list of (square, piece) tuples."""
        board = Board.initial()
        pieces = board.get_pieces_by_color(Color.WHITE)
        # Check one entry
        found_king = False
        for square, piece in pieces:
            if square == Square.from_algebraic("e1"):
                assert piece == Piece.KING
                found_king = True
        assert found_king


class TestBoardCopy:
    """Tests for Board copying."""

    def test_board_copy_equals_original(self):
        """Copied board equals original."""
        board = Board.initial()
        copy = board.copy()
        for file in "abcdefgh":
            for rank in range(1, 9):
                sq = Square(file=file, rank=rank)
                assert board.get(sq) == copy.get(sq)

    def test_board_copy_is_independent(self):
        """Modifying copy doesn't affect original."""
        board = Board.initial()
        copy = board.copy()
        modified = copy.remove(Square.from_algebraic("e1"))
        assert board.get(Square.from_algebraic("e1")) is not None
        assert modified.get(Square.from_algebraic("e1")) is None
