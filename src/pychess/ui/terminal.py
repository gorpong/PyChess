"""Terminal-based renderer using the blessed library.

This module implements the Renderer interface using blessed for
terminal control, colors, and input handling.
"""

import sys
from typing import Optional

from blessed import Terminal

from pychess.model.game_state import GameState
from pychess.model.piece import Color, Piece
from pychess.model.square import Square
from pychess.ui.renderer import Renderer
from pychess.ui.board_view import BoardView


def format_elapsed_time(seconds: float) -> str:
    """Format elapsed time in a human-readable format.
    
    Args:
        seconds: Elapsed time in seconds (can be float, will be truncated)
        
    Returns:
        Formatted string like "45s", "5m 12s", or "1h 23m 45s"
    """
    # Handle negative values
    if seconds < 0:
        seconds = 0
    
    # Truncate to integer
    total_seconds = int(seconds)
    
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    secs = total_seconds % 60
    
    if hours > 0:
        return f"{hours}h {minutes}m {secs}s"
    elif minutes > 0:
        return f"{minutes}m {secs}s"
    else:
        return f"{secs}s"


class TerminalRenderer(Renderer):
    """Terminal-based renderer using blessed."""

    # Terminal size requirements
    MIN_WIDTH = 100
    MIN_HEIGHT = 44

    # Board display dimensions
    SQUARE_WIDTH = 6
    SQUARE_HEIGHT = 3
    BOARD_START_X = 5
    BOARD_START_Y = 3

    def __init__(self, use_unicode: bool = True):
        """Initialize terminal renderer.

        Args:
            use_unicode: Whether to use Unicode piece symbols
        """
        self.term = Terminal()
        self.board_view = BoardView(use_unicode=use_unicode)
        self.status_messages: list[str] = []
        self.input_buffer = ""

    def _safe_format(self, text: str, formatter) -> str:
        """Safely apply a terminal formatter with fallback.

        Args:
            text: Text to format
            formatter: Terminal formatter function (e.g., self.term.bold)

        Returns:
            Formatted text, or plain text if formatter fails
        """
        try:
            return formatter(text)
        except (TypeError, AttributeError):
            return text

    def _format_game_result(self, result: str) -> str:
        """Format a game result code into a human-readable string.

        Args:
            result: Result code ("1-0", "0-1", "1/2-1/2")

        Returns:
            Human-readable result string
        """
        if result == "1-0":
            return "White Wins!"
        elif result == "0-1":
            return "Black Wins!"
        elif result == "1/2-1/2":
            return "Draw!"
        else:
            return result

    def initialize(self) -> None:
        """Initialize the renderer and set up the display."""
        # Check terminal size
        self.check_terminal_size()

        # Clear screen
        print(self.term.clear())

        # Hide cursor
        print(self.term.hide_cursor(), end="", flush=True)

    def cleanup(self) -> None:
        """Clean up resources and restore terminal state.
        
        Note: We intentionally do NOT clear the screen here so that
        the final game state (including any game result) remains visible
        after the program exits.
        """
        # Show cursor
        print(self.term.normal_cursor(), end="", flush=True)
        
        # Move cursor to bottom of screen so prompt appears below the game
        print(self.term.move_xy(0, self.term.height - 1))

    def check_terminal_size(self) -> tuple[int, int]:
        """Check if terminal size meets minimum requirements.

        Returns:
            Tuple of (width, height)

        Raises:
            ValueError: If terminal is too small
        """
        width = self.term.width
        height = self.term.height

        if width < self.MIN_WIDTH or height < self.MIN_HEIGHT:
            raise ValueError(
                f"Terminal too small. "
                f"Minimum size: {self.MIN_WIDTH}x{self.MIN_HEIGHT}, "
                f"Current size: {width}x{height}"
            )

        return (width, height)

    def render(
        self,
        game_state: GameState,
        selected_square: Optional[Square] = None,
        cursor_square: Optional[Square] = None,
        legal_moves: Optional[set[Square]] = None,
        status_messages: Optional[list[str]] = None,
        elapsed_seconds: Optional[int] = None,
        game_result: Optional[str] = None,
    ) -> None:
        """Render the current game state.

        Args:
            game_state: Current game state to render
            selected_square: Currently selected square (if any)
            cursor_square: Square where cursor is positioned (if any)
            legal_moves: Set of legal destination squares to highlight (if any)
            status_messages: List of status messages to display
            elapsed_seconds: Total elapsed game time in seconds (if any)
            game_result: Game result string ("1-0", "0-1", "1/2-1/2") if game ended
        """
        if status_messages:
            self.status_messages = status_messages

        if legal_moves is None:
            legal_moves = set()

        # Clear screen
        print(self.term.home() + self.term.clear(), end="")

        # Render board
        self._render_board(
            game_state.board,
            selected_square,
            cursor_square,
            legal_moves,
            game_result
        )

        # Render status area
        self._render_status(game_state, elapsed_seconds)

        # Render input area
        self._render_input()

        # Flush output
        sys.stdout.flush()

    def _render_board(
        self,
        board,
        selected_square: Optional[Square],
        cursor_square: Optional[Square],
        legal_moves: set[Square],
        game_result: Optional[str] = None,
    ) -> None:
        """Render the chess board with pieces and highlighting.

        Args:
            board: Board to render
            selected_square: Currently selected square
            cursor_square: Square where cursor is positioned
            legal_moves: Set of legal destination squares
            game_result: Game result string if game ended
        """
        files = "abcdefgh"

        # Calculate center offset if terminal is wider than needed
        board_total_width = 8 * self.SQUARE_WIDTH + 10
        center_x = max(0, (self.term.width - board_total_width) // 2)

        # Draw title
        title = "PyChess - Terminal Chess Game"
        title_x = center_x + (board_total_width - len(title)) // 2
        print(self.term.move_xy(title_x, 1) + self._safe_format(title, self.term.bold))

        # Draw game result in prominent position (top-left area)
        if game_result:
            result_text = self._format_game_result(game_result)
            # Display in the left margin area, vertically centered with board
            result_x = 2
            result_y = self.BOARD_START_Y + 4  # Roughly middle of board
            
            # Draw a box around the result
            box_width = len(result_text) + 4
            print(self.term.move_xy(result_x, result_y - 1) + "+" + "-" * (box_width - 2) + "+")
            print(self.term.move_xy(result_x, result_y) + "| " + self._safe_format(result_text, self.term.bold) + " |")
            print(self.term.move_xy(result_x, result_y + 1) + "+" + "-" * (box_width - 2) + "+")

        # Draw top border
        border_x = center_x + self.BOARD_START_X - 2
        border_y = self.BOARD_START_Y - 1
        border_line = "+" + "-" * (8 * self.SQUARE_WIDTH + 2) + "+"
        print(self.term.move_xy(border_x, border_y) + border_line)

        # Render each rank from 8 to 1
        for rank in range(8, 0, -1):
            rank_y = self.BOARD_START_Y + (8 - rank) * self.SQUARE_HEIGHT

            # Draw rank label (left side)
            rank_label_x = center_x + self.BOARD_START_X - 3
            print(self.term.move_xy(rank_label_x, rank_y + 1) + str(rank))

            # Draw each file
            for file_idx, file in enumerate(files):
                square = Square(file=file, rank=rank)
                piece_info = board.get(square)

                # Calculate square position
                square_x = center_x + self.BOARD_START_X + file_idx * self.SQUARE_WIDTH
                square_y = rank_y

                # Determine background color
                is_light = self.board_view.is_light_square(square)
                is_selected = (square == selected_square)
                is_cursor = (square == cursor_square)
                is_legal_move = (square in legal_moves)

                # Choose colors
                if is_cursor:
                    bg_color = self.term.on_yellow
                elif is_selected:
                    bg_color = self.term.on_cyan
                elif is_legal_move:
                    bg_color = self.term.on_green if is_light else self.term.on_darkgreen
                elif is_light:
                    bg_color = self.term.on_white
                else:
                    bg_color = self.term.on_color(240)  # Dark gray

                # Render square (3 lines high)
                for line in range(self.SQUARE_HEIGHT):
                    content = " " * self.SQUARE_WIDTH

                    # Place piece symbol in the middle line
                    if line == 1 and piece_info:
                        piece_type, piece_color = piece_info
                        symbol = self.board_view.get_piece_symbol(piece_type, piece_color)

                        # Color the piece text for better contrast
                        # White pieces: Use blue/darkblue (visible on both light and dark squares)
                        # Black pieces: Use black/darkgray (visible on light squares)
                        if piece_color == Color.WHITE:
                            # Blue for white pieces - visible on both backgrounds
                            piece_text = self._safe_format(symbol, self.term.blue)
                        else:
                            # Black for black pieces - visible on light backgrounds
                            piece_text = self._safe_format(symbol, self.term.black)

                        # Center the piece in the square
                        padding = (self.SQUARE_WIDTH - 1) // 2
                        # We need to handle the colored text specially with background
                        left_pad = " " * padding
                        right_pad = " " * (self.SQUARE_WIDTH - padding - 1)

                        # Print with background and piece color
                        print(
                            self.term.move_xy(square_x, square_y + line) +
                            bg_color(left_pad) +
                            bg_color(piece_text) +
                            bg_color(right_pad) +
                            self.term.normal
                        )
                        continue

                    print(
                        self.term.move_xy(square_x, square_y + line) +
                        bg_color(content) +
                        self.term.normal
                    )

            # Draw rank label (right side)
            rank_label_x = center_x + self.BOARD_START_X + 8 * self.SQUARE_WIDTH + 1
            print(self.term.move_xy(rank_label_x, rank_y + 1) + str(rank))

        # Draw bottom border
        border_y = self.BOARD_START_Y + 8 * self.SQUARE_HEIGHT
        print(self.term.move_xy(border_x, border_y) + border_line)

        # Draw file labels
        file_labels_y = border_y + 1
        file_labels_x = center_x + self.BOARD_START_X
        for file_idx, file in enumerate(files):
            label_x = file_labels_x + file_idx * self.SQUARE_WIDTH + self.SQUARE_WIDTH // 2
            print(self.term.move_xy(label_x, file_labels_y) + file)

    def _render_status(self, game_state: GameState, elapsed_seconds: Optional[int] = None) -> None:
        """Render the status area with game information.

        Args:
            game_state: Current game state
            elapsed_seconds: Total elapsed game time in seconds (if any)
        """
        status_y = self.BOARD_START_Y + 8 * self.SQUARE_HEIGHT + 3

        # Display turn and elapsed time on same line
        turn_text = f"Turn: {game_state.active_color.name}"
        if elapsed_seconds is not None:
            time_text = f"Time: {format_elapsed_time(elapsed_seconds)}"
            turn_text = f"{turn_text}    {time_text}"
        print(self.term.move_xy(5, status_y) + self._safe_format(turn_text, self.term.bold))

        # Display move history (last 5 moves)
        history_y = status_y + 2
        print(self.term.move_xy(5, history_y) + self._safe_format("Move History:", self.term.bold))

        moves = game_state.move_history
        last_moves = moves[-10:] if len(moves) > 10 else moves

        # Display in pairs (White, Black)
        for i in range(0, len(last_moves), 2):
            move_num = (i // 2) + 1
            white_move = last_moves[i] if i < len(last_moves) else ""
            black_move = last_moves[i + 1] if i + 1 < len(last_moves) else ""

            move_text = f"{move_num}. {white_move:8} {black_move}"
            print(self.term.move_xy(5, history_y + 1 + (i // 2)) + move_text)

        # Display status messages
        messages_y = status_y + 10
        print(self.term.move_xy(5, messages_y) + self._safe_format("Status:", self.term.bold))

        # Show last 5 messages
        for idx, msg in enumerate(self.status_messages[-5:]):
            print(self.term.move_xy(5, messages_y + 1 + idx) + msg)

    def _render_input(self, mode: str = "san") -> None:
        """Render the input area.

        Args:
            mode: Input mode - "san" for SAN notation, "cursor" for cursor navigation
        """
        input_y = self.term.height - 3

        # Clear the input line first to handle backspace properly
        # This ensures deleted characters don't remain visible
        print(self.term.move_xy(5, input_y) + self.term.clear_eol(), end="")

        if mode == "cursor":
            # Cursor mode instructions
            prompt = "Cursor Mode: Use arrow keys to move, Enter to select/move"
            print(self.term.move_xy(5, input_y) + self._safe_format(prompt, self.term.bold))
            help_text = "Commands: q=quit, u=undo, r=restart, ?=help, T=tips, Esc=cancel, /=SAN mode"
        else:
            # SAN input mode
            prompt = "Enter move (SAN): "
            print(self.term.move_xy(5, input_y) + self._safe_format(prompt, self.term.bold) + self.input_buffer)
            help_text = "Commands: q=quit, u=undo, r=restart, ?=help, T=tips, /=cursor mode"

        print(self.term.move_xy(5, input_y + 1) + self._safe_format(help_text, self.term.dim))

    def get_input(self) -> str:
        """Get input from the user.

        Returns:
            Input string (e.g., SAN move, key press)
        """
        self.input_buffer = ""

        with self.term.cbreak():
            while True:
                key = self.term.inkey(timeout=None)

                if not key:
                    continue

                # Handle special keys
                if key.name == "KEY_ENTER":
                    result = self.input_buffer
                    self.input_buffer = ""
                    return result
                elif key.name == "KEY_BACKSPACE" or key.name == "KEY_DELETE":
                    if self.input_buffer:
                        self.input_buffer = self.input_buffer[:-1]
                elif key.name == "KEY_ESCAPE":
                    return "q"  # Treat Escape as quit
                elif key.is_sequence:
                    # Ignore other special sequences for now
                    continue
                else:
                    # Regular character
                    self.input_buffer += str(key)

                # Re-render input area
                self._render_input()

    def get_key_input(self):
        """Get a single key press or mouse event for cursor navigation.

        Returns:
            Key object from blessed Terminal (may be keyboard or mouse event)
        """
        with self.term.cbreak(), self.term.mouse_enabled(clicks=True, report_drag=True):
            return self.term.inkey(timeout=None)

    def wait_for_keypress(self) -> None:
        """Wait for a keyboard press, ignoring mouse events.
        
        This is used for "Press any key to continue" prompts where
        we don't want residual mouse events to trigger continuation.
        """
        with self.term.cbreak():
            while True:
                key = self.term.inkey(timeout=None)
                
                # Ignore mouse events (they have name "KEY_MOUSE" in blessed)
                if key.name == "KEY_MOUSE":
                    continue
                
                # Any keyboard input is accepted
                return

    def show_error(self, message: str) -> None:
        """Display an error message to the user.

        Args:
            message: Error message to display
        """
        error_msg = f"ERROR: {message}"
        self.status_messages.append(error_msg)

    def show_message(self, message: str) -> None:
        """Display an informational message to the user.

        Args:
            message: Message to display
        """
        self.status_messages.append(message)

    def _get_board_start_x(self) -> int:
        """Calculate the X coordinate where the board starts.

        The board is centered in the terminal, so this calculates the
        offset based on terminal width.

        Returns:
            X coordinate of the left edge of the a-file squares
        """
        board_total_width = 8 * self.SQUARE_WIDTH + 10
        center_offset = max(0, (self.term.width - board_total_width) // 2)
        return center_offset + self.BOARD_START_X

    def pixel_to_square(self, x: int, y: int) -> Optional[Square]:
        """Convert terminal coordinates to a board square.

        Args:
            x: Terminal X coordinate (0-indexed from left)
            y: Terminal Y coordinate (0-indexed from top)

        Returns:
            Square at the given coordinates, or None if outside the board
        """
        board_x = self._get_board_start_x()
        board_y = self.BOARD_START_Y

        # Check if click is within board bounds
        board_width = 8 * self.SQUARE_WIDTH
        board_height = 8 * self.SQUARE_HEIGHT

        if x < board_x or x >= board_x + board_width:
            return None
        if y < board_y or y >= board_y + board_height:
            return None

        # Calculate file (a-h) from X coordinate
        file_idx = (x - board_x) // self.SQUARE_WIDTH
        if file_idx < 0 or file_idx > 7:
            return None

        # Calculate rank (1-8) from Y coordinate
        # Board renders rank 8 at top (y=board_y), rank 1 at bottom
        rank_from_top = (y - board_y) // self.SQUARE_HEIGHT
        if rank_from_top < 0 or rank_from_top > 7:
            return None

        # Convert to actual rank (8 at top, 1 at bottom)
        rank = 8 - rank_from_top

        # Convert file index to letter
        file = chr(ord('a') + file_idx)

        return Square(file=file, rank=rank)

    def prompt_promotion_choice(self) -> Piece:
        """Prompt user to choose a piece for pawn promotion.

        Displays a dialog allowing the user to choose between
        Queen, Rook, Bishop, or Knight. Pressing Enter without
        a selection defaults to Queen.

        Returns:
            The chosen piece type (QUEEN, ROOK, BISHOP, or KNIGHT)
        """
        # Calculate dialog position (center of screen)
        dialog_width = 50
        dialog_height = 9
        dialog_x = (self.term.width - dialog_width) // 2
        dialog_y = (self.term.height - dialog_height) // 2

        # Draw dialog box
        with self.term.cbreak():
            # Top border
            print(self.term.move_xy(dialog_x, dialog_y) + 
                  "╔" + "═" * (dialog_width - 2) + "╗")
            
            # Title
            title = "Pawn Promotion"
            title_padding = (dialog_width - 2 - len(title)) // 2
            print(self.term.move_xy(dialog_x, dialog_y + 1) + 
                  "║" + " " * title_padding + 
                  self._safe_format(title, self.term.bold) + 
                  " " * (dialog_width - 2 - title_padding - len(title)) + "║")
            
            # Separator
            print(self.term.move_xy(dialog_x, dialog_y + 2) + 
                  "╟" + "─" * (dialog_width - 2) + "╢")
            
            # Options
            options = [
                "Q - Queen  (♕) [default]",
                "R - Rook   (♖)",
                "B - Bishop (♗)",
                "N - Knight (♘)",
            ]
            for i, option in enumerate(options):
                option_padding = (dialog_width - 2 - len(option)) // 2
                print(self.term.move_xy(dialog_x, dialog_y + 3 + i) + 
                      "║" + " " * option_padding + option + 
                      " " * (dialog_width - 2 - option_padding - len(option)) + "║")
            
            # Bottom border
            print(self.term.move_xy(dialog_x, dialog_y + 7) + 
                  "╟" + "─" * (dialog_width - 2) + "╢")
            
            prompt = "Press Q/R/B/N or Enter for Queen:"
            prompt_padding = (dialog_width - 2 - len(prompt)) // 2
            print(self.term.move_xy(dialog_x, dialog_y + 8) + 
                  "║" + " " * prompt_padding + prompt + 
                  " " * (dialog_width - 2 - prompt_padding - len(prompt)) + "║")
            
            print(self.term.move_xy(dialog_x, dialog_y + 9) + 
                  "╚" + "═" * (dialog_width - 2) + "╝")
            
            sys.stdout.flush()

            # Wait for valid input
            while True:
                key = self.term.inkey(timeout=None)
                choice = str(key).upper()

                if choice == 'Q' or key.name == 'KEY_ENTER':
                    return Piece.QUEEN
                elif choice == 'R':
                    return Piece.ROOK
                elif choice == 'B':
                    return Piece.BISHOP
                elif choice == 'N':
                    return Piece.KNIGHT
                # Ignore other keys and wait for valid input
