"""Tests for mouse support functionality.

This module tests the coordinate conversion from terminal pixels to board squares,
as well as the mouse-based interaction flow.
"""

import pytest
from unittest.mock import Mock, MagicMock
from pychess.model.square import Square
from pychess.ui.terminal import TerminalRenderer


class TestTerminalRendererPixelToSquare:
    """Tests for converting terminal coordinates to board squares."""

    @pytest.fixture
    def renderer(self):
        """Create a renderer with mocked terminal."""
        renderer = TerminalRenderer(use_unicode=True)
        # Mock terminal dimensions
        renderer.term = Mock()
        renderer.term.width = 120
        renderer.term.height = 50
        return renderer

    def test_pixel_to_square_returns_none_outside_board(self, renderer):
        """Clicking outside the board should return None."""
        # Way outside the board
        assert renderer.pixel_to_square(0, 0) is None
        assert renderer.pixel_to_square(1000, 1000) is None
        
    def test_pixel_to_square_returns_none_on_border(self, renderer):
        """Clicking on the board border should return None."""
        # The border is outside the actual squares
        # Need to calculate based on actual board position
        board_x = renderer._get_board_start_x()
        board_y = renderer.BOARD_START_Y
        
        # Click on top border (above rank 8)
        assert renderer.pixel_to_square(board_x + 10, board_y - 1) is None

    def test_pixel_to_square_a1_corner(self, renderer):
        """Clicking on a1 square should return Square a1."""
        board_x = renderer._get_board_start_x()
        board_y = renderer.BOARD_START_Y
        
        # a1 is in the bottom-left of the board (rank 1, file a)
        # Board renders rank 8 at top, rank 1 at bottom
        # So a1 is at y offset of 7 * SQUARE_HEIGHT (7 ranks above it)
        a1_x = board_x + 0 * renderer.SQUARE_WIDTH + renderer.SQUARE_WIDTH // 2
        a1_y = board_y + 7 * renderer.SQUARE_HEIGHT + renderer.SQUARE_HEIGHT // 2
        
        square = renderer.pixel_to_square(a1_x, a1_y)
        assert square == Square(file="a", rank=1)

    def test_pixel_to_square_h8_corner(self, renderer):
        """Clicking on h8 square should return Square h8."""
        board_x = renderer._get_board_start_x()
        board_y = renderer.BOARD_START_Y
        
        # h8 is in the top-right of the board
        h8_x = board_x + 7 * renderer.SQUARE_WIDTH + renderer.SQUARE_WIDTH // 2
        h8_y = board_y + 0 * renderer.SQUARE_HEIGHT + renderer.SQUARE_HEIGHT // 2
        
        square = renderer.pixel_to_square(h8_x, h8_y)
        assert square == Square(file="h", rank=8)

    def test_pixel_to_square_e4_center(self, renderer):
        """Clicking on e4 square should return Square e4."""
        board_x = renderer._get_board_start_x()
        board_y = renderer.BOARD_START_Y
        
        # e4 is file e (index 4), rank 4
        # Rank 4 means 4 ranks from bottom, so 8-4=4 ranks from top
        e4_x = board_x + 4 * renderer.SQUARE_WIDTH + renderer.SQUARE_WIDTH // 2
        e4_y = board_y + 4 * renderer.SQUARE_HEIGHT + renderer.SQUARE_HEIGHT // 2
        
        square = renderer.pixel_to_square(e4_x, e4_y)
        assert square == Square(file="e", rank=4)

    def test_pixel_to_square_all_corners_valid(self, renderer):
        """All four board corners should map to correct squares."""
        board_x = renderer._get_board_start_x()
        board_y = renderer.BOARD_START_Y
        
        test_cases = [
            # (file_idx, rank_from_top, expected_file, expected_rank)
            (0, 7, "a", 1),  # a1 - bottom left
            (7, 7, "h", 1),  # h1 - bottom right
            (0, 0, "a", 8),  # a8 - top left
            (7, 0, "h", 8),  # h8 - top right
        ]
        
        for file_idx, rank_from_top, expected_file, expected_rank in test_cases:
            x = board_x + file_idx * renderer.SQUARE_WIDTH + renderer.SQUARE_WIDTH // 2
            y = board_y + rank_from_top * renderer.SQUARE_HEIGHT + renderer.SQUARE_HEIGHT // 2
            
            square = renderer.pixel_to_square(x, y)
            expected = Square(file=expected_file, rank=expected_rank)
            assert square == expected, f"Expected {expected} but got {square} for ({x}, {y})"

    def test_pixel_to_square_edge_of_square(self, renderer):
        """Clicking at the edge of a square should still return that square."""
        board_x = renderer._get_board_start_x()
        board_y = renderer.BOARD_START_Y
        
        # Click at very start of e4 square (top-left corner of the square)
        e4_x = board_x + 4 * renderer.SQUARE_WIDTH
        e4_y = board_y + 4 * renderer.SQUARE_HEIGHT
        
        square = renderer.pixel_to_square(e4_x, e4_y)
        assert square == Square(file="e", rank=4)

    def test_pixel_to_square_just_before_next_square(self, renderer):
        """Clicking at the end of a square should return that square, not the next."""
        board_x = renderer._get_board_start_x()
        board_y = renderer.BOARD_START_Y
        
        # Click at the very end of e4 square (just before f4)
        e4_x = board_x + 5 * renderer.SQUARE_WIDTH - 1
        e4_y = board_y + 4 * renderer.SQUARE_HEIGHT + renderer.SQUARE_HEIGHT // 2
        
        square = renderer.pixel_to_square(e4_x, e4_y)
        assert square == Square(file="e", rank=4)


class TestTerminalRendererGetBoardStartX:
    """Tests for the board start X coordinate calculation."""

    def test_get_board_start_x_centered(self):
        """Board should be centered in the terminal."""
        renderer = TerminalRenderer(use_unicode=True)
        renderer.term = Mock()
        renderer.term.width = 120
        
        board_x = renderer._get_board_start_x()
        
        # Board should be offset from left edge
        assert board_x > 0
        
    def test_get_board_start_x_minimum_width(self):
        """At minimum width, board start should include centering offset."""
        renderer = TerminalRenderer(use_unicode=True)
        renderer.term = Mock()
        renderer.term.width = renderer.MIN_WIDTH
        
        board_x = renderer._get_board_start_x()
        
        # At minimum width (100), board is still centered
        # board_total_width = 8*6 + 10 = 58
        # center_offset = (100 - 58) // 2 = 21
        # board_x = 21 + 5 = 26
        board_total_width = 8 * renderer.SQUARE_WIDTH + 10
        expected_offset = max(0, (renderer.MIN_WIDTH - board_total_width) // 2)
        assert board_x == expected_offset + renderer.BOARD_START_X

    def test_get_board_start_x_wider_terminal(self):
        """Wider terminal should push board start further right."""
        renderer = TerminalRenderer(use_unicode=True)
        renderer.term = Mock()
        
        renderer.term.width = 100
        x_100 = renderer._get_board_start_x()
        
        renderer.term.width = 150
        x_150 = renderer._get_board_start_x()
        
        assert x_150 > x_100


class TestMouseIntegration:
    """Integration tests for mouse-based piece selection and movement."""

    def test_click_on_own_piece_selects_it(self):
        """Clicking on own piece should select it."""
        # This will be tested more thoroughly in game_session tests
        # For now, verify the Square conversion works end-to-end
        renderer = TerminalRenderer(use_unicode=True)
        renderer.term = Mock()
        renderer.term.width = 120
        renderer.term.height = 50
        
        board_x = renderer._get_board_start_x()
        board_y = renderer.BOARD_START_Y
        
        # Click on e2 (white pawn starting position)
        # e2 is file e (index 4), rank 2 (6 ranks from top)
        e2_x = board_x + 4 * renderer.SQUARE_WIDTH + renderer.SQUARE_WIDTH // 2
        e2_y = board_y + 6 * renderer.SQUARE_HEIGHT + renderer.SQUARE_HEIGHT // 2
        
        square = renderer.pixel_to_square(e2_x, e2_y)
        assert square == Square(file="e", rank=2)
