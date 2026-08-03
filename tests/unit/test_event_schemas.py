from typing import get_args

from app.models.security_event import SEVERITIES, STATUSES
from app.schemas.events import Severity, Status


def test_severity_literal_matches_model_constants():
    assert set(get_args(Severity)) == set(SEVERITIES)


def test_status_literal_matches_model_constants():
    assert set(get_args(Status)) == set(STATUSES)