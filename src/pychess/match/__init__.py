"""Networked-multiplayer match domain.

Domain model for a two-player networked chess match: invite codes, seat
ownership, move authorization. Independent of HTTP or WebSocket transport;
see `docs/NETWORK_MULTIPLAYER_DESIGN.md` for the broader architecture.
"""

from pychess.match.errors import (
    IllegalMatchMove,
    InviteCodeExhausted,
    MatchError,
    MatchFull,
    MatchNotActive,
    MatchNotFound,
    NotInMatch,
    NotYourTurn,
    PromotionPending,
)
from pychess.match.models import (
    Match,
    MatchStatus,
    Player,
    SeatChoice,
)
from pychess.match.repository import InMemoryMatchRepository, MatchRepository
from pychess.match.service import MatchService
from pychess.match.sqlalchemy_repository import SqlAlchemyMatchRepository

__all__ = [
    "IllegalMatchMove",
    "InMemoryMatchRepository",
    "InviteCodeExhausted",
    "Match",
    "MatchError",
    "MatchFull",
    "MatchNotActive",
    "MatchNotFound",
    "MatchRepository",
    "MatchService",
    "MatchStatus",
    "NotInMatch",
    "NotYourTurn",
    "Player",
    "PromotionPending",
    "SeatChoice",
    "SqlAlchemyMatchRepository",
]
