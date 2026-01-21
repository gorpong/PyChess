# Instructions for Agentic Coding Models

We are building a **terminal-based ASCII Chess game in Python**, designed to be
**playable and fun**, but not a full commercial product.  The game strictly follows
the official rules and notation standards of real chess.

## Core Goals

There's a number of goals we need to get with this. It should be a game that is
both multi-player (two human players) and single-player against the computer.
The AI for the computer should have at least 3 levels, with Easy, Medium and Hard,
but a stretch goal would be for an Expert level.

We are writing this in Python, version 3.11+ and prioritizing clarity, explicit
control flow and, most importantly, readable loops. We use simple, idiomatic Python,
so don't want any clever tricks or premature abstractions. We want small classes
and prefer dataclasses if we're dealing with state information. The code should
be deterministic where possible, and if there's any randomness, then it needs to
be seedable so we can test it consistently.  

Most importantly, the game must "feel good" to the players, which means the input
needs to be responsive, clear highlighting of selection points, obvious help text,
and helpful status messages at certain times.

We don't want any sort of Graphical UI, this is all a text-based game that can run
on Linux and Windows in Python. We don't care about networking features, so no sort
of multi-player games over a network (although, that might be something we can add
at a future time, so don't rule it out entirely). At no point do we want any sort
of monetization, so even if we add networking features at some point, it will
never need to support any sort of in-game purchase or anything like that.

## Game persistence & logging

We need to be able to save the game, and the save file should be in PGN format.
Portable Game Notation is a container format that includes headers, SAN moves,
(Standard Algebraic Notation) comments, and metadata. Each saved game MUST
include at minimum the following PGN headers:

* `Event`
* `Site` (e.g. `"Terminal"`)
* `Date`
* `White`
* `Black`
* `Result` (`1-0`, `0-1`, `1/2-1/2`, or `*`)
* `TimeControl` (use `"-"` if no clock)
* `TotalTimeSeconds` (custom tag, integer)

Other ones are optional, since the PGN spec supports them, but every saved game
must include at least these.

In the PGN file, all moves have to be recorced using SAN. You can include
optional comments by using the `{}` notation, which is supported in SAN.
The total time spent playing the game needs to be tracked and saved in
the file, but the timing inforamtion doesn't need to be displayed, as that
would likely be very disruptive redrawing the entire game board just for
the second-by-second update.

### Save limits

We want to be able to save up to 10 games, and we need to be able to save
complete and incomplete games. If the limit is exceeded then it's okay to
discard one, and we should discard the oldest, completed game before any of
the in-progress ones. If there are only in-progress games, then pick the
oldest saved one, just like completed. If the user is quitting the game in
the middle, then they must be prompted to name the game for saving.

### Loading saved games

It's important that the user be able to list the existing games with a command
line argument. They should also be able to select and load an incomplete game.
When loading the game, the board must be reconstructed by replaing the SAN moves.
All state information (e.g., turn, castling rights, en passant, etc.) must be
restored properly.

## Technology Constraints

* Language: Python 3.11+
* Platform: Terminal (ANSI / curses)
* No external game engines
* Standard library preferred

### Development Process

We need to use the test-driven development where tests are created before code
and they are designed to fail until the proper implementation is done. We can't
just make tests that match the existing code, so if the test created fails after
the code has been created, it's important to ensure we only update the test once
we've verified there's a real problem with the test. Tests created first are to
help drive the development process and test the edge cases before we actually
build the code, so it's more likely the code wasn't done correctly rather than
the test being wrong, so only update the test after verifying by looking at the
code being tested to ensure there's a problem with the way the test is written.

We need to work in small, reviewable steps, such that we're only implementing a
single feature or single bug-fix in each code development cycle. No code should
be commited without explicit user approval, which needs to include a proposed
commit message which also needs to be approved. Be sure to present a plan before
writing any code > 15 lines long. That plan needs to include a summary of the
goals for the code, a complete list of files to be modified/created, details on
how the changes being made will be tested and/or verified, and the plan needs to
be approved before writing any code.

If working on a bug-fix and the root cause isn't immediately obvious, it's important
to ask for assistance rather than just making assumptions. If a post-commit fix
is required, label it clearly as a fix and describe the problem deatils.

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

* Clear explanations to the user with approval before implementing new code for new features:
  * Must describe any classes that will be modified/created/removed
  * Must describe any methods that will be modified/created/removed
  * Must describe any APIs that will be modified/created/removed
  * If the new feature is listed as a milestone, be sure to update the MILESTONES.md file after it's implemented
* Minimal but sufficient comments
* Tests included where logic is non-trivial
* No placeholder TODOs without explanation
