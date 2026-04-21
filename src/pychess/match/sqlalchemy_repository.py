"""SQLAlchemy-backed implementation of `MatchRepository`.

Each method opens a short-lived session, performs its work, commits, and
closes. This detached-object style matches the service's usage pattern
(fetch → mutate on the Python object → save) without relying on the
session's identity map across call boundaries, which keeps behaviour
symmetric with the in-memory implementation.

An engine factory is provided for the common case of building a
SQLite-backed repo from a path or URL; tests typically use an in-memory
`sqlite://` URL.
"""

from __future__ import annotations

from typing import Optional

from sqlalchemy import Engine, create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from pychess.match.models import Match
from pychess.match.orm import Base, MatchORM


class SqlAlchemyMatchRepository:
    def __init__(self, engine: Engine) -> None:
        self._engine = engine
        self._session_factory = sessionmaker(bind=engine, expire_on_commit=False)

    @classmethod
    def from_url(cls, url: str, *, create_schema: bool = False) -> "SqlAlchemyMatchRepository":
        """Build a repo from a SQLAlchemy URL.

        `create_schema=True` is convenient for tests and first-boot in dev;
        production deployments should apply migrations via Alembic instead.
        """
        engine = create_engine(url, future=True)
        if create_schema:
            Base.metadata.create_all(engine)
        return cls(engine)

    # -------------------- MatchRepository protocol --------------------

    def save(self, match: Match) -> None:
        with self._session_factory.begin() as session:
            existing = session.get(MatchORM, match.match_id)
            if existing is None:
                session.add(MatchORM.from_domain(match))
            else:
                existing.apply_domain(match)

    def get(self, match_id: str) -> Optional[Match]:
        with self._session_factory() as session:
            row = session.get(MatchORM, match_id)
            return row.to_domain() if row is not None else None

    def get_by_invite(self, invite_code: str) -> Optional[Match]:
        with self._session_factory() as session:
            row = session.scalar(
                select(MatchORM).where(MatchORM.invite_code == invite_code)
            )
            return row.to_domain() if row is not None else None

    def invite_code_exists(self, invite_code: str) -> bool:
        with self._session_factory() as session:
            return session.scalar(
                select(MatchORM.match_id).where(MatchORM.invite_code == invite_code)
            ) is not None

    def delete(self, match_id: str) -> None:
        with self._session_factory.begin() as session:
            row = session.get(MatchORM, match_id)
            if row is not None:
                session.delete(row)

    # -------------------- helpers --------------------

    @property
    def engine(self) -> Engine:
        return self._engine


def make_engine(url: str) -> Engine:
    """Shared helper to build the app-wide engine. Keeps URL handling in one place."""
    return create_engine(url, future=True)
