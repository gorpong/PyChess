"""HTTP route handlers for PyChess web UI."""

from datetime import date
from flask import Blueprint, render_template, session, redirect, url_for, request

from pychess.model.piece import Color
from pychess.model.square import Square
from pychess.persistence.save_manager import InvalidGameNameError
from pychess.web.serializers import (
    board_to_template_data,
    game_state_to_dict,
    format_move_history,
)
from pychess.web.game_manager import get_game_manager, WebGameSession


bp = Blueprint('main', __name__)


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


def render_game_state(game_session: WebGameSession, template: str = 'game.html'):
    """Render the current game state.
    
    For HTMX requests, returns just the game_area partial.
    For full page requests, returns the complete game template.
    
    Args:
        game_session: The game session to render.
        template: Template to use for full page rendering.
        
    Returns:
        Rendered template response.
    """
    is_htmx = request.headers.get('HX-Request') == 'true'
    context = build_game_context(game_session)
    
    if is_htmx:
        return render_template('partials/game_area.html', **context)
    else:
        return render_template(template, **context)


def build_game_context(game_session: WebGameSession) -> dict:
    """Build template context for game rendering.
    
    Args:
        game_session: The game session to render.
        
    Returns:
        Dictionary of template context variables.
    """
    show_promotion = game_session.pending_promotion is not None
    promotion_color = None
    if show_promotion:
        promotion_color = 'w' if game_session.game_state.turn == Color.WHITE else 'b'
    
    legal_moves = game_session.get_legal_moves_for_selected()
    
    board_data = board_to_template_data(
        game_session.game_state.board,
        selected=game_session.selected_square,
        legal_moves=legal_moves,
        last_move=game_session.last_move,
    )
    game_data = game_state_to_dict(game_session.game_state)
    
    # Generate default save name
    default_save_name = game_session.game_name
    if not default_save_name:
        today = date.today().strftime("%Y-%m-%d")
        default_save_name = f"Game {today}"
    
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
        'game_ended_during_session': game_session.game_ended_during_session,
        'show_save_dialog': False,
        'save_and_quit': False,
        'default_save_name': default_save_name,
        'save_error': None,
        'ai_thinking': False,  # AI moves are synchronous, so this is always False in response
    }


@bp.route('/')
def index():
    """Render the game mode selection page.
    
    If an active game session exists, redirects to /game.
    """
    game_session = get_current_session()
    if game_session:
        return redirect(url_for('main.game'))
    
    return render_template('index.html')


@bp.route('/game')
def game():
    """Render the active game page.
    
    If no active game session exists, redirects to /.
    """
    game_session = get_current_session()
    if not game_session:
        return redirect(url_for('main.index'))
    
    return render_game_state(game_session)


@bp.route('/games')
def list_games():
    """Render the saved games list page."""
    manager = get_game_manager()
    saved_games = manager.list_saved_games()
    
    # Reverse to show newest first
    saved_games = list(reversed(saved_games))
    
    # Enrich with game mode from headers
    enriched_games = []
    for game in saved_games:
        try:
            _, headers = manager._save_manager.load_game(game.name)
            game_mode = headers.game_mode if headers.game_mode else "Unknown"
        except Exception:
            game_mode = "Unknown"
        
        # Create a dict with all game info plus game_mode
        enriched_games.append({
            'name': game.name,
            'white': game.white,
            'black': game.black,
            'result': game.result,
            'date': game.date,
            'move_count': game.move_count,
            'is_complete': game.is_complete,
            'game_mode': game_mode,
        })
    
    return render_template('games.html', saved_games=enriched_games)


@bp.route('/api/new-game', methods=['POST'])
def new_game():
    """Create a new game with specified mode."""
    manager = get_game_manager()
    
    mode = request.form.get('mode', 'multiplayer')
    if mode not in ('multiplayer', 'easy', 'medium', 'hard'):
        mode = 'multiplayer'
    
    old_session_id = session.get('game_session_id')
    if old_session_id:
        manager.delete_game(old_session_id)
    
    session_id = manager.create_session_id()
    session['game_session_id'] = session_id
    manager.create_game(session_id, mode)
    
    return redirect(url_for('main.game'))


@bp.route('/api/restart', methods=['POST'])
def restart():
    """Restart the current game with the same mode."""
    manager = get_game_manager()
    game_session = get_current_session()
    
    if not game_session:
        return redirect(url_for('main.index'))
    
    current_mode = game_session.game_mode
    
    old_session_id = session.get('game_session_id')
    if old_session_id:
        manager.delete_game(old_session_id)
    
    session_id = manager.create_session_id()
    session['game_session_id'] = session_id
    manager.create_game(session_id, current_mode)
    
    return redirect(url_for('main.game'))


@bp.route('/api/quit', methods=['POST'])
def quit_game():
    """Quit the current game and return to menu."""
    manager = get_game_manager()
    
    session_id = session.get('game_session_id')
    if session_id:
        manager.delete_game(session_id)
        session.pop('game_session_id', None)
    
    return redirect(url_for('main.index'))


@bp.route('/api/select', methods=['POST'])
def select_square():
    """Handle square selection (and move execution if legal destination)."""
    manager = get_game_manager()
    game_session = get_current_session()
    
    if not game_session:
        return redirect(url_for('main.index'))
    
    square_str = request.form.get('square', '')
    
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


@bp.route('/api/show-save-dialog', methods=['POST'])
def show_save_dialog():
    """Show the save game dialog."""
    game_session = get_current_session()
    
    if not game_session:
        return redirect(url_for('main.index'))
    
    save_and_quit = request.form.get('save_and_quit', 'false') == 'true'
    
    context = build_game_context(game_session)
    context['show_save_dialog'] = True
    context['save_and_quit'] = save_and_quit
    
    is_htmx = request.headers.get('HX-Request') == 'true'
    if is_htmx:
        return render_template('partials/game_area.html', **context)
    else:
        return render_template('game.html', **context)


@bp.route('/api/cancel-save', methods=['POST'])
def cancel_save():
    """Cancel the save dialog."""
    game_session = get_current_session()
    
    if not game_session:
        return redirect(url_for('main.index'))
    
    return render_game_state(game_session)


@bp.route('/api/games/save', methods=['POST'])
def save_game():
    """Save the current game."""
    manager = get_game_manager()
    game_session = get_current_session()
    
    if not game_session:
        return redirect(url_for('main.index'))
    
    name = request.form.get('name', '').strip()
    save_and_quit = request.form.get('save_and_quit', 'false') == 'true'
    
    if not name:
        context = build_game_context(game_session)
        context['show_save_dialog'] = True
        context['save_and_quit'] = save_and_quit
        context['save_error'] = 'Please enter a name for your game.'
        
        is_htmx = request.headers.get('HX-Request') == 'true'
        if is_htmx:
            return render_template('partials/game_area.html', **context)
        else:
            return render_template('game.html', **context)
    
    try:
        saved_name = manager.save_game(game_session, name)
        
        if save_and_quit:
            # Delete session and redirect to menu
            session_id = session.get('game_session_id')
            if session_id:
                manager.delete_game(session_id)
                session.pop('game_session_id', None)
            return redirect(url_for('main.index'))
        else:
            # Stay in game, show success message
            game_session.status_messages = [f'Game saved as "{saved_name}"']
            manager.update_game(game_session)
            return render_game_state(game_session)
            
    except InvalidGameNameError as e:
        context = build_game_context(game_session)
        context['show_save_dialog'] = True
        context['save_and_quit'] = save_and_quit
        context['save_error'] = str(e)
        
        is_htmx = request.headers.get('HX-Request') == 'true'
        if is_htmx:
            return render_template('partials/game_area.html', **context)
        else:
            return render_template('game.html', **context)


@bp.route('/api/games/<name>/load', methods=['POST'])
def load_game(name: str):
    """Load a saved game."""
    manager = get_game_manager()
    
    # Delete existing session if any
    old_session_id = session.get('game_session_id')
    if old_session_id:
        manager.delete_game(old_session_id)
    
    try:
        session_id = manager.create_session_id()
        session['game_session_id'] = session_id
        manager.load_saved_game(session_id, name)
        
        return redirect(url_for('main.game'))
        
    except (FileNotFoundError, InvalidGameNameError):
        # Clear session and redirect to games list
        session.pop('game_session_id', None)
        return redirect(url_for('main.list_games'))


@bp.route('/api/games/<name>/delete', methods=['POST'])
def delete_game(name: str):
    """Delete a saved game."""
    manager = get_game_manager()
    
    try:
        manager.delete_saved_game(name)
    except (FileNotFoundError, InvalidGameNameError):
        pass  # Ignore errors, just refresh the list
    
    # Return to games list
    return redirect(url_for('main.list_games'))
