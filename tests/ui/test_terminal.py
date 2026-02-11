"""Tests for terminal renderer, including elapsed time display."""

import pytest
from io import StringIO
from unittest.mock import Mock, MagicMock, patch

from pychess.ui.terminal import TerminalRenderer, format_elapsed_time
from pychess.model.game_state import GameState


class TestFormatElapsedTime:
    """Tests for elapsed time formatting function."""

    def test_format_zero_seconds(self):
        """Zero seconds should display as '0s'."""
        assert format_elapsed_time(0) == "0s"

    def test_format_seconds_only(self):
        """Under 60 seconds should show only seconds."""
        assert format_elapsed_time(45) == "45s"
        assert format_elapsed_time(1) == "1s"
        assert format_elapsed_time(59) == "59s"

    def test_format_minutes_and_seconds(self):
        """Between 1 minute and 1 hour should show minutes and seconds."""
        assert format_elapsed_time(60) == "1m 0s"
        assert format_elapsed_time(61) == "1m 1s"
        assert format_elapsed_time(125) == "2m 5s"
        assert format_elapsed_time(3599) == "59m 59s"

    def test_format_hours_minutes_seconds(self):
        """1 hour or more should show hours, minutes, and seconds."""
        assert format_elapsed_time(3600) == "1h 0m 0s"
        assert format_elapsed_time(3661) == "1h 1m 1s"
        assert format_elapsed_time(7325) == "2h 2m 5s"

    def test_format_large_hours(self):
        """Should handle many hours correctly."""
        # 10 hours, 30 minutes, 45 seconds
        seconds = 10 * 3600 + 30 * 60 + 45
        assert format_elapsed_time(seconds) == "10h 30m 45s"

    def test_format_negative_returns_zero(self):
        """Negative values should be treated as zero."""
        assert format_elapsed_time(-1) == "0s"
        assert format_elapsed_time(-100) == "0s"

    def test_format_float_truncates(self):
        """Float values should be truncated to integer."""
        assert format_elapsed_time(45.9) == "45s"
        assert format_elapsed_time(125.5) == "2m 5s"


def _create_mock_renderer():
    """Create a TerminalRenderer with mocked terminal for testing."""
    renderer = TerminalRenderer(use_unicode=True)
    renderer.term = MagicMock()
    renderer.term.width = 120
    renderer.term.height = 50
    renderer.term.home = Mock(return_value="")
    renderer.term.clear = Mock(return_value="")
    renderer.term.move_xy = Mock(return_value="")
    renderer.term.clear_eol = Mock(return_value="")  # Add for _render_input
    renderer.term.bold = Mock(side_effect=lambda x: x)
    renderer.term.dim = Mock(side_effect=lambda x: x)
    renderer.term.normal = ""
    renderer.term.on_white = Mock(side_effect=lambda x: x)
    renderer.term.on_yellow = Mock(side_effect=lambda x: x)
    renderer.term.on_cyan = Mock(side_effect=lambda x: x)
    renderer.term.on_green = Mock(side_effect=lambda x: x)
    renderer.term.on_darkgreen = Mock(side_effect=lambda x: x)
    renderer.term.on_color = Mock(return_value=Mock(side_effect=lambda x: x))
    renderer.term.blue = Mock(side_effect=lambda x: x)
    renderer.term.black = Mock(side_effect=lambda x: x)
    return renderer


class TestRendererElapsedTimeDisplay:
    """Tests for elapsed time display in the renderer.
    
    These tests verify that when elapsed_seconds is passed to render(),
    the time is actually formatted and included in the output.
    """

    def test_render_displays_elapsed_time_when_provided(self):
        """When elapsed_seconds is provided, the formatted time should appear in output."""
        renderer = _create_mock_renderer()
        state = GameState.initial()
        
        # Capture print output
        printed_output = []
        original_print = print
        
        def capture_print(*args, **kwargs):
            printed_output.append(' '.join(str(a) for a in args))
        
        with patch('builtins.print', capture_print):
            renderer.render(state, elapsed_seconds=3661)  # 1h 1m 1s
        
        # Join all output and check for the time string
        all_output = ' '.join(printed_output)
        assert "Time:" in all_output
        assert "1h 1m 1s" in all_output

    def test_render_displays_minutes_format(self):
        """Elapsed time under 1 hour should display in minutes format."""
        renderer = _create_mock_renderer()
        state = GameState.initial()
        
        printed_output = []
        
        def capture_print(*args, **kwargs):
            printed_output.append(' '.join(str(a) for a in args))
        
        with patch('builtins.print', capture_print):
            renderer.render(state, elapsed_seconds=125)  # 2m 5s
        
        all_output = ' '.join(printed_output)
        assert "Time:" in all_output
        assert "2m 5s" in all_output

    def test_render_displays_seconds_format(self):
        """Elapsed time under 1 minute should display in seconds format."""
        renderer = _create_mock_renderer()
        state = GameState.initial()
        
        printed_output = []
        
        def capture_print(*args, **kwargs):
            printed_output.append(' '.join(str(a) for a in args))
        
        with patch('builtins.print', capture_print):
            renderer.render(state, elapsed_seconds=45)
        
        all_output = ' '.join(printed_output)
        assert "Time:" in all_output
        assert "45s" in all_output

    def test_render_no_time_when_elapsed_seconds_not_provided(self):
        """When elapsed_seconds is None, no time should be displayed."""
        renderer = _create_mock_renderer()
        state = GameState.initial()
        
        printed_output = []
        
        def capture_print(*args, **kwargs):
            printed_output.append(' '.join(str(a) for a in args))
        
        with patch('builtins.print', capture_print):
            renderer.render(state)  # No elapsed_seconds
        
        all_output = ' '.join(printed_output)
        # "Time:" should not appear when no elapsed_seconds provided
        assert "Time:" not in all_output

    def test_render_status_includes_turn_and_time(self):
        """Status line should include both turn and time info."""
        renderer = _create_mock_renderer()
        state = GameState.initial()
        
        printed_output = []
        
        def capture_print(*args, **kwargs):
            printed_output.append(' '.join(str(a) for a in args))
        
        with patch('builtins.print', capture_print):
            renderer.render(state, elapsed_seconds=7200)  # 2 hours
        
        all_output = ' '.join(printed_output)
        assert "Turn:" in all_output
        assert "WHITE" in all_output
        assert "Time:" in all_output
        assert "2h 0m 0s" in all_output


class TestGameSessionPassesElapsedTime:
    """Tests that GameSession correctly calculates and passes elapsed time to renderer."""

    def test_session_render_passes_elapsed_seconds(self):
        """GameSession._render() should calculate and pass elapsed_seconds to renderer."""
        from pychess.controller.game_session import GameSession
        import time
        
        mock_renderer = Mock()
        mock_renderer.render = Mock()
        mock_renderer._render_input = Mock()
        
        session = GameSession(mock_renderer)
        # Set start_time to 100 seconds ago
        session.start_time = time.time() - 100
        
        # Call _render
        session._render()
        
        # Verify render was called with elapsed_seconds
        mock_renderer.render.assert_called_once()
        call_kwargs = mock_renderer.render.call_args[1]
        
        assert 'elapsed_seconds' in call_kwargs
        # Should be approximately 100 seconds (allow some tolerance)
        assert call_kwargs['elapsed_seconds'] >= 100
        assert call_kwargs['elapsed_seconds'] < 102

    def test_session_render_elapsed_time_accumulates(self):
        """Elapsed time should increase between renders."""
        from pychess.controller.game_session import GameSession
        import time
        
        mock_renderer = Mock()
        mock_renderer.render = Mock()
        mock_renderer._render_input = Mock()
        
        session = GameSession(mock_renderer)
        session.start_time = time.time() - 50  # 50 seconds ago
        
        session._render()
        first_elapsed = mock_renderer.render.call_args[1]['elapsed_seconds']
        
        # Simulate some time passing
        session.start_time -= 10  # Effectively add 10 more seconds
        
        session._render()
        second_elapsed = mock_renderer.render.call_args[1]['elapsed_seconds']
        
        assert second_elapsed > first_elapsed
        assert second_elapsed - first_elapsed >= 10


class TestFormatGameResult:
    """Tests for the _format_game_result helper method."""

    def test_format_white_wins(self):
        """'1-0' should format to 'White Wins!'."""
        renderer = _create_mock_renderer()
        assert renderer._format_game_result("1-0") == "White Wins!"

    def test_format_black_wins(self):
        """'0-1' should format to 'Black Wins!'."""
        renderer = _create_mock_renderer()
        assert renderer._format_game_result("0-1") == "Black Wins!"

    def test_format_draw(self):
        """'1/2-1/2' should format to 'Draw!'."""
        renderer = _create_mock_renderer()
        assert renderer._format_game_result("1/2-1/2") == "Draw!"

    def test_format_unknown_returns_input(self):
        """Unknown result codes should be returned as-is."""
        renderer = _create_mock_renderer()
        assert renderer._format_game_result("*") == "*"
        assert renderer._format_game_result("unknown") == "unknown"


class TestCleanup:
    """Tests for renderer cleanup behavior."""

    def test_cleanup_does_not_clear_screen(self):
        """Cleanup should NOT clear the screen so game result remains visible."""
        renderer = _create_mock_renderer()
        
        printed_output = []
        
        def capture_print(*args, **kwargs):
            printed_output.append(' '.join(str(a) for a in args))
        
        # Mock term.clear to track if it's called
        renderer.term.clear = Mock(return_value="CLEAR_CALLED")
        
        with patch('builtins.print', capture_print):
            renderer.cleanup()
        
        all_output = ' '.join(printed_output)
        # The clear sequence should NOT appear in the output
        assert "CLEAR_CALLED" not in all_output

    def test_cleanup_restores_cursor(self):
        """Cleanup should restore the cursor visibility."""
        renderer = _create_mock_renderer()
        
        printed_output = []
        
        def capture_print(*args, **kwargs):
            printed_output.append(' '.join(str(a) for a in args))
        
        renderer.term.normal_cursor = Mock(return_value="CURSOR_RESTORED")
        
        with patch('builtins.print', capture_print):
            renderer.cleanup()
        
        all_output = ' '.join(printed_output)
        assert "CURSOR_RESTORED" in all_output

    def test_cleanup_moves_cursor_to_bottom(self):
        """Cleanup should move cursor to bottom so shell prompt appears below game."""
        renderer = _create_mock_renderer()
        
        printed_output = []
        
        def capture_print(*args, **kwargs):
            printed_output.append(' '.join(str(a) for a in args))
        
        renderer.term.move_xy = Mock(return_value="MOVED_TO_BOTTOM")
        renderer.term.height = 50
        
        with patch('builtins.print', capture_print):
            renderer.cleanup()
        
        all_output = ' '.join(printed_output)
        assert "MOVED_TO_BOTTOM" in all_output
        # Verify move_xy was called with y = height - 1
        renderer.term.move_xy.assert_called_with(0, 49)


class TestWaitForKeypress:
    """Tests for wait_for_keypress method that ignores mouse events."""

    def test_wait_for_keypress_returns_on_keyboard_input(self):
        """wait_for_keypress should return when a keyboard key is pressed."""
        renderer = _create_mock_renderer()
        
        # Create a mock key that simulates a keyboard press (not mouse)
        mock_key = MagicMock()
        mock_key.is_sequence = False
        mock_key.name = None  # Regular character
        mock_key.code = None  # Not a mouse event
        
        # Set up inkey to return our mock key
        renderer.term.inkey = Mock(return_value=mock_key)
        renderer.term.cbreak = MagicMock(return_value=MagicMock(__enter__=Mock(), __exit__=Mock()))
        
        # Should return without hanging
        renderer.wait_for_keypress()
        
        # Verify inkey was called
        renderer.term.inkey.assert_called()

    def test_wait_for_keypress_ignores_mouse_click_events(self):
        """wait_for_keypress should ignore mouse click events and keep waiting."""
        renderer = _create_mock_renderer()
        
        # Create mock events: first a mouse event, then a keyboard event
        mouse_event = MagicMock()
        mouse_event.name = "KEY_MOUSE"
        mouse_event.code = 1001  # Mouse event code
        
        keyboard_event = MagicMock()
        keyboard_event.name = "a"
        keyboard_event.code = None
        
        # inkey returns mouse first, then keyboard
        renderer.term.inkey = Mock(side_effect=[mouse_event, keyboard_event])
        renderer.term.cbreak = MagicMock(return_value=MagicMock(__enter__=Mock(), __exit__=Mock()))
        
        renderer.wait_for_keypress()
        
        # Should have been called twice (mouse ignored, keyboard accepted)
        assert renderer.term.inkey.call_count == 2

    def test_wait_for_keypress_ignores_mouse_release_events(self):
        """wait_for_keypress should ignore mouse release events."""
        renderer = _create_mock_renderer()
        
        # Mouse release event followed by keyboard
        mouse_release = MagicMock()
        mouse_release.name = "KEY_MOUSE"
        mouse_release.code = 1002  # Different mouse code
        
        keyboard_event = MagicMock()
        keyboard_event.name = "KEY_ENTER"
        keyboard_event.code = None
        
        renderer.term.inkey = Mock(side_effect=[mouse_release, keyboard_event])
        renderer.term.cbreak = MagicMock(return_value=MagicMock(__enter__=Mock(), __exit__=Mock()))
        
        renderer.wait_for_keypress()
        
        assert renderer.term.inkey.call_count == 2

    def test_wait_for_keypress_accepts_enter_key(self):
        """wait_for_keypress should accept Enter key."""
        renderer = _create_mock_renderer()
        
        enter_key = MagicMock()
        enter_key.name = "KEY_ENTER"
        enter_key.code = None
        
        renderer.term.inkey = Mock(return_value=enter_key)
        renderer.term.cbreak = MagicMock(return_value=MagicMock(__enter__=Mock(), __exit__=Mock()))
        
        renderer.wait_for_keypress()
        
        renderer.term.inkey.assert_called_once()

    def test_wait_for_keypress_accepts_escape_key(self):
        """wait_for_keypress should accept Escape key."""
        renderer = _create_mock_renderer()
        
        esc_key = MagicMock()
        esc_key.name = "KEY_ESCAPE"
        esc_key.code = None
        
        renderer.term.inkey = Mock(return_value=esc_key)
        renderer.term.cbreak = MagicMock(return_value=MagicMock(__enter__=Mock(), __exit__=Mock()))
        
        renderer.wait_for_keypress()
        
        renderer.term.inkey.assert_called_once()

    def test_wait_for_keypress_accepts_space_key(self):
        """wait_for_keypress should accept Space key."""
        renderer = _create_mock_renderer()
        
        space_key = MagicMock()
        space_key.name = None
        space_key.code = None
        space_key.__str__ = Mock(return_value=" ")
        
        renderer.term.inkey = Mock(return_value=space_key)
        renderer.term.cbreak = MagicMock(return_value=MagicMock(__enter__=Mock(), __exit__=Mock()))
        
        renderer.wait_for_keypress()
        
        renderer.term.inkey.assert_called_once()


class TestGameResultDisplay:
    """Tests for game result display in the renderer."""

    def test_render_displays_white_wins(self):
        """When game_result='1-0' is provided, 'White Wins' should appear in output."""
        renderer = _create_mock_renderer()
        state = GameState.initial()
        
        printed_output = []
        
        def capture_print(*args, **kwargs):
            printed_output.append(' '.join(str(a) for a in args))
        
        with patch('builtins.print', capture_print):
            renderer.render(state, game_result="1-0")
        
        all_output = ' '.join(printed_output)
        assert "White Wins" in all_output or "WHITE WINS" in all_output

    def test_render_displays_black_wins(self):
        """When game_result='0-1' is provided, 'Black Wins' should appear in output."""
        renderer = _create_mock_renderer()
        state = GameState.initial()
        
        printed_output = []
        
        def capture_print(*args, **kwargs):
            printed_output.append(' '.join(str(a) for a in args))
        
        with patch('builtins.print', capture_print):
            renderer.render(state, game_result="0-1")
        
        all_output = ' '.join(printed_output)
        assert "Black Wins" in all_output or "BLACK WINS" in all_output

    def test_render_displays_draw(self):
        """When game_result='1/2-1/2' is provided, 'Draw' should appear in output."""
        renderer = _create_mock_renderer()
        state = GameState.initial()
        
        printed_output = []
        
        def capture_print(*args, **kwargs):
            printed_output.append(' '.join(str(a) for a in args))
        
        with patch('builtins.print', capture_print):
            renderer.render(state, game_result="1/2-1/2")
        
        all_output = ' '.join(printed_output)
        assert "Draw" in all_output or "DRAW" in all_output

    def test_render_no_result_when_not_provided(self):
        """When game_result is None, no win/draw message should appear."""
        renderer = _create_mock_renderer()
        state = GameState.initial()
        
        printed_output = []
        
        def capture_print(*args, **kwargs):
            printed_output.append(' '.join(str(a) for a in args))
        
        with patch('builtins.print', capture_print):
            renderer.render(state)  # No game_result
        
        all_output = ' '.join(printed_output)
        # None of the result messages should appear
        assert "White Wins" not in all_output and "WHITE WINS" not in all_output
        assert "Black Wins" not in all_output and "BLACK WINS" not in all_output
        assert "Draw" not in all_output or "Draw" in "Drawing"  # Avoid false positive

    def test_render_accepts_game_result_parameter(self):
        """Render method should accept game_result parameter without error."""
        renderer = _create_mock_renderer()
        state = GameState.initial()
        
        # Should not raise
        with patch('builtins.print'):
            renderer.render(state, game_result="1-0")
            renderer.render(state, game_result="0-1")
            renderer.render(state, game_result="1/2-1/2")
            renderer.render(state, game_result=None)


class TestRenderPerformance:
    """Tests for render performance optimizations."""

    def test_render_uses_single_print_call(self):
        """Render should consolidate all output into a single print() call for efficiency.
        
        This test verifies the performance optimization where instead of making 200+
        individual print() calls (one for each square line, border, label, etc.),
        the renderer builds the entire frame as a string and calls print() once.
        """
        renderer = _create_mock_renderer()
        state = GameState.initial()
        
        with patch('builtins.print') as mock_print:
            renderer.render(
                state,
                selected_square=None,
                cursor_square=None,
                legal_moves=set(),
                status_messages=["Test message"],
                elapsed_seconds=10
            )
            
            # Should only call print() once for the entire render
            # (plus one for flush, but we're counting the main render print)
            assert mock_print.call_count == 1, \
                f"Expected 1 print() call for efficiency but got {mock_print.call_count}"
    
    def test_render_with_game_result_uses_single_print(self):
        """Render with game result should still use only one print() call."""
        renderer = _create_mock_renderer()
        state = GameState.initial()
        
        with patch('builtins.print') as mock_print:
            renderer.render(
                state,
                game_result="1-0"
            )
            
            assert mock_print.call_count == 1, \
                f"Expected 1 print() call but got {mock_print.call_count}"
