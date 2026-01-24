"""Command-line interface for PyChess.

This module handles argument parsing and CLI commands for listing
and loading saved games.
"""

import argparse
import sys
from typing import Optional

from pychess.model.game_state import GameState
from pychess.notation.pgn import PGNHeaders
from pychess.persistence.save_manager import (
    SaveManager,
    SavedGameInfo,
    InvalidGameNameError,
    validate_game_name,
)
from pychess.ui.terminal import format_elapsed_time


class CLIError(Exception):
    """Raised for CLI-related errors."""
    pass


def parse_args(args: list[str]) -> argparse.Namespace:
    """Parse command-line arguments.
    
    Args:
        args: List of command-line arguments (typically sys.argv[1:])
        
    Returns:
        Parsed arguments namespace
    """
    parser = argparse.ArgumentParser(
        prog="pychess",
        description="Terminal-based ASCII Chess Game",
        epilog="Start a new game by running without arguments.",
    )
    
    parser.add_argument(
        "--list-games",
        action="store_true",
        help="List all saved games",
    )
    
    parser.add_argument(
        "--load",
        metavar="NAME",
        help="Load a saved game by name",
    )
    
    parser.add_argument(
        "--show-game",
        metavar="NAME",
        help="Display a saved game in magazine-style format",
    )
    
    return parser.parse_args(args)


def validate_and_exit_on_bad_name(name: str) -> str:
    """Validate a game name and exit immediately if invalid.
    
    This function is the security gate for user-provided game names.
    If the name contains any path traversal characters or other
    dangerous input, the program exits immediately with an error.
    
    Args:
        name: The game name to validate
        
    Returns:
        The validated name if valid
        
    Note:
        Exits the program with code 1 if the name is invalid.
        Does NOT provide alternatives or retry options.
    """
    try:
        return validate_game_name(name)
    except InvalidGameNameError as e:
        print(f"Error: Invalid game name: {name}", file=sys.stderr)
        print("Game names cannot contain path characters (/, \\, .., :)", file=sys.stderr)
        sys.exit(1)


def handle_list_games(manager: SaveManager) -> None:
    """Handle the --list-games command.
    
    Prints a formatted list of all saved games with their metadata.
    
    Args:
        manager: SaveManager instance
    """
    games = manager.list_games()
    
    if not games:
        print("No saved games found.")
        print("\nStart a new game by running: pychess")
        return
    
    print(f"Saved Games ({len(games)}/10):")
    print("-" * 82)
    print(f"{'Name':<20} {'White':<12} {'Black':<12} {'Result':<10} {'Moves':<6} {'Time'}")
    print("-" * 82)
    
    for game in games:
        status = game.result if game.is_complete else "(ongoing)"
        time_str = format_elapsed_time(game.total_time_seconds)
        print(
            f"{game.name:<20} "
            f"{game.white:<12} "
            f"{game.black:<12} "
            f"{status:<10} "
            f"{game.move_count:<6} "
            f"{time_str}"
        )
    
    print("-" * 82)
    print("\nTo load a game: pychess --load \"<name>\"")


def handle_show_game(manager: SaveManager, name: str) -> None:
    """Handle the --show-game command.
    
    Displays a saved game in a human-friendly "magazine style" format
    with headers and one move pair per line.
    
    Args:
        manager: SaveManager instance
        name: Name of the game to display
        
    Raises:
        CLIError: If the game name is invalid or game not found
    """
    # Validate name - this is security critical
    try:
        validated_name = validate_game_name(name)
    except InvalidGameNameError:
        raise CLIError(
            f"Invalid game name: {name}\n"
            "Game names cannot contain path characters (/, \\, .., :)"
        )
    
    # Try to load the game
    try:
        state, headers = manager.load_game(validated_name)
    except FileNotFoundError:
        raise CLIError(f"Game not found: {name}")
    
    # Display header section
    print()
    print("=" * 60)
    print(f"  Game: {validated_name}")
    print("=" * 60)
    print()
    print(f"  White: {headers.white:<20} Black: {headers.black}")
    print(f"  Date:  {headers.date:<20} Result: {headers.result}")
    print(f"  Time:  {format_elapsed_time(headers.total_time_seconds)}")
    print()
    print("-" * 60)
    print("  Moves:")
    print("-" * 60)
    
    # Display moves in magazine style (one pair per line)
    moves = state.move_history
    
    if not moves:
        print("  (No moves yet)")
    else:
        for i in range(0, len(moves), 2):
            move_num = (i // 2) + 1
            white_move = moves[i]
            black_move = moves[i + 1] if i + 1 < len(moves) else ""
            
            # Format: "  1.  e4       e5"
            print(f"  {move_num:>3}.  {white_move:<8} {black_move}")
    
    print()
    print("-" * 60)
    
    # Show result at the end if game is complete
    if headers.result in ("1-0", "0-1", "1/2-1/2"):
        if headers.result == "1-0":
            result_text = "White wins"
        elif headers.result == "0-1":
            result_text = "Black wins"
        else:
            result_text = "Draw"
        print(f"  Result: {headers.result} ({result_text})")
    else:
        print("  Game in progress...")
    
    print("=" * 60)
    print()


def handle_load_game(
    manager: SaveManager,
    name: str
) -> tuple[GameState, PGNHeaders]:
    """Handle the --load command.
    
    Validates the game name and loads the game state.
    
    Args:
        manager: SaveManager instance
        name: Name of the game to load
        
    Returns:
        Tuple of (GameState, PGNHeaders)
        
    Raises:
        CLIError: If the game name is invalid or game not found
    """
    # Validate name - this is security critical
    try:
        validated_name = validate_game_name(name)
    except InvalidGameNameError:
        raise CLIError(
            f"Invalid game name: {name}\n"
            "Game names cannot contain path characters (/, \\, .., :)"
        )
    
    # Try to load the game
    try:
        return manager.load_game(validated_name)
    except FileNotFoundError:
        raise CLIError(f"Game not found: {name}")


def run_cli() -> Optional[tuple[GameState, PGNHeaders, str]]:
    """Run CLI argument handling.
    
    This is the main entry point for CLI processing. It parses
    arguments and handles --list-games, --show-game, and --load commands.
    
    Returns:
        None if --list-games or --show-game was used (program should exit)
        Tuple of (GameState, PGNHeaders, game_name) if --load was used
        None if no arguments (start new game)
        
    Raises:
        SystemExit: On invalid arguments or --list-games/--show-game
    """
    args = parse_args(sys.argv[1:])
    manager = SaveManager()
    
    # Handle --list-games
    if args.list_games:
        handle_list_games(manager)
        sys.exit(0)
    
    # Handle --show-game
    if args.show_game:
        # Validate and exit on bad name - no second chances
        validated_name = validate_and_exit_on_bad_name(args.show_game)
        
        try:
            handle_show_game(manager, validated_name)
            sys.exit(0)
        except CLIError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
    
    # Handle --load
    if args.load:
        # Validate and exit on bad name - no second chances
        validated_name = validate_and_exit_on_bad_name(args.load)
        
        try:
            state, headers = handle_load_game(manager, validated_name)
            return (state, headers, validated_name)
        except CLIError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
    
    # No CLI arguments - start new game
    return None
