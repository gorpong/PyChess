"""Game session management for web UI.

This module handles creating, storing, and retrieving game sessions
for the web interface. Each browser session gets a unique game instance.
"""

import time
import secrets
from dataclasses import dataclass, field
from typing import Optional

from pychess.ai.engine import AIEngine, Difficulty
from pychess.model.game_state import GameState
from pychess.model.square import Square
from pychess.persistence.save_manager import SaveManager


# Map mode strings to AI difficulty
MODE_TO_DIFFICULTY = {
    'easy': Difficulty.EASY,
    'medium': Difficulty.MEDIUM,
    'hard': Difficulty.HARD,
}


@dataclass
class WebGameSession:
    """Server-side game session for web UI.
    
    Attributes:
        session_id: Unique identifier for this session.
        game_state: Current game state.
        state_history: Previous states for undo functionality.
        selected_square: Currently selected square, if any.
        ai_engine: AI engine for single-player mode, None for multiplayer.
        game_mode: One of 'multiplayer', 'easy', 'medium', or 'hard'.
        start_time: Unix timestamp when game started.
        game_name: Name for saving, None until saved or loaded.
        last_move: Tuple of (from_square, to_square) for highlighting.
    """
    session_id: str
    game_state: GameState
    state_history: list[GameState] = field(default_factory=list)
    selected_square: Optional[Square] = None
    ai_engine: Optional[AIEngine] = None
    game_mode: str = 'multiplayer'
    start_time: float = field(default_factory=time.time)
    game_name: Optional[str] = None
    last_move: Optional[tuple[Square, Square]] = None
    status_messages: list[str] = field(default_factory=list)


class GameManager:
    """Manages active game sessions.
    
    Sessions are stored in memory during play. Games are persisted
    to PGN files via SaveManager when user clicks "Save & Quit".
    
    Attributes:
        max_sessions: Maximum number of concurrent sessions allowed.
    """
    
    def __init__(self, max_sessions: int = 100) -> None:
        """Initialize the game manager.
        
        Args:
            max_sessions: Maximum concurrent sessions before oldest is evicted.
        """
        self.max_sessions = max_sessions
        self._sessions: dict[str, WebGameSession] = {}
        self._save_manager = SaveManager()
    
    def create_session_id(self) -> str:
        """Generate a new unique session ID.
        
        Returns:
            A secure random session ID string.
        """
        return secrets.token_urlsafe(32)
    
    def create_game(self, session_id: str, mode: str) -> WebGameSession:
        """Create a new game for the given session.
        
        Args:
            session_id: Unique session identifier.
            mode: Game mode - 'multiplayer', 'easy', 'medium', or 'hard'.
            
        Returns:
            The newly created WebGameSession.
        """
        # Enforce session limit
        self._enforce_session_limit()
        
        # Create AI engine if needed
        ai_engine = None
        if mode in MODE_TO_DIFFICULTY:
            ai_engine = AIEngine(MODE_TO_DIFFICULTY[mode])
        
        # Create session
        session = WebGameSession(
            session_id=session_id,
            game_state=GameState.initial(),
            ai_engine=ai_engine,
            game_mode=mode,
            status_messages=['Welcome to PyChess!'],
        )
        
        self._sessions[session_id] = session
        return session
    
    def get_game(self, session_id: str) -> Optional[WebGameSession]:
        """Get existing game for session.
        
        Args:
            session_id: Session identifier to look up.
            
        Returns:
            The WebGameSession if found, None otherwise.
        """
        return self._sessions.get(session_id)
    
    def update_game(self, session: WebGameSession) -> None:
        """Update the game state for a session.
        
        Args:
            session: The session to update (uses session.session_id as key).
        """
        self._sessions[session.session_id] = session
    
    def delete_game(self, session_id: str) -> None:
        """Remove a game session.
        
        Args:
            session_id: Session identifier to remove.
        """
        self._sessions.pop(session_id, None)
    
    def load_saved_game(self, session_id: str, game_name: str) -> WebGameSession:
        """Load a saved game from PGN into a new session.
        
        Args:
            session_id: Session identifier for the new session.
            game_name: Name of the saved game to load.
            
        Returns:
            The WebGameSession with loaded game state.
            
        Raises:
            FileNotFoundError: If the saved game doesn't exist.
        """
        # Enforce session limit
        self._enforce_session_limit()
        
        # Load from save manager
        game_state, headers = self._save_manager.load_game(game_name)
        
        # Determine game mode from headers
        mode = 'multiplayer'
        ai_engine = None
        
        game_mode_header = headers.game_mode
        if game_mode_header in ('Easy', 'Medium', 'Hard'):
            mode = game_mode_header.lower()
            ai_engine = AIEngine(MODE_TO_DIFFICULTY[mode])
        
        # Create session with loaded state
        session = WebGameSession(
            session_id=session_id,
            game_state=game_state,
            ai_engine=ai_engine,
            game_mode=mode,
            game_name=game_name,
            status_messages=[f'Loaded game: {game_name}'],
        )
        
        # Restore elapsed time
        if headers.total_time_seconds > 0:
            session.start_time = time.time() - headers.total_time_seconds
        
        self._sessions[session_id] = session
        return session
    
    def get_session_count(self) -> int:
        """Get the current number of active sessions.
        
        Returns:
            Number of active sessions.
        """
        return len(self._sessions)
    
    def _enforce_session_limit(self) -> None:
        """Evict oldest session if at capacity."""
        if len(self._sessions) >= self.max_sessions:
            # Find oldest session by start_time
            oldest_id = min(
                self._sessions.keys(),
                key=lambda sid: self._sessions[sid].start_time
            )
            self.delete_game(oldest_id)


# Global game manager instance
_game_manager: Optional[GameManager] = None


def get_game_manager() -> GameManager:
    """Get the global game manager instance.
    
    Returns:
        The singleton GameManager instance.
    """
    global _game_manager
    if _game_manager is None:
        _game_manager = GameManager()
    return _game_manager


def reset_game_manager() -> None:
    """Reset the global game manager. Used for testing."""
    global _game_manager
    _game_manager = None
