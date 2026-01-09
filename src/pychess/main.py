"""Entry point for PyChess."""

import sys
from typing import Optional

from pychess.ui.terminal import TerminalRenderer
from pychess.ai.engine import AIEngine, Difficulty
from pychess.controller.game_session import GameSession


def select_game_mode(term) -> tuple[str, Optional[Difficulty]]:
    """Show game mode selection menu.

    Args:
        term: Terminal instance

    Returns:
        Tuple of (mode, difficulty) where mode is "multiplayer" or "ai"
        and difficulty is None for multiplayer or a Difficulty for AI
    """
    print(term.home() + term.clear())

    menu_text = """
╔══════════════════════════════════════════════════════════════════════╗
║                     PyChess - Game Mode Selection                    ║
╚══════════════════════════════════════════════════════════════════════╝

Select a game mode:

  1. Multiplayer (Two Players)
  2. vs AI - Easy (Random moves)
  3. vs AI - Medium (Material-based)
  4. vs AI - Hard (Material + Positional)

  q. Quit

Enter your choice (1-4, q): """

    print(menu_text, end="", flush=True)

    with term.cbreak():
        while True:
            key = term.inkey(timeout=None)
            choice = str(key).lower()

            if choice == '1':
                return ("multiplayer", None)
            elif choice == '2':
                return ("ai", Difficulty.EASY)
            elif choice == '3':
                return ("ai", Difficulty.MEDIUM)
            elif choice == '4':
                return ("ai", Difficulty.HARD)
            elif choice == 'q':
                sys.exit(0)


def main() -> None:
    """Main entry point for the pychess command."""
    renderer = TerminalRenderer(use_unicode=True)

    try:
        # Initialize renderer
        renderer.initialize()

        # Select game mode
        mode, difficulty = select_game_mode(renderer.term)

        # Create AI if needed
        ai_engine = AIEngine(difficulty) if mode == "ai" else None

        # Create and run game session
        session = GameSession(renderer, ai_engine)
        session.run()

    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nGame interrupted by user.", file=sys.stderr)
    finally:
        # Clean up
        renderer.cleanup()


if __name__ == "__main__":
    main()
