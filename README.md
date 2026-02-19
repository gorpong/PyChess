# PyChess - Terminal & Web ASCII Chess

A fully-featured, beautiful chess game written in Python. Play chess in your 
terminal with Unicode pieces and color-coded squares, or in your browser with a
modern web interface. Full chess rules implementation with AI opponents.

## Features

- ✨ **Two Interfaces** - Play in terminal (curses) or browser (web UI)
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
│   ├── model/       # Game state, board, pieces
│   ├── rules/       # Move generation, validation
│   ├── notation/    # SAN parsing, PGN support
│   ├── ai/          # AI engines (easy, medium, hard)
│   ├── ui/          # Terminal UI
│   ├── web/         # Web UI (Flask + HTMX)
│   └── persistence/ # Save/load functionality
├── tests/
│   ├── model/
│   ├── rules/
│   ├── notation/
│   ├── ai/
│   ├── web/
│   └── integration/
└── README.md
````

### Technology Stack

**Terminal UI:**

- Python blessed for terminal rendering
- Unicode chess symbols

**Web UI:**

- Flask for HTTP server
- HTMX for reactive updates (no JavaScript framework)
- SVG chess pieces
- CSS Grid for board layout

**Core:**

- Pure Python, no external chess engines
- Dataclasses for state management
- Comprehensive test coverage

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

## Requirements

- Python 3.12+
- Flask 3.0+ (for web UI)
- Terminal with Unicode support (for terminal UI)
- Modern web browser (for web UI)

## License

MIT License - See LICENSE file for details

## Acknowledgments

- Chess rules based on [FIDE Laws of Chess](https://handbook.fide.com/chapter/E012023)
- SAN notation following official chess standards
- Built with [blessed](https://github.com/jquast/blessed) for terminal UI
- Web UI powered by [HTMX](https://htmx.org/)

---

**Enjoy playing chess!** ♔♕♖♗♘♙
