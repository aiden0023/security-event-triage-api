import logging
from datetime import datetime

from flask import current_app, g
from sqlalchemy import tuple_
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.extensions import db
from app.models import SecurityEvent
from app.pagination import decode_cursor, encode_cursor
from app.schemas.events import EventIngest, EventPage, EventQuery

logger = logging.getLogger(__name__)


def ingest(org_id: int, payload: EventIngest) -> tuple[SecurityEvent, bool]:
    """Idempotently stores an event and returns (event, created)."""
    data = payload.model_dump()
    data["org_id"] = org_id
    if data["source_ip"] is not None:
        data["source_ip"] = str(data["source_ip"])

    stmt = (
        pg_insert(SecurityEvent)
        .values(**data)
        .on_conflict_do_nothing(index_elements=["org_id", "source", "external_id"])
        .returning(SecurityEvent.id)
    )
    new_id = db.session.execute(stmt).scalar_one_or_none()
    db.session.commit()

    if new_id is not None:
        return db.session.get(SecurityEvent, new_id), True

    existing = db.session.scalar(
        db.select(SecurityEvent).filter_by(
            org_id=org_id,
            source=data["source"],
            external_id=data["external_id"],
        )
    )
    return existing, False


def visible_events(
    org_id: int,
    *,
    limit: int,
    status: str | None = None,
    severity: str | None = None,
    after: tuple[datetime, int] | None = None
) -> tuple[list[SecurityEvent], bool]:
    """One page of an org's events with the newsest first. Returns (events, has_more)."""
    stmt = db.select(SecurityEvent).where(SecurityEvent.org_id == org_id)

    if status is not None:
        stmt = stmt.where(SecurityEvent.status == status)
    if severity is not None:
        stmt = stmt.where(SecurityEvent.severity == severity)
    if after is not None:
        stmt = stmt.where(
            tuple_(SecurityEvent.occurred_at, SecurityEvent.id) < tuple_(*after)
        )

    stmt = stmt.order_by(
        SecurityEvent.occurred_at.desc(), SecurityEvent.id.desc()
    ).limit(limit + 1)

    rows = db.session.scalars(stmt).all()
    has_more = len(rows) > limit
    return list(rows[:limit]), has_more


def list_events_page(org_id: int, query: EventQuery) -> EventPage:
    limit = min(
        query.limit or current_app.config["DEFAULT_PAGE_SIZE"],
        current_app.config["MAX_PAGE_SIZE"],
    )
    after = decode_cursor(query.after) if query.after else None

    events, has_more = visible_events(
        org_id=org_id, limit=limit, status=query.status, severity=query.severity, after=after
    )
    next_cursor = encode_cursor(events[-1].occurred_at, events[-1].id) if has_more else None
    return EventPage(items=events, next_cursor=next_cursor, has_more=has_more)


def find_event(org_id: int, event_id: int) -> SecurityEvent | None:
    """Find an event scoped to an org. Returns None if event is missing
    OR is owned by a different org."""
    event = db.session.scalar(
        db.select(SecurityEvent).where(
            SecurityEvent.id == event_id,
            SecurityEvent.org_id == org_id
        )
    )
    if event is None:
        _log_lookup_miss(org_id, event_id)
    return event


def _log_lookup_miss(org_id: int, event_id: int) -> None:
    """Server-side only: was this a real 404, or a blocked cross-tenant read?"""
    owner_org_id = db.session.scalar(
        db.select(SecurityEvent.org_id).where(SecurityEvent.id == event_id)
    )

    context = {
        "request_id": g.get("request_id"),
        "actor_org_id": org_id,
        "event_id": event_id,
        "owner_org_id": owner_org_id,
    }

    if owner_org_id is not None:
        logger.warning("event_lookup_denied", extra=context)
    else:
        logger.info("event_lookup_missing", extra=context)
