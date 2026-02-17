"""Entry point for PyChess."""

import argparse
import sys
import time
from typing import Optional

from pychess.ui.terminal import TerminalRenderer
from pychess.ai.engine import AIEngine, Difficulty
from pychess.controller.game_session import GameSession
from pychess.cli import run_cli, CLIError
from pychess.model.game_state import GameState
from pychess.notation.pgn import PGNHeaders
from pychess.persistence.save_manager import SaveManager, sanitize_game_name, InvalidGameNameError


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


def prompt_save_game(
    renderer,
    session: GameSession,
    save_manager: SaveManager,
    game_name: Optional[str] = None
) -> None:
    """Prompt user to save an incomplete game.
    
    Args:
        renderer: Terminal renderer
        session: Current game session
        save_manager: Save manager instance
        game_name: Existing game name (for loaded games)
    """
    # Only prompt for incomplete games with moves
    if not session.game_state.move_history:
        return
    
    print(renderer.term.home() + renderer.term.clear())
    
    # Ask if they want to save
    save_choice = input("Save this game before quitting? (y/n): ").strip().lower()
    if save_choice != 'y':
        return
    
    # Get game name
    if game_name:
        use_existing = input(f"Save as '{game_name}'? (y/n): ").strip().lower()
        if use_existing == 'y':
            name = game_name
        else:
            name = input("Enter a name for this game: ").strip()
    else:
        name = input("Enter a name for this game: ").strip()
    
    if not name:
        print("No name provided. Game not saved.")
        return
    
    # Sanitize the name
    try:
        sanitized_name = sanitize_game_name(name)
    except InvalidGameNameError as e:
        print(f"Invalid name: {e}")
        return

    # Determine game mode string
    if session.is_multiplayer:
        game_mode = "Multiplayer"
    elif session.ai_engine:
        game_mode = session.ai_engine.difficulty.name.capitalize()
    else:
        game_mode = "Multiplayer"
    
    # Create headers
    headers = PGNHeaders(
        event="Casual Game",
        site="Terminal",
        white="White" if session.is_multiplayer else "Player",
        black="Black" if session.is_multiplayer else "Computer",
        result="*",  # Incomplete
        total_time_seconds=int(time.time() - session.start_time),
        game_mode=game_mode,
    )
    
    # Save the game
    try:
        filepath = save_manager.save_game(sanitized_name, session.game_state, headers)
        print(f"Game saved as '{sanitized_name}'")
    except Exception as e:
        print(f"Error saving game: {e}")


def parse_main_args() -> argparse.Namespace:
    """Parse command-line arguments for main entry point.
    
    Returns:
        Parsed arguments namespace.
    """
    parser = argparse.ArgumentParser(
        prog="pychess",
        description="Terminal-based ASCII Chess Game",
        add_help=False,  # We handle help via run_cli for terminal mode
    )
    parser.add_argument(
        "--web",
        action="store_true",
        help="Start the web UI instead of terminal UI",
    )
    # Parse known args to allow other args to pass through to run_cli
    args, _ = parser.parse_known_args()
    return args


def main() -> None:
    """Main entry point for the pychess command."""
    # Check for --web flag first
    args = parse_main_args()
    if args.web:
        from pychess.web.app import main as web_main
        web_main()
        return
    
    # Handle CLI arguments first (before initializing renderer)
    loaded_game = run_cli()
    
    renderer = TerminalRenderer(use_unicode=True)
    save_manager = SaveManager()
    game_name: Optional[str] = None

    try:
        # Initialize renderer
        renderer.initialize()

        if loaded_game:
            # Load existing game
            state, headers, game_name = loaded_game
            
            # Restore AI engine from saved game mode
            ai_engine = None
            game_mode_str = headers.game_mode
            
            if game_mode_str == "Easy":
                ai_engine = AIEngine(Difficulty.EASY)
            elif game_mode_str == "Medium":
                ai_engine = AIEngine(Difficulty.MEDIUM)
            elif game_mode_str == "Hard":
                ai_engine = AIEngine(Difficulty.HARD)
            elif game_mode_str == "Multiplayer" and headers.black == "Computer":
                # Legacy AI game from before GameMode header was added
                # Default to Easy difficulty since we don't know the original
                ai_engine = AIEngine(Difficulty.EASY)
                game_mode_str = "Easy"  # Update for display
            # "Multiplayer" with human Black = no AI engine

            # Create session with loaded state
            session = GameSession(renderer, ai_engine)
            session.game_state = state
            
            # Restore elapsed time from saved game
            # Adjust start_time so elapsed calculations are cumulative
            if headers.total_time_seconds > 0:
                session.start_time = time.time() - headers.total_time_seconds
            
            mode_display = game_mode_str if game_mode_str != "Multiplayer" else "Two Players"
            session.status_messages = [
                f"Loaded game: {game_name}",
                f"{headers.white} vs {headers.black} ({mode_display})",
            ]
        else:
            # Select game mode for new game
            mode, difficulty = select_game_mode(renderer.term)

            # Create AI if needed
            ai_engine = AIEngine(difficulty) if mode == "ai" else None

            # Create new game session
            session = GameSession(renderer, ai_engine)
        
        # Run the game
        session.run()
        
        # After game ends, prompt to save if incomplete
        from pychess.rules.game_logic import get_game_result
        result = get_game_result(session.game_state)
        
        if result:
            # Game completed - save automatically with result
            if session.game_state.move_history:
                # Determine game mode string
                if session.is_multiplayer:
                    game_mode = "Multiplayer"
                elif session.ai_engine:
                    game_mode = session.ai_engine.difficulty.name.capitalize()
                else:
                    game_mode = "Multiplayer"
                
                headers = PGNHeaders(
                    event="Casual Game",
                    site="Terminal",
                    white="White" if session.is_multiplayer else "Player",
                    black="Black" if session.is_multiplayer else "Computer",
                    result=result,
                    total_time_seconds=int(time.time() - session.start_time),
                    game_mode=game_mode,
                )
                
                # Generate a default name if not loaded
                if not game_name:
                    # Find next available game number
                    existing = save_manager.list_games()
                    game_num = len(existing) + 1
                    game_name = f"Game_{game_num}"
                
                try:
                    save_manager.save_game(game_name, session.game_state, headers)
                except Exception:
                    pass  # Don't fail on save errors for completed games
        else:
            # Game incomplete - prompt to save
            prompt_save_game(renderer, session, save_manager, game_name)

    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        # Handle Ctrl+C - prompt to save
        print("\n")
        try:
            prompt_save_game(renderer, session, save_manager, game_name)
        except Exception:
            pass
        print("Game interrupted by user.", file=sys.stderr)
    finally:
        # Clean up
        renderer.cleanup()


if __name__ == "__main__":
    main()
