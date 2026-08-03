from flask import Blueprint, request
from flask_jwt_extended import current_user, jwt_required

from app.schemas.events import EventIngest, EventQuery, EventResponse
from app.services import event_service

bp = Blueprint("events", __name__, url_prefix="/api/events")


@bp.post("")
@jwt_required()
def create_event():
    payload = EventIngest.model_validate(request.get_json(silent=True) or {})
    event, created = event_service.ingest(current_user.org_id, payload)
    body = EventResponse.model_validate(event).model_dump(mode="json")
    return body, (201 if created else 200)


@bp.get("")
@jwt_required()
def list_events():
    query = EventQuery.model_validate(request.args.to_dict())
    page = event_service.list_events_page(current_user.org_id, query)
    return page.model_dump(mode="json"), 200
