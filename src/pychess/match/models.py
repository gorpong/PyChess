"""Value objects and aggregate for the match domain."""

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

from pychess.model.game_state import GameState
from pychess.model.piece import Color
from pychess.rules.move import Move


class MatchStatus(str, Enum):
    """Lifecycle of a networked match.

    Values are strings (not auto ints) so database round-trips are
    human-readable and resilient to enum reordering.
    """

    WAITING = "waiting"    # Created; one seat open, no game moves yet.
    ACTIVE = "active"      # Both seats filled; moves can be submitted.
    FINISHED = "finished"  # Game ended by checkmate, stalemate, or draw rule.
    ABANDONED = "abandoned"  # A player resigned (or — future — timed out).


class SeatChoice(str, Enum):
    """Creator's seat preference at match creation time."""

    WHITE = "white"
    BLACK = "black"
    RANDOM = "random"

    def to_color(self) -> Optional[Color]:
        """Return the concrete `Color` for WHITE/BLACK; None for RANDOM.

        The service resolves RANDOM itself so tests can inject a deterministic
        RNG without every call site doing it.
        """
        if self is SeatChoice.WHITE:
            return Color.WHITE
        if self is SeatChoice.BLACK:
            return Color.BLACK
        return None


@dataclass(frozen=True)
class Player:
    """Identity of a participant. Created once per browser, UUID in a cookie."""

    player_id: str
    display_name: Optional[str] = None


@dataclass
class Match:
    """A two-player chess match.

    Mutable by design: service methods evolve the same instance in place so
    the ORM repository can persist with standard flush semantics. The shape
    mirrors `WebGameSession` where it can, so existing web-layer serializers
    carry over with minimal change.
    """

    match_id: str
    invite_code: str
    game_state: GameState
    status: MatchStatus = MatchStatus.WAITING
    white_player_id: Optional[str] = None
    black_player_id: Optional[str] = None
    result: Optional[str] = None   # '1-0' | '0-1' | '1/2-1/2' when FINISHED/ABANDONED
    pending_promotion: Optional[Move] = None
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)

    # -- seat inspection helpers --

    def seat_of(self, player_id: str) -> Optional[Color]:
        """Return the color `player_id` is seated on, or None if not in match."""
        if self.white_player_id == player_id:
            return Color.WHITE
        if self.black_player_id == player_id:
            return Color.BLACK
        return None

    def occupant(self, seat: Color) -> Optional[str]:
        """Return the player_id on `seat`, or None if vacant."""
        return self.white_player_id if seat == Color.WHITE else self.black_player_id

    def is_full(self) -> bool:
        return self.white_player_id is not None and self.black_player_id is not None

    def open_seat(self) -> Optional[Color]:
        """The single vacant seat, or None if both are filled."""
        if self.white_player_id is None and self.black_player_id is not None:
            return Color.WHITE
        if self.black_player_id is None and self.white_player_id is not None:
            return Color.BLACK
        return None

    def assign_seat(self, seat: Color, player_id: str) -> None:
        """Place `player_id` on `seat`. Caller is responsible for vacancy check."""
        if seat == Color.WHITE:
            self.white_player_id = player_id
        else:
            self.black_player_id = player_id

    def touch(self) -> None:
        """Bump `updated_at` to now; called after any state change."""
        self.updated_at = time.time()
