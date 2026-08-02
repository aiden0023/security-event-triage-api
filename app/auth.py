from flask import Flask

from app import db, jwt
from app.errors import error_response
from app.models import User


def register_jwt_callbacks(app: Flask) -> None:
    @jwt.user_identity_loader
    def _user_identity(user: User) -> str:
        return str(user.id)

    @jwt.user_lookup_loader
    def _user_lookup(_jwt_header: dict, jwt_data: dict) -> User | None:
        """Resolves the token subject to a live user on every protected request."""
        try:
            user_id = int(jwt_data["sub"])
        except (ValueError, TypeError, KeyError):
            return None
        user = db.session.get(User, user_id)
        if user is None or not user.is_active:
            return None
        return user

    @jwt.user_lookup_error_loader
    def _user_lookup_error(_jwt_header: dict, _jwt_data: dict):
        return error_response(401, "authentication_failed", "Authentication is required.")

    @jwt.unauthorized_loader
    def _missing_token(_reason: str):
        return error_response(401, "authentication_required", "Authentication is required.")

    @jwt.invalid_token_loader
    def _invalid_token(_reason: str):
        return error_response(401, "invalid_token", "The token is invalid.")

    @jwt.expired_token_loader
    def _expired_token(_jwt_header: dict, _jwt_data: dict):
        return error_response(401, "token_expired", "The token has expired.")
