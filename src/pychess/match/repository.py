"""Persistence abstraction for `Match` aggregates.

`MatchRepository` is a Protocol so the service can sit on top of either
the process-local in-memory implementation below or the SQLAlchemy-backed
one used by the web server. The two implementations must be behaviourally
indistinguishable to `MatchService`.
"""

from typing import Optional, Protocol

from pychess.match.models import Match


class MatchRepository(Protocol):
    """Persistence contract for `Match` aggregates.

    Implementations are responsible for identity: two lookups with the same
    id must return the same live object so service mutations are visible
    across callers. The in-memory repo satisfies this trivially; the ORM
    repo relies on SQLAlchemy's identity map.
    """

    def save(self, match: Match) -> None:
        """Insert a new match or persist mutations to an existing one."""
        ...

    def get(self, match_id: str) -> Optional[Match]:
        """Fetch by match id; None if absent."""
        ...

    def get_by_invite(self, invite_code: str) -> Optional[Match]:
        """Fetch by invite code; None if absent."""
        ...

    def invite_code_exists(self, invite_code: str) -> bool:
        """Used by the service's collision-retry loop during creation."""
        ...

    def delete(self, match_id: str) -> None:
        """Remove a match. Idempotent: a missing id is a no-op."""
        ...


class InMemoryMatchRepository:
    """Process-local repository. Dict-of-dicts; safe only within one process."""

    def __init__(self) -> None:
        self._by_id: dict[str, Match] = {}
        self._by_invite: dict[str, Match] = {}

    def save(self, match: Match) -> None:
        self._by_id[match.match_id] = match
        self._by_invite[match.invite_code] = match

    def get(self, match_id: str) -> Optional[Match]:
        return self._by_id.get(match_id)

    def get_by_invite(self, invite_code: str) -> Optional[Match]:
        return self._by_invite.get(invite_code)

    def invite_code_exists(self, invite_code: str) -> bool:
        return invite_code in self._by_invite

    def delete(self, match_id: str) -> None:
        match = self._by_id.pop(match_id, None)
        if match is not None:
            self._by_invite.pop(match.invite_code, None)

    def all_matches(self) -> list[Match]:
        """Test-only helper: enumerate every match in the repo."""
        return list(self._by_id.values())
