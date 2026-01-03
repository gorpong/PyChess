"""Piece and Color definitions for chess."""

from enum import Enum


class Color(Enum):
    """Chess piece colors."""

    WHITE = "white"
    BLACK = "black"

    def opposite(self) -> "Color":
        """Return the opposite color."""
        return Color.BLACK if self == Color.WHITE else Color.WHITE


class Piece(Enum):
    """Chess piece types."""

    KING = "king"
    QUEEN = "queen"
    ROOK = "rook"
    BISHOP = "bishop"
    KNIGHT = "knight"
    PAWN = "pawn"

    @property
    def san_letter(self) -> str:
        """Return the SAN letter for this piece type.

        Pawns have no letter prefix in SAN notation.
        """
        san_letters = {
            Piece.KING: "K",
            Piece.QUEEN: "Q",
            Piece.ROOK: "R",
            Piece.BISHOP: "B",
            Piece.KNIGHT: "N",
            Piece.PAWN: "",
        }
        return san_letters[self]

    @classmethod
    def from_san(cls, letter: str) -> "Piece":
        """Create a Piece from its SAN letter.

        Raises ValueError for invalid letters.
        """
        san_to_piece = {
            "K": Piece.KING,
            "Q": Piece.QUEEN,
            "R": Piece.ROOK,
            "B": Piece.BISHOP,
            "N": Piece.KNIGHT,
        }
        if letter not in san_to_piece:
            raise ValueError(f"Invalid SAN piece letter: '{letter}'")
        return san_to_piece[letter]

    def unicode_symbol(self, color: Color) -> str:
        """Return the Unicode chess symbol for this piece and color.

        White pieces: U+2654 to U+2659
        Black pieces: U+265A to U+265F
        """
        white_symbols = {
            Piece.KING: "\u2654",
            Piece.QUEEN: "\u2655",
            Piece.ROOK: "\u2656",
            Piece.BISHOP: "\u2657",
            Piece.KNIGHT: "\u2658",
            Piece.PAWN: "\u2659",
        }
        black_symbols = {
            Piece.KING: "\u265a",
            Piece.QUEEN: "\u265b",
            Piece.ROOK: "\u265c",
            Piece.BISHOP: "\u265d",
            Piece.KNIGHT: "\u265e",
            Piece.PAWN: "\u265f",
        }
        if color == Color.WHITE:
            return white_symbols[self]
        return black_symbols[self]

    def ascii_symbol(self, color: Color) -> str:
        """Return ASCII fallback symbol for this piece and color.

        White pieces are uppercase, black pieces are lowercase.
        """
        ascii_letters = {
            Piece.KING: "K",
            Piece.QUEEN: "Q",
            Piece.ROOK: "R",
            Piece.BISHOP: "B",
            Piece.KNIGHT: "N",
            Piece.PAWN: "P",
        }
        letter = ascii_letters[self]
        return letter if color == Color.WHITE else letter.lower()
