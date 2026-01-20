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
    print("-" * 70)
    print(f"{'Name':<20} {'White':<12} {'Black':<12} {'Result':<10} {'Moves'}")
    print("-" * 70)
    
    for game in games:
        status = game.result if game.is_complete else "(ongoing)"
        print(
            f"{game.name:<20} "
            f"{game.white:<12} "
            f"{game.black:<12} "
            f"{status:<10} "
            f"{game.move_count}"
        )
    
    print("-" * 70)
    print("\nTo load a game: pychess --load \"<name>\"")


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
    arguments and handles --list-games and --load commands.
    
    Returns:
        None if --list-games was used (program should exit)
        Tuple of (GameState, PGNHeaders, game_name) if --load was used
        None if no arguments (start new game)
        
    Raises:
        SystemExit: On invalid arguments or --list-games
    """
    args = parse_args(sys.argv[1:])
    manager = SaveManager()
    
    # Handle --list-games
    if args.list_games:
        handle_list_games(manager)
        sys.exit(0)
    
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
