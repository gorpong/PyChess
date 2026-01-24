"""Overlay displays for help, PGN examples, and other information."""

from blessed import Terminal

from pychess.ui.terminal import TerminalRenderer


# Help sections - each section has a name, optional key shortcut, and content
HELP_SECTIONS = [
    {
        "name": "Controls",
        "key": "1",
        "content": """CURSOR MODE (Default):
  Arrow Keys        - Move cursor around the board
  Enter             - Select piece / Make move
  Escape            - Cancel selection (press twice in Multiplayer)
  TAB               - Show/hide legal move hints (AI Easy/Medium only)
  /                 - Switch to SAN input mode

MOUSE CONTROLS:
  Left Click        - Select piece or make move
  Drag & Drop       - Click piece, drag to destination, release to move

SAN INPUT MODE:
  Type moves        - e.g., e4, Nf3, Bxc6, O-O, e8=Q
  /                 - Switch back to cursor mode

GLOBAL COMMANDS:
  q                 - Quit game (with confirmation)
  r                 - Restart game
  u                 - Undo last move
  ?                 - Show this help screen
  T                 - Jump to Tips for Beginners

GAME MECHANICS:
  • Use arrow keys or mouse to navigate and select/move pieces
  • Press TAB to show legal moves for selected piece (AI Easy/Medium)
  • Legal moves are highlighted in green when hints enabled
  • Selected piece is highlighted in cyan
  • Current cursor position is highlighted in yellow
  • Moves are recorded in Standard Algebraic Notation (SAN)

PIECE COLORS:
  Blue pieces       - White (your pieces if playing White)
  Black pieces      - Black (your pieces if playing Black)"""
    },
    {
        "name": "How to Play",
        "key": "2",
        "content": """UNDERSTANDING THE BOARD:

The board is displayed from White's perspective (rank 1 at bottom, rank 8 at top):

  • Files are labeled a-h (left to right)
  • Ranks are labeled 1-8 (bottom to top)
  • White pieces appear in blue
  • Black pieces appear in black
  • Light squares have a white/light background
  • Dark squares have a gray/dark background

PIECE SYMBOLS:

PyChess uses Unicode chess symbols:

  Piece     White   Black   Letter
  ─────     ─────   ─────   ──────
  King        ♔       ♚       K
  Queen       ♕       ♛       Q
  Rook        ♖       ♜       R
  Bishop      ♗       ♝       B
  Knight      ♘       ♞       N
  Pawn        ♙       ♟       (none)

MAKING MOVES:

  1. Use arrow keys or mouse to select your piece
  2. Press Enter or click to confirm selection
  3. Move cursor to destination square
  4. Press Enter or click to complete the move

Or type moves directly in SAN mode (press / to switch)."""
    },
    {
        "name": "SAN Notation",
        "key": "3",
        "content": """STANDARD ALGEBRAIC NOTATION (SAN):

SAN is the official notation system for recording chess moves.

BASIC MOVES:

  Pawn Moves:
    e4        - Move pawn to e4
    d5        - Move pawn to d5
    e8=Q      - Promote pawn to Queen on e8

  Piece Moves (use capital letter):
    Nf3       - Knight to f3
    Bb5       - Bishop to b5
    Qd4       - Queen to d4
    Ra1       - Rook to a1
    Ke2       - King to e2

CAPTURES:

  Use 'x' to indicate a capture:
    exd5      - Pawn on e-file captures on d5
    Nxe5      - Knight captures on e5
    Bxc6      - Bishop captures on c6

SPECIAL MOVES:

  Castling:
    O-O       - Kingside castling (short)
    O-O-O     - Queenside castling (long)

  Promotion:
    e8=Q      - Promote to Queen
    e8=R      - Promote to Rook
    e8=B      - Promote to Bishop
    e8=N      - Promote to Knight

  En Passant:
    exd6      - Pawn captures en passant (auto-detected)

DISAMBIGUATION:

  When multiple pieces can move to the same square:
    Nbd7      - Knight from b-file to d7
    N5f3      - Knight from rank 5 to f3
    Qh4e1     - Queen from h4 to e1

CHECK AND CHECKMATE:

  The game automatically adds these symbols:
    Qh5+      - Queen to h5, giving check
    Qxf7#     - Queen captures f7, checkmate"""
    },
    {
        "name": "Chess Rules",
        "key": "4",
        "content": """MOVEMENT RULES:

  King      - Moves one square in any direction
  Queen     - Moves any number of squares in any straight line
  Rook      - Moves any number of squares horizontally or vertically
  Bishop    - Moves any number of squares diagonally
  Knight    - Moves in an "L" shape (2+1 squares), can jump over pieces
  Pawn      - Moves forward one square (two on first move)
              Captures diagonally forward
              Promotes when reaching the opposite end

SPECIAL RULES:

  Castling - Move king two squares toward a rook, rook jumps over:
    • King and rook must not have moved
    • No pieces between them
    • King not in check, doesn't pass through check, doesn't end in check

  En Passant - Special pawn capture:
    • When opponent's pawn moves two squares forward
    • And lands beside your pawn
    • You can capture it as if it moved only one square
    • Must be done immediately on the next move

  Promotion - When a pawn reaches the opposite end:
    • Must promote to Queen, Rook, Bishop, or Knight
    • Usually promoted to Queen (most powerful)

GAME END CONDITIONS:

  Checkmate            - King is in check with no legal moves (win/loss)
  Stalemate            - No legal moves but not in check (draw)
  Insufficient Material - Not enough pieces to checkmate (draw)
  Threefold Repetition - Same position occurs three times (draw)
  Fifty-Move Rule      - 50 moves without capture or pawn move (draw)"""
    },
    {
        "name": "Tips for Beginners",
        "key": "t",
        "content": """TIPS FOR BEGINNERS:

  1. Control the Center
     Move pawns to e4, d4, e5, or d5 early. The center is the most
     important area of the board.

  2. Develop Knights and Bishops
     Get your minor pieces out before moving the Queen. Knights are
     usually developed to f3/c3 (White) or f6/c6 (Black).

  3. Castle Early
     Protect your King by castling in the first 10 moves. This also
     connects your rooks.

  4. Think Before Moving
     Before each move, check if it leaves any pieces undefended.
     Ask yourself: "What is my opponent threatening?"

  5. Watch for Checks
     Always look for ways to attack the opponent's King. Checks
     force your opponent to respond.

  6. Protect Your Pieces
     Don't leave valuable pieces where they can be captured for free.
     Remember piece values: Q=9, R=5, B=3, N=3, P=1

COMMON OPENING MOVES:

  e4    - King's Pawn Opening (most popular, opens lines)
  d4    - Queen's Pawn Opening (solid and strategic)
  Nf3   - Reti Opening (flexible, delays pawn commitment)
  c4    - English Opening (controls d5, strategic)

AFTER 1. e4 e5:

  2. Nf3         - Open games, attacks e5 pawn
  2. Bc4         - Italian Game, targets f7
  2. Nf3 Nc6 3. Bb5 - Spanish/Ruy Lopez (classical)

Scholar'S MATE WARNING:

  Watch out for Qh5 + Bc4 threatening Qxf7#. Defend with Nc6, g6, or Nf6."""
    },
]


def _format_help_line(line: str, bold_func) -> str:
    """Format a help line, making headings bold.
    
    Args:
        line: The line to format
        bold_func: Function to apply bold formatting
        
    Returns:
        Formatted line
    """
    stripped = line.strip()
    
    # Check if this is a heading (all caps followed by colon, or title case with colon)
    if stripped and stripped.endswith(':'):
        # Check if it's a major heading (mostly uppercase)
        if stripped[:-1].isupper() or stripped[:-1].replace(' ', '').isupper():
            return bold_func(line)
        # Check if it's a subheading (title-like)
        elif stripped[0].isupper() and len(stripped) > 1:
            return bold_func(line)
    
    return line


def _split_into_pages(text: str, max_lines_per_page: int) -> list[list[str]]:
    """Split help text into pages, breaking at blank lines when possible.

    Args:
        text: The help text to split
        max_lines_per_page: Maximum number of content lines per page

    Returns:
        List of pages, where each page is a list of lines
    """
    lines = text.strip().split('\n')
    
    if not lines or (len(lines) == 1 and not lines[0]):
        return []
    
    pages = []
    current_page = []

    for line in lines:
        # Check if adding this line would exceed the limit
        if len(current_page) >= max_lines_per_page:
            # Need to start a new page
            # Try to break at a blank line by looking back
            if line.strip() == '':
                # Current line is blank - perfect break point
                pages.append(current_page)
                current_page = []
                continue
            else:
                # Look for a blank line to break at
                break_index = None
                for i in range(len(current_page) - 1, -1, -1):
                    if current_page[i].strip() == '':
                        break_index = i
                        break

                if break_index is not None:
                    # Break at the blank line
                    pages.append(current_page[:break_index])
                    current_page = current_page[break_index + 1:]
                else:
                    # No blank line found - break at max
                    pages.append(current_page)
                    current_page = []

        current_page.append(line)

    # Add the last page if it has content
    if current_page:
        pages.append(current_page)

    return pages


def show_help_overlay(term: Terminal, start_section: str = None) -> None:
    """Display paginated help overlay with multiple sections.

    Args:
        term: Terminal instance
        start_section: Optional section key to start at (e.g., "t" for Tips)
    """
    # Calculate max lines per page (80% of MIN_HEIGHT minus header/footer)
    max_lines = int(TerminalRenderer.MIN_HEIGHT * 0.8) - 6

    # Find starting section
    current_section_idx = 0
    if start_section:
        for i, s in enumerate(HELP_SECTIONS):
            if s.get("key") == start_section.lower():
                current_section_idx = i
                break
    
    with term.cbreak():
        while True:
            section = HELP_SECTIONS[current_section_idx]
            
            # Split current section into pages
            pages = _split_into_pages(section["content"], max_lines)
            if not pages:
                pages = [[""]]
            total_pages = len(pages)
            current_page = 0
            
            # Inner loop for pages within a section
            while True:
                # Clear screen
                print(term.home() + term.clear())

                # Draw header with section name
                section_name = section["name"]
                header_text = f"PyChess - Help: {section_name}"
                padding = (70 - len(header_text)) // 2
                
                print()
                print("╔" + "═" * 70 + "╗")
                print("║" + " " * padding + term.bold(header_text) + " " * (70 - padding - len(header_text)) + "║")
                print("╚" + "═" * 70 + "╝")
                print()

                # Draw current page content with formatting
                for line in pages[current_page]:
                    formatted = _format_help_line(line, term.bold)
                    print(formatted)

                # Draw footer with navigation
                print()
                print("═" * 72)
                
                # Section navigation hints
                section_hints = []
                for i, s in enumerate(HELP_SECTIONS):
                    key = s.get("key", str(i + 1))
                    name = s["name"]
                    if i == current_section_idx:
                        section_hints.append(f"[{key}:{name}]")
                    else:
                        section_hints.append(f"{key}:{name}")
                
                print("Sections: " + "  ".join(section_hints))
                
                # Page info
                if total_pages > 1:
                    print(f"Page {current_page + 1}/{total_pages} | "
                          f"Space/→/↓=next page, ←/↑=prev page | "
                          f"Q/Esc=return to game")
                else:
                    print("Q/Esc = return to game | Press section number/letter to switch")

                # Wait for key press
                key = term.inkey(timeout=None)
                key_lower = key.lower() if hasattr(key, 'lower') else str(key).lower()

                # Handle quit
                if key_lower == 'q' or key.name == 'KEY_ESCAPE':
                    return
                
                # Handle section switching
                section_switched = False
                for i, s in enumerate(HELP_SECTIONS):
                    if s.get("key") == key_lower:
                        current_section_idx = i
                        section_switched = True
                        break
                
                if section_switched:
                    break  # Break inner loop to reload section
                
                # Handle page navigation within section
                if key == ' ' or key.name == 'KEY_ENTER' or key.name == 'KEY_RIGHT' or key.name == 'KEY_DOWN':
                    if current_page < total_pages - 1:
                        current_page += 1
                    elif current_section_idx < len(HELP_SECTIONS) - 1:
                        # Move to next section
                        current_section_idx += 1
                        break
                elif key.name == 'KEY_LEFT' or key.name == 'KEY_UP':
                    if current_page > 0:
                        current_page -= 1
                    elif current_section_idx > 0:
                        # Move to previous section
                        current_section_idx -= 1
                        break
