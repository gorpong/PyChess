"""HTTP route handlers for PyChess web UI."""

from flask import Blueprint, render_template, session, redirect, url_for, request

from pychess.model.square import Square
from pychess.web.serializers import board_to_template_data, game_state_to_dict
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
    
    Args:
        game_session: The game session to render.
        template: Template to use for rendering.
        
    Returns:
        Rendered template response.
    """
    # Get legal moves if hints are enabled
    legal_moves = game_session.get_legal_moves_for_selected()
    
    board_data = board_to_template_data(
        game_session.game_state.board,
        selected=game_session.selected_square,
        legal_moves=legal_moves,
        last_move=game_session.last_move,
    )
    game_data = game_state_to_dict(game_session.game_state)
    
    return render_template(
        template,
        board_data=board_data,
        game=game_data,
        status_messages=game_session.status_messages,
        game_mode=game_session.game_mode,
        selected_square=game_session.selected_square,
        show_hints=game_session.show_hints,
        hints_allowed=game_session.hints_allowed,
    )


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
    """Handle square selection."""
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
    
    # Handle selection
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
