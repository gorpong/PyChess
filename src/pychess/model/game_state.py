"""Game state representation for chess."""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional

from pychess.model.piece import Color
from pychess.model.square import Square
from pychess.model.board import Board


@dataclass(frozen=True)
class CastlingRights:
    """Immutable castling rights for both players."""

    white_kingside: bool
    white_queenside: bool
    black_kingside: bool
    black_queenside: bool

    @classmethod
    def initial(cls) -> CastlingRights:
        """Create initial castling rights (all available)."""
        return cls(
            white_kingside=True,
            white_queenside=True,
            black_kingside=True,
            black_queenside=True,
        )

    def can_castle(self, color: Color, kingside: bool) -> bool:
        """Check if castling is still allowed for given color and side."""
        if color == Color.WHITE:
            return self.white_kingside if kingside else self.white_queenside
        return self.black_kingside if kingside else self.black_queenside

    def revoke(self, color: Color, kingside: bool) -> CastlingRights:
        """Return new rights with specified castling revoked."""
        return CastlingRights(
            white_kingside=(
                False if color == Color.WHITE and kingside else self.white_kingside
            ),
            white_queenside=(
                False if color == Color.WHITE and not kingside else self.white_queenside
            ),
            black_kingside=(
                False if color == Color.BLACK and kingside else self.black_kingside
            ),
            black_queenside=(
                False if color == Color.BLACK and not kingside else self.black_queenside
            ),
        )

    def revoke_all(self, color: Color) -> CastlingRights:
        """Return new rights with all castling revoked for a color."""
        if color == Color.WHITE:
            return CastlingRights(
                white_kingside=False,
                white_queenside=False,
                black_kingside=self.black_kingside,
                black_queenside=self.black_queenside,
            )
        return CastlingRights(
            white_kingside=self.white_kingside,
            white_queenside=self.white_queenside,
            black_kingside=False,
            black_queenside=False,
        )


@dataclass(frozen=True)
class GameState:
    """Complete immutable game state.

    Contains all information needed to continue a game:
    - Board position
    - Whose turn it is
    - Castling rights
    - En passant target square
    - Half-move clock (for 50-move rule)
    - Full-move number
    - Move history (SAN notation)
    - Position history (hashes for threefold repetition)
    """

    board: Board
    turn: Color
    castling: CastlingRights
    en_passant_square: Optional[Square]
    halfmove_clock: int
    fullmove_number: int
    _move_history: tuple[str, ...] = field(default_factory=tuple)
    _position_history: tuple[int, ...] = field(default_factory=tuple)

    @property
    def move_history(self) -> list[str]:
        """Return move history as a list."""
        return list(self._move_history)

    @property
    def position_history(self) -> list[int]:
        """Return position history as a list of hashes."""
        return list(self._position_history)

    @property
    def position_hash(self) -> int:
        """Compute a hash of the current position for repetition detection.

        The hash includes: board position, turn, castling rights, en passant square.
        It does NOT include: halfmove clock, fullmove number, or move history.
        """
        # Build a tuple of all position-relevant state
        # Board pieces as sorted list of (square, piece, color)
        pieces = []
        for square, (piece, color) in sorted(
            self.board._pieces.items(),
            key=lambda x: (x[0].file, x[0].rank)
        ):
            pieces.append((square.file, square.rank, piece.name, color.name))

        state_tuple = (
            tuple(pieces),
            self.turn.name,
            self.castling.white_kingside,
            self.castling.white_queenside,
            self.castling.black_kingside,
            self.castling.black_queenside,
            self.en_passant_square.to_algebraic() if self.en_passant_square else None,
        )
        return hash(state_tuple)

    @classmethod
    def initial(cls) -> GameState:
        """Create initial game state."""
        return cls(
            board=Board.initial(),
            turn=Color.WHITE,
            castling=CastlingRights.initial(),
            en_passant_square=None,
            halfmove_clock=0,
            fullmove_number=1,
            _move_history=(),
        )

    @property
    def is_white_turn(self) -> bool:
        """Return True if it's white's turn."""
        return self.turn == Color.WHITE

    @property
    def active_color(self) -> Color:
        """Return the color to move."""
        return self.turn

    @property
    def opponent_color(self) -> Color:
        """Return the color not to move."""
        return self.turn.opposite()

    def with_board(self, board: Board) -> GameState:
        """Return new state with different board."""
        return GameState(
            board=board,
            turn=self.turn,
            castling=self.castling,
            en_passant_square=self.en_passant_square,
            halfmove_clock=self.halfmove_clock,
            fullmove_number=self.fullmove_number,
            _move_history=self._move_history,
            _position_history=self._position_history,
        )

    def with_turn(self, turn: Color) -> GameState:
        """Return new state with different turn."""
        return GameState(
            board=self.board,
            turn=turn,
            castling=self.castling,
            en_passant_square=self.en_passant_square,
            halfmove_clock=self.halfmove_clock,
            fullmove_number=self.fullmove_number,
            _move_history=self._move_history,
            _position_history=self._position_history,
        )

    def with_castling(self, castling: CastlingRights) -> GameState:
        """Return new state with different castling rights."""
        return GameState(
            board=self.board,
            turn=self.turn,
            castling=castling,
            en_passant_square=self.en_passant_square,
            halfmove_clock=self.halfmove_clock,
            fullmove_number=self.fullmove_number,
            _move_history=self._move_history,
            _position_history=self._position_history,
        )

    def with_en_passant(self, square: Optional[Square]) -> GameState:
        """Return new state with different en passant square."""
        return GameState(
            board=self.board,
            turn=self.turn,
            castling=self.castling,
            en_passant_square=square,
            halfmove_clock=self.halfmove_clock,
            fullmove_number=self.fullmove_number,
            _move_history=self._move_history,
            _position_history=self._position_history,
        )

    def with_halfmove_clock(self, clock: int) -> GameState:
        """Return new state with different halfmove clock."""
        return GameState(
            board=self.board,
            turn=self.turn,
            castling=self.castling,
            en_passant_square=self.en_passant_square,
            halfmove_clock=clock,
            fullmove_number=self.fullmove_number,
            _move_history=self._move_history,
            _position_history=self._position_history,
        )

    def with_fullmove_number(self, number: int) -> GameState:
        """Return new state with different fullmove number."""
        return GameState(
            board=self.board,
            turn=self.turn,
            castling=self.castling,
            en_passant_square=self.en_passant_square,
            halfmove_clock=self.halfmove_clock,
            fullmove_number=number,
            _move_history=self._move_history,
            _position_history=self._position_history,
        )

    def with_move_added(self, san_move: str) -> GameState:
        """Return new state with move added to history."""
        return GameState(
            board=self.board,
            turn=self.turn,
            castling=self.castling,
            en_passant_square=self.en_passant_square,
            halfmove_clock=self.halfmove_clock,
            fullmove_number=self.fullmove_number,
            _move_history=self._move_history + (san_move,),
            _position_history=self._position_history,
        )

    def with_position_hash_added(self, position_hash: int) -> GameState:
        """Return new state with position hash added to history."""
        return GameState(
            board=self.board,
            turn=self.turn,
            castling=self.castling,
            en_passant_square=self.en_passant_square,
            halfmove_clock=self.halfmove_clock,
            fullmove_number=self.fullmove_number,
            _move_history=self._move_history,
            _position_history=self._position_history + (position_hash,),
        )
