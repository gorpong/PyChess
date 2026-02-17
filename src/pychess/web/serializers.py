"""Serialization utilities for converting game state to web-friendly formats."""

from typing import Optional

from pychess.model.board import Board
from pychess.model.game_state import GameState
from pychess.model.piece import Color, Piece
from pychess.model.square import Square
from pychess.rules.validator import is_in_check


# Piece code mapping for template rendering
PIECE_CODES = {
    (Piece.KING, Color.WHITE): 'wK',
    (Piece.QUEEN, Color.WHITE): 'wQ',
    (Piece.ROOK, Color.WHITE): 'wR',
    (Piece.BISHOP, Color.WHITE): 'wB',
    (Piece.KNIGHT, Color.WHITE): 'wN',
    (Piece.PAWN, Color.WHITE): 'wP',
    (Piece.KING, Color.BLACK): 'bK',
    (Piece.QUEEN, Color.BLACK): 'bQ',
    (Piece.ROOK, Color.BLACK): 'bR',
    (Piece.BISHOP, Color.BLACK): 'bB',
    (Piece.KNIGHT, Color.BLACK): 'bN',
    (Piece.PAWN, Color.BLACK): 'bP',
}


def game_state_to_dict(state: GameState) -> dict:
    """Convert GameState to JSON-serializable dict.
    
    Args:
        state: The game state to serialize.
        
    Returns:
        Dictionary with game state information suitable for JSON serialization.
        Keys:
        - turn: 'white' or 'black'
        - fullmove_number: int
        - halfmove_clock: int
        - castling: dict with white/black containing kingside/queenside bools
        - en_passant: square string (e.g., 'e3') or None
        - move_history: list of SAN strings
        - is_check: bool indicating if current player is in check
    """
    return {
        'turn': 'white' if state.turn == Color.WHITE else 'black',
        'fullmove_number': state.fullmove_number,
        'halfmove_clock': state.halfmove_clock,
        'castling': {
            'white': {
                'kingside': state.castling.white_kingside,
                'queenside': state.castling.white_queenside,
            },
            'black': {
                'kingside': state.castling.black_kingside,
                'queenside': state.castling.black_queenside,
            },
        },
        'en_passant': (
            state.en_passant_square.to_algebraic() 
            if state.en_passant_square else None
        ),
        'move_history': state.move_history,
        'is_check': is_in_check(state.board, state.turn),
    }


def square_to_piece_code(board: Board, square: Square) -> Optional[str]:
    """Get the piece code for a square.
    
    Args:
        board: The board to query.
        square: The square to check.
        
    Returns:
        Piece code string (e.g., 'wK', 'bP') or None if square is empty.
    """
    piece_info = board.get(square)
    if piece_info is None:
        return None
    piece, color = piece_info
    return PIECE_CODES.get((piece, color))


def is_light_square(square: Square) -> bool:
    """Determine if a square is a light square.
    
    Args:
        square: The square to check.
        
    Returns:
        True if the square is light-colored, False if dark.
    """
    file_idx = ord(square.file) - ord('a')
    rank_idx = square.rank - 1
    return (file_idx + rank_idx) % 2 == 1


def board_to_template_data(
    board: Board,
    selected: Optional[Square] = None,
    legal_moves: Optional[set[Square]] = None,
    last_move: Optional[tuple[Square, Square]] = None,
) -> list[list[dict]]:
    """Convert board to 8x8 list of square data for templates.
    
    The board is returned from White's perspective (rank 8 at top, rank 1 at bottom).
    
    Args:
        board: The board to convert.
        selected: Currently selected square, if any.
        legal_moves: Set of legal destination squares to highlight.
        last_move: Tuple of (from_square, to_square) for last move highlighting.
        
    Returns:
        8x8 list of lists, where each inner dict contains:
        - square: algebraic notation (e.g., 'e4')
        - piece: piece code (e.g., 'wK', 'bP') or None
        - is_light: bool indicating light or dark square
        - is_selected: bool indicating if this square is selected
        - is_legal_move: bool indicating if this is a legal destination
        - is_last_move: bool indicating if this square was part of last move
        - has_piece: bool indicating if square has a piece (for CSS styling)
    """
    if legal_moves is None:
        legal_moves = set()
    
    last_move_squares = set()
    if last_move is not None:
        last_move_squares.add(last_move[0])
        last_move_squares.add(last_move[1])
    
    rows = []
    
    # Iterate from rank 8 down to rank 1 (top to bottom from White's view)
    for rank in range(8, 0, -1):
        row = []
        for file in 'abcdefgh':
            square = Square(file=file, rank=rank)
            piece_code = square_to_piece_code(board, square)
            
            row.append({
                'square': square.to_algebraic(),
                'piece': piece_code,
                'is_light': is_light_square(square),
                'is_selected': square == selected,
                'is_legal_move': square in legal_moves,
                'is_last_move': square in last_move_squares,
                'has_piece': piece_code is not None,
            })
        rows.append(row)
    
    return rows
