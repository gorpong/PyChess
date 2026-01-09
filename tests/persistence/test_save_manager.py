"""Tests for save manager functionality."""

import os
import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch

from pychess.persistence.save_manager import (
    SaveManager,
    SavedGameInfo,
    sanitize_game_name,
    validate_game_name,
    InvalidGameNameError,
)
from pychess.model.game_state import GameState
from pychess.notation.pgn import PGNHeaders


class TestSanitizeGameName:
    """Tests for game name sanitization."""

    def test_simple_name_unchanged(self):
        """Simple alphanumeric names should be unchanged."""
        assert sanitize_game_name("MyGame") == "MyGame"
        assert sanitize_game_name("Game1") == "Game1"
        assert sanitize_game_name("test") == "test"

    def test_spaces_converted_to_underscores(self):
        """Spaces should be converted to underscores."""
        assert sanitize_game_name("My Game") == "My_Game"
        assert sanitize_game_name("Game 1 Test") == "Game_1_Test"

    def test_special_chars_removed(self):
        """Special characters should be removed."""
        assert sanitize_game_name("Game!@#$%") == "Game"
        assert sanitize_game_name("Test&Name") == "TestName"

    def test_multiple_underscores_collapsed(self):
        """Multiple consecutive underscores should be collapsed."""
        assert sanitize_game_name("My   Game") == "My_Game"
        assert sanitize_game_name("Test___Name") == "Test_Name"

    def test_leading_trailing_underscores_stripped(self):
        """Leading and trailing underscores should be stripped."""
        assert sanitize_game_name("  Game  ") == "Game"
        assert sanitize_game_name("___Test___") == "Test"

    def test_empty_after_sanitize_raises(self):
        """Names that become empty after sanitization should raise."""
        with pytest.raises(InvalidGameNameError):
            sanitize_game_name("!@#$%")
        with pytest.raises(InvalidGameNameError):
            sanitize_game_name("   ")

    def test_too_long_name_truncated(self):
        """Names longer than 50 chars should be truncated."""
        long_name = "A" * 100
        result = sanitize_game_name(long_name)
        assert len(result) <= 50


class TestValidateGameName:
    """Tests for game name validation - security critical."""

    def test_valid_names_pass(self):
        """Valid game names should pass validation."""
        validate_game_name("MyGame")
        validate_game_name("Game_1")
        validate_game_name("Test-Game")
        validate_game_name("Game.2024")

    def test_unix_path_separator_rejected(self):
        """Forward slash (Unix path separator) must be rejected."""
        with pytest.raises(InvalidGameNameError, match="path"):
            validate_game_name("path/to/game")
        with pytest.raises(InvalidGameNameError, match="path"):
            validate_game_name("/etc/passwd")
        with pytest.raises(InvalidGameNameError, match="path"):
            validate_game_name("../parent")

    def test_windows_path_separator_rejected(self):
        """Backslash (Windows path separator) must be rejected."""
        with pytest.raises(InvalidGameNameError, match="path"):
            validate_game_name("path\\to\\game")
        with pytest.raises(InvalidGameNameError, match="path"):
            validate_game_name("C:\\Users\\test")
        with pytest.raises(InvalidGameNameError, match="path"):
            validate_game_name("..\\parent")

    def test_dot_dot_rejected(self):
        """Parent directory reference (..) must be rejected."""
        with pytest.raises(InvalidGameNameError, match="path"):
            validate_game_name("..")
        with pytest.raises(InvalidGameNameError, match="path"):
            validate_game_name("..game")
        with pytest.raises(InvalidGameNameError, match="path"):
            validate_game_name("game..")

    def test_absolute_path_rejected(self):
        """Absolute paths must be rejected."""
        with pytest.raises(InvalidGameNameError, match="path"):
            validate_game_name("/absolute/path")
        with pytest.raises(InvalidGameNameError, match="path"):
            validate_game_name("C:/Windows/System32")

    def test_null_byte_rejected(self):
        """Null bytes must be rejected."""
        with pytest.raises(InvalidGameNameError, match="path"):
            validate_game_name("game\x00name")

    def test_empty_name_rejected(self):
        """Empty names must be rejected."""
        with pytest.raises(InvalidGameNameError):
            validate_game_name("")
        with pytest.raises(InvalidGameNameError):
            validate_game_name("   ")

    def test_pgn_extension_stripped_before_validation(self):
        """Names ending in .pgn should have it stripped."""
        # This should not raise - .pgn is stripped
        validate_game_name("MyGame.pgn")

    def test_hidden_file_rejected(self):
        """Hidden files (starting with dot) must be rejected."""
        with pytest.raises(InvalidGameNameError, match="path"):
            validate_game_name(".hidden")
        with pytest.raises(InvalidGameNameError, match="path"):
            validate_game_name(".bashrc")

    def test_colon_rejected(self):
        """Colons (Windows drive letters) must be rejected."""
        with pytest.raises(InvalidGameNameError, match="path"):
            validate_game_name("C:")
        with pytest.raises(InvalidGameNameError, match="path"):
            validate_game_name("D:game")


class TestSaveManager:
    """Tests for SaveManager class."""

    @pytest.fixture
    def save_dir(self):
        """Create a temporary save directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def manager(self, save_dir):
        """Create a SaveManager with temp directory."""
        return SaveManager(save_dir)

    def test_creates_save_directory(self, save_dir):
        """SaveManager should create save directory if it doesn't exist."""
        new_dir = save_dir / "new_subdir"
        assert not new_dir.exists()
        
        manager = SaveManager(new_dir)
        
        assert new_dir.exists()

    def test_list_games_empty(self, manager):
        """list_games should return empty list when no saves exist."""
        games = manager.list_games()
        assert games == []

    def test_save_game(self, manager):
        """save_game should create a PGN file."""
        state = GameState.initial()
        headers = PGNHeaders(
            event="Test Game",
            white="Player1",
            black="Player2",
            result="*"
        )
        
        manager.save_game("TestGame", state, headers)
        
        games = manager.list_games()
        assert len(games) == 1
        assert games[0].name == "TestGame"

    def test_save_game_with_moves(self, manager):
        """save_game should preserve move history."""
        # Create a state with some moves
        state = GameState.initial()
        # Manually add moves to history for testing
        state = state.with_move_added("e4").with_move_added("e5")
        
        headers = PGNHeaders(result="*")
        manager.save_game("WithMoves", state, headers)
        
        # Load it back
        loaded_state, loaded_headers = manager.load_game("WithMoves")
        assert loaded_state.move_history == ["e4", "e5"]

    def test_list_games_returns_info(self, manager):
        """list_games should return SavedGameInfo with metadata."""
        state = GameState.initial()
        headers = PGNHeaders(
            white="Alice",
            black="Bob",
            result="1-0",
            date="2024.01.15"
        )
        manager.save_game("InfoTest", state, headers)
        
        games = manager.list_games()
        assert len(games) == 1
        info = games[0]
        assert info.name == "InfoTest"
        assert info.white == "Alice"
        assert info.black == "Bob"
        assert info.result == "1-0"
        assert info.date == "2024.01.15"

    def test_load_game(self, manager):
        """load_game should restore game state."""
        state = GameState.initial()
        headers = PGNHeaders(white="Test", black="Test2", result="*")
        manager.save_game("LoadTest", state, headers)
        
        loaded_state, loaded_headers = manager.load_game("LoadTest")
        
        assert loaded_state.fullmove_number == 1
        assert loaded_headers.white == "Test"
        assert loaded_headers.black == "Test2"

    def test_load_nonexistent_game_raises(self, manager):
        """load_game should raise for nonexistent game."""
        with pytest.raises(FileNotFoundError):
            manager.load_game("DoesNotExist")

    def test_load_game_validates_name(self, manager):
        """load_game should validate game name for path traversal."""
        with pytest.raises(InvalidGameNameError):
            manager.load_game("../etc/passwd")
        with pytest.raises(InvalidGameNameError):
            manager.load_game("..\\Windows\\System32")

    def test_save_game_validates_name(self, manager):
        """save_game should validate game name for path traversal."""
        state = GameState.initial()
        headers = PGNHeaders()
        
        with pytest.raises(InvalidGameNameError):
            manager.save_game("/etc/passwd", state, headers)
        with pytest.raises(InvalidGameNameError):
            manager.save_game("..\\test", state, headers)

    def test_delete_game(self, manager):
        """delete_game should remove the save file."""
        state = GameState.initial()
        headers = PGNHeaders()
        manager.save_game("ToDelete", state, headers)
        
        assert len(manager.list_games()) == 1
        
        manager.delete_game("ToDelete")
        
        assert len(manager.list_games()) == 0

    def test_delete_nonexistent_game_raises(self, manager):
        """delete_game should raise for nonexistent game."""
        with pytest.raises(FileNotFoundError):
            manager.delete_game("DoesNotExist")

    def test_game_exists(self, manager):
        """game_exists should return True for existing games."""
        state = GameState.initial()
        headers = PGNHeaders()
        
        assert manager.game_exists("MyGame") is False
        
        manager.save_game("MyGame", state, headers)
        
        assert manager.game_exists("MyGame") is True

    def test_overwrite_existing_game(self, manager):
        """Saving with same name should overwrite."""
        state = GameState.initial()
        headers1 = PGNHeaders(white="First")
        headers2 = PGNHeaders(white="Second")
        
        manager.save_game("Overwrite", state, headers1)
        manager.save_game("Overwrite", state, headers2)
        
        _, loaded_headers = manager.load_game("Overwrite")
        assert loaded_headers.white == "Second"
        assert len(manager.list_games()) == 1


class TestSaveLimit:
    """Tests for the 10-game save limit."""

    @pytest.fixture
    def save_dir(self):
        """Create a temporary save directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def manager(self, save_dir):
        """Create a SaveManager with temp directory."""
        return SaveManager(save_dir)

    def test_max_10_games(self, manager):
        """Should enforce 10 game limit."""
        state = GameState.initial()
        
        # Save 10 completed games
        for i in range(10):
            headers = PGNHeaders(result="1-0")
            manager.save_game(f"Game{i}", state, headers)
        
        assert len(manager.list_games()) == 10
        
        # Save 11th game - should evict oldest completed
        headers = PGNHeaders(result="1-0")
        manager.save_game("Game10", state, headers)
        
        assert len(manager.list_games()) == 10
        # Game0 should be evicted (oldest completed)
        assert not manager.game_exists("Game0")
        assert manager.game_exists("Game10")

    def test_incomplete_games_preserved(self, manager):
        """Incomplete games should be preserved over complete ones."""
        state = GameState.initial()
        
        # Save 5 incomplete games
        for i in range(5):
            headers = PGNHeaders(result="*")
            manager.save_game(f"Incomplete{i}", state, headers)
        
        # Save 5 complete games
        for i in range(5):
            headers = PGNHeaders(result="1-0")
            manager.save_game(f"Complete{i}", state, headers)
        
        # Save 11th game (complete)
        headers = PGNHeaders(result="0-1")
        manager.save_game("NewComplete", state, headers)
        
        # Should have 10 games, oldest complete game evicted
        assert len(manager.list_games()) == 10
        assert not manager.game_exists("Complete0")
        
        # All incomplete games should still exist
        for i in range(5):
            assert manager.game_exists(f"Incomplete{i}")

    def test_evict_oldest_complete_first(self, manager):
        """Should evict oldest completed game first."""
        state = GameState.initial()
        
        # Save games in order with different results
        headers = PGNHeaders(result="1-0")  # Complete
        manager.save_game("OldComplete", state, headers)
        
        headers = PGNHeaders(result="*")  # Incomplete
        manager.save_game("OldIncomplete", state, headers)
        
        # Fill up to 10
        for i in range(8):
            headers = PGNHeaders(result="1-0")
            manager.save_game(f"Game{i}", state, headers)
        
        # Add 11th
        headers = PGNHeaders(result="1-0")
        manager.save_game("NewGame", state, headers)
        
        # OldComplete should be gone, OldIncomplete should remain
        assert not manager.game_exists("OldComplete")
        assert manager.game_exists("OldIncomplete")


class TestSavedGameInfo:
    """Tests for SavedGameInfo dataclass."""

    def test_is_complete_true_for_white_win(self):
        """is_complete should be True for 1-0."""
        info = SavedGameInfo(
            name="test",
            white="W",
            black="B",
            result="1-0",
            date="2024.01.01",
            move_count=10,
            filepath=Path("test.pgn")
        )
        assert info.is_complete is True

    def test_is_complete_true_for_black_win(self):
        """is_complete should be True for 0-1."""
        info = SavedGameInfo(
            name="test",
            white="W",
            black="B",
            result="0-1",
            date="2024.01.01",
            move_count=10,
            filepath=Path("test.pgn")
        )
        assert info.is_complete is True

    def test_is_complete_true_for_draw(self):
        """is_complete should be True for 1/2-1/2."""
        info = SavedGameInfo(
            name="test",
            white="W",
            black="B",
            result="1/2-1/2",
            date="2024.01.01",
            move_count=10,
            filepath=Path("test.pgn")
        )
        assert info.is_complete is True

    def test_is_complete_false_for_ongoing(self):
        """is_complete should be False for *."""
        info = SavedGameInfo(
            name="test",
            white="W",
            black="B",
            result="*",
            date="2024.01.01",
            move_count=10,
            filepath=Path("test.pgn")
        )
        assert info.is_complete is False
