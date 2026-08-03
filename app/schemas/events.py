from datetime import datetime
from typing import Any, Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, IPvAnyAddress

Severity = Literal["low", "medium", "high", "critical"]
Status = Literal["new", "investigating", "resolved", "false_positive"]


class EventIngest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    source: str = Field(min_length=1, max_length=60)
    external_id: str = Field(min_length=1, max_length=120)
    title: str = Field(min_length=1, max_length=200)
    description: str | None = None
    event_type: str = Field(min_length=1, max_length=60)
    severity: Severity
    source_ip: IPvAnyAddress | None = None
    occurred_at: AwareDatetime
    raw: dict[str, Any] = Field(default_factory=dict)


class EventQuery(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    limit: int | None = Field(default=None, ge=1)
    after: str | None = None
    status: Status | None = None
    severity: Severity | None = None


class EventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    org_id: int
    source: str
    external_id: str
    title: str
    description: str | None
    event_type: str
    severity: str
    source_ip: IPvAnyAddress | None
    status: str
    assigned_to_id: int | None
    occurred_at: datetime
    created_at: datetime
    updated_at: datetime


class EventPage(BaseModel):
    items: list[EventResponse]
    next_cursor: str | None
    has_more: bool


class EventDetail(EventResponse):
    raw: dict[str, Any]
