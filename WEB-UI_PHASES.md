# PyChess Web UI Implementation Phases

This document tracks the phased implementation of a web-based UI for PyChess.
Each phase is designed to be a small, reviewable step that can be tested
independently before moving to the next phase.

## Document History

| Date | Phase | Status | Notes |
| ------ | ------- | -------- | ------- |
| 2026-02-16 | 1 | Complete | Project setup, Flask skeleton |
| 2026-02-16 | 2 | Complete | Game state serialization |
| 2026-02-16 | 3 | Complete | Board rendering with SVG pieces |
| 2026-02-17 | 4 | Complete | Game session management |
| 2026-02-17 | 5 | Complete | Piece selection and hints (on request) |
| 2026-02-17 | 6 | Complete | Move execution, promotion, undo, game end |

---

## Technology Stack

### Chosen Stack

- **Backend:** Flask 3.0+ (lightweight, well-documented)
- **Frontend Reactivity:** HTMX 1.9+ (HTML-over-the-wire, minimal JS)
- **Styling:** Custom CSS with CSS Grid
- **Piece Display:** SVG chess pieces (scalable, consistent rendering)
- **Future Enhancement:** WebSocket support for real-time AI feedback

### Rationale

1. Aligns with project philosophy: clarity over cleverness
2. Minimal dependencies beyond standard library
3. No complex JavaScript build process
4. Easy to test with Flask's test client
5. Progressive enhancement possible (WebSockets later if needed)
6. Self-contained: HTMX vendored locally, no CDN required

### New Dependencies

```toml
# To be added to pyproject.toml [project.dependencies]
flask = ">=3.0.0"
```

### Entry Points

```toml
# To be added to pyproject.toml [project.scripts]
pychess-web = "pychess.web.app:main"
```

The terminal `pychess` command will also support `pychess --web` to launch
the web interface.

---

## Architecture Overview

### Directory Structure

```text
src/pychess/
├── web/                          # Web UI package
│   ├── __init__.py
│   ├── app.py                    # Flask application factory
│   ├── routes.py                 # HTTP route handlers
│   ├── game_manager.py           # Session-based game management
│   ├── serializers.py            # GameState ↔ JSON/HTML helpers
│   ├── static/
│   │   ├── css/
│   │   │   └── chess.css         # Board and UI styling
│   │   ├── js/
│   │   │   ├── htmx.min.js       # Vendored HTMX (no CDN)
│   │   │   └── chess.js          # Minimal enhancements
│   │   └── images/
│   │       └── pieces/           # SVG chess pieces
│   │           ├── wK.svg        # White King
│   │           ├── wQ.svg        # White Queen
│   │           ├── wR.svg        # White Rook
│   │           ├── wB.svg        # White Bishop
│   │           ├── wN.svg        # White Knight
│   │           ├── wP.svg        # White Pawn
│   │           ├── bK.svg        # Black King
│   │           ├── bQ.svg        # Black Queen
│   │           ├── bR.svg        # Black Rook
│   │           ├── bB.svg        # Black Bishop
│   │           ├── bN.svg        # Black Knight
│   │           └── bP.svg        # Black Pawn
│   └── templates/
│       ├── base.html             # Base template with HTMX
│       ├── index.html            # Mode selection
│       ├── game.html             # Game page
│       ├── games_list.html       # Saved games list
│       └── partials/
│           ├── board.html        # HTMX partial - board
│           ├── status.html       # HTMX partial - status messages
│           ├── history.html      # HTMX partial - move history
│           └── promotion.html    # HTMX partial - promotion dialog
tests/
└── web/
    ├── __init__.py
    ├── test_app.py
    ├── test_routes.py
    ├── test_serializers.py
    └── test_game_manager.py
```

### Component Relationships

```text
┌─────────────────────────────────────────────────────────────┐
│                       Browser                               │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │ Board View  │  │ Status Bar  │  │ Move History        │  │
│  │ (CSS Grid)  │  │ (Messages)  │  │ (SAN list)          │  │
│  └──────┬──────┘  └──────┬──────┘  └──────────┬──────────┘  │
│         │                │                    │             │
│         └────────────────┼────────────────────┘             │
│                          │ HTMX                             │
│                          ▼                                  │
└─────────────────────────HTTP────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                    Flask Server                             │
│  ┌─────────────┐  ┌─────────────────────┐                   │
│  │   routes    │──│   game_manager      │                   │
│  │  (HTTP)     │  │ (session → game)    │                   │
│  └─────────────┘  └──────────┬──────────┘                   │
│                              │                              │
│         ┌────────────────────┼────────────────────┐         │
│         ▼                    ▼                    ▼         │
│  ┌─────────────┐   ┌─────────────────┐  ┌───────────────┐   │
│  │  GameState  │   │   AIEngine      │  │  SaveManager  │   │
│  │  (model)    │   │   (ai)          │  │  (persist)    │   │
│  └─────────────┘   └─────────────────┘  └───────────────┘   │
│        │                                                    │
│        ▼                                                    │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  rules (validator, move_generator, game_logic)      │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

### Key Design Decisions

1. **Session-based games** - Each browser session gets a game instance stored
   server-side. Games persist via `SaveManager` when user clicks "Save & Quit".

2. **Reuse existing components:**
   - `GameState`, `Board`, `Square`, `Piece` - unchanged
   - `get_legal_moves()`, `is_move_legal()` - unchanged
   - `move_to_san()`, `san_to_move()` - unchanged
   - `AIEngine` - unchanged
   - `SaveManager` - unchanged (handles cross-UI game persistence)

3. **New web-specific controller** - `WebGameSession` wraps game logic without
   terminal dependencies.

4. **HTMX for reactivity** - Board updates via HTML fragment replacement.
   HTMX is vendored locally for offline play.

5. **SVG pieces** - Scalable vector graphics for consistent rendering across
   browsers and screen sizes.

6. **Cross-UI save compatibility** - Games saved from web UI can be loaded
   in terminal UI and vice versa (both use PGN via `SaveManager`).

---

## Phase 1: Project Setup & Flask Skeleton

### Goal

Create the basic Flask application structure that can be run and returns
a simple "Welcome to PyChess" page. Establish the project organization
and verify the build/install process works.

### Files to Create

1. `src/pychess/web/__init__.py` - Package marker
2. `src/pychess/web/app.py` - Flask application factory and entry point
3. `src/pychess/web/routes.py` - Basic route returning welcome page
4. `src/pychess/web/templates/base.html` - Base HTML template
5. `src/pychess/web/templates/index.html` - Simple index page
6. `src/pychess/web/static/js/htmx.min.js` - Vendored HTMX library
7. `tests/web/__init__.py` - Test package marker
8. `tests/web/test_app.py` - Basic application tests

### Files to Modify

1. `pyproject.toml` - Add Flask dependency and entry points
2. `src/pychess/main.py` - Add `--web` flag support

### pyproject.toml Changes

```toml
[project]
dependencies = [
    "blessed>=1.20.0",
    "flask>=3.0.0",
]

[project.scripts]
pychess = "pychess.main:main"
pychess-web = "pychess.web.app:main"
```

### Acceptance Criteria

- [ ] `pip install -e .` succeeds with new dependencies
- [ ] `pychess-web` command starts Flask development server on port 8080
- [ ] `pychess --web` also starts the web server
- [ ] Visiting `http://localhost:8080` shows "Welcome to PyChess"
- [ ] Page loads HTMX from local vendored file (no network request)
- [ ] All existing terminal tests still pass
- [ ] New tests pass: test app creation, test index route returns 200

### Testing Strategy

```python
def test_app_creates_successfully():
    """Test that Flask app can be created."""
    from pychess.web.app import create_app
    app = create_app()
    assert app is not None


def test_index_returns_200(client):
    """Test that index page returns successfully."""
    response = client.get('/')
    assert response.status_code == 200
    assert b'PyChess' in response.data
```

---

## Phase 2: Game State Serialization

### Goal

Create serialization utilities to convert `GameState` to JSON-friendly
dictionaries for API responses, and to extract display-ready data for
templates.

### Files to Create

1. `src/pychess/web/serializers.py` - Serialization functions
2. `tests/web/test_serializers.py` - Serializer tests

### Key Functions

```python
def game_state_to_dict(state: GameState) -> dict:
    """Convert GameState to JSON-serializable dict.
    
    Returns dict with keys:
    - turn: 'white' or 'black'
    - fullmove_number: int
    - halfmove_clock: int
    - castling: dict with kingside/queenside for each color
    - en_passant: square string or None
    - move_history: list of SAN strings
    - is_check: bool
    """

def board_to_template_data(
    board: Board,
    selected: Optional[Square] = None,
    legal_moves: Optional[set[Square]] = None,
    last_move: Optional[tuple[Square, Square]] = None,
) -> list[list[dict]]:
    """Convert board to 8x8 list of square data for templates.
    
    Each square dict contains:
    - square: algebraic notation (e.g., 'e4')
    - piece: piece code (e.g., 'wK', 'bP') or None
    - is_light: bool
    - is_selected: bool
    - is_legal_move: bool
    - is_last_move: bool
    """
```

### Acceptance Criteria

- [ ] `game_state_to_dict()` produces valid JSON for initial position
- [ ] `board_to_template_data()` produces 8x8 grid with piece info
- [ ] Round-trip test: serialize and verify data integrity
- [ ] Handles special states: en passant square, castling rights
- [ ] Selected square and legal moves properly flagged

### Testing Strategy

```python
def test_initial_position_serialization():
    """Test serializing the initial game position."""
    state = GameState.initial()
    data = game_state_to_dict(state)
    assert data['turn'] == 'white'
    assert data['fullmove_number'] == 1
    assert data['castling']['white']['kingside'] is True


def test_board_template_data_dimensions():
    """Test that board data is 8x8."""
    board = Board.initial()
    data = board_to_template_data(board)
    assert len(data) == 8
    assert all(len(rank) == 8 for rank in data)


def test_board_template_data_piece_codes():
    """Test that pieces have correct codes."""
    board = Board.initial()
    data = board_to_template_data(board)
    # Rank 8 (index 0) should have black pieces
    assert data[0][0]['piece'] == 'bR'  # a8
    assert data[0][4]['piece'] == 'bK'  # e8
    # Rank 1 (index 7) should have white pieces
    assert data[7][0]['piece'] == 'wR'  # a1
    assert data[7][4]['piece'] == 'wK'  # e1
```

---

## Phase 3: Board Rendering (HTML/CSS) with SVG Pieces

### Goal

Create the visual chess board using HTML and CSS with SVG piece images.
The board should display correctly with proper colors, pieces, and
coordinate labels.

### Files to Create

1. `src/pychess/web/templates/partials/board.html` - Board partial template
2. `src/pychess/web/static/css/chess.css` - Board and piece styling
3. `src/pychess/web/static/images/pieces/*.svg` - 12 SVG piece files

### Files to Modify

1. `src/pychess/web/routes.py` - Add route to display board with game state
2. `src/pychess/web/templates/index.html` - Include board partial for testing

### SVG Piece Sources

Options for SVG pieces (all public domain or permissively licensed):

1. **Wikimedia Commons Chess Pieces** - Public domain, classic style
2. **Colin M.L. Burnett pieces** - BSD licensed, widely used
3. **Custom minimal SVGs** - Create simple geometric pieces

Recommendation: Use Colin M.L. Burnett pieces (same as lichess.org uses)
as they are clean, recognizable, and freely licensed.

### Visual Design Specifications

- 8x8 grid using CSS Grid
- Square colors: Light `#f0d9b5`, Dark `#b58863`
- Board border: subtle shadow or outline
- Piece sizing: 80-90% of square size, centered
- File labels (a-h) below board
- Rank labels (1-8) to the left of board
- Responsive: min-width 320px, max-width 640px

### Board HTML Structure

```html
<div class="board-container">
<div class="rank-labels">
<span>8</span><span>7</span><!-- ... --><span>1</span>
</div>
<div class="board" id="board">
{% for rank in board_data %}
{% for square in rank %}
<div class="square {% if square.is_light %}light{% else %}dark{% endif %}"
data-square="{{ square.square }}">
{% if square.piece %}
<img src="/static/images/pieces/{{ square.piece }}.svg"
alt="{{ square.piece }}"
class="piece">
{% endif %}
</div>
  {% endfor %}
{% endfor %}
<div class="file-labels">
<span>a</span><span>b</span><!-- ... --><span>h</span>
</div>
```

### Acceptance Criteria

- [ ] Board displays with correct alternating square colors
- [ ] All 32 pieces show in correct starting positions
- [ ] SVG pieces render clearly at various sizes
- [ ] Pieces are centered within squares
- [ ] Board has file (a-h) and rank (1-8) labels
- [ ] Board is centered on page and reasonably sized
- [ ] Works in Chrome, Firefox, Safari on Linux/Windows/macOS
- [ ] Resizing browser window scales board appropriately

### Testing Strategy

- Visual inspection in multiple browsers
- Template renders without Jinja errors
- Correct number of squares (64)
- All 12 SVG files load without 404 errors

```python
def test_board_partial_renders(client):
    """Test that board partial renders without errors."""
    response = client.get('/test-board')
    assert response.status_code == 200
    assert b'class="board"' in response.data
    assert response.data.count(b'class="square') == 64
```

## Phase 4: Game Session Management

### Goal

Create server-side game session management. Each browser session gets
a unique game that persists across requests within that session.

### Files to Create

1. `src/pychess/web/game_manager.py` - Session and game management

### Key Classes

```python
@dataclass
class WebGameSession:
    """Server-side game session for web UI.
    
    Attributes:
        session_id: Unique identifier for this session
        game_state: Current game state
        state_history: Previous states for undo functionality
        selected_square: Currently selected square (if any)
        ai_engine: AI engine for single-player mode (None for multiplayer)
        game_mode: 'multiplayer', 'easy', 'medium', or 'hard'
        start_time: Unix timestamp when game started
        game_name: Name for saving (None until saved or loaded)
    """
    session_id: str
    game_state: GameState
    state_history: list[GameState]
    selected_square: Optional[Square]
    ai_engine: Optional[AIEngine]
    game_mode: str
    start_time: float
    game_name: Optional[str] = None


class GameManager:
    """Manages active game sessions.
    
    Sessions are stored in memory during play. Games are persisted
    to PGN files via SaveManager when user clicks "Save & Quit".
    """
    
    def __init__(self, max_sessions: int = 100) -> None:
        """Initialize with maximum concurrent sessions."""
    
    def create_game(self, session_id: str, mode: str) -> WebGameSession:
        """Create a new game for the given session."""
    
    def get_game(self, session_id: str) -> Optional[WebGameSession]:
        """Get existing game for session, or None."""
    
    def update_game(self, session_id: str, game: WebGameSession) -> None:
        """Update the game state for a session."""
    
    def delete_game(self, session_id: str) -> None:
        """Remove a game session (after save or abandon)."""
    
    def load_saved_game(
        self, session_id: str, game_name: str
    ) -> WebGameSession:
        """Load a saved game from PGN into a new session."""
```

### Files to Modify

1. `src/pychess/web/routes.py` - Integrate session management
2. `src/pychess/web/app.py` - Configure Flask secret key for sessions

### Acceptance Criteria

- [ ] New game creates session with initial position
- [ ] Session persists across page refreshes (same browser)
- [ ] Different browsers/incognito windows get different games
- [ ] Game state updates correctly on moves
- [ ] Session properly tracks selected square
- [ ] AI engine initialized correctly for AI modes
- [ ] Sessions have reasonable memory limits (max 100 concurrent)

### Testing Strategy

```python
def test_create_game_returns_initial_position():
    """Test that new game has initial position."""
    manager = GameManager()
    session = manager.create_game("test-id", "multiplayer")
    assert session.game_state.fullmove_number == 1
    assert session.game_state.turn == Color.WHITE


def test_different_sessions_independent():
    """Test that different sessions have independent games."""
    manager = GameManager()
    session1 = manager.create_game("id-1", "multiplayer")
    session2 = manager.create_game("id-2", "multiplayer")
    
    # Modify session1
    session1.selected_square = Square(file='e', rank=2)
    manager.update_game("id-1", session1)
    
    # session2 should be unaffected
    retrieved = manager.get_game("id-2")
    assert retrieved.selected_square is None


def test_ai_engine_created_for_ai_mode():
    """Test that AI engine is initialized for AI modes."""
    manager = GameManager()
    session = manager.create_game("test-id", "hard")
    assert session.ai_engine is not None
    assert session.ai_engine.difficulty == Difficulty.HARD
```

## Phase 5: Piece Selection & Legal Move Display

### Goal

Implement click-to-select piece functionality. When a piece is clicked,
highlight it and show its legal destination squares.

### Files to Modify

1. `src/pychess/web/routes.py` - Add selection endpoint
2. `src/pychess/web/templates/partials/board.html` - Add HTMX click handlers
3. `src/pychess/web/static/css/chess.css` - Selection and highlight styles
4. `src/pychess/web/game_manager.py` - Add selection handling methods

### Files to Create

1. `src/pychess/web/static/js/chess.js` - Minimal JS for click coordinate extraction

### Interaction Flow

1. User clicks square containing their piece
2. HTMX sends POST to /api/select with square parameter
3. Server validates piece belongs to active player
4. Server calculates legal moves for that piece
5. Server updates session's selected_square
6. Server returns updated board HTML with:
   - Selected square highlighted (golden/yellow)
   - Legal destination squares highlighted (green overlay/dot)
7. HTMX swaps board HTML

### HTMX Integration

```html
<div class="square {{ square_classes }}"
data-square="{{ square.square }}"
hx-post="/api/select"
hx-vals='{"square": "{{ square.square }}"}'
hx-target="#board"
hx-swap="outerHTML">
```

### CSS Highlight Classes

```css
.square.selected {
box-shadow: inset 0 0 0 4px #ffcc00;
}

.square.legal-move::after {
content: '';
position: absolute;
width: 30%;
height: 30%;
background: rgba(0, 128, 0, 0.5);
border-radius: 50%;
}

.square.legal-move.has-piece::after {
/* For captures: ring around the square instead of dot */
width: 100%;
height: 100%;
background: transparent;
border: 4px solid rgba(0, 128, 0, 0.5);
border-radius: 0;
box-sizing: border-box;
}
```

### Acceptance Criteria

- [ ] Clicking own piece highlights it with visible selection indicator
- [ ] Legal destination squares show green dot (empty) or ring (capture)
- [ ] Clicking opponent's piece shows error message, no selection
- [ ] Clicking empty square when nothing selected does nothing
- [ ] Clicking empty square when piece selected clears selection
- [ ] Clicking same piece again deselects it
- [ ] Board updates feel responsive (< 200ms perceived)

### Testing Strategy

```python
def test_select_own_piece_returns_legal_moves(client):
"""Test selecting own piece shows legal moves."""
# Start new game
client.post('/api/new-game', data={'mode': 'multiplayer'})

# Select e2 pawn (White's turn)
response = client.post('/api/select', data={'square': 'e2'})
assert response.status_code == 200

# Should have selected class on e2
assert b'selected' in response.data
# Should show e3 and e4 as legal moves
assert response.data.count(b'legal-move') >= 2


def test_select_opponent_piece_rejected(client):
"""Test that selecting opponent's piece fails."""
client.post('/api/new-game', data={'mode': 'multiplayer'})

# Try to select e7 pawn (Black's piece, but White's turn)
response = client.post('/api/select', data={'square': 'e7'})

# Should not have any selection
assert b'selected' not in response.data
```

---

## Phase 6: Move Execution

### Goal

Complete the move flow: user selects piece, clicks destination, move
executes, board updates.

### Files to Modify

1. `src/pychess/web/routes.py` - Add move endpoint
2. `src/pychess/web/game_manager.py` - Add move execution method
3. `src/pychess/web/templates/partials/board.html` - Handle move vs select click
4. `src/pychess/web/templates/game.html` - Add status and history panels
5. `src/pychess/web/static/css/chess.css` - Last move highlighting

### Files to Create

1. `src/pychess/web/templates/partials/status.html` - Status message display
2. `src/pychess/web/templates/partials/history.html` - Move history display
3. `src/pychess/web/templates/partials/promotion.html` - Promotion piece chooser

### Interaction Flow (Normal Move)

1. User has piece selected (from Phase 5)
2. User clicks a legal destination square
3. JavaScript detects click is on legal-move square
4. HTMX sends POST to `/api/move` with `from` and `to` parameters
5. Server validates move is legal
6. Server executes move, updates game state
7. Server clears selection, records move in history
8. Server returns updated board + status + history (HTMX OOB swap)

### Interaction Flow (Pawn Promotion)

1. User moves pawn to promotion rank
2. Server detects promotion needed
3. Server returns promotion dialog partial
4. User clicks promotion piece choice (Q/R/B/N)
5. HTMX sends POST to `/api/promote` with piece choice
6. Server completes move with chosen piece
7. Normal response with updated board

### Promotion Dialog HTML

```html
<div id="promotion-dialog" class="promotion-overlay">
<div class="promotion-choices">
<button hx-post="/api/promote" hx-vals='{"piece": "Q"}'>
<img src="/static/images/pieces/{{ color }}Q.svg" alt="Queen">
</button>
<button hx-post="/api/promote" hx-vals='{"piece": "R"}'>
<img src="/static/images/pieces/{{ color }}R.svg" alt="Rook">
</button>
<button hx-post="/api/promote" hx-vals='{"piece": "B"}'>
<img src="/static/images/pieces/{{ color }}B.svg" alt="Bishop">
</button>
<button hx-post="/api/promote" hx-vals='{"piece": "N"}'>
<img src="/static/images/pieces/{{ color }}N.svg" alt="Knight">
</button>
</div>
```

### HTMX Out-Of-Band Swaps

Move responses update multiple elements simultaneously:

```html
<!-- Primary response: the board -->
<div id="board">...</div>
<div id="status" hx-swap-oob="true">
<p class="status-message">White played e4</p>
</div>
<div id="history" hx-swap-oob="true">
<ol class="move-list">
<li><span class="move-number">1.</span> e4</li>
</ol>
</div>
```

### Acceptance Criteria

- [ ] Legal moves execute successfully
- [ ] Board updates to show new position
- [ ] Moved piece appears on destination square
- [ ] Captured pieces are removed
- [ ] Turn indicator changes (shown in status)
- [ ] Move appears in history panel (SAN notation)
- [ ] Last move squares are highlighted
- [ ] Illegal move attempts show error, don't change state
- [ ] Pawn promotion shows piece choice dialog
- [ ] Promotion completes with chosen piece
- [ ] Castling moves both king and rook
- [ ] En passant removes captured pawn correctly
- [ ] Check is indicated in status
- [ ] Checkmate ends game with result message
- [ ] Stalemate ends game with draw message

### Testing Strategy

```python
def test_e4_opening_move(client):
    """Test executing e4 as opening move."""
    client.post('/api/new-game', data={'mode': 'multiplayer'})
    client.post('/api/select', data={'square': 'e2'})
    response = client.post('/api/move', data={'from': 'e2', 'to': 'e4'})
    
    assert response.status_code == 200
    # Pawn should be on e4 now
    assert b'data-square="e4"' in response.data
    # e2 should be empty
    # Status should indicate Black's turn


def test_castling_moves_both_pieces(client):
    """Test that castling moves king and rook."""
    # Set up position where castling is legal
    # Execute O-O
    # Verify king on g1 and rook on f1


def test_promotion_shows_dialog(client):
    """Test that pawn promotion shows piece selection."""
    # Set up position with pawn on 7th rank
    # Move pawn to 8th rank
    # Response should contain promotion dialog
```

## Phase 7: AI Integration

### Goal

Integrate the existing AIEngine for single-player mode. After the human
player moves, the AI responds automatically.

### Files to Modify

1. `src/pychess/web/game_manager.py` - Add AI move execution
2. `src/pychess/web/routes.py` - Handle AI response in move flow
3. `src/pychess/web/templates/partials/status.html` - Show AI thinking/move

### Challenges & Solutions

**Challenge:** AI thinking blocks the HTTP response.
**Solution:** For Easy and Medium AI, thinking is fast (< 100ms) and can be
synchronous. For Hard AI, thinking may take 1-2 seconds which is acceptable
for an initial implementation. Future enhancement: WebSocket for async
notification.

### Modified Move Flow (vs AI)

1. Human makes move (same as Phase 6)
2. Server executes human move
3. Server detects it's AI's turn
4. Server calls `ai_engine.select_move(game_state)`
5. Server executes AI move
6. Server returns board showing position after BOTH moves
7. Status shows: "You played: e4 — AI played: e5"

### Undo Behavior

In AI mode, undo should undo BOTH the AI's move and the human's previous
move (same as terminal version), allowing the player to retry their turn.

```python
def undo_move(self, session: WebGameSession) -> WebGameSession:
    """Undo the last move(s).
    
    In AI mode: undoes both AI's move and player's move.
    In multiplayer: undoes single move.
    """
    if session.ai_engine and len(session.state_history) >= 2:
        # Pop AI's state, then player's state
        session.state_history.pop()
        session.game_state = session.state_history.pop()
    elif session.state_history:
        session.game_state = session.state_history.pop()
    
    return session
```

### Acceptance Criteria

- [ ] AI responds automatically after human move
- [ ] AI moves are legal (validated by rules engine)
- [ ] All three difficulty levels work correctly
- [ ] Easy AI makes random legal moves
- [ ] Medium AI prefers captures and material
- [ ] Hard AI uses positional evaluation
- [ ] AI checkmates are detected and displayed
- [ ] Undo in AI mode undoes both moves
- [ ] Status clearly shows both human and AI moves

### Testing Strategy

```python
def test_ai_responds_to_human_move(client):
    """Test that AI makes a move after human."""
    client.post('/api/new-game', data={'mode': 'easy'})
    client.post('/api/select', data={'square': 'e2'})
    response = client.post('/api/move', data={'from': 'e2', 'to': 'e4'})
    
    # After human's e4 and AI's response, it should be White's turn
    assert b"Your turn" in response.data or b"White to move" in response.data


def test_undo_in_ai_mode_undoes_both(client):
    """Test that undo removes both human and AI moves."""
    client.post('/api/new-game', data={'mode': 'easy'})
    client.post('/api/select', data={'square': 'e2'})
    client.post('/api/move', data={'from': 'e2', 'to': 'e4'})
    
    # Now undo
    response = client.post('/api/undo')
    
    # Should be back to initial position
    # e2 should have white pawn again
```

## Phase 8: Game Mode Menu & Navigation

### Goal

Create the game mode selection page and overall navigation flow,
matching terminal functionality.

### Files to Modify

1. `src/pychess/web/templates/index.html` - Full mode selection UI
2. `src/pychess/web/templates/game.html` - Add navigation controls
3. `src/pychess/web/routes.py` - Handle mode selection and navigation

### Mode Selection UI

```text
┌────────────────────────────────────────────────────────────┐
│                                                            │
│                    ♔ PyChess ♚                           │
│                                                            │
│              Terminal Chess in Your Browser                │
│                                                            │
├────────────────────────────────────────────────────────────┤
│                                                            │
│          ┌─────────────────────────────────────┐           │
│          │   👥  Two Players (Multiplayer)     │           │
│          └─────────────────────────────────────┘           │
│                                                            │
│          ┌─────────────────────────────────────┐           │
│          │   🤖  Play vs AI - Easy             │           │
│          └─────────────────────────────────────┘           │
│                                                            │
│          ┌─────────────────────────────────────┐           │
│          │   🤖  Play vs AI - Medium           │           │
│          └─────────────────────────────────────┘           │
│                                                            │
│          ┌─────────────────────────────────────┐           │
│          │   🤖  Play vs AI - Hard             │           │
│          └─────────────────────────────────────┘           │
│                                                            │
│          ┌─────────────────────────────────────┐           │
│          │   📂  Load Saved Game               │           │
│          └─────────────────────────────────────┘           │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

### In-Game Navigation Controls

The game page should have:

- **Undo** button - Undo last move(s)
- **Restart** button - Start new game (with confirmation)
- **Save & Quit** button - Save game and return to menu
- **Quit** button - Return to menu (with save prompt if game in progress)

### Routes

| Method | Path | Description |
| --------- | ----- | ----------- |
| GET | `/` | Mode selection page |
| POST | `/api/new-game` | Create new game with mode |
| GET | `/game` | Current game page |
| POST | `/api/quit` | Quit current game |

### Acceptance Criteria

- [ ] Index page shows all game mode options
- [ ] Clicking mode starts new game and redirects to /game
- [ ] Game page has visible Undo, Restart, Save & Quit buttons
- [ ] Restart prompts for confirmation if game in progress
- [ ] Quit prompts to save if game has moves
- [ ] Navigation works without full page reloads where sensible

### Testing Strategy

```python
def test_index_shows_all_modes(client):
    """Test that index page has all game mode options."""
    response = client.get('/')
    assert b'Multiplayer' in response.data
    assert b'Easy' in response.data
    assert b'Medium' in response.data
    assert b'Hard' in response.data
    assert b'Load Saved' in response.data


def test_new_game_redirects_to_game(client):
    """Test that starting new game goes to game page."""
    response = client.post('/api/new-game', 
                          data={'mode': 'multiplayer'},
                          follow_redirects=True)
    assert b'board' in response.data
```

## Phase 9: Save/Load Integration

### Goal

Integrate with existing SaveManager for game persistence. Users can
save games in progress, load previous games, and games auto-save on
completion. Saved games work across web and terminal interfaces.

### Files to Modify

1. `src/pychess/web/routes.py` - Save/load endpoints
2. `src/pychess/web/game_manager.py` - Save/load methods
3. `src/pychess/web/templates/index.html` - Link to saved games

### Files to Create

1. `src/pychess/web/templates/games_list.html` - Saved games list page
2. `src/pychess/web/templates/partials/save_dialog.html` - Save name input

### New Routes

| **Method** | **Path** | **Description** |
| ---------- | -------- | --------------- |
| GET | `/games` | List all saved games |
| POST | `/api/games/save` | Save current game |
| POST | `/api/games/<name>/load` | Load a saved game |
| DELETE | `/api/games/<name>` | Delete a saved game |

### Save Flow

1. User clicks "Save & Quit" button
2. If game has no name, show save dialog for name input
3. User enters name and confirms
4. Server calls `SaveManager.save_game()` with PGN headers
5. Server clears session
6. User redirected to index or games list

### Load Flow

1. User clicks "Load Saved Game" on index
2. Server shows list of saved games with metadata
3. User clicks game to load
4. Server calls `SaveManager.load_game()`
5. Server creates new session with loaded state
6. User redirected to /game with loaded position

### Games List UI

```text
┌────────────────────────────────────────────────────────────────────────┐
│                         📂 Saved Games (3/10)                          │
├────────────────────────────────────────────────────────────────────────┤
│                                                                        │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │ Practice Game 1                                                  │  │
│  │ Player vs Computer (Easy) • 12 moves • In Progress               │  │
│  │ Last played: 2024-01-15                                          │  │
│  │                                        [Load]  [Delete]          │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                                                        │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │ Quick Match                                                      │  │
│  │ White vs Black (Multiplayer) • 24 moves • White wins (1-0)       │  │
│  │ Last played: 2024-01-14                                          │  │
│  │                                        [View]  [Delete]          │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                                                        │
│                              [← Back to Menu]                          │
│                                                                        │
└────────────────────────────────────────────────────────────────────────┘
```

### Cross-UI Compatibility

Games saved from web UI can be loaded in terminal:

```bash
pychess --load "Practice Game 1"
```

Games saved from terminal can be loaded in web UI.

### Acceptance Criteria

- [ ] Can save in-progress game with custom name
- [ ] Saved games list shows all games with metadata
- [ ] Can load incomplete game and continue playing
- [ ] Completed games can be viewed (read-only)
- [ ] Can delete saved games
- [ ] Save respects 10-game limit (evicts oldest completed)
- [ ] Completed games auto-save with generated name
- [ ] Quit with unsaved changes prompts to save
- [ ] Games saved in web load correctly in terminal
- [ ] Games saved in terminal load correctly in web

### Testing Strategy

```python
def test_save_game_creates_pgn_file(client, tmp_path):
    """Test that saving creates a PGN file."""
    # Start and play a game
    client.post('/api/new-game', data={'mode': 'multiplayer'})
    client.post('/api/select', data={'square': 'e2'})
    client.post('/api/move', data={'from': 'e2', 'to': 'e4'})
    
    # Save it
    response = client.post('/api/games/save', 
                          data={'name': 'Test Game'})
    assert response.status_code == 200
    
    # Verify file exists
    # Verify PGN content is valid


def test_load_game_restores_position(client):
    """Test that loading restores game state."""
    # Save a game with some moves
    # Start fresh session
    # Load the game
    # Verify board shows saved position
```

## Phase 10: Polish & Desktop Browser Support

### Goal

Final polish pass ensuring good user experience across desktop browsers
on Linux, Windows, and macOS. Responsive design for various window sizes.

### Tasks

1. **Responsive CSS**
   - Board scales smoothly from 320px to 640px width
   - UI remains usable at small window sizes
   - Large screens don't have awkwardly huge board
2. **Visual feedback**
   - Loading indicator during AI thinking
   - Button hover/active states
   - Smooth transitions on board updates

3. **Keyboard shortcuts** (optional enhancement)
   - `u` - Undo
   - `r` - Restart (with confirmation)
   - `Escape` - Clear selection

4. **Error handling**
   - Network errors show friendly message
   - Invalid states handled gracefully
   - Session timeout handling

5. **Browser testing**
   - Chrome on Linux, Windows, macOS
   - Firefox on Linux, Windows, macOS
   - Safari on macOS
   - Edge on Windows

### CSS Responsive Breakpoints

```css
/* Base: small windows */
.board-container {
    max-width: 100%;
    padding: 1rem;
}

.board {
    width: min(90vw, 480px);
    height: min(90vw, 480px);
}

/* Larger windows */
@media (min-width: 768px) {
    .game-layout {
        display: grid;
        grid-template-columns: auto 250px;
        gap: 2rem;
    }
    
    .board {
        width: min(60vw, 560px);
        height: min(60vw, 560px);
    }
}

/* Large screens */
@media (min-width: 1200px) {
    .board {
        width: 560px;
        height: 560px;
    }
}
```

### Acceptance Criteria

- [ ] Works correctly in Chrome on Linux
- [ ] Works correctly in Chrome on Windows
- [ ] Works correctly in Chrome on macOS
- [ ] Works correctly in Firefox on all platforms
- [ ] Works correctly in Safari on macOS
- [ ] Works correctly in Edge on Windows
- [ ] Board remains usable at 800x600 window size
- [ ] Board scales nicely at 1920x1080
- [ ] AI thinking shows loading indicator
- [ ] Buttons have clear hover/active states
- [ ] No console errors during normal use
- [ ] Error states show user-friendly messages

### Testing Strategy

- Manual browser testing matrix
- Resize browser to various sizes
- Test on actual Windows/Mac/Linux if available
- Verify no JS console errors

---

## Future Enhancements (Not in Initial Scope)

These are explicitly out of scope for the initial 10 phases but
documented for future consideration:

### Near-term Possibilities

1. Drag-and-drop moves - More natural piece movement
2. Move animations - Pieces slide to destination
3. Sound effects - Move sounds, check warnings
4. Keyboard navigation - Arrow keys to move selection

### Medium-term Possibilities

1. WebSocket for AI - Async AI moves with "thinking" indicator
2. Analysis mode - Review games move-by-move with navigation
3. Opening book display - Show opening names
4. Multiple themes - Dark mode, different piece sets, board colors

### Long-term Possibilities

1. Multiplayer over network - Real-time remote play
2. Game export - Download PGN, share links
3. Puzzle mode - Chess puzzles/tactics training
4. ELO tracking - Track improvement over time

---

## Appendix A: HTMX Patterns Used

### Pattern 1: Click to Select/Move

```html
<div class="square"
hx-post="/api/click"
hx-vals='{"square": "e2"}'
hx-target="#board"
hx-swap="outerHTML">
```

### Pattern 2: Out-of-Band Updates

Server response updates multiple elements:

```html
<!-- Primary target -->
<div id="board">...</div>
<div id="status" hx-swap-oob="true">...</div>
<div id="history" hx-swap-oob="true">...</div>
```

### Pattern 3: Confirmation Dialog

```html
<button hx-post="/api/restart"
hx-confirm="Start a new game? Current progress will be lost.">
Restart
</button>
```

### Pattern 4: Form Submission

```html
<form hx-post="/api/games/save" hx-target="#save-result">
<input type="text" name="name" placeholder="Game name">
<button type="submit">Save</button>
</form>
```

---

## Appendix B: CSS Color Scheme

```css
:root {
    /* Board colors - classic wood tones */
    --light-square: #f0d9b5;
    --dark-square: #b58863;
    
    /* Highlight colors */
    --selected: #ffcc00;
    --selected-shadow: rgba(255, 204, 0, 0.6);
    --legal-move: rgba(0, 128, 0, 0.5);
    --last-move-light: #f7ec7a;
    --last-move-dark: #dac34b;
    --check: rgba(255, 0, 0, 0.5);
    
    /* UI colors - dark theme */
    --bg-primary: #312e2b;
    --bg-secondary: #272522;
    --bg-tertiary: #1f1d1b;
    --text-primary: #ffffff;
    --text-secondary: #b0b0b0;
    --text-muted: #737373;
    
    /* Accent colors */
    --accent-primary: #81b64c;
    --accent-hover: #9ece5a;
    --danger: #c33;
    --danger-hover: #d44;
}
```

---

## Appendix C: API Endpoint Summary

| Method | Path | Description |
| ------ | ---- | ----------- |
| GET | `/` | Game mode selection page |
| GET | `/game` | Current game page |
| GET | `/games` | Saved games list page |
| POST | `/api/new-game` | Create new game |
| POST | `/api/select` | Select a square |
| POST | `/api/move` | Execute a move |
| POST | `/api/promote` | Complete pawn promotion |
| POST | `/api/undo` | Undo last move(s) |
| POST | `/api/restart` | Restart current game |
| POST | `/api/quit` | Quit current game |
| POST | `/api/games/save` | Save current game |
| POST | `/api/games/<name>/load` | Load a saved game |
| DELETE | `/api/games/<name>` | Delete a saved game |

---
