"""Board rendering logic for terminal display.

This module handles the visual representation of the chess board,
including pieces, colors, and highlighting.
"""

from typing import Optional

from pychess.model.board import Board
from pychess.model.piece import Piece, Color
from pychess.model.square import Square


# Unicode chess piece symbols (white pieces, black pieces)
UNICODE_PIECES = {
    (Piece.KING, Color.WHITE): "♔",
    (Piece.QUEEN, Color.WHITE): "♕",
    (Piece.ROOK, Color.WHITE): "♖",
    (Piece.BISHOP, Color.WHITE): "♗",
    (Piece.KNIGHT, Color.WHITE): "♘",
    (Piece.PAWN, Color.WHITE): "♙",
    (Piece.KING, Color.BLACK): "♚",
    (Piece.QUEEN, Color.BLACK): "♛",
    (Piece.ROOK, Color.BLACK): "♜",
    (Piece.BISHOP, Color.BLACK): "♝",
    (Piece.KNIGHT, Color.BLACK): "♞",
    (Piece.PAWN, Color.BLACK): "♟",
}

# ASCII fallback (uppercase = white, lowercase = black)
ASCII_PIECES = {
    (Piece.KING, Color.WHITE): "K",
    (Piece.QUEEN, Color.WHITE): "Q",
    (Piece.ROOK, Color.WHITE): "R",
    (Piece.BISHOP, Color.WHITE): "B",
    (Piece.KNIGHT, Color.WHITE): "N",
    (Piece.PAWN, Color.WHITE): "P",
    (Piece.KING, Color.BLACK): "k",
    (Piece.QUEEN, Color.BLACK): "q",
    (Piece.ROOK, Color.BLACK): "r",
    (Piece.BISHOP, Color.BLACK): "b",
    (Piece.KNIGHT, Color.BLACK): "n",
    (Piece.PAWN, Color.BLACK): "p",
}


class BoardView:
    """Handles rendering of the chess board."""

    def __init__(self, use_unicode: bool = True):
        """Initialize board view.

        Args:
            use_unicode: Whether to use Unicode piece symbols (True) or ASCII (False)
        """
        self.use_unicode = use_unicode
        self.piece_map = UNICODE_PIECES if use_unicode else ASCII_PIECES

    def get_piece_symbol(self, piece_type: Piece, color: Color) -> str:
        """Get the display symbol for a piece.

        Args:
            piece_type: Type of piece
            color: Color of piece

        Returns:
            String symbol for the piece
        """
        return self.piece_map.get((piece_type, color), " ")

    def is_light_square(self, square: Square) -> bool:
        """Determine if a square is light or dark.

        Args:
            square: Square to check

        Returns:
            True if light square, False if dark
        """
        file_idx = ord(square.file) - ord('a')
        rank_idx = square.rank - 1
        return (file_idx + rank_idx) % 2 == 1

    def get_square_at_position(self, file: str, rank: int) -> Square:
        """Create a Square object for the given file and rank.

        Args:
            file: File letter (a-h)
            rank: Rank number (1-8)

        Returns:
            Square object
        """
        return Square(file=file, rank=rank)

    def render_board_text(
        self,
        board: Board,
        selected_square: Optional[Square] = None,
        cursor_square: Optional[Square] = None,
        legal_moves: Optional[set[Square]] = None,
    ) -> list[str]:
        """Render the board as a list of text lines.

        This is a simplified text representation for testing.
        The actual terminal rendering will use blessed for colors and formatting.

        Args:
            board: Board to render
            selected_square: Currently selected square
            cursor_square: Square where cursor is positioned
            legal_moves: Set of legal destination squares to highlight

        Returns:
            List of strings representing the board
        """
        if legal_moves is None:
            legal_moves = set()

        lines = []
        files = "abcdefgh"

        # Top border
        lines.append("  +" + "-" * 24 + "+")

        # Render ranks from 8 to 1 (top to bottom)
        for rank in range(8, 0, -1):
            line_parts = [f"{rank} |"]

            for file in files:
                square = Square(file=file, rank=rank)
                piece_info = board.get(square)

                # Determine piece symbol
                if piece_info:
                    piece_type, color = piece_info
                    symbol = self.get_piece_symbol(piece_type, color)
                else:
                    symbol = " "

                # Add markers for selection/cursor
                prefix = ""
                suffix = ""

                if square == cursor_square:
                    prefix = "["
                    suffix = "]"
                elif square == selected_square:
                    prefix = "("
                    suffix = ")"
                elif square in legal_moves:
                    prefix = "<"
                    suffix = ">"
                else:
                    prefix = " "
                    suffix = " "

                line_parts.append(prefix + symbol + suffix)

            line_parts.append("|")
            lines.append("".join(line_parts))

        # Bottom border
        lines.append("  +" + "-" * 24 + "+")

        # File labels
        file_labels = "    " + "  ".join(files)
        lines.append(file_labels)

        return lines
