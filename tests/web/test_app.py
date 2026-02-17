"""Tests for Flask application setup."""

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


class TestAppCreation:
    """Tests for application factory."""
    
    def test_app_creates_successfully(self):
        """Test that Flask app can be created."""
        app = create_app()
        assert app is not None
    
    def test_app_is_testing_when_configured(self):
        """Test that test config is applied."""
        app = create_app({'TESTING': True})
        assert app.config['TESTING'] is True


class TestIndexRoute:
    """Tests for index page."""
    
    def test_index_returns_200(self, client):
        """Test that index page returns successfully."""
        response = client.get('/')
        assert response.status_code == 200
    
    def test_index_contains_pychess(self, client):
        """Test that index page contains PyChess branding."""
        response = client.get('/')
        assert b'PyChess' in response.data
    
    def test_index_is_html(self, client):
        """Test that index returns HTML content."""
        response = client.get('/')
        assert b'<!DOCTYPE html>' in response.data
