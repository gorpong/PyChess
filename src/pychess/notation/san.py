"""Standard Algebraic Notation (SAN) parsing and generation.

SAN is the standard notation for recording chess moves. Examples:
- e4 (pawn to e4)
- Nf3 (knight to f3)
- Bxc6 (bishop captures on c6)
- O-O (kingside castling)
- O-O-O (queenside castling)
- e8=Q (pawn promotes to queen)
- Qxf7# (queen captures f7, checkmate)
"""

import re
from typing import Optional

from pychess.model.board import Board
from pychess.model.game_state import GameState
from pychess.model.piece import Piece, Color
from pychess.model.square import Square
from pychess.rules.move import Move
from pychess.rules.validator import get_legal_moves, is_in_check, is_move_legal
from pychess.rules.game_logic import is_checkmate


# Piece letter mapping
PIECE_LETTERS = {
    Piece.KING: "K",
    Piece.QUEEN: "Q",
    Piece.ROOK: "R",
    Piece.BISHOP: "B",
    Piece.KNIGHT: "N",
    Piece.PAWN: "",
}

LETTER_TO_PIECE = {
    "K": Piece.KING,
    "Q": Piece.QUEEN,
    "R": Piece.ROOK,
    "B": Piece.BISHOP,
    "N": Piece.KNIGHT,
}


def move_to_san(game_state: GameState, move: Move) -> str:
    """Convert a move to Standard Algebraic Notation.

    Args:
        game_state: Current game state before the move
        move: The move to convert

    Returns:
        SAN string representation of the move
    """
    # Handle castling
    if move.is_castling:
        if move.to_square.file == "g":
            san = "O-O"
        else:
            san = "O-O-O"
        return _add_check_suffix(game_state, move, san)

    board = game_state.board
    piece_info = board.get(move.from_square)
    if piece_info is None:
        raise ValueError(f"No piece at {move.from_square}")

    piece_type, color = piece_info

    # Build SAN string
    san_parts = []

    # Piece letter (empty for pawns)
    piece_letter = PIECE_LETTERS[piece_type]

    if piece_type == Piece.PAWN:
        # Pawn moves
        if move.is_capture or move.is_en_passant:
            # Pawn captures include source file
            san_parts.append(move.from_square.file)
            san_parts.append("x")
        san_parts.append(move.to_square.to_algebraic())

        # Promotion
        if move.promotion:
            san_parts.append("=")
            san_parts.append(PIECE_LETTERS[move.promotion])
    else:
        # Non-pawn pieces
        san_parts.append(piece_letter)

        # Disambiguation
        disambiguation = _get_disambiguation(game_state, move, piece_type)
        san_parts.append(disambiguation)

        # Capture
        if move.is_capture:
            san_parts.append("x")

        # Destination square
        san_parts.append(move.to_square.to_algebraic())

    san = "".join(san_parts)
    return _add_check_suffix(game_state, move, san)


def _get_disambiguation(game_state: GameState, move: Move, piece_type: Piece) -> str:
    """Get disambiguation string for a piece move.

    When multiple pieces of the same type can move to the same square,
    we need to disambiguate by file, rank, or both.

    Args:
        game_state: Current game state
        move: The move being made
        piece_type: Type of piece moving

    Returns:
        Disambiguation string (empty if not needed, or file/rank/both)
    """
    to_square = move.to_square
    from_square = move.from_square

    # Get all legal moves to find other pieces that can reach the same square
    all_legal_moves = get_legal_moves(game_state)

    # Find other pieces of same type that can reach the target
    candidates = []
    for legal_move in all_legal_moves:
        if legal_move.to_square != to_square:
            continue
        if legal_move.from_square == from_square:
            continue

        # Check if it's the same piece type
        piece_info = game_state.board.get(legal_move.from_square)
        if piece_info and piece_info[0] == piece_type:
            candidates.append(legal_move.from_square)

    if not candidates:
        return ""

    # Need disambiguation - check if file or rank alone would uniquely identify
    same_file = any(sq.file == from_square.file for sq in candidates)
    same_rank = any(sq.rank == from_square.rank for sq in candidates)

    if not same_file:
        # File alone is unique
        return from_square.file
    elif not same_rank:
        # Rank alone is unique (file is not unique)
        return str(from_square.rank)
    else:
        # Need both file and rank
        return from_square.to_algebraic()


def _add_check_suffix(game_state: GameState, move: Move, san: str) -> str:
    """Add check (+) or checkmate (#) suffix if applicable.

    Args:
        game_state: Current game state before the move
        move: The move being made
        san: SAN string without check suffix

    Returns:
        SAN string with check/mate suffix if applicable
    """
    # Apply the move to get the resulting state
    new_state = _apply_move(game_state, move)

    # Check if opponent is in check
    opponent_color = new_state.active_color
    if is_in_check(new_state.board, opponent_color):
        # Check if it's checkmate
        if is_checkmate(new_state):
            return san + "#"
        else:
            return san + "+"

    return san


def _apply_move(game_state: GameState, move: Move) -> GameState:
    """Apply a move to get the resulting game state.

    Args:
        game_state: Current game state
        move: Move to apply

    Returns:
        New game state after the move
    """
    board = game_state.board
    from_square = move.from_square
    to_square = move.to_square

    piece_info = board.get(from_square)
    if piece_info is None:
        return game_state

    piece_type, color = piece_info

    # Remove piece from source
    new_board = board.remove(from_square)

    # Handle en passant capture
    if move.is_en_passant:
        captured_pawn_rank = from_square.rank
        captured_pawn_square = Square(file=to_square.file, rank=captured_pawn_rank)
        new_board = new_board.remove(captured_pawn_square)

    # Handle castling (move the rook)
    if move.is_castling:
        rank = from_square.rank
        if to_square.file == 'g':
            rook_from = Square(file='h', rank=rank)
            rook_to = Square(file='f', rank=rank)
        else:
            rook_from = Square(file='a', rank=rank)
            rook_to = Square(file='d', rank=rank)

        rook_info = new_board.get(rook_from)
        if rook_info:
            new_board = new_board.remove(rook_from)
            new_board = new_board.set(rook_to, rook_info[0], rook_info[1])

    # Place piece on destination (handle promotion)
    if move.promotion:
        new_board = new_board.set(to_square, move.promotion, color)
    else:
        new_board = new_board.set(to_square, piece_type, color)

    # Switch turn
    new_turn = color.opposite()

    return game_state.with_board(new_board).with_turn(new_turn)


def san_to_move(game_state: GameState, san: str) -> Move:
    """Parse a SAN string to a Move object.

    Args:
        game_state: Current game state
        san: SAN string to parse

    Returns:
        Move object representing the SAN

    Raises:
        ValueError: If SAN is invalid or ambiguous
    """
    # Strip check/mate annotations
    san = san.rstrip("+#")

    # Handle castling
    if san == "O-O" or san == "0-0":
        return _parse_castling(game_state, kingside=True)
    if san == "O-O-O" or san == "0-0-0":
        return _parse_castling(game_state, kingside=False)

    # Parse regular move
    return _parse_regular_move(game_state, san)


def _parse_castling(game_state: GameState, kingside: bool) -> Move:
    """Parse a castling move.

    Args:
        game_state: Current game state
        kingside: True for kingside, False for queenside

    Returns:
        Move object for castling
    """
    color = game_state.active_color
    rank = 1 if color == Color.WHITE else 8

    from_square = Square(file="e", rank=rank)
    to_file = "g" if kingside else "c"
    to_square = Square(file=to_file, rank=rank)

    return Move(
        from_square=from_square,
        to_square=to_square,
        is_castling=True
    )


def _parse_regular_move(game_state: GameState, san: str) -> Move:
    """Parse a regular (non-castling) move.

    Args:
        game_state: Current game state
        san: SAN string (without check annotations)

    Returns:
        Move object

    Raises:
        ValueError: If SAN is invalid or ambiguous
    """
    # Regex pattern for SAN
    # Groups: piece?, disambiguation?, capture?, destination, promotion?
    pattern = r'^([KQRBN])?([a-h])?([1-8])?(x)?([a-h][1-8])(=[QRBN])?$'
    match = re.match(pattern, san)

    if not match:
        raise ValueError(f"Invalid SAN: {san}")

    piece_letter = match.group(1)
    disambig_file = match.group(2)
    disambig_rank = match.group(3)
    is_capture = match.group(4) is not None
    destination = match.group(5)
    promotion_str = match.group(6)

    # Determine piece type
    if piece_letter:
        piece_type = LETTER_TO_PIECE[piece_letter]
    else:
        piece_type = Piece.PAWN

    # Parse destination
    to_square = Square.from_algebraic(destination)

    # Parse promotion
    promotion = None
    if promotion_str:
        promotion = LETTER_TO_PIECE[promotion_str[1]]  # Skip the '='

    # Find the source square
    from_square = _find_source_square(
        game_state, piece_type, to_square, disambig_file, disambig_rank, is_capture
    )

    if from_square is None:
        raise ValueError(f"No legal move for SAN: {san}")

    # Determine if it's en passant
    is_en_passant = (
        piece_type == Piece.PAWN
        and is_capture
        and game_state.board.get(to_square) is None
        and game_state.en_passant_square == to_square
    )

    # Check if target has a piece (for capture flag)
    target_piece = game_state.board.get(to_square)
    actual_capture = target_piece is not None or is_en_passant

    return Move(
        from_square=from_square,
        to_square=to_square,
        promotion=promotion,
        is_capture=actual_capture,
        is_en_passant=is_en_passant
    )


def _find_source_square(
    game_state: GameState,
    piece_type: Piece,
    to_square: Square,
    disambig_file: Optional[str],
    disambig_rank: Optional[str],
    is_capture: bool
) -> Optional[Square]:
    """Find the source square for a move.

    Args:
        game_state: Current game state
        piece_type: Type of piece moving
        to_square: Destination square
        disambig_file: Disambiguation file (if any)
        disambig_rank: Disambiguation rank (if any)
        is_capture: Whether it's a capture

    Returns:
        Source square, or None if not found
    """
    # Get all legal moves and filter by piece type and destination
    all_legal_moves = get_legal_moves(game_state)
    board = game_state.board

    candidates = set()  # Use set to deduplicate (multiple promotion moves from same square)

    for move in all_legal_moves:
        # Check destination
        if move.to_square != to_square:
            continue

        # Check piece type
        piece_info = board.get(move.from_square)
        if piece_info is None or piece_info[0] != piece_type:
            continue

        from_square = move.from_square

        # Apply disambiguation filter
        if disambig_file and from_square.file != disambig_file:
            continue
        if disambig_rank and from_square.rank != int(disambig_rank):
            continue

        candidates.add(from_square)

    if len(candidates) == 0:
        return None
    if len(candidates) == 1:
        return list(candidates)[0]

    # Ambiguous - multiple pieces can reach the target
    raise ValueError(f"Ambiguous move: multiple pieces can reach {to_square}")
