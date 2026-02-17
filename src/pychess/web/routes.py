"""HTTP route handlers for PyChess web UI."""

from flask import Blueprint, render_template, session, redirect, url_for, request

from pychess.model.game_state import GameState
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


@bp.route('/')
def index():
    """Render the game mode selection page with current board."""
    game_session = get_or_create_session()
    
    board_data = board_to_template_data(
        game_session.game_state.board,
        selected=game_session.selected_square,
        last_move=game_session.last_move,
    )
    game_data = game_state_to_dict(game_session.game_state)
    
    return render_template(
        'index.html',
        board_data=board_data,
        game=game_data,
        status_messages=game_session.status_messages,
        game_mode=game_session.game_mode,
    )


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
