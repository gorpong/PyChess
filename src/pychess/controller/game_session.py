"""Game session controller for managing game flow.

This module provides the GameSession class which orchestrates the game loop,
handling input events, game state updates, and AI integration.
"""

import time
from typing import Optional

from pychess.model.game_state import GameState
from pychess.model.piece import Color
from pychess.model.square import Square
from pychess.notation.san import san_to_move, move_to_san
from pychess.notation.pgn import _apply_san_move
from pychess.rules.move import Move
from pychess.rules.validator import get_legal_moves, is_move_legal
from pychess.rules.game_logic import get_game_result
from pychess.ui.cursor import CursorState
from pychess.ui.input_handler import InputHandler, InputType, InputEvent
from pychess.ui.overlays import show_help_overlay
from pychess.ai.engine import AIEngine, Difficulty


class GameSession:
    """Manages a single game session including state, input, and AI.
    
    This class encapsulates all game session state and provides methods
    for handling input events. It coordinates between the UI layer,
    game rules, and AI engine.
    
    Attributes:
        renderer: Terminal renderer instance
        ai_engine: AI engine for single-player mode (None for multiplayer)
        game_state: Current game state
        cursor_state: Current cursor position and selection
        input_mode: Current input mode ("cursor" or "san")
        state_history: List of previous game states for undo
        status_messages: List of status messages to display
        hints_allowed: Whether hints are available in this mode
        is_multiplayer: Whether this is a two-player game
        start_time: Unix timestamp when the session started
    """

    def __init__(
        self,
        renderer,
        ai_engine: Optional[AIEngine] = None
    ) -> None:
        """Initialize a new game session.
        
        Args:
            renderer: Terminal renderer instance
            ai_engine: AI engine for single-player mode (None for multiplayer)
        """
        self.renderer = renderer
        self.ai_engine = ai_engine
        
        # Game state
        self.game_state = GameState.initial()
        self.cursor_state = CursorState.initial()
        self.input_mode = "cursor"
        self.state_history: list[GameState] = []
        
        # Timing
        self.start_time = time.time()
        
        # Session configuration
        self.hints_allowed = (
            ai_engine is not None and
            ai_engine.difficulty in (Difficulty.EASY, Difficulty.MEDIUM)
        )
        self.is_multiplayer = ai_engine is None
        
        # Status messages
        if self.hints_allowed:
            self.status_messages = [
                "Welcome to PyChess!",
                "Use arrow keys to move, Enter to select, TAB for hints"
            ]
        else:
            self.status_messages = [
                "Welcome to PyChess!",
                "Use arrow keys to move cursor, Enter to select"
            ]
        
        # Input type dispatch table for cursor mode
        self._cursor_handlers = {
            InputType.MOVE_UP: self._handle_move_up,
            InputType.MOVE_DOWN: self._handle_move_down,
            InputType.MOVE_LEFT: self._handle_move_left,
            InputType.MOVE_RIGHT: self._handle_move_right,
            InputType.SELECT: self._handle_select,
            InputType.CANCEL: self._handle_cancel,
            InputType.QUIT: self._handle_quit,
            InputType.UNDO: self._handle_undo,
            InputType.RESTART: self._handle_restart,
            InputType.HELP: self._handle_help,
            InputType.TOGGLE_MODE: self._handle_toggle_mode,
            InputType.SHOW_HINTS: self._handle_show_hints,
        }

    def run(self) -> None:
        """Run the main game loop.
        
        This method handles the primary game loop, alternating between
        rendering and input handling until the game ends or user quits.
        """
        input_handler = InputHandler()
        
        while True:
            # Check for game end
            if self._check_game_end():
                break
            
            # Render current position
            self._render()
            
            # Handle input based on mode
            if self.input_mode == "san":
                user_input = self.renderer.get_input().strip()
                should_quit = self.handle_san_input(user_input)
            else:
                key = self.renderer.get_key_input()
                event = input_handler.process_key(key)
                should_quit = self.handle_input(event)
            
            if should_quit:
                break

    def _check_game_end(self) -> bool:
        """Check if the game has ended and display result.
        
        Returns:
            True if game has ended, False otherwise
        """
        result = get_game_result(self.game_state)
        if result:
            if result == "1-0":
                self.status_messages.append("Game Over: White wins!")
            elif result == "0-1":
                self.status_messages.append("Game Over: Black wins!")
            else:
                self.status_messages.append("Game Over: Draw!")
            
            # Render final position
            self.renderer.render(self.game_state, status_messages=self.status_messages)
            self.renderer.show_message("Press any key to exit...")
            self.renderer.get_key_input()
            return True
        return False

    def _render(self) -> None:
        """Render the current game state."""
        # Get legal moves for highlighting
        legal_move_squares = self.get_legal_move_squares()
        
        # Render current position with cursor
        self.renderer.render(
            self.game_state,
            selected_square=self.cursor_state.selected_square,
            cursor_square=self.cursor_state.position,
            legal_moves=legal_move_squares,
            status_messages=self.status_messages
        )
        
        # Update input prompt
        self.renderer._render_input(mode=self.input_mode)

    def handle_input(self, event: InputEvent) -> bool:
        """Handle an input event in cursor mode.
        
        Args:
            event: The input event to handle
            
        Returns:
            True if the game should quit, False otherwise
        """
        handler = self._cursor_handlers.get(event.input_type)
        if handler:
            result = handler()
            # Only QUIT handler returns a meaningful value
            if event.input_type == InputType.QUIT:
                return result
        return False

    def handle_san_input(self, user_input: str) -> bool:
        """Handle input in SAN mode.
        
        Args:
            user_input: The user's text input
            
        Returns:
            True if the game should quit, False otherwise
        """
        # Handle empty input
        if not user_input:
            return False
        
        # Check for mode toggle
        if user_input == '/':
            self.input_mode = "cursor"
            self.status_messages = ["Switched to cursor mode"]
            return False
        
        # Handle commands
        cmd = user_input.lower()
        
        if cmd == 'q':
            return self._handle_quit()
        
        if cmd == 'u':
            self._handle_undo()
            return False
        
        if cmd == 'r':
            self._handle_restart()
            return False
        
        if cmd == '?':
            self._handle_help()
            return False
        
        # Try to parse as SAN move
        try:
            move = san_to_move(self.game_state, user_input)
            
            # Verify move is legal
            if not is_move_legal(self.game_state, move):
                self.renderer.show_error(f"Illegal move: {user_input}")
                return False
            
            # Execute the move
            self._execute_move(move)
            
        except ValueError:
            self.renderer.show_error(f"Invalid move: {user_input}")
        
        return False

    def get_legal_move_squares(self) -> set[Square]:
        """Get legal move destination squares for the selected piece.
        
        Returns:
            Set of squares the selected piece can legally move to,
            or empty set if no piece selected or hints not enabled.
        """
        if not self.cursor_state.selected_square:
            return set()
        
        if not self.cursor_state.show_hints:
            return set()
        
        if not self.hints_allowed:
            return set()
        
        # Find legal moves from selected square
        legal_move_squares = set()
        all_legal_moves = get_legal_moves(self.game_state)
        for move in all_legal_moves:
            if move.from_square == self.cursor_state.selected_square:
                legal_move_squares.add(move.to_square)
        
        return legal_move_squares

    # --- Cursor movement handlers ---
    
    def _handle_move_up(self) -> None:
        """Handle MOVE_UP input."""
        self.cursor_state = self.cursor_state.move_up()

    def _handle_move_down(self) -> None:
        """Handle MOVE_DOWN input."""
        self.cursor_state = self.cursor_state.move_down()

    def _handle_move_left(self) -> None:
        """Handle MOVE_LEFT input."""
        self.cursor_state = self.cursor_state.move_left()

    def _handle_move_right(self) -> None:
        """Handle MOVE_RIGHT input."""
        self.cursor_state = self.cursor_state.move_right()

    # --- Selection and move handlers ---
    
    def _handle_select(self) -> None:
        """Handle SELECT input (Enter key).
        
        This either:
        1. Attempts a move if a piece is selected and cursor is on different square
        2. Selects the piece at cursor if it belongs to current player
        3. Clears selection if cursor is on empty square
        """
        move_attempt = self.cursor_state.attempt_move()
        
        if move_attempt:
            from_square, to_square = move_attempt
            self._try_cursor_move(from_square, to_square)
        else:
            self._try_select_piece()

    def _try_cursor_move(self, from_square: Square, to_square: Square) -> None:
        """Try to execute a move from cursor selection.
        
        Args:
            from_square: Source square
            to_square: Destination square
        """
        # Find matching legal move
        legal_moves = get_legal_moves(self.game_state)
        matching_move = None
        
        for move in legal_moves:
            if move.from_square == from_square and move.to_square == to_square:
                matching_move = move
                break
        
        if matching_move:
            self._execute_move(matching_move)
            self.cursor_state = self.cursor_state.clear_selection()
        else:
            self.renderer.show_error("Illegal move")
            self.cursor_state = self.cursor_state.clear_selection()

    def _try_select_piece(self) -> None:
        """Try to select the piece at the current cursor position."""
        piece_info = self.game_state.board.get(self.cursor_state.position)
        
        if piece_info:
            piece_type, piece_color = piece_info
            if piece_color == self.game_state.active_color:
                self.cursor_state = self.cursor_state.select_square()
                self.status_messages = [
                    f"Selected {piece_color.name} {piece_type.name}"
                ]
            else:
                self.renderer.show_error("Not your piece!")
        else:
            # Empty square - deselect
            self.cursor_state = self.cursor_state.clear_selection()

    def _execute_move(self, move: Move) -> None:
        """Execute a validated move and trigger AI if needed.
        
        Args:
            move: The move to execute (must be legal)
        """
        # Save state for undo
        self.state_history.append(self.game_state)
        
        # Apply the move
        san_notation = move_to_san(self.game_state, move)
        self.game_state = _apply_san_move(self.game_state, san_notation, move)
        self.status_messages = [f"Move: {san_notation}"]
        
        # AI move if applicable
        if self.ai_engine and self.game_state.active_color == Color.BLACK:
            self._do_ai_move(san_notation)

    def _do_ai_move(self, player_san: str) -> None:
        """Execute the AI's move.
        
        Args:
            player_san: The player's move in SAN notation (for status message)
        """
        self.status_messages.append("AI is thinking...")
        self.renderer.render(self.game_state, status_messages=self.status_messages)
        
        try:
            ai_move = self.ai_engine.select_move(self.game_state)
            self.state_history.append(self.game_state)
            ai_san = move_to_san(self.game_state, ai_move)
            self.game_state = _apply_san_move(self.game_state, ai_san, ai_move)
            self.status_messages = [
                f"Your move: {player_san}",
                f"AI played: {ai_san}"
            ]
        except ValueError:
            self.status_messages = ["AI has no legal moves"]

    # --- Cancel handler ---
    
    def _handle_cancel(self) -> None:
        """Handle CANCEL input (Escape key).
        
        In multiplayer mode, requires confirmation (double-escape).
        In AI mode, immediately cancels selection.
        """
        if self.cursor_state.pending_cancel:
            # Second Escape confirms cancel in multiplayer
            self.cursor_state = self.cursor_state.confirm_cancel()
            self.status_messages = ["Selection cancelled"]
        elif self.is_multiplayer and self.cursor_state.selected_square:
            # First Escape in multiplayer: request confirmation
            self.cursor_state = self.cursor_state.request_cancel()
            self.status_messages = ["Press Escape again to cancel, or continue playing"]
        else:
            # AI mode or nothing selected: immediate cancel
            self.cursor_state = self.cursor_state.cancel_selection()
            self.status_messages = ["Selection cancelled"]

    # --- Global command handlers ---
    
    def _handle_quit(self) -> bool:
        """Handle QUIT input.
        
        Returns:
            True if user confirmed quit, False otherwise
        """
        print(self.renderer.term.home() + self.renderer.term.clear())
        confirm = input("Are you sure you want to quit? (y/n): ")
        return confirm.lower() == 'y'

    def _handle_undo(self) -> None:
        """Handle UNDO input."""
        if self.state_history:
            self.game_state = self.state_history.pop()
            self.cursor_state = self.cursor_state.clear_selection()
            self.status_messages = ["Move undone"]
        else:
            self.renderer.show_error("No moves to undo")

    def _handle_restart(self) -> None:
        """Handle RESTART input.
        
        If moves have been made, prompts for confirmation before resetting
        to prevent accidental loss of game progress.
        """
        # Check if there's any game progress to lose
        # - state_history: moves made this session (for undo)
        # - move_history: all moves in the game (including loaded games)
        has_progress = self.state_history or self.game_state.move_history
        
        # If no moves made, restart without confirmation
        if not has_progress:
            self._do_restart()
            return
        
        # Prompt for confirmation
        print(self.renderer.term.home() + self.renderer.term.clear())
        confirm = input("Are you sure you want to restart? All progress will be lost. (y/n): ")
        
        if confirm.lower() == 'y':
            self._do_restart()
        else:
            self.status_messages = ["Restart cancelled"]

    def _do_restart(self) -> None:
        """Actually perform the restart (no confirmation)."""
        self.game_state = GameState.initial()
        self.cursor_state = CursorState.initial()
        self.state_history = []
        self.status_messages = ["Game restarted!"]

    def _handle_help(self) -> None:
        """Handle HELP input."""
        show_help_overlay(self.renderer.term)

    def _handle_toggle_mode(self) -> None:
        """Handle TOGGLE_MODE input."""
        self.input_mode = "san"
        self.cursor_state = self.cursor_state.clear_selection()
        self.status_messages = ["Switched to SAN input mode - type moves like 'e4'"]

    def _handle_show_hints(self) -> None:
        """Handle SHOW_HINTS input (TAB key)."""
        if self.hints_allowed:
            if self.cursor_state.selected_square:
                self.cursor_state = self.cursor_state.toggle_hints()
                if self.cursor_state.show_hints:
                    self.status_messages = ["Showing legal moves (TAB to hide)"]
                else:
                    self.status_messages = ["Hints hidden"]
            else:
                self.renderer.show_error("Select a piece first, then press TAB for hints")
        else:
            self.renderer.show_error("Hints not available in this mode")
