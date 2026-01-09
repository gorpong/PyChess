"""PGN (Portable Game Notation) serialization and parsing.

PGN is a standard format for recording chess games. Example:
[Event "Casual Game"]
[Site "Terminal"]
[Date "2024.01.15"]
[White "Player1"]
[Black "Computer"]
[Result "1-0"]

1. e4 e5 2. Nf3 Nc6 3. Bb5 a6 1-0
"""

import re
from datetime import date
from typing import Optional
from dataclasses import dataclass, field

from pychess.model.game_state import GameState
from pychess.model.piece import Color
from pychess.notation.san import move_to_san, san_to_move


@dataclass
class PGNHeaders:
    """PGN game headers (tags)."""

    event: str = "Casual Game"
    site: str = "Terminal"
    date: str = ""  # YYYY.MM.DD format
    white: str = "White"
    black: str = "Black"
    result: str = "*"  # 1-0, 0-1, 1/2-1/2, or * (ongoing)
    time_control: str = "-"
    total_time_seconds: int = 0
    game_mode: str = "Multiplayer"  # "Multiplayer", "Easy", "Medium", "Hard"

    def __post_init__(self):
        if not self.date:
            today = date.today()
            self.date = today.strftime("%Y.%m.%d")


def game_to_pgn(
    game_state: GameState,
    headers: Optional[PGNHeaders] = None,
    comments: Optional[dict[int, str]] = None
) -> str:
    """Serialize a game state to PGN format.

    Args:
        game_state: The game state to serialize
        headers: PGN headers (defaults will be used if not provided)
        comments: Optional dictionary mapping move number (1-indexed) to comment

    Returns:
        PGN string representation
    """
    if headers is None:
        headers = PGNHeaders()

    if comments is None:
        comments = {}

    lines = []

    # Headers
    lines.append(f'[Event "{headers.event}"]')
    lines.append(f'[Site "{headers.site}"]')
    lines.append(f'[Date "{headers.date}"]')
    lines.append(f'[White "{headers.white}"]')
    lines.append(f'[Black "{headers.black}"]')
    lines.append(f'[Result "{headers.result}"]')
    lines.append(f'[TimeControl "{headers.time_control}"]')
    lines.append(f'[TotalTimeSeconds "{headers.total_time_seconds}"]')
    lines.append(f'[GameMode "{headers.game_mode}"]')
    lines.append("")  # Blank line after headers

    # Move text
    moves = game_state.move_history
    move_text_parts = []

    for i, san_move in enumerate(moves):
        move_num = (i // 2) + 1
        is_white_move = (i % 2 == 0)

        if is_white_move:
            move_text_parts.append(f"{move_num}.")

        move_text_parts.append(san_move)

        # Add comment if present (1-indexed move number)
        if (i + 1) in comments:
            move_text_parts.append(f"{{{comments[i + 1]}}}")

    # Add result
    if headers.result != "*":
        move_text_parts.append(headers.result)

    # Format move text with line wrapping
    move_text = " ".join(move_text_parts)
    lines.append(move_text)

    return "\n".join(lines)


def pgn_to_game(pgn_string: str) -> tuple[GameState, PGNHeaders]:
    """Parse a PGN string and replay moves to restore game state.

    Args:
        pgn_string: PGN formatted string

    Returns:
        Tuple of (GameState after all moves, PGNHeaders)

    Raises:
        ValueError: If PGN is malformed or contains invalid moves
    """
    headers = _parse_headers(pgn_string)
    move_text = _extract_move_text(pgn_string)
    san_moves = _parse_moves(move_text)

    # Replay moves from initial position
    state = GameState.initial()

    for san in san_moves:
        try:
            move = san_to_move(state, san)
            # Apply the move
            state = _apply_san_move(state, san, move)
        except ValueError as e:
            raise ValueError(f"Invalid move '{san}': {e}") from e

    return state, headers


def _parse_headers(pgn_string: str) -> PGNHeaders:
    """Parse PGN headers from string.

    Args:
        pgn_string: Full PGN string

    Returns:
        PGNHeaders object
    """
    headers = PGNHeaders()

    # Pattern for [Tag "Value"]
    pattern = r'\[(\w+)\s+"([^"]*)"\]'

    for match in re.finditer(pattern, pgn_string):
        tag = match.group(1).lower()
        value = match.group(2)

        if tag == "event":
            headers.event = value
        elif tag == "site":
            headers.site = value
        elif tag == "date":
            headers.date = value
        elif tag == "white":
            headers.white = value
        elif tag == "black":
            headers.black = value
        elif tag == "result":
            headers.result = value
        elif tag == "timecontrol":
            headers.time_control = value
        elif tag == "totaltimeseconds":
            try:
                headers.total_time_seconds = int(value)
            except ValueError:
                pass
        elif tag == "gamemode":
            headers.game_mode = value

    return headers


def _extract_move_text(pgn_string: str) -> str:
    """Extract move text from PGN (everything after headers).

    Args:
        pgn_string: Full PGN string

    Returns:
        Move text portion
    """
    # Find the last header line
    lines = pgn_string.strip().split("\n")
    move_text_lines = []
    in_headers = True

    for line in lines:
        line = line.strip()
        if in_headers:
            if line.startswith("[") and line.endswith("]"):
                continue
            elif line == "":
                in_headers = False
            else:
                in_headers = False
                move_text_lines.append(line)
        else:
            move_text_lines.append(line)

    return " ".join(move_text_lines)


def _parse_moves(move_text: str) -> list[str]:
    """Parse move text into list of SAN moves.

    Args:
        move_text: Move text portion of PGN

    Returns:
        List of SAN move strings
    """
    moves = []

    # Remove comments {text}
    move_text = re.sub(r'\{[^}]*\}', '', move_text)

    # Remove variations (text)
    move_text = re.sub(r'\([^)]*\)', '', move_text)

    # Remove NAGs like $1, $2, etc.
    move_text = re.sub(r'\$\d+', '', move_text)

    # Remove result at end
    move_text = re.sub(r'(1-0|0-1|1/2-1/2|\*)\s*$', '', move_text)

    # Split into tokens
    tokens = move_text.split()

    for token in tokens:
        token = token.strip()
        if not token:
            continue

        # Skip move numbers (1. or 1...)
        if re.match(r'^\d+\.+$', token):
            continue

        # Skip dots alone
        if token == ".":
            continue

        # This should be a SAN move
        moves.append(token)

    return moves


def _apply_san_move(state: GameState, san: str, move) -> GameState:
    """Apply a move to the game state and update all fields.

    Args:
        state: Current game state
        san: SAN notation of the move
        move: Parsed Move object

    Returns:
        New game state after the move
    """
    from pychess.model.piece import Piece
    from pychess.model.square import Square

    board = state.board
    from_square = move.from_square
    to_square = move.to_square

    piece_info = board.get(from_square)
    if piece_info is None:
        return state

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

    # Update castling rights
    new_castling = state.castling
    if piece_type == Piece.KING:
        new_castling = new_castling.revoke_all(color)
    elif piece_type == Piece.ROOK:
        if from_square.file == 'a':
            new_castling = new_castling.revoke(color, kingside=False)
        elif from_square.file == 'h':
            new_castling = new_castling.revoke(color, kingside=True)

    # Update en passant square
    new_en_passant = None
    if piece_type == Piece.PAWN and abs(to_square.rank - from_square.rank) == 2:
        # Double pawn push - set en passant square
        ep_rank = (from_square.rank + to_square.rank) // 2
        new_en_passant = Square(file=from_square.file, rank=ep_rank)

    # Update halfmove clock
    is_capture = move.is_capture or board.get(to_square) is not None
    if piece_type == Piece.PAWN or is_capture:
        new_halfmove = 0
    else:
        new_halfmove = state.halfmove_clock + 1

    # Update fullmove number
    new_fullmove = state.fullmove_number
    if color == Color.BLACK:
        new_fullmove += 1

    # Switch turn
    new_turn = color.opposite()

    # Add move to history and position hash
    new_state = (
        state
        .with_board(new_board)
        .with_turn(new_turn)
        .with_castling(new_castling)
        .with_en_passant(new_en_passant)
        .with_halfmove_clock(new_halfmove)
        .with_fullmove_number(new_fullmove)
        .with_move_added(san)
    )

    # Add position hash for repetition tracking
    new_state = new_state.with_position_hash_added(new_state.position_hash)

    return new_state
