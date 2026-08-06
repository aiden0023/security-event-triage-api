from app.errors import ConflictError
from app.models.security_event import (
    STATUS_FALSE_POSITIVE,
    STATUS_INVESTIGATING,
    STATUS_NEW,
    STATUS_RESOLVED,
)

ACTION_START = "start"
ACTION_RESOLVE = "resolve"
ACTION_FALSE_POSITIVE = "false_positive"
ACTION_REOPEN = "reopen"
ACTIONS = (ACTION_START, ACTION_RESOLVE, ACTION_FALSE_POSITIVE, ACTION_REOPEN)

_TRANSITIONS: dict[tuple[str, str], str] = {
    (STATUS_NEW, ACTION_START): STATUS_INVESTIGATING,
    (STATUS_NEW, ACTION_RESOLVE): STATUS_RESOLVED,
    (STATUS_NEW, ACTION_FALSE_POSITIVE): STATUS_FALSE_POSITIVE,
    (STATUS_INVESTIGATING, ACTION_RESOLVE): STATUS_RESOLVED,
    (STATUS_INVESTIGATING, ACTION_FALSE_POSITIVE): STATUS_FALSE_POSITIVE,
    (STATUS_RESOLVED, ACTION_REOPEN): STATUS_INVESTIGATING,
    (STATUS_FALSE_POSITIVE, ACTION_REOPEN): STATUS_INVESTIGATING,
}


def next_status(current: str, action: str) -> str:
    """Resolve the (current status, action) pair to the resulting status. Raises ConflictError
    (409) if the action is not legal from the current status."""
    try:
        return _TRANSITIONS[(current, action)]
    except KeyError:
        raise ConflictError(
            f"Cannot {action} an event with status {current}.",
            code="illegal_transition",
        ) from None
