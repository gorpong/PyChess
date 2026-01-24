"""Tests for pawn promotion dialog in cursor/mouse mode."""

import pytest
from unittest.mock import Mock, MagicMock, patch

from pychess.controller.game_session import GameSession
from pychess.model.game_state import GameState
from pychess.model.piece import Color, Piece
from pychess.model.board import Board
from pychess.model.square import Square
from pychess.ui.cursor import CursorState
from pychess.ui.input_handler import InputType, InputEvent


def create_promotion_position() -> GameState:
    """Create a game state with a white pawn on e7 ready to promote."""
    # Start with empty board
    board = Board.empty()
    
    # Place kings (required for valid position) - keep black king away from e8
    board = board.set(Square.from_algebraic("e1"), Piece.KING, Color.WHITE)
    board = board.set(Square.from_algebraic("a8"), Piece.KING, Color.BLACK)
    
    # Place white pawn on e7 (one step from promotion)
    board = board.set(Square.from_algebraic("e7"), Piece.PAWN, Color.WHITE)
    
    # Create game state with white to move
    state = GameState.initial()
    state = state.with_board(board)
    
    return state


def create_capture_promotion_position() -> GameState:
    """Create a game state with a white pawn on e7 that can capture-promote on d8."""
    board = Board.empty()
    
    # Place kings
    board = board.set(Square.from_algebraic("e1"), Piece.KING, Color.WHITE)
    board = board.set(Square.from_algebraic("a8"), Piece.KING, Color.BLACK)
    
    # Place white pawn on e7
    board = board.set(Square.from_algebraic("e7"), Piece.PAWN, Color.WHITE)
    
    # Place black piece on d8 to capture
    board = board.set(Square.from_algebraic("d8"), Piece.ROOK, Color.BLACK)
    
    state = GameState.initial()
    state = state.with_board(board)
    
    return state


def create_black_promotion_position() -> GameState:
    """Create a game state with a black pawn on e2 ready to promote."""
    board = Board.empty()
    
    # Place kings - keep white king away from e1
    board = board.set(Square.from_algebraic("a1"), Piece.KING, Color.WHITE)
    board = board.set(Square.from_algebraic("e8"), Piece.KING, Color.BLACK)
    
    # Place black pawn on e2 (one step from promotion)
    board = board.set(Square.from_algebraic("e2"), Piece.PAWN, Color.BLACK)
    
    state = GameState.initial()
    state = state.with_board(board)
    state = state.with_turn(Color.BLACK)
    
    return state


class TestPromotionDetection:
    """Tests for detecting when a move requires promotion choice."""

    def test_detects_promotion_move(self):
        """Should detect when cursor move results in promotion."""
        renderer = Mock()
        renderer.prompt_promotion_choice = Mock(return_value=Piece.QUEEN)
        session = GameSession(renderer)
        session.game_state = create_promotion_position()
        
        # Select pawn on e7
        session.cursor_state = CursorState(
            position=Square.from_algebraic("e8"),
            selected_square=Square.from_algebraic("e7")
        )
        
        # Make the move (e7-e8)
        session.handle_input(InputEvent(InputType.SELECT))
        
        # Should have prompted for promotion choice
        renderer.prompt_promotion_choice.assert_called_once()

    def test_detects_capture_promotion(self):
        """Should detect promotion on capture moves."""
        renderer = Mock()
        renderer.prompt_promotion_choice = Mock(return_value=Piece.QUEEN)
        session = GameSession(renderer)
        session.game_state = create_capture_promotion_position()
        
        # Select pawn on e7, move to d8 (capture)
        session.cursor_state = CursorState(
            position=Square.from_algebraic("d8"),
            selected_square=Square.from_algebraic("e7")
        )
        
        session.handle_input(InputEvent(InputType.SELECT))
        
        renderer.prompt_promotion_choice.assert_called_once()

    def test_detects_black_promotion(self):
        """Should detect promotion for black pawns moving to rank 1."""
        renderer = Mock()
        renderer.prompt_promotion_choice = Mock(return_value=Piece.QUEEN)
        session = GameSession(renderer)
        session.game_state = create_black_promotion_position()
        
        # Select black pawn on e2, move to e1
        session.cursor_state = CursorState(
            position=Square.from_algebraic("e1"),
            selected_square=Square.from_algebraic("e2")
        )
        
        session.handle_input(InputEvent(InputType.SELECT))
        
        renderer.prompt_promotion_choice.assert_called_once()


class TestPromotionChoice:
    """Tests for handling user's promotion choice."""

    def test_promotes_to_queen_when_selected(self):
        """Should promote to Queen when user selects Q."""
        renderer = Mock()
        renderer.prompt_promotion_choice = Mock(return_value=Piece.QUEEN)
        session = GameSession(renderer)
        session.game_state = create_promotion_position()
        
        session.cursor_state = CursorState(
            position=Square.from_algebraic("e8"),
            selected_square=Square.from_algebraic("e7")
        )
        
        session.handle_input(InputEvent(InputType.SELECT))
        
        # Check that e8 now has a Queen
        piece_info = session.game_state.board.get(Square.from_algebraic("e8"))
        assert piece_info is not None
        assert piece_info[0] == Piece.QUEEN
        assert piece_info[1] == Color.WHITE

    def test_promotes_to_rook_when_selected(self):
        """Should promote to Rook when user selects R."""
        renderer = Mock()
        renderer.prompt_promotion_choice = Mock(return_value=Piece.ROOK)
        session = GameSession(renderer)
        session.game_state = create_promotion_position()
        
        session.cursor_state = CursorState(
            position=Square.from_algebraic("e8"),
            selected_square=Square.from_algebraic("e7")
        )
        
        session.handle_input(InputEvent(InputType.SELECT))
        
        piece_info = session.game_state.board.get(Square.from_algebraic("e8"))
        assert piece_info is not None
        assert piece_info[0] == Piece.ROOK

    def test_promotes_to_bishop_when_selected(self):
        """Should promote to Bishop when user selects B."""
        renderer = Mock()
        renderer.prompt_promotion_choice = Mock(return_value=Piece.BISHOP)
        session = GameSession(renderer)
        session.game_state = create_promotion_position()
        
        session.cursor_state = CursorState(
            position=Square.from_algebraic("e8"),
            selected_square=Square.from_algebraic("e7")
        )
        
        session.handle_input(InputEvent(InputType.SELECT))
        
        piece_info = session.game_state.board.get(Square.from_algebraic("e8"))
        assert piece_info is not None
        assert piece_info[0] == Piece.BISHOP

    def test_promotes_to_knight_when_selected(self):
        """Should promote to Knight when user selects N."""
        renderer = Mock()
        renderer.prompt_promotion_choice = Mock(return_value=Piece.KNIGHT)
        session = GameSession(renderer)
        session.game_state = create_promotion_position()
        
        session.cursor_state = CursorState(
            position=Square.from_algebraic("e8"),
            selected_square=Square.from_algebraic("e7")
        )
        
        session.handle_input(InputEvent(InputType.SELECT))
        
        piece_info = session.game_state.board.get(Square.from_algebraic("e8"))
        assert piece_info is not None
        assert piece_info[0] == Piece.KNIGHT

    def test_default_to_queen_on_enter(self):
        """Should default to Queen when user presses Enter."""
        renderer = Mock()
        # Returning Queen simulates pressing Enter (default)
        renderer.prompt_promotion_choice = Mock(return_value=Piece.QUEEN)
        session = GameSession(renderer)
        session.game_state = create_promotion_position()
        
        session.cursor_state = CursorState(
            position=Square.from_algebraic("e8"),
            selected_square=Square.from_algebraic("e7")
        )
        
        session.handle_input(InputEvent(InputType.SELECT))
        
        piece_info = session.game_state.board.get(Square.from_algebraic("e8"))
        assert piece_info is not None
        assert piece_info[0] == Piece.QUEEN


class TestPromotionWithMouse:
    """Tests for promotion via mouse input."""

    def test_mouse_drag_triggers_promotion_dialog(self):
        """Mouse drag to promotion square should show promotion dialog."""
        renderer = Mock()
        renderer.prompt_promotion_choice = Mock(return_value=Piece.QUEEN)
        renderer.pixel_to_square = Mock(side_effect=[
            Square.from_algebraic("e7"),  # Click on pawn
            Square.from_algebraic("e8"),  # Release on promotion square
        ])
        
        session = GameSession(renderer)
        session.game_state = create_promotion_position()
        
        # Simulate mouse click on e7 (the pawn)
        click_event = InputEvent(
            InputType.MOUSE_CLICK,
            mouse_x=100,
            mouse_y=50
        )
        session.handle_input(click_event)
        
        # Simulate mouse release on e8 (promotion square)
        release_event = InputEvent(
            InputType.MOUSE_RELEASE,
            mouse_x=100,
            mouse_y=25
        )
        session.handle_input(release_event)
        
        # Should have prompted for promotion
        renderer.prompt_promotion_choice.assert_called_once()

    def test_mouse_click_move_triggers_promotion_dialog(self):
        """Click-to-select then click-to-move should show promotion dialog."""
        renderer = Mock()
        renderer.prompt_promotion_choice = Mock(return_value=Piece.ROOK)
        renderer.pixel_to_square = Mock(return_value=Square.from_algebraic("e8"))
        
        session = GameSession(renderer)
        session.game_state = create_promotion_position()
        
        # First select the pawn via cursor
        session.cursor_state = CursorState(
            position=Square.from_algebraic("e7"),
            selected_square=Square.from_algebraic("e7")
        )
        
        # Click on e8 to move
        click_event = InputEvent(
            InputType.MOUSE_CLICK,
            mouse_x=100,
            mouse_y=25
        )
        session.handle_input(click_event)
        
        # Should have promoted to Rook
        piece_info = session.game_state.board.get(Square.from_algebraic("e8"))
        assert piece_info is not None
        assert piece_info[0] == Piece.ROOK


class TestPromotionSANRecording:
    """Tests for SAN notation recording of promotions."""

    def test_promotion_recorded_in_san(self):
        """Promotion should be recorded with proper SAN notation."""
        renderer = Mock()
        renderer.prompt_promotion_choice = Mock(return_value=Piece.KNIGHT)
        session = GameSession(renderer)
        session.game_state = create_promotion_position()
        
        session.cursor_state = CursorState(
            position=Square.from_algebraic("e8"),
            selected_square=Square.from_algebraic("e7")
        )
        
        session.handle_input(InputEvent(InputType.SELECT))
        
        # Last move should include promotion notation
        last_move = session.game_state.move_history[-1]
        assert "=N" in last_move or "=♞" in last_move  # Knight promotion

    def test_capture_promotion_recorded_correctly(self):
        """Capture with promotion should have correct SAN."""
        renderer = Mock()
        renderer.prompt_promotion_choice = Mock(return_value=Piece.QUEEN)
        session = GameSession(renderer)
        session.game_state = create_capture_promotion_position()
        
        session.cursor_state = CursorState(
            position=Square.from_algebraic("d8"),
            selected_square=Square.from_algebraic("e7")
        )
        
        session.handle_input(InputEvent(InputType.SELECT))
        
        # Last move should be capture with promotion
        last_move = session.game_state.move_history[-1]
        assert "x" in last_move  # Capture notation
        assert "=Q" in last_move or "=♕" in last_move  # Queen promotion


class TestNonPromotionMoves:
    """Tests to ensure non-promotion moves still work correctly."""

    def test_normal_pawn_move_no_dialog(self):
        """Normal pawn moves should not show promotion dialog."""
        renderer = Mock()
        renderer.prompt_promotion_choice = Mock()
        session = GameSession(renderer)
        
        # Move e2-e4 (standard opening)
        session.cursor_state = CursorState(
            position=Square.from_algebraic("e4"),
            selected_square=Square.from_algebraic("e2")
        )
        
        session.handle_input(InputEvent(InputType.SELECT))
        
        # Should NOT have prompted for promotion
        renderer.prompt_promotion_choice.assert_not_called()

    def test_piece_move_no_dialog(self):
        """Non-pawn moves should not show promotion dialog."""
        renderer = Mock()
        renderer.prompt_promotion_choice = Mock()
        session = GameSession(renderer)
        
        # Move knight Ng1-f3
        session.cursor_state = CursorState(
            position=Square.from_algebraic("f3"),
            selected_square=Square.from_algebraic("g1")
        )
        
        session.handle_input(InputEvent(InputType.SELECT))
        
        renderer.prompt_promotion_choice.assert_not_called()
