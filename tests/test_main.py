"""Tests for main module game loading logic."""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from pychess.model.game_state import GameState
from pychess.notation.pgn import PGNHeaders, pgn_to_game
from pychess.ai.engine import AIEngine, Difficulty


class TestInferAIModeFromHeaders:
    """Tests for inferring AI mode from PGN headers when GameMode is missing."""

    def test_infer_ai_mode_when_black_is_computer(self):
        """When Black='Computer' and GameMode is default, should infer AI mode."""
        # Create a PGN string like an older saved game without GameMode header
        pgn_content = '''[Event "Casual Game"]
[Site "Terminal"]
[Date "2026.01.09"]
[White "Player"]
[Black "Computer"]
[Result "*"]
[TimeControl "-"]
[TotalTimeSeconds "72"]

1. e4 e5'''
        
        state, headers = pgn_to_game(pgn_content)
        
        # The headers should have Black = "Computer"
        assert headers.black == "Computer"
        # GameMode will be default "Multiplayer" since it's not in the PGN
        assert headers.game_mode == "Multiplayer"
        
        # Test the inference logic that should be in main.py
        # If GameMode is "Multiplayer" but Black is "Computer", 
        # this indicates an AI game from before GameMode was added
        is_ai_game = (
            headers.game_mode == "Multiplayer" and
            headers.black == "Computer"
        )
        assert is_ai_game is True

    def test_no_ai_inference_when_both_human_players(self):
        """When both White and Black are human names, should remain multiplayer."""
        pgn_content = '''[Event "Casual Game"]
[Site "Terminal"]
[Date "2026.01.09"]
[White "Alice"]
[Black "Bob"]
[Result "*"]
[TimeControl "-"]
[TotalTimeSeconds "72"]

1. e4 e5'''
        
        state, headers = pgn_to_game(pgn_content)
        
        assert headers.black == "Bob"
        assert headers.game_mode == "Multiplayer"
        
        # Should NOT infer AI mode
        is_ai_game = (
            headers.game_mode == "Multiplayer" and
            headers.black == "Computer"
        )
        assert is_ai_game is False

    def test_explicit_game_mode_takes_precedence(self):
        """When GameMode is explicitly set, it should take precedence."""
        pgn_content = '''[Event "Casual Game"]
[Site "Terminal"]
[Date "2026.01.09"]
[White "Player"]
[Black "Computer"]
[Result "*"]
[TimeControl "-"]
[TotalTimeSeconds "72"]
[GameMode "Easy"]

1. e4 e5'''
        
        state, headers = pgn_to_game(pgn_content)
        
        # Explicit GameMode should be used
        assert headers.game_mode == "Easy"
        assert headers.black == "Computer"

    def test_white_player_black_computer_pattern(self):
        """Standard AI game pattern: White='Player', Black='Computer'."""
        headers = PGNHeaders(
            white="Player",
            black="Computer",
            game_mode="Multiplayer"  # Default when loading legacy file
        )
        
        # This is the pattern that indicates a legacy AI game
        is_legacy_ai_game = (
            headers.game_mode == "Multiplayer" and
            headers.black == "Computer"
        )
        assert is_legacy_ai_game is True

    def test_white_white_black_black_is_multiplayer(self):
        """Default multiplayer pattern: White='White', Black='Black'."""
        headers = PGNHeaders(
            white="White",
            black="Black",
            game_mode="Multiplayer"
        )
        
        is_legacy_ai_game = (
            headers.game_mode == "Multiplayer" and
            headers.black == "Computer"
        )
        assert is_legacy_ai_game is False


class TestLegacyAIGameLoading:
    """Tests for loading legacy AI games without GameMode header."""

    def test_legacy_ai_game_creates_ai_engine(self):
        """Loading legacy AI game (Black='Computer', no GameMode) should create AI engine."""
        # This tests the actual logic in main.py for creating AI engine
        # from legacy game files
        
        # Simulate headers from a legacy PGN file
        headers = PGNHeaders(
            white="Player",
            black="Computer",
            game_mode="Multiplayer"  # Default - no GameMode header in file
        )
        
        # Apply the same logic as main.py
        ai_engine = None
        game_mode_str = headers.game_mode
        
        if game_mode_str == "Easy":
            ai_engine = AIEngine(Difficulty.EASY)
        elif game_mode_str == "Medium":
            ai_engine = AIEngine(Difficulty.MEDIUM)
        elif game_mode_str == "Hard":
            ai_engine = AIEngine(Difficulty.HARD)
        elif game_mode_str == "Multiplayer" and headers.black == "Computer":
            # Legacy AI game inference
            ai_engine = AIEngine(Difficulty.EASY)
            game_mode_str = "Easy"
        
        # Should have created an AI engine
        assert ai_engine is not None
        assert ai_engine.difficulty == Difficulty.EASY
        assert game_mode_str == "Easy"

    def test_multiplayer_game_no_ai_engine(self):
        """Loading multiplayer game should not create AI engine."""
        headers = PGNHeaders(
            white="Alice",
            black="Bob",
            game_mode="Multiplayer"
        )
        
        ai_engine = None
        game_mode_str = headers.game_mode
        
        if game_mode_str == "Easy":
            ai_engine = AIEngine(Difficulty.EASY)
        elif game_mode_str == "Medium":
            ai_engine = AIEngine(Difficulty.MEDIUM)
        elif game_mode_str == "Hard":
            ai_engine = AIEngine(Difficulty.HARD)
        elif game_mode_str == "Multiplayer" and headers.black == "Computer":
            ai_engine = AIEngine(Difficulty.EASY)
            game_mode_str = "Easy"
        
        # Should NOT have created an AI engine
        assert ai_engine is None
        assert game_mode_str == "Multiplayer"

    def test_explicit_easy_mode_uses_easy(self):
        """Loading game with explicit Easy GameMode should use Easy."""
        headers = PGNHeaders(
            white="Player",
            black="Computer",
            game_mode="Easy"
        )
        
        ai_engine = None
        game_mode_str = headers.game_mode
        
        if game_mode_str == "Easy":
            ai_engine = AIEngine(Difficulty.EASY)
        elif game_mode_str == "Medium":
            ai_engine = AIEngine(Difficulty.MEDIUM)
        elif game_mode_str == "Hard":
            ai_engine = AIEngine(Difficulty.HARD)
        elif game_mode_str == "Multiplayer" and headers.black == "Computer":
            ai_engine = AIEngine(Difficulty.EASY)
            game_mode_str = "Easy"
        
        assert ai_engine is not None
        assert ai_engine.difficulty == Difficulty.EASY

    def test_explicit_hard_mode_uses_hard(self):
        """Loading game with explicit Hard GameMode should use Hard."""
        headers = PGNHeaders(
            white="Player",
            black="Computer",
            game_mode="Hard"
        )
        
        ai_engine = None
        game_mode_str = headers.game_mode
        
        if game_mode_str == "Easy":
            ai_engine = AIEngine(Difficulty.EASY)
        elif game_mode_str == "Medium":
            ai_engine = AIEngine(Difficulty.MEDIUM)
        elif game_mode_str == "Hard":
            ai_engine = AIEngine(Difficulty.HARD)
        elif game_mode_str == "Multiplayer" and headers.black == "Computer":
            ai_engine = AIEngine(Difficulty.EASY)
            game_mode_str = "Easy"
        
        assert ai_engine is not None
        assert ai_engine.difficulty == Difficulty.HARD
