# PyChess - Terminal ASCII Chess

A fully-featured, beautiful terminal-based chess game written in Python. Play chess right in your terminal with Unicode pieces, color-coded squares, and full chess rules implementation.

## Features

- ✨ **Beautiful Terminal UI** - Color-coded board with Unicode chess pieces
- ♟️ **Full Chess Rules** - Complete implementation of official FIDE rules
- 📝 **Standard Algebraic Notation (SAN)** - Industry-standard move notation
- 💾 **PGN Support** - Save and load games in Portable Game Notation format
- 🎮 **Multiple Game Modes** - Play multiplayer or against AI
- 🤖 **AI Opponents** - Three difficulty levels (Easy, Medium, Hard)
- 🎯 **Dual Input Modes** - Cursor navigation or SAN text input
- 🔄 **Undo/Redo** - Full move history with unlimited undo
- ❓ **Help System** - Comprehensive in-game help overlay
- 🏁 **Complete Game Logic** - Checkmate, stalemate, draws, en passant, castling, promotion
- 📊 **Move History** - Track all moves in SAN notation
- ⚡ **Fast & Responsive** - Lightweight and instant feedback

## Installation

### Pre-Requisite (e.g., Python and Git on Windows, Linux should have pre-installed)

These instructions are for **Windows users who just want to play the game**.

You only need to do this setup **once**.

---

### Step 1: Install Python for Windows

1. Go to:
   👉 [https://www.python.org/downloads/windows/](https://www.python.org/downloads/windows/)

2. Download **Python 3.12 (64-bit)**

3. Run the installer and **IMPORTANT**:

   - ✅ Check **“Add Python to PATH”**
   - Click **Install Now**

4. After installation, open **Command Prompt** and verify:

   ```bat
   python --version
   ```

   You should see something like:

   ```text
   Python 3.12.x
   ```

---

### Step 2: Install Git for Windows

1. Go to:
   👉 [https://git-scm.com/download/win](https://git-scm.com/download/win)

2. Run the installer

   - Default options are fine
   - This gives you **Git Bash** and `git` in Command Prompt

3. Verify installation:

   ```bat
   git --version
   ```

---

### Step 3: Download the Game

Open **Command Prompt** (or Git Bash) and run:

```bat
git clone https://github.com/gorpong/PyChess
cd PyChess
```

---

### Step 4: Install the Game (One-Time)

This installs PyChess like a normal program.

```bat
python -m pip install .
```

That’s it! 🎉
The `pychess` command is now available system-wide.

---

### Step 5: Play the Game

From **any Command Prompt**:

```bat
pychess
```

The game menu will appear immediately.

```bat
pychess --help
```

Will show you to command line options for launching saved games, etc.

---

### ❓ Troubleshooting (Windows)

**If `pychess` is not found:**

```bat
python -m pip install --upgrade pip
python -m pip install .
```

**If Unicode chess pieces look wrong:**

- Use **Windows Terminal** (recommended)
- Or increase font size
- Or try a font like *Cascadia Mono* or *Consolas*

## Requirements (Linux/UNIX and Windows)

- Python 3.12 or higher
- Terminal with Unicode support (most modern terminals)
- Minimum terminal size: 100x44 characters

### Install from source

```bash
# Clone the repository
git clone https://github.com/gorpong/PyChess
cd pychess

# Install dependencies and add `pychess` to path
pip install .
```

## Quick Start

```bash
# Start a new game (shows game mode selection menu)
pychess

# Other ways to launch:
pychess --list-games       # List saved games
pychess --load "Game 1"    # Load a saved game
```

When you start the game, you'll see a menu:

1. **Multiplayer** - Two players on the same computer
2. **vs AI - Easy** - Random moves
3. **vs AI - Medium** - Material-based strategy
4. **vs AI - Hard** - Material + positional play

## How to Play

### Understanding the Board

The board is displayed from White's perspective (rank 1 at bottom, rank 8 at top):

- **Files** are labeled a-h (left to right)
- **Ranks** are labeled 1-8 (bottom to top)
- **White pieces** appear in blue
- **Black pieces** appear in black
- **Light squares** have a white/light background
- **Dark squares** have a gray/dark background

### Piece Symbols

PyChess uses Unicode chess symbols for a beautiful display:

| Piece | White | Black | ASCII |
|-------|-------|-------|-------|
| King  | ♔     | ♚     | K/k   |
| Queen | ♕     | ♛     | Q/q   |
| Rook  | ♖     | ♜     | R/r   |
| Bishop| ♗     | ♝     | B/b   |
| Knight| ♘     | ♞     | N/n   |
| Pawn  | ♙     | ♟     | P/p   |

## Standard Algebraic Notation (SAN)

PyChess uses Standard Algebraic Notation, the official notation system for
recording chess games.

### Basic Moves

**Pawn Moves:**

- `e4` - Move pawn to e4
- `d5` - Move pawn to d5
- `e8=Q` - Promote pawn to Queen on e8

**Piece Moves:**

- `Nf3` - Move Knight to f3
- `Bb5` - Move Bishop to b5
- `Qd4` - Move Queen to d4
- `Ra1` - Move Rook to a1
- `Ke2` - Move King to e2

### Captures

Use `x` to indicate a capture:

- `exd5` - Pawn on e-file captures on d5
- `Nxe5` - Knight captures on e5
- `Bxc6` - Bishop captures on c6

### Special Moves

**Castling:**

- `O-O` - Kingside castling (short castling)
- `O-O-O` - Queenside castling (long castling)

**Promotion:**

- `e8=Q` - Promote to Queen
- `e8=R` - Promote to Rook
- `e8=B` - Promote to Bishop
- `e8=N` - Promote to Knight
- `exd8=Q` - Capture and promote to Queen

**En Passant:**

- `exd6` - Pawn captures en passant (automatically detected)

### Disambiguation

When multiple pieces of the same type can move to the same square:

- `Nbd7` - Knight from b-file moves to d7
- `N5f3` - Knight from rank 5 moves to f3
- `Qh4e1` - Queen from h4 moves to e1 (file and rank needed)

### Check and Checkmate

The game automatically adds check and checkmate symbols:

- `Qh5+` - Queen to h5, giving check
- `Qxf7#` - Queen captures f7, checkmate

## Game Controls

### Cursor Mode (Default)

Use arrow keys to navigate:

- **Arrow Keys** - Move cursor around the board
- **Enter** - Select piece / Make move
- **Escape** - Cancel selection
- **TAB** - Show/hide legal move hints (Easy/Medium AI only)
- **/** - Switch to SAN input mode

### Mouse Controls

PyChess supports full mouse interaction:

- **Left Click** - Select a piece or move to a square
- **Drag & Drop** - Click and hold on a piece, drag to destination, release to move
- **Click-Click** - Click a piece to select it, then click the destination square

Mouse controls work alongside keyboard controls - you can mix and match as you prefer.

### SAN Input Mode

Type moves directly in Standard Algebraic Notation:

- Type moves like `e4`, `Nf3`, `Bxc6`, `O-O`, `e8=Q`
- **Enter** - Submit the move
- **Backspace** - Delete last character
- **/** - Switch back to cursor mode

### Global Commands (Both Modes)

- **q** - Quit the game (with confirmation)
- **r** - Restart the game
- **u** - Undo the last move
- **?** - Show help overlay

## Example Game

Here's a quick example of the Scholar's Mate:

```text
1. e4 e5
2. Bc4 Nc6
3. Qh5 Nf6
4. Qxf7#
```

To play this in PyChess, you would type:

1. `e4` (press Enter)
2. `e5` (press Enter)
3. `Bc4` (press Enter)
4. `Nc6` (press Enter)
5. `Qh5` (press Enter)
6. `Nf6` (press Enter)
7. `Qxf7` (press Enter) - Checkmate!

## Chess Rules Reference

### Movement Rules

- **King**: Moves one square in any direction
- **Queen**: Moves any number of squares in any straight line
- **Rook**: Moves any number of squares horizontally or vertically
- **Bishop**: Moves any number of squares diagonally
- **Knight**: Moves in an "L" shape (2+1 squares), can jump over pieces
- **Pawn**:
  - Moves forward one square (two on first move)
  - Captures diagonally forward
  - Promotes when reaching the opposite end

### Special Rules

**Castling** - Move king two squares toward a rook, rook jumps over:

- King and rook must not have moved
- No pieces between them
- King not in check, doesn't pass through check, doesn't end in check

**En Passant** - Special pawn capture:

- When opponent's pawn moves two squares forward
- And lands beside your pawn
- You can capture it as if it moved only one square
- Must be done immediately on the next move

**Promotion** - When a pawn reaches the opposite end:

- Must promote to Queen, Rook, Bishop, or Knight
- Usually promoted to Queen (most powerful)

### Game End Conditions

- **Checkmate**: King is in check with no legal moves
- **Stalemate**: No legal moves but not in check (draw)
- **Insufficient Material**: Not enough pieces to checkmate (draw)
- **Threefold Repetition**: Same position occurs three times (draw)
- **Fifty-Move Rule**: 50 moves without capture or pawn move (draw)

## Tips for Beginners

1. **Control the Center**: Move pawns to e4, d4, e5, or d5 early
2. **Develop Knights and Bishops**: Get them out before moving the Queen
3. **Castle Early**: Protect your King by castling in the first 10 moves
4. **Think Before Moving**: Check if your move leaves pieces undefended
5. **Watch for Checks**: Always look for ways to attack the opponent's King
6. **Protect Your Pieces**: Don't leave valuable pieces where they can be captured

### Common Opening Moves

- **e4** - King's Pawn Opening (most popular)
- **d4** - Queen's Pawn Opening (solid and strategic)
- **Nf3** - Reti Opening (flexible)
- **c4** - English Opening (strategic)

After **1. e4 e5**, common continuations:

- **2. Nf3** - Open games
- **2. Bc4** - Italian Game
- **2. Nf3 Nc6 3. Bb5** - Spanish Opening (Ruy Lopez)

## Development Roadmap

- [x] Complete chess rules engine
- [x] SAN notation support
- [x] PGN import/export
- [x] Basic terminal UI
- [x] Cursor controls with visual feedback
- [x] Dual input modes (cursor + SAN)
- [x] AI opponents (Easy, Medium, Hard)
- [x] Undo/redo functionality
- [x] Help overlay system
- [x] Game mode selection menu
- [x] Mouse support
- [x] Save/load game functionality
- [ ] Time controls
- [ ] Advanced features (opening book, analysis)

## Technical Details

### Architecture

PyChess follows clean architecture principles:

- **Model** - Game state, board, pieces (`src/pychess/model/`)
- **Rules** - Move generation, validation, game logic (`src/pychess/rules/`)
- **Notation** - SAN parsing/generation, PGN support (`src/pychess/notation/`)
- **UI** - Terminal rendering, input handling (`src/pychess/ui/`)

### Testing

PyChess has comprehensive test coverage:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=pychess

# Run specific test file
pytest tests/model/test_board.py
```

## Troubleshooting

### Terminal Too Small

If you see "Terminal too small" error:

- Resize your terminal to at least 100x44 characters
- Or use fullscreen mode

### Unicode Characters Not Displaying

If chess pieces don't display correctly:

- Ensure your terminal supports Unicode
- Try a different terminal (iTerm2, Windows Terminal, GNOME Terminal)
- Or use ASCII mode (coming soon)

### Colors Look Wrong

If colors appear incorrect:

- Check your terminal's color scheme
- Try a terminal with 256-color support
- Ensure TERM environment variable is set correctly

## Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues.

### Development Setup

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run linter
ruff check src/

# Format code
black src/
```

## License

MIT License - See LICENSE file for details

## Acknowledgments

- Chess rules based on [FIDE Laws of Chess](https://handbook.fide.com/chapter/E012023)
- SAN notation following official chess standards
- Built with [blessed](https://github.com/jquast/blessed) for terminal UI

## Support

Having issues? Found a bug? Have a suggestion?
- Open an issue on GitHub
- Check the troubleshooting section above
- Review the SAN notation guide

---

**Enjoy playing chess in your terminal!** ♔♕♖♗♘♙
