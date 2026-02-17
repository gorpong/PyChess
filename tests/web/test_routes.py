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
    
    def test_index_shows_hints_button_for_multiplayer(self, client):
        """Test that hints button is shown in multiplayer mode."""
        client.get('/')  # Creates multiplayer by default
        response = client.get('/')
        assert b'Show Hints' in response.data
    
    def test_index_shows_hints_disabled_message_for_hard(self, client):
        """Test that hints are disabled message shows in hard mode."""
        client.post('/api/new-game', data={'mode': 'hard'})
        response = client.get('/')
        assert b'Hints disabled in Hard mode' in response.data


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
    
    def test_new_game_creates_ai_modes(self, client):
        """Test creating AI games at various difficulties."""
        for mode in ('easy', 'medium', 'hard'):
            client.post('/api/new-game', data={'mode': mode})
            
            manager = get_game_manager()
            with client.session_transaction() as sess:
                session_id = sess.get('game_session_id')
            
            game = manager.get_game(session_id)
            assert game.game_mode == mode
            assert game.ai_engine is not None


class TestSelectSquareRoute:
    """Tests for square selection route."""
    
    def test_select_own_piece(self, client):
        """Test selecting own piece highlights it."""
        client.get('/')  # Create session
        response = client.post('/api/select', data={'square': 'e2'})
        
        assert response.status_code == 200
        assert b'selected' in response.data
        assert b'Selected White Pawn' in response.data
    
    def test_select_opponent_piece_rejected(self, client):
        """Test that selecting opponent's piece shows error."""
        client.get('/')
        response = client.post('/api/select', data={'square': 'e7'})
        
        assert response.status_code == 200
        assert b"not your piece" in response.data.lower()
    
    def test_select_empty_square_clears_selection(self, client):
        """Test that selecting empty square clears selection."""
        client.get('/')
        client.post('/api/select', data={'square': 'e2'})  # Select pawn
        response = client.post('/api/select', data={'square': 'e4'})  # Click empty
        
        assert b'Selection cleared' in response.data
    
    def test_select_same_square_deselects(self, client):
        """Test that clicking selected square deselects it."""
        client.get('/')
        client.post('/api/select', data={'square': 'e2'})
        response = client.post('/api/select', data={'square': 'e2'})
        
        assert b'Selection cleared' in response.data
    
    def test_select_invalid_square_ignored(self, client):
        """Test that invalid square strings are ignored."""
        client.get('/')
        response = client.post('/api/select', data={'square': 'invalid'})
        
        assert response.status_code == 200
    
    def test_select_without_session_redirects(self, client):
        """Test that selecting without session redirects to index."""
        response = client.post('/api/select', data={'square': 'e2'})
        
        assert response.status_code == 302


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
        assert b'Showing' in response.data
    
    def test_toggle_hints_off(self, client):
        """Test that toggling hints again hides them."""
        client.get('/')
        client.post('/api/select', data={'square': 'e2'})
        client.post('/api/toggle-hints')  # Turn on
        response = client.post('/api/toggle-hints')  # Turn off
        
        assert b'Hints hidden' in response.data
    
    def test_hints_not_available_in_hard_mode(self, client):
        """Test that hints are not available in hard mode."""
        client.post('/api/new-game', data={'mode': 'hard'})
        client.post('/api/select', data={'square': 'e2'})
        response = client.post('/api/toggle-hints')
        
        assert b'not available in Hard mode' in response.data
        assert b'legal-move' not in response.data
    
    def test_hints_available_in_easy_mode(self, client):
        """Test that hints are available in easy mode."""
        client.post('/api/new-game', data={'mode': 'easy'})
        client.post('/api/select', data={'square': 'e2'})
        response = client.post('/api/toggle-hints')
        
        assert b'legal-move' in response.data
    
    def test_hints_available_in_medium_mode(self, client):
        """Test that hints are available in medium mode."""
        client.post('/api/new-game', data={'mode': 'medium'})
        client.post('/api/select', data={'square': 'e2'})
        response = client.post('/api/toggle-hints')
        
        assert b'legal-move' in response.data
    
    def test_hints_available_in_multiplayer(self, client):
        """Test that hints are available in multiplayer mode."""
        client.post('/api/new-game', data={'mode': 'multiplayer'})
        client.post('/api/select', data={'square': 'e2'})
        response = client.post('/api/toggle-hints')
        
        assert b'legal-move' in response.data
    
    def test_hints_reset_on_new_selection(self, client):
        """Test that hints are reset when selecting a different piece."""
        client.get('/')
        client.post('/api/select', data={'square': 'e2'})
        client.post('/api/toggle-hints')  # Turn on hints
        response = client.post('/api/select', data={'square': 'd2'})  # Select different piece
        
        # Hints should be off for new selection
        assert b'legal-move' not in response.data
