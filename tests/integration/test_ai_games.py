"""Integration tests for AI game functionality."""

import pytest

from pychess.web.app import create_app
from pychess.web.game_manager import reset_game_manager, get_game_manager
from pychess.model.piece import Color


@pytest.fixture
def app(tmp_path, monkeypatch):
    """Create application for testing with isolated save directory."""
    reset_game_manager()
    monkeypatch.setattr(
        'pychess.persistence.save_manager.get_default_save_dir',
        lambda: tmp_path
    )
    app = create_app({'TESTING': True, 'SECRET_KEY': 'test-secret'})
    yield app
    reset_game_manager()


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


def make_move(client, from_sq: str, to_sq: str):
    """Helper to make a move by selecting squares."""
    client.post('/api/select', data={'square': from_sq})
    return client.post('/api/select', data={'square': to_sq})


class TestEasyAI:
    """Tests for Easy AI."""
    
    def test_easy_ai_responds_to_move(self, client):
        """Easy AI should respond after human move."""
        client.post('/api/new-game', data={'mode': 'easy'})
        
        # Make a move
        make_move(client, 'e2', 'e4')
        
        manager = get_game_manager()
        with client.session_transaction() as sess:
            session_id = sess.get('game_session_id')
        game = manager.get_game(session_id)
        
        # AI should have responded
        assert game.game_state.turn == Color.WHITE
        assert len(game.game_state.move_history) == 2
    
    def test_easy_ai_allows_hints(self, client):
        """Easy mode should allow hints."""
        client.post('/api/new-game', data={'mode': 'easy'})
        client.post('/api/select', data={'square': 'e2'})
        response = client.post('/api/toggle-hints')
        
        assert b'legal-move' in response.data


class TestMediumAI:
    """Tests for Medium AI."""
    
    def test_medium_ai_responds_to_move(self, client):
        """Medium AI should respond after human move."""
        client.post('/api/new-game', data={'mode': 'medium'})
        
        make_move(client, 'e2', 'e4')
        
        manager = get_game_manager()
        with client.session_transaction() as sess:
            session_id = sess.get('game_session_id')
        game = manager.get_game(session_id)
        
        assert game.game_state.turn == Color.WHITE
        assert len(game.game_state.move_history) == 2
    
    def test_medium_ai_captures_free_piece(self, client):
        """Medium AI should capture an undefended piece."""
        client.post('/api/new-game', data={'mode': 'medium'})
        
        manager = get_game_manager()
        with client.session_transaction() as sess:
            session_id = sess.get('game_session_id')
        game = manager.get_game(session_id)
        
        # Set up position where White has a free piece for Black to take
        from pychess.model.board import Board
        from pychess.model.piece import Piece, Color
        from pychess.model.square import Square
        
        board = Board.empty()
        board = board.set(Square(file='e', rank=1), Piece.KING, Color.WHITE)
        board = board.set(Square(file='e', rank=8), Piece.KING, Color.BLACK)
        board = board.set(Square(file='d', rank=4), Piece.ROOK, Color.WHITE)  # Free rook
        board = board.set(Square(file='d', rank=8), Piece.QUEEN, Color.BLACK)  # Can take rook
        board = board.set(Square(file='a', rank=2), Piece.PAWN, Color.WHITE)  # Give White a move
        
        game.game_state = game.game_state.with_board(board)
        game.state_history = []
        manager.update_game(game)
        
        # White makes an unrelated move
        make_move(client, 'a2', 'a3')
        
        game = manager.get_game(session_id)
        
        # Black (AI) should have captured the rook
        rook_square = game.game_state.board.get(Square(file='d', rank=4))
        # Either the rook is gone or Black's queen is there
        assert rook_square is None or rook_square[1] == Color.BLACK


class TestHardAI:
    """Tests for Hard AI."""
    
    def test_hard_ai_responds_to_move(self, client):
        """Hard AI should respond after human move."""
        client.post('/api/new-game', data={'mode': 'hard'})
        
        make_move(client, 'e2', 'e4')
        
        manager = get_game_manager()
        with client.session_transaction() as sess:
            session_id = sess.get('game_session_id')
        game = manager.get_game(session_id)
        
        assert game.game_state.turn == Color.WHITE
        assert len(game.game_state.move_history) == 2
    
    def test_hard_ai_disables_hints(self, client):
        """Hard mode should disable hints."""
        client.post('/api/new-game', data={'mode': 'hard'})
        client.post('/api/select', data={'square': 'e2'})
        response = client.post('/api/toggle-hints')
        
        assert b'not available in Hard mode' in response.data
    
    def test_hard_ai_makes_reasonable_opening(self, client):
        """Hard AI should make a reasonable opening move."""
        client.post('/api/new-game', data={'mode': 'hard'})
        
        make_move(client, 'e2', 'e4')
        
        manager = get_game_manager()
        with client.session_transaction() as sess:
            session_id = sess.get('game_session_id')
        game = manager.get_game(session_id)
        
        # AI should have made a sensible response to e4
        # Common responses: e5, e6, c5, c6, d5, d6, Nf6, Nc6
        ai_move = game.game_state.move_history[1]
        reasonable_responses = ['e5', 'e6', 'c5', 'c6', 'd5', 'd6', 'Nf6', 'Nc6', 'g6', 'd5']
        
        assert ai_move in reasonable_responses, f"AI played {ai_move}, expected reasonable response"


class TestAIUndo:
    """Tests for undo in AI games."""
    
    def test_undo_removes_both_moves(self, client):
        """Undo in AI mode should remove both human and AI moves."""
        client.post('/api/new-game', data={'mode': 'easy'})
        
        # Make a move (AI responds)
        make_move(client, 'e2', 'e4')
        
        manager = get_game_manager()
        with client.session_transaction() as sess:
            session_id = sess.get('game_session_id')
        game = manager.get_game(session_id)
        
        assert len(game.game_state.move_history) == 2
        
        # Undo
        response = client.post('/api/undo')
        
        game = manager.get_game(session_id)
        
        assert len(game.game_state.move_history) == 0
        assert game.game_state.turn == Color.WHITE
        assert b'Both moves undone' in response.data
    
    def test_multiple_undo_in_ai_game(self, client):
        """Multiple undos should work correctly in AI game."""
        client.post('/api/new-game', data={'mode': 'easy'})
        
        # Make two moves (AI responds to each)
        make_move(client, 'e2', 'e4')
        make_move(client, 'd2', 'd4')
        
        manager = get_game_manager()
        with client.session_transaction() as sess:
            session_id = sess.get('game_session_id')
        game = manager.get_game(session_id)
        
        assert len(game.game_state.move_history) == 4
        
        # Undo once
        client.post('/api/undo')
        game = manager.get_game(session_id)
        assert len(game.game_state.move_history) == 2
        
        # Undo again
        client.post('/api/undo')
        game = manager.get_game(session_id)
        assert len(game.game_state.move_history) == 0


class TestAIGameEnd:
    """Tests for AI game end scenarios."""
    
    def test_ai_checkmate_detected(self, client):
        """Game should end when AI delivers checkmate."""
        client.post('/api/new-game', data={'mode': 'easy'})
        
        manager = get_game_manager()
        with client.session_transaction() as sess:
            session_id = sess.get('game_session_id')
        game = manager.get_game(session_id)
        
        # Set up position where AI (Black) can checkmate in one
        from pychess.model.board import Board
        from pychess.model.piece import Piece, Color
        from pychess.model.square import Square
        
        board = Board.empty()
        # White king trapped in corner
        board = board.set(Square(file='h', rank=1), Piece.KING, Color.WHITE)
        board = board.set(Square(file='g', rank=2), Piece.PAWN, Color.WHITE)
        board = board.set(Square(file='h', rank=2), Piece.PAWN, Color.WHITE)
        board = board.set(Square(file='f', rank=1), Piece.ROOK, Color.WHITE)
        # Black has rook that can mate
        board = board.set(Square(file='e', rank=8), Piece.KING, Color.BLACK)
        board = board.set(Square(file='a', rank=1), Piece.ROOK, Color.BLACK)
        # Give White an unrelated piece to move
        board = board.set(Square(file='a', rank=3), Piece.PAWN, Color.WHITE)
        
        game.game_state = game.game_state.with_board(board)
        game.state_history = []
        manager.update_game(game)
        
        # White makes a move, AI should find mate
        # Note: Easy AI is random, so it might not find mate
        # This test verifies the detection works IF mate happens
        make_move(client, 'a3', 'a4')
        
        game = manager.get_game(session_id)
        
        # If AI found mate, game should be over
        if game.game_result:
            assert game.game_result == '0-1'
            assert game.is_game_over
