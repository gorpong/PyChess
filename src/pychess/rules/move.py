"""Move representation for chess."""

from dataclasses import dataclass
from typing import Optional

from pychess.model.square import Square
from pychess.model.piece import Piece


@dataclass(frozen=True)
class Move:
    """An immutable chess move.

    Represents a move from one square to another, with optional
    special move flags (promotion, castling, en passant, capture).
    """

    from_square: Square
    to_square: Square
    promotion: Optional[Piece] = None
    is_castling: bool = False
    is_en_passant: bool = False
    is_capture: bool = False

    def __str__(self) -> str:
        """Return readable string representation."""
        return f"{self.from_square} -> {self.to_square}"

    def __repr__(self) -> str:
        """Return detailed representation."""
        parts = [f"from={self.from_square}", f"to={self.to_square}"]
        if self.promotion:
            parts.append(f"promotion={self.promotion.name}")
        if self.is_castling:
            parts.append("castling")
        if self.is_en_passant:
            parts.append("en_passant")
        if self.is_capture:
            parts.append("capture")
        return f"Move({', '.join(parts)})"
