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
    show_hints: bool = False
    pending_cancel: bool = False

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
            New CursorState with updated position (hints and pending_cancel preserved)
        """
        if self.position.rank < 8:
            new_pos = Square(file=self.position.file, rank=self.position.rank + 1)
            return CursorState(
                position=new_pos,
                selected_square=self.selected_square,
                show_hints=self.show_hints,
                pending_cancel=self.pending_cancel
            )
        return self

    def move_down(self) -> "CursorState":
        """Move cursor down one rank (toward rank 1).

        Returns:
            New CursorState with updated position (hints and pending_cancel preserved)
        """
        if self.position.rank > 1:
            new_pos = Square(file=self.position.file, rank=self.position.rank - 1)
            return CursorState(
                position=new_pos,
                selected_square=self.selected_square,
                show_hints=self.show_hints,
                pending_cancel=self.pending_cancel
            )
        return self

    def move_left(self) -> "CursorState":
        """Move cursor left one file (toward a-file).

        Returns:
            New CursorState with updated position (hints and pending_cancel preserved)
        """
        file_idx = ord(self.position.file) - ord('a')
        if file_idx > 0:
            new_file = chr(ord('a') + file_idx - 1)
            new_pos = Square(file=new_file, rank=self.position.rank)
            return CursorState(
                position=new_pos,
                selected_square=self.selected_square,
                show_hints=self.show_hints,
                pending_cancel=self.pending_cancel
            )
        return self

    def move_right(self) -> "CursorState":
        """Move cursor right one file (toward h-file).

        Returns:
            New CursorState with updated position (hints and pending_cancel preserved)
        """
        file_idx = ord(self.position.file) - ord('a')
        if file_idx < 7:
            new_file = chr(ord('a') + file_idx + 1)
            new_pos = Square(file=new_file, rank=self.position.rank)
            return CursorState(
                position=new_pos,
                selected_square=self.selected_square,
                show_hints=self.show_hints,
                pending_cancel=self.pending_cancel
            )
        return self

    def select_square(self) -> "CursorState":
        """Select the square at cursor position, or deselect if already selected.

        Returns:
            New CursorState with updated selection (hints and pending_cancel cleared)
        """
        if self.selected_square == self.position:
            # Deselect if clicking same square
            return CursorState(
                position=self.position,
                selected_square=None,
                show_hints=False,
                pending_cancel=False
            )
        else:
            # Select new square - clear hints and pending_cancel since selection changed
            return CursorState(
                position=self.position,
                selected_square=self.position,
                show_hints=False,
                pending_cancel=False
            )

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
            New CursorState with no selection (hints and pending_cancel cleared)
        """
        return CursorState(
            position=self.position,
            selected_square=None,
            show_hints=False,
            pending_cancel=False
        )

    def clear_selection(self) -> "CursorState":
        """Clear selection (alias for cancel_selection).

        Returns:
            New CursorState with no selection (hints cleared)
        """
        return self.cancel_selection()

    def toggle_hints(self) -> "CursorState":
        """Toggle hint visibility.

        Returns:
            New CursorState with toggled show_hints
        """
        return CursorState(
            position=self.position,
            selected_square=self.selected_square,
            show_hints=not self.show_hints
        )

    def clear_hints(self) -> "CursorState":
        """Clear hint visibility.

        Returns:
            New CursorState with show_hints=False
        """
        return CursorState(
            position=self.position,
            selected_square=self.selected_square,
            show_hints=False,
            pending_cancel=self.pending_cancel
        )

    def request_cancel(self) -> "CursorState":
        """Request cancellation of current selection.

        If a piece is selected, sets pending_cancel to True.
        If nothing is selected, returns unchanged state.

        Returns:
            New CursorState with pending_cancel set if piece was selected
        """
        if self.selected_square is None:
            # Nothing to cancel
            return self
        return CursorState(
            position=self.position,
            selected_square=self.selected_square,
            show_hints=self.show_hints,
            pending_cancel=True
        )

    def confirm_cancel(self) -> "CursorState":
        """Confirm cancellation and clear selection.

        Returns:
            New CursorState with selection and pending_cancel cleared
        """
        return CursorState(
            position=self.position,
            selected_square=None,
            show_hints=False,
            pending_cancel=False
        )

    def deny_cancel(self) -> "CursorState":
        """Deny cancellation and keep selection.

        Returns:
            New CursorState with pending_cancel cleared but selection kept
        """
        return CursorState(
            position=self.position,
            selected_square=self.selected_square,
            show_hints=self.show_hints,
            pending_cancel=False
        )
