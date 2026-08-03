from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from itertools import count

import pytest
from flask import Flask
from flask.testing import FlaskClient
from flask_jwt_extended import create_access_token
from sqlalchemy import text
from sqlalchemy.orm import Session

from app import create_app
from app.extensions import db as _db
from app.models import Organization, SecurityEvent, User
from app.models.security_event import SEVERITY_MEDIUM, STATUS_NEW
from app.models.user import ROLE_ADMIN, ROLE_ANALYST
from app.services.password import hash_password

TEST_PASSWORD = "test-password"
_TEST_PASSWORD_HASH = hash_password(TEST_PASSWORD)
_EVENT_BASE_TIME = datetime(2026, 1, 1, tzinfo=UTC)
_org_counter = count(1)
_user_counter = count(1)
_event_counter = count(1)


@pytest.fixture(scope="session")
def app() -> Flask:
    application = create_app("test")
    with application.app_context():
        _db.create_all()
        yield application
        _db.drop_all()


@pytest.fixture
def session(app: Flask) -> Session:
    yield _db.session
    _db.session.rollback()
    tables = ", ".join(f'"{table.name}"' for table in _db.metadata.sorted_tables)
    _db.session.execute(text(f"TRUNCATE {tables} RESTART IDENTITY CASCADE"))
    _db.session.commit()


@pytest.fixture
def client(app: Flask) -> FlaskClient:
    return app.test_client()


@pytest.fixture
def make_org(session: Session) -> Callable[..., Organization]:
    def _make(name: str | None = None, *, is_provider: bool = False) -> Organization:
        org = Organization(
            name=name or f"Test Org {next(_org_counter)}",
            is_provider=is_provider,
        )
        session.add(org)
        session.flush()
        return org
    return _make


@pytest.fixture
def make_user(session: Session) -> Callable[..., User]:
    def _make(
        *,
        org: Organization,
        role: str = ROLE_ANALYST,
        email: str | None = None,
        is_active: bool = True,
    ) -> User:
        user = User(
            email=email or f"user{next(_user_counter)}@test.example",
            org_id=org.id,
            role=role,
            password_hash=_TEST_PASSWORD_HASH,
            is_active=is_active,
        )
        session.add(user)
        session.flush()
        return user
    return _make


@pytest.fixture
def make_event(session: Session) -> Callable[..., SecurityEvent]:
    def _make(
        *,
        org: Organization,
        occurred_at: datetime | None = None,
        severity: str = SEVERITY_MEDIUM,
        status: str = STATUS_NEW,
        source: str = "pytest",
        external_id: str | None = None,
        title: str = "Test Event",
        event_type: str = "test",
        source_ip: str | None = None,
        description: str | None = None,
        assigned_to: User | None = None,
        raw: dict | None = None,
    ) -> SecurityEvent:
        n = next(_event_counter)
        event = SecurityEvent(
            org_id=org.id,
            source=source,
            external_id=external_id or f"evt-{n}",
            title=title,
            event_type=event_type,
            severity=severity,
            status=status,
            source_ip=source_ip,
            description=description,
            raw=raw if raw is not None else {},
            occurred_at=occurred_at or (_EVENT_BASE_TIME + timedelta(minutes=n)),
            assigned_to_id=assigned_to.id if assigned_to else None,
        )
        session.add(event)
        session.flush()
        return event
    return _make


@pytest.fixture
def auth_header(app: Flask) -> Callable[[User], dict[str, str]]:
    def _header(user: User) -> dict[str, str]:
        return {"Authorization": f"Bearer {create_access_token(identity=user)}"}
    return _header


@pytest.fixture
def provider_org(make_org) -> Organization:
    return make_org("Provider Company", is_provider=True)


@pytest.fixture
def customer_org(make_org) -> Organization:
    return make_org("Company One", is_provider=False)


@pytest.fixture
def other_org(make_org) -> Organization:
    return make_org("Company Two", is_provider=False)


@pytest.fixture
def provider_admin(make_user, provider_org) -> User:
    return make_user(org=provider_org, role=ROLE_ADMIN)


@pytest.fixture
def customer_admin(make_user, customer_org) -> User:
    return make_user(org=customer_org, role=ROLE_ADMIN)


@pytest.fixture
def customer_analyst(make_user, customer_org) -> User:
    return make_user(org=customer_org, role=ROLE_ANALYST)


@pytest.fixture
def other_admin(make_user, other_org) -> User:
    return make_user(org=other_org, role=ROLE_ADMIN)


@pytest.fixture
def other_analyst(make_user, other_org) -> User:
    return make_user(org=other_org, role=ROLE_ANALYST)
