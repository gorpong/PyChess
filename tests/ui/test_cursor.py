"""Tests for cursor state management with hint and mouse functionality."""

import pytest
from pychess.model.square import Square
from pychess.ui.cursor import CursorState


class TestCursorStateMouseSupport:
    """Tests for mouse-related cursor functionality."""

    def test_move_to_sets_cursor_position(self):
        """move_to() should move cursor directly to the specified square."""
        cursor = CursorState.initial()
        target = Square(file="d", rank=5)
        
        cursor = cursor.move_to(target)
        
        assert cursor.position == target

    def test_move_to_preserves_selection(self):
        """move_to() should preserve the current selection."""
        cursor = CursorState.initial()
        cursor = cursor.select_square()  # Select e2
        selected = cursor.selected_square
        
        target = Square(file="f", rank=4)
        cursor = cursor.move_to(target)
        
        assert cursor.position == target
        assert cursor.selected_square == selected

    def test_move_to_preserves_hints(self):
        """move_to() should preserve hint visibility."""
        cursor = CursorState.initial()
        cursor = cursor.toggle_hints()
        assert cursor.show_hints is True
        
        target = Square(file="g", rank=7)
        cursor = cursor.move_to(target)
        
        assert cursor.show_hints is True

    def test_move_to_preserves_pending_cancel(self):
        """move_to() should preserve pending_cancel state."""
        cursor = CursorState.initial()
        cursor = cursor.select_square()
        cursor = cursor.request_cancel()
        assert cursor.pending_cancel is True
        
        target = Square(file="a", rank=1)
        cursor = cursor.move_to(target)
        
        assert cursor.pending_cancel is True

    def test_move_to_works_for_all_squares(self):
        """move_to() should work for any valid square."""
        cursor = CursorState.initial()
        
        # Test corners
        for file, rank in [("a", 1), ("a", 8), ("h", 1), ("h", 8)]:
            target = Square(file=file, rank=rank)
            new_cursor = cursor.move_to(target)
            assert new_cursor.position == target

    def test_move_to_same_square_no_change(self):
        """move_to() to current position should return equivalent state."""
        cursor = CursorState.initial()
        original_pos = cursor.position
        
        cursor = cursor.move_to(original_pos)
        
        assert cursor.position == original_pos


class TestCursorStateHints:
    """Tests for cursor hint visibility management."""

    def test_initial_state_hints_hidden(self):
        """Initial cursor state should have hints disabled."""
        cursor = CursorState.initial()
        assert cursor.show_hints is False

    def test_toggle_hints_enables_when_disabled(self):
        """Toggling hints when disabled should enable them."""
        cursor = CursorState.initial()
        cursor = cursor.toggle_hints()
        assert cursor.show_hints is True

    def test_toggle_hints_disables_when_enabled(self):
        """Toggling hints when enabled should disable them."""
        cursor = CursorState.initial()
        cursor = cursor.toggle_hints()  # Enable
        cursor = cursor.toggle_hints()  # Disable
        assert cursor.show_hints is False

    def test_clear_hints(self):
        """Clear hints should disable hint visibility."""
        cursor = CursorState.initial()
        cursor = cursor.toggle_hints()  # Enable
        assert cursor.show_hints is True
        cursor = cursor.clear_hints()
        assert cursor.show_hints is False

    def test_clear_hints_when_already_hidden(self):
        """Clear hints when already hidden should remain hidden."""
        cursor = CursorState.initial()
        cursor = cursor.clear_hints()
        assert cursor.show_hints is False

    def test_hints_cleared_on_selection_change(self):
        """Hints should be cleared when selection changes."""
        cursor = CursorState.initial()
        cursor = cursor.toggle_hints()
        assert cursor.show_hints is True

        # Selecting a square should clear hints
        cursor = cursor.select_square()
        assert cursor.show_hints is False

    def test_hints_cleared_on_cancel_selection(self):
        """Hints should be cleared when selection is cancelled."""
        cursor = CursorState.initial()
        cursor = cursor.select_square()
        cursor = cursor.toggle_hints()
        assert cursor.show_hints is True

        cursor = cursor.cancel_selection()
        assert cursor.show_hints is False

    def test_hints_preserved_during_cursor_movement(self):
        """Hints should remain visible during cursor movement."""
        cursor = CursorState.initial()
        cursor = cursor.toggle_hints()
        assert cursor.show_hints is True

        # Move cursor around - hints should stay
        cursor = cursor.move_up()
        assert cursor.show_hints is True

        cursor = cursor.move_left()
        assert cursor.show_hints is True

        cursor = cursor.move_down()
        assert cursor.show_hints is True

        cursor = cursor.move_right()
        assert cursor.show_hints is True

    def test_show_hints_field_in_constructor(self):
        """CursorState should accept show_hints in constructor."""
        cursor = CursorState(
            position=Square(file="e", rank=4),
            selected_square=Square(file="e", rank=2),
            show_hints=True
        )
        assert cursor.show_hints is True
        assert cursor.position == Square(file="e", rank=4)
        assert cursor.selected_square == Square(file="e", rank=2)
