"""Entry point for PyChess."""

import sys

from pychess.model.game_state import GameState
from pychess.notation.san import san_to_move, move_to_san
from pychess.rules.validator import get_legal_moves, is_move_legal
from pychess.rules.game_logic import get_game_result
from pychess.ui.terminal import TerminalRenderer


def main() -> None:
    """Main entry point for the pychess command."""
    renderer = TerminalRenderer(use_unicode=True)

    try:
        # Initialize renderer
        renderer.initialize()

        # Start game loop
        run_game(renderer)

    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nGame interrupted by user.", file=sys.stderr)
    finally:
        # Clean up
        renderer.cleanup()


def run_game(renderer: TerminalRenderer) -> None:
    """Run the main game loop.

    Args:
        renderer: Terminal renderer instance
    """
    game_state = GameState.initial()
    status_messages = ["Welcome to PyChess!", "Enter moves in SAN notation (e.g., e4, Nf3)"]

    while True:
        # Check for game end
        result = get_game_result(game_state)
        if result:
            if result == "1-0":
                status_messages.append("Game Over: White wins!")
            elif result == "0-1":
                status_messages.append("Game Over: Black wins!")
            else:
                status_messages.append("Game Over: Draw!")

            # Render final position
            renderer.render(game_state, status_messages=status_messages)
            renderer.show_message("Press Enter to exit...")
            renderer.get_input()
            break

        # Render current position
        renderer.render(game_state, status_messages=status_messages)

        # Get user input
        user_input = renderer.get_input().strip()

        # Handle special commands
        if not user_input:
            continue

        if user_input.lower() == 'q':
            confirm = input("Are you sure you want to quit? (y/n): ")
            if confirm.lower() == 'y':
                break
            continue

        if user_input.lower() == 'u':
            # Undo last move
            if len(game_state.move_history) > 0:
                # For now, just show message - full undo will be implemented later
                renderer.show_message("Undo not yet implemented")
            else:
                renderer.show_error("No moves to undo")
            continue

        if user_input.lower() == 'r':
            # Restart game
            game_state = GameState.initial()
            status_messages = ["Game restarted!"]
            continue

        if user_input.lower() == '?':
            # Show help
            renderer.show_message("Help: Enter moves in SAN notation")
            renderer.show_message("Commands: q=quit, u=undo, r=restart")
            continue

        # Try to parse as SAN move
        try:
            move = san_to_move(game_state, user_input)

            # Verify move is legal
            if not is_move_legal(game_state, move):
                renderer.show_error(f"Illegal move: {user_input}")
                continue

            # Apply the move
            from pychess.notation.pgn import _apply_san_move
            san_notation = move_to_san(game_state, move)
            game_state = _apply_san_move(game_state, san_notation, move)

            status_messages = [f"Move: {san_notation}"]

        except ValueError as e:
            renderer.show_error(f"Invalid move: {user_input}")
            continue


if __name__ == "__main__":
    main()
