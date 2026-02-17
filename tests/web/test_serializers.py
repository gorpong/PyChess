"""Tests for game state serialization."""

import pytest

from pychess.model.board import Board
from pychess.model.game_state import GameState
from pychess.model.piece import Color, Piece
from pychess.model.square import Square
from pychess.web.serializers import (
    board_to_template_data,
    game_state_to_dict,
    is_light_square,
    square_to_piece_code,
    PIECE_CODES,
)


class TestGameStateToDict:
    """Tests for game_state_to_dict function."""
    
    def test_initial_position_turn(self):
        """Test that initial position has white to move."""
        state = GameState.initial()
        data = game_state_to_dict(state)
        assert data['turn'] == 'white'
    
    def test_initial_position_fullmove_number(self):
        """Test that initial position is move 1."""
        state = GameState.initial()
        data = game_state_to_dict(state)
        assert data['fullmove_number'] == 1
    
    def test_initial_position_halfmove_clock(self):
        """Test that initial position has zero halfmove clock."""
        state = GameState.initial()
        data = game_state_to_dict(state)
        assert data['halfmove_clock'] == 0
    
    def test_initial_position_castling_rights(self):
        """Test that initial position has all castling rights."""
        state = GameState.initial()
        data = game_state_to_dict(state)
        assert data['castling']['white']['kingside'] is True
        assert data['castling']['white']['queenside'] is True
        assert data['castling']['black']['kingside'] is True
        assert data['castling']['black']['queenside'] is True
    
    def test_initial_position_no_en_passant(self):
        """Test that initial position has no en passant square."""
        state = GameState.initial()
        data = game_state_to_dict(state)
        assert data['en_passant'] is None
    
    def test_initial_position_empty_history(self):
        """Test that initial position has empty move history."""
        state = GameState.initial()
        data = game_state_to_dict(state)
        assert data['move_history'] == []
    
    def test_initial_position_not_in_check(self):
        """Test that initial position is not in check."""
        state = GameState.initial()
        data = game_state_to_dict(state)
        assert data['is_check'] is False
    
    def test_black_turn_serialization(self):
        """Test serialization when it's black's turn."""
        state = GameState.initial().with_turn(Color.BLACK)
        data = game_state_to_dict(state)
        assert data['turn'] == 'black'
    
    def test_en_passant_square_serialization(self):
        """Test that en passant square is serialized correctly."""
        state = GameState.initial().with_en_passant(Square(file='e', rank=3))
        data = game_state_to_dict(state)
        assert data['en_passant'] == 'e3'
    
    def test_move_history_serialization(self):
        """Test that move history is included."""
        state = GameState.initial().with_move_added('e4').with_move_added('e5')
        data = game_state_to_dict(state)
        assert data['move_history'] == ['e4', 'e5']


class TestSquareToPieceCode:
    """Tests for square_to_piece_code function."""
    
    def test_white_king_code(self):
        """Test white king piece code."""
        board = Board.initial()
        square = Square(file='e', rank=1)
        assert square_to_piece_code(board, square) == 'wK'
    
    def test_black_king_code(self):
        """Test black king piece code."""
        board = Board.initial()
        square = Square(file='e', rank=8)
        assert square_to_piece_code(board, square) == 'bK'
    
    def test_white_pawn_code(self):
        """Test white pawn piece code."""
        board = Board.initial()
        square = Square(file='e', rank=2)
        assert square_to_piece_code(board, square) == 'wP'
    
    def test_black_pawn_code(self):
        """Test black pawn piece code."""
        board = Board.initial()
        square = Square(file='e', rank=7)
        assert square_to_piece_code(board, square) == 'bP'
    
    def test_empty_square_returns_none(self):
        """Test that empty square returns None."""
        board = Board.initial()
        square = Square(file='e', rank=4)
        assert square_to_piece_code(board, square) is None
    
    def test_all_piece_codes_defined(self):
        """Test that all 12 piece codes are defined."""
        assert len(PIECE_CODES) == 12


class TestIsLightSquare:
    """Tests for is_light_square function."""
    
    def test_a1_is_dark(self):
        """Test that a1 is a dark square."""
        square = Square(file='a', rank=1)
        assert is_light_square(square) is False
    
    def test_a8_is_light(self):
        """Test that a8 is a light square."""
        square = Square(file='a', rank=8)
        assert is_light_square(square) is True
    
    def test_h1_is_light(self):
        """Test that h1 is a light square."""
        square = Square(file='h', rank=1)
        assert is_light_square(square) is True
    
    def test_h8_is_dark(self):
        """Test that h8 is a dark square."""
        square = Square(file='h', rank=8)
        assert is_light_square(square) is False
    
    def test_e4_is_light(self):
        """Test that e4 is a light square."""
        square = Square(file='e', rank=4)
        assert is_light_square(square) is True
    
    def test_d4_is_dark(self):
        """Test that d4 is a dark square."""
        square = Square(file='d', rank=4)
        assert is_light_square(square) is False


class TestBoardToTemplateData:
    """Tests for board_to_template_data function."""
    
    def test_returns_8_rows(self):
        """Test that board data has 8 rows."""
        board = Board.initial()
        data = board_to_template_data(board)
        assert len(data) == 8
    
    def test_each_row_has_8_squares(self):
        """Test that each row has 8 squares."""
        board = Board.initial()
        data = board_to_template_data(board)
        assert all(len(row) == 8 for row in data)
    
    def test_first_row_is_rank_8(self):
        """Test that first row is rank 8 (black's back rank)."""
        board = Board.initial()
        data = board_to_template_data(board)
        # First square of first row should be a8
        assert data[0][0]['square'] == 'a8'
        # Last square of first row should be h8
        assert data[0][7]['square'] == 'h8'
    
    def test_last_row_is_rank_1(self):
        """Test that last row is rank 1 (white's back rank)."""
        board = Board.initial()
        data = board_to_template_data(board)
        # First square of last row should be a1
        assert data[7][0]['square'] == 'a1'
        # Last square of last row should be h1
        assert data[7][7]['square'] == 'h1'
    
    def test_black_rook_on_a8(self):
        """Test that a8 has black rook."""
        board = Board.initial()
        data = board_to_template_data(board)
        assert data[0][0]['piece'] == 'bR'
    
    def test_white_king_on_e1(self):
        """Test that e1 has white king."""
        board = Board.initial()
        data = board_to_template_data(board)
        # e1 is in row 7 (rank 1), column 4 (file e)
        assert data[7][4]['piece'] == 'wK'
    
    def test_empty_square_in_center(self):
        """Test that center squares are empty."""
        board = Board.initial()
        data = board_to_template_data(board)
        # e4 is in row 4 (rank 4), column 4 (file e)
        assert data[4][4]['piece'] is None
        assert data[4][4]['has_piece'] is False
    
    def test_square_colors_alternate(self):
        """Test that square colors alternate correctly."""
        board = Board.initial()
        data = board_to_template_data(board)
        # a8 is light
        assert data[0][0]['is_light'] is True
        # b8 is dark
        assert data[0][1]['is_light'] is False
        # a7 is dark
        assert data[1][0]['is_light'] is False
    
    def test_selected_square_flagged(self):
        """Test that selected square is properly flagged."""
        board = Board.initial()
        selected = Square(file='e', rank=2)
        data = board_to_template_data(board, selected=selected)
        
        # e2 is row 6 (rank 2), column 4 (file e)
        assert data[6][4]['is_selected'] is True
        # Other squares should not be selected
        assert data[0][0]['is_selected'] is False
    
    def test_legal_moves_flagged(self):
        """Test that legal move squares are properly flagged."""
        board = Board.initial()
        legal_moves = {Square(file='e', rank=3), Square(file='e', rank=4)}
        data = board_to_template_data(board, legal_moves=legal_moves)
        
        # e3 is row 5, column 4
        assert data[5][4]['is_legal_move'] is True
        # e4 is row 4, column 4
        assert data[4][4]['is_legal_move'] is True
        # e5 should not be flagged
        assert data[3][4]['is_legal_move'] is False
    
    def test_last_move_flagged(self):
        """Test that last move squares are properly flagged."""
        board = Board.initial()
        last_move = (Square(file='e', rank=2), Square(file='e', rank=4))
        data = board_to_template_data(board, last_move=last_move)
        
        # e2 is row 6, column 4
        assert data[6][4]['is_last_move'] is True
        # e4 is row 4, column 4
        assert data[4][4]['is_last_move'] is True
        # e3 should not be flagged
        assert data[5][4]['is_last_move'] is False
    
    def test_has_piece_flag(self):
        """Test that has_piece flag is set correctly."""
        board = Board.initial()
        data = board_to_template_data(board)
        
        # e1 has white king
        assert data[7][4]['has_piece'] is True
        # e4 is empty
        assert data[4][4]['has_piece'] is False
    
    def test_all_square_keys_present(self):
        """Test that all expected keys are present in square data."""
        board = Board.initial()
        data = board_to_template_data(board)
        
        expected_keys = {
            'square', 'piece', 'is_light', 'is_selected',
            'is_legal_move', 'is_last_move', 'has_piece'
        }
        
        for row in data:
            for square_data in row:
                assert set(square_data.keys()) == expected_keys
