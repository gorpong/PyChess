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
**Status:** ✅ COMPLETE (308 tests passing)

**Goal:** Detect checkmate, stalemate, and draw conditions.

**Tasks:**
- [x] Create `src/pychess/rules/game_logic.py`
- [x] Implement `is_checkmate(game_state)` - in check with no legal moves
- [x] Implement `is_stalemate(game_state)` - not in check but no legal moves
- [x] Implement `is_fifty_move_rule(game_state)` - halfmove_clock >= 100
- [x] Implement `is_threefold_repetition(game_state)` - requires position hashing
- [x] Implement `is_insufficient_material(board)` - K vs K, K+B vs K, K+N vs K, K+B vs K+B (same color bishops)
- [x] Implement `get_game_result(game_state)` - returns "1-0", "0-1", "1/2-1/2", or None (ongoing)
- [x] Add position hash to GameState for repetition detection
- [x] Create `tests/rules/test_game_logic.py` (43 tests)

**Test cases include:**
- Fool's mate (fastest checkmate)
- Scholar's mate
- Back rank mate
- Smothered mate
- Stalemate positions (basic, king in corner, with blocked pawn)
- Fifty-move rule trigger
- Threefold repetition
- All insufficient material combinations

**Files created:**
- `src/pychess/rules/game_logic.py`
- `tests/rules/test_game_logic.py` (43 tests)
- Updated `src/pychess/model/game_state.py` with position_hash and position_history
- Updated `src/pychess/rules/__init__.py` to export game_logic functions

---

### Milestone 5: SAN Notation
**Status:** ✅ COMPLETE (369 tests passing)

**Goal:** Parse and generate Standard Algebraic Notation for moves.

**Tasks:**
- [x] Create `src/pychess/notation/san.py`
- [x] Implement `move_to_san(game_state, move)` - generates SAN string from Move
- [x] Implement `san_to_move(game_state, san_string)` - parses SAN string to Move
- [x] Handle piece letters: K, Q, R, B, N (pawn has no letter)
- [x] Handle captures: 'x' notation
- [x] Handle disambiguation: file, rank, or both when multiple pieces can reach same square
- [x] Handle check '+' and checkmate '#' suffixes
- [x] Handle castling: O-O (kingside), O-O-O (queenside)
- [x] Handle promotion: =Q, =R, =B, =N
- [x] Handle en passant (standard capture notation, target square)
- [x] Create `tests/notation/test_san.py`

**Test cases include:**
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

**Files created:**
- `src/pychess/notation/__init__.py`
- `src/pychess/notation/san.py`
- `tests/notation/__init__.py`
- `tests/notation/test_san.py`

---

### Milestone 6: PGN Persistence
**Status:** ✅ COMPLETE (369 tests passing)

**Goal:** Save and load games in PGN format.

**Tasks:**
- [x] Create `src/pychess/notation/pgn.py`
- [x] Implement PGN header serialization with required tags:
  - Event, Site, Date, White, Black, Result, TimeControl, TotalTimeSeconds
- [x] Implement PGN move text serialization (move pairs with numbers)
- [x] Implement PGN comment serialization using `{}` notation
- [x] Implement PGN parsing (headers + moves)
- [x] Implement `game_to_pgn(game_state, headers)` - serialize to PGN string
- [x] Implement `pgn_to_game(pgn_string)` - parse PGN and replay moves to restore state
- [x] Create `tests/notation/test_pgn.py`
- [x] Create `tests/persistence/__init__.py` directory structure

**Note:** `save_manager.py` not yet implemented - will be created in a future milestone when CLI integration is complete.

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

**Files created:**
- `src/pychess/notation/pgn.py`
- `src/pychess/persistence/__init__.py`
- `tests/notation/test_pgn.py`
- `tests/persistence/__init__.py`

**Files deferred:**
- `src/pychess/persistence/save_manager.py` - to be implemented with CLI integration
- `tests/persistence/test_save_manager.py` - to be implemented with save_manager

---

### Milestone 7: Basic Terminal UI
**Status:** ✅ COMPLETE (369 tests passing)

**Goal:** Render board and accept SAN input using `blessed` library.

**Tasks:**
- [x] Create `src/pychess/ui/renderer.py` - abstract renderer interface
- [x] Create `src/pychess/ui/terminal.py` - blessed-based implementation
- [x] Create `src/pychess/ui/board_view.py` - board drawing logic
- [x] Implement terminal size detection (100x44 minimum)
- [x] Implement board rendering with rank/file labels
- [x] Implement piece rendering (Unicode glyphs with ASCII fallback)
- [x] Implement light/dark square background colors
- [x] Implement status message area (last 5 messages)
- [x] Implement SAN text input field
- [x] Create basic game loop (alternating turns)
- [x] Center board for larger terminals
- [x] Update main.py with functional game loop

**Features implemented:**
- Abstract `Renderer` interface for separation of concerns
- `TerminalRenderer` using blessed library with full color support
- `BoardView` with Unicode chess piece symbols and ASCII fallback
- Board rendering with 6x3 character squares for visibility
- Background colors: white/gray for light/dark squares
- Highlighting: yellow for cursor, cyan for selection, green for legal moves
- Status area showing: current turn, move history (last 5 moves), status messages
- Input area with prompt and help text
- Basic commands: q=quit, u=undo (placeholder), r=restart, ?=help
- Full SAN move parsing and execution
- Game end detection (checkmate, stalemate, draw)
- Error handling and validation

**Files created:**
- `src/pychess/ui/__init__.py`
- `src/pychess/ui/renderer.py`
- `src/pychess/ui/terminal.py`
- `src/pychess/ui/board_view.py`
- Updated `src/pychess/main.py` with game loop

**Note:** The game is now playable with SAN input! Cursor/keyboard movement and mouse support will be added in Milestone 8.

---

### Milestone 8: Cursor & Selection System
**Status:** ✅ COMPLETE (369 tests passing)

**Goal:** Arrow key navigation and Enter-based piece selection.

**Tasks:**
- [x] Create `src/pychess/ui/cursor.py` - cursor state management
- [x] Create `src/pychess/ui/input_handler.py` - keyboard input processing
- [x] Implement cursor rendering (highlight current square)
- [x] Implement arrow key movement (no wrapping at edges)
- [x] Implement Enter to select piece (validates own piece)
- [x] Implement Enter on destination to attempt move
- [x] Implement Escape to cancel selection
- [x] Implement selected piece highlighting (cyan background)
- [x] Implement cursor highlighting (yellow background)
- [x] Implement legal move highlighting (green background)
- [x] Implement illegal move error display
- [x] Update main game loop to use cursor-based input

**Features implemented:**
- `CursorState` dataclass for managing cursor position and selection
- Arrow key navigation (up/down/left/right)
- Enter key selection mechanics:
  - First Enter: Select piece (validates it's your piece)
  - Second Enter: Attempt move to cursor position
  - Enter on empty square: Clear selection
- Escape key to cancel selection
- Visual feedback:
  - Yellow highlight: Current cursor position
  - Cyan highlight: Selected piece
  - Green highlight: Legal destination squares for selected piece
- Automatic legal move calculation and highlighting
- Error messages for invalid selections and illegal moves
- Command keys: q (quit), r (restart), u (undo), ? (help)

**Files created:**
- `src/pychess/ui/cursor.py`
- `src/pychess/ui/input_handler.py`
- Updated `src/pychess/ui/terminal.py` with cursor mode support
- Updated `src/pychess/main.py` with cursor-based game loop

**Note:** The game now supports intuitive cursor-based navigation! Use arrow keys to move, Enter to select and move pieces. Legal moves are highlighted in green when a piece is selected.

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
**Status:** ✅ COMPLETE (369 tests passing)

**Goal:** Implement undo, restart, help, quit, and other UX features.

**Tasks:**
- [x] Implement undo logic (restore previous state from history)
- [x] Implement `u` key for undo in both cursor and SAN modes
- [x] Implement `r` key for restart with state history reset
- [x] Implement `?` key for help overlay
- [x] Create `src/pychess/ui/overlays.py` for help display
- [x] Implement `q`/`Esc` for quit with confirmation
- [x] Clear state history on restart

**Features implemented:**
- Full undo functionality with state history tracking
- Undo works in both cursor and SAN input modes
- Help overlay with comprehensive game instructions:
  - Cursor mode controls
  - SAN input mode examples
  - Global commands reference
  - SAN notation guide with examples
- Restart clears all history
- Quit confirmation dialog

**Files created:**
- `src/pychess/ui/overlays.py`
- Updated `src/pychess/main.py` with undo and help systems

**Deferred features:**
- Time display (t key) - will add in future milestone
- PGN comments - will add with save/load functionality
- Promotion dialog - currently auto-handled via SAN
- Game time tracking - future enhancement

---

### Milestone 11: AI - Easy, Medium & Hard
**Status:** ✅ COMPLETE (369 tests passing)

**Goal:** Single-player against AI opponents at multiple difficulty levels.

**Tasks:**
- [x] Create `src/pychess/ai/__init__.py`
- [x] Create `src/pychess/ai/engine.py` - AI interface and difficulty dispatcher
- [x] Create `src/pychess/ai/evaluation.py` - evaluation functions
- [x] Implement Easy difficulty - random legal move selection
- [x] Implement Medium difficulty - material-based evaluation
- [x] Implement Hard difficulty - material + positional evaluation
- [x] Implement seedable randomness for deterministic testing
- [x] Integrate AI into game loop (plays as Black after White's move)
- [x] Add game mode selection menu at startup
- [x] Undo works correctly with AI (undoes last player move)

**Features implemented:**
- **AIEngine class** with three difficulty levels:
  - Easy: Random move selection
  - Medium: Material-based evaluation (captures, promotions)
  - Hard: Material + positional heuristics (center control, pawn advancement)
- **Evaluation system** with:
  - Standard piece values (P=100, N=320, B=330, R=500, Q=900)
  - Material balance calculation
  - Positional bonuses for center control
  - Pawn advancement scoring
- **Game mode selection menu** at startup:
  - Option 1: Multiplayer (two humans)
  - Option 2: vs AI - Easy
  - Option 3: vs AI - Medium
  - Option 4: vs AI - Hard
- **AI integration**:
  - AI plays automatically as Black after White moves
  - "AI is thinking..." status message
  - Displays both player and AI moves
  - Works in both cursor and SAN input modes

**Material values implemented:**
- Pawn: 100 (base unit)
- Knight: 320
- Bishop: 330
- Rook: 500
- Queen: 900
- King: 0 (invaluable)

**Files created:**
- `src/pychess/ai/__init__.py`
- `src/pychess/ai/engine.py`
- `src/pychess/ai/evaluation.py`
- Updated `src/pychess/main.py` with mode selection and AI integration

**Note:** You can now play chess against the computer! The AI provides a good challenge at Medium and Hard difficulties.

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
**Status:** ✅ COMPLETE (396 tests passing)

**Goal:** TAB highlighting of legal moves and final UX refinements.

**Tasks:**
- [x] Implement TAB to show legal moves for selected piece
- [x] Enable hints only vs AI (Easy/Medium)
- [x] Disable hints in multiplayer mode
- [x] Implement multiplayer cancel confirmation
- [x] Final UI polish and edge case handling
- [x] Ensure all highlighting states render correctly

**Features implemented:**
- **TAB key hint system:**
  - Press TAB after selecting a piece to show legal moves (green highlighting)
  - Press TAB again to hide hints
  - Hints automatically clear when selection changes
  - Hints only available in AI Easy/Medium modes (teaching/learning modes)
  - Disabled in Multiplayer and AI Hard modes for competitive play
- **Multiplayer cancel confirmation:**
  - In multiplayer mode, pressing Escape once shows "Press Escape again to cancel"
  - Second Escape confirms and clears selection
  - Prevents accidental deselection during two-player games
  - AI modes use immediate cancel (no confirmation needed)
- **CursorState enhancements:**
  - Added `show_hints` field for hint visibility tracking
  - Added `pending_cancel` field for cancel confirmation state
  - Added `toggle_hints()`, `clear_hints()` methods
  - Added `request_cancel()`, `confirm_cancel()`, `deny_cancel()` methods
  - Hints and pending_cancel preserved during cursor movement
  - Both cleared on selection change or cancel
- **InputHandler enhancements:**
  - Added `SHOW_HINTS` input type for TAB key
- **Help overlay updated:**
  - Documents TAB key for hints
  - Documents Escape behavior in multiplayer mode

**Behavior summary:**
- **AI Easy/Medium mode:** Select piece → Press TAB → See legal moves in green
- **Multiplayer mode:** Select piece → Press Escape → "Press again to cancel" → Escape confirms
- **AI Hard mode:** No hints available, immediate cancel

**Files created/modified:**
- `src/pychess/ui/cursor.py` - added show_hints, pending_cancel fields and methods
- `src/pychess/ui/input_handler.py` - added SHOW_HINTS input type and TAB handling
- `src/pychess/ui/overlays.py` - updated help text for TAB and Escape
- `src/pychess/main.py` - integrated hint toggle and cancel confirmation
- `tests/ui/__init__.py` - new test package
- `tests/ui/test_cursor.py` - 9 tests for hint functionality
- `tests/ui/test_input_handler.py` - 6 tests for input handling
- `tests/ui/test_game_mode.py` - 12 tests for mode-specific behaviors

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
