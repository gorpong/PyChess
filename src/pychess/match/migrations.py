"""Programmatic Alembic upgrade helper.

The web entry point calls `apply_migrations(url)` at startup (gated by
`PYCHESS_AUTO_MIGRATE=1`) so fresh Docker containers come up with the
schema in place. Out-of-band deploys can still run `alembic upgrade head`
from the command line; both paths share the same `env.py` config.
"""

from __future__ import annotations

import os
from pathlib import Path

from alembic import command
from alembic.config import Config

# alembic.ini and migrations/ live at the repo root for source checkouts.
# When PyChess is installed from a wheel (e.g. in a Docker image) they are
# not inside the package, so we resolve them in this priority order:
#   1. Explicit PYCHESS_ALEMBIC_INI env var
#   2. Current working directory (the Dockerfile sets WORKDIR /app and copies
#      alembic.ini + migrations there)
#   3. Source-checkout layout (this module's parent-parent-parent dir)
_MODULE_SOURCE_ROOT = Path(__file__).resolve().parents[3]


def _find_alembic_ini() -> Path | None:
    env = os.environ.get("PYCHESS_ALEMBIC_INI")
    if env:
        p = Path(env)
        if p.is_file():
            return p
    cwd_ini = Path.cwd() / "alembic.ini"
    if cwd_ini.is_file():
        return cwd_ini
    source_ini = _MODULE_SOURCE_ROOT / "alembic.ini"
    if source_ini.is_file():
        return source_ini
    return None


def _find_script_location(ini: Path | None) -> Path | None:
    if ini is not None:
        candidate = ini.parent / "migrations"
        if candidate.is_dir():
            return candidate
    cwd_mig = Path.cwd() / "migrations"
    if cwd_mig.is_dir():
        return cwd_mig
    source_mig = _MODULE_SOURCE_ROOT / "migrations"
    if source_mig.is_dir():
        return source_mig
    return None


def build_config(url: str, *, ini_path: Path | None = None) -> Config:
    """Return an Alembic `Config` object pointed at `url`."""
    ini = ini_path or _find_alembic_ini()
    script_location = _find_script_location(ini)
    if script_location is None:
        raise RuntimeError(
            "Could not locate Alembic migrations/ directory. "
            "Set PYCHESS_ALEMBIC_INI to the path of alembic.ini, or run from "
            "a directory containing migrations/."
        )

    if ini is not None:
        cfg = Config(str(ini))
    else:
        cfg = Config()
    cfg.set_main_option("script_location", str(script_location))
    cfg.set_main_option("sqlalchemy.url", url)
    return cfg


def apply_migrations(url: str) -> None:
    """Upgrade the schema at `url` to head. Safe to call on every boot."""
    cfg = build_config(url)
    command.upgrade(cfg, "head")


def auto_migrate_if_enabled(url: str) -> bool:
    """Apply migrations only when the `PYCHESS_AUTO_MIGRATE` env var is truthy.

    Production deploys often prefer to gate DDL behind a human step; this
    helper honors that by no-op'ing unless explicitly opted in. Dev and
    Docker turn it on via environment.
    """
    if os.environ.get("PYCHESS_AUTO_MIGRATE", "").lower() in ("1", "true", "yes", "on"):
        apply_migrations(url)
        return True
    return False
