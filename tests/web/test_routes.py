"""Tests for web routes."""

import pytest

from pychess.web.app import create_app


@pytest.fixture
def app():
    """Create application for testing."""
    app = create_app({'TESTING': True})
    return app


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


class TestIndexRoute:
    """Tests for index route with board."""
    
    def test_index_returns_200(self, client):
        """Test that index page returns successfully."""
        response = client.get('/')
        assert response.status_code == 200
    
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
        # Should have white king
        assert b'wK.svg' in response.data
        # Should have black king
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
