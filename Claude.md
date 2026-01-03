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

## Implementation Decisions Made

(Updated continuously as decisions are finalized.)

---

## Milestone Phases

(Updated as milestones are completed.)

---
