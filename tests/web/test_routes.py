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
    
    def test_index_shows_mode_selection(self, client):
        """Test that index shows game mode selection."""
        response = client.get('/')
        assert b'Select Game Mode' in response.data
    
    def test_index_shows_multiplayer_option(self, client):
        """Test that multiplayer mode option is shown."""
        response = client.get('/')
        assert b'Multiplayer' in response.data
    
    def test_index_shows_ai_options(self, client):
        """Test that AI difficulty options are shown."""
        response = client.get('/')
        assert b'Easy' in response.data
        assert b'Medium' in response.data
        assert b'Hard' in response.data
    
    def test_index_does_not_create_session(self, client):
        """Test that visiting index does not create a game session."""
        client.get('/')
        
        with client.session_transaction() as sess:
            assert 'game_session_id' not in sess
    
    def test_index_redirects_to_game_if_session_exists(self, client):
        """Test that index redirects to /game if active session exists."""
        # Create a game first
        client.post('/api/new-game', data={'mode': 'multiplayer'})
        
        # Now visiting index should redirect to game
        response = client.get('/')
        assert response.status_code == 302
        assert '/game' in response.location


class TestGameRoute:
    """Tests for game route."""
    
    def test_game_redirects_to_index_without_session(self, client):
        """Test that /game redirects to / without active session."""
        response = client.get('/game')
        assert response.status_code == 302
        assert response.location == '/'
    
    def test_game_returns_200_with_session(self, client):
        """Test that /game returns successfully with active session."""
        client.post('/api/new-game', data={'mode': 'multiplayer'})
        response = client.get('/game')
        assert response.status_code == 200
    
    def test_game_contains_board(self, client):
        """Test that game page contains the board."""
        client.post('/api/new-game', data={'mode': 'multiplayer'})
        response = client.get('/game')
        assert b'id="board"' in response.data
    
    def test_game_contains_64_squares(self, client):
        """Test that board has 64 squares."""
        client.post('/api/new-game', data={'mode': 'multiplayer'})
        response = client.get('/game')
        assert response.data.count(b'class="square') == 64
    
    def test_game_shows_white_to_move(self, client):
        """Test that initial position shows white to move."""
        client.post('/api/new-game', data={'mode': 'multiplayer'})
        response = client.get('/game')
        assert b'White to move' in response.data
    
    def test_game_shows_move_history_panel(self, client):
        """Test that move history panel is shown."""
        client.post('/api/new-game', data={'mode': 'multiplayer'})
        response = client.get('/game')
        assert b'Move History' in response.data
    
    def test_game_shows_control_buttons(self, client):
        """Test that control buttons are shown."""
        client.post('/api/new-game', data={'mode': 'multiplayer'})
        response = client.get('/game')
        assert b'Undo' in response.data
        assert b'Restart' in response.data
        assert b'Quit' in response.data


class TestNewGameRoute:
    """Tests for new game creation route."""
    
    def test_new_game_redirects_to_game(self, client):
        """Test that new game redirects to /game."""
        response = client.post('/api/new-game', data={'mode': 'multiplayer'})
        assert response.status_code == 302
        assert '/game' in response.location
    
    def test_new_game_creates_session(self, client):
        """Test that new game creates a session."""
        client.post('/api/new-game', data={'mode': 'multiplayer'})
        
        with client.session_transaction() as sess:
            assert 'game_session_id' in sess
    
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
    
    def test_new_game_replaces_existing_session(self, client):
        """Test that creating new game replaces existing session."""
        # Create first game
        client.post('/api/new-game', data={'mode': 'multiplayer'})
        with client.session_transaction() as sess:
            first_session_id = sess.get('game_session_id')
        
        # Create second game
        client.post('/api/new-game', data={'mode': 'easy'})
        with client.session_transaction() as sess:
            second_session_id = sess.get('game_session_id')
        
        # Should have different session IDs
        assert first_session_id != second_session_id
        
        # First session should be deleted
        manager = get_game_manager()
        assert manager.get_game(first_session_id) is None


class TestRestartRoute:
    """Tests for game restart route."""
    
    def test_restart_redirects_to_game(self, client):
        """Test that restart redirects to /game."""
        client.post('/api/new-game', data={'mode': 'multiplayer'})
        response = client.post('/api/restart')
        assert response.status_code == 302
        assert '/game' in response.location
    
    def test_restart_preserves_mode(self, client):
        """Test that restart preserves the game mode."""
        client.post('/api/new-game', data={'mode': 'medium'})
        client.post('/api/restart')
        
        manager = get_game_manager()
        with client.session_transaction() as sess:
            session_id = sess.get('game_session_id')
        
        game = manager.get_game(session_id)
        assert game.game_mode == 'medium'
    
    def test_restart_resets_board(self, client):
        """Test that restart resets the board to initial position."""
        client.post('/api/new-game', data={'mode': 'multiplayer'})
        
        # Make a move
        client.post('/api/select', data={'square': 'e2'})
        client.post('/api/select', data={'square': 'e4'})
        
        # Restart
        client.post('/api/restart')
        
        # Check board is reset
        manager = get_game_manager()
        with client.session_transaction() as sess:
            session_id = sess.get('game_session_id')
        
        game = manager.get_game(session_id)
        # e2 should have a pawn again
        from pychess.model.square import Square
        from pychess.model.piece import Piece, Color
        piece = game.game_state.board.get(Square(file='e', rank=2))
        assert piece == (Piece.PAWN, Color.WHITE)
    
    def test_restart_without_session_redirects_to_index(self, client):
        """Test that restart without session redirects to index."""
        response = client.post('/api/restart')
        assert response.status_code == 302
        assert response.location == '/'


class TestQuitRoute:
    """Tests for game quit route."""
    
    def test_quit_redirects_to_index(self, client):
        """Test that quit redirects to /."""
        client.post('/api/new-game', data={'mode': 'multiplayer'})
        response = client.get('/api/quit')
        assert response.status_code == 302
        assert response.location == '/'
    
    def test_quit_deletes_session(self, client):
        """Test that quit deletes the game session."""
        client.post('/api/new-game', data={'mode': 'multiplayer'})
        
        with client.session_transaction() as sess:
            session_id = sess.get('game_session_id')
        
        client.get('/api/quit')
        
        # Session should be deleted
        manager = get_game_manager()
        assert manager.get_game(session_id) is None
    
    def test_quit_clears_session_cookie(self, client):
        """Test that quit clears the session ID from cookie."""
        client.post('/api/new-game', data={'mode': 'multiplayer'})
        client.get('/api/quit')
        
        with client.session_transaction() as sess:
            assert 'game_session_id' not in sess
    
    def test_quit_without_session_no_error(self, client):
        """Test that quit without session doesn't error."""
        response = client.get('/api/quit')
        assert response.status_code == 302
        assert response.location == '/'


class TestSelectSquareRoute:
    """Tests for square selection route."""
    
    def test_select_own_piece(self, client):
        """Test selecting own piece highlights it."""
        client.post('/api/new-game', data={'mode': 'multiplayer'})
        response = client.post('/api/select', data={'square': 'e2'})
        
        assert response.status_code == 200
        assert b'selected' in response.data
    
    def test_select_opponent_piece_rejected(self, client):
        """Test that selecting opponent's piece shows error."""
        client.post('/api/new-game', data={'mode': 'multiplayer'})
        response = client.post('/api/select', data={'square': 'e7'})
        
        assert response.status_code == 200
        assert b"not your piece" in response.data.lower()
    
    def test_select_without_session_redirects(self, client):
        """Test that select without session redirects to index."""
        response = client.post('/api/select', data={'square': 'e2'})
        assert response.status_code == 302
        assert response.location == '/'


class TestMoveExecution:
    """Tests for move execution via select."""
    
    def test_simple_pawn_move(self, client):
        """Test executing a simple pawn move."""
        client.post('/api/new-game', data={'mode': 'multiplayer'})
        client.post('/api/select', data={'square': 'e2'})
        response = client.post('/api/select', data={'square': 'e4'})
        
        assert response.status_code == 200
        assert b'e4' in response.data  # Move should appear in history
    
    def test_move_updates_turn(self, client):
        """Test that move updates turn indicator."""
        client.post('/api/new-game', data={'mode': 'multiplayer'})
        client.post('/api/select', data={'square': 'e2'})
        response = client.post('/api/select', data={'square': 'e4'})
        
        assert b'Black to move' in response.data
    
    def test_move_shows_last_move_highlight(self, client):
        """Test that last move squares are highlighted."""
        client.post('/api/new-game', data={'mode': 'multiplayer'})
        client.post('/api/select', data={'square': 'e2'})
        response = client.post('/api/select', data={'square': 'e4'})
        
        assert b'last-move' in response.data
    
    def test_move_appears_in_history(self, client):
        """Test that move appears in move history."""
        client.post('/api/new-game', data={'mode': 'multiplayer'})
        client.post('/api/select', data={'square': 'e2'})
        response = client.post('/api/select', data={'square': 'e4'})
        
        # Move history should show "1." and "e4"
        assert b'1.' in response.data

    def test_capture_move(self, client):
        """Test executing a capture move."""
        client.post('/api/new-game', data={'mode': 'multiplayer'})
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
        client.post('/api/new-game', data={'mode': 'multiplayer'})
        
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
        
        response = client.get('/game')
        assert b'promotion' in response.data.lower()
    
    def test_promote_to_queen(self, client):
        """Test promoting to queen."""
        client.post('/api/new-game', data={'mode': 'multiplayer'})
        
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
        client.post('/api/new-game', data={'mode': 'multiplayer'})
        client.post('/api/select', data={'square': 'e2'})
        client.post('/api/select', data={'square': 'e4'})
        
        response = client.post('/api/undo')
        
        assert response.status_code == 200
        assert b'Move undone' in response.data
        assert b'White to move' in response.data
    
    def test_undo_no_moves(self, client):
        """Test undo with no moves to undo."""
        client.post('/api/new-game', data={'mode': 'multiplayer'})
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
        client.post('/api/new-game', data={'mode': 'multiplayer'})
        response = client.post('/api/toggle-hints')
        
        assert b'Select a piece first' in response.data
    
    def test_toggle_hints_shows_legal_moves(self, client):
        """Test that toggling hints shows legal moves."""
        client.post('/api/new-game', data={'mode': 'multiplayer'})
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


class TestGamesListRoute:
    """Tests for saved games list route."""
    
    def test_games_list_returns_200(self, client):
        """Test that games list page returns successfully."""
        response = client.get('/games')
        assert response.status_code == 200
    
    def test_games_list_shows_no_games_message(self, client):
        """Test that empty games list shows message."""
        response = client.get('/games')
        assert b'No saved games found' in response.data
    
    def test_games_list_shows_back_button(self, client):
        """Test that games list has back to menu button."""
        response = client.get('/games')
        assert b'Back to Menu' in response.data


class TestSaveGameRoute:
    """Tests for save game functionality."""
    
    def test_show_save_dialog(self, client):
        """Test showing the save dialog."""
        client.post('/api/new-game', data={'mode': 'multiplayer'})
        response = client.post('/api/show-save-dialog', data={'save_and_quit': 'false'})
        
        assert response.status_code == 200
        assert b'Save Game' in response.data or b'save-dialog' in response.data
    
    def test_show_save_and_quit_dialog(self, client):
        """Test showing the save & quit dialog."""
        client.post('/api/new-game', data={'mode': 'multiplayer'})
        response = client.post('/api/show-save-dialog', data={'save_and_quit': 'true'})
        
        assert response.status_code == 200
        assert b'Save' in response.data
    
    def test_cancel_save_dialog(self, client):
        """Test canceling the save dialog."""
        client.post('/api/new-game', data={'mode': 'multiplayer'})
        client.post('/api/show-save-dialog', data={'save_and_quit': 'false'})
        response = client.post('/api/cancel-save')
        
        assert response.status_code == 200
        # Should be back to normal game view
        assert b'save-dialog' not in response.data or b'White to move' in response.data
    
    def test_save_game_empty_name_error(self, client):
        """Test that saving with empty name shows error."""
        client.post('/api/new-game', data={'mode': 'multiplayer'})
        response = client.post('/api/games/save', data={'name': '', 'save_and_quit': 'false'})
        
        assert response.status_code == 200
        assert b'Please enter a name' in response.data
    
    def test_save_game_success(self, client, tmp_path, monkeypatch):
        """Test successful game save."""
        # Use temp directory for saves
        monkeypatch.setattr(
            'pychess.persistence.save_manager.get_default_save_dir',
            lambda: tmp_path
        )
        
        client.post('/api/new-game', data={'mode': 'multiplayer'})
        # Make a move first
        client.post('/api/select', data={'square': 'e2'})
        client.post('/api/select', data={'square': 'e4'})
        
        response = client.post('/api/games/save', data={'name': 'Test Game', 'save_and_quit': 'false'})
        
        assert response.status_code == 200
        assert b'Game saved' in response.data
        
        # Verify file was created
        assert (tmp_path / 'Test_Game.pgn').exists()
    
    def test_save_and_quit_redirects_to_menu(self, client, tmp_path, monkeypatch):
        """Test that save & quit redirects to menu."""
        monkeypatch.setattr(
            'pychess.persistence.save_manager.get_default_save_dir',
            lambda: tmp_path
        )
        
        client.post('/api/new-game', data={'mode': 'multiplayer'})
        response = client.post('/api/games/save', data={'name': 'Test Game', 'save_and_quit': 'true'})
        
        assert response.status_code == 302
        assert response.location == '/'
        
        # Session should be cleared
        with client.session_transaction() as sess:
            assert 'game_session_id' not in sess


class TestLoadGameRoute:
    """Tests for load game functionality."""
    
    def test_load_nonexistent_game_redirects(self, client):
        """Test that loading nonexistent game redirects to games list."""
        response = client.post('/api/games/nonexistent/load')
        
        assert response.status_code == 302
        assert '/games' in response.location
    
    def test_load_game_success(self, client, tmp_path, monkeypatch):
        """Test successful game load."""
        monkeypatch.setattr(
            'pychess.persistence.save_manager.get_default_save_dir',
            lambda: tmp_path
        )
        
        # Create a saved game first
        client.post('/api/new-game', data={'mode': 'multiplayer'})
        client.post('/api/select', data={'square': 'e2'})
        client.post('/api/select', data={'square': 'e4'})
        client.post('/api/games/save', data={'name': 'Load Test', 'save_and_quit': 'true'})
        
        # Now load it
        response = client.post('/api/games/Load_Test/load')
        
        assert response.status_code == 302
        assert '/game' in response.location
        
        # Verify game was loaded
        response = client.get('/game')
        assert b'e4' in response.data  # Move should be in history


class TestDeleteGameRoute:
    """Tests for delete game functionality."""
    
    def test_delete_nonexistent_game_no_error(self, client):
        """Test that deleting nonexistent game doesn't error."""
        response = client.post('/api/games/nonexistent/delete')
        
        # Should redirect to games list without error
        assert response.status_code == 302
        assert '/games' in response.location
    
    def test_delete_game_success(self, client, tmp_path, monkeypatch):
        """Test successful game deletion."""
        monkeypatch.setattr(
            'pychess.persistence.save_manager.get_default_save_dir',
            lambda: tmp_path
        )
        
        # Create a saved game first
        client.post('/api/new-game', data={'mode': 'multiplayer'})
        client.post('/api/games/save', data={'name': 'Delete Test', 'save_and_quit': 'false'})
        
        # Verify file exists
        assert (tmp_path / 'Delete_Test.pgn').exists()
        
        # Delete it
        response = client.post('/api/games/Delete_Test/delete')
        
        assert response.status_code == 302
        assert '/games' in response.location
        
        # Verify file is gone
        assert not (tmp_path / 'Delete_Test.pgn').exists()


class TestQuitRoutePost:
    """Tests for quit route (now POST)."""
    
    def test_quit_post_redirects_to_index(self, client):
        """Test that POST quit redirects to /."""
        client.post('/api/new-game', data={'mode': 'multiplayer'})
        response = client.post('/api/quit')
        
        assert response.status_code == 302
        assert response.location == '/'
    
    def test_quit_get_not_allowed(self, client):
        """Test that GET quit is not allowed."""
        client.post('/api/new-game', data={'mode': 'multiplayer'})
        response = client.get('/api/quit')
        
        # Should return 405 Method Not Allowed
        assert response.status_code == 405
