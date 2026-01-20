"""Tests for input handler with hint key and mouse support."""

import pytest
from unittest.mock import Mock
from pychess.ui.input_handler import InputHandler, InputType, InputEvent


class TestInputHandlerMouseEvents:
    """Tests for mouse event handling."""

    def test_mouse_click_input_type_exists(self):
        """InputType enum should have MOUSE_CLICK value."""
        assert hasattr(InputType, 'MOUSE_CLICK')
        assert InputType.MOUSE_CLICK is not None

    def test_mouse_release_input_type_exists(self):
        """InputType enum should have MOUSE_RELEASE value."""
        assert hasattr(InputType, 'MOUSE_RELEASE')
        assert InputType.MOUSE_RELEASE is not None

    def test_input_event_has_mouse_coords(self):
        """InputEvent should support mouse_x and mouse_y coordinates."""
        event = InputEvent(
            input_type=InputType.MOUSE_CLICK,
            data=None,
            mouse_x=10,
            mouse_y=20
        )
        assert event.mouse_x == 10
        assert event.mouse_y == 20

    def test_input_event_mouse_coords_default_to_none(self):
        """InputEvent mouse coordinates should default to None."""
        event = InputEvent(input_type=InputType.SELECT)
        assert event.mouse_x is None
        assert event.mouse_y is None

    def test_process_key_detects_mouse_left_click(self):
        """Left mouse click should produce MOUSE_CLICK event with coordinates."""
        handler = InputHandler()

        mock_key = Mock()
        mock_key.name = "MOUSE_LEFT"
        mock_key.mouse_xy = (15, 10)
        mock_key.released = False

        event = handler.process_key(mock_key)
        assert event.input_type == InputType.MOUSE_CLICK
        assert event.mouse_x == 15
        assert event.mouse_y == 10

    def test_process_key_detects_mouse_release(self):
        """Mouse button release should produce MOUSE_RELEASE event."""
        handler = InputHandler()

        mock_key = Mock()
        mock_key.name = "MOUSE_LEFT_RELEASED"
        mock_key.mouse_xy = (20, 15)
        mock_key.released = True

        event = handler.process_key(mock_key)
        assert event.input_type == InputType.MOUSE_RELEASE
        assert event.mouse_x == 20
        assert event.mouse_y == 15

    def test_process_key_ignores_scroll_events(self):
        """Scroll wheel events should be ignored (return UNKNOWN)."""
        handler = InputHandler()

        mock_key = Mock()
        mock_key.name = "MOUSE_SCROLL_UP"
        mock_key.mouse_xy = (10, 10)
        mock_key.released = False

        event = handler.process_key(mock_key)
        assert event.input_type == InputType.UNKNOWN

    def test_process_key_ignores_right_click(self):
        """Right mouse click should be ignored (return UNKNOWN)."""
        handler = InputHandler()

        mock_key = Mock()
        mock_key.name = "MOUSE_RIGHT"
        mock_key.mouse_xy = (10, 10)
        mock_key.released = False

        event = handler.process_key(mock_key)
        assert event.input_type == InputType.UNKNOWN


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
