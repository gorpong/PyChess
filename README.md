# PyChess - Terminal & Web ASCII Chess

A fully-featured, beautiful chess game written in Python. Play chess in your 
terminal with Unicode pieces and color-coded squares, or in your browser with a
modern web interface. Full chess rules implementation with AI opponents.

## Features

- ✨ **Two Interfaces** - Play in terminal (curses) or browser (web UI)
- 🌐 **Online Multiplayer** - Play over the internet via shareable invite links; real-time updates over WebSocket
- ♟️ **Full Chess Rules** - Complete implementation of official FIDE rules
- 📝 **Standard Algebraic Notation (SAN)** - Industry-standard move notation
- 💾 **PGN Support** - Save and load games in Portable Game Notation format
- 🎮 **Multiple Game Modes** - Play multiplayer or against AI
- 🤖 **AI Opponents** - Three difficulty levels (Easy, Medium, Hard)
- 🎯 **Dual Input Modes** - Cursor navigation or SAN text input (terminal)
- 🖱️ **Point & Click** - Intuitive mouse/touch controls (web)
- 🔄 **Undo/Redo** - Full move history with unlimited undo
- ❓ **Help System** - Comprehensive in-game help
- 🏁 **Complete Game Logic** - Checkmate, stalemate, draws, en passant, castling, promotion
- 📊 **Move History** - Track all moves in SAN notation
- ⌨️ **Keyboard Shortcuts** - Quick actions with keyboard (web)
- 📱 **Responsive Design** - Works on desktop and tablet browsers (web)

## Installation

### Prerequisites

- Python 3.12 or higher
- Terminal with Unicode support (for terminal UI)
- Modern web browser (for web UI)

#### Windows Setup

1. Download and install Python 3.12+ from [python.org](https://www.python.org/downloads/windows/)
   - **Important**: Check "Add Python to PATH" during installation

2. Download and install Git from [git-scm.com](https://git-scm.com/download/win)

3. Open Command Prompt and run:

````bat
git clone https://github.com/gorpong/PyChess
cd PyChess
python -m pip install .
````

#### Linux/macOS Setup

````bash
git clone https://github.com/gorpong/PyChess
cd pychess
pip install .
````

## Quick Start

### Terminal Interface

````bash
# Start a new game (shows game mode selection menu)
pychess

# List saved games
pychess --list-games

# Load a saved game
pychess --load "Game Name"

# Show a saved game in magazine format
pychess --show-game "Game Name"
````

### Web Interface

````bash
# Start the web server
pychess-web

# Start with debug mode
pychess-web --debug

# Start on a different port
pychess-web --port 9000
````

Then open your browser to `http://localhost:8080`

### Online Multiplayer

Once the web server is running, open `http://localhost:8080/match/` to reach the
online-play landing page. From there:

1. **Host**: click **Create game**, pick your colour (White / Black / Random),
   and copy the invite URL that appears above the board.
2. **Share** the URL with your opponent (text message, email, whatever).
3. **Guest**: opens the URL, lands on the join page, clicks the claim button.
4. Both browsers refresh automatically as moves are made. Either player can
   click **Resign** at any time.

The server stores in-progress matches in SQLite so a closed laptop or a quick
page refresh picks up exactly where you left off — as long as your browser
still has the PyChess session cookie.

For playing across different networks (i.e. you and the opponent are not on
the same LAN), see **[Self-hosting with Docker](#self-hosting-with-docker)**
below — you'll need to either run the server somewhere both of you can reach
or use a tunnel such as Cloudflare Tunnel or ngrok.

## Game Modes

When you start the game, you'll see a menu with these options:

1. **Multiplayer** - Two players on the same device
2. **vs AI - Easy** - Random moves (great for beginners)
3. **vs AI - Medium** - Material-based strategy (captures pieces)
4. **vs AI - Hard** - Positional play with piece-square evaluation

## How to Play

### Terminal Interface

#### Cursor Mode (Default)

- **Arrow Keys** - Move cursor around the board
- **Enter** - Select piece / Make move
- **Escape** - Cancel selection
- **TAB** - Show/hide legal move hints (Easy/Medium modes only)
- **/** - Switch to SAN input mode

#### SAN Input Mode

- Type moves like `e4`, `Nf3`, `Bxc6`, `O-O`, `e8=Q`
- **Enter** - Submit the move
- **Backspace** - Delete last character
- **/** - Switch back to cursor mode

#### Global Commands

- **q** - Quit the game
- **r** - Restart the game
- **u** - Undo the last move
- **?** - Show help overlay

### Web Interface

#### Mouse Controls

- **Click** a piece to select it
- **Click** a destination square to move
- Selected piece shows highlighted
- Legal moves shown when hints enabled

#### Keyboard Shortcuts

- **U** - Undo the last move
- **Escape** - Clear selection / Cancel dialog

#### Buttons

- **Show Hints** - Display legal moves for selected piece (Easy/Medium modes)
- **Undo** - Take back the last move
- **Save** - Save the current game
- **Restart** - Start a new game (same mode)
- **Save & Quit** - Save and return to menu
- **Quit** - Return to menu without saving

## Understanding the Board

The board is displayed from White's perspective:

- **Files** are labeled a-h (left to right)
- **Ranks** are labeled 1-8 (bottom to top)
- **Light squares** have a cream/tan color
- **Dark squares** have a brown color

### Piece Symbols

| Piece  | Terminal (White/Black) | Meaning |
|--------|------------------------|---------|
| King   | ♔ / ♚                | K       |
| Queen  | ♕ / ♛                | Q       |
| Rook   | ♖ / ♜                | R       |
| Bishop | ♗ / ♝                | B       |
| Knight | ♘ / ♞                | N       |
| Pawn   | ♙ / ♟                | P       |

## Standard Algebraic Notation (SAN)

PyChess uses Standard Algebraic Notation, the official notation system for recording chess games.

### Basic Moves

**Pawn Moves:**

- `e4` - Move pawn to e4
- `exd5` - Pawn on e-file captures on d5
- `e8=Q` - Promote pawn to Queen on e8

**Piece Moves:**

- `Nf3` - Move Knight to f3
- `Bb5` - Move Bishop to b5
- `Qd4` - Move Queen to d4
- `Nxe5` - Knight captures on e5

**Special Moves:**

- `O-O` - Kingside castling
- `O-O-O` - Queenside castling

### Check and Checkmate

- `Qh5+` - Queen to h5, giving check
- `Qxf7#` - Queen captures f7, checkmate

## Saving and Loading Games

Games are saved in PGN (Portable Game Notation) format, the standard format for chess games.

### Save Locations

- **Windows**: `%LOCALAPPDATA%\pychess\saves\`
- **macOS/Linux**: `~/.pychess/saves/`

### Save Limits

- Maximum 10 saved games
- Oldest completed games are removed first when limit is reached
- In-progress games are preserved over completed games

### PGN Headers

Each saved game includes:

- Event, Site, Date
- White and Black player names
- Result (1-0, 0-1, 1/2-1/2, or * for ongoing)
- Game mode (Multiplayer, Easy, Medium, Hard)
- Total time played

## Chess Rules Reference

### Movement Rules

- **King**: One square in any direction
- **Queen**: Any number of squares in any straight line
- **Rook**: Any number of squares horizontally or vertically
- **Bishop**: Any number of squares diagonally
- **Knight**: L-shape (2+1 squares), can jump over pieces
- **Pawn**: Forward one square (two on first move), captures diagonally

### Special Rules

**Castling** - King moves two squares toward a rook:

- King and rook must not have moved
- No pieces between them
- King not in check, doesn't pass through or end in check

**En Passant** - Special pawn capture:

- When opponent's pawn moves two squares
- Your pawn can capture as if it moved one square
- Must be done immediately

**Promotion** - When a pawn reaches the opposite end:

- Must promote to Queen, Rook, Bishop, or Knight

### Game End Conditions

- **Checkmate**: King in check with no legal moves
- **Stalemate**: No legal moves but not in check (draw)
- **Insufficient Material**: Not enough pieces to checkmate (draw)
- **Threefold Repetition**: Same position three times (draw)
- **Fifty-Move Rule**: 50 moves without capture or pawn move (draw)

## Tips for Beginners

1. **Control the Center** - Move pawns to e4, d4, e5, or d5 early
2. **Develop Pieces** - Get knights and bishops out before the queen
3. **Castle Early** - Protect your king in the first 10 moves
4. **Think Ahead** - Check if your move leaves pieces undefended
5. **Watch for Checks** - Always look for ways to attack the opponent's king

### Common Opening Moves

- **1. e4** - King's Pawn Opening (most popular)
- **1. d4** - Queen's Pawn Opening (solid)
- **1. Nf3** - Reti Opening (flexible)
- **1. c4** - English Opening (strategic)

## Development

### Running Tests

````bash
# Run all tests
pytest

# Run with coverage
pytest --cov=pychess

# Run specific test file
pytest tests/model/test_board.py

# Run integration tests
pytest tests/integration/ -v
````

### Project Structure

````text
pychess/
├── src/pychess/
│   ├── model/        # Game state, board, pieces (immutable)
│   ├── rules/        # Move generation, validation
│   ├── notation/     # SAN parsing, PGN support
│   ├── ai/           # AI engines (easy, medium, hard)
│   ├── ui/           # Terminal UI
│   ├── controller/   # Shared GameController + terminal GameSession
│   ├── match/        # Networked-multiplayer domain (Match, MatchService,
│   │                 # MatchRepository, SQLAlchemy ORM, Alembic helpers)
│   ├── web/          # Web UI (Flask + HTMX) + match routes + Socket.IO
│   └── persistence/  # Local PGN save/load
├── tests/
│   ├── model/
│   ├── rules/
│   ├── notation/
│   ├── ai/
│   ├── controller/
│   ├── match/        # Domain + repository (parametrized over both repos)
│   ├── web/          # Routes, Socket.IO, templates
│   ├── e2e/          # External-process tests (skipped unless PYCHESS_E2E_BASE_URL is set)
│   └── integration/
├── migrations/       # Alembic revisions
├── Dockerfile
├── docker-compose.yml
├── docker-compose.e2e.yml
├── docs/NETWORK_MULTIPLAYER_DESIGN.md  # Architecture reasoning
└── README.md
````

### Technology Stack

**Terminal UI:**

- Python blessed for terminal rendering
- Unicode chess symbols

**Web UI:**

- Flask for HTTP server
- HTMX for reactive updates (no JavaScript framework)
- Flask-SocketIO for real-time match updates (WebSocket, threading async mode)
- SVG chess pieces
- CSS Grid for board layout

**Networked multiplayer:**

- SQLAlchemy 2.x ORM + Alembic migrations (SQLite by default, Postgres-ready)
- Signed Flask session cookies for browser-scoped player identity
- Shareable invite codes (URL-safe, 8 chars from an unambiguous alphabet)

**Core:**

- Pure Python, no external chess engines
- Dataclasses for state management
- 1080+ tests, behavioural suite parametrized across in-memory and SQLAlchemy repositories

## Troubleshooting

### Terminal Too Small

If you see "Terminal too small" error:

- Resize your terminal to at least 100x44 characters
- Or use fullscreen mode

### Unicode Characters Not Displaying

If chess pieces don't display correctly:

- Use a modern terminal (Windows Terminal, iTerm2, GNOME Terminal)
- Try a font like Cascadia Mono or Consolas

### Web UI Not Loading

If the web interface doesn't load:

- Check that port 8080 is not in use
- Try a different port: `pychess-web --port 9000`
- Check browser console for JavaScript errors

### Online match: "Opponent disconnected" stays showing after they rejoin

The presence chip updates from server-pushed events only when your browser
is actively connected to the `/match` namespace. If you refreshed the page
while your opponent was already back, you may see a stale chip until the
next event arrives; submitting any move or clicking resign will redraw the
page from the authoritative server state.

### WebSocket connection fails behind a reverse proxy

If the client shows "connection error" banners and the server log shows
only HTTP polling requests, your reverse proxy is stripping the `Upgrade`
header. For nginx, add:

```nginx
proxy_http_version 1.1;
proxy_set_header Upgrade $http_upgrade;
proxy_set_header Connection "upgrade";
```

Cloudflare's WebSocket support is on by default; Fly.io and Render
handle this automatically.

## Requirements

- Python 3.12+
- Flask 3.0+ and Flask-SocketIO 5.3+ (web UI + networked multiplayer)
- SQLAlchemy 2.0+ and Alembic 1.13+ (networked multiplayer match persistence)
- Terminal with Unicode support (for terminal UI)
- Modern web browser (for web UI)
- Internet-accessible deployment for cross-network play (Docker image included)

## Self-hosting with Docker

The networked-multiplayer feature is designed to run inside a container. A
multi-stage `Dockerfile` builds a wheel in an isolated stage and installs it
into a slim Python 3.12 runtime as a non-root user. The container serves the
app with Gunicorn + gevent-websocket so real WebSocket handshakes do not go
through Werkzeug's development server. Match state is written to
`/data/matches.db` so you can persist games across restarts via a volume mount.

### Quick start

```bash
# Build and run the server on localhost:8080
docker compose up --build

# Open http://localhost:8080/match/ in two different browsers (or profiles)
# to create and join a game.

# Stop (keeps the match database)
docker compose down

# Stop and wipe the match database
docker compose down -v
```

If port 8080 is occupied on your host, override the external mapping:

```bash
HOST_PORT=8090 docker compose up --build
# Now http://localhost:8090/match/
```

### Running the end-to-end suite against a live container

The `docker-compose.e2e.yml` overlay builds a small tests image and runs
the external-process e2e suite against the running server — useful as a
pre-PR gate.

```bash
docker compose -f docker-compose.yml -f docker-compose.e2e.yml up \
    --build --abort-on-container-exit --exit-code-from e2e
```

### Deploying to a cloud host

Any platform that runs OCI images and gives you a persistent volume works
out of the box: Fly.io, Render, Railway, Hetzner, a home server with nginx
in front — all fine. Make sure to:

- Set `SECRET_KEY` to something long and random (the session cookie is
  signed with it; losing it invalidates all existing cookies).
- Mount a persistent volume at `/data` so SQLite survives restarts.
- Set `PYCHESS_AUTO_MIGRATE=1` for the first deploy so Alembic creates the
  schema; leave it on or switch it off based on your operational taste.
- Leave `PYCHESS_CREATE_SCHEMA=0` when `PYCHESS_AUTO_MIGRATE=1`; that keeps
  Alembic as the single schema-management path. For quick local source runs
  with migrations disabled, omit `PYCHESS_CREATE_SCHEMA` and the app will
  create missing tables with SQLAlchemy metadata.
- If you're behind TLS-terminating reverse proxy, make sure it forwards
  the `Upgrade` header so WebSocket connections complete.

## Configuration

Environment variables (read by `pychess-web` at startup):

| Variable | Default | Purpose |
|---|---|---|
| `SECRET_KEY` | random per boot | Flask session signing. **Set this explicitly in production** — a rotating key logs every player out on every restart. |
| `PYCHESS_DB_URL` | `sqlite:///pychess-matches.db` | SQLAlchemy URL for the match database. Accepts any SQLAlchemy dialect; `postgresql+psycopg://user:pw@host/db` works unchanged. |
| `PYCHESS_AUTO_MIGRATE` | off | When truthy (`1`, `true`, `yes`, `on`), run `alembic upgrade head` on startup. Docker turns it on; production deploys often prefer to gate schema changes behind a human step. |
| `PYCHESS_CREATE_SCHEMA` | auto | Controls SQLAlchemy `create_all` fallback. When unset, the app uses `create_all` only if startup migrations did not run. Docker sets this to `0` so Alembic is the only schema path. |
| `PYCHESS_SOCKETIO_ASYNC_MODE` | `threading` | Flask-SocketIO async mode for local `pychess-web` runs. Docker sets this to `gevent` because the image installs Gunicorn + gevent-websocket. |
| `PYCHESS_ALEMBIC_INI` | auto-detected | Explicit path to `alembic.ini` when neither CWD nor the source-checkout layout apply. |
| `PYCHESS_DEBUG` | off | Enables Flask debug mode (same as `--debug`). **Never set this in production**; it enables the Werkzeug interactive debugger. |
| `HOST_PORT` | `8080` | Docker Compose host-side port mapping only — does not affect the in-container port. |

### Security notes

- Player identity is a UUID kept in a Flask-signed session cookie. A leaked
  cookie means a hijacked seat; acceptable for a family-chess context but
  not for public-internet tournaments.
- Invite codes are 8 URL-safe characters from a 32-character unambiguous
  alphabet (~10¹² space). The service also retries up to 32 times on
  collision, and the `invite_code` column has a unique DB constraint as a
  belt.
- Every move is re-authorized against `match.seats[current_turn] ==
  request.player_id` inside `MatchService`. Both the HTTP and WebSocket
  entry points go through the same check — there is no path that bypasses
  seat authorization.
- TLS is out of scope for the app process; terminate it at your reverse
  proxy (Fly.io edge, Cloudflare, nginx). The Docker container listens on
  plain HTTP by design.

## Configuration knobs for common tweaks

### Add read-only spectators

By default, only the two seated players can open the play page or connect to
the `/match` Socket.IO namespace. If you want read-only spectators, change the
full-match branch in `src/pychess/web/match_routes.py` and allow non-seated
Socket.IO connects in `src/pychess/web/match_socketio.py`.

```python
# In match_routes.py, redirect late invite opens to the play page:
if match.status == MatchStatus.ACTIVE or match.is_full():
    return redirect(url_for("match.play", match_id=match.match_id))
```

### Vendor the Socket.IO client instead of using the CDN

`src/pychess/web/templates/match/play.html` loads the Socket.IO browser
client from `cdn.socket.io` with a subresource-integrity hash. That's the
default because a pinned CDN link with SRI is resistant to supply-chain
tampering and keeps the repo smaller. If you want zero external requests:

```bash
# 1. Download the pinned version into the static dir
curl -fsSL -o src/pychess/web/static/js/socket.io.min.js \
    https://cdn.socket.io/4.7.5/socket.io.min.js

# 2. Verify the checksum matches what's in play.html (optional but recommended)
sha384sum src/pychess/web/static/js/socket.io.min.js | \
    awk '{ print "sha384-" $1 | "xxd -r -p | base64 -w 0" }'

# 3. Change one script tag in templates/match/play.html from:
#       <script src="https://cdn.socket.io/4.7.5/socket.io.min.js" ...></script>
#    to:
#       <script src="{{ url_for('static', filename='js/socket.io.min.js') }}"></script>
```

The `match.js` glue code does not change.

### Switch async mode for local source runs

For local `pychess-web` source runs, the default `threading` async mode handles
two long-lived WebSocket connections comfortably. If you want to mirror the
Docker runtime locally:

```bash
pip install "pychess[server]"
PYCHESS_SOCKETIO_ASYNC_MODE=gevent \
  gunicorn --worker-class geventwebsocket.gunicorn.workers.GeventWebSocketWorker \
  --workers 1 --bind 0.0.0.0:8080 'pychess.web.app:create_app()'
```

Keep one worker unless you add a Socket.IO message queue; otherwise separate
workers will not share room membership.

## Architecture notes

The networked multiplayer feature shares one rule-application codepath with
the local CLI and the single-user web UI:

```
┌─────────────────┐   ┌──────────────────────┐   ┌───────────────────────┐
│  GameSession    │   │   GameManager        │   │   MatchService        │
│  (terminal UI)  │   │   (single-player     │   │   (networked,         │
│                 │   │    web UI)           │   │    two-player)        │
└────────┬────────┘   └───────────┬──────────┘   └───────────┬───────────┘
         │                        │                          │
         └────────────────────────┼──────────────────────────┘
                                  │
                                  ▼
                    ┌──────────────────────────┐
                    │   GameController         │
                    │   (pure rule application)│
                    └────────────┬─────────────┘
                                 │
                                 ▼
                    ┌──────────────────────────┐
                    │   pychess.model +        │
                    │   pychess.rules          │
                    │   (immutable state       │
                    │    machine + pure rules) │
                    └──────────────────────────┘
```

- `GameController` validates moves against the full legal-moves generator
  (not just a king-safety check) and returns a `MoveOutcome` that callers
  translate into UI updates, HTTP responses, or Socket.IO events.
- `MatchService` is the single place that enforces seat authorization. It
  has no knowledge of HTTP or WebSocket — transport layers are thin
  translators on top.
- `MatchRepository` is a Protocol with two implementations: an in-memory
  dict for tests and a SQLAlchemy ORM repo for production. The service
  test suite runs against both to guarantee behavioural parity.

See `docs/NETWORK_MULTIPLAYER_DESIGN.md` for the full design reasoning.

## Future actions

Known improvements we explicitly did not ship in the networked multiplayer
feature, with enough detail for someone (possibly future-you) to pick them up:

### Fix flaky `test_evict_oldest_complete_first` persistence test

`tests/persistence/test_save_manager.py::TestSaveLimit::test_evict_oldest_complete_first`
intermittently fails on full-suite runs. Root cause: the test relies on
`MTIME_DELAY = 0.01` (10ms sleeps) to produce distinct file mtimes, and
then sorts by `st_mtime` to decide eviction order. On filesystems with
1-second mtime granularity (ext2/ext3, some network mounts, some WSL2
tmpfs configurations), two files saved within the same 1-second window
get identical mtimes and the sort order becomes undefined. The test
"mostly works" only because the 10ms sleeps occasionally straddle a
1-second boundary.

Recommended fix: replace the `time.sleep(MTIME_DELAY)` dance with
explicit `os.utime(path, (ts, ts))` calls that set monotonically
increasing timestamps after save. No sleeps, no filesystem-granularity
dependence, same assertion. The change is local to the test file:

```python
# Instead of:
manager.save_game("OldComplete", state, headers)
time.sleep(MTIME_DELAY)

# Do:
path = manager.save_game("OldComplete", state, headers)
os.utime(path, (counter, counter)); counter += 1
```

This is a blocking issue for CI — a flaky test stops the pipeline for no
real reason. Prioritize before adding CI.

### Optional browser-level smoke via Playwright

The in-process Flask-SocketIO tests cover the full event protocol and the
external-process e2e tests cover Docker deployment. A browser-driven
smoke test would additionally prove the rendered SVG/CSS behaves on real
browsers. If you ever need it, a Playwright suite under `tests/e2e/browser/`
and a second `docker-compose.browser.yml` overlay would slot in cleanly.

### Explicit draw offer / accept flow

Resigning works today; offering a draw mid-game does not. Sketched in
`docs/NETWORK_MULTIPLAYER_DESIGN.md` §7 as the event pair
`draw_offered` → `draw_response`. Requires a small state addition on
`Match` (`pending_draw_offer_from: Optional[Color]`) plus two new
`MatchService` methods. Maybe an hour of work including tests.

### Time controls / clocks

Not implemented; requires a background tick loop and a fair bit of state.
Off-scope for teaching chess with family, but an obvious next-feature candidate.

### CLI as a network client

`GameController` was extracted specifically so a future terminal-based
client could reuse the same rule-application code. Blocked on redesigning
`GameSession.run()`'s blocking input loop to be event-driven. Doable;
roughly doubles the scope that Phases 0–4 covered.

## License

MIT License - See LICENSE file for details

## Acknowledgments

- Chess rules based on [FIDE Laws of Chess](https://handbook.fide.com/chapter/E012023)
- SAN notation following official chess standards
- Built with [blessed](https://github.com/jquast/blessed) for terminal UI
- Web UI powered by [HTMX](https://htmx.org/)

---

**Enjoy playing chess!** ♔♕♖♗♘♙
