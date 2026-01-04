"""Entry point for PyChess."""

import sys

from pychess.model.game_state import GameState
from pychess.model.square import Square
from pychess.notation.san import san_to_move, move_to_san
from pychess.rules.move import Move
from pychess.rules.validator import get_legal_moves, is_move_legal
from pychess.rules.game_logic import get_game_result
from pychess.ui.terminal import TerminalRenderer
from pychess.ui.cursor import CursorState
from pychess.ui.input_handler import InputHandler, InputType


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
    """Run the main game loop with cursor-based navigation.

    Args:
        renderer: Terminal renderer instance
    """
    game_state = GameState.initial()
    cursor_state = CursorState.initial()
    input_handler = InputHandler()
    input_mode = "cursor"  # "cursor" or "san"
    status_messages = ["Welcome to PyChess!", "Use arrow keys to move cursor, Enter to select"]

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
            renderer.show_message("Press any key to exit...")
            renderer.get_key_input()
            break

        # Get legal moves for highlighting (if piece selected)
        legal_move_squares = set()
        if cursor_state.selected_square:
            # Find legal moves from selected square
            all_legal_moves = get_legal_moves(game_state)
            for move in all_legal_moves:
                if move.from_square == cursor_state.selected_square:
                    legal_move_squares.add(move.to_square)

        # Render current position with cursor
        renderer.render(
            game_state,
            selected_square=cursor_state.selected_square,
            cursor_square=cursor_state.position,
            legal_moves=legal_move_squares,
            status_messages=status_messages
        )

        # Update input prompt
        renderer._render_input(mode=input_mode)

        # Handle input based on mode
        if input_mode == "san":
            # SAN input mode
            user_input = renderer.get_input().strip()

            # Handle empty input
            if not user_input:
                continue

            # Check for mode toggle
            if user_input == '/':
                input_mode = "cursor"
                status_messages = ["Switched to cursor mode"]
                continue

            # Handle commands
            if user_input.lower() == 'q':
                print(renderer.term.home() + renderer.term.clear())
                confirm = input("Are you sure you want to quit? (y/n): ")
                if confirm.lower() == 'y':
                    break
                continue

            if user_input.lower() == 'r':
                game_state = GameState.initial()
                cursor_state = CursorState.initial()
                status_messages = ["Game restarted!"]
                continue

            if user_input.lower() == '?':
                renderer.show_message("Enter moves in SAN notation (e.g., e4, Nf3)")
                renderer.show_message("Press / to switch to cursor mode")
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

            except ValueError:
                renderer.show_error(f"Invalid move: {user_input}")
                continue

        else:
            # Cursor mode
            # Get key input
            key = renderer.get_key_input()
            event = input_handler.process_key(key)

            # Handle input events
            if event.input_type == InputType.MOVE_UP:
                cursor_state = cursor_state.move_up()

            elif event.input_type == InputType.MOVE_DOWN:
                cursor_state = cursor_state.move_down()

            elif event.input_type == InputType.MOVE_LEFT:
                cursor_state = cursor_state.move_left()

            elif event.input_type == InputType.MOVE_RIGHT:
                cursor_state = cursor_state.move_right()

            elif event.input_type == InputType.SELECT:
                # Try to make a move or select a piece
                move_attempt = cursor_state.attempt_move()

                if move_attempt:
                    from_square, to_square = move_attempt

                    # Find matching legal move
                    legal_moves = get_legal_moves(game_state)
                    matching_move = None

                    for move in legal_moves:
                        if move.from_square == from_square and move.to_square == to_square:
                            matching_move = move
                            break

                    if matching_move:
                        # Valid move - apply it
                        from pychess.notation.pgn import _apply_san_move
                        san_notation = move_to_san(game_state, matching_move)
                        game_state = _apply_san_move(game_state, san_notation, matching_move)
                        cursor_state = cursor_state.clear_selection()
                        status_messages = [f"Move: {san_notation}"]
                    else:
                        # Invalid move
                        renderer.show_error("Illegal move")
                        cursor_state = cursor_state.clear_selection()
                else:
                    # Select piece at cursor
                    piece_info = game_state.board.get(cursor_state.position)

                    if piece_info:
                        piece_type, piece_color = piece_info
                        # Check if it's the current player's piece
                        if piece_color == game_state.active_color:
                            cursor_state = cursor_state.select_square()
                            status_messages = [f"Selected {piece_color.name} {piece_type.name}"]
                        else:
                            renderer.show_error("Not your piece!")
                    else:
                        # Empty square - deselect
                        cursor_state = cursor_state.clear_selection()

            elif event.input_type == InputType.CANCEL:
                cursor_state = cursor_state.cancel_selection()
                status_messages = ["Selection cancelled"]

            elif event.input_type == InputType.QUIT:
                # Clear screen for confirmation prompt
                print(renderer.term.home() + renderer.term.clear())
                confirm = input("Are you sure you want to quit? (y/n): ")
                if confirm.lower() == 'y':
                    break

            elif event.input_type == InputType.UNDO:
                renderer.show_message("Undo not yet implemented")

            elif event.input_type == InputType.RESTART:
                game_state = GameState.initial()
                cursor_state = CursorState.initial()
                status_messages = ["Game restarted!"]

            elif event.input_type == InputType.HELP:
                renderer.show_message("Arrow keys=move cursor, Enter=select/move")
                renderer.show_message("q=quit, r=restart, Esc=cancel, /=SAN mode")

            elif event.input_type == InputType.TOGGLE_MODE:
                input_mode = "san"
                cursor_state = cursor_state.clear_selection()
                status_messages = ["Switched to SAN input mode - type moves like 'e4'"]


if __name__ == "__main__":
    main()
