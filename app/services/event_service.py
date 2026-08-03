from datetime import datetime

from flask import current_app
from sqlalchemy import tuple_
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.extensions import db
from app.models import SecurityEvent
from app.pagination import decode_cursor, encode_cursor
from app.schemas.events import EventIngest, EventPage, EventQuery


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
