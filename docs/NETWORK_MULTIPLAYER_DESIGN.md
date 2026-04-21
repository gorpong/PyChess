# PyChess Networked Multiplayer — Design Document

**Status:** Implemented. Kept for historical context — do not read as a forward-looking TODO.
**Author:** Design pass, 2026-04-17
**Scope:** Add remote two-player gameplay to PyChess via a cloud/self-hosted server, while preserving existing local CLI and single-user web modes.

> Everything below describes the reasoning that informed the implementation on
> this branch. For how to actually run the feature, see the main `README.md`.

---

## 1. Goals & Non-Goals

### Goals
- Two humans on different networks can play a full game of chess against each other through a shared server.
- Invite-by-URL: one player creates a game, shares a link, the other joins. No accounts, no passwords.
- Real-time move delivery (WebSocket push), not poll-driven.
- Games survive server restarts (SQLite-backed).
- Lenient reconnection: closing a laptop does not end the game.
- The existing local CLI and single-user web experience continue to work unchanged.
- Docker Compose topology lets us test server + two clients locally before any cloud deploy.

### Non-Goals (this iteration)
- Accounts, authentication, ratings, matchmaking lobby.
- Spectators, chat, clocks/time controls.
- CLI as a network client (explicitly deferred; can be added later with minimal server-side changes).
- Horizontal scaling / multi-process server. Single-container, single-process is sufficient for 2-player hobby use.
- Tournament/rating systems, analysis engines, live broadcasts.

---

## 2. Current Architecture (Summary)

| Layer | Module | State |
|---|---|---|
| Engine (pure) | `pychess.model`, `pychess.rules`, `pychess.notation` | Immutable `GameState`, pure functions. **Already network-safe.** |
| AI | `pychess.ai` | Pure; takes `GameState`, returns `Move`. |
| Persistence | `pychess.persistence` | PGN files on local disk, sanitized names, 10-game cap. |
| CLI controller | `pychess.controller.game_session` | `GameSession.run()` is a **blocking loop** that calls renderer methods directly. Hot spot for any networking refactor of CLI. |
| Web controller | `pychess.web.game_manager` | `GameManager` singleton, in-memory dict of `WebGameSession` keyed by secure cookie session id. |
| Web HTTP | `pychess.web.routes` (Flask + HTMX) | 14 REST endpoints; no WebSocket today. |
| Tests | `tests/` | ~42 files, ~12K lines. Engine and rules thoroughly covered; web routes covered via Flask test client. |

### Coupling observations relevant to this work

1. **Engine is clean.** `GameState` + rules are pure and immutable — they drop straight into a server process with no refactoring.
2. **Web already has a session layer** (`GameManager`) that we can generalise to "a match with two players" rather than "a game belonging to one browser cookie". This is the main refactor.
3. **No player identity concept anywhere.** `GameState.turn` is derived from move count. Networked play needs an explicit binding: *which cookie owns the White seat vs. the Black seat in match M?*
4. **CLI is out of scope** for networked play, but we want our refactor to make a future CLI-client plausible (don't regress that direction).
5. **Persistence is PGN-file-per-game.** For server use we need a database layer that can hold in-progress games with metadata (invite code, seat→player map, status). PGN stays as the canonical move record inside each row.

---

## 3. Target Architecture

```
┌─────────────────────────┐       ┌─────────────────────────┐
│  Browser A (White)      │       │  Browser B (Black)      │
│  pychess web UI         │       │  pychess web UI         │
└───────────┬─────────────┘       └─────────────┬───────────┘
            │ HTTPS + WSS                         │
            │                                      │
            ▼                                      ▼
        ┌─────────────────────────────────────────────┐
        │  pychess-server (Flask + Flask-SocketIO)    │
        │  ┌─────────────────────────────────────┐    │
        │  │ HTTP routes (existing + /match/*)   │    │
        │  │ SocketIO namespace /match           │    │
        │  │ MatchService (new)                  │    │
        │  │ GameController (new, UI-agnostic)   │    │
        │  │ engine (model + rules + notation)   │    │
        │  │ MatchRepository (new, SQLite)       │    │
        │  └─────────────────────────────────────┘    │
        └──────────────────┬──────────────────────────┘
                           │
                   ┌───────┴────────┐
                   │  SQLite volume │
                   │  matches.db    │
                   └────────────────┘
```

### New components

- **`GameController`** — UI-agnostic orchestrator. Takes a `GameState`, a `Move` (or SAN string + source seat), returns a new `GameState` + events (`move_applied`, `promotion_required`, `game_over`, …). No Flask, no blessed, no cookies. Both `GameSession` (CLI) and `MatchService` (server) will sit on top of it.
- **`Match`** — value object: `match_id`, `invite_code`, `seats: {White: player_id|None, Black: player_id|None}`, `game_state`, `status ∈ {waiting, active, finished, abandoned}`, `created_at`, `last_move_at`, timestamps of connect/disconnect per seat.
- **`Player`** — minimal: `player_id` (UUID in signed cookie), optional display name.
- **`MatchService`** — business logic: create match, join match, apply remote move, handle reconnect. Authorizes every move against `match.seats[current_turn] == requesting_player_id`.
- **`MatchRepository`** — SQLite-backed storage for `Match`. One row per match; move log appended as PGN.
- **SocketIO `/match` namespace** — event-driven channel. Rooms keyed by `match_id`; both players join the room on connect.

### What does not change

- `pychess.model`, `pychess.rules`, `pychess.notation`, `pychess.ai`, `pychess.persistence` (local PGN saves): untouched.
- CLI (`pychess.controller.game_session`, `pychess.ui.*`): untouched in behaviour, though we migrate its inner *logic* onto `GameController` so both entry points share one code path (§4).
- Existing single-user web routes and HTMX templates: continue to work. New multiplayer lives behind `/match/*` routes + `/match` Socket.IO namespace.

---

## 4. Refactoring Prerequisites (Phase 0)

Before networking is added, we extract a shared `GameController` so both the CLI and the new `MatchService` are driven by the same rules-application code. This is not strictly required, but it is the single highest-leverage cleanup and it pays for itself the moment we want the server to enforce promotions or end-of-game detection exactly like the CLI does.

### Why it needs to come first
- Today `GameSession._execute_move` and `GameManager._execute_move` duplicate validation, promotion handling, and game-end detection with slightly different code paths. Duplicating a *third* time inside `MatchService` is the path to divergent bugs.
- Test surface: the existing tests pin down the observable behaviour of both controllers. If we consolidate onto one controller **before** adding a network, the safety net catches regressions immediately.

### Shape
```python
# pychess/controller/game_controller.py  (new, pure)
@dataclass(frozen=True)
class MoveOutcome:
    new_state: GameState
    events: tuple[GameEvent, ...]   # MoveApplied, PromotionRequired, GameOver, etc.

class GameController:
    def apply_move(self, state: GameState, move: Move) -> MoveOutcome: ...
    def apply_san(self, state: GameState, san: str) -> MoveOutcome: ...
    def legal_moves(self, state: GameState, square: Square) -> list[Move]: ...
    def detect_end(self, state: GameState) -> GameOver | None: ...
```
`GameSession` and `GameManager` become thin — they own I/O, cursor/selection state, pending-promotion UI state, and delegate all rule work to `GameController`.

### Exit criteria for Phase 0
- `GameController` exists with unit tests.
- `GameSession` and `GameManager` call `GameController` for all move application and game-end detection.
- All existing tests still pass with zero behaviour change.

---

## 5. Phased Implementation Plan

Each phase ends with a concrete test gate. **Do not move to the next phase until the gate is green.**

### Phase 0 — Controller Extraction (refactor, no user-visible change)
- Extract `GameController` per §4.
- Rewrite `GameSession._execute_move` and `GameManager._execute_move` to delegate.
- **Tests (gate):** all existing tests pass unchanged + new `tests/controller/test_game_controller.py` covering move application, SAN parsing, promotion, checkmate/stalemate/draw detection, and event emission.

### Phase 1 — Match Domain Model (no I/O, no network yet)
- Add `pychess.match` package: `Match`, `Player`, `Seat (Color)`, `MatchStatus` enum, `MatchService` (in-memory implementation), invite-code generator (8-char URL-safe).
- `MatchService.create_match(creator_player_id, creator_seat)` → `Match` with invite code.
- `MatchService.join(invite_code, joiner_player_id)` → assigns remaining seat; rejects if already full or same player tries to take both seats.
- `MatchService.submit_move(match_id, player_id, move)` — validates `match.seats[state.turn] == player_id`, delegates to `GameController`, updates match, returns events.
- **Tests (gate):** `tests/match/test_match_service.py`:
  - Creating, joining, rejecting a third joiner.
  - Move authorization: wrong player on turn is rejected; right player is accepted.
  - Creator seat choice: `white`, `black`, and `random` all honored; joiner lands on the other seat.
  - Promotion across seats.
  - Game-over persists to `match.status = finished`.
  - Invite-code uniqueness, collision handling.

### Phase 2 — SQLite Persistence for Matches (SQLAlchemy ORM)
- Add `MatchRepository` backed by **SQLAlchemy 2.x ORM**. Rationale: greenfield project, the extra setup cost is small, and we get Alembic migrations, typed sessions, and a clean path off SQLite (to Postgres) if hosting ever demands it — without rewriting persistence.
- Dependencies added: `sqlalchemy>=2.0`, `alembic>=1.13`.
- `MatchORM` declarative model mirrors the schema in §6; `MatchRepository` exposes domain-level `save(match)` / `get(match_id)` / `get_by_invite(code)` / `list_active_for_player(player_id)` and internally maps ORM rows to `Match` domain objects.
- `MatchService` accepts a repository protocol; in-memory impl becomes a test double. The domain layer never imports SQLAlchemy.
- Alembic initialized; baseline migration generated from the models. Server boot runs `alembic upgrade head` automatically if `PYCHESS_AUTO_MIGRATE=1` (default in dev/Docker; off for prod-by-hand).
- **Tests (gate):** `tests/match/test_match_repository.py` — round-trip save/load including mid-game, finished, abandoned states; full Phase 1 service suite re-run with the SQLAlchemy repo injected; Alembic upgrade from empty DB on a `tmp_path` SQLite file.

### Phase 3 — HTTP Endpoints for Matches
- New blueprint `pychess.web.match_routes`:
  - `POST /match/new` — creator **explicitly picks their seat** (`white`, `black`, or `random`). Returns `{match_id, invite_code, invite_url, your_seat}`. The "New Game" form on the landing page offers all three options; `random` is useful so the creator isn't always on the same side when they're teaching. The joiner is auto-assigned the remaining seat.
  - `GET /match/join/<invite_code>` — page that prompts to join (shows who's waiting), POSTs to…
  - `POST /match/join/<invite_code>` — claims the open seat, redirects to match page.
  - `GET /match/<match_id>` — match page: renders board + current state for this viewer's seat orientation.
  - `POST /match/<match_id>/move` — fallback for non-WS clients (and for tests); submits a move.
  - `POST /match/<match_id>/resign` — resign.
- Player identity: signed cookie `pychess_player_id` (UUID), set on first visit to any `/match/*` route.
- **Tests (gate):** `tests/web/test_match_routes.py` using Flask test client:
  - Create-and-join full round trip with two simulated cookies.
  - Move authorization (player B cannot move on player A's turn).
  - Reconnect: closing and reopening the session cookie still lets that player move if the cookie is preserved. Fresh cookie cannot hijack an existing seat.

### Phase 4 — WebSocket (Flask-SocketIO) Push Layer
- Add `flask-socketio` + `eventlet` (or `gevent`) to deps.
- `/match` Socket.IO namespace. On connect with `match_id` query param:
  - Authenticate via cookie `pychess_player_id`.
  - `join_room(match_id)`.
  - Emit current `match_state` to connecting socket.
  - Broadcast `opponent_connected` to the other seat.
- Events (server→client): `match_state`, `move_applied`, `promotion_required`, `game_over`, `opponent_connected`, `opponent_disconnected`, `error`.
- Events (client→server): `submit_move`, `resign`, `request_state`.
- `MatchService.submit_move` gains a post-commit hook that pushes to the room.
- HTMX/JS client: lightweight socket.io-client in a new `match.js`, reusing existing board rendering.
- **Tests (gate):** `tests/web/test_match_socketio.py` using `socketio.test_client`:
  - Two clients join same match; move from A is received by B.
  - Unauthorized move (wrong seat) yields `error` event, no state change.
  - `opponent_disconnected` emitted on close; reconnect re-emits `match_state`.

### Phase 5 — Docker Topology & End-to-End Verification
- `Dockerfile` — multi-stage: build wheel, slim runtime image. Runs `pychess-web` bound to `0.0.0.0:8080`.
- `docker-compose.yml` with three services:
  - `server` — the app image, exposes `:8080`, mounts volume `pychess-data:/data` for `matches.db`.
  - `client-a`, `client-b` — headless browser drivers (Playwright) for integration smoke. Optional: replace with a documented "open two browser tabs" flow if Playwright adds too much weight.
- `docker-compose.test.yml` overlay runs pytest inside the image against the live server.
- **Tests (gate):** `tests/e2e/test_two_player_match.py` (Playwright or `requests` + `python-socketio` client): scripts player A creating a match and player B joining, exchanges 4–6 moves, verifies both clients see identical final state, then disconnects A and confirms B sees `opponent_disconnected` and A's reconnect restores state.

### Phase 6 — Polish, Reconnect UX, Docs
- Reconnect indicator in UI (chip showing opponent online/offline).
- Landing page: "Create game" / "Join with code".
- Resign / offer draw buttons (draw offer as a single server event pair: `draw_offered`, `draw_response`).
- Update `README.md` with the new online-play section, `docker compose up` instructions, deploy notes for Fly.io / Render as an appendix.
- Retire `docs/NETWORK_MULTIPLAYER_DESIGN.md` from the user-facing surface (keep in repo; note "implemented" status).
- **Tests (gate):** All prior suites green. Manual smoke: full game between two browsers, including mid-game refresh of both clients, wins cleanly.

---

## 6. Data Model (Persistence)

```sql
CREATE TABLE matches (
    id              TEXT PRIMARY KEY,           -- UUID4
    invite_code     TEXT NOT NULL UNIQUE,       -- 8 chars URL-safe
    status          TEXT NOT NULL,              -- waiting|active|finished|abandoned
    white_player_id TEXT,
    black_player_id TEXT,
    pgn             TEXT NOT NULL DEFAULT '',   -- authoritative move history
    current_fen     TEXT NOT NULL,              -- cache; recomputable from pgn
    result          TEXT,                       -- 1-0 | 0-1 | 1/2-1/2 | *
    created_at      INTEGER NOT NULL,
    updated_at      INTEGER NOT NULL
);
CREATE INDEX idx_matches_invite ON matches(invite_code);
CREATE INDEX idx_matches_status_updated ON matches(status, updated_at);
```

Player IDs are opaque UUIDs from signed cookies; there is no `players` table in this iteration (no login).

---

## 7. Protocol Reference

### REST (subset — see Phase 3 for full list)
- `POST /match/new` → `{match_id, invite_code, invite_url, your_seat}`
- `POST /match/join/<invite_code>` → redirect to `/match/<match_id>`
- `POST /match/<match_id>/move` (form: `from`, `to`, `promotion?`) → `{ok, state}`

### Socket.IO `/match` namespace
Server → client:
- `match_state { fen, pgn, turn, your_seat, seats, status, result? }`
- `move_applied { san, fen, by_seat }`
- `promotion_required { from, to }`
- `game_over { result, reason }`
- `opponent_connected {}` / `opponent_disconnected {}`
- `error { code, message }`

Client → server:
- `submit_move { from, to, promotion? }`
- `resign {}`
- `request_state {}`

All server responses to `submit_move` are authoritative; clients render only what the server confirms. Optimistic UI is a later concern.

---

## 8. Security & Abuse Considerations

- **Move authorization:** Every submitted move is rejected unless `match.seats[state.turn] == request.player_id`. This is the single most important server-side check.
- **Cookie integrity:** `pychess_player_id` is an itsdangerous-signed cookie. Leaked cookie = seat hijack; acceptable trade-off for "no accounts" design, documented in README.
- **Rate limiting:** Per-socket cap on `submit_move` events (e.g., 10/sec) to deflect a spamming client. Flask-Limiter on REST endpoints.
- **Invite code entropy:** 8 URL-safe chars ≈ 48 bits; collision-checked on insert. Invite codes are short-lived — once both seats are claimed, the code is no longer needed, and `/match/join/<code>` 410s.
- **Input validation:** Reuse `notation.san` parser — it already rejects malformed SAN. FEN never comes from clients.
- **Secrets:** `SECRET_KEY` must be environment-provided in Docker. README documents generation.
- **TLS:** Out of scope for the app; terminated by the hosting platform's edge proxy (Fly.io / Render / a reverse proxy in front of Docker Compose).

---

## 9. Docker Topology

**Dev / test (local):**
```
docker compose up          # server on localhost:8080
                           # open two browser tabs to test
docker compose --profile e2e up   # also runs Playwright e2e suite
```

**Production-ish (self-host or PaaS):**
- Single container, `pychess-web` bound to `$PORT`.
- Volume mount for `/data` (SQLite db).
- Environment: `SECRET_KEY`, `PYCHESS_DB_PATH=/data/matches.db`, `PYCHESS_PUBLIC_URL` (used to build invite URLs).

---

## 10. Testing Strategy

- **Keep TDD discipline.** Every phase above has a named test file and an explicit gate.
- **Engine tests stay untouched.** They are our regression oracle for the Phase 0 refactor.
- **New suites:**
  - `tests/controller/test_game_controller.py` (Phase 0)
  - `tests/match/test_match_service.py` (Phase 1)
  - `tests/match/test_match_repository.py` (Phase 2)
  - `tests/web/test_match_routes.py` (Phase 3)
  - `tests/web/test_match_socketio.py` (Phase 4)
  - `tests/e2e/test_two_player_match.py` (Phase 5)
- **CI hint:** Once stable, add a GitHub Actions workflow: `pytest` on push; `docker compose --profile e2e up --abort-on-container-exit` on PRs.

---

## 11. Risks & Open Questions

| Risk | Mitigation |
|---|---|
| Flask-SocketIO + eventlet can be fussy with Flask 3.x. | Pin versions; have a long-polling fallback ready (Socket.IO supports it natively). |
| Player loses cookie (clears cookies / switches device). | Accept it as a known limitation; document a "rejoin code" feature as future work — signed token in the invite URL itself so a seat can be recovered. |
| Server restart mid-move broadcast. | SQLite write precedes emit. Client re-fetches `match_state` on reconnect, so a dropped broadcast self-heals on the next socket connect. |
| SQLite write contention. | Single-process server + per-match serialization. Not a concern at 2-player scale. |

### Deferred questions (not blocking)
- Time controls / clocks.
- Draw-by-agreement UI flow (sketched above but not finalized).
- CLI-as-network-client — the `GameController` refactor leaves the door open; revisit once server is stable.
- Rating / match history page.

---

## 12. Proposed PR Plan

One PR per phase, each reviewed and merged independently. This maps cleanly onto the test gates above and keeps the diff reviewable:

1. `refactor: extract GameController shared by CLI and web` (Phase 0)
2. `feat: Match domain model and in-memory MatchService` (Phase 1)
3. `feat: SQLite-backed MatchRepository` (Phase 2)
4. `feat: /match HTTP endpoints and shareable invite codes` (Phase 3)
5. `feat: real-time match updates via Flask-SocketIO` (Phase 4)
6. `chore: Dockerfile and docker-compose for local multi-client testing` (Phase 5)
7. `docs: README online-play section; polish reconnect UX` (Phase 6)

---
