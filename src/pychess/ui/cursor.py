"""Cursor state management for board navigation.

This module manages the cursor position and selected piece state
for keyboard-based chess piece movement.
"""

from dataclasses import dataclass
from typing import Optional

from pychess.model.square import Square


@dataclass
class CursorState:
    """Manages cursor position and selection state."""

    position: Square
    selected_square: Optional[Square] = None

    @classmethod
    def initial(cls) -> "CursorState":
        """Create initial cursor state at e2 (common starting position).

        Returns:
            CursorState with cursor at e2
        """
        return cls(position=Square(file="e", rank=2))

    def move_up(self) -> "CursorState":
        """Move cursor up one rank (toward rank 8).

        Returns:
            New CursorState with updated position
        """
        if self.position.rank < 8:
            new_pos = Square(file=self.position.file, rank=self.position.rank + 1)
            return CursorState(position=new_pos, selected_square=self.selected_square)
        return self

    def move_down(self) -> "CursorState":
        """Move cursor down one rank (toward rank 1).

        Returns:
            New CursorState with updated position
        """
        if self.position.rank > 1:
            new_pos = Square(file=self.position.file, rank=self.position.rank - 1)
            return CursorState(position=new_pos, selected_square=self.selected_square)
        return self

    def move_left(self) -> "CursorState":
        """Move cursor left one file (toward a-file).

        Returns:
            New CursorState with updated position
        """
        file_idx = ord(self.position.file) - ord('a')
        if file_idx > 0:
            new_file = chr(ord('a') + file_idx - 1)
            new_pos = Square(file=new_file, rank=self.position.rank)
            return CursorState(position=new_pos, selected_square=self.selected_square)
        return self

    def move_right(self) -> "CursorState":
        """Move cursor right one file (toward h-file).

        Returns:
            New CursorState with updated position
        """
        file_idx = ord(self.position.file) - ord('a')
        if file_idx < 7:
            new_file = chr(ord('a') + file_idx + 1)
            new_pos = Square(file=new_file, rank=self.position.rank)
            return CursorState(position=new_pos, selected_square=self.selected_square)
        return self

    def select_square(self) -> "CursorState":
        """Select the square at cursor position, or deselect if already selected.

        Returns:
            New CursorState with updated selection
        """
        if self.selected_square == self.position:
            # Deselect if clicking same square
            return CursorState(position=self.position, selected_square=None)
        else:
            # Select new square
            return CursorState(position=self.position, selected_square=self.position)

    def attempt_move(self) -> Optional[tuple[Square, Square]]:
        """Attempt to make a move from selected square to cursor position.

        Returns:
            Tuple of (from_square, to_square) if a piece is selected and
            cursor is on a different square, None otherwise
        """
        if self.selected_square and self.selected_square != self.position:
            return (self.selected_square, self.position)
        return None

    def cancel_selection(self) -> "CursorState":
        """Cancel current selection.

        Returns:
            New CursorState with no selection
        """
        return CursorState(position=self.position, selected_square=None)

    def clear_selection(self) -> "CursorState":
        """Clear selection (alias for cancel_selection).

        Returns:
            New CursorState with no selection
        """
        return self.cancel_selection()
