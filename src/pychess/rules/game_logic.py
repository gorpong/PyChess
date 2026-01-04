"""Game end condition detection (checkmate, stalemate, draws)."""

from typing import Optional

from pychess.model.board import Board
from pychess.model.game_state import GameState
from pychess.model.piece import Piece, Color
from pychess.model.square import Square
from pychess.rules.validator import is_in_check, get_legal_moves


def is_checkmate(game_state: GameState) -> bool:
    """Check if the current player is in checkmate.

    Checkmate occurs when:
    1. The player's king is in check
    2. The player has no legal moves

    Args:
        game_state: Current game state

    Returns:
        True if the current player is checkmated
    """
    active_color = game_state.active_color

    # Must be in check
    if not is_in_check(game_state.board, active_color):
        return False

    # Must have no legal moves
    legal_moves = get_legal_moves(game_state)
    return len(legal_moves) == 0


def is_stalemate(game_state: GameState) -> bool:
    """Check if the current player is in stalemate.

    Stalemate occurs when:
    1. The player's king is NOT in check
    2. The player has no legal moves

    Args:
        game_state: Current game state

    Returns:
        True if the current player is stalemated
    """
    active_color = game_state.active_color

    # Must NOT be in check
    if is_in_check(game_state.board, active_color):
        return False

    # Must have no legal moves
    legal_moves = get_legal_moves(game_state)
    return len(legal_moves) == 0


def is_fifty_move_rule(game_state: GameState) -> bool:
    """Check if the fifty-move rule applies.

    The fifty-move rule allows a player to claim a draw if no pawn has moved
    and no capture has been made in the last fifty moves by each player
    (100 half-moves total).

    Args:
        game_state: Current game state

    Returns:
        True if 50-move rule draw can be claimed (halfmove_clock >= 100)
    """
    return game_state.halfmove_clock >= 100


def is_threefold_repetition(game_state: GameState) -> bool:
    """Check if the position has occurred three times.

    A position is considered the same if:
    - Same pieces on same squares
    - Same player to move
    - Same castling rights
    - Same en passant possibilities

    Args:
        game_state: Current game state

    Returns:
        True if current position has occurred three times total
    """
    current_hash = game_state.position_hash
    position_history = game_state.position_history

    # Count occurrences in history plus current position
    count = position_history.count(current_hash) + 1

    return count >= 3


def is_insufficient_material(board: Board) -> bool:
    """Check if neither player can checkmate due to insufficient material.

    Insufficient material occurs with:
    - K vs K
    - K+B vs K
    - K+N vs K
    - K+B vs K+B (bishops on same color squares)

    Args:
        board: Current board position

    Returns:
        True if neither player can force checkmate
    """
    white_pieces = board.get_pieces_by_color(Color.WHITE)
    black_pieces = board.get_pieces_by_color(Color.BLACK)

    # Extract piece types (excluding kings)
    white_non_kings = [(sq, p) for sq, p in white_pieces if p != Piece.KING]
    black_non_kings = [(sq, p) for sq, p in black_pieces if p != Piece.KING]

    white_count = len(white_non_kings)
    black_count = len(black_non_kings)

    # K vs K
    if white_count == 0 and black_count == 0:
        return True

    # K+minor vs K (minor = bishop or knight)
    if white_count == 0 and black_count == 1:
        piece = black_non_kings[0][1]
        if piece in (Piece.BISHOP, Piece.KNIGHT):
            return True

    if black_count == 0 and white_count == 1:
        piece = white_non_kings[0][1]
        if piece in (Piece.BISHOP, Piece.KNIGHT):
            return True

    # K+B vs K+B (same color bishops)
    if white_count == 1 and black_count == 1:
        white_sq, white_piece = white_non_kings[0]
        black_sq, black_piece = black_non_kings[0]

        if white_piece == Piece.BISHOP and black_piece == Piece.BISHOP:
            # Check if bishops are on same color squares
            white_bishop_color = _square_color(white_sq)
            black_bishop_color = _square_color(black_sq)

            if white_bishop_color == black_bishop_color:
                return True

    return False


def _square_color(square: Square) -> str:
    """Determine the color of a square (light or dark).

    Args:
        square: The square to check

    Returns:
        "light" or "dark"
    """
    # a1 is dark, h1 is light, etc.
    # Sum of file_index (0-7) + rank (1-8) is odd for light, even for dark
    file_idx = square.file_index
    rank = square.rank

    if (file_idx + rank) % 2 == 0:
        return "dark"
    return "light"


def get_game_result(game_state: GameState) -> Optional[str]:
    """Determine the game result if the game is over.

    Args:
        game_state: Current game state

    Returns:
        "1-0" if white wins
        "0-1" if black wins
        "1/2-1/2" if draw
        None if game is ongoing
    """
    # Check for checkmate
    if is_checkmate(game_state):
        # The player to move is checkmated, so opponent wins
        if game_state.active_color == Color.WHITE:
            return "0-1"  # Black wins
        else:
            return "1-0"  # White wins

    # Check for stalemate
    if is_stalemate(game_state):
        return "1/2-1/2"

    # Check for 50-move rule
    if is_fifty_move_rule(game_state):
        return "1/2-1/2"

    # Check for threefold repetition
    if is_threefold_repetition(game_state):
        return "1/2-1/2"

    # Check for insufficient material
    if is_insufficient_material(game_state.board):
        return "1/2-1/2"

    # Game is ongoing
    return None
