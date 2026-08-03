import base64
import binascii
from datetime import datetime

from app.errors import BadRequestError


def encode_cursor(occurred_at: datetime, event_id: int) -> str:
    """Create a url-safe base64 cursor of '<timestamp>|<event_id>'."""
    raw = f"{occurred_at.isoformat()}|{event_id}"
    return base64.urlsafe_b64encode(raw.encode()).decode()


def decode_cursor(cursor: str) -> tuple[datetime, int]:
    """Decode the cursor from encode_cursor. Raises BadRequestError if anything with the cursor
    is malformed."""
    try:
        raw = base64.urlsafe_b64decode(cursor.encode()).decode()
        ts_str, id_str = raw.rsplit("|", maxsplit=1)
        return datetime.fromisoformat(ts_str), int(id_str)
    except (ValueError, binascii.Error) as exc:
        raise BadRequestError("Invalid pagination cursor.", code="invalid_cursor") from exc