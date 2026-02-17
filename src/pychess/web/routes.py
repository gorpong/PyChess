"""HTTP route handlers for PyChess web UI."""

from flask import Blueprint, render_template


bp = Blueprint('main', __name__)


@bp.route('/')
def index():
    """Render the game mode selection page."""
    return render_template('index.html')
