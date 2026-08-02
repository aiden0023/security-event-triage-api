from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError

_password_hasher = PasswordHasher()


def hash_password(password: str) -> str:
    """Return an argon2id hash string for the given password."""
    return _password_hasher.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    """Return True if the given password matches the given hashed password."""
    try:
        return _password_hasher.verify(password, hashed_password)
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return False
