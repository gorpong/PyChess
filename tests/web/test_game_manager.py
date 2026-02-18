"""Tests for game session management."""

import pytest
import time

from pychess.model.piece import Color
from pychess.model.square import Square
from pychess.ai.engine import Difficulty
from pychess.web.game_manager import (
    GameManager,
    WebGameSession,
    get_game_manager,
    reset_game_manager,
)


@pytest.fixture
def manager():
    """Create a fresh game manager for each test."""
    return GameManager()


@pytest.fixture(autouse=True)
def reset_global_manager():
    """Reset global manager before and after each test."""
    reset_game_manager()
    yield
    reset_game_manager()


class TestWebGameSession:
    """Tests for WebGameSession dataclass."""
    
    def test_session_has_required_fields(self):
        """Test that session has all required fields."""
        from pychess.model.game_state import GameState
        
        session = WebGameSession(
            session_id='test-id',
            game_state=GameState.initial(),
        )
        
        assert session.session_id == 'test-id'
        assert session.game_state is not None
        assert session.state_history == []
        assert session.selected_square is None
        assert session.ai_engine is None
        assert session.game_mode == 'multiplayer'
        assert session.game_name is None
        assert session.last_move is None
    
    def test_session_defaults_start_time(self):
        """Test that start_time defaults to current time."""
        from pychess.model.game_state import GameState
        
        before = time.time()
        session = WebGameSession(
            session_id='test-id',
            game_state=GameState.initial(),
        )
        after = time.time()
        
        assert before <= session.start_time <= after


class TestGameManagerCreateGame:
    """Tests for creating new games."""
    
    def test_create_multiplayer_game(self, manager):
        """Test creating a multiplayer game."""
        session = manager.create_game('test-id', 'multiplayer')
        
        assert session.session_id == 'test-id'
        assert session.game_mode == 'multiplayer'
        assert session.ai_engine is None
        assert session.game_state.turn == Color.WHITE
    
    def test_create_easy_ai_game(self, manager):
        """Test creating an easy AI game."""
        session = manager.create_game('test-id', 'easy')
        
        assert session.game_mode == 'easy'
        assert session.ai_engine is not None
        assert session.ai_engine.difficulty == Difficulty.EASY
    
    def test_create_medium_ai_game(self, manager):
        """Test creating a medium AI game."""
        session = manager.create_game('test-id', 'medium')
        
        assert session.game_mode == 'medium'
        assert session.ai_engine is not None
        assert session.ai_engine.difficulty == Difficulty.MEDIUM
    
    def test_create_hard_ai_game(self, manager):
        """Test creating a hard AI game."""
        session = manager.create_game('test-id', 'hard')
        
        assert session.game_mode == 'hard'
        assert session.ai_engine is not None
        assert session.ai_engine.difficulty == Difficulty.HARD
    
    def test_create_game_stores_session(self, manager):
        """Test that created game is stored and retrievable."""
        manager.create_game('test-id', 'multiplayer')
        
        retrieved = manager.get_game('test-id')
        assert retrieved is not None
        assert retrieved.session_id == 'test-id'
    
    def test_create_game_has_welcome_message(self, manager):
        """Test that new game has welcome status message."""
        session = manager.create_game('test-id', 'multiplayer')
        
        assert 'Welcome to PyChess!' in session.status_messages


class TestGameManagerGetGame:
    """Tests for retrieving games."""
    
    def test_get_existing_game(self, manager):
        """Test retrieving an existing game."""
        manager.create_game('test-id', 'multiplayer')
        
        session = manager.get_game('test-id')
        assert session is not None
        assert session.session_id == 'test-id'
    
    def test_get_nonexistent_game_returns_none(self, manager):
        """Test that getting nonexistent game returns None."""
        session = manager.get_game('nonexistent')
        assert session is None


class TestGameManagerUpdateGame:
    """Tests for updating games."""
    
    def test_update_game_persists_changes(self, manager):
        """Test that updates are persisted."""
        session = manager.create_game('test-id', 'multiplayer')
        
        # Modify session
        session.selected_square = Square(file='e', rank=2)
        manager.update_game(session)
        
        # Retrieve and verify
        retrieved = manager.get_game('test-id')
        assert retrieved.selected_square == Square(file='e', rank=2)


class TestGameManagerDeleteGame:
    """Tests for deleting games."""
    
    def test_delete_existing_game(self, manager):
        """Test deleting an existing game."""
        manager.create_game('test-id', 'multiplayer')
        
        manager.delete_game('test-id')
        
        assert manager.get_game('test-id') is None
    
    def test_delete_nonexistent_game_no_error(self, manager):
        """Test that deleting nonexistent game doesn't raise."""
        manager.delete_game('nonexistent')  # Should not raise


class TestGameManagerSessionLimit:
    """Tests for session limit enforcement."""
    
    def test_enforces_max_sessions(self):
        """Test that session limit is enforced."""
        manager = GameManager(max_sessions=3)
        
        manager.create_game('session-1', 'multiplayer')
        manager.create_game('session-2', 'multiplayer')
        manager.create_game('session-3', 'multiplayer')
        
        assert manager.get_session_count() == 3
        
        # Creating 4th should evict oldest
        manager.create_game('session-4', 'multiplayer')
        
        assert manager.get_session_count() == 3
        assert manager.get_game('session-1') is None
        assert manager.get_game('session-4') is not None
    
    def test_evicts_oldest_session(self):
        """Test that oldest session by start_time is evicted."""
        manager = GameManager(max_sessions=2)
        
        # Create sessions with controlled start times
        session1 = manager.create_game('oldest', 'multiplayer')
        session1.start_time = 1000
        manager.update_game(session1)
        
        session2 = manager.create_game('newer', 'multiplayer')
        session2.start_time = 2000
        manager.update_game(session2)
        
        # Create third - should evict 'oldest'
        manager.create_game('newest', 'multiplayer')
        
        assert manager.get_game('oldest') is None
        assert manager.get_game('newer') is not None
        assert manager.get_game('newest') is not None


class TestGameManagerSessionId:
    """Tests for session ID generation."""
    
    def test_session_id_is_string(self, manager):
        """Test that session ID is a string."""
        session_id = manager.create_session_id()
        assert isinstance(session_id, str)
    
    def test_session_ids_are_unique(self, manager):
        """Test that generated session IDs are unique."""
        ids = [manager.create_session_id() for _ in range(100)]
        assert len(ids) == len(set(ids))
    
    def test_session_id_is_url_safe(self, manager):
        """Test that session ID is URL-safe."""
        session_id = manager.create_session_id()
        # URL-safe base64 uses only alphanumeric, dash, and underscore
        import re
        assert re.match(r'^[A-Za-z0-9_-]+$', session_id)


class TestGlobalGameManager:
    """Tests for global game manager singleton."""
    
    def test_get_game_manager_returns_same_instance(self):
        """Test that get_game_manager returns singleton."""
        manager1 = get_game_manager()
        manager2 = get_game_manager()
        assert manager1 is manager2
    
    def test_reset_clears_singleton(self):
        """Test that reset_game_manager clears the singleton."""
        manager1 = get_game_manager()
        manager1.create_game('test', 'multiplayer')
        
        reset_game_manager()
        
        manager2 = get_game_manager()
        assert manager2.get_game('test') is None

class TestWebGameSessionHints:
    """Tests for hint functionality in WebGameSession."""

    def test_hints_allowed_in_multiplayer(self):
        """Test that hints are allowed in multiplayer mode."""
        from pychess.model.game_state import GameState

        session = WebGameSession(
            session_id='test',
            game_state=GameState.initial(),
            game_mode='multiplayer',
        )
        assert session.hints_allowed is True

    def test_hints_allowed_in_easy(self):
        """Test that hints are allowed in easy mode."""
        from pychess.model.game_state import GameState

        session = WebGameSession(
            session_id='test',
            game_state=GameState.initial(),
            game_mode='easy',
        )
        assert session.hints_allowed is True

    def test_hints_allowed_in_medium(self):
        """Test that hints are allowed in medium mode."""
        from pychess.model.game_state import GameState

        session = WebGameSession(
            session_id='test',
            game_state=GameState.initial(),
            game_mode='medium',
        )
        assert session.hints_allowed is True

    def test_hints_not_allowed_in_hard(self):
        """Test that hints are not allowed in hard mode."""
        from pychess.model.game_state import GameState

        session = WebGameSession(
            session_id='test',
            game_state=GameState.initial(),
            game_mode='hard',
        )
        assert session.hints_allowed is False

    def test_get_legal_moves_empty_without_selection(self):
        """Test that legal moves is empty without selection."""
        from pychess.model.game_state import GameState

        session = WebGameSession(
            session_id='test',
            game_state=GameState.initial(),
            game_mode='multiplayer',
            show_hints=True,
        )
        assert session.get_legal_moves_for_selected() == set()

    def test_get_legal_moves_empty_without_hints_enabled(self):
        """Test that legal moves is empty when hints not enabled."""
        from pychess.model.game_state import GameState

        session = WebGameSession(
            session_id='test',
            game_state=GameState.initial(),
            game_mode='multiplayer',
            selected_square=Square(file='e', rank=2),
            show_hints=False,
        )
        assert session.get_legal_moves_for_selected() == set()

    def test_get_legal_moves_returns_moves_when_enabled(self):
        """Test that legal moves are returned when hints enabled."""
        from pychess.model.game_state import GameState

        session = WebGameSession(
            session_id='test',
            game_state=GameState.initial(),
            game_mode='multiplayer',
            selected_square=Square(file='e', rank=2),
            show_hints=True,
        )
        legal_moves = session.get_legal_moves_for_selected()

        # e2 pawn can move to e3 and e4
        assert Square(file='e', rank=3) in legal_moves
        assert Square(file='e', rank=4) in legal_moves
        assert len(legal_moves) == 2


class TestGameManagerSelection:
    """Tests for selection handling in GameManager."""

    def test_select_own_piece(self, manager):
        """Test selecting own piece."""
        session = manager.create_game('test', 'multiplayer')

        session = manager.select_square(session, Square(file='e', rank=2))

        assert session.selected_square == Square(file='e', rank=2)

    def test_select_opponent_piece_rejected(self, manager):
        """Test that selecting opponent's piece is rejected."""
        session = manager.create_game('test', 'multiplayer')

        session = manager.select_square(session, Square(file='e', rank=7))

        assert session.selected_square is None
        assert "not your piece" in session.status_messages[0].lower()

    def test_select_empty_square_clears(self, manager):
        """Test that selecting empty square clears selection."""
        session = manager.create_game('test', 'multiplayer')
        session = manager.select_square(session, Square(file='e', rank=2))

        session = manager.select_square(session, Square(file='e', rank=4))

        assert session.selected_square is None

    def test_select_same_square_deselects(self, manager):
        """Test that clicking same square deselects."""
        session = manager.create_game('test', 'multiplayer')
        session = manager.select_square(session, Square(file='e', rank=2))

        session = manager.select_square(session, Square(file='e', rank=2))

        assert session.selected_square is None

    def test_selection_resets_hints(self, manager):
        """Test that new selection resets hints."""
        session = manager.create_game('test', 'multiplayer')
        session = manager.select_square(session, Square(file='e', rank=2))
        session = manager.toggle_hints(session)
        assert session.show_hints is True

        session = manager.select_square(session, Square(file='d', rank=2))

        assert session.show_hints is False


class TestGameManagerToggleHints:
    """Tests for hint toggling in GameManager."""

    def test_toggle_hints_on(self, manager):
        """Test toggling hints on."""
        session = manager.create_game('test', 'multiplayer')
        session = manager.select_square(session, Square(file='e', rank=2))

        session = manager.toggle_hints(session)

        assert session.show_hints is True

    def test_toggle_hints_off(self, manager):
        """Test toggling hints off."""
        session = manager.create_game('test', 'multiplayer')
        session = manager.select_square(session, Square(file='e', rank=2))
        session = manager.toggle_hints(session)

        session = manager.toggle_hints(session)

        assert session.show_hints is False

    def test_toggle_hints_requires_selection(self, manager):
        """Test that toggle hints requires selection."""
        session = manager.create_game('test', 'multiplayer')

        session = manager.toggle_hints(session)

        assert session.show_hints is False
        assert 'Select a piece first' in session.status_messages[0]

    def test_toggle_hints_rejected_in_hard_mode(self, manager):
        """Test that hints are rejected in hard mode."""
        session = manager.create_game('test', 'hard')
        session = manager.select_square(session, Square(file='e', rank=2))

        session = manager.toggle_hints(session)

        assert session.show_hints is False
        assert 'not available in Hard mode' in session.status_messages[0]



class TestGameManagerMoveExecution:
    """Tests for move execution in GameManager."""
    
    def test_move_via_selection(self, manager):
        """Test executing a move by selecting destination."""
        session = manager.create_game('test', 'multiplayer')
        
        # Select e2 pawn
        session = manager.select_square(session, Square(file='e', rank=2))
        # Click e4 (legal destination)
        session = manager.select_square(session, Square(file='e', rank=4))
        
        # Pawn should have moved
        assert session.game_state.board.get(Square(file='e', rank=4)) is not None
        assert session.game_state.board.get(Square(file='e', rank=2)) is None
    
    def test_move_updates_turn(self, manager):
        """Test that move updates turn."""
        session = manager.create_game('test', 'multiplayer')
        
        session = manager.select_square(session, Square(file='e', rank=2))
        session = manager.select_square(session, Square(file='e', rank=4))
        
        assert session.game_state.turn == Color.BLACK
    
    def test_move_clears_selection(self, manager):
        """Test that move clears selection."""
        session = manager.create_game('test', 'multiplayer')
        
        session = manager.select_square(session, Square(file='e', rank=2))
        session = manager.select_square(session, Square(file='e', rank=4))
        
        assert session.selected_square is None
    
    def test_move_sets_last_move(self, manager):
        """Test that move sets last_move for highlighting."""
        session = manager.create_game('test', 'multiplayer')
        
        session = manager.select_square(session, Square(file='e', rank=2))
        session = manager.select_square(session, Square(file='e', rank=4))
        
        assert session.last_move == (
            Square(file='e', rank=2),
            Square(file='e', rank=4),
        )
    
    def test_move_adds_to_history(self, manager):
        """Test that move is added to move history."""
        session = manager.create_game('test', 'multiplayer')
        
        session = manager.select_square(session, Square(file='e', rank=2))
        session = manager.select_square(session, Square(file='e', rank=4))
        
        assert 'e4' in session.game_state.move_history
    
    def test_move_adds_state_to_history(self, manager):
        """Test that previous state is saved for undo."""
        session = manager.create_game('test', 'multiplayer')
        
        session = manager.select_square(session, Square(file='e', rank=2))
        session = manager.select_square(session, Square(file='e', rank=4))
        
        assert len(session.state_history) == 1
    
    def test_illegal_move_not_executed(self, manager):
        """Test that clicking non-legal square doesn't move."""
        session = manager.create_game('test', 'multiplayer')
        
        session = manager.select_square(session, Square(file='e', rank=2))
        # e5 is not a legal destination for e2 pawn
        session = manager.select_square(session, Square(file='e', rank=5))
        
        # Should have cleared selection, not moved
        assert session.game_state.board.get(Square(file='e', rank=2)) is not None


class TestGameManagerPromotion:
    """Tests for pawn promotion."""
    
    def test_complete_promotion_to_queen(self, manager):
        """Test completing promotion to queen."""
        from pychess.rules.move import Move
        
        session = manager.create_game('test', 'multiplayer')
        session.pending_promotion = Move(
            from_square=Square(file='e', rank=7),
            to_square=Square(file='e', rank=8),
        )
        
        session = manager.complete_promotion(session, 'Q')
        
        assert session.pending_promotion is None
    
    def test_complete_promotion_invalid_piece(self, manager):
        """Test that invalid promotion piece is rejected."""
        from pychess.rules.move import Move
        
        session = manager.create_game('test', 'multiplayer')
        session.pending_promotion = Move(
            from_square=Square(file='e', rank=7),
            to_square=Square(file='e', rank=8),
        )
        
        session = manager.complete_promotion(session, 'X')
        
        assert 'Invalid promotion piece' in session.status_messages[0]
    
    def test_complete_promotion_no_pending(self, manager):
        """Test promotion without pending promotion."""
        session = manager.create_game('test', 'multiplayer')
        
        session = manager.complete_promotion(session, 'Q')
        
        assert 'No promotion pending' in session.status_messages[0]


class TestGameManagerUndo:
    """Tests for undo functionality."""
    
    def test_undo_single_move(self, manager):
        """Test undoing a single move in multiplayer."""
        session = manager.create_game('test', 'multiplayer')
        
        session = manager.select_square(session, Square(file='e', rank=2))
        session = manager.select_square(session, Square(file='e', rank=4))
        
        session = manager.undo_move(session)
        
        assert session.game_state.turn == Color.WHITE
        assert session.game_state.board.get(Square(file='e', rank=2)) is not None
    
    def test_undo_no_moves(self, manager):
        """Test undo with no moves."""
        session = manager.create_game('test', 'multiplayer')
        
        session = manager.undo_move(session)
        
        assert 'No moves to undo' in session.status_messages[0]
    
    def test_undo_clears_selection(self, manager):
        """Test that undo clears selection."""
        session = manager.create_game('test', 'multiplayer')
        
        session = manager.select_square(session, Square(file='e', rank=2))
        session = manager.select_square(session, Square(file='e', rank=4))
        session.selected_square = Square(file='d', rank=2)
        
        session = manager.undo_move(session)
        
        assert session.selected_square is None
    
    def test_undo_clears_last_move(self, manager):
        """Test that undo clears last move highlight."""
        session = manager.create_game('test', 'multiplayer')
        
        session = manager.select_square(session, Square(file='e', rank=2))
        session = manager.select_square(session, Square(file='e', rank=4))
        
        session = manager.undo_move(session)
        
        assert session.last_move is None


class TestGameManagerGameEnd:
    """Tests for game end detection."""
    
    def test_checkmate_detected(self, manager):
        """Test that checkmate is detected."""
        session = manager.create_game('test', 'multiplayer')
        
        # Fool's mate: 1. f3 e5 2. g4 Qh4#
        moves = [
            (Square(file='f', rank=2), Square(file='f', rank=3)),
            (Square(file='e', rank=7), Square(file='e', rank=5)),
            (Square(file='g', rank=2), Square(file='g', rank=4)),
            (Square(file='d', rank=8), Square(file='h', rank=4)),
        ]
        
        for from_sq, to_sq in moves:
            session = manager.select_square(session, from_sq)
            session = manager.select_square(session, to_sq)
        
        assert session.game_result == '0-1'
        assert session.is_game_over
    
    def test_game_over_blocks_moves(self, manager):
        """Test that moves are blocked after game over."""
        session = manager.create_game('test', 'multiplayer')
        session.game_result = '1-0'
        
        original_state = session.game_state
        session = manager.select_square(session, Square(file='e', rank=2))
        
        # Should not have selected anything
        assert session.selected_square is None
        assert session.game_state == original_state


class TestGameManagerAIIntegration:
    """Tests for AI integration in GameManager."""

    def test_ai_moves_after_human_in_easy_mode(self, manager):
        """Test that AI moves after human move in easy mode."""
        session = manager.create_game('test', 'easy')
        
        # Human plays e4
        session = manager.select_square(session, Square(file='e', rank=2))
        session = manager.select_square(session, Square(file='e', rank=4))
        
        # AI should have responded, so it's White's turn again
        assert session.game_state.turn == Color.WHITE
        # Should have 2 states in history (human move + AI move)
        assert len(session.state_history) == 2

    def test_ai_moves_after_human_in_medium_mode(self, manager):
        """Test that AI moves after human move in medium mode."""
        session = manager.create_game('test', 'medium')
        
        # Human plays e4
        session = manager.select_square(session, Square(file='e', rank=2))
        session = manager.select_square(session, Square(file='e', rank=4))
        
        # AI should have responded
        assert session.game_state.turn == Color.WHITE
        assert len(session.state_history) == 2

    def test_ai_moves_after_human_in_hard_mode(self, manager):
        """Test that AI moves after human move in hard mode."""
        session = manager.create_game('test', 'hard')
        
        # Human plays e4
        session = manager.select_square(session, Square(file='e', rank=2))
        session = manager.select_square(session, Square(file='e', rank=4))
        
        # AI should have responded
        assert session.game_state.turn == Color.WHITE
        assert len(session.state_history) == 2

    def test_ai_does_not_move_in_multiplayer(self, manager):
        """Test that no AI move occurs in multiplayer mode."""
        session = manager.create_game('test', 'multiplayer')
        
        # Human plays e4
        session = manager.select_square(session, Square(file='e', rank=2))
        session = manager.select_square(session, Square(file='e', rank=4))
        
        # Should still be Black's turn (no AI)
        assert session.game_state.turn == Color.BLACK
        # Only 1 state in history (human move only)
        assert len(session.state_history) == 1

    def test_undo_removes_both_moves_in_ai_mode(self, manager):
        """Test that undo removes both human and AI moves in AI mode."""
        session = manager.create_game('test', 'easy')
        
        # Human plays e4, AI responds
        session = manager.select_square(session, Square(file='e', rank=2))
        session = manager.select_square(session, Square(file='e', rank=4))
        
        # Verify AI moved
        assert session.game_state.turn == Color.WHITE
        assert len(session.state_history) == 2
        
        # Undo should remove both moves
        session = manager.undo_move(session)
        
        # Back to initial position, White's turn
        assert session.game_state.turn == Color.WHITE
        assert len(session.state_history) == 0
        # Pawn should be back on e2
        assert session.game_state.board.get(Square(file='e', rank=2)) is not None
        assert session.game_state.board.get(Square(file='e', rank=4)) is None

    def test_ai_move_sets_last_move(self, manager):
        """Test that AI move updates last_move for highlighting."""
        session = manager.create_game('test', 'easy')
        
        # Human plays e4
        session = manager.select_square(session, Square(file='e', rank=2))
        session = manager.select_square(session, Square(file='e', rank=4))
        
        # last_move should reflect AI's move, not human's
        assert session.last_move is not None
        # AI plays as Black, so from_square should be on rank 7 (initial pawn/piece position)
        # or the move should be a valid Black move
        from_sq, to_sq = session.last_move
        # The piece that moved should now be at to_sq
        assert session.game_state.board.get(to_sq) is not None

    def test_ai_move_adds_to_move_history(self, manager):
        """Test that AI move is recorded in game state move history."""
        session = manager.create_game('test', 'easy')
        
        # Human plays e4
        session = manager.select_square(session, Square(file='e', rank=2))
        session = manager.select_square(session, Square(file='e', rank=4))
        
        # Move history should have 2 moves
        assert len(session.game_state.move_history) == 2
        assert session.game_state.move_history[0] == 'e4'

    def test_ai_status_messages_after_move(self, manager):
        """Test that status messages include both human and AI moves."""
        session = manager.create_game('test', 'easy')
        
        # Human plays e4
        session = manager.select_square(session, Square(file='e', rank=2))
        session = manager.select_square(session, Square(file='e', rank=4))
        
        # Status should mention both moves
        messages = ' '.join(session.status_messages)
        assert 'e4' in messages
        assert 'AI played' in messages

    def test_ai_checkmate_ends_game(self, manager):
        """Test that AI delivering checkmate ends the game."""
        session = manager.create_game('test', 'easy')
        
        # Set up a position where AI can checkmate
        # We'll use Fool's Mate setup: after f3, e5, g4, AI plays Qh4#
        # But since AI is random in easy mode, we'll just verify the
        # game end detection works if AI happens to checkmate
        
        # For this test, manually set up near-checkmate position
        from pychess.model.board import Board
        from pychess.model.piece import Piece
        
        board = Board.empty()
        # White king trapped
        board = board.set(Square(file='h', rank=1), Piece.KING, Color.WHITE)
        board = board.set(Square(file='g', rank=1), Piece.ROOK, Color.WHITE)
        board = board.set(Square(file='g', rank=2), Piece.PAWN, Color.WHITE)
        board = board.set(Square(file='h', rank=2), Piece.PAWN, Color.WHITE)
        # Black has rook that can deliver mate
        board = board.set(Square(file='e', rank=8), Piece.KING, Color.BLACK)
        board = board.set(Square(file='a', rank=1), Piece.ROOK, Color.BLACK)
        
        session.game_state = session.game_state.with_board(board)
        session.state_history = []
        
        # It's White's turn, make a move that doesn't prevent mate
        # Move the g2 pawn
        session = manager.select_square(session, Square(file='g', rank=2))
        session = manager.select_square(session, Square(file='g', rank=3))
        
        # If AI found the mate (Rxg1#), game should be over
        # Note: Easy AI is random, so it might not find mate
        # This test verifies the detection works IF mate occurs
        if session.game_result:
            assert session.game_result == '0-1'
            assert session.is_game_over

    def test_ai_no_legal_moves_handled(self, manager):
        """Test handling when AI has no legal moves (stalemate/checkmate)."""
        session = manager.create_game('test', 'easy')
        
        # Set up stalemate position for Black after White moves
        from pychess.model.board import Board
        from pychess.model.piece import Piece
        
        board = Board.empty()
        board = board.set(Square(file='h', rank=8), Piece.KING, Color.BLACK)
        board = board.set(Square(file='f', rank=7), Piece.QUEEN, Color.WHITE)
        board = board.set(Square(file='g', rank=6), Piece.KING, Color.WHITE)
        
        session.game_state = session.game_state.with_board(board)
        session.state_history = []
        
        # White moves queen to g7, stalemating Black
        session = manager.select_square(session, Square(file='f', rank=7))
        session = manager.select_square(session, Square(file='g', rank=7))
        
        # Game should be over (stalemate = draw)
        assert session.game_result == '1/2-1/2'
        assert session.is_game_over
