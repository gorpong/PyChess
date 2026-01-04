"""Abstract renderer interface for the chess UI.

This interface separates the rendering logic from the game logic,
allowing different rendering implementations (terminal, GUI, etc.).
"""

from abc import ABC, abstractmethod
from typing import Optional

from pychess.model.game_state import GameState
from pychess.model.square import Square


class Renderer(ABC):
    """Abstract interface for rendering the chess board and UI."""

    @abstractmethod
    def initialize(self) -> None:
        """Initialize the renderer and set up the display."""
        pass

    @abstractmethod
    def cleanup(self) -> None:
        """Clean up resources and restore terminal state."""
        pass

    @abstractmethod
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
        pass

    @abstractmethod
    def get_input(self) -> str:
        """Get input from the user.

        Returns:
            Input string (e.g., SAN move, key press)
        """
        pass

    @abstractmethod
    def show_error(self, message: str) -> None:
        """Display an error message to the user.

        Args:
            message: Error message to display
        """
        pass

    @abstractmethod
    def show_message(self, message: str) -> None:
        """Display an informational message to the user.

        Args:
            message: Message to display
        """
        pass

    @abstractmethod
    def check_terminal_size(self) -> tuple[int, int]:
        """Check if terminal size meets minimum requirements.

        Returns:
            Tuple of (width, height)

        Raises:
            ValueError: If terminal is too small
        """
        pass
