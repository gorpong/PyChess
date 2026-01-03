"""Shared test fixtures for PyChess."""

import pytest
from pychess.model.board import Board
from pychess.model.piece import Piece, Color
from pychess.model.square import Square


@pytest.fixture
def empty_board():
    """Empty board for move generation tests."""
    return Board.empty()


@pytest.fixture
def initial_board():
    """Standard initial board position."""
    return Board.initial()


def place_piece(board: Board, algebraic: str, piece: Piece, color: Color) -> Board:
    """Helper to place a piece on the board."""
    return board.set(Square.from_algebraic(algebraic), piece, color)
