"""Tests for GameSession controller."""

import pytest
from unittest.mock import Mock, MagicMock, patch, call

from pychess.controller.game_session import GameSession
from pychess.model.game_state import GameState
from pychess.model.piece import Color, Piece
from pychess.model.square import Square
from pychess.ui.cursor import CursorState
from pychess.ui.input_handler import InputType, InputEvent
from pychess.ai.engine import AIEngine, Difficulty


class TestGameSessionInit:
    """Tests for GameSession initialization."""

    def test_creates_initial_game_state(self):
        """GameSession should start with initial game state."""
        renderer = Mock()
        session = GameSession(renderer)
        
        assert session.game_state.fullmove_number == 1
        assert session.game_state.active_color == Color.WHITE

    def test_start_time_is_set(self):
        """GameSession should record start time."""
        import time
        renderer = Mock()
        before = time.time()
        session = GameSession(renderer)
        after = time.time()
        
        assert before <= session.start_time <= after

    def test_creates_initial_cursor_state(self):
        """GameSession should start with cursor at e2."""
        renderer = Mock()
        session = GameSession(renderer)
        
        assert session.cursor_state.position == Square(file="e", rank=2)
        assert session.cursor_state.selected_square is None

    def test_starts_in_cursor_mode(self):
        """GameSession should start in cursor input mode."""
        renderer = Mock()
        session = GameSession(renderer)
        
        assert session.input_mode == "cursor"

    def test_empty_state_history(self):
        """GameSession should start with empty state history."""
        renderer = Mock()
        session = GameSession(renderer)
        
        assert session.state_history == []

    def test_stores_ai_engine(self):
        """GameSession should store AI engine if provided."""
        renderer = Mock()
        ai_engine = AIEngine(Difficulty.EASY)
        session = GameSession(renderer, ai_engine)
        
        assert session.ai_engine is ai_engine

    def test_no_ai_engine_for_multiplayer(self):
        """GameSession should have no AI engine for multiplayer."""
        renderer = Mock()
        session = GameSession(renderer, ai_engine=None)
        
        assert session.ai_engine is None

    def test_hints_allowed_for_easy_ai(self):
        """Hints should be allowed for Easy AI mode."""
        renderer = Mock()
        ai_engine = AIEngine(Difficulty.EASY)
        session = GameSession(renderer, ai_engine)
        
        assert session.hints_allowed is True

    def test_hints_allowed_for_medium_ai(self):
        """Hints should be allowed for Medium AI mode."""
        renderer = Mock()
        ai_engine = AIEngine(Difficulty.MEDIUM)
        session = GameSession(renderer, ai_engine)
        
        assert session.hints_allowed is True

    def test_hints_not_allowed_for_hard_ai(self):
        """Hints should not be allowed for Hard AI mode."""
        renderer = Mock()
        ai_engine = AIEngine(Difficulty.HARD)
        session = GameSession(renderer, ai_engine)
        
        assert session.hints_allowed is False

    def test_hints_not_allowed_for_multiplayer(self):
        """Hints should not be allowed for multiplayer."""
        renderer = Mock()
        session = GameSession(renderer, ai_engine=None)
        
        assert session.hints_allowed is False

    def test_is_multiplayer_true_when_no_ai(self):
        """is_multiplayer should be True when no AI engine."""
        renderer = Mock()
        session = GameSession(renderer, ai_engine=None)
        
        assert session.is_multiplayer is True

    def test_is_multiplayer_false_when_ai(self):
        """is_multiplayer should be False when AI engine present."""
        renderer = Mock()
        ai_engine = AIEngine(Difficulty.EASY)
        session = GameSession(renderer, ai_engine)
        
        assert session.is_multiplayer is False


class TestCursorMovement:
    """Tests for cursor movement handlers."""

    def test_handle_move_up(self):
        """MOVE_UP should move cursor up one rank."""
        renderer = Mock()
        session = GameSession(renderer)
        session.cursor_state = CursorState(position=Square(file="e", rank=4))
        
        session.handle_input(InputEvent(InputType.MOVE_UP))
        
        assert session.cursor_state.position == Square(file="e", rank=5)

    def test_handle_move_down(self):
        """MOVE_DOWN should move cursor down one rank."""
        renderer = Mock()
        session = GameSession(renderer)
        session.cursor_state = CursorState(position=Square(file="e", rank=4))
        
        session.handle_input(InputEvent(InputType.MOVE_DOWN))
        
        assert session.cursor_state.position == Square(file="e", rank=3)

    def test_handle_move_left(self):
        """MOVE_LEFT should move cursor left one file."""
        renderer = Mock()
        session = GameSession(renderer)
        session.cursor_state = CursorState(position=Square(file="e", rank=4))
        
        session.handle_input(InputEvent(InputType.MOVE_LEFT))
        
        assert session.cursor_state.position == Square(file="d", rank=4)

    def test_handle_move_right(self):
        """MOVE_RIGHT should move cursor right one file."""
        renderer = Mock()
        session = GameSession(renderer)
        session.cursor_state = CursorState(position=Square(file="e", rank=4))
        
        session.handle_input(InputEvent(InputType.MOVE_RIGHT))
        
        assert session.cursor_state.position == Square(file="f", rank=4)


class TestPieceSelection:
    """Tests for piece selection logic."""

    def test_select_own_piece(self):
        """Selecting own piece should set selected_square."""
        renderer = Mock()
        renderer.show_error = Mock()
        session = GameSession(renderer)
        # Cursor on e2 (white pawn)
        session.cursor_state = CursorState(position=Square(file="e", rank=2))
        
        session.handle_input(InputEvent(InputType.SELECT))
        
        assert session.cursor_state.selected_square == Square(file="e", rank=2)

    def test_select_opponent_piece_shows_error(self):
        """Selecting opponent's piece should show error."""
        renderer = Mock()
        renderer.show_error = Mock()
        session = GameSession(renderer)
        # Cursor on e7 (black pawn)
        session.cursor_state = CursorState(position=Square(file="e", rank=7))
        
        session.handle_input(InputEvent(InputType.SELECT))
        
        renderer.show_error.assert_called_once_with("Not your piece!")
        assert session.cursor_state.selected_square is None

    def test_select_empty_square_clears_selection(self):
        """Selecting empty square should clear selection."""
        renderer = Mock()
        session = GameSession(renderer)
        session.cursor_state = CursorState(
            position=Square(file="e", rank=4),
            selected_square=Square(file="e", rank=2)
        )
        
        session.handle_input(InputEvent(InputType.SELECT))
        
        assert session.cursor_state.selected_square is None


class TestMoveExecution:
    """Tests for move execution."""

    def test_valid_move_updates_game_state(self):
        """Valid move should update game state."""
        renderer = Mock()
        session = GameSession(renderer)
        # Select e2 pawn
        session.cursor_state = CursorState(
            position=Square(file="e", rank=4),
            selected_square=Square(file="e", rank=2)
        )
        
        session.handle_input(InputEvent(InputType.SELECT))
        
        # Pawn should have moved
        assert session.game_state.board.get(Square(file="e", rank=4)) is not None
        assert session.game_state.board.get(Square(file="e", rank=2)) is None
        assert session.game_state.active_color == Color.BLACK

    def test_valid_move_saves_to_history(self):
        """Valid move should save previous state to history."""
        renderer = Mock()
        session = GameSession(renderer)
        initial_state = session.game_state
        
        # Select and move e2 pawn to e4
        session.cursor_state = CursorState(
            position=Square(file="e", rank=4),
            selected_square=Square(file="e", rank=2)
        )
        session.handle_input(InputEvent(InputType.SELECT))
        
        assert len(session.state_history) == 1
        assert session.state_history[0] is initial_state

    def test_valid_move_clears_selection(self):
        """Valid move should clear selection."""
        renderer = Mock()
        session = GameSession(renderer)
        session.cursor_state = CursorState(
            position=Square(file="e", rank=4),
            selected_square=Square(file="e", rank=2)
        )
        
        session.handle_input(InputEvent(InputType.SELECT))
        
        assert session.cursor_state.selected_square is None

    def test_invalid_move_shows_error(self):
        """Invalid move should show error."""
        renderer = Mock()
        renderer.show_error = Mock()
        session = GameSession(renderer)
        # Try to move pawn to e5 (illegal - can only go to e3 or e4)
        session.cursor_state = CursorState(
            position=Square(file="e", rank=5),
            selected_square=Square(file="e", rank=2)
        )
        
        session.handle_input(InputEvent(InputType.SELECT))
        
        renderer.show_error.assert_called_once_with("Illegal move")

    def test_invalid_move_clears_selection(self):
        """Invalid move should clear selection."""
        renderer = Mock()
        renderer.show_error = Mock()
        session = GameSession(renderer)
        session.cursor_state = CursorState(
            position=Square(file="e", rank=5),
            selected_square=Square(file="e", rank=2)
        )
        
        session.handle_input(InputEvent(InputType.SELECT))
        
        assert session.cursor_state.selected_square is None


class TestAIIntegration:
    """Tests for AI move execution."""

    def test_ai_moves_after_player(self):
        """AI should move after player's move."""
        renderer = Mock()
        ai_engine = AIEngine(Difficulty.EASY, seed=42)
        session = GameSession(renderer, ai_engine)
        
        # Player moves e2-e4
        session.cursor_state = CursorState(
            position=Square(file="e", rank=4),
            selected_square=Square(file="e", rank=2)
        )
        session.handle_input(InputEvent(InputType.SELECT))
        
        # After AI moves, it should be white's turn again
        assert session.game_state.active_color == Color.WHITE
        # State history should have 2 entries (player move + AI move)
        assert len(session.state_history) == 2

    def test_no_ai_move_in_multiplayer(self):
        """No AI move should occur in multiplayer mode."""
        renderer = Mock()
        session = GameSession(renderer, ai_engine=None)
        
        # Player moves e2-e4
        session.cursor_state = CursorState(
            position=Square(file="e", rank=4),
            selected_square=Square(file="e", rank=2)
        )
        session.handle_input(InputEvent(InputType.SELECT))
        
        # Should be black's turn (no AI)
        assert session.game_state.active_color == Color.BLACK
        assert len(session.state_history) == 1


class TestUndo:
    """Tests for undo functionality."""

    def test_undo_restores_previous_state(self):
        """Undo should restore previous game state."""
        renderer = Mock()
        session = GameSession(renderer)
        initial_state = session.game_state
        
        # Make a move
        session.cursor_state = CursorState(
            position=Square(file="e", rank=4),
            selected_square=Square(file="e", rank=2)
        )
        session.handle_input(InputEvent(InputType.SELECT))
        
        # Undo
        session.handle_input(InputEvent(InputType.UNDO))
        
        assert session.game_state is initial_state
        assert session.state_history == []

    def test_undo_clears_selection(self):
        """Undo should clear cursor selection."""
        renderer = Mock()
        session = GameSession(renderer)
        
        # Make a move
        session.cursor_state = CursorState(
            position=Square(file="e", rank=4),
            selected_square=Square(file="e", rank=2)
        )
        session.handle_input(InputEvent(InputType.SELECT))
        
        # Select another piece then undo
        session.cursor_state = CursorState(
            position=Square(file="d", rank=2),
            selected_square=Square(file="d", rank=2)
        )
        session.handle_input(InputEvent(InputType.UNDO))
        
        assert session.cursor_state.selected_square is None

    def test_undo_with_empty_history_shows_error(self):
        """Undo with empty history should show error."""
        renderer = Mock()
        renderer.show_error = Mock()
        session = GameSession(renderer)
        
        session.handle_input(InputEvent(InputType.UNDO))
        
        renderer.show_error.assert_called_once_with("No moves to undo")


class TestRestart:
    """Tests for restart functionality."""

    def test_restart_requires_confirmation(self):
        """Restart should require confirmation before resetting."""
        renderer = Mock()
        renderer.term = Mock()
        renderer.term.home = Mock(return_value="")
        renderer.term.clear = Mock(return_value="")
        session = GameSession(renderer)
        
        # Make a move so there's history
        session.cursor_state = CursorState(
            position=Square(file="e", rank=4),
            selected_square=Square(file="e", rank=2)
        )
        session.handle_input(InputEvent(InputType.SELECT))
        original_state = session.game_state
        
        # Restart with 'n' confirmation - should not reset
        with patch('builtins.input', return_value='n'):
            with patch('builtins.print'):
                session.handle_input(InputEvent(InputType.RESTART))
        
        # Game should NOT have been reset
        assert session.game_state is original_state
        assert len(session.state_history) > 0

    def test_restart_confirmed_resets_game(self):
        """Restart should reset game when user confirms with 'y'."""
        renderer = Mock()
        renderer.term = Mock()
        renderer.term.home = Mock(return_value="")
        renderer.term.clear = Mock(return_value="")
        session = GameSession(renderer)
        
        # Make a move
        session.cursor_state = CursorState(
            position=Square(file="e", rank=4),
            selected_square=Square(file="e", rank=2)
        )
        session.handle_input(InputEvent(InputType.SELECT))
        
        # Restart with 'y' confirmation
        with patch('builtins.input', return_value='y'):
            with patch('builtins.print'):
                session.handle_input(InputEvent(InputType.RESTART))
        
        assert session.game_state.fullmove_number == 1
        assert session.game_state.active_color == Color.WHITE
        assert session.game_state.board.get(Square(file="e", rank=2)) is not None

    def test_restart_clears_history_when_confirmed(self):
        """Restart should clear state history when confirmed."""
        renderer = Mock()
        renderer.term = Mock()
        renderer.term.home = Mock(return_value="")
        renderer.term.clear = Mock(return_value="")
        session = GameSession(renderer)
        
        # Make a move
        session.cursor_state = CursorState(
            position=Square(file="e", rank=4),
            selected_square=Square(file="e", rank=2)
        )
        session.handle_input(InputEvent(InputType.SELECT))
        
        # Restart with confirmation
        with patch('builtins.input', return_value='y'):
            with patch('builtins.print'):
                session.handle_input(InputEvent(InputType.RESTART))
        
        assert session.state_history == []

    def test_restart_resets_cursor_when_confirmed(self):
        """Restart should reset cursor to initial position when confirmed."""
        renderer = Mock()
        renderer.term = Mock()
        renderer.term.home = Mock(return_value="")
        renderer.term.clear = Mock(return_value="")
        session = GameSession(renderer)
        session.cursor_state = CursorState(position=Square(file="h", rank=8))
        
        with patch('builtins.input', return_value='y'):
            with patch('builtins.print'):
                session.handle_input(InputEvent(InputType.RESTART))
        
        assert session.cursor_state.position == Square(file="e", rank=2)

    def test_restart_no_confirmation_needed_at_start(self):
        """Restart should not require confirmation when no moves made."""
        renderer = Mock()
        session = GameSession(renderer)
        
        # No moves made, just restart
        session.handle_input(InputEvent(InputType.RESTART))
        
        # Should reset without prompting (no input mock needed)
        assert session.game_state.fullmove_number == 1
        assert session.state_history == []

    def test_restart_requires_confirmation_for_loaded_game(self):
        """Restart should require confirmation for loaded games with move history."""
        renderer = Mock()
        renderer.term = Mock()
        renderer.term.home = Mock(return_value="")
        renderer.term.clear = Mock(return_value="")
        session = GameSession(renderer)
        
        # Simulate a loaded game: state_history is empty but move_history has moves
        # This is what happens when loading a saved game
        session.game_state = session.game_state.with_move_added("e4").with_move_added("e5")
        session.state_history = []  # Empty - no undo states from this session
        
        original_state = session.game_state
        
        # Restart with 'n' confirmation - should not reset
        with patch('builtins.input', return_value='n'):
            with patch('builtins.print'):
                session.handle_input(InputEvent(InputType.RESTART))
        
        # Game should NOT have been reset
        assert session.game_state is original_state
        assert list(session.game_state.move_history) == ["e4", "e5"]

    def test_restart_loaded_game_confirmed(self):
        """Restart should reset loaded game when user confirms."""
        renderer = Mock()
        renderer.term = Mock()
        renderer.term.home = Mock(return_value="")
        renderer.term.clear = Mock(return_value="")
        session = GameSession(renderer)
        
        # Simulate a loaded game with move history
        session.game_state = session.game_state.with_move_added("e4").with_move_added("e5")
        session.state_history = []
        
        # Restart with 'y' confirmation
        with patch('builtins.input', return_value='y'):
            with patch('builtins.print'):
                session.handle_input(InputEvent(InputType.RESTART))
        
        # Game should have been reset
        assert session.game_state.fullmove_number == 1
        assert len(session.game_state.move_history) == 0


class TestCancel:
    """Tests for cancel/escape functionality."""

    def test_cancel_clears_selection_in_ai_mode(self):
        """Cancel should immediately clear selection in AI mode."""
        renderer = Mock()
        ai_engine = AIEngine(Difficulty.EASY)
        session = GameSession(renderer, ai_engine)
        session.cursor_state = CursorState(
            position=Square(file="e", rank=2),
            selected_square=Square(file="e", rank=2)
        )
        
        session.handle_input(InputEvent(InputType.CANCEL))
        
        assert session.cursor_state.selected_square is None

    def test_cancel_requests_confirmation_in_multiplayer(self):
        """First cancel in multiplayer should request confirmation."""
        renderer = Mock()
        session = GameSession(renderer, ai_engine=None)
        session.cursor_state = CursorState(
            position=Square(file="e", rank=2),
            selected_square=Square(file="e", rank=2)
        )
        
        session.handle_input(InputEvent(InputType.CANCEL))
        
        assert session.cursor_state.pending_cancel is True
        assert session.cursor_state.selected_square is not None

    def test_second_cancel_confirms_in_multiplayer(self):
        """Second cancel in multiplayer should confirm and clear."""
        renderer = Mock()
        session = GameSession(renderer, ai_engine=None)
        session.cursor_state = CursorState(
            position=Square(file="e", rank=2),
            selected_square=Square(file="e", rank=2),
            pending_cancel=True
        )
        
        session.handle_input(InputEvent(InputType.CANCEL))
        
        assert session.cursor_state.selected_square is None
        assert session.cursor_state.pending_cancel is False


class TestHints:
    """Tests for hint functionality."""

    def test_hints_toggle_when_allowed_and_piece_selected(self):
        """TAB should toggle hints when allowed and piece selected."""
        renderer = Mock()
        renderer.show_error = Mock()
        ai_engine = AIEngine(Difficulty.EASY)
        session = GameSession(renderer, ai_engine)
        session.cursor_state = CursorState(
            position=Square(file="e", rank=2),
            selected_square=Square(file="e", rank=2)
        )
        
        session.handle_input(InputEvent(InputType.SHOW_HINTS))
        
        assert session.cursor_state.show_hints is True

    def test_hints_error_when_not_allowed(self):
        """TAB should show error when hints not allowed."""
        renderer = Mock()
        renderer.show_error = Mock()
        ai_engine = AIEngine(Difficulty.HARD)
        session = GameSession(renderer, ai_engine)
        session.cursor_state = CursorState(
            position=Square(file="e", rank=2),
            selected_square=Square(file="e", rank=2)
        )
        
        session.handle_input(InputEvent(InputType.SHOW_HINTS))
        
        renderer.show_error.assert_called_once_with("Hints not available in this mode")

    def test_hints_error_when_no_piece_selected(self):
        """TAB should show error when no piece selected."""
        renderer = Mock()
        renderer.show_error = Mock()
        ai_engine = AIEngine(Difficulty.EASY)
        session = GameSession(renderer, ai_engine)
        
        session.handle_input(InputEvent(InputType.SHOW_HINTS))
        
        renderer.show_error.assert_called_once_with("Select a piece first, then press TAB for hints")


class TestModeToggle:
    """Tests for input mode toggling."""

    def test_toggle_mode_switches_to_san(self):
        """TOGGLE_MODE should switch from cursor to SAN mode."""
        renderer = Mock()
        session = GameSession(renderer)
        
        session.handle_input(InputEvent(InputType.TOGGLE_MODE))
        
        assert session.input_mode == "san"

    def test_toggle_mode_clears_selection(self):
        """TOGGLE_MODE should clear cursor selection."""
        renderer = Mock()
        session = GameSession(renderer)
        session.cursor_state = CursorState(
            position=Square(file="e", rank=2),
            selected_square=Square(file="e", rank=2)
        )
        
        session.handle_input(InputEvent(InputType.TOGGLE_MODE))
        
        assert session.cursor_state.selected_square is None


class TestHelp:
    """Tests for help overlay."""

    def test_help_calls_overlay(self):
        """HELP should trigger help overlay."""
        renderer = Mock()
        renderer.term = Mock()
        session = GameSession(renderer)
        
        with patch('pychess.controller.game_session.show_help_overlay') as mock_help:
            session.handle_input(InputEvent(InputType.HELP))
            mock_help.assert_called_once_with(renderer.term)


class TestQuit:
    """Tests for quit handling."""

    def test_quit_returns_should_quit_true(self):
        """QUIT handler should return should_quit=True."""
        renderer = Mock()
        renderer.term = Mock()
        renderer.term.home = Mock(return_value="")
        renderer.term.clear = Mock(return_value="")
        session = GameSession(renderer)
        
        with patch('builtins.input', return_value='y'):
            with patch('builtins.print'):
                result = session.handle_input(InputEvent(InputType.QUIT))
        
        assert result is True

    def test_quit_cancelled_returns_false(self):
        """Cancelled quit should return should_quit=False."""
        renderer = Mock()
        renderer.term = Mock()
        renderer.term.home = Mock(return_value="")
        renderer.term.clear = Mock(return_value="")
        session = GameSession(renderer)
        
        with patch('builtins.input', return_value='n'):
            with patch('builtins.print'):
                result = session.handle_input(InputEvent(InputType.QUIT))
        
        assert result is False


class TestSANInput:
    """Tests for SAN input mode."""

    def test_san_valid_move(self):
        """Valid SAN move should update game state."""
        renderer = Mock()
        session = GameSession(renderer)
        session.input_mode = "san"
        
        result = session.handle_san_input("e4")
        
        assert session.game_state.board.get(Square(file="e", rank=4)) is not None
        assert session.game_state.active_color == Color.BLACK

    def test_san_invalid_move_shows_error(self):
        """Invalid SAN move should show error."""
        renderer = Mock()
        renderer.show_error = Mock()
        session = GameSession(renderer)
        session.input_mode = "san"
        
        session.handle_san_input("e5")  # Invalid - pawn can't go to e5
        
        renderer.show_error.assert_called()

    def test_san_slash_toggles_to_cursor_mode(self):
        """'/' in SAN mode should switch to cursor mode."""
        renderer = Mock()
        session = GameSession(renderer)
        session.input_mode = "san"
        
        session.handle_san_input("/")
        
        assert session.input_mode == "cursor"

    def test_san_u_undoes_move(self):
        """'u' in SAN mode should undo."""
        renderer = Mock()
        session = GameSession(renderer)
        session.input_mode = "san"
        
        # Make a move first
        session.handle_san_input("e4")
        assert session.game_state.active_color == Color.BLACK
        
        # Undo
        session.handle_san_input("u")
        
        assert session.game_state.active_color == Color.WHITE

    def test_san_r_restarts_game_with_confirmation(self):
        """'r' in SAN mode should restart game after confirmation."""
        renderer = Mock()
        renderer.term = Mock()
        renderer.term.home = Mock(return_value="")
        renderer.term.clear = Mock(return_value="")
        session = GameSession(renderer)
        session.input_mode = "san"
        
        # Make a move
        session.handle_san_input("e4")
        
        # Restart with confirmation
        with patch('builtins.input', return_value='y'):
            with patch('builtins.print'):
                session.handle_san_input("r")
        
        assert session.game_state.fullmove_number == 1
        assert session.state_history == []

    def test_san_r_restart_cancelled(self):
        """'r' in SAN mode should not restart if user cancels."""
        renderer = Mock()
        renderer.term = Mock()
        renderer.term.home = Mock(return_value="")
        renderer.term.clear = Mock(return_value="")
        session = GameSession(renderer)
        session.input_mode = "san"
        
        # Make a move
        session.handle_san_input("e4")
        original_state = session.game_state
        
        # Restart but cancel
        with patch('builtins.input', return_value='n'):
            with patch('builtins.print'):
                session.handle_san_input("r")
        
        # Should not have restarted
        assert session.game_state is original_state
        assert len(session.state_history) > 0


class TestStatusMessages:
    """Tests for status message management."""

    def test_initial_welcome_messages(self):
        """Session should start with welcome messages."""
        renderer = Mock()
        session = GameSession(renderer)
        
        assert "Welcome to PyChess!" in session.status_messages

    def test_move_updates_status(self):
        """Successful move should update status messages."""
        renderer = Mock()
        session = GameSession(renderer)
        session.cursor_state = CursorState(
            position=Square(file="e", rank=4),
            selected_square=Square(file="e", rank=2)
        )
        
        session.handle_input(InputEvent(InputType.SELECT))
        
        assert any("e4" in msg for msg in session.status_messages)


class TestGetLegalMoveSquares:
    """Tests for legal move square calculation."""

    def test_returns_empty_when_no_selection(self):
        """Should return empty set when no piece selected."""
        renderer = Mock()
        session = GameSession(renderer)
        
        squares = session.get_legal_move_squares()
        
        assert squares == set()

    def test_returns_empty_when_hints_disabled(self):
        """Should return empty set when hints not shown."""
        renderer = Mock()
        ai_engine = AIEngine(Difficulty.EASY)
        session = GameSession(renderer, ai_engine)
        session.cursor_state = CursorState(
            position=Square(file="e", rank=2),
            selected_square=Square(file="e", rank=2),
            show_hints=False
        )
        
        squares = session.get_legal_move_squares()
        
        assert squares == set()

    def test_returns_moves_when_hints_enabled(self):
        """Should return legal move squares when hints enabled."""
        renderer = Mock()
        ai_engine = AIEngine(Difficulty.EASY)
        session = GameSession(renderer, ai_engine)
        session.cursor_state = CursorState(
            position=Square(file="e", rank=2),
            selected_square=Square(file="e", rank=2),
            show_hints=True
        )
        
        squares = session.get_legal_move_squares()
        
        assert Square(file="e", rank=3) in squares
        assert Square(file="e", rank=4) in squares


class TestMouseHandling:
    """Tests for mouse event handling in GameSession."""

    def test_mouse_click_type_in_handler_table(self):
        """MOUSE_CLICK should be in the cursor handlers table."""
        renderer = Mock()
        session = GameSession(renderer)
        
        assert InputType.MOUSE_CLICK in session._cursor_handlers

    def test_mouse_release_type_in_handler_table(self):
        """MOUSE_RELEASE should be in the cursor handlers table."""
        renderer = Mock()
        session = GameSession(renderer)
        
        assert InputType.MOUSE_RELEASE in session._cursor_handlers

    def test_mouse_click_on_own_piece_selects_it(self):
        """Clicking on own piece should select it."""
        renderer = Mock()
        renderer.pixel_to_square = Mock(return_value=Square(file="e", rank=2))
        session = GameSession(renderer)
        
        # Mouse click at coordinates that map to e2 (white pawn)
        event = InputEvent(
            InputType.MOUSE_CLICK,
            mouse_x=50,
            mouse_y=30
        )
        session.handle_input(event)
        
        # e2 should be selected
        assert session.cursor_state.selected_square == Square(file="e", rank=2)
        assert session.cursor_state.position == Square(file="e", rank=2)

    def test_mouse_click_on_opponent_piece_shows_error(self):
        """Clicking on opponent's piece should show error."""
        renderer = Mock()
        renderer.pixel_to_square = Mock(return_value=Square(file="e", rank=7))
        renderer.show_error = Mock()
        session = GameSession(renderer)
        
        # Mouse click on e7 (black pawn) when it's white's turn
        event = InputEvent(
            InputType.MOUSE_CLICK,
            mouse_x=50,
            mouse_y=10
        )
        session.handle_input(event)
        
        # Should show error, not select
        renderer.show_error.assert_called_once()
        assert session.cursor_state.selected_square is None

    def test_mouse_click_on_empty_square_clears_selection(self):
        """Clicking on empty square should clear current selection."""
        renderer = Mock()
        renderer.pixel_to_square = Mock(return_value=Square(file="e", rank=4))
        session = GameSession(renderer)
        
        # First select a piece
        session.cursor_state = CursorState(
            position=Square(file="e", rank=2),
            selected_square=Square(file="e", rank=2)
        )
        
        # Click on empty square e4
        event = InputEvent(
            InputType.MOUSE_CLICK,
            mouse_x=50,
            mouse_y=20
        )
        session.handle_input(event)
        
        # Selection should be cleared, cursor moves to e4
        assert session.cursor_state.selected_square is None
        assert session.cursor_state.position == Square(file="e", rank=4)

    def test_mouse_click_on_destination_makes_move(self):
        """Clicking on valid destination with piece selected should make move."""
        renderer = Mock()
        renderer.render = Mock()
        session = GameSession(renderer)
        
        # Select e2 pawn first
        session.cursor_state = CursorState(
            position=Square(file="e", rank=2),
            selected_square=Square(file="e", rank=2)
        )
        
        # Click on e4 to move
        renderer.pixel_to_square = Mock(return_value=Square(file="e", rank=4))
        event = InputEvent(
            InputType.MOUSE_CLICK,
            mouse_x=50,
            mouse_y=20
        )
        session.handle_input(event)
        
        # Move should be made
        assert "e4" in session.game_state.move_history
        assert session.cursor_state.selected_square is None

    def test_mouse_click_on_illegal_destination_shows_error(self):
        """Clicking on illegal destination should show error."""
        renderer = Mock()
        renderer.show_error = Mock()
        session = GameSession(renderer)
        
        # Select e2 pawn
        session.cursor_state = CursorState(
            position=Square(file="e", rank=2),
            selected_square=Square(file="e", rank=2)
        )
        
        # Try to move to e5 (illegal - pawn can't jump that far)
        renderer.pixel_to_square = Mock(return_value=Square(file="e", rank=5))
        event = InputEvent(
            InputType.MOUSE_CLICK,
            mouse_x=50,
            mouse_y=15
        )
        session.handle_input(event)
        
        # Should show error
        renderer.show_error.assert_called()
        assert session.cursor_state.selected_square is None

    def test_mouse_click_outside_board_ignored(self):
        """Clicking outside board should be ignored."""
        renderer = Mock()
        renderer.pixel_to_square = Mock(return_value=None)
        session = GameSession(renderer)
        
        initial_cursor = session.cursor_state
        
        # Click outside board
        event = InputEvent(
            InputType.MOUSE_CLICK,
            mouse_x=0,
            mouse_y=0
        )
        session.handle_input(event)
        
        # Nothing should change
        assert session.cursor_state == initial_cursor

    def test_drag_and_drop_move(self):
        """Click on piece, drag to destination, release should make move."""
        renderer = Mock()
        renderer.render = Mock()
        session = GameSession(renderer)
        
        # Click on e2 (start drag)
        renderer.pixel_to_square = Mock(return_value=Square(file="e", rank=2))
        click_event = InputEvent(
            InputType.MOUSE_CLICK,
            mouse_x=50,
            mouse_y=30
        )
        session.handle_input(click_event)
        
        # e2 should be selected
        assert session.cursor_state.selected_square == Square(file="e", rank=2)
        
        # Release on e4 (end drag)
        renderer.pixel_to_square = Mock(return_value=Square(file="e", rank=4))
        release_event = InputEvent(
            InputType.MOUSE_RELEASE,
            mouse_x=50,
            mouse_y=20
        )
        session.handle_input(release_event)
        
        # Move should be made
        assert "e4" in session.game_state.move_history

    def test_mouse_release_without_selection_ignored(self):
        """Mouse release without prior selection should be ignored."""
        renderer = Mock()
        renderer.pixel_to_square = Mock(return_value=Square(file="e", rank=4))
        session = GameSession(renderer)
        
        initial_state = session.game_state
        
        # Release without any selection
        release_event = InputEvent(
            InputType.MOUSE_RELEASE,
            mouse_x=50,
            mouse_y=20
        )
        session.handle_input(release_event)
        
        # Nothing should change
        assert session.game_state == initial_state

    def test_mouse_release_on_same_square_keeps_selection(self):
        """Releasing on the same square as click should keep selection."""
        renderer = Mock()
        session = GameSession(renderer)
        
        # Click on e2 to select
        renderer.pixel_to_square = Mock(return_value=Square(file="e", rank=2))
        click_event = InputEvent(
            InputType.MOUSE_CLICK,
            mouse_x=50,
            mouse_y=30
        )
        session.handle_input(click_event)
        
        # Release on same square e2
        release_event = InputEvent(
            InputType.MOUSE_RELEASE,
            mouse_x=50,
            mouse_y=30
        )
        session.handle_input(release_event)
        
        # Selection should still be there (click-to-select behavior)
        assert session.cursor_state.selected_square == Square(file="e", rank=2)

    def test_mouse_click_moves_cursor_position(self):
        """Mouse click should move cursor to clicked square."""
        renderer = Mock()
        renderer.pixel_to_square = Mock(return_value=Square(file="d", rank=4))
        session = GameSession(renderer)
        
        event = InputEvent(
            InputType.MOUSE_CLICK,
            mouse_x=40,
            mouse_y=20
        )
        session.handle_input(event)
        
        # Cursor should move to d4
        assert session.cursor_state.position == Square(file="d", rank=4)
