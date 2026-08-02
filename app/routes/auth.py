from flask import Blueprint, request

from app import limiter
from app.schemas.auth import LoginRequest
from app.services import auth_service

bp = Blueprint("auth", __name__, url_prefix="/api/auth")


@bp.post("/login")
@limiter.limit("5 per minute")
def login():
    payload = LoginRequest.model_validate(request.get_json(silent=True) or {})
    return auth_service.login(payload.email, payload.password).model_dump(), 200
