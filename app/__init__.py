import os

from flask import Flask

from app.config import config_by_name
from app.extensions import db, jwt, limiter, migrate


def create_app(config_name: str | None = None) -> Flask:
    """Build an instance of the Flask application."""
    app = Flask(__name__)

    config_name = config_name or os.environ.get("APP_CONFIG", "dev")
    if config_name not in config_by_name:
        raise RuntimeError(f"Unknown config name: {config_name}")
    app.config.from_object(config_by_name[config_name])
    app.config["CONFIG_NAME"] = config_name

    _verify_required_settings(app)
    _register_extensions(app)
    _register_error_handlers(app)
    _register_blueprints(app)
    _register_cli(app)

    return app


def _verify_required_settings(app: Flask) -> None:
    missing = [name for name in app.config.get("REQUIRED_SETTINGS", ()) if not app.config.get(name)]
    if missing:
        raise RuntimeError(f"Missing required settings: {missing}")


def _register_extensions(app: Flask) -> None:
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    limiter.init_app(app)

    from app.auth import register_jwt_callbacks
    register_jwt_callbacks(app)

    # Imported for the side effect of registering models on Base.metadata
    from app import models  # noqa: F401


def _register_blueprints(app: Flask) -> None:
    # Defer imports to call time to make sure every module is fully loaded before
    # any route is imported
    from app.routes.auth import bp as auth_bp
    from app.routes.events import bp as events_bp
    from app.routes.health import bp as health_bp
    app.register_blueprint(health_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(events_bp)


def _register_cli(app: Flask) -> None:
    # Defer imports to call time to make sure models and db are imported first.
    from app.cli import register_cli
    register_cli(app)


def _register_error_handlers(app: Flask) -> None:
    # Deferred import
    from app.errors import register_error_handlers
    register_error_handlers(app)
