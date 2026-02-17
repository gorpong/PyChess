"""Tests for game session management."""

import pytest
import time

from pychess.model.piece import Color
from pychess.model.square import Square
from pychess.ai.engine import Difficulty
from pychess.web.game_manager import (
    GameManager,
    WebGameSession,
    get_game_manager,
    reset_game_manager,
)


@pytest.fixture
def manager():
    """Create a fresh game manager for each test."""
    return GameManager()


@pytest.fixture(autouse=True)
def reset_global_manager():
    """Reset global manager before and after each test."""
    reset_game_manager()
    yield
    reset_game_manager()


class TestWebGameSession:
    """Tests for WebGameSession dataclass."""
    
    def test_session_has_required_fields(self):
        """Test that session has all required fields."""
        from pychess.model.game_state import GameState
        
        session = WebGameSession(
            session_id='test-id',
            game_state=GameState.initial(),
        )
        
        assert session.session_id == 'test-id'
        assert session.game_state is not None
        assert session.state_history == []
        assert session.selected_square is None
        assert session.ai_engine is None
        assert session.game_mode == 'multiplayer'
        assert session.game_name is None
        assert session.last_move is None
    
    def test_session_defaults_start_time(self):
        """Test that start_time defaults to current time."""
        from pychess.model.game_state import GameState
        
        before = time.time()
        session = WebGameSession(
            session_id='test-id',
            game_state=GameState.initial(),
        )
        after = time.time()
        
        assert before <= session.start_time <= after


class TestGameManagerCreateGame:
    """Tests for creating new games."""
    
    def test_create_multiplayer_game(self, manager):
        """Test creating a multiplayer game."""
        session = manager.create_game('test-id', 'multiplayer')
        
        assert session.session_id == 'test-id'
        assert session.game_mode == 'multiplayer'
        assert session.ai_engine is None
        assert session.game_state.turn == Color.WHITE
    
    def test_create_easy_ai_game(self, manager):
        """Test creating an easy AI game."""
        session = manager.create_game('test-id', 'easy')
        
        assert session.game_mode == 'easy'
        assert session.ai_engine is not None
        assert session.ai_engine.difficulty == Difficulty.EASY
    
    def test_create_medium_ai_game(self, manager):
        """Test creating a medium AI game."""
        session = manager.create_game('test-id', 'medium')
        
        assert session.game_mode == 'medium'
        assert session.ai_engine is not None
        assert session.ai_engine.difficulty == Difficulty.MEDIUM
    
    def test_create_hard_ai_game(self, manager):
        """Test creating a hard AI game."""
        session = manager.create_game('test-id', 'hard')
        
        assert session.game_mode == 'hard'
        assert session.ai_engine is not None
        assert session.ai_engine.difficulty == Difficulty.HARD
    
    def test_create_game_stores_session(self, manager):
        """Test that created game is stored and retrievable."""
        manager.create_game('test-id', 'multiplayer')
        
        retrieved = manager.get_game('test-id')
        assert retrieved is not None
        assert retrieved.session_id == 'test-id'
    
    def test_create_game_has_welcome_message(self, manager):
        """Test that new game has welcome status message."""
        session = manager.create_game('test-id', 'multiplayer')
        
        assert 'Welcome to PyChess!' in session.status_messages


class TestGameManagerGetGame:
    """Tests for retrieving games."""
    
    def test_get_existing_game(self, manager):
        """Test retrieving an existing game."""
        manager.create_game('test-id', 'multiplayer')
        
        session = manager.get_game('test-id')
        assert session is not None
        assert session.session_id == 'test-id'
    
    def test_get_nonexistent_game_returns_none(self, manager):
        """Test that getting nonexistent game returns None."""
        session = manager.get_game('nonexistent')
        assert session is None


class TestGameManagerUpdateGame:
    """Tests for updating games."""
    
    def test_update_game_persists_changes(self, manager):
        """Test that updates are persisted."""
        session = manager.create_game('test-id', 'multiplayer')
        
        # Modify session
        session.selected_square = Square(file='e', rank=2)
        manager.update_game(session)
        
        # Retrieve and verify
        retrieved = manager.get_game('test-id')
        assert retrieved.selected_square == Square(file='e', rank=2)


class TestGameManagerDeleteGame:
    """Tests for deleting games."""
    
    def test_delete_existing_game(self, manager):
        """Test deleting an existing game."""
        manager.create_game('test-id', 'multiplayer')
        
        manager.delete_game('test-id')
        
        assert manager.get_game('test-id') is None
    
    def test_delete_nonexistent_game_no_error(self, manager):
        """Test that deleting nonexistent game doesn't raise."""
        manager.delete_game('nonexistent')  # Should not raise


class TestGameManagerSessionLimit:
    """Tests for session limit enforcement."""
    
    def test_enforces_max_sessions(self):
        """Test that session limit is enforced."""
        manager = GameManager(max_sessions=3)
        
        manager.create_game('session-1', 'multiplayer')
        manager.create_game('session-2', 'multiplayer')
        manager.create_game('session-3', 'multiplayer')
        
        assert manager.get_session_count() == 3
        
        # Creating 4th should evict oldest
        manager.create_game('session-4', 'multiplayer')
        
        assert manager.get_session_count() == 3
        assert manager.get_game('session-1') is None
        assert manager.get_game('session-4') is not None
    
    def test_evicts_oldest_session(self):
        """Test that oldest session by start_time is evicted."""
        manager = GameManager(max_sessions=2)
        
        # Create sessions with controlled start times
        session1 = manager.create_game('oldest', 'multiplayer')
        session1.start_time = 1000
        manager.update_game(session1)
        
        session2 = manager.create_game('newer', 'multiplayer')
        session2.start_time = 2000
        manager.update_game(session2)
        
        # Create third - should evict 'oldest'
        manager.create_game('newest', 'multiplayer')
        
        assert manager.get_game('oldest') is None
        assert manager.get_game('newer') is not None
        assert manager.get_game('newest') is not None


class TestGameManagerSessionId:
    """Tests for session ID generation."""
    
    def test_session_id_is_string(self, manager):
        """Test that session ID is a string."""
        session_id = manager.create_session_id()
        assert isinstance(session_id, str)
    
    def test_session_ids_are_unique(self, manager):
        """Test that generated session IDs are unique."""
        ids = [manager.create_session_id() for _ in range(100)]
        assert len(ids) == len(set(ids))
    
    def test_session_id_is_url_safe(self, manager):
        """Test that session ID is URL-safe."""
        session_id = manager.create_session_id()
        # URL-safe base64 uses only alphanumeric, dash, and underscore
        import re
        assert re.match(r'^[A-Za-z0-9_-]+$', session_id)


class TestGlobalGameManager:
    """Tests for global game manager singleton."""
    
    def test_get_game_manager_returns_same_instance(self):
        """Test that get_game_manager returns singleton."""
        manager1 = get_game_manager()
        manager2 = get_game_manager()
        assert manager1 is manager2
    
    def test_reset_clears_singleton(self):
        """Test that reset_game_manager clears the singleton."""
        manager1 = get_game_manager()
        manager1.create_game('test', 'multiplayer')
        
        reset_game_manager()
        
        manager2 = get_game_manager()
        assert manager2.get_game('test') is None

class TestWebGameSessionHints:
    """Tests for hint functionality in WebGameSession."""

    def test_hints_allowed_in_multiplayer(self):
        """Test that hints are allowed in multiplayer mode."""
        from pychess.model.game_state import GameState

        session = WebGameSession(
            session_id='test',
            game_state=GameState.initial(),
            game_mode='multiplayer',
        )
        assert session.hints_allowed is True

    def test_hints_allowed_in_easy(self):
        """Test that hints are allowed in easy mode."""
        from pychess.model.game_state import GameState

        session = WebGameSession(
            session_id='test',
            game_state=GameState.initial(),
            game_mode='easy',
        )
        assert session.hints_allowed is True

    def test_hints_allowed_in_medium(self):
        """Test that hints are allowed in medium mode."""
        from pychess.model.game_state import GameState

        session = WebGameSession(
            session_id='test',
            game_state=GameState.initial(),
            game_mode='medium',
        )
        assert session.hints_allowed is True

    def test_hints_not_allowed_in_hard(self):
        """Test that hints are not allowed in hard mode."""
        from pychess.model.game_state import GameState

        session = WebGameSession(
            session_id='test',
            game_state=GameState.initial(),
            game_mode='hard',
        )
        assert session.hints_allowed is False

    def test_get_legal_moves_empty_without_selection(self):
        """Test that legal moves is empty without selection."""
        from pychess.model.game_state import GameState

        session = WebGameSession(
            session_id='test',
            game_state=GameState.initial(),
            game_mode='multiplayer',
            show_hints=True,
        )
        assert session.get_legal_moves_for_selected() == set()

    def test_get_legal_moves_empty_without_hints_enabled(self):
        """Test that legal moves is empty when hints not enabled."""
        from pychess.model.game_state import GameState

        session = WebGameSession(
            session_id='test',
            game_state=GameState.initial(),
            game_mode='multiplayer',
            selected_square=Square(file='e', rank=2),
            show_hints=False,
        )
        assert session.get_legal_moves_for_selected() == set()

    def test_get_legal_moves_returns_moves_when_enabled(self):
        """Test that legal moves are returned when hints enabled."""
        from pychess.model.game_state import GameState

        session = WebGameSession(
            session_id='test',
            game_state=GameState.initial(),
            game_mode='multiplayer',
            selected_square=Square(file='e', rank=2),
            show_hints=True,
        )
        legal_moves = session.get_legal_moves_for_selected()

        # e2 pawn can move to e3 and e4
        assert Square(file='e', rank=3) in legal_moves
        assert Square(file='e', rank=4) in legal_moves
        assert len(legal_moves) == 2


class TestGameManagerSelection:
    """Tests for selection handling in GameManager."""

    def test_select_own_piece(self, manager):
        """Test selecting own piece."""
        session = manager.create_game('test', 'multiplayer')

        session = manager.select_square(session, Square(file='e', rank=2))

        assert session.selected_square == Square(file='e', rank=2)

    def test_select_opponent_piece_rejected(self, manager):
        """Test that selecting opponent's piece is rejected."""
        session = manager.create_game('test', 'multiplayer')

        session = manager.select_square(session, Square(file='e', rank=7))

        assert session.selected_square is None
        assert "not your piece" in session.status_messages[0].lower()

    def test_select_empty_square_clears(self, manager):
        """Test that selecting empty square clears selection."""
        session = manager.create_game('test', 'multiplayer')
        session = manager.select_square(session, Square(file='e', rank=2))

        session = manager.select_square(session, Square(file='e', rank=4))

        assert session.selected_square is None

    def test_select_same_square_deselects(self, manager):
        """Test that clicking same square deselects."""
        session = manager.create_game('test', 'multiplayer')
        session = manager.select_square(session, Square(file='e', rank=2))

        session = manager.select_square(session, Square(file='e', rank=2))

        assert session.selected_square is None

    def test_selection_resets_hints(self, manager):
        """Test that new selection resets hints."""
        session = manager.create_game('test', 'multiplayer')
        session = manager.select_square(session, Square(file='e', rank=2))
        session = manager.toggle_hints(session)
        assert session.show_hints is True

        session = manager.select_square(session, Square(file='d', rank=2))

        assert session.show_hints is False


class TestGameManagerToggleHints:
    """Tests for hint toggling in GameManager."""

    def test_toggle_hints_on(self, manager):
        """Test toggling hints on."""
        session = manager.create_game('test', 'multiplayer')
        session = manager.select_square(session, Square(file='e', rank=2))

        session = manager.toggle_hints(session)

        assert session.show_hints is True

    def test_toggle_hints_off(self, manager):
        """Test toggling hints off."""
        session = manager.create_game('test', 'multiplayer')
        session = manager.select_square(session, Square(file='e', rank=2))
        session = manager.toggle_hints(session)

        session = manager.toggle_hints(session)

        assert session.show_hints is False

    def test_toggle_hints_requires_selection(self, manager):
        """Test that toggle hints requires selection."""
        session = manager.create_game('test', 'multiplayer')

        session = manager.toggle_hints(session)

        assert session.show_hints is False
        assert 'Select a piece first' in session.status_messages[0]

    def test_toggle_hints_rejected_in_hard_mode(self, manager):
        """Test that hints are rejected in hard mode."""
        session = manager.create_game('test', 'hard')
        session = manager.select_square(session, Square(file='e', rank=2))

        session = manager.toggle_hints(session)

        assert session.show_hints is False
        assert 'not available in Hard mode' in session.status_messages[0]

