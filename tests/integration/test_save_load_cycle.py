"""Integration tests for save/load game cycles."""

import pytest

from pychess.web.app import create_app
from pychess.web.game_manager import reset_game_manager, get_game_manager


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


class TestSaveAndLoad:
    """Test saving and loading games."""
    
    def test_save_load_continue_play(self, client):
        """Save a game, load it, and continue playing."""
        # Start game and make moves
        client.post('/api/new-game', data={'mode': 'multiplayer'})
        make_move(client, 'e2', 'e4')
        make_move(client, 'e7', 'e5')
        
        # Save the game
        client.post('/api/games/save', data={'name': 'Test Game', 'save_and_quit': 'true'})
        
        # Load the game
        client.post('/api/games/Test_Game/load')
        
        # Continue playing
        make_move(client, 'g1', 'f3')
        
        manager = get_game_manager()
        with client.session_transaction() as sess:
            session_id = sess.get('game_session_id')
        game = manager.get_game(session_id)
        
        # Should have 3 moves now
        assert len(game.game_state.move_history) == 3
        assert game.game_state.move_history == ['e4', 'e5', 'Nf3']
    
    def test_save_overwrites_existing(self, client, tmp_path):
        """Saving with same name overwrites the existing file."""
        # Start and save first game
        client.post('/api/new-game', data={'mode': 'multiplayer'})
        make_move(client, 'e2', 'e4')
        client.post('/api/games/save', data={'name': 'Overwrite Test', 'save_and_quit': 'false'})
        
        # Make another move and save again
        make_move(client, 'e7', 'e5')
        client.post('/api/games/save', data={'name': 'Overwrite Test', 'save_and_quit': 'true'})
        
        # Load and verify it has both moves
        client.post('/api/games/Overwrite_Test/load')
        
        manager = get_game_manager()
        with client.session_transaction() as sess:
            session_id = sess.get('game_session_id')
        game = manager.get_game(session_id)
        
        assert len(game.game_state.move_history) == 2
        
        # Should only be one file
        pgn_files = list(tmp_path.glob('*.pgn'))
        assert len(pgn_files) == 1
    
    def test_load_preserves_game_mode_multiplayer(self, client):
        """Loading a multiplayer game preserves the mode."""
        client.post('/api/new-game', data={'mode': 'multiplayer'})
        make_move(client, 'e2', 'e4')
        client.post('/api/games/save', data={'name': 'Mode Test MP', 'save_and_quit': 'true'})
        
        client.post('/api/games/Mode_Test_MP/load')
        
        manager = get_game_manager()
        with client.session_transaction() as sess:
            session_id = sess.get('game_session_id')
        game = manager.get_game(session_id)
        
        assert game.game_mode == 'multiplayer'
        assert game.ai_engine is None
    
    def test_load_preserves_game_mode_ai(self, client):
        """Loading an AI game preserves the mode and AI engine."""
        client.post('/api/new-game', data={'mode': 'medium'})
        
        manager = get_game_manager()
        with client.session_transaction() as sess:
            session_id = sess.get('game_session_id')
        game = manager.get_game(session_id)
        
        # Make a move (AI will respond)
        make_move(client, 'e2', 'e4')
        
        # Save
        client.post('/api/games/save', data={'name': 'Mode Test AI', 'save_and_quit': 'true'})
        
        # Load
        client.post('/api/games/Mode_Test_AI/load')
        
        with client.session_transaction() as sess:
            session_id = sess.get('game_session_id')
        game = manager.get_game(session_id)
        
        assert game.game_mode == 'medium'
        assert game.ai_engine is not None
    
    def test_load_completed_game_is_view_only(self, client):
        """Loading a completed game should be view-only."""
        client.post('/api/new-game', data={'mode': 'multiplayer'})
        
        # Play Fool's Mate
        make_move(client, 'f2', 'f3')
        make_move(client, 'e7', 'e5')
        make_move(client, 'g2', 'g4')
        make_move(client, 'd8', 'h4')  # Checkmate
        
        # Save
        client.post('/api/games/save', data={'name': 'Completed Game', 'save_and_quit': 'true'})
        
        # Load
        client.post('/api/games/Completed_Game/load')
        
        manager = get_game_manager()
        with client.session_transaction() as sess:
            session_id = sess.get('game_session_id')
        game = manager.get_game(session_id)
        
        assert game.game_result == '0-1'
        assert game.is_game_over
        # Should not have ended during this session (was loaded)
        assert game.game_ended_during_session is False
    
    def test_multiple_save_load_cycles(self, client):
        """Test multiple save/load cycles maintain consistency."""
        # Cycle 1: Start, play, save
        client.post('/api/new-game', data={'mode': 'multiplayer'})
        make_move(client, 'e2', 'e4')
        client.post('/api/games/save', data={'name': 'Cycle Test', 'save_and_quit': 'true'})
        
        # Cycle 2: Load, play, save
        client.post('/api/games/Cycle_Test/load')
        make_move(client, 'e7', 'e5')
        client.post('/api/games/save', data={'name': 'Cycle Test', 'save_and_quit': 'true'})
        
        # Cycle 3: Load, play, save
        client.post('/api/games/Cycle_Test/load')
        make_move(client, 'g1', 'f3')
        client.post('/api/games/save', data={'name': 'Cycle Test', 'save_and_quit': 'true'})
        
        # Final load and verify
        client.post('/api/games/Cycle_Test/load')
        
        manager = get_game_manager()
        with client.session_transaction() as sess:
            session_id = sess.get('game_session_id')
        game = manager.get_game(session_id)
        
        assert len(game.game_state.move_history) == 3
        assert game.game_state.move_history == ['e4', 'e5', 'Nf3']
    
    def test_save_preserves_move_history_exactly(self, client):
        """Verify move history is preserved exactly through save/load."""
        client.post('/api/new-game', data={'mode': 'multiplayer'})
        
        # Play several moves including special notation
        make_move(client, 'e2', 'e4')
        make_move(client, 'e7', 'e5')
        make_move(client, 'g1', 'f3')
        make_move(client, 'b8', 'c6')
        make_move(client, 'f1', 'b5')  # Bb5
        
        manager = get_game_manager()
        with client.session_transaction() as sess:
            session_id = sess.get('game_session_id')
        game = manager.get_game(session_id)
        
        original_history = game.game_state.move_history.copy()
        
        # Save and quit
        client.post('/api/games/save', data={'name': 'History Test', 'save_and_quit': 'true'})
        
        # Load
        client.post('/api/games/History_Test/load')
        
        with client.session_transaction() as sess:
            session_id = sess.get('game_session_id')
        game = manager.get_game(session_id)
        
        assert game.game_state.move_history == original_history
