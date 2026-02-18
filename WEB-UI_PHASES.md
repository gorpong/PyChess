# PyChess Web UI Implementation Phases

## Document History

| Date | Phase | Status | Notes |
| ------ | ------- | -------- | ------- |
| 2026-02-16 | 1 | Complete | Project setup, Flask skeleton |
| 2026-02-16 | 2 | Complete | Game state serialization |
| 2026-02-16 | 3 | Complete | Board rendering with SVG pieces |
| 2026-02-17 | 4 | Complete | Game session management |
| 2026-02-17 | 5 | Complete | Piece selection and hints (on request) |
| 2026-02-17 | 6 | Complete | Move execution, promotion, undo, game end |
| 2026-02-17 | 7 | Complete | AI integration polish and tests |
| 2026-02-17 | 8 | Complete | Game mode menu and navigation |

---

## Continuation Instructions for Next Agent

### Context

Phases 1-6 are complete. The web UI has:

- Flask app with HTMX for reactivity
- Working chess board with SVG pieces
- Piece selection and move execution
- Pawn promotion dialog
- Undo functionality
- Game end detection (checkmate, stalemate, draws)
- Hints system (only in multiplayer/easy/medium modes, on request)
- AI already integrated in game_manager.py (executes after human move)

### Files to Request

To continue development, request these files:

**Core web files:**

- `src/pychess/web/app.py`
- `src/pychess/web/routes.py`
- `src/pychess/web/game_manager.py`
- `src/pychess/web/serializers.py`

**Templates:**

- `src/pychess/web/templates/base.html`
- `src/pychess/web/templates/index.html`
- `src/pychess/web/templates/partials/game_area.html`
- `src/pychess/web/templates/partials/board.html`
- `src/pychess/web/templates/partials/history.html`
- `src/pychess/web/templates/partials/promotion.html`

**CSS:**

- `src/pychess/web/static/css/chess.css`

**Tests:**

- `tests/web/test_routes.py`
- `tests/web/test_game_manager.py`

**Reference files from terminal UI:**

- `src/pychess/persistence/save_manager.py`
- `src/pychess/main.py` (for save/load flow reference)

### Remaining Phases

- Phase 7: AI Integration (already works, needs status messaging polish)
- Phase 8: Game Mode Menu & Navigation
- Phase 9: Save/Load Integration
- Phase 10: Polish & Desktop Browser Support

---

## Completed Phases (As-Built)

### Phase 1: Project Setup

**Created:**

- `src/pychess/web/__init__.py`
- `src/pychess/web/app.py` - Flask factory with `create_app()`, entry point `main()`
- `src/pychess/web/routes.py` - Blueprint registered as `main`
- `src/pychess/web/templates/base.html`
- `src/pychess/web/templates/index.html`
- `src/pychess/web/static/js/htmx.min.js` - Vendored locally
- `src/pychess/web/static/js/chess.js` - Placeholder
- `tests/web/__init__.py`
- `tests/web/test_app.py`

**Modified:**

- `pyproject.toml` - Added `flask>=3.0.0`, entry point `pychess-web`
- `src/pychess/main.py` - Added `--web` flag support

**Key decisions:**

- Debug mode off by default, enabled via `--debug` flag or `PYCHESS_DEBUG` env var
- Server runs on port 8080 by default
- HTMX vendored locally (no CDN)

### Phase 2: Game State Serialization

**Created:**

- `src/pychess/web/serializers.py`
- `tests/web/test_serializers.py`

**Functions implemented:**

- `game_state_to_dict(state)` - Returns dict with turn, castling, en_passant, move_history, is_check
- `board_to_template_data(board, selected, legal_moves, last_move)` - Returns 8x8 grid of square dicts
- `square_to_piece_code(board, square)` - Returns piece codes like 'wK', 'bP'
- `is_light_square(square)` - Boolean for square color
- `format_move_history(move_history)` - Returns list of (move_num, white_move, black_move) tuples

### Phase 3: Board Rendering

**Created:**

- `src/pychess/web/templates/partials/board.html`
- `src/pychess/web/static/css/chess.css`
- `src/pychess/web/static/images/pieces/*.svg` - 12 SVG files (wK, wQ, wR, wB, wN, wP, bK, bQ, bR, bB, bN, bP)

**Modified:**

- `src/pychess/web/routes.py` - Index route returns board data
- `src/pychess/web/templates/index.html` - Includes board partial

**CSS features:**

- CSS Grid for 8x8 board
- Square colors: light `#f0d9b5`, dark `#b58863`
- Hover uses `filter: brightness(1.1)` for visibility on both colors
- Rank labels (1-8) and file labels (a-h)

### Phase 4: Game Session Management

**Created:**

- `src/pychess/web/game_manager.py`
- `tests/web/test_game_manager.py`

**Key classes:**

- `WebGameSession` dataclass with: session_id, game_state, state_history, selected_square, ai_engine, game_mode, start_time, game_name, last_move, show_hints, status_messages, pending_promotion, game_result
- `GameManager` class with: create_game, get_game, update_game, delete_game, select_square, toggle_hints, complete_promotion, undo_move, load_saved_game

**Global functions:**

- `get_game_manager()` - Returns singleton
- `reset_game_manager()` - For testing

**Session ID:** Generated with `secrets.token_urlsafe(32)`

**Modified:**

- `src/pychess/web/app.py` - Added secure session config
- `src/pychess/web/routes.py` - Added `get_or_create_session()`, `get_current_session()`, `/api/new-game` route

### Phase 5: Piece Selection & Hints

**Modified:**

- `src/pychess/web/game_manager.py` - Added `hints_allowed` property, `get_legal_moves_for_selected()`, `select_square()`, `toggle_hints()`
- `src/pychess/web/routes.py` - Added `/api/select`, `/api/toggle-hints` routes, `render_game_state()`, `build_game_context()`
- `src/pychess/web/templates/partials/board.html` - Added HTMX attributes
- `src/pychess/web/static/css/chess.css` - Added selection, legal-move, hover styles

**Created:**

- `src/pychess/web/templates/partials/game_area.html` - Main game layout partial

**Hints behavior:**

- Only available in multiplayer, easy, medium modes (not hard)
- Must select piece first, then click "Show Hints" button
- Resets when selecting different piece

**HTMX pattern:**

- Squares post to `/api/select` with `hx-vals='{"square": "..."}'`
- Target is `#game-container`, swap is `innerHTML`
- `render_game_state()` detects HTMX requests via `HX-Request` header and returns partial

### Phase 6: Move Execution

**Modified:**

- `src/pychess/web/game_manager.py` - Added `_execute_move()`, `_apply_move()`, `_do_ai_move()`, `complete_promotion()`, `undo_move()`, game end detection
- `src/pychess/web/routes.py` - Added `/api/promote`, `/api/undo` routes
- `src/pychess/web/serializers.py` - Added `format_move_history()`
- `src/pychess/web/templates/partials/game_area.html` - Added history panel, promotion overlay, game-over overlay, undo button
- `src/pychess/web/static/css/chess.css` - Added promotion dialog, game-over overlay, history panel styles

**Created:**

- `src/pychess/web/templates/partials/promotion.html`
- `src/pychess/web/templates/partials/history.html`

**Move execution:**

- Click legal destination in `select_square()` triggers move
- Promotion detected when multiple moves match (different promotion pieces)
- `pending_promotion` stored in session, completed via `/api/promote`
- AI move executes automatically after human move in AI modes
- Undo removes both moves in AI mode, single move in multiplayer

**Game end:**

- `game_result` stored in session ('1-0', '0-1', '1/2-1/2')
- `is_game_over` property blocks further moves
- Overlay displayed with result

---

## Remaining Phases

### Phase 7: AI Integration

AI already works in game_manager.py. Phase 7 should:

- Add "AI thinking..." status message display
- Verify all difficulty levels work correctly
- Add tests for AI response flow

### Phase 8: Game Mode Menu & Navigation

Need to implement:

- Mode selection buttons on index page (currently shows board immediately)
- Separate `/game` route for active game
- Restart button with confirmation
- Save & Quit button
- Quit button with save prompt

Routes to add:

- `GET /game` - Game page (separate from index)
- `POST /api/restart` - Restart game
- `POST /api/quit` - Quit game

### Phase 9: Save/Load Integration

Need to implement:

- `GET /games` - List saved games
- `POST /api/games/save` - Save current game
- `POST /api/games/<name>/load` - Load saved game
- `DELETE /api/games/<name>` - Delete saved game
- Save dialog partial for name input
- Games list template

Use existing `SaveManager` from `src/pychess/persistence/save_manager.py`.

### Phase 10: Polish

- Loading indicator for AI thinking
- Keyboard shortcuts (u=undo, r=restart, Escape=clear selection)
- Error handling improvements
- Browser testing (Chrome, Firefox, Safari, Edge)
- Responsive CSS verification

---

## API Endpoints (Current)

| Method | Path | Description |
| -------- | ------ | ------------- |
| GET | `/` | Index with board |
| POST | `/api/new-game` | Create game (mode param) |
| POST | `/api/select` | Select square (square param) |
| POST | `/api/toggle-hints` | Toggle hints |
| POST | `/api/promote` | Complete promotion (piece param) |
| POST | `/api/undo` | Undo move(s) |

## API Endpoints (To Add)

| Method | Path | Description |
| -------- | ------ | ------------- |
| GET | `/game` | Game page |
| GET | `/games` | Saved games list |
| POST | `/api/restart` | Restart game |
| POST | `/api/quit` | Quit game |
| POST | `/api/games/save` | Save game |
| POST | `/api/games/<name>/load` | Load game |
| DELETE | `/api/games/<name>` | Delete game |
