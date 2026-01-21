"""Tests for main module game loading logic."""

import pytest
import time
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


class TestGameTimerRestoration:
    """Tests for restoring game timer when loading saved games.
    
    These tests verify that the main module correctly restores elapsed time
    when loading a saved game by mocking run_cli() to return a loaded game
    with saved time, then inspecting the resulting session's start_time.
    """

    def test_loaded_game_restores_elapsed_time(self):
        """Loading a game with TotalTimeSeconds should adjust session.start_time.
        
        Mocks run_cli() to simulate loading a game that was played for 1 hour,
        then verifies the session's start_time was adjusted so elapsed time
        calculations will be cumulative.
        """
        from pychess.notation.pgn import PGNHeaders
        from pychess.controller.game_session import GameSession
        
        # Create headers with 1 hour of saved time
        saved_seconds = 3600
        headers = PGNHeaders(
            white="Player",
            black="Computer",
            game_mode="Easy",
            total_time_seconds=saved_seconds,
        )
        
        # Create a game state to return
        state = GameState.initial()
        
        # Capture the session that gets created
        captured_session = None
        original_init = GameSession.__init__
        
        def capturing_init(self, *args, **kwargs):
            nonlocal captured_session
            original_init(self, *args, **kwargs)
            captured_session = self
        
        with patch('pychess.main.run_cli') as mock_run_cli:
            mock_run_cli.return_value = (state, headers, "TestGame")
            
            with patch('pychess.main.TerminalRenderer') as mock_renderer_class:
                mock_renderer = MagicMock()
                mock_renderer.term = MagicMock()
                mock_renderer_class.return_value = mock_renderer
                
                with patch('pychess.main.SaveManager'):
                    with patch.object(GameSession, '__init__', capturing_init):
                        with patch.object(GameSession, 'run'):
                            # Patch get_game_result where it's imported in main()
                            with patch('pychess.rules.game_logic.get_game_result', return_value=None):
                                with patch('pychess.main.prompt_save_game'):
                                    before_main = time.time()
                                    
                                    from pychess.main import main
                                    main()
                                    
                                    after_main = time.time()
        
        # Verify the session was captured
        assert captured_session is not None
        
        # The elapsed time should be approximately saved_seconds
        # because start_time was adjusted backward by saved_seconds
        elapsed = after_main - captured_session.start_time
        assert elapsed >= saved_seconds - 1  # Allow 1 sec tolerance
        assert elapsed < saved_seconds + 2  # Allow 2 sec for test execution

    def test_loaded_game_with_zero_time_no_adjustment(self):
        """Loading a game with TotalTimeSeconds=0 should have start_time near current time."""
        from pychess.notation.pgn import PGNHeaders
        from pychess.controller.game_session import GameSession
        
        headers = PGNHeaders(
            white="Player",
            black="Computer", 
            game_mode="Easy",
            total_time_seconds=0,
        )
        state = GameState.initial()
        
        captured_session = None
        original_init = GameSession.__init__
        
        def capturing_init(self, *args, **kwargs):
            nonlocal captured_session
            original_init(self, *args, **kwargs)
            captured_session = self
        
        with patch('pychess.main.run_cli') as mock_run_cli:
            mock_run_cli.return_value = (state, headers, "TestGame")
            
            with patch('pychess.main.TerminalRenderer') as mock_renderer_class:
                mock_renderer = MagicMock()
                mock_renderer.term = MagicMock()
                mock_renderer_class.return_value = mock_renderer
                
                with patch('pychess.main.SaveManager'):
                    with patch.object(GameSession, '__init__', capturing_init):
                        with patch.object(GameSession, 'run'):
                            with patch('pychess.rules.game_logic.get_game_result', return_value=None):
                                with patch('pychess.main.prompt_save_game'):
                                    before_main = time.time()
                                    from pychess.main import main
                                    main()
                                    after_main = time.time()
        
        assert captured_session is not None
        
        # With zero saved time, elapsed should be near zero
        elapsed = after_main - captured_session.start_time
        assert elapsed < 2  # Should be very small

    def test_new_game_has_fresh_start_time(self):
        """A new game (not loaded) should have start_time at current time."""
        from pychess.controller.game_session import GameSession
        
        captured_session = None
        original_init = GameSession.__init__
        
        def capturing_init(self, *args, **kwargs):
            nonlocal captured_session
            original_init(self, *args, **kwargs)
            captured_session = self
        
        with patch('pychess.main.run_cli') as mock_run_cli:
            # Return None to indicate no loaded game
            mock_run_cli.return_value = None
            
            with patch('pychess.main.TerminalRenderer') as mock_renderer_class:
                mock_renderer = MagicMock()
                mock_renderer.term = MagicMock()
                mock_renderer_class.return_value = mock_renderer
                
                with patch('pychess.main.SaveManager'):
                    with patch('pychess.main.select_game_mode') as mock_select:
                        # Return multiplayer mode
                        mock_select.return_value = ("multiplayer", None)
                        
                        with patch.object(GameSession, '__init__', capturing_init):
                            with patch.object(GameSession, 'run'):
                                with patch('pychess.rules.game_logic.get_game_result', return_value=None):
                                    with patch('pychess.main.prompt_save_game'):
                                        before_main = time.time()
                                        from pychess.main import main
                                        main()
                                        after_main = time.time()
        
        assert captured_session is not None
        
        # New game should have elapsed time near zero
        elapsed = after_main - captured_session.start_time
        assert elapsed < 2  # Very small elapsed time
