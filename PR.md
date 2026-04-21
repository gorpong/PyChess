# Suggested PR description

> Copy this into the GitHub PR body (or paste into `gh pr create --body-file PR.md`),
> then delete `PR.md` from the branch before merging — this file is just a staging
> draft.

---

## Add networked two-player multiplayer

Adds a server-hosted two-player mode to PyChess so players on different
networks can share an invite link and play in real time. Built on top of the
existing engine and web UI without any changes to their user-visible
behaviour — all local CLI, single-user web, and AI flows work exactly as
before.

### What you get

- `/match/` web landing page with **Create new game** (White / Black / Random
  seat picker) and **Join with code**.
- Invite-code URLs shareable by text, email, or link — no accounts, no logins.
- Real-time move push via Flask-SocketIO (WebSocket with long-poll fallback).
- SQLite-backed match persistence via SQLAlchemy + Alembic, so closed laptops
  and server restarts don't kill in-progress games.
- Opponent presence indicator (online / offline chip) on the play page.
- Resign button; resigning before the opponent joins deletes the match outright
  so stale invite codes don't linger.
- Full Docker deployment story: multi-stage `Dockerfile`, `docker-compose.yml`
  with named volume for SQLite, `docker-compose.e2e.yml` overlay that runs an
  external-process e2e suite against the live container.

### Why this shape

Detailed reasoning lives in [`docs/NETWORK_MULTIPLAYER_DESIGN.md`](docs/NETWORK_MULTIPLAYER_DESIGN.md)
(included in the diff; marked Implemented). The short version:

- **The engine was already clean.** `pychess.model` + `pychess.rules` are
  immutable and pure. They drop into a server process with no changes.
- **The existing controllers weren't.** `GameSession` (CLI) and `GameManager`
  (single-user web) each had their own `_execute_move` with small
  behavioural drift. Phase 0 of this work extracted a shared `GameController`
  that all three call sites — CLI, single-user web, and the new
  `MatchService` — delegate to. That refactor is the reason a networked
  server can enforce the exact same move semantics as a local game without
  code duplication.
- **Strict authorization at one boundary.** Every single move (HTTP form,
  WebSocket event, or otherwise) re-checks `match.seats[state.turn] ==
  requesting_player_id` inside `MatchService`. There is no path that bypasses
  this check. Player identity is a signed Flask session cookie — no
  secondary auth surface, no new secrets to manage.
- **Trust the framework.** SQLAlchemy ORM + Alembic from day one rather than
  raw `sqlite3` means migrating off SQLite (e.g. to Postgres for multi-instance
  deploys) is a URL change, not a rewrite. Also avoids the SQLite-specific
  gotcha of needing `render_as_batch=True` for future `ALTER` migrations.

### Test coverage

- **1080 unit/integration tests**, zero regressions against the 930-test
  baseline. Net +150 new tests.
- Match-service behavioural suite is parametrized across both repository
  implementations (in-memory and SQLAlchemy), so the SQL-backed repo is
  guaranteed behaviourally equivalent to its test-double counterpart.
- Alembic migrations are covered: empty-DB upgrade, idempotency, and a
  service round-trip against the migrated schema.
- HTTP routes exercised via Flask test client with two simulated browsers
  (separate cookie jars): creation, joining, seat authorization, reconnection
  via cookie recovery, spectator mode, resign.
- Socket.IO event protocol covered via `SocketIOTestClient`: connect
  rejection without a cookie / match id, initial-state push on connect,
  move broadcast, opponent-disconnect notifications, error paths, resign
  over WebSocket, REST→WS cross-talk.
- **6 external-process e2e tests** under `tests/e2e/` run inside a pytest
  container that talks to the live server container via the
  `docker-compose.e2e.yml` overlay. They're skipped unless
  `PYCHESS_E2E_BASE_URL` is set, so developer `pytest` runs stay fast.

Run locally:

```bash
pytest                                # 1080 passed, 6 skipped (e2e auto-skip)
docker compose -f docker-compose.yml -f docker-compose.e2e.yml up \
    --build --abort-on-container-exit --exit-code-from e2e
                                      # full stack + e2e: 6 passed
```

### Review path (suggested order)

1. `docs/NETWORK_MULTIPLAYER_DESIGN.md` — the architectural reasoning.
2. `src/pychess/controller/game_controller.py` — the shared controller that
   made everything else possible.
3. `src/pychess/match/` — the networked domain (models, service, repos,
   serialization, migrations).
4. `src/pychess/web/match_routes.py` + `match_socketio.py` — the transport
   layer, deliberately thin.
5. Tests — in particular `tests/match/test_match_service.py` (behavioural
   contract) and `tests/web/test_match_socketio.py` (Socket.IO dispatch).

### Known limitations / future work

These are explicitly documented in the README's **Future actions** section so
nothing is hiding:

- One pre-existing persistence test (`test_evict_oldest_complete_first`) is
  intermittently flaky on filesystems with 1-second `mtime` granularity
  (ext3, some WSL2 tmpfs configs). Root cause identified and a minimal fix
  sketched — not changed in this PR because it's pre-existing and unrelated,
  but worth fixing before wiring up CI.
- Werkzeug dev server under `allow_unsafe_werkzeug=True` is fine for home
  use but emits occasional `write() before start_response` warnings. Gunicorn
  + gevent upgrade path is documented.
- Draw offers are not implemented (resign is). Sketched as a ~1-hour task.
- Time controls / clocks are not implemented.
- CLI-as-network-client was deliberately deferred; the shared
  `GameController` refactor leaves the door open.

### Backwards compatibility

- All pre-existing tests pass without modification except:
  - **Two tests in `tests/web/test_game_manager.py`** that set up impossible
    board positions and relied on the old unvalidated move-application path.
    The new shared controller strictly validates against the legal-moves
    generator (required for safe networked play); the tests were updated to
    use a real promotion setup. No runtime behaviour regressed.
  - **Five tests in `tests/web/test_app.py`** that called `create_app()` with
    no arguments. Now that `create_app` provisions a `MatchService` backed by
    a SQLite file, unflagged calls would drip a `pychess-matches.db` into the
    developer's working directory on every test run. The tests were updated
    to pass `{'TESTING': True}`, which routes to an in-memory DB. Test
    behaviour and assertions are unchanged; the edit is purely test hygiene.
- New environment variables (`PYCHESS_DB_URL`, `PYCHESS_AUTO_MIGRATE`,
  `PYCHESS_SOCKETIO_ASYNC_MODE`, etc.) all have sensible defaults that keep
  `pychess-web` behaving like it did before for anyone who doesn't know the
  feature exists.
- New optional Python dependencies: `flask-socketio`, `simple-websocket`,
  `sqlalchemy`, `alembic`. Listed in `pyproject.toml`.

### Security notes

Summarized in the README but worth flagging for review:

- Session cookie is the only auth surface. Leaked cookie = hijacked seat.
  Acceptable for family / friends use, not for public tournaments.
- Invite codes are ~10¹² space, collision-retried, and uniquely indexed at
  the DB layer.
- TLS is out of scope for the app; expect a reverse proxy to terminate it.
- No user-supplied data reaches the ORM as raw SQL; all writes go through
  typed columns and SQLAlchemy parameter binding.

---

*This branch is the product of a 6-phase development plan laid out in the
design doc, with every phase gated on a green test suite before moving on.
Happy to walk through any section in person if that helps the review.*
