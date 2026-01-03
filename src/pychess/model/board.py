"""Chess board representation."""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional

from pychess.model.piece import Piece, Color
from pychess.model.square import Square


@dataclass(frozen=True)
class Board:
    """An immutable chess board.

    Stores piece positions as a mapping from square to (piece, color).
    Immutable - all modification methods return new Board instances.
    """

    _pieces: dict[Square, tuple[Piece, Color]] = field(default_factory=dict)

    def get(self, square: Square) -> Optional[tuple[Piece, Color]]:
        """Get the piece at a square, or None if empty."""
        return self._pieces.get(square)

    def set(self, square: Square, piece: Piece, color: Color) -> Board:
        """Return a new board with a piece placed at the square."""
        new_pieces = dict(self._pieces)
        new_pieces[square] = (piece, color)
        return Board(_pieces=new_pieces)

    def remove(self, square: Square) -> Board:
        """Return a new board with the piece removed from the square."""
        new_pieces = dict(self._pieces)
        new_pieces.pop(square, None)
        return Board(_pieces=new_pieces)

    def find_pieces(self, piece: Piece, color: Color) -> list[Square]:
        """Find all squares containing the specified piece and color."""
        return [
            sq for sq, (p, c) in self._pieces.items()
            if p == piece and c == color
        ]

    def get_pieces_by_color(self, color: Color) -> list[tuple[Square, Piece]]:
        """Get all pieces of a given color as (square, piece) tuples."""
        return [
            (sq, p) for sq, (p, c) in self._pieces.items()
            if c == color
        ]

    def copy(self) -> Board:
        """Return a copy of this board."""
        return Board(_pieces=dict(self._pieces))

    @classmethod
    def empty(cls) -> Board:
        """Create an empty board."""
        return cls(_pieces={})

    @classmethod
    def initial(cls) -> Board:
        """Create a board with the standard initial position."""
        pieces: dict[Square, tuple[Piece, Color]] = {}

        # White pieces (rank 1)
        pieces[Square(file="a", rank=1)] = (Piece.ROOK, Color.WHITE)
        pieces[Square(file="b", rank=1)] = (Piece.KNIGHT, Color.WHITE)
        pieces[Square(file="c", rank=1)] = (Piece.BISHOP, Color.WHITE)
        pieces[Square(file="d", rank=1)] = (Piece.QUEEN, Color.WHITE)
        pieces[Square(file="e", rank=1)] = (Piece.KING, Color.WHITE)
        pieces[Square(file="f", rank=1)] = (Piece.BISHOP, Color.WHITE)
        pieces[Square(file="g", rank=1)] = (Piece.KNIGHT, Color.WHITE)
        pieces[Square(file="h", rank=1)] = (Piece.ROOK, Color.WHITE)

        # White pawns (rank 2)
        for file in "abcdefgh":
            pieces[Square(file=file, rank=2)] = (Piece.PAWN, Color.WHITE)

        # Black pieces (rank 8)
        pieces[Square(file="a", rank=8)] = (Piece.ROOK, Color.BLACK)
        pieces[Square(file="b", rank=8)] = (Piece.KNIGHT, Color.BLACK)
        pieces[Square(file="c", rank=8)] = (Piece.BISHOP, Color.BLACK)
        pieces[Square(file="d", rank=8)] = (Piece.QUEEN, Color.BLACK)
        pieces[Square(file="e", rank=8)] = (Piece.KING, Color.BLACK)
        pieces[Square(file="f", rank=8)] = (Piece.BISHOP, Color.BLACK)
        pieces[Square(file="g", rank=8)] = (Piece.KNIGHT, Color.BLACK)
        pieces[Square(file="h", rank=8)] = (Piece.ROOK, Color.BLACK)

        # Black pawns (rank 7)
        for file in "abcdefgh":
            pieces[Square(file=file, rank=7)] = (Piece.PAWN, Color.BLACK)

        return cls(_pieces=pieces)
