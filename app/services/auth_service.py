from flask import current_app
from flask_jwt_extended import create_access_token

from app.errors import AuthenticationError
from app.extensions import db
from app.models import User
from app.schemas.auth import TokenResponse
from app.services.password import hash_password, verify_password

# Used to hash if email does not exist so it does not return early
_DUMMY_HASH = hash_password("this-is-a-placeholder-for-timing")


def login(email: str, password: str) -> TokenResponse:
    """Authenticate and issue an access token, or raise an exception."""
    user = _authenticate(email, password)
    if user is None:
        raise AuthenticationError("Invalid email or password.", code="invalid_credentials")
    expires = current_app.config["JWT_ACCESS_TOKEN_EXPIRES"]
    return TokenResponse(
        access_token=create_access_token(identity=user),
        expires_in=int(expires.total_seconds()),
    )


def _authenticate(email: str, password: str) -> User | None:
    """Returns the user if credentials are valid, else None."""
    user = db.session.scalar(db.select(User).filter_by(email=email.strip().lower()))
    if user is None:
        verify_password(_DUMMY_HASH, password)
        return None

    if not verify_password(user.password_hash, password):
        return None

    if not user.is_active:
        return None

    return user
