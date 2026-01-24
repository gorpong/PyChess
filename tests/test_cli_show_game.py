"""Tests for --show-game CLI option."""

import pytest
import tempfile
from pathlib import Path

from pychess.cli import parse_args, handle_show_game, CLIError
from pychess.persistence.save_manager import SaveManager
from pychess.notation.pgn import PGNHeaders
from pychess.model.game_state import GameState


class TestShowGameArgs:
    """Tests for --show-game argument parsing."""

    def test_show_game_accepts_name(self):
        """--show-game should accept a game name."""
        args = parse_args(["--show-game", "MyGame"])
        assert args.show_game == "MyGame"

    def test_show_game_requires_name(self):
        """--show-game without a name should fail."""
        with pytest.raises(SystemExit):
            parse_args(["--show-game"])


class TestHandleShowGame:
    """Tests for handle_show_game function."""

    @pytest.fixture
    def save_dir(self):
        """Create a temporary save directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    def test_show_nonexistent_game_raises(self, save_dir):
        """Showing a nonexistent game should raise CLIError."""
        manager = SaveManager(save_dir)
        
        with pytest.raises(CLIError, match="not found"):
            handle_show_game(manager, "DoesNotExist")

    def test_show_game_displays_headers(self, save_dir, capsys):
        """Should display game headers."""
        manager = SaveManager(save_dir)
        state = GameState.initial()
        headers = PGNHeaders(
            white="Alice",
            black="Bob",
            result="1-0",
            date="2024.01.15",
            total_time_seconds=330,
        )
        manager.save_game("TestGame", state, headers)
        
        handle_show_game(manager, "TestGame")
        
        captured = capsys.readouterr()
        assert "TestGame" in captured.out
        assert "Alice" in captured.out
        assert "Bob" in captured.out
        assert "1-0" in captured.out
        assert "2024.01.15" in captured.out

    def test_show_game_displays_time(self, save_dir, capsys):
        """Should display formatted game time."""
        manager = SaveManager(save_dir)
        state = GameState.initial()
        headers = PGNHeaders(
            white="Alice",
            black="Bob",
            result="*",
            total_time_seconds=330,  # 5m 30s
        )
        manager.save_game("TestGame", state, headers)
        
        handle_show_game(manager, "TestGame")
        
        captured = capsys.readouterr()
        assert "5m 30s" in captured.out

    def test_show_game_displays_moves_magazine_style(self, save_dir, capsys):
        """Should display moves in magazine style (one pair per line)."""
        manager = SaveManager(save_dir)
        
        # Create a game with some moves
        state = GameState.initial()
        state = state.with_move_added("e4")
        state = state.with_move_added("e5")
        state = state.with_move_added("Nf3")
        state = state.with_move_added("Nc6")
        
        headers = PGNHeaders(white="Alice", black="Bob", result="*")
        manager.save_game("TestGame", state, headers)
        
        handle_show_game(manager, "TestGame")
        
        captured = capsys.readouterr()
        # Each move pair should be on its own line
        # Look for the pattern: move number, white move, black move
        assert "1." in captured.out
        assert "e4" in captured.out
        assert "e5" in captured.out
        assert "2." in captured.out
        assert "Nf3" in captured.out
        assert "Nc6" in captured.out

    def test_show_game_handles_odd_number_of_moves(self, save_dir, capsys):
        """Should handle games with odd number of moves (white's last move)."""
        manager = SaveManager(save_dir)
        
        state = GameState.initial()
        state = state.with_move_added("e4")
        state = state.with_move_added("e5")
        state = state.with_move_added("Nf3")  # White's move, no black response yet
        
        headers = PGNHeaders(white="Alice", black="Bob", result="*")
        manager.save_game("TestGame", state, headers)
        
        handle_show_game(manager, "TestGame")
        
        captured = capsys.readouterr()
        assert "Nf3" in captured.out

    def test_show_game_handles_empty_game(self, save_dir, capsys):
        """Should handle games with no moves."""
        manager = SaveManager(save_dir)
        state = GameState.initial()
        headers = PGNHeaders(white="Alice", black="Bob", result="*")
        manager.save_game("TestGame", state, headers)
        
        handle_show_game(manager, "TestGame")
        
        captured = capsys.readouterr()
        # Should still show headers without crashing
        assert "Alice" in captured.out
        assert "Bob" in captured.out

    def test_show_game_path_traversal_raises(self, save_dir):
        """Path traversal attempt should raise CLIError."""
        manager = SaveManager(save_dir)
        
        with pytest.raises(CLIError, match="Invalid game name"):
            handle_show_game(manager, "../etc/passwd")

    def test_show_game_displays_result_at_end(self, save_dir, capsys):
        """Completed games should show result after moves."""
        manager = SaveManager(save_dir)
        
        state = GameState.initial()
        state = state.with_move_added("e4")
        state = state.with_move_added("e5")
        
        headers = PGNHeaders(white="Alice", black="Bob", result="1-0")
        manager.save_game("TestGame", state, headers)
        
        handle_show_game(manager, "TestGame")
        
        captured = capsys.readouterr()
        # Result should appear in the output
        assert "1-0" in captured.out
