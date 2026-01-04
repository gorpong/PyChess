"""Chess position evaluation functions for AI."""

from pychess.model.game_state import GameState
from pychess.model.piece import Piece, Color
from pychess.rules.move import Move
from pychess.notation.pgn import _apply_san_move
from pychess.notation.san import move_to_san


# Standard piece values
PIECE_VALUES = {
    Piece.PAWN: 100,
    Piece.KNIGHT: 320,
    Piece.BISHOP: 330,
    Piece.ROOK: 500,
    Piece.QUEEN: 900,
    Piece.KING: 0,  # King is invaluable
}


def evaluate_material_balance(game_state: GameState, color: Color) -> int:
    """Evaluate material balance for a given color.

    Args:
        game_state: Current game state
        color: Color to evaluate for

    Returns:
        Material score (positive is better for color)
    """
    board = game_state.board
    score = 0

    for square_str in [f"{f}{r}" for r in range(1, 9) for f in 'abcdefgh']:
        from pychess.model.square import Square
        square = Square.from_algebraic(square_str)
        piece_info = board.get(square)

        if piece_info:
            piece_type, piece_color = piece_info
            value = PIECE_VALUES.get(piece_type, 0)

            if piece_color == color:
                score += value
            else:
                score -= value

    return score


def evaluate_move_material(game_state: GameState, move: Move) -> int:
    """Evaluate material gain/loss from a move.

    Args:
        game_state: Current game state
        move: Move to evaluate

    Returns:
        Material score (higher is better)
    """
    board = game_state.board
    color = game_state.active_color

    # Start with current material balance
    current_score = evaluate_material_balance(game_state, color)

    # Check if move captures a piece
    captured_piece = board.get(move.to_square)
    capture_value = 0

    if captured_piece:
        captured_type, _ = captured_piece
        capture_value = PIECE_VALUES.get(captured_type, 0)

    # Check for en passant capture
    if move.is_en_passant:
        capture_value = PIECE_VALUES[Piece.PAWN]

    # Promotion bonus
    promotion_value = 0
    if move.promotion:
        # Gain queen value minus pawn value
        promotion_value = PIECE_VALUES[move.promotion] - PIECE_VALUES[Piece.PAWN]

    return current_score + capture_value + promotion_value


def evaluate_position(game_state: GameState, move: Move) -> int:
    """Evaluate position after a move (material + basic positional).

    Args:
        game_state: Current game state
        move: Move to evaluate

    Returns:
        Position score (higher is better)
    """
    # Apply the move temporarily
    try:
        san = move_to_san(game_state, move)
        new_state = _apply_san_move(game_state, san, move)
        color = game_state.active_color

        # Material evaluation
        material_score = evaluate_material_balance(new_state, color)

        # Basic positional bonuses
        positional_score = _evaluate_position_bonus(new_state, color)

        return material_score + positional_score

    except Exception:
        # If evaluation fails, fall back to material only
        return evaluate_move_material(game_state, move)


def _evaluate_position_bonus(game_state: GameState, color: Color) -> int:
    """Calculate basic positional bonuses.

    Args:
        game_state: Game state
        color: Color to evaluate for

    Returns:
        Positional bonus score
    """
    from pychess.model.square import Square
    board = game_state.board
    bonus = 0

    for square_str in [f"{f}{r}" for r in range(1, 9) for f in 'abcdefgh']:
        square = Square.from_algebraic(square_str)
        piece_info = board.get(square)

        if piece_info:
            piece_type, piece_color = piece_info

            if piece_color == color:
                # Center control bonus for pieces
                file_idx = ord(square.file) - ord('a')
                rank_idx = square.rank - 1

                # Center squares (d4, d5, e4, e5) are valuable
                distance_from_center = abs(3.5 - file_idx) + abs(3.5 - rank_idx)
                center_bonus = max(0, 10 - int(distance_from_center * 2))

                # Knights and bishops especially benefit from center
                if piece_type in (Piece.KNIGHT, Piece.BISHOP):
                    bonus += center_bonus

                # Pawns: bonus for advancement
                if piece_type == Piece.PAWN:
                    if piece_color == Color.WHITE:
                        bonus += rank_idx * 5  # More bonus for advanced pawns
                    else:
                        bonus += (7 - rank_idx) * 5

    return bonus
