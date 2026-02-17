"""Tests for Flask application creation and configuration."""

import pytest

from pychess.web.app import create_app


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
    
    def test_app_has_secret_key(self):
        """Test that app has a secret key configured."""
        app = create_app()
        assert app.config['SECRET_KEY'] is not None
        assert len(app.config['SECRET_KEY']) > 0
    
    def test_app_secret_key_can_be_overridden(self):
        """Test that secret key can be set via config."""
        app = create_app({'SECRET_KEY': 'test-secret'})
        assert app.config['SECRET_KEY'] == 'test-secret'
    
    def test_app_has_secure_session_settings(self):
        """Test that session cookies have secure settings."""
        app = create_app()
        assert app.config['SESSION_COOKIE_HTTPONLY'] is True
        assert app.config['SESSION_COOKIE_SAMESITE'] == 'Lax'
