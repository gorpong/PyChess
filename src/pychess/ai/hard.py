"""Hard AI evaluation using piece-square tables.

Piece-square tables assign positional bonuses/penalties based on where
pieces are located on the board. Values are from White's perspective
and are mirrored for Black.
"""

from pychess.model.game_state import GameState
from pychess.model.piece import Piece, Color
from pychess.model.square import Square
from pychess.rules.move import Move


# Standard piece values (centipawns)
PIECE_VALUES = {
    Piece.PAWN: 100,
    Piece.KNIGHT: 320,
    Piece.BISHOP: 330,
    Piece.ROOK: 500,
    Piece.QUEEN: 900,
    Piece.KING: 0,  # King is invaluable
}


# Piece-square tables are 8x8 arrays indexed [rank][file] from White's perspective.
# Rank 0 = rank 1 (White's back rank), Rank 7 = rank 8 (Black's back rank).
# File 0 = a-file, File 7 = h-file.
# Values are in centipawns.

# Pawn table: encourage center control and advancement
# Penalize staying on starting squares, bonus for advancement
PAWN_TABLE = [
    [  0,   0,   0,   0,   0,   0,   0,   0],  # rank 1 (impossible for pawns)
    [  5,  10,  10, -20, -20,  10,  10,   5],  # rank 2 (starting rank)
    [  5,  -5, -10,   0,   0, -10,  -5,   5],  # rank 3
    [  0,   0,   0,  20,  20,   0,   0,   0],  # rank 4 (center control)
    [  5,   5,  10,  25,  25,  10,   5,   5],  # rank 5
    [ 10,  10,  20,  30,  30,  20,  10,  10],  # rank 6
    [ 50,  50,  50,  50,  50,  50,  50,  50],  # rank 7 (about to promote)
    [  0,   0,   0,   0,   0,   0,   0,   0],  # rank 8 (impossible for pawns)
]

# Knight table: strongly prefer center, penalize edges and corners
KNIGHT_TABLE = [
    [-50, -40, -30, -30, -30, -30, -40, -50],  # rank 1
    [-40, -20,   0,   5,   5,   0, -20, -40],  # rank 2
    [-30,   5,  10,  15,  15,  10,   5, -30],  # rank 3
    [-30,   0,  15,  20,  20,  15,   0, -30],  # rank 4
    [-30,   5,  15,  20,  20,  15,   5, -30],  # rank 5
    [-30,   0,  10,  15,  15,  10,   0, -30],  # rank 6
    [-40, -20,   0,   0,   0,   0, -20, -40],  # rank 7
    [-50, -40, -30, -30, -30, -30, -40, -50],  # rank 8
]

# Bishop table: prefer long diagonals, avoid corners
BISHOP_TABLE = [
    [-20, -10, -10, -10, -10, -10, -10, -20],  # rank 1
    [-10,   5,   0,   0,   0,   0,   5, -10],  # rank 2
    [-10,  10,  10,  10,  10,  10,  10, -10],  # rank 3
    [-10,   0,  10,  10,  10,  10,   0, -10],  # rank 4
    [-10,   5,   5,  10,  10,   5,   5, -10],  # rank 5
    [-10,   0,   5,  10,  10,   5,   0, -10],  # rank 6
    [-10,   0,   0,   0,   0,   0,   0, -10],  # rank 7
    [-20, -10, -10, -10, -10, -10, -10, -20],  # rank 8
]

# Rook table: prefer open files (c,d,e,f), 7th rank is strong
ROOK_TABLE = [
    [  0,   0,   0,   5,   5,   0,   0,   0],  # rank 1
    [ -5,   0,   0,   0,   0,   0,   0,  -5],  # rank 2
    [ -5,   0,   0,   0,   0,   0,   0,  -5],  # rank 3
    [ -5,   0,   0,   0,   0,   0,   0,  -5],  # rank 4
    [ -5,   0,   0,   0,   0,   0,   0,  -5],  # rank 5
    [ -5,   0,   0,   0,   0,   0,   0,  -5],  # rank 6
    [  5,  10,  10,  10,  10,  10,  10,   5],  # rank 7 (7th rank bonus)
    [  0,   0,   0,   0,   0,   0,   0,   0],  # rank 8
]

# Queen table: slight center preference, avoid early development to edges
QUEEN_TABLE = [
    [-20, -10, -10,  -5,  -5, -10, -10, -20],  # rank 1
    [-10,   0,   5,   0,   0,   0,   0, -10],  # rank 2
    [-10,   5,   5,   5,   5,   5,   0, -10],  # rank 3
    [  0,   0,   5,   5,   5,   5,   0,  -5],  # rank 4
    [ -5,   0,   5,   5,   5,   5,   0,  -5],  # rank 5
    [-10,   0,   5,   5,   5,   5,   0, -10],  # rank 6
    [-10,   0,   0,   0,   0,   0,   0, -10],  # rank 7
    [-20, -10, -10,  -5,  -5, -10, -10, -20],  # rank 8
]

# King middlegame table: prefer castled positions (corners), avoid center
KING_MIDDLEGAME_TABLE = [
    [ 20,  30,  10,   0,   0,  10,  30,  20],  # rank 1 (castled positions)
    [ 20,  20,   0,   0,   0,   0,  20,  20],  # rank 2
    [-10, -20, -20, -20, -20, -20, -20, -10],  # rank 3
    [-20, -30, -30, -40, -40, -30, -30, -20],  # rank 4
    [-30, -40, -40, -50, -50, -40, -40, -30],  # rank 5
    [-30, -40, -40, -50, -50, -40, -40, -30],  # rank 6
    [-30, -40, -40, -50, -50, -40, -40, -30],  # rank 7
    [-30, -40, -40, -50, -50, -40, -40, -30],  # rank 8
]

# King endgame table: prefer center for active king
KING_ENDGAME_TABLE = [
    [-50, -30, -30, -30, -30, -30, -30, -50],  # rank 1
    [-30, -30,   0,   0,   0,   0, -30, -30],  # rank 2
    [-30, -10,  20,  30,  30,  20, -10, -30],  # rank 3
    [-30, -10,  30,  40,  40,  30, -10, -30],  # rank 4
    [-30, -10,  30,  40,  40,  30, -10, -30],  # rank 5
    [-30, -10,  20,  30,  30,  20, -10, -30],  # rank 6
    [-30, -20, -10,   0,   0, -10, -20, -30],  # rank 7
    [-50, -40, -30, -20, -20, -30, -40, -50],  # rank 8
]


def get_piece_square_table(piece: Piece, is_endgame: bool = False) -> list[list[int]]:
    """Get the piece-square table for a given piece type.
    
    Args:
        piece: The piece type
        is_endgame: Whether to use endgame tables (affects king only)
        
    Returns:
        8x8 table of positional values
    """
    if piece == Piece.PAWN:
        return PAWN_TABLE
    elif piece == Piece.KNIGHT:
        return KNIGHT_TABLE
    elif piece == Piece.BISHOP:
        return BISHOP_TABLE
    elif piece == Piece.ROOK:
        return ROOK_TABLE
    elif piece == Piece.QUEEN:
        return QUEEN_TABLE
    elif piece == Piece.KING:
        return KING_ENDGAME_TABLE if is_endgame else KING_MIDDLEGAME_TABLE
    else:
        # Should never happen
        return [[0] * 8 for _ in range(8)]


def get_piece_square_value(piece: Piece, square: Square, color: Color, 
                           is_endgame: bool = False) -> int:
    """Get the piece-square table value for a piece at a given square.
    
    Args:
        piece: The piece type
        square: The square the piece is on
        color: The color of the piece
        is_endgame: Whether to use endgame evaluation
        
    Returns:
        Positional value in centipawns (positive is good for the piece's color)
    """
    table = get_piece_square_table(piece, is_endgame)
    
    file_idx = square.file_index  # 0-7 (a-h)
    rank_idx = square.rank_index  # 0-7 (rank 1-8)
    
    # For Black, mirror the table vertically (rank 1 becomes rank 8, etc.)
    if color == Color.BLACK:
        rank_idx = 7 - rank_idx
    
    return table[rank_idx][file_idx]


def is_endgame(game_state: GameState) -> bool:
    """Determine if the position is an endgame.
    
    Endgame is defined as:
    - Both sides have no queens, OR
    - Every side which has a queen has at most one other piece (not counting pawns)
    
    Args:
        game_state: Current game state
        
    Returns:
        True if position is an endgame
    """
    board = game_state.board
    
    white_queens = 0
    black_queens = 0
    white_minor_major = 0  # knights, bishops, rooks
    black_minor_major = 0
    
    for square_str in [f"{f}{r}" for r in range(1, 9) for f in 'abcdefgh']:
        square = Square.from_algebraic(square_str)
        piece_info = board.get(square)
        
        if piece_info:
            piece_type, piece_color = piece_info
            
            if piece_type == Piece.QUEEN:
                if piece_color == Color.WHITE:
                    white_queens += 1
                else:
                    black_queens += 1
            elif piece_type in (Piece.KNIGHT, Piece.BISHOP, Piece.ROOK):
                if piece_color == Color.WHITE:
                    white_minor_major += 1
                else:
                    black_minor_major += 1
    
    # No queens at all = endgame
    if white_queens == 0 and black_queens == 0:
        return True
    
    # If a side has a queen, they must have at most 1 other piece for endgame
    if white_queens > 0 and white_minor_major > 1:
        return False
    if black_queens > 0 and black_minor_major > 1:
        return False
    
    return True


def evaluate_piece_square_tables(game_state: GameState, color: Color) -> int:
    """Evaluate position using piece-square tables.
    
    Args:
        game_state: Current game state
        color: Color to evaluate for (positive score = good for this color)
        
    Returns:
        Positional score in centipawns
    """
    board = game_state.board
    endgame = is_endgame(game_state)
    score = 0
    
    for square_str in [f"{f}{r}" for r in range(1, 9) for f in 'abcdefgh']:
        square = Square.from_algebraic(square_str)
        piece_info = board.get(square)
        
        if piece_info:
            piece_type, piece_color = piece_info
            
            # Get piece-square value
            ps_value = get_piece_square_value(piece_type, square, piece_color, endgame)
            
            if piece_color == color:
                score += ps_value
            else:
                score -= ps_value
    
    return score


def evaluate_material(game_state: GameState, color: Color) -> int:
    """Evaluate material balance for a given color.
    
    Args:
        game_state: Current game state
        color: Color to evaluate for
        
    Returns:
        Material score in centipawns (positive = good for color)
    """
    board = game_state.board
    score = 0
    
    for square_str in [f"{f}{r}" for r in range(1, 9) for f in 'abcdefgh']:
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


def evaluate_position_hard(game_state: GameState, color: Color) -> int:
    """Full evaluation combining material and piece-square tables.
    
    Args:
        game_state: Current game state
        color: Color to evaluate for
        
    Returns:
        Total evaluation score in centipawns
    """
    material = evaluate_material(game_state, color)
    positional = evaluate_piece_square_tables(game_state, color)
    
    return material + positional


def score_move_for_ordering(game_state: GameState, move: Move) -> int:
    """Score a move for move ordering purposes.
    
    Higher scores = moves to search first.
    Order: promotions > captures (MVV-LVA) > other moves
    
    Args:
        game_state: Current game state
        move: Move to score
        
    Returns:
        Ordering score (higher = search first)
    """
    score = 0
    board = game_state.board
    
    # Promotion: very high priority
    if move.promotion:
        score += 10000 + PIECE_VALUES.get(move.promotion, 0)
    
    # Captures: use MVV-LVA (Most Valuable Victim - Least Valuable Attacker)
    captured_piece = board.get(move.to_square)
    if captured_piece:
        victim_value = PIECE_VALUES.get(captured_piece[0], 0)
        attacker = board.get(move.from_square)
        attacker_value = PIECE_VALUES.get(attacker[0], 0) if attacker else 0
        # MVV-LVA: prefer capturing high value with low value
        score += 1000 + (victim_value * 10) - attacker_value
    
    # En passant capture
    if move.is_en_passant:
        score += 1000 + (PIECE_VALUES[Piece.PAWN] * 10) - PIECE_VALUES[Piece.PAWN]
    
    # Castling: modest bonus
    if move.is_castling:
        score += 500
    
    return score


def order_moves(game_state: GameState, moves: list[Move]) -> list[Move]:
    """Order moves for better search efficiency.
    
    Moves are sorted by score (highest first).
    
    Args:
        game_state: Current game state
        moves: List of legal moves
        
    Returns:
        Sorted list of moves
    """
    scored_moves = [(score_move_for_ordering(game_state, move), move) for move in moves]
    scored_moves.sort(key=lambda x: x[0], reverse=True)
    return [move for _, move in scored_moves]


def select_best_move(game_state: GameState, legal_moves: list[Move]) -> Move:
    """Select the best move using piece-square table evaluation.
    
    Evaluates all positions after each move and picks the best one.
    Uses move ordering to break ties consistently.
    
    Args:
        game_state: Current game state
        legal_moves: List of legal moves to choose from
        
    Returns:
        The best move found
    """
    from pychess.notation.san import move_to_san
    from pychess.notation.pgn import _apply_san_move
    
    if not legal_moves:
        raise ValueError("No legal moves available")
    
    color = game_state.active_color
    
    # Order moves for consistent tie-breaking
    ordered_moves = order_moves(game_state, legal_moves)
    
    best_move = ordered_moves[0]
    best_score = float('-inf')
    
    for move in ordered_moves:
        try:
            # Apply move temporarily
            san = move_to_san(game_state, move)
            new_state = _apply_san_move(game_state, san, move)
            
            # Evaluate resulting position (from moving player's perspective)
            score = evaluate_position_hard(new_state, color)
            
            if score > best_score:
                best_score = score
                best_move = move
                
        except Exception:
            # If evaluation fails, skip this move
            continue
    
    return best_move
