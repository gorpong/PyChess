"""Tests for web routes."""

import pytest

from pychess.web.app import create_app
from pychess.web.game_manager import reset_game_manager, get_game_manager


@pytest.fixture
def app():
    """Create application for testing."""
    reset_game_manager()
    app = create_app({'TESTING': True, 'SECRET_KEY': 'test-secret'})
    yield app
    reset_game_manager()


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


class TestIndexRoute:
    """Tests for index route."""
    
    def test_index_returns_200(self, client):
        """Test that index page returns successfully."""
        response = client.get('/')
        assert response.status_code == 200
    
    def test_index_returns_html(self, client):
        """Test that index returns HTML content."""
        response = client.get('/')
        assert b'<!DOCTYPE html>' in response.data
    
    def test_index_contains_pychess_branding(self, client):
        """Test that index page contains PyChess branding."""
        response = client.get('/')
        assert b'PyChess' in response.data
    
    def test_index_contains_board(self, client):
        """Test that index page contains the board."""
        response = client.get('/')
        assert b'id="board"' in response.data
    
    def test_index_contains_64_squares(self, client):
        """Test that board has 64 squares."""
        response = client.get('/')
        assert response.data.count(b'class="square') == 64
    
    def test_index_shows_white_to_move(self, client):
        """Test that initial position shows white to move."""
        response = client.get('/')
        assert b'White to move' in response.data
    
    def test_index_creates_session(self, client):
        """Test that visiting index creates a game session."""
        with client.session_transaction() as sess:
            assert 'game_session_id' not in sess
        
        client.get('/')
        
        with client.session_transaction() as sess:
            assert 'game_session_id' in sess
    
    def test_index_shows_move_history_panel(self, client):
        """Test that move history panel is shown."""
        response = client.get('/')
        assert b'Move History' in response.data
    
    def test_index_shows_undo_button(self, client):
        """Test that undo button is shown."""
        response = client.get('/')
        assert b'Undo' in response.data


class TestNewGameRoute:
    """Tests for new game creation route."""
    
    def test_new_game_redirects_to_index(self, client):
        """Test that new game redirects to index."""
        response = client.post('/api/new-game', data={'mode': 'multiplayer'})
        assert response.status_code == 302
        assert response.location == '/'
    
    def test_new_game_creates_multiplayer(self, client):
        """Test creating a multiplayer game."""
        client.post('/api/new-game', data={'mode': 'multiplayer'})
        
        manager = get_game_manager()
        with client.session_transaction() as sess:
            session_id = sess.get('game_session_id')
        
        game = manager.get_game(session_id)
        assert game is not None
        assert game.game_mode == 'multiplayer'
    
    def test_new_game_creates_ai_modes(self, client):
        """Test creating AI games at various difficulties."""
        for mode in ('easy', 'medium', 'hard'):
            client.post('/api/new-game', data={'mode': mode})
            
            manager = get_game_manager()
            with client.session_transaction() as sess:
                session_id = sess.get('game_session_id')
            
            game = manager.get_game(session_id)
            assert game.game_mode == mode


class TestSelectSquareRoute:
    """Tests for square selection route."""
    
    def test_select_own_piece(self, client):
        """Test selecting own piece highlights it."""
        client.get('/')
        response = client.post('/api/select', data={'square': 'e2'})
        
        assert response.status_code == 200
        assert b'selected' in response.data
    
    def test_select_opponent_piece_rejected(self, client):
        """Test that selecting opponent's piece shows error."""
        client.get('/')
        response = client.post('/api/select', data={'square': 'e7'})
        
        assert response.status_code == 200
        assert b"not your piece" in response.data.lower()


class TestMoveExecution:
    """Tests for move execution via select."""
    
    def test_simple_pawn_move(self, client):
        """Test executing a simple pawn move."""
        client.get('/')
        client.post('/api/select', data={'square': 'e2'})
        response = client.post('/api/select', data={'square': 'e4'})
        
        assert response.status_code == 200
        assert b'e4' in response.data  # Move should appear in history
    
    def test_move_updates_turn(self, client):
        """Test that move updates turn indicator."""
        client.get('/')
        client.post('/api/select', data={'square': 'e2'})
        response = client.post('/api/select', data={'square': 'e4'})
        
        assert b'Black to move' in response.data
    
    def test_move_shows_last_move_highlight(self, client):
        """Test that last move squares are highlighted."""
        client.get('/')
        client.post('/api/select', data={'square': 'e2'})
        response = client.post('/api/select', data={'square': 'e4'})
        
        assert b'last-move' in response.data
    
    def test_move_appears_in_history(self, client):
        """Test that move appears in move history."""
        client.get('/')
        client.post('/api/select', data={'square': 'e2'})
        response = client.post('/api/select', data={'square': 'e4'})
        
        # Move history should show "1." and "e4"
        assert b'1.' in response.data
    

    def test_capture_move(self, client):
        """Test executing a capture move."""
        client.get('/')
        # 1. e4 e5 2. Qh5 Nc6 3. Qxf7+ (capture with check)
        moves = [
            ('e2', 'e4'), ('e7', 'e5'),
            ('d1', 'h5'), ('b8', 'c6'),
            ('h5', 'f7'),  # Capture
        ]
        for from_sq, to_sq in moves:
            client.post('/api/select', data={'square': from_sq})
            client.post('/api/select', data={'square': to_sq})

        manager = get_game_manager()
        with client.session_transaction() as sess:
            session_id = sess.get('game_session_id')
        game = manager.get_game(session_id)

        # Verify capture happened - move includes check indicator
        # The move is 'Qxf7+' because it gives check
        assert any('Qxf7' in move for move in game.game_state.move_history)


class TestPromotionRoute:
    """Tests for pawn promotion."""
    
    def test_promotion_shows_dialog(self, client):
        """Test that promotion shows piece selection dialog."""
        # Set up a position with pawn ready to promote
        # This is tricky without direct state manipulation
        # For now, test the promotion endpoint directly
        client.get('/')
        
        manager = get_game_manager()
        with client.session_transaction() as sess:
            session_id = sess.get('game_session_id')
        game = manager.get_game(session_id)
        
        # Manually set up pending promotion
        from pychess.model.square import Square
        from pychess.rules.move import Move
        game.pending_promotion = Move(
            from_square=Square(file='e', rank=7),
            to_square=Square(file='e', rank=8),
        )
        manager.update_game(game)
        
        response = client.get('/')
        assert b'promotion' in response.data.lower()
    
    def test_promote_to_queen(self, client):
        """Test promoting to queen."""
        client.get('/')
        
        manager = get_game_manager()
        with client.session_transaction() as sess:
            session_id = sess.get('game_session_id')
        game = manager.get_game(session_id)
        
        # Manually set up pending promotion
        from pychess.model.square import Square
        from pychess.rules.move import Move
        game.pending_promotion = Move(
            from_square=Square(file='e', rank=7),
            to_square=Square(file='e', rank=8),
        )
        manager.update_game(game)
        
        response = client.post('/api/promote', data={'piece': 'Q'})
        assert response.status_code == 200


class TestUndoRoute:
    """Tests for undo functionality."""
    
    def test_undo_move(self, client):
        """Test undoing a move."""
        client.get('/')
        client.post('/api/select', data={'square': 'e2'})
        client.post('/api/select', data={'square': 'e4'})
        
        response = client.post('/api/undo')
        
        assert response.status_code == 200
        assert b'Move undone' in response.data
        assert b'White to move' in response.data
    
    def test_undo_no_moves(self, client):
        """Test undo with no moves to undo."""
        client.get('/')
        response = client.post('/api/undo')
        
        assert b'No moves to undo' in response.data
    
    def test_undo_in_ai_mode_undoes_both(self, client):
        """Test that undo in AI mode undoes both moves."""
        client.post('/api/new-game', data={'mode': 'easy'})
        client.post('/api/select', data={'square': 'e2'})
        client.post('/api/select', data={'square': 'e4'})
        
        # AI should have moved, making it white's turn again
        response = client.post('/api/undo')
        
        # After undo, should be back to initial position
        assert b'Both moves undone' in response.data


class TestToggleHintsRoute:
    """Tests for hints toggle route."""
    
    def test_toggle_hints_requires_selection(self, client):
        """Test that toggling hints without selection shows message."""
        client.get('/')
        response = client.post('/api/toggle-hints')
        
        assert b'Select a piece first' in response.data
    
    def test_toggle_hints_shows_legal_moves(self, client):
        """Test that toggling hints shows legal moves."""
        client.get('/')
        client.post('/api/select', data={'square': 'e2'})
        response = client.post('/api/toggle-hints')
        
        assert response.status_code == 200
        assert b'legal-move' in response.data
    
    def test_hints_not_available_in_hard_mode(self, client):
        """Test that hints are not available in hard mode."""
        client.post('/api/new-game', data={'mode': 'hard'})
        client.post('/api/select', data={'square': 'e2'})
        response = client.post('/api/toggle-hints')
        
        assert b'not available in Hard mode' in response.data
