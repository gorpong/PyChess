"""Overlay displays for help, PGN examples, and other information."""

from blessed import Terminal


def show_help_overlay(term: Terminal) -> None:
    """Display help overlay with controls and commands.

    Args:
        term: Terminal instance
    """
    # Clear screen
    print(term.home() + term.clear())

    # Draw help content
    help_text = """
╔══════════════════════════════════════════════════════════════════════╗
║                          PyChess - Help                              ║
╚══════════════════════════════════════════════════════════════════════╝

CURSOR MODE (Default):
  Arrow Keys        - Move cursor around the board
  Enter             - Select piece / Make move
  Escape            - Cancel selection (press twice in Multiplayer)
  TAB               - Show/hide legal move hints (AI Easy/Medium only)
  /                 - Switch to SAN input mode

SAN INPUT MODE:
  Type moves        - e.g., e4, Nf3, Bxc6, O-O, e8=Q
  /                 - Switch back to cursor mode

GLOBAL COMMANDS:
  q                 - Quit game (with confirmation)
  r                 - Restart game
  u                 - Undo last move
  ?                 - Show this help screen

GAME MECHANICS:
  • Use arrow keys to navigate and Enter to select/move pieces
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
  Black pieces      - Black (your pieces if playing Black)

═══════════════════════════════════════════════════════════════════════

Press any key to return to the game...
"""

    print(help_text)

    # Wait for key press
    with term.cbreak():
        term.inkey(timeout=None)
