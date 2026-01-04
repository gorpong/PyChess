"""Move validation and check detection.

This module filters pseudo-legal moves to only legal moves by checking
if moves leave the king in check.
"""

from typing import Optional

from pychess.model.board import Board
from pychess.model.game_state import GameState
from pychess.model.piece import Piece, Color
from pychess.model.square import Square
from pychess.rules.move import Move
from pychess.rules.move_generator import MoveGenerator


def is_square_attacked(board: Board, square: Square, by_color: Color) -> bool:
    """Check if a square is attacked by any piece of the given color.

    Args:
        board: Current board position
        square: Square to check for attacks
        by_color: Color of the attacking side

    Returns:
        True if the square is attacked by any piece of by_color
    """
    # Check all pieces of by_color to see if any attack the target square
    pieces = board.get_pieces_by_color(by_color)

    for piece_square, piece_type in pieces:
        if _piece_attacks_square(board, piece_square, piece_type, by_color, square):
            return True

    return False


def _piece_attacks_square(
    board: Board,
    from_square: Square,
    piece_type: Piece,
    color: Color,
    target_square: Square
) -> bool:
    """Check if a specific piece attacks a target square.

    For sliding pieces, this checks if the target is on the attack path,
    even if blocked by a friendly piece.

    Args:
        board: Current board position
        from_square: Square the piece is on
        piece_type: Type of the piece
        color: Color of the piece
        target_square: Target square to check

    Returns:
        True if the piece attacks the target square
    """
    # For pawns, we need special handling since they attack differently than they move
    if piece_type == Piece.PAWN:
        return _pawn_attacks_square(from_square, color, target_square)

    # For knights and kings, use move generation (they can't be blocked)
    if piece_type == Piece.KNIGHT:
        moves = MoveGenerator.generate_knight_moves(board, from_square, color)
        return any(move.to_square == target_square for move in moves)

    if piece_type == Piece.KING:
        moves = MoveGenerator.generate_king_moves(board, from_square, color, castling_rights=None)
        return any(move.to_square == target_square for move in moves)

    # For sliding pieces (bishop, rook, queen), check if target is on attack path
    # We need to check this differently because friendly pieces block moves but still "attack" through them
    if piece_type == Piece.BISHOP:
        return _sliding_piece_attacks(from_square, target_square, diagonal=True, orthogonal=False, board=board, color=color)
    elif piece_type == Piece.ROOK:
        return _sliding_piece_attacks(from_square, target_square, diagonal=False, orthogonal=True, board=board, color=color)
    elif piece_type == Piece.QUEEN:
        return _sliding_piece_attacks(from_square, target_square, diagonal=True, orthogonal=True, board=board, color=color)

    return False


def _sliding_piece_attacks(
    from_square: Square,
    target_square: Square,
    diagonal: bool,
    orthogonal: bool,
    board: Board,
    color: Color
) -> bool:
    """Check if a sliding piece can attack a target square.

    Args:
        from_square: Square the sliding piece is on
        target_square: Target square to check
        diagonal: Whether piece moves diagonally
        orthogonal: Whether piece moves orthogonally
        board: Current board
        color: Color of the attacking piece

    Returns:
        True if the piece can attack the target
    """
    file_diff = target_square.file_index - from_square.file_index
    rank_diff = target_square.rank - from_square.rank

    # Check if target is on a valid line of attack
    is_diagonal = abs(file_diff) == abs(rank_diff) and file_diff != 0
    is_orthogonal = (file_diff == 0 and rank_diff != 0) or (rank_diff == 0 and file_diff != 0)

    if diagonal and is_diagonal:
        # Check path is not blocked by opponent piece (friendly pieces don't block "attacks")
        return _path_not_blocked_by_opponent(from_square, target_square, board, color)
    elif orthogonal and is_orthogonal:
        # Check path is not blocked by opponent piece
        return _path_not_blocked_by_opponent(from_square, target_square, board, color)

    return False


def _path_not_blocked_by_opponent(from_square: Square, to_square: Square, board: Board, color: Color) -> bool:
    """Check if path between two squares is not blocked by any piece.

    Any piece (friendly or opponent) blocks sliding piece attacks beyond that square.

    Args:
        from_square: Starting square
        to_square: Target square
        board: Current board
        color: Color of the attacking piece

    Returns:
        True if path is clear up to (but not including) the target square
    """
    file_diff = to_square.file_index - from_square.file_index
    rank_diff = to_square.rank - from_square.rank

    # Determine direction
    file_step = 0 if file_diff == 0 else (1 if file_diff > 0 else -1)
    rank_step = 0 if rank_diff == 0 else (1 if rank_diff > 0 else -1)

    # Check each square along the path (not including start or end)
    current_file = from_square.file_index + file_step
    current_rank = from_square.rank + rank_step

    while current_file != to_square.file_index or current_rank != to_square.rank:
        current_square = Square(file=chr(ord('a') + current_file), rank=current_rank)
        piece = board.get(current_square)

        # Any piece in the way blocks the attack path
        if piece is not None:
            return False

        current_file += file_step
        current_rank += rank_step

    return True


def _pawn_attacks_square(from_square: Square, color: Color, target_square: Square) -> bool:
    """Check if a pawn attacks a target square.

    Pawns attack diagonally forward, different from their normal move pattern.

    Args:
        from_square: Square the pawn is on
        color: Color of the pawn
        target_square: Target square to check

    Returns:
        True if the pawn attacks the target square
    """
    file_idx = from_square.file_index
    rank = from_square.rank

    # Direction: white attacks up (+1), black attacks down (-1)
    direction = 1 if color == Color.WHITE else -1
    attack_rank = rank + direction

    # Check if target is on the attack rank
    if target_square.rank != attack_rank:
        return False

    # Check if target is diagonally adjacent (one file away)
    target_file_idx = target_square.file_index
    return abs(target_file_idx - file_idx) == 1


def is_in_check(board: Board, color: Color) -> bool:
    """Check if the king of the given color is in check.

    Args:
        board: Current board position
        color: Color of the king to check

    Returns:
        True if the king is in check
    """
    # Find the king
    king_squares = board.find_pieces(Piece.KING, color)

    if not king_squares:
        # No king found (shouldn't happen in valid position)
        return False

    king_square = king_squares[0]

    # Check if the king's square is attacked by the opponent
    opponent_color = color.opposite()
    return is_square_attacked(board, king_square, opponent_color)


def is_move_legal(game_state: GameState, move: Move) -> bool:
    """Check if a move is legal (doesn't leave own king in check).

    This includes special validation for:
    - King cannot move into check
    - Cannot move if it leaves king in check (pinned pieces)
    - Castling: cannot castle out of, through, or into check
    - En passant: cannot expose king to check

    Args:
        game_state: Current game state
        move: Move to validate

    Returns:
        True if the move is legal
    """
    board = game_state.board
    active_color = game_state.active_color

    # Special handling for castling
    if move.is_castling:
        return _is_castling_legal(game_state, move)

    # Make the move on a new board
    new_board = _apply_move_to_board(board, move)

    # Check if our king is in check after the move
    return not is_in_check(new_board, active_color)


def _is_castling_legal(game_state: GameState, move: Move) -> bool:
    """Check if a castling move is legal.

    Castling is illegal if:
    - King is currently in check
    - King would pass through check
    - King would end in check

    Args:
        game_state: Current game state
        move: Castling move to validate

    Returns:
        True if castling is legal
    """
    board = game_state.board
    active_color = game_state.active_color
    opponent_color = active_color.opposite()

    # Cannot castle out of check
    if is_in_check(board, active_color):
        return False

    from_square = move.from_square
    to_square = move.to_square

    # Determine if kingside or queenside
    is_kingside = to_square.file > from_square.file

    # Check squares the king passes through
    if active_color == Color.WHITE:
        if is_kingside:
            # Kingside: e1 -> f1 -> g1
            squares_to_check = [
                Square.from_algebraic("e1"),
                Square.from_algebraic("f1"),
                Square.from_algebraic("g1")
            ]
        else:
            # Queenside: e1 -> d1 -> c1
            squares_to_check = [
                Square.from_algebraic("e1"),
                Square.from_algebraic("d1"),
                Square.from_algebraic("c1")
            ]
    else:
        if is_kingside:
            # Kingside: e8 -> f8 -> g8
            squares_to_check = [
                Square.from_algebraic("e8"),
                Square.from_algebraic("f8"),
                Square.from_algebraic("g8")
            ]
        else:
            # Queenside: e8 -> d8 -> c8
            squares_to_check = [
                Square.from_algebraic("e8"),
                Square.from_algebraic("d8"),
                Square.from_algebraic("c8")
            ]

    # King cannot castle through or into check
    for square in squares_to_check:
        if is_square_attacked(board, square, opponent_color):
            return False

    return True


def _apply_move_to_board(board: Board, move: Move) -> Board:
    """Apply a move to a board and return the new board.

    Handles special moves like en passant and castling.

    Args:
        board: Current board
        move: Move to apply

    Returns:
        New board with move applied
    """
    from_square = move.from_square
    to_square = move.to_square

    # Get the moving piece
    piece_info = board.get(from_square)
    if piece_info is None:
        # No piece to move (shouldn't happen for valid moves)
        return board

    piece_type, color = piece_info

    # Remove piece from source square
    new_board = board.remove(from_square)

    # Handle en passant capture
    if move.is_en_passant:
        # Remove the captured pawn (on the same rank as the moving pawn)
        captured_pawn_rank = from_square.rank
        captured_pawn_square = Square(file=to_square.file, rank=captured_pawn_rank)
        new_board = new_board.remove(captured_pawn_square)

    # Handle castling (move the rook)
    if move.is_castling:
        rank = from_square.rank
        if to_square.file == 'g':
            # Kingside castling: move h-rook to f
            rook_from = Square(file='h', rank=rank)
            rook_to = Square(file='f', rank=rank)
        else:
            # Queenside castling: move a-rook to d
            rook_from = Square(file='a', rank=rank)
            rook_to = Square(file='d', rank=rank)

        rook_info = new_board.get(rook_from)
        if rook_info is not None:
            new_board = new_board.remove(rook_from)
            new_board = new_board.set(rook_to, rook_info[0], rook_info[1])

    # Place piece on destination square (handle promotion)
    if move.promotion:
        new_board = new_board.set(to_square, move.promotion, color)
    else:
        new_board = new_board.set(to_square, piece_type, color)

    return new_board


def get_legal_moves(game_state: GameState) -> list[Move]:
    """Get all legal moves for the current player.

    Args:
        game_state: Current game state

    Returns:
        List of all legal moves for the active player
    """
    board = game_state.board
    active_color = game_state.active_color
    legal_moves = []

    # Get all pieces of the active color
    pieces = board.get_pieces_by_color(active_color)

    for from_square, piece_type in pieces:
        # Generate pseudo-legal moves for this piece
        if piece_type == Piece.PAWN:
            pseudo_moves = MoveGenerator.generate_pawn_moves(
                board, from_square, active_color, game_state.en_passant_square
            )
        elif piece_type == Piece.KNIGHT:
            pseudo_moves = MoveGenerator.generate_knight_moves(board, from_square, active_color)
        elif piece_type == Piece.BISHOP:
            pseudo_moves = MoveGenerator.generate_bishop_moves(board, from_square, active_color)
        elif piece_type == Piece.ROOK:
            pseudo_moves = MoveGenerator.generate_rook_moves(board, from_square, active_color)
        elif piece_type == Piece.QUEEN:
            pseudo_moves = MoveGenerator.generate_queen_moves(board, from_square, active_color)
        elif piece_type == Piece.KING:
            pseudo_moves = MoveGenerator.generate_king_moves(
                board, from_square, active_color, game_state.castling
            )
        else:
            pseudo_moves = []

        # Filter to only legal moves
        for move in pseudo_moves:
            if is_move_legal(game_state, move):
                legal_moves.append(move)

    return legal_moves
