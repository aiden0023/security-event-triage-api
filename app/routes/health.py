from flask import Blueprint, jsonify

bp = Blueprint("health", __name__, url_prefix="/api")


@bp.get("/health")
def health():
    """Returns 200 if Flask started."""
    return jsonify({"status": "ok"}), 200
