"""Integration tests for full game scenarios."""

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


class TestFoolsMate:
    """Test Fool's Mate - fastest checkmate (2 moves)."""
    
    def test_fools_mate_black_wins(self, client):
        """Play Fool's Mate: 1.f3 e5 2.g4 Qh4# - Black wins."""
        client.post('/api/new-game', data={'mode': 'multiplayer'})
        
        # 1. f3
        make_move(client, 'f2', 'f3')
        # 1... e5
        make_move(client, 'e7', 'e5')
        # 2. g4
        make_move(client, 'g2', 'g4')
        # 2... Qh4#
        response = make_move(client, 'd8', 'h4')
        
        assert b'Black wins' in response.data or b'0-1' in response.data
        
        # Verify game state
        manager = get_game_manager()
        with client.session_transaction() as sess:
            session_id = sess.get('game_session_id')
        game = manager.get_game(session_id)
        
        assert game.game_result == '0-1'
        assert game.is_game_over


class TestScholarsMate:
    """Test Scholar's Mate - common beginner checkmate."""
    
    def test_scholars_mate_white_wins(self, client):
        """Play Scholar's Mate: 1.e4 e5 2.Bc4 Nc6 3.Qh5 Nf6 4.Qxf7# - White wins."""
        client.post('/api/new-game', data={'mode': 'multiplayer'})
        
        # 1. e4 e5
        make_move(client, 'e2', 'e4')
        make_move(client, 'e7', 'e5')
        # 2. Bc4 Nc6
        make_move(client, 'f1', 'c4')
        make_move(client, 'b8', 'c6')
        # 3. Qh5 Nf6
        make_move(client, 'd1', 'h5')
        make_move(client, 'g8', 'f6')
        # 4. Qxf7#
        response = make_move(client, 'h5', 'f7')
        
        assert b'White wins' in response.data or b'1-0' in response.data
        
        manager = get_game_manager()
        with client.session_transaction() as sess:
            session_id = sess.get('game_session_id')
        game = manager.get_game(session_id)
        
        assert game.game_result == '1-0'


class TestStalemate:
    """Test stalemate detection."""
    
    def test_stalemate_is_draw(self, client):
        """Set up and reach a stalemate position."""
        client.post('/api/new-game', data={'mode': 'multiplayer'})
        
        manager = get_game_manager()
        with client.session_transaction() as sess:
            session_id = sess.get('game_session_id')
        game = manager.get_game(session_id)
        
        # Set up a stalemate position directly
        # Black king on h8, White queen on f7, White king on g6
        from pychess.model.board import Board
        from pychess.model.piece import Piece, Color
        from pychess.model.square import Square
        
        board = Board.empty()
        board = board.set(Square(file='h', rank=8), Piece.KING, Color.BLACK)
        board = board.set(Square(file='e', rank=6), Piece.QUEEN, Color.WHITE)
        board = board.set(Square(file='g', rank=6), Piece.KING, Color.WHITE)
        
        game.game_state = game.game_state.with_board(board)
        game.state_history = []
        manager.update_game(game)
        
        # White plays Qf7, stalemating Black
        response = make_move(client, 'e6', 'f7')
        
        assert b'Draw' in response.data or b'1/2-1/2' in response.data
        
        game = manager.get_game(session_id)
        assert game.game_result == '1/2-1/2'


class TestCastling:
    """Test castling moves."""
    
    def test_kingside_castling(self, client):
        """Test kingside castling (O-O)."""
        client.post('/api/new-game', data={'mode': 'multiplayer'})
        
        # Clear path for kingside castling
        # 1. e4 e5 2. Nf3 Nc6 3. Bc4 Bc5 4. O-O
        make_move(client, 'e2', 'e4')
        make_move(client, 'e7', 'e5')
        make_move(client, 'g1', 'f3')
        make_move(client, 'b8', 'c6')
        make_move(client, 'f1', 'c4')
        make_move(client, 'f8', 'c5')
        
        # Castle kingside
        response = make_move(client, 'e1', 'g1')
        
        manager = get_game_manager()
        with client.session_transaction() as sess:
            session_id = sess.get('game_session_id')
        game = manager.get_game(session_id)
        
        # King should be on g1, rook on f1
        from pychess.model.square import Square
        from pychess.model.piece import Piece, Color
        
        king_pos = game.game_state.board.get(Square(file='g', rank=1))
        rook_pos = game.game_state.board.get(Square(file='f', rank=1))
        
        assert king_pos == (Piece.KING, Color.WHITE)
        assert rook_pos == (Piece.ROOK, Color.WHITE)
        assert 'O-O' in game.game_state.move_history
    
    def test_queenside_castling(self, client):
        """Test queenside castling (O-O-O)."""
        client.post('/api/new-game', data={'mode': 'multiplayer'})
        
        # Clear path for queenside castling
        # 1. d4 d5 2. Nc3 Nc6 3. Bf4 Bf5 4. Qd3 Qd6 5. O-O-O
        make_move(client, 'd2', 'd4')
        make_move(client, 'd7', 'd5')
        make_move(client, 'b1', 'c3')
        make_move(client, 'b8', 'c6')
        make_move(client, 'c1', 'f4')
        make_move(client, 'c8', 'f5')
        make_move(client, 'd1', 'd3')
        make_move(client, 'd8', 'd6')
        
        # Castle queenside
        response = make_move(client, 'e1', 'c1')
        
        manager = get_game_manager()
        with client.session_transaction() as sess:
            session_id = sess.get('game_session_id')
        game = manager.get_game(session_id)
        
        from pychess.model.square import Square
        from pychess.model.piece import Piece, Color
        
        king_pos = game.game_state.board.get(Square(file='c', rank=1))
        rook_pos = game.game_state.board.get(Square(file='d', rank=1))
        
        assert king_pos == (Piece.KING, Color.WHITE)
        assert rook_pos == (Piece.ROOK, Color.WHITE)
        assert 'O-O-O' in game.game_state.move_history


class TestEnPassant:
    """Test en passant capture."""
    
    def test_en_passant_capture(self, client):
        """Test en passant pawn capture."""
        client.post('/api/new-game', data={'mode': 'multiplayer'})
        
        # Set up en passant: 1. e4 a6 2. e5 d5 3. exd6 (en passant)
        make_move(client, 'e2', 'e4')
        make_move(client, 'a7', 'a6')
        make_move(client, 'e4', 'e5')
        make_move(client, 'd7', 'd5')  # Black pawn moves two squares
        
        # En passant capture
        response = make_move(client, 'e5', 'd6')
        
        manager = get_game_manager()
        with client.session_transaction() as sess:
            session_id = sess.get('game_session_id')
        game = manager.get_game(session_id)
        
        from pychess.model.square import Square
        from pychess.model.piece import Piece, Color
        
        # White pawn should be on d6
        pawn_pos = game.game_state.board.get(Square(file='d', rank=6))
        assert pawn_pos == (Piece.PAWN, Color.WHITE)
        
        # Black pawn on d5 should be gone
        captured_pos = game.game_state.board.get(Square(file='d', rank=5))
        assert captured_pos is None


class TestPromotion:
    """Test pawn promotion."""
    
    def test_promotion_to_queen(self, client):
        """Test promoting a pawn to queen."""
        client.post('/api/new-game', data={'mode': 'multiplayer'})
        
        manager = get_game_manager()
        with client.session_transaction() as sess:
            session_id = sess.get('game_session_id')
        game = manager.get_game(session_id)
        
        # Set up promotion position
        from pychess.model.board import Board
        from pychess.model.piece import Piece, Color
        from pychess.model.square import Square
        
        board = Board.empty()
        board = board.set(Square(file='e', rank=1), Piece.KING, Color.WHITE)
        board = board.set(Square(file='e', rank=8), Piece.KING, Color.BLACK)
        board = board.set(Square(file='a', rank=7), Piece.PAWN, Color.WHITE)
        
        game.game_state = game.game_state.with_board(board)
        game.state_history = []
        manager.update_game(game)
        
        # Move pawn to promotion square
        client.post('/api/select', data={'square': 'a7'})
        response = client.post('/api/select', data={'square': 'a8'})
        
        # Should show promotion dialog
        assert b'promotion' in response.data.lower()
        
        # Complete promotion to queen
        response = client.post('/api/promote', data={'piece': 'Q'})
        
        game = manager.get_game(session_id)
        queen_pos = game.game_state.board.get(Square(file='a', rank=8))
        assert queen_pos == (Piece.QUEEN, Color.WHITE)
    
    def test_promotion_to_knight(self, client):
        """Test underpromotion to knight."""
        client.post('/api/new-game', data={'mode': 'multiplayer'})
        
        manager = get_game_manager()
        with client.session_transaction() as sess:
            session_id = sess.get('game_session_id')
        game = manager.get_game(session_id)
        
        from pychess.model.board import Board
        from pychess.model.piece import Piece, Color
        from pychess.model.square import Square
        
        board = Board.empty()
        board = board.set(Square(file='e', rank=1), Piece.KING, Color.WHITE)
        board = board.set(Square(file='e', rank=8), Piece.KING, Color.BLACK)
        board = board.set(Square(file='a', rank=7), Piece.PAWN, Color.WHITE)
        
        game.game_state = game.game_state.with_board(board)
        game.state_history = []
        manager.update_game(game)
        
        # Move pawn and promote to knight
        client.post('/api/select', data={'square': 'a7'})
        client.post('/api/select', data={'square': 'a8'})
        response = client.post('/api/promote', data={'piece': 'N'})
        
        game = manager.get_game(session_id)
        knight_pos = game.game_state.board.get(Square(file='a', rank=8))
        assert knight_pos == (Piece.KNIGHT, Color.WHITE)
