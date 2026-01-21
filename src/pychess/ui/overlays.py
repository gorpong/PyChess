"""Overlay displays for help, PGN examples, and other information."""

from blessed import Terminal

from pychess.ui.terminal import TerminalRenderer


# Help text content with sections separated by blank lines
HELP_TEXT = """CURSOR MODE (Default):
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

GAME MECHANICS:
  • Use arrow keys or mouse to navigate and select/move pieces
  • Press TAB to show legal moves for selected piece (AI Easy/Medium)
  • Legal moves are highlighted in green when hints enabled
  • Selected piece is highlighted in cyan
  • Current cursor position is highlighted in yellow
  • Moves are recorded in Standard Algebraic Notation (SAN)

STANDARD ALGEBRAIC NOTATION (SAN) EXAMPLES:
  e4                - Pawn to e4
  Nf3               - Knight to f3
  Bxc6              - Bishop captures on c6
  O-O               - Kingside castling
  O-O-O             - Queenside castling
  e8=Q              - Pawn promotes to Queen
  exd5              - Pawn on e-file captures on d5
  Rad1              - Rook from a-file to d1 (disambiguation)

PIECE COLORS:
  Blue pieces       - White (your pieces if playing White)
  Black pieces      - Black (your pieces if playing Black)"""


def _split_into_pages(text: str, max_lines_per_page: int) -> list[list[str]]:
    """Split help text into pages, breaking at blank lines when possible.

    Args:
        text: The help text to split
        max_lines_per_page: Maximum number of content lines per page

    Returns:
        List of pages, where each page is a list of lines
    """
    lines = text.strip().split('\n')
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


def show_help_overlay(term: Terminal) -> None:
    """Display paginated help overlay with controls and commands.

    Args:
        term: Terminal instance
    """
    # Calculate max lines per page (80% of MIN_HEIGHT)
    max_lines = int(TerminalRenderer.MIN_HEIGHT * 0.8)

    # Split help text into pages
    pages = _split_into_pages(HELP_TEXT, max_lines)
    total_pages = len(pages)
    current_page = 0

    with term.cbreak():
        while True:
            # Clear screen
            print(term.home() + term.clear())

            # Draw header
            header = """
╔══════════════════════════════════════════════════════════════════════╗
║                          PyChess - Help                              ║
╚══════════════════════════════════════════════════════════════════════╝
"""
            print(header)

            # Draw current page content
            for line in pages[current_page]:
                print(line)

            # Draw footer with page indicator and navigation help
            print()
            print("═" * 72)
            print(f"Page {current_page + 1}/{total_pages}")
            if total_pages > 1:
                print("Navigation: Space/Enter/→/↓ = next, ←/↑ = prev, Q/Esc = return to game")
            else:
                print("Press Q or Esc to return to the game")

            # Wait for key press
            key = term.inkey(timeout=None)

            # Handle navigation
            if key.lower() == 'q' or key.name == 'KEY_ESCAPE':
                break
            elif key == ' ' or key.name == 'KEY_ENTER' or key.name == 'KEY_RIGHT' or key.name == 'KEY_DOWN':
                if current_page < total_pages - 1:
                    current_page += 1
            elif key.name == 'KEY_LEFT' or key.name == 'KEY_UP':
                if current_page > 0:
                    current_page -= 1
