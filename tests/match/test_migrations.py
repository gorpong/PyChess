"""End-to-end Alembic smoke tests.

Verifies that running `alembic upgrade head` on a fresh SQLite file
produces a schema the `SqlAlchemyMatchRepository` can immediately use.
This is the guarantee that `apply_migrations` + the committed revisions
give us a working DB — without relying on `Base.metadata.create_all`.
"""

from __future__ import annotations

import pytest
from sqlalchemy import create_engine, inspect

from pychess.match import MatchService, SeatChoice, SqlAlchemyMatchRepository
from pychess.match.migrations import apply_migrations, auto_migrate_if_enabled


class TestAlembicUpgrade:
    def test_upgrade_creates_matches_table(self, tmp_path):
        db_path = tmp_path / "fresh.db"
        url = f"sqlite:///{db_path}"

        apply_migrations(url)

        engine = create_engine(url, future=True)
        inspector = inspect(engine)
        assert "matches" in inspector.get_table_names()
        columns = {c["name"] for c in inspector.get_columns("matches")}
        assert {"match_id", "invite_code", "status", "game_state_json"} <= columns

    def test_upgrade_is_idempotent(self, tmp_path):
        url = f"sqlite:///{tmp_path / 'fresh.db'}"

        apply_migrations(url)
        apply_migrations(url)  # second call must not fail

        engine = create_engine(url, future=True)
        assert "matches" in inspect(engine).get_table_names()

    def test_service_works_against_alembic_schema(self, tmp_path):
        """A repo pointed at an Alembic-migrated file should behave normally."""
        url = f"sqlite:///{tmp_path / 'migrated.db'}"
        apply_migrations(url)

        repo = SqlAlchemyMatchRepository.from_url(url, create_schema=False)
        service = MatchService(repo)
        match = service.create_match("alice", SeatChoice.WHITE)
        service.join(match.invite_code, "bob")

        reloaded = service.get_match(match.match_id)
        assert reloaded.white_player_id == "alice"
        assert reloaded.black_player_id == "bob"


class TestAutoMigrate:
    def test_no_op_when_env_unset(self, tmp_path, monkeypatch):
        monkeypatch.delenv("PYCHESS_AUTO_MIGRATE", raising=False)
        url = f"sqlite:///{tmp_path / 'gated.db'}"

        auto_migrate_if_enabled(url)

        # DB file isn't touched — no schema, no file (SQLite creates lazily).
        assert not (tmp_path / "gated.db").exists()

    @pytest.mark.parametrize("value", ["1", "true", "yes", "on", "TRUE"])
    def test_runs_when_env_set(self, tmp_path, monkeypatch, value):
        monkeypatch.setenv("PYCHESS_AUTO_MIGRATE", value)
        url = f"sqlite:///{tmp_path / 'gated.db'}"

        auto_migrate_if_enabled(url)

        engine = create_engine(url, future=True)
        assert "matches" in inspect(engine).get_table_names()
