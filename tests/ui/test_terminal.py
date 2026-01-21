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
