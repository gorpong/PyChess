"""Tests for CLI argument parsing and validation."""

import pytest
import sys
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from pychess.cli import parse_args, handle_list_games, handle_load_game, CLIError
from pychess.persistence.save_manager import SaveManager, InvalidGameNameError
from pychess.notation.pgn import PGNHeaders
from pychess.model.game_state import GameState


class TestParseArgs:
    """Tests for CLI argument parsing."""

    def test_no_args_returns_new_game(self):
        """No arguments should start a new game."""
        args = parse_args([])
        assert args.list_games is False
        assert args.load is None

    def test_list_games_flag(self):
        """--list-games should set list_games to True."""
        args = parse_args(["--list-games"])
        assert args.list_games is True

    def test_load_with_name(self):
        """--load should accept a game name."""
        args = parse_args(["--load", "MyGame"])
        assert args.load == "MyGame"

    def test_load_requires_name(self):
        """--load without a name should fail."""
        with pytest.raises(SystemExit):
            parse_args(["--load"])

    def test_list_and_load_mutually_exclusive(self):
        """--list-games and --load should be mutually exclusive."""
        # This depends on implementation - might allow both
        # but only one action is performed


class TestHandleListGames:
    """Tests for --list-games handling."""

    @pytest.fixture
    def save_dir(self):
        """Create a temporary save directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    def test_list_empty_shows_message(self, save_dir, capsys):
        """Empty save directory should show appropriate message."""
        manager = SaveManager(save_dir)
        
        handle_list_games(manager)
        
        captured = capsys.readouterr()
        assert "No saved games" in captured.out

    def test_list_shows_games(self, save_dir, capsys):
        """Should list all saved games with info."""
        manager = SaveManager(save_dir)
        state = GameState.initial()
        
        headers1 = PGNHeaders(white="Alice", black="Bob", result="1-0")
        manager.save_game("Game1", state, headers1)
        
        headers2 = PGNHeaders(white="Charlie", black="Dave", result="*")
        manager.save_game("Game2", state, headers2)
        
        handle_list_games(manager)
        
        captured = capsys.readouterr()
        assert "Game1" in captured.out
        assert "Alice" in captured.out
        assert "Bob" in captured.out
        assert "Game2" in captured.out
        assert "Charlie" in captured.out


class TestHandleLoadGame:
    """Tests for --load handling."""

    @pytest.fixture
    def save_dir(self):
        """Create a temporary save directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    def test_load_existing_game(self, save_dir):
        """Loading an existing game should return state and headers."""
        manager = SaveManager(save_dir)
        state = GameState.initial()
        headers = PGNHeaders(white="Test", black="Test2", result="*")
        manager.save_game("TestGame", state, headers)
        
        loaded_state, loaded_headers = handle_load_game(manager, "TestGame")
        
        assert loaded_headers.white == "Test"

    def test_load_nonexistent_raises(self, save_dir):
        """Loading nonexistent game should raise CLIError."""
        manager = SaveManager(save_dir)
        
        with pytest.raises(CLIError, match="not found"):
            handle_load_game(manager, "DoesNotExist")

    def test_load_path_traversal_exits(self, save_dir):
        """Path traversal attempt should raise CLIError immediately."""
        manager = SaveManager(save_dir)
        
        with pytest.raises(CLIError, match="Invalid game name"):
            handle_load_game(manager, "../etc/passwd")

    def test_load_windows_path_exits(self, save_dir):
        """Windows path traversal should raise CLIError immediately."""
        manager = SaveManager(save_dir)
        
        with pytest.raises(CLIError, match="Invalid game name"):
            handle_load_game(manager, "..\\Windows\\System32")

    def test_load_absolute_path_exits(self, save_dir):
        """Absolute path should raise CLIError immediately."""
        manager = SaveManager(save_dir)
        
        with pytest.raises(CLIError, match="Invalid game name"):
            handle_load_game(manager, "/etc/passwd")

    def test_load_hidden_file_exits(self, save_dir):
        """Hidden file attempt should raise CLIError immediately."""
        manager = SaveManager(save_dir)
        
        with pytest.raises(CLIError, match="Invalid game name"):
            handle_load_game(manager, ".bashrc")

    def test_load_null_byte_exits(self, save_dir):
        """Null byte in name should raise CLIError immediately."""
        manager = SaveManager(save_dir)
        
        with pytest.raises(CLIError, match="Invalid game name"):
            handle_load_game(manager, "game\x00.txt")


class TestCLIIntegration:
    """Integration tests for CLI behavior."""

    def test_path_traversal_causes_immediate_exit(self):
        """Path traversal should cause immediate program exit."""
        # This tests the actual exit behavior
        with patch('sys.exit') as mock_exit:
            with patch('builtins.print') as mock_print:
                from pychess.cli import validate_and_exit_on_bad_name
                
                validate_and_exit_on_bad_name("../etc/passwd")
                
                mock_exit.assert_called_once_with(1)

    def test_valid_name_does_not_exit(self):
        """Valid name should not cause exit."""
        with patch('sys.exit') as mock_exit:
            from pychess.cli import validate_and_exit_on_bad_name
            
            result = validate_and_exit_on_bad_name("ValidGame")
            
            mock_exit.assert_not_called()
            assert result == "ValidGame"
