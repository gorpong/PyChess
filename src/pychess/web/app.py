"""Flask application factory for PyChess web UI."""

import os
import secrets

from flask import Flask

from pychess.web import routes


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
    
    # Default configuration
    # Generate a secure secret key if not provided
    default_secret = os.environ.get('SECRET_KEY')
    if default_secret is None:
        default_secret = secrets.token_hex(32)
    
    app.config.from_mapping(
        SECRET_KEY=default_secret,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE='Lax',
    )
    
    # Override with test config if provided
    if test_config is not None:
        app.config.from_mapping(test_config)
    
    # Register routes
    app.register_blueprint(routes.bp)
    
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
    
    # Environment variable can also enable debug mode
    debug = args.debug or os.environ.get('PYCHESS_DEBUG', '').lower() == 'true'
    
    app = create_app()
    app.run(host=args.host, port=args.port, debug=debug)


if __name__ == '__main__':
    main()
