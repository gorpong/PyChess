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
    
    def test_index_contains_piece_images(self, client):
        """Test that board contains piece images."""
        response = client.get('/')
        assert b'wK.svg' in response.data
        assert b'bK.svg' in response.data
    
    def test_index_contains_rank_labels(self, client):
        """Test that board has rank labels."""
        response = client.get('/')
        assert b'rank-labels' in response.data
    
    def test_index_contains_file_labels(self, client):
        """Test that board has file labels."""
        response = client.get('/')
        assert b'file-labels' in response.data
    
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
    
    def test_index_persists_session(self, client):
        """Test that session persists across requests."""
        client.get('/')
        
        with client.session_transaction() as sess:
            first_session_id = sess.get('game_session_id')
        
        client.get('/')
        
        with client.session_transaction() as sess:
            second_session_id = sess.get('game_session_id')
        
        assert first_session_id == second_session_id


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
        assert game.ai_engine is None
    
    def test_new_game_creates_easy_ai(self, client):
        """Test creating an easy AI game."""
        client.post('/api/new-game', data={'mode': 'easy'})
        
        manager = get_game_manager()
        with client.session_transaction() as sess:
            session_id = sess.get('game_session_id')
        
        game = manager.get_game(session_id)
        assert game is not None
        assert game.game_mode == 'easy'
        assert game.ai_engine is not None
    
    def test_new_game_creates_medium_ai(self, client):
        """Test creating a medium AI game."""
        client.post('/api/new-game', data={'mode': 'medium'})
        
        manager = get_game_manager()
        with client.session_transaction() as sess:
            session_id = sess.get('game_session_id')
        
        game = manager.get_game(session_id)
        assert game is not None
        assert game.game_mode == 'medium'
        assert game.ai_engine is not None
    
    def test_new_game_creates_hard_ai(self, client):
        """Test creating a hard AI game."""
        client.post('/api/new-game', data={'mode': 'hard'})
        
        manager = get_game_manager()
        with client.session_transaction() as sess:
            session_id = sess.get('game_session_id')
        
        game = manager.get_game(session_id)
        assert game is not None
        assert game.game_mode == 'hard'
        assert game.ai_engine is not None
    
    def test_new_game_replaces_existing(self, client):
        """Test that new game replaces existing session."""
        # Create first game
        client.post('/api/new-game', data={'mode': 'multiplayer'})
        
        with client.session_transaction() as sess:
            first_session_id = sess.get('game_session_id')
        
        # Create second game
        client.post('/api/new-game', data={'mode': 'easy'})
        
        with client.session_transaction() as sess:
            second_session_id = sess.get('game_session_id')
        
        # Session IDs should be different
        assert first_session_id != second_session_id
        
        # Old session should be gone
        manager = get_game_manager()
        assert manager.get_game(first_session_id) is None
        assert manager.get_game(second_session_id) is not None
    
    def test_new_game_invalid_mode_defaults_to_multiplayer(self, client):
        """Test that invalid mode defaults to multiplayer."""
        client.post('/api/new-game', data={'mode': 'invalid'})
        
        manager = get_game_manager()
        with client.session_transaction() as sess:
            session_id = sess.get('game_session_id')
        
        game = manager.get_game(session_id)
        assert game.game_mode == 'multiplayer'
