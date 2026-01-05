"""Tests for input handler with hint key support."""

import pytest
from unittest.mock import Mock
from pychess.ui.input_handler import InputHandler, InputType, InputEvent


class TestInputHandlerShowHints:
    """Tests for TAB key hint toggling."""

    def test_tab_key_returns_show_hints_event(self):
        """Pressing TAB should return SHOW_HINTS input type."""
        handler = InputHandler()

        # Create a mock key object that simulates TAB
        mock_key = Mock()
        mock_key.name = "KEY_TAB"

        event = handler.process_key(mock_key)
        assert event.input_type == InputType.SHOW_HINTS

    def test_show_hints_input_type_exists(self):
        """InputType enum should have SHOW_HINTS value."""
        assert hasattr(InputType, 'SHOW_HINTS')
        assert InputType.SHOW_HINTS is not None


class TestInputHandlerExistingKeys:
    """Ensure existing key bindings still work."""

    def test_arrow_keys_still_work(self):
        """Arrow keys should still produce movement events."""
        handler = InputHandler()

        for key_name, expected_type in [
            ("KEY_UP", InputType.MOVE_UP),
            ("KEY_DOWN", InputType.MOVE_DOWN),
            ("KEY_LEFT", InputType.MOVE_LEFT),
            ("KEY_RIGHT", InputType.MOVE_RIGHT),
        ]:
            mock_key = Mock()
            mock_key.name = key_name
            event = handler.process_key(mock_key)
            assert event.input_type == expected_type

    def test_enter_key_still_works(self):
        """Enter key should still produce SELECT event."""
        handler = InputHandler()
        mock_key = Mock()
        mock_key.name = "KEY_ENTER"
        event = handler.process_key(mock_key)
        assert event.input_type == InputType.SELECT

    def test_escape_key_still_works(self):
        """Escape key should still produce CANCEL event."""
        handler = InputHandler()
        mock_key = Mock()
        mock_key.name = "KEY_ESCAPE"
        event = handler.process_key(mock_key)
        assert event.input_type == InputType.CANCEL

    def test_command_keys_still_work(self):
        """Command keys (q, u, r, ?, /) should still work."""
        handler = InputHandler()

        for char, expected_type in [
            ('q', InputType.QUIT),
            ('u', InputType.UNDO),
            ('r', InputType.RESTART),
            ('?', InputType.HELP),
            ('/', InputType.TOGGLE_MODE),
        ]:
            mock_key = Mock()
            mock_key.name = None  # Not a special key
            mock_key.__str__ = Mock(return_value=char)
            event = handler.process_key(mock_key)
            assert event.input_type == expected_type
