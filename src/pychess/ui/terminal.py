"""Terminal-based renderer using the blessed library.

This module implements the Renderer interface using blessed for
terminal control, colors, and input handling.
"""

import sys
from typing import Optional

from blessed import Terminal

from pychess.model.game_state import GameState
from pychess.model.piece import Color
from pychess.model.square import Square
from pychess.ui.renderer import Renderer
from pychess.ui.board_view import BoardView


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

    def initialize(self) -> None:
        """Initialize the renderer and set up the display."""
        # Check terminal size
        self.check_terminal_size()

        # Clear screen
        print(self.term.clear())

        # Hide cursor
        print(self.term.hide_cursor(), end="", flush=True)

    def cleanup(self) -> None:
        """Clean up resources and restore terminal state."""
        # Show cursor
        print(self.term.normal_cursor(), end="", flush=True)

        # Clear screen
        print(self.term.clear())

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
    ) -> None:
        """Render the current game state.

        Args:
            game_state: Current game state to render
            selected_square: Currently selected square (if any)
            cursor_square: Square where cursor is positioned (if any)
            legal_moves: Set of legal destination squares to highlight (if any)
            status_messages: List of status messages to display
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
            legal_moves
        )

        # Render status area
        self._render_status(game_state)

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
    ) -> None:
        """Render the chess board with pieces and highlighting.

        Args:
            board: Board to render
            selected_square: Currently selected square
            cursor_square: Square where cursor is positioned
            legal_moves: Set of legal destination squares
        """
        files = "abcdefgh"

        # Calculate center offset if terminal is wider than needed
        board_total_width = 8 * self.SQUARE_WIDTH + 10
        center_x = max(0, (self.term.width - board_total_width) // 2)

        # Draw title
        title = "PyChess - Terminal Chess Game"
        title_x = center_x + (board_total_width - len(title)) // 2
        print(self.term.move_xy(title_x, 1) + self._safe_format(title, self.term.bold))

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

    def _render_status(self, game_state: GameState) -> None:
        """Render the status area with game information.

        Args:
            game_state: Current game state
        """
        status_y = self.BOARD_START_Y + 8 * self.SQUARE_HEIGHT + 3

        # Display turn
        turn_text = f"Turn: {game_state.active_color.name}"
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

    def _render_input(self) -> None:
        """Render the input area."""
        input_y = self.term.height - 3

        # Draw input prompt
        prompt = "Enter move (SAN): "
        print(self.term.move_xy(5, input_y) + self._safe_format(prompt, self.term.bold) + self.input_buffer)

        # Draw help text (with dim if available, otherwise normal)
        help_text = "Commands: q=quit, u=undo, r=restart, ?=help"
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
