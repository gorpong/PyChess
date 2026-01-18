# Instructions for Agentic Coding Models

We are building a **terminal-based ASCII Chess game in Python**, designed to be
**playable and fun**, but not a full commercial product.  The game strictly follows
the official rules and notation standards of real chess.

## Core Goals

* **Multi-player Chess** (two human players)
* **Single-player Chess vs Computer**
  * Difficulty levels:
    * Easy
    * Medium
    * Hard
    * Expert (optional)
* Written in **Python 3.11+**
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

## Non-Goals

* Graphical UI
* Network features
* Monetization

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

## Technology Constraints

* Language: Python 3.11+
* Platform: Terminal (ANSI / curses)
* No external game engines
* Standard library preferred
* Individual moves are represented internally and displayed using **Standard Algebraic Notation (SAN)**.
* Complete games are saved and loaded using **PGN (Portable Game Notation)**, which is a container format that includes headers, SAN moves, comments, and metadata.

### Development Process

* Use test-driven development with RED+GREEN states when developing new code
* Work in small, reviewable steps
* Do not commit without explicit user approval
* Include as part of the approval seeking process the proposed commit message
* Present a plan before writing any code > 15 lines long
  * The plan must include a summary of the goals for the code
  * The plan must include a list of files to be modified
  * The plan must include how the changes will be tested/verified
* Ask for assistance if working on a bug-fix and you cannot determine the root cause
* If a post-commit fix is required, label it clearly as a fix and describe the problem

### Code Style

* Favor clarity over cleverness
* Explicit control flow over abstraction
* Small, single-purpose functions
* No premature optimization
* Game state must be isolated from rendering
* Input handling must not mutate state directly

### Game Rules

Gameplay must follow the FIDE Laws of Chess [https://handbook.fide.com/chapter/E012023](https://handbook.fide.com/chapter/E012023)

Move notation must follow the Standard Algebraic Notation (SAN) specification [https://en.wikipedia.org/wiki/Algebraic_notation_(chess)](https://en.wikipedia.org/wiki/Algebraic_notation_%28chess%29)

Game storage must follow the Portable Game Notation (PGN) specification [https://en.wikipedia.org/wiki/Algebraic_notation_(chess)](https://en.wikipedia.org/wiki/Algebraic_notation_%28chess%29)

### Agent Behavior

* Do not invent rules or mechanics
* Ask clarification questions when uncertain
* Do not refactor unrelated code
* Do not change public interfaces without approval

### Expected Outputs

* Clear explanations to the user before implementing new code for new features:
  * Must describe any classes that will be modified/created/removed
  * Must describe any methods that will be modified/created/removed
  * Must describe any APIs that will be modified/created/removed
* Minimal but sufficient comments
* Tests included where logic is non-trivial
* No placeholder TODOs without explanation
