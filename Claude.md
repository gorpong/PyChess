# 🧠 Claude.md — Terminal ASCII Chess (Python)

We are building a **terminal-based ASCII Chess game in Python**, designed to be **playable and fun**, but not a full commercial product.

The game strictly follows the official rules and notation standards of real chess.

## Authoritative references

* **Rules**: FIDE Laws of Chess
  [https://handbook.fide.com/chapter/E012023](https://handbook.fide.com/chapter/E012023)
* **Move notation**: Standard Algebraic Notation (SAN)
  [https://en.wikipedia.org/wiki/Algebraic_notation_(chess)](https://en.wikipedia.org/wiki/Algebraic_notation_%28chess%29)
* **Game storage**: Portable Game Notation (PGN)

### Notation clarification (IMPORTANT)

* Individual moves are represented internally and displayed using **Standard Algebraic Notation (SAN)**.
* Complete games are saved and loaded using **PGN (Portable Game Notation)**, which is a container format that includes headers, SAN moves, comments, and metadata.

---

## Core goals

* **Multi-player Chess** (two human players)
* **Single-player Chess vs Computer**

  * Difficulty levels:

    * Easy
    * Medium
    * Hard
    * Expert (optional)
* Written in **Python 3.12+**
* Prioritize **clarity, explicit control flow, and readable loops**
* Use **simple, idiomatic Python**

  * No clever tricks
  * No premature abstractions
* Prefer **small classes / dataclasses** for state
* **Deterministic where possible**

  * Any randomness must be seedable for tests
* The game must feel good:

  * Responsive input
  * Clear highlighting
  * Helpful status messages

---

## Game persistence & logging

### PGN save requirements

Each saved game MUST include at minimum the following PGN headers:

* `Event`
* `Site` (e.g. `"Terminal"`)
* `Date`
* `White`
* `Black`
* `Result` (`1-0`, `0-1`, `1/2-1/2`, or `*`)
* `TimeControl` (use `"-"` if no clock)
* `TotalTimeSeconds` (custom tag, integer)

Additional rules:

* Moves MUST be recorded using **SAN**
* Comments MAY be included using `{}` notation
* Total game time must be tracked and saved, but does **not** need to be displayed

### Save limits

* Up to **10 games** may be stored
* Both complete and incomplete games are allowed
* If the limit is exceeded:

  * The **oldest completed game** is discarded first
  * Incomplete games are preserved preferentially
* If the user quits mid-game:

  * They must be prompted to **name the game**

### Loading saved games

* The game must support:

  * Listing saved games via command-line argument
  * Selecting and loading an incomplete game
* When loading:

  * The board is reconstructed by replaying SAN moves
  * All state (turn, castling rights, en passant, etc.) must be restored

---

## AI difficulty expectations

These are **behavioral constraints**, not strict implementations:

* **Easy**

  * Random legal move selection
* **Medium**

  * Material-based evaluation only
* **Hard**

  * Material + basic positional heuristics
* **Expert (optional)**

  * Depth-limited minimax with alpha-beta pruning

All AI move selection must rely exclusively on the same rules engine used for human move validation.

---

## Input & UX requirements (CRITICAL)

### Gameboard layout

1. Support a **100×44 terminal display**

   * If the terminal is smaller, show an error and exit
   * If larger, center the chessboard
2. Draw a proper chessboard with rank and file labels
3. Use glyphs for pieces if available

   * Otherwise:

     * Uppercase letters for major pieces
     * Lowercase `p` for pawns
4. Use background coloring to clearly distinguish light and dark squares

---

### Keyboard controls

The user may use **any combination** of the following input methods:

#### 1. Algebraic notation input (SAN)

* Accept full SAN, including:

  * Piece designators (`KQBNR`, pawn implied)
  * Captures (`x`)
  * Disambiguation
  * Check (`+`) and mate (`#`)
  * Castling (`O-O`, `O-O-O`)
  * Promotion (`=Q`, `=R`, etc.)
* Disambiguation must be accepted and required when necessary
* If input begins with `- `, treat it as a **PGN comment** for the previous move

---

#### 2. Cursor / keyboard movement (non-notation)

This is the primary keyboard interaction model:

1. Arrow keys move a **cursor**
2. **Enter** on a piece selects it
3. Move cursor to destination
4. **Enter** attempts the move:

   * Legal → commit move
   * Illegal → keep selection and show error
5. **Enter** again on the source square cancels selection

   * `Esc` also cancels
   * Multiplayer: cancel requires opponent confirmation
   * AI (Hard+): cancel is not allowed
6. Highlighting:

   * Cursor always visible
   * Selected piece clearly marked
   * **TAB** shows legal moves:

     * Allowed vs AI (Easy/Medium)
     * Disabled in multiplayer

---

#### 3. Mouse interaction (via `blessed`)

1. Move mouse to a piece
2. Click to select

   * Click-and-release or click-and-hold supported
3. Release attempts move
4. Illegal moves preserve selection and show error
5. Same highlighting rules as keyboard mode

---

### Global keyboard commands

These keys are **never interpreted as files or ranks**:

* `u` → undo

  * vs AI: undo AI move + player move
  * Undo removes moves from board state **and PGN**
* `r` → restart game (board + timers)
* `t` → show total game time (`hh:mm:ss`)
* `?` → help / legend overlay
* `q` or `Esc` → quit (confirmation required)

---

## Minimal feature set (MVP but fun)

1. **Terminal rendering**

   * Grid-based ASCII board
   * Cursor + selection highlighting
   * Status log (last 3–5 messages)
   * All move display in SAN

2. **Input handling**

   * SAN entry
   * Cursor + Enter semantics
   * Mouse support
   * Cancel, undo, quit

3. **Rules engine**

   * Full move legality
   * Check, checkmate, stalemate
   * Castling, en passant, promotion
   * Draw detection (minimum: stalemate)

4. **Quality-of-life**

   * Restart game
   * Help overlay
   * PGN examples overlay
   * Undo (strongly recommended)

---

## Explicit non-goals (v1)

* No network or online play
* No UCI / XBoard engine integration
* No opening books
* No GUI outside the terminal

---

## Technical constraints / requirements

* Provide a proper `.gitignore`
* Provide `pyproject.toml` or equivalent
* Installable as `pychess`
* Use **`blessed`** for terminal UI

  * Rendering must be abstracted behind an interface
* Rendering must be grid-based (no heavy widgets)
* Separation of concerns:

  * **Model** — game state
  * **Rules** — legality, win/draw logic
  * **UI** — rendering, input, cursor, mouse
  * **AI** — move selection only
* All state must be explicit and inspectable

---

## Code quality expectations

* Clear naming
* Minimal globals
* Comments explain *why*, not *what*
* Small, purpose-driven files

---

## Test-Driven Development (MANDATORY)

Strictly follow:

1. **RED** — write tests
2. **GREEN** — minimal pass
3. **REFACTOR** — clean up

Tests must cover:

* Initial board setup
* Move legality
* Check / mate / stalemate
* PGN correctness
* Undo behavior
* Save/load replay accuracy

UI tests may be light.

---

## Output expectations

Start by proposing:

1. A **high-level architecture**
2. A **milestone-based development plan**

Then proceed incrementally.

After each milestone:

* Pause for review
* Provide a **specific commit message**
* Apply fixes as separate commits (`Fix:` prefix)

Ask clarifying questions **only when necessary**; otherwise choose reasonable defaults and document them.

---

## CRITICAL: Post-Milestone Checklist

**STOP after completing each milestone and perform these steps IN ORDER:**

1. ✅ Run all tests and confirm they pass
2. ✅ Update "Milestone Phases" section below with completion status
3. ✅ Update "Implementation Decisions Made" section if any decisions were made
4. ✅ Pause for user review
5. ✅ Create git commit with specific message (after user approval)
6. ✅ Only then proceed to the next milestone

**DO NOT skip these steps. DO NOT proceed to the next milestone without committing.**

---

## Implementation Decisions Made

(Updated continuously as decisions are finalized.)

1. **Immutable data structures**: All model classes (Piece, Color, Square, Board, GameState, CastlingRights, Move) are frozen dataclasses for thread safety and predictability.
2. **Tuple storage with list API**: GameState stores move_history internally as tuple (immutable) but exposes it as list via property (for test compatibility and usability).
3. **Pseudo-legal move generation**: MoveGenerator produces moves that may leave king in check; full legality checking is deferred to validator module.
4. **SAN letter for pawns**: Empty string ("") since pawns don't use a piece letter prefix in SAN notation.

---

## Milestone Phases

### Milestone 1: Project Setup & Core Data Model
**Status:** ✅ COMPLETE (154 tests passing)

- [x] Create `pyproject.toml` with dependencies (`blessed`, `pytest`)
- [x] Create `.gitignore`
- [x] `Piece` enum (KING, QUEEN, ROOK, BISHOP, KNIGHT, PAWN) with SAN letters and Unicode symbols
- [x] `Color` enum (WHITE, BLACK) with `opposite()` method
- [x] `Square` dataclass with file/rank validation, algebraic notation parsing
- [x] `Board` class with initial position setup, immutable operations
- [x] `GameState` dataclass (board, turn, castling rights, en passant, clocks, move history)
- [x] `CastlingRights` dataclass with revoke methods

**Files created:**
- `pyproject.toml`, `.gitignore`
- `src/pychess/__init__.py`, `src/pychess/main.py`
- `src/pychess/model/__init__.py`, `piece.py`, `square.py`, `board.py`, `game_state.py`
- `tests/__init__.py`, `tests/model/__init__.py`
- `tests/model/test_piece.py` (41 tests)
- `tests/model/test_square.py` (43 tests)
- `tests/model/test_board.py` (38 tests)
- `tests/model/test_game_state.py` (32 tests)

---

### Milestone 2: Basic Move Representation & Generation
**Status:** ✅ COMPLETE (227 tests passing)

- [x] `Move` dataclass (from_square, to_square, promotion, is_castling, is_en_passant, is_capture)
- [x] Pawn move generation (single/double push, captures, en passant, promotion)
- [x] Knight move generation (L-shape jumps)
- [x] Bishop move generation (diagonal sliding)
- [x] Rook move generation (orthogonal sliding)
- [x] Queen move generation (bishop + rook combined)
- [x] King move generation (single step + castling candidates)

**Files created:**
- `src/pychess/rules/__init__.py`, `move.py`, `move_generator.py`
- `tests/rules/__init__.py`, `test_move.py` (24 tests), `test_move_generator.py` (49 tests)
- `tests/conftest.py` (shared fixtures)

---

### Milestone 3: Move Validation & Check Detection
**Status:** ✅ COMPLETE (265 tests passing)

**Goal:** Filter pseudo-legal moves to only legal moves; detect check.

**Tasks:**
- [x] Create `src/pychess/rules/validator.py`
- [x] Implement `is_square_attacked(board, square, by_color)` - checks if any piece of `by_color` attacks the square
- [x] Implement `is_in_check(board, color)` - checks if the king of `color` is in check
- [x] Implement `is_move_legal(game_state, move)` - validates move doesn't leave own king in check
- [x] Implement `get_legal_moves(game_state)` - returns all legal moves for current player
- [x] Add castling validation: king cannot castle out of, through, or into check
- [x] Add en passant validation: cannot expose king to check
- [x] Create `tests/rules/test_validator.py` with comprehensive tests (38 tests)

**Test cases include:**
- Basic check detection (single attacker)
- Multiple attackers (double check)
- Pinned pieces cannot move off pin line (can only move along pin line)
- King cannot move into check
- Blocking check with piece
- Capturing attacking piece
- Castling blocked by check/attack on traversal squares
- En passant discovered check edge case

**Files created:**
- `src/pychess/rules/validator.py`
- `tests/rules/test_validator.py` (38 tests)
- Updated `src/pychess/rules/__init__.py` to export validator functions

---

### Milestone 4: Game End Conditions
**Status:** ⏳ PENDING

**Goal:** Detect checkmate, stalemate, and draw conditions.

**Tasks:**
- [ ] Create `src/pychess/rules/game_logic.py`
- [ ] Implement `is_checkmate(game_state)` - in check with no legal moves
- [ ] Implement `is_stalemate(game_state)` - not in check but no legal moves
- [ ] Implement `is_fifty_move_rule(game_state)` - halfmove_clock >= 100
- [ ] Implement `is_threefold_repetition(game_state)` - requires position hashing
- [ ] Implement `is_insufficient_material(board)` - K vs K, K+B vs K, K+N vs K, K+B vs K+B (same color bishops)
- [ ] Implement `get_game_result(game_state)` - returns "1-0", "0-1", "1/2-1/2", or None (ongoing)
- [ ] Add position hash to GameState for repetition detection
- [ ] Create `tests/rules/test_game_logic.py`

**Test cases must include:**
- Fool's mate (fastest checkmate)
- Scholar's mate
- Back rank mate
- Smothered mate
- Stalemate positions
- Fifty-move rule trigger
- Threefold repetition
- All insufficient material combinations

**Files to create:**
- `src/pychess/rules/game_logic.py`
- `tests/rules/test_game_logic.py`

---

### Milestone 5: SAN Notation
**Status:** ⏳ PENDING

**Goal:** Parse and generate Standard Algebraic Notation for moves.

**Tasks:**
- [ ] Create `src/pychess/notation/san.py`
- [ ] Implement `move_to_san(game_state, move)` - generates SAN string from Move
- [ ] Implement `san_to_move(game_state, san_string)` - parses SAN string to Move
- [ ] Handle piece letters: K, Q, R, B, N (pawn has no letter)
- [ ] Handle captures: 'x' notation
- [ ] Handle disambiguation: file, rank, or both when multiple pieces can reach same square
- [ ] Handle check '+' and checkmate '#' suffixes
- [ ] Handle castling: O-O (kingside), O-O-O (queenside)
- [ ] Handle promotion: =Q, =R, =B, =N
- [ ] Handle en passant (standard capture notation, target square)
- [ ] Create `tests/notation/test_san.py`

**Test cases must include:**
- Simple pawn moves: e4, d5
- Pawn captures: exd5
- Piece moves: Nf3, Bb5
- Piece captures: Bxc6
- Disambiguation by file: Rad1, Rfd1
- Disambiguation by rank: R1d2, R8d2
- Disambiguation by both: Qh4e1
- Castling both sides
- Promotion: e8=Q
- Promotion with capture: exd8=N
- Check notation: Bb5+
- Checkmate notation: Qxf7#

**Files to create:**
- `src/pychess/notation/__init__.py`
- `src/pychess/notation/san.py`
- `tests/notation/__init__.py`
- `tests/notation/test_san.py`

---

### Milestone 6: PGN Persistence
**Status:** ⏳ PENDING

**Goal:** Save and load games in PGN format.

**Tasks:**
- [ ] Create `src/pychess/notation/pgn.py`
- [ ] Implement PGN header serialization with required tags:
  - Event, Site, Date, White, Black, Result, TimeControl, TotalTimeSeconds
- [ ] Implement PGN move text serialization (move pairs with numbers)
- [ ] Implement PGN comment serialization using `{}` notation
- [ ] Implement PGN parsing (headers + moves)
- [ ] Implement `game_to_pgn(game_state, headers)` - serialize to PGN string
- [ ] Implement `pgn_to_game(pgn_string)` - parse PGN and replay moves to restore state
- [ ] Create `src/pychess/persistence/save_manager.py`
- [ ] Implement 10-game storage limit with eviction policy (oldest completed first)
- [ ] Implement game listing for CLI
- [ ] Implement game loading by name
- [ ] Create `tests/notation/test_pgn.py`
- [ ] Create `tests/persistence/test_save_manager.py`

**PGN Format Example:**
```
[Event "Casual Game"]
[Site "Terminal"]
[Date "2024.01.15"]
[White "Player1"]
[Black "Computer"]
[Result "1-0"]
[TimeControl "-"]
[TotalTimeSeconds "342"]

1. e4 e5 2. Nf3 Nc6 3. Bb5 {Spanish Game} a6 4. Ba4 Nf6 1-0
```

**Files to create:**
- `src/pychess/notation/pgn.py`
- `src/pychess/persistence/__init__.py`
- `src/pychess/persistence/save_manager.py`
- `tests/notation/test_pgn.py`
- `tests/persistence/__init__.py`
- `tests/persistence/test_save_manager.py`

---

### Milestone 7: Basic Terminal UI
**Status:** ⏳ PENDING

**Goal:** Render board and accept SAN input using `blessed` library.

**Tasks:**
- [ ] Create `src/pychess/ui/renderer.py` - abstract renderer interface
- [ ] Create `src/pychess/ui/terminal.py` - blessed-based implementation
- [ ] Create `src/pychess/ui/board_view.py` - board drawing logic
- [ ] Implement terminal size detection (100x44 minimum)
- [ ] Implement board rendering with rank/file labels
- [ ] Implement piece rendering (Unicode glyphs with ASCII fallback)
- [ ] Implement light/dark square background colors
- [ ] Implement status message area (last 3-5 messages)
- [ ] Implement SAN text input field
- [ ] Create basic game loop (alternating turns)
- [ ] Center board for larger terminals

**Files to create:**
- `src/pychess/ui/__init__.py`
- `src/pychess/ui/renderer.py`
- `src/pychess/ui/terminal.py`
- `src/pychess/ui/board_view.py`

---

### Milestone 8: Cursor & Selection System
**Status:** ⏳ PENDING

**Goal:** Arrow key navigation and Enter-based piece selection.

**Tasks:**
- [ ] Create `src/pychess/ui/cursor.py` - cursor state management
- [ ] Create `src/pychess/ui/input_handler.py` - keyboard input processing
- [ ] Implement cursor rendering (highlight current square)
- [ ] Implement arrow key movement (wrapping at edges optional)
- [ ] Implement Enter to select piece (validate own piece)
- [ ] Implement Enter on destination to attempt move
- [ ] Implement Enter on source square to cancel selection
- [ ] Implement Escape to cancel selection
- [ ] Implement selected piece highlighting (different from cursor)
- [ ] Implement illegal move error display

**Files to create:**
- `src/pychess/ui/cursor.py`
- `src/pychess/ui/input_handler.py`

---

### Milestone 9: Mouse Support
**Status:** ⏳ PENDING

**Goal:** Click-based piece movement using blessed mouse events.

**Tasks:**
- [ ] Add mouse event handling to input_handler.py
- [ ] Implement click-to-select piece
- [ ] Implement click-on-destination to move
- [ ] Implement drag-and-drop (click-hold-release)
- [ ] Share highlighting logic with keyboard mode
- [ ] Handle mouse position to board square conversion

---

### Milestone 10: Global Commands & UX Polish
**Status:** ⏳ PENDING

**Goal:** Implement undo, restart, help, quit, and other UX features.

**Tasks:**
- [ ] Implement undo logic in game state (restore previous state, update move history)
- [ ] Implement `u` key for undo
- [ ] Implement `r` key for restart (with confirmation)
- [ ] Implement `t` key for time display (hh:mm:ss format)
- [ ] Implement `?` key for help overlay
- [ ] Create `src/pychess/ui/overlays.py` for help, PGN examples
- [ ] Implement `q`/`Esc` for quit (with confirmation, save prompt)
- [ ] Implement `- ` prefix for adding PGN comments to previous move
- [ ] Implement promotion dialog UI (select Q/R/B/N)
- [ ] Track total game time

**Files to create:**
- `src/pychess/ui/overlays.py`

---

### Milestone 11: AI - Easy & Medium
**Status:** ⏳ PENDING

**Goal:** Single-player against basic AI opponents.

**Tasks:**
- [ ] Create `src/pychess/ai/__init__.py`
- [ ] Create `src/pychess/ai/engine.py` - AI interface and difficulty dispatcher
- [ ] Create `src/pychess/ai/evaluation.py` - shared evaluation functions
- [ ] Create `src/pychess/ai/easy.py` - random legal move selection
- [ ] Create `src/pychess/ai/medium.py` - material-based evaluation
- [ ] Implement seedable randomness for deterministic testing
- [ ] Integrate AI into game loop
- [ ] Implement undo vs AI (undo both AI + player moves)
- [ ] Add game mode selection (multiplayer vs AI + difficulty)
- [ ] Create `tests/ai/test_easy.py`
- [ ] Create `tests/ai/test_medium.py`

**Material values (standard):**
- Pawn: 1
- Knight: 3
- Bishop: 3
- Rook: 5
- Queen: 9
- King: 0 (infinite, not captured)

**Files to create:**
- `src/pychess/ai/__init__.py`
- `src/pychess/ai/engine.py`
- `src/pychess/ai/evaluation.py`
- `src/pychess/ai/easy.py`
- `src/pychess/ai/medium.py`
- `tests/ai/__init__.py`
- `tests/ai/test_easy.py`
- `tests/ai/test_medium.py`

---

### Milestone 12: AI - Hard
**Status:** ⏳ PENDING

**Goal:** Positional evaluation for stronger AI play.

**Tasks:**
- [ ] Create `src/pychess/ai/hard.py`
- [ ] Implement piece-square tables for positional scoring
- [ ] Combine material + positional evaluation
- [ ] Implement move ordering for better play
- [ ] Implement cancel restriction for Hard+ difficulty
- [ ] Create `tests/ai/test_hard.py`

**Piece-square table concepts:**
- Pawns: value center control, advancement
- Knights: value center squares, penalize edges
- Bishops: value diagonals, penalize blocked
- Rooks: value open files, 7th rank
- Queen: slightly prefer center early
- King: castle early (corners), centralize in endgame

**Files to create:**
- `src/pychess/ai/hard.py`
- `tests/ai/test_hard.py`

---

### Milestone 13: Legal Move Hints & Polish
**Status:** ⏳ PENDING

**Goal:** TAB highlighting of legal moves and final UX refinements.

**Tasks:**
- [ ] Implement TAB to show legal moves for selected piece
- [ ] Enable hints only vs AI (Easy/Medium)
- [ ] Disable hints in multiplayer mode
- [ ] Implement multiplayer cancel confirmation
- [ ] Final UI polish and edge case handling
- [ ] Ensure all highlighting states render correctly

---

### Milestone 14: Integration & CLI
**Status:** ⏳ PENDING

**Goal:** Complete application with full CLI interface.

**Tasks:**
- [ ] Create `src/pychess/controller/__init__.py`
- [ ] Create `src/pychess/controller/game_controller.py` - main game orchestration
- [ ] Update `src/pychess/main.py` with CLI argument parsing
- [ ] Implement `--list-games` to show saved games
- [ ] Implement `--load <name>` to load a saved game
- [ ] Implement game mode selection menu
- [ ] Create end-to-end integration tests
- [ ] Final documentation and README updates

**CLI interface:**
```
pychess                    # Start new game (mode selection menu)
pychess --list-games       # List saved games
pychess --load "Game 1"    # Load saved game
pychess --help             # Show help
```

**Files to create:**
- `src/pychess/controller/__init__.py`
- `src/pychess/controller/game_controller.py`

---
