"""Input handling for keyboard and terminal interactions.

This module processes keyboard input for cursor movement, piece selection,
and command execution.
"""

from dataclasses import dataclass
from enum import Enum, auto
from typing import Optional


class InputType(Enum):
    """Types of input actions."""
    MOVE_UP = auto()
    MOVE_DOWN = auto()
    MOVE_LEFT = auto()
    MOVE_RIGHT = auto()
    SELECT = auto()  # Enter key
    CANCEL = auto()  # Escape key
    QUIT = auto()
    UNDO = auto()
    RESTART = auto()
    HELP = auto()
    SAN_INPUT = auto()  # Text input for SAN notation
    UNKNOWN = auto()


@dataclass
class InputEvent:
    """Represents a processed input event."""
    input_type: InputType
    data: Optional[str] = None  # For SAN_INPUT, contains the move string


class InputHandler:
    """Handles keyboard input processing."""

    def __init__(self):
        """Initialize input handler."""
        self.input_mode = "cursor"  # "cursor" or "text"

    def process_key(self, key) -> InputEvent:
        """Process a key press from blessed Terminal.

        Args:
            key: Key object from blessed Terminal.inkey()

        Returns:
            InputEvent representing the action
        """
        # Handle special keys
        if key.name == "KEY_UP":
            return InputEvent(InputType.MOVE_UP)
        elif key.name == "KEY_DOWN":
            return InputEvent(InputType.MOVE_DOWN)
        elif key.name == "KEY_LEFT":
            return InputEvent(InputType.MOVE_LEFT)
        elif key.name == "KEY_RIGHT":
            return InputEvent(InputType.MOVE_RIGHT)
        elif key.name == "KEY_ENTER":
            return InputEvent(InputType.SELECT)
        elif key.name == "KEY_ESCAPE":
            return InputEvent(InputType.CANCEL)

        # Handle character keys
        char = str(key).lower()

        if char == 'q':
            return InputEvent(InputType.QUIT)
        elif char == 'u':
            return InputEvent(InputType.UNDO)
        elif char == 'r':
            return InputEvent(InputType.RESTART)
        elif char == '?':
            return InputEvent(InputType.HELP)

        # Unknown key
        return InputEvent(InputType.UNKNOWN)

    def set_mode(self, mode: str) -> None:
        """Set input mode.

        Args:
            mode: "cursor" for cursor navigation, "text" for SAN input
        """
        if mode in ("cursor", "text"):
            self.input_mode = mode

    def get_mode(self) -> str:
        """Get current input mode.

        Returns:
            Current mode string
        """
        return self.input_mode
