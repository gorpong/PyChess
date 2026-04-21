"""SQLAlchemy ORM mapping for the match domain.

We keep the ORM layer intentionally small: one table, one mapped class,
and conversion helpers to and from the `Match` domain object. The service
layer never sees a `MatchORM`; the repository is the translation seam.

Schema notes:
    - `match_id` is the primary key; UUID-shaped but we store opaque text.
    - `invite_code` is uniquely indexed so collision detection is cheap.
    - `status` is a string (not a DB enum) so migrating the `MatchStatus`
      Python enum doesn't require a DDL change.
    - `game_state_json` / `pending_promotion_json` hold the serialized
      mutable state via `pychess.match.serialization`.
"""

from __future__ import annotations

from sqlalchemy import Float, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from pychess.match.models import Match, MatchStatus
from pychess.match.serialization import (
    game_state_from_json,
    game_state_to_json,
    move_from_json,
    move_to_json,
)


class Base(DeclarativeBase):
    """Declarative base for all ORM models in this project."""


class MatchORM(Base):
    __tablename__ = "matches"

    match_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    invite_code: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    status: Mapped[str] = mapped_column(String(16), index=True)
    white_player_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    black_player_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    result: Mapped[str | None] = mapped_column(String(8), nullable=True)
    game_state_json: Mapped[str] = mapped_column(Text)
    pending_promotion_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[float] = mapped_column(Float)
    updated_at: Mapped[float] = mapped_column(Float, index=True)

    @classmethod
    def from_domain(cls, match: Match) -> "MatchORM":
        return cls(
            match_id=match.match_id,
            invite_code=match.invite_code,
            status=match.status.value,
            white_player_id=match.white_player_id,
            black_player_id=match.black_player_id,
            result=match.result,
            game_state_json=game_state_to_json(match.game_state),
            pending_promotion_json=move_to_json(match.pending_promotion),
            created_at=match.created_at,
            updated_at=match.updated_at,
        )

    def apply_domain(self, match: Match) -> None:
        """Update this row in place from a domain `Match`. Used on save-update."""
        self.invite_code = match.invite_code
        self.status = match.status.value
        self.white_player_id = match.white_player_id
        self.black_player_id = match.black_player_id
        self.result = match.result
        self.game_state_json = game_state_to_json(match.game_state)
        self.pending_promotion_json = move_to_json(match.pending_promotion)
        self.created_at = match.created_at
        self.updated_at = match.updated_at

    def to_domain(self) -> Match:
        return Match(
            match_id=self.match_id,
            invite_code=self.invite_code,
            game_state=game_state_from_json(self.game_state_json),
            status=MatchStatus(self.status),
            white_player_id=self.white_player_id,
            black_player_id=self.black_player_id,
            result=self.result,
            pending_promotion=move_from_json(self.pending_promotion_json),
            created_at=self.created_at,
            updated_at=self.updated_at,
        )
