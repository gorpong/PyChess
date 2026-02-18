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
from pychess.model.piece import Color, Piece
from pychess.model.square import Square
from pychess.notation.san import move_to_san
from pychess.notation.pgn import _apply_san_move
from pychess.persistence.save_manager import SaveManager
from pychess.rules.move import Move
from pychess.rules.validator import get_legal_moves, is_in_check
from pychess.rules.game_logic import get_game_result


# Map mode strings to AI difficulty
MODE_TO_DIFFICULTY = {
    'easy': Difficulty.EASY,
    'medium': Difficulty.MEDIUM,
    'hard': Difficulty.HARD,
}

# Modes where hints are allowed
HINTS_ALLOWED_MODES = {'multiplayer', 'easy', 'medium'}

# Map piece letters to Piece enum
PROMOTION_PIECES = {
    'Q': Piece.QUEEN,
    'R': Piece.ROOK,
    'B': Piece.BISHOP,
    'N': Piece.KNIGHT,
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
        show_hints: Whether to currently display legal move hints.
        status_messages: List of status messages to display.
        pending_promotion: Move awaiting promotion piece choice, if any.
        game_result: Game result if game has ended ('1-0', '0-1', '1/2-1/2').
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
    show_hints: bool = False
    status_messages: list[str] = field(default_factory=list)
    pending_promotion: Optional[Move] = None
    game_result: Optional[str] = None
    
    @property
    def hints_allowed(self) -> bool:
        """Check if hints are allowed in this game mode."""
        return self.game_mode in HINTS_ALLOWED_MODES
    
    @property
    def is_game_over(self) -> bool:
        """Check if the game has ended."""
        return self.game_result is not None
    
    def get_legal_moves_for_selected(self) -> set[Square]:
        """Get legal destination squares for the selected piece.
        
        Returns:
            Set of squares the selected piece can legally move to,
            or empty set if no piece selected or hints not enabled.
        """
        if not self.selected_square:
            return set()
        
        if not self.show_hints:
            return set()
        
        if not self.hints_allowed:
            return set()
        
        legal_squares = set()
        all_legal_moves = get_legal_moves(self.game_state)
        for move in all_legal_moves:
            if move.from_square == self.selected_square:
                legal_squares.add(move.to_square)
        
        return legal_squares


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
    
    def select_square(self, session: WebGameSession, square: Square) -> WebGameSession:
        """Handle square selection logic.
        
        If a piece is already selected and the clicked square is a legal
        destination, this will execute the move instead of selecting.
        
        Args:
            session: Current game session.
            square: Square that was clicked.
            
        Returns:
            Updated session with new selection state or after move.
        """
        # Don't allow interaction if game is over
        if session.is_game_over:
            return session
        
        # Don't allow interaction if waiting for promotion choice
        if session.pending_promotion:
            return session
        
        game_state = session.game_state
        
        # If clicking the already-selected square, deselect it
        if session.selected_square == square:
            session.selected_square = None
            session.show_hints = False
            session.status_messages = ['Selection cleared']
            return session
        
        # If a piece is already selected, check if this is a move attempt
        if session.selected_square:
            # Check if clicked square is a legal destination
            legal_moves = get_legal_moves(game_state)
            matching_moves = [
                m for m in legal_moves
                if m.from_square == session.selected_square and m.to_square == square
            ]
            
            if matching_moves:
                # This is a move attempt
                return self._execute_move(session, matching_moves)
        
        # Otherwise, try to select a piece
        piece_info = game_state.board.get(square)
        
        if piece_info:
            piece_type, piece_color = piece_info
            if piece_color == game_state.turn:
                # Select this piece
                session.selected_square = square
                session.show_hints = False  # Reset hints on new selection
                color_name = 'White' if piece_color == Color.WHITE else 'Black'
                session.status_messages = [f'Selected {color_name} {piece_type.name.title()}']
            else:
                # Opponent's piece - can't select
                session.status_messages = ["That's not your piece!"]
        else:
            # Empty square - clear selection
            session.selected_square = None
            session.show_hints = False
            session.status_messages = ['Selection cleared']
        
        return session
    
    def _execute_move(
        self, 
        session: WebGameSession, 
        matching_moves: list[Move]
    ) -> WebGameSession:
        """Execute a move or prompt for promotion.
        
        Args:
            session: Current game session.
            matching_moves: List of legal moves matching the from/to squares.
                           Multiple moves indicate promotion options.
                           
        Returns:
            Updated session after move or with promotion pending.
        """
        # Check if this is a promotion (multiple moves = different promotion pieces)
        promotion_moves = [m for m in matching_moves if m.promotion is not None]
        
        if len(promotion_moves) > 1:
            # Need to ask for promotion piece
            # Store the base move info and wait for piece selection
            session.pending_promotion = matching_moves[0]  # Store any, we'll update promotion
            session.status_messages = ['Choose a piece for promotion']
            return session
        
        # Single move - execute it
        move = matching_moves[0]
        return self._apply_move(session, move)
    
    def _apply_move(self, session: WebGameSession, move: Move) -> WebGameSession:
        """Apply a move to the game state.
        
        Args:
            session: Current game session.
            move: The move to apply.
            
        Returns:
            Updated session after move.
        """
        # Save state for undo
        session.state_history.append(session.game_state)
        
        # Generate SAN before applying move
        san = move_to_san(session.game_state, move)
        
        # Apply the move
        session.game_state = _apply_san_move(session.game_state, san, move)
        
        # Update last move for highlighting
        session.last_move = (move.from_square, move.to_square)
        
        # Clear selection
        session.selected_square = None
        session.show_hints = False
        session.pending_promotion = None
        
        # Check for game end
        result = get_game_result(session.game_state)
        if result:
            session.game_result = result
            session.status_messages = [f'Move: {san}', self._result_message(result)]
            return session
        
        # Set status message
        session.status_messages = [f'Move: {san}']
        
        # If playing against AI and it's AI's turn, make AI move
        if session.ai_engine and session.game_state.turn == Color.BLACK:
            session = self._do_ai_move(session, san)
        
        return session
    
    def _do_ai_move(self, session: WebGameSession, player_san: str) -> WebGameSession:
        """Execute the AI's move.
        
        Args:
            session: Current game session.
            player_san: The player's move in SAN notation for status message.
            
        Returns:
            Updated session after AI move.
        """
        try:
            ai_move = session.ai_engine.select_move(session.game_state)
            
            # Save state for undo
            session.state_history.append(session.game_state)
            
            # Generate SAN and apply
            ai_san = move_to_san(session.game_state, ai_move)
            session.game_state = _apply_san_move(session.game_state, ai_san, ai_move)
            
            # Update last move
            session.last_move = (ai_move.from_square, ai_move.to_square)
            
            # Check for game end
            result = get_game_result(session.game_state)
            if result:
                session.game_result = result
                session.status_messages = [
                    f'Your move: {player_san}',
                    f'AI played: {ai_san}',
                    self._result_message(result),
                ]
            else:
                session.status_messages = [
                    f'Your move: {player_san}',
                    f'AI played: {ai_san}',
                ]
                
        except ValueError:
            session.status_messages = [f'Your move: {player_san}', 'AI has no legal moves']
        
        return session
    
    def _result_message(self, result: str) -> str:
        """Get a human-readable message for a game result.
        
        Args:
            result: Game result string ('1-0', '0-1', '1/2-1/2').
            
        Returns:
            Human-readable result message.
        """
        if result == '1-0':
            return 'Game Over: White wins!'
        elif result == '0-1':
            return 'Game Over: Black wins!'
        else:
            return 'Game Over: Draw!'
    
    def complete_promotion(self, session: WebGameSession, piece_letter: str) -> WebGameSession:
        """Complete a pending promotion with the chosen piece.
        
        Args:
            session: Current game session with pending promotion.
            piece_letter: Letter of chosen piece ('Q', 'R', 'B', 'N').
            
        Returns:
            Updated session after promotion move.
        """
        if not session.pending_promotion:
            session.status_messages = ['No promotion pending']
            return session
        
        piece = PROMOTION_PIECES.get(piece_letter.upper())
        if not piece:
            session.status_messages = ['Invalid promotion piece']
            return session
        
        # Create the promotion move
        base_move = session.pending_promotion
        promotion_move = Move(
            from_square=base_move.from_square,
            to_square=base_move.to_square,
            promotion=piece,
        )
        
        return self._apply_move(session, promotion_move)
    
    def undo_move(self, session: WebGameSession) -> WebGameSession:
        """Undo the last move(s).
        
        In AI mode, undoes both the AI's move and the player's move.
        In multiplayer, undoes a single move.
        
        Args:
            session: Current game session.
            
        Returns:
            Updated session after undo.
        """
        if not session.state_history:
            session.status_messages = ['No moves to undo']
            return session
        
        # Clear any pending promotion
        session.pending_promotion = None
        session.game_result = None
        
        # In AI mode, undo both AI's move and player's move
        if session.ai_engine and len(session.state_history) >= 2:
            session.state_history.pop()  # AI's move
            session.game_state = session.state_history.pop()  # Player's move
            session.status_messages = ['Both moves undone - your turn again']
        else:
            session.game_state = session.state_history.pop()
            session.status_messages = ['Move undone']
        
        # Clear selection and last move
        session.selected_square = None
        session.show_hints = False
        session.last_move = None
        
        return session
    
    def toggle_hints(self, session: WebGameSession) -> WebGameSession:
        """Toggle hint display for the current selection.
        
        Args:
            session: Current game session.
            
        Returns:
            Updated session with toggled hints state.
        """
        if session.is_game_over:
            session.status_messages = ['Game is over']
            return session
        
        if not session.hints_allowed:
            session.status_messages = ['Hints are not available in Hard mode']
            return session
        
        if not session.selected_square:
            session.status_messages = ['Select a piece first to see hints']
            return session
        
        session.show_hints = not session.show_hints
        
        if session.show_hints:
            legal_moves = session.get_legal_moves_for_selected()
            move_count = len(legal_moves)
            session.status_messages = [f'Showing {move_count} legal move(s)']
        else:
            session.status_messages = ['Hints hidden']
        
        return session
    
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
        
        # Check if game is already over
        result = get_game_result(game_state)
        if result:
            session.game_result = result
        
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
