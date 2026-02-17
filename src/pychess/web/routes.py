"""HTTP route handlers for PyChess web UI."""

from flask import Blueprint, render_template

from pychess.model.game_state import GameState
from pychess.web.serializers import board_to_template_data, game_state_to_dict


bp = Blueprint('main', __name__)


@bp.route('/')
def index():
    """Render the game mode selection page with initial board."""
    state = GameState.initial()
    board_data = board_to_template_data(state.board)
    game_data = game_state_to_dict(state)
    
    return render_template(
        'index.html',
        board_data=board_data,
        game=game_data,
    )
