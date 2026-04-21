"""JSON (de)serialization for the mutable state stored on a `Match`.

The ORM repository persists `GameState` and the optional pending-promotion
`Move` as JSON text columns. Keeping the encoding here (rather than in a
SQLAlchemy TypeDecorator) makes round-trip behaviour easy to unit-test in
isolation and keeps the ORM module focused on schema.

The match package deliberately serializes through `GameState`'s public data
API so persistence is not coupled to the model package's private tuple fields
or the board's internal piece map.
"""

from __future__ import annotations

import json
from typing import Optional

from pychess.model.game_state import GameState
from pychess.model.piece import Piece
from pychess.model.square import Square
from pychess.rules.move import Move

_SCHEMA_VERSION = 1


def game_state_to_json(state: GameState) -> str:
    payload = {"v": _SCHEMA_VERSION, **state.to_public_data()}
    return json.dumps(payload, separators=(",", ":"))


def game_state_from_json(raw: str) -> GameState:
    data = json.loads(raw)
    version = data.get("v", 1)
    if version != _SCHEMA_VERSION:
        raise ValueError(
            f"Unknown match serialization version: {version} (expected {_SCHEMA_VERSION})"
        )
    return GameState.from_public_data({k: v for k, v in data.items() if k != "v"})


def move_to_json(move: Optional[Move]) -> Optional[str]:
    if move is None:
        return None
    return json.dumps(
        {
            "from": _sq(move.from_square),
            "to": _sq(move.to_square),
            "promotion": move.promotion.name if move.promotion else None,
            "is_castling": move.is_castling,
            "is_en_passant": move.is_en_passant,
            "is_capture": move.is_capture,
        },
        separators=(",", ":"),
    )


def move_from_json(raw: Optional[str]) -> Optional[Move]:
    if raw is None:
        return None
    data = json.loads(raw)
    return Move(
        from_square=Square.from_algebraic(data["from"]),
        to_square=Square.from_algebraic(data["to"]),
        promotion=Piece[data["promotion"]] if data.get("promotion") else None,
        is_castling=data.get("is_castling", False),
        is_en_passant=data.get("is_en_passant", False),
        is_capture=data.get("is_capture", False),
    )

# -------------------- internals --------------------


def _sq(square: Square) -> str:
    return f"{square.file}{square.rank}"
