"""Save manager for persisting chess games.

This module handles saving, loading, and managing PGN game files
with proper security validation to prevent path traversal attacks.
"""

import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from pychess.model.game_state import GameState
from pychess.notation.pgn import PGNHeaders, game_to_pgn, pgn_to_game


class InvalidGameNameError(Exception):
    """Raised when a game name contains invalid or dangerous characters."""
    pass


# Maximum number of saved games
MAX_SAVED_GAMES = 10

# Maximum length for game names
MAX_NAME_LENGTH = 50

# Pattern for dangerous path characters
# Matches: forward slash, backslash, null byte, colon (drive letter), 
# or parent directory reference (..)
DANGEROUS_PATH_PATTERN = re.compile(r'[/\\:\x00]|\.{2}')

# Pattern for valid characters after sanitization
VALID_CHARS_PATTERN = re.compile(r'^[a-zA-Z0-9_\-\.]+$')


def validate_game_name(name: str) -> str:
    """Validate a game name for security.
    
    This function checks for path traversal attempts and other
    dangerous input. It must be called before any file operations.
    
    Args:
        name: The game name to validate
        
    Returns:
        The validated name (with .pgn extension stripped if present)
        
    Raises:
        InvalidGameNameError: If the name contains dangerous characters
                              or path components
    """
    if not name or not name.strip():
        raise InvalidGameNameError("Game name cannot be empty")
    
    # Strip whitespace
    name = name.strip()
    
    # Strip .pgn extension if present
    if name.lower().endswith('.pgn'):
        name = name[:-4]
    
    if not name:
        raise InvalidGameNameError("Game name cannot be empty")
    
    # Check for hidden files (Unix-style)
    if name.startswith('.'):
        raise InvalidGameNameError(
            "Invalid game name: contains path information or special characters"
        )
    
    # Check for dangerous path characters
    if DANGEROUS_PATH_PATTERN.search(name):
        raise InvalidGameNameError(
            "Invalid game name: contains path information or special characters"
        )
    
    # Additional check: ensure no path separators even if escaped somehow
    if os.sep in name or os.altsep and os.altsep in name:
        raise InvalidGameNameError(
            "Invalid game name: contains path information or special characters"
        )
    
    return name


def sanitize_game_name(name: str) -> str:
    """Sanitize a game name for use as a filename.
    
    This converts user input into a safe filename by:
    - Converting spaces to underscores
    - Removing special characters
    - Collapsing multiple underscores
    - Truncating to max length
    
    Args:
        name: The raw user input
        
    Returns:
        A sanitized filename-safe string
        
    Raises:
        InvalidGameNameError: If the name becomes empty after sanitization
    """
    if not name or not name.strip():
        raise InvalidGameNameError("Game name cannot be empty")
    
    # Convert spaces to underscores
    result = name.replace(' ', '_')
    
    # Keep only alphanumeric, underscore, hyphen, and dot
    result = re.sub(r'[^a-zA-Z0-9_\-\.]', '', result)
    
    # Collapse multiple underscores
    result = re.sub(r'_+', '_', result)
    
    # Strip leading/trailing underscores
    result = result.strip('_')
    
    # Truncate to max length
    if len(result) > MAX_NAME_LENGTH:
        result = result[:MAX_NAME_LENGTH]
    
    if not result:
        raise InvalidGameNameError(
            "Game name contains no valid characters after sanitization"
        )
    
    return result


@dataclass
class SavedGameInfo:
    """Information about a saved game."""
    
    name: str
    white: str
    black: str
    result: str
    date: str
    move_count: int
    filepath: Path
    
    @property
    def is_complete(self) -> bool:
        """Return True if the game has ended."""
        return self.result in ("1-0", "0-1", "1/2-1/2")


class SaveManager:
    """Manages saving and loading of chess games.
    
    Games are stored as PGN files in a designated save directory.
    A maximum of 10 games can be stored, with automatic eviction
    of the oldest completed games when the limit is exceeded.
    
    Attributes:
        save_dir: Path to the directory where games are saved
    """
    
    def __init__(self, save_dir: Optional[Path] = None) -> None:
        """Initialize the save manager.
        
        Args:
            save_dir: Directory for save files. Defaults to ~/.pychess/saves/
        """
        if save_dir is None:
            save_dir = Path.home() / ".pychess" / "saves"
        
        self.save_dir = Path(save_dir)
        self._ensure_save_dir()
    
    def _ensure_save_dir(self) -> None:
        """Create the save directory if it doesn't exist."""
        self.save_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_filepath(self, name: str) -> Path:
        """Get the full filepath for a game name.
        
        Args:
            name: Validated game name
            
        Returns:
            Full path to the PGN file
        """
        return self.save_dir / f"{name}.pgn"
    
    def list_games(self) -> list[SavedGameInfo]:
        """List all saved games.
        
        Returns:
            List of SavedGameInfo objects sorted by modification time (oldest first)
        """
        games = []
        
        for filepath in self.save_dir.glob("*.pgn"):
            try:
                info = self._read_game_info(filepath)
                if info:
                    games.append(info)
            except Exception:
                # Skip corrupted files
                continue
        
        # Sort by modification time (oldest first)
        games.sort(key=lambda g: g.filepath.stat().st_mtime)
        
        return games
    
    def _read_game_info(self, filepath: Path) -> Optional[SavedGameInfo]:
        """Read game info from a PGN file without full parsing.
        
        Args:
            filepath: Path to the PGN file
            
        Returns:
            SavedGameInfo or None if file is invalid
        """
        try:
            content = filepath.read_text()
            state, headers = pgn_to_game(content)
            
            # Extract name from filename (without .pgn)
            name = filepath.stem
            
            return SavedGameInfo(
                name=name,
                white=headers.white,
                black=headers.black,
                result=headers.result,
                date=headers.date,
                move_count=len(state.move_history),
                filepath=filepath,
            )
        except Exception:
            return None
    
    def save_game(
        self,
        name: str,
        game_state: GameState,
        headers: PGNHeaders,
    ) -> Path:
        """Save a game to disk.
        
        Args:
            name: Name for the saved game
            game_state: Current game state
            headers: PGN headers for the game
            
        Returns:
            Path to the saved file
            
        Raises:
            InvalidGameNameError: If name contains dangerous characters
        """
        # Validate name for security
        validated_name = validate_game_name(name)
        
        # Enforce save limit before saving
        self._enforce_save_limit(validated_name)
        
        # Generate PGN content
        pgn_content = game_to_pgn(game_state, headers)
        
        # Write to file
        filepath = self._get_filepath(validated_name)
        filepath.write_text(pgn_content)
        
        return filepath
    
    def load_game(self, name: str) -> tuple[GameState, PGNHeaders]:
        """Load a game from disk.
        
        Args:
            name: Name of the saved game
            
        Returns:
            Tuple of (GameState, PGNHeaders)
            
        Raises:
            InvalidGameNameError: If name contains dangerous characters
            FileNotFoundError: If the game doesn't exist
        """
        # Validate name for security
        validated_name = validate_game_name(name)
        
        filepath = self._get_filepath(validated_name)
        
        if not filepath.exists():
            raise FileNotFoundError(f"No saved game found: {name}")
        
        content = filepath.read_text()
        return pgn_to_game(content)
    
    def delete_game(self, name: str) -> None:
        """Delete a saved game.
        
        Args:
            name: Name of the game to delete
            
        Raises:
            InvalidGameNameError: If name contains dangerous characters
            FileNotFoundError: If the game doesn't exist
        """
        # Validate name for security
        validated_name = validate_game_name(name)
        
        filepath = self._get_filepath(validated_name)
        
        if not filepath.exists():
            raise FileNotFoundError(f"No saved game found: {name}")
        
        filepath.unlink()
    
    def game_exists(self, name: str) -> bool:
        """Check if a saved game exists.
        
        Args:
            name: Name of the game
            
        Returns:
            True if the game exists, False otherwise
        """
        try:
            validated_name = validate_game_name(name)
            filepath = self._get_filepath(validated_name)
            return filepath.exists()
        except InvalidGameNameError:
            return False
    
    def _enforce_save_limit(self, exclude_name: str = "") -> None:
        """Enforce the maximum save limit by evicting old games.
        
        Eviction policy:
        1. Oldest completed games are evicted first
        2. Incomplete games are preserved
        3. If all games are incomplete, oldest is evicted
        
        Args:
            exclude_name: Name to exclude from count (for overwrites)
        """
        games = self.list_games()
        
        # Filter out the game we're about to overwrite
        games = [g for g in games if g.name != exclude_name]
        
        # If under limit, nothing to do
        if len(games) < MAX_SAVED_GAMES:
            return
        
        # Need to evict games
        while len(games) >= MAX_SAVED_GAMES:
            # Find oldest completed game
            completed_games = [g for g in games if g.is_complete]
            
            if completed_games:
                # Evict oldest completed game (list is sorted by mtime)
                to_evict = completed_games[0]
            else:
                # All games incomplete - evict oldest
                to_evict = games[0]
            
            # Delete the file
            to_evict.filepath.unlink()
            games.remove(to_evict)
