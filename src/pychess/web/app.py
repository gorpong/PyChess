"""Flask application factory for PyChess web UI."""

import os
import secrets

from flask import Flask
from flask_socketio import SocketIO

from pychess.match import MatchService, SqlAlchemyMatchRepository
from pychess.match.migrations import auto_migrate_if_enabled
from pychess.web import match_routes, match_socketio, routes


def _truthy(value: object) -> bool:
    """Interpret common env/config truthy spellings."""
    if isinstance(value, bool):
        return value
    return str(value).lower() in ("1", "true", "yes", "on")


def create_app(test_config: dict | None = None) -> Flask:
    """Create and configure the Flask application.

    Args:
        test_config: Optional configuration dictionary for testing.

    Returns:
        Configured Flask application instance.
    """
    app = Flask(
        __name__,
        static_folder='static',
        template_folder='templates',
    )

    default_secret = os.environ.get('SECRET_KEY')
    if default_secret is None:
        default_secret = secrets.token_hex(32)

    app.config.from_mapping(
        SECRET_KEY=default_secret,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE='Lax',
        MATCH_DB_URL=os.environ.get('PYCHESS_DB_URL', 'sqlite:///pychess-matches.db'),
        MATCH_CREATE_SCHEMA=os.environ.get('PYCHESS_CREATE_SCHEMA'),
    )

    if test_config is not None:
        app.config.from_mapping(test_config)
        # Default to an in-memory DB under TESTING so test runs don't litter
        # the working directory with SQLite files. Explicit MATCH_DB_URL in
        # test_config still wins.
        if app.config.get('TESTING') and 'MATCH_DB_URL' not in test_config:
            app.config['MATCH_DB_URL'] = 'sqlite://'

    # Opt-in schema upgrade (PYCHESS_AUTO_MIGRATE=1) for fresh Docker containers.
    # If migrations ran, don't also call SQLAlchemy create_all; the app should
    # have one schema bootstrap path per process.
    migrated = auto_migrate_if_enabled(app.config['MATCH_DB_URL'])
    if app.config['MATCH_CREATE_SCHEMA'] is None:
        create_schema = not migrated
    else:
        create_schema = _truthy(app.config['MATCH_CREATE_SCHEMA'])

    # Attach a single process-wide MatchService so routes can share the
    # repository's connection pool. Tests may override by setting
    # `app.match_service` after construction.
    repo = SqlAlchemyMatchRepository.from_url(
        app.config['MATCH_DB_URL'],
        create_schema=create_schema,
    )
    app.match_service = MatchService(repo)

    app.register_blueprint(routes.bp)
    app.register_blueprint(match_routes.bp)

    # Socket.IO layer for real-time move push. Local `pychess-web` runs use
    # threading + simple-websocket by default; Docker sets this to gevent and
    # runs under Gunicorn's gevent-websocket worker.
    async_mode = app.config.get("SOCKETIO_ASYNC_MODE") or os.environ.get(
        "PYCHESS_SOCKETIO_ASYNC_MODE", "threading"
    )
    socketio = SocketIO(
        app,
        async_mode=async_mode,
        cors_allowed_origins="*" if app.config.get("TESTING") else None,
    )
    match_socketio.register(socketio)
    app.socketio = socketio

    return app


def main() -> None:
    """Entry point for pychess-web command."""
    import argparse

    parser = argparse.ArgumentParser(
        prog="pychess-web",
        description="PyChess Web UI Server",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable Flask debug mode (do not use in production)",
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Host to bind to (default: 127.0.0.1)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8080,
        help="Port to bind to (default: 8080)",
    )
    args = parser.parse_args()

    debug = args.debug or os.environ.get('PYCHESS_DEBUG', '').lower() == 'true'

    app = create_app()
    # Local development entry point. Docker does not call this; it runs
    # `create_app()` under Gunicorn + gevent-websocket instead.
    app.socketio.run(
        app,
        host=args.host,
        port=args.port,
        debug=debug,
        allow_unsafe_werkzeug=True,
    )


if __name__ == '__main__':
    main()
