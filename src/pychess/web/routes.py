"""HTTP route handlers for PyChess web UI."""

from flask import Blueprint, render_template, session, redirect, url_for, request

from pychess.model.piece import Color
from pychess.model.square import Square
from pychess.web.serializers import (
    board_to_template_data,
    game_state_to_dict,
    format_move_history,
)
from pychess.web.game_manager import get_game_manager, WebGameSession


bp = Blueprint('main', __name__)


def get_or_create_session() -> WebGameSession:
    """Get existing game session or create a new one.
    
    Returns:
        The current WebGameSession for this browser session.
    """
    manager = get_game_manager()
    
    # Check for existing session
    session_id = session.get('game_session_id')
    if session_id:
        game = manager.get_game(session_id)
        if game:
            return game
    
    # Create new session
    session_id = manager.create_session_id()
    session['game_session_id'] = session_id
    return manager.create_game(session_id, 'multiplayer')


def get_current_session() -> WebGameSession | None:
    """Get existing game session without creating a new one.
    
    Returns:
        The current WebGameSession if exists, None otherwise.
    """
    manager = get_game_manager()
    session_id = session.get('game_session_id')
    if session_id:
        return manager.get_game(session_id)
    return None


def render_game_state(game_session: WebGameSession, template: str = 'index.html'):
    """Render the current game state.
    
    For HTMX requests, returns just the game_area partial.
    For full page requests, returns the complete index template.
    
    Args:
        game_session: The game session to render.
        template: Template to use for full page rendering.
        
    Returns:
        Rendered template response.
    """
    # Determine if this is an HTMX request
    is_htmx = request.headers.get('HX-Request') == 'true'
    
    # Build common template context
    context = build_game_context(game_session)
    
    if is_htmx:
        # Return just the game area partial for HTMX swaps
        return render_template('partials/game_area.html', **context)
    else:
        # Return full page for regular requests
        return render_template(template, **context)


def build_game_context(game_session: WebGameSession) -> dict:
    """Build template context for game rendering.
    
    Args:
        game_session: The game session to render.
        
    Returns:
        Dictionary of template context variables.
    """
    # Check if promotion dialog should be shown
    show_promotion = game_session.pending_promotion is not None
    promotion_color = None
    if show_promotion:
        promotion_color = 'w' if game_session.game_state.turn == Color.WHITE else 'b'
    
    # Get legal moves if hints are enabled
    legal_moves = game_session.get_legal_moves_for_selected()
    
    board_data = board_to_template_data(
        game_session.game_state.board,
        selected=game_session.selected_square,
        legal_moves=legal_moves,
        last_move=game_session.last_move,
    )
    game_data = game_state_to_dict(game_session.game_state)
    
    return {
        'board_data': board_data,
        'game': game_data,
        'status_messages': game_session.status_messages,
        'game_mode': game_session.game_mode,
        'selected_square': game_session.selected_square,
        'show_hints': game_session.show_hints,
        'hints_allowed': game_session.hints_allowed,
        'move_pairs': format_move_history(game_session.game_state.move_history),
        'show_promotion': show_promotion,
        'promotion_color': promotion_color,
        'game_result': game_session.game_result,
    }

@bp.route('/')
def index():
    """Render the game mode selection page with current board."""
    game_session = get_or_create_session()
    return render_game_state(game_session)


@bp.route('/api/new-game', methods=['POST'])
def new_game():
    """Create a new game with specified mode."""
    manager = get_game_manager()
    
    mode = request.form.get('mode', 'multiplayer')
    if mode not in ('multiplayer', 'easy', 'medium', 'hard'):
        mode = 'multiplayer'
    
    # Delete existing session if any
    old_session_id = session.get('game_session_id')
    if old_session_id:
        manager.delete_game(old_session_id)
    
    # Create new session
    session_id = manager.create_session_id()
    session['game_session_id'] = session_id
    manager.create_game(session_id, mode)
    
    return redirect(url_for('main.index'))


@bp.route('/api/select', methods=['POST'])
def select_square():
    """Handle square selection (and move execution if legal destination)."""
    manager = get_game_manager()
    game_session = get_current_session()
    
    if not game_session:
        return redirect(url_for('main.index'))
    
    square_str = request.form.get('square', '')
    
    # Parse square string (e.g., 'e2')
    if len(square_str) != 2:
        return render_game_state(game_session)
    
    try:
        file = square_str[0].lower()
        rank = int(square_str[1])
        if file not in 'abcdefgh' or rank not in range(1, 9):
            raise ValueError("Invalid square")
        square = Square(file=file, rank=rank)
    except (ValueError, IndexError):
        return render_game_state(game_session)
    
    # Handle selection (may also execute move)
    game_session = manager.select_square(game_session, square)
    manager.update_game(game_session)
    
    return render_game_state(game_session)


@bp.route('/api/toggle-hints', methods=['POST'])
def toggle_hints():
    """Toggle legal move hints display."""
    manager = get_game_manager()
    game_session = get_current_session()
    
    if not game_session:
        return redirect(url_for('main.index'))
    
    game_session = manager.toggle_hints(game_session)
    manager.update_game(game_session)
    
    return render_game_state(game_session)


@bp.route('/api/promote', methods=['POST'])
def promote():
    """Complete a pawn promotion with chosen piece."""
    manager = get_game_manager()
    game_session = get_current_session()
    
    if not game_session:
        return redirect(url_for('main.index'))
    
    piece = request.form.get('piece', 'Q')
    
    game_session = manager.complete_promotion(game_session, piece)
    manager.update_game(game_session)
    
    return render_game_state(game_session)


@bp.route('/api/undo', methods=['POST'])
def undo():
    """Undo the last move(s)."""
    manager = get_game_manager()
    game_session = get_current_session()
    
    if not game_session:
        return redirect(url_for('main.index'))
    
    game_session = manager.undo_move(game_session)
    manager.update_game(game_session)
    
    return render_game_state(game_session)
