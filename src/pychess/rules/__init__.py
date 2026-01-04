"""Rules engine - move generation and validation."""

from pychess.rules.move import Move
from pychess.rules.move_generator import MoveGenerator
from pychess.rules.validator import (
    is_square_attacked,
    is_in_check,
    is_move_legal,
    get_legal_moves,
)
from pychess.rules.game_logic import (
    is_checkmate,
    is_stalemate,
    is_fifty_move_rule,
    is_threefold_repetition,
    is_insufficient_material,
    get_game_result,
)

__all__ = [
    "Move",
    "MoveGenerator",
    "is_square_attacked",
    "is_in_check",
    "is_move_legal",
    "get_legal_moves",
    "is_checkmate",
    "is_stalemate",
    "is_fifty_move_rule",
    "is_threefold_repetition",
    "is_insufficient_material",
    "get_game_result",
]
