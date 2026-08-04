import logging

from app.models.security_event import SEVERITY_HIGH


def _error(response):
    return response.get_json()["error"]


def test_get_event_returns_detail_with_raw(
    client, auth_header, customer_analyst, customer_org, make_event
):
    event = make_event(
        org=customer_org,
        title="Suspicious login",
        severity=SEVERITY_HIGH,
        source_ip="203.0.113.10",
        raw={"vendor": "crowdstrike", "score": 9},
    )
    event_id = event.id

    response = client.get(
        f"/api/events/{event_id}", headers=auth_header(customer_analyst)
    )

    assert response.status_code == 200
    body = response.get_json()
    assert body["id"] == event_id
    assert body["org_id"] == customer_org.id
    assert body["title"] == "Suspicious login"
    assert body["severity"] == SEVERITY_HIGH
    assert body["source_ip"] == "203.0.113.10"
    assert body["raw"] == {"vendor": "crowdstrike", "score": 9}


def test_get_event_cross_tenant_returns_404(
    client, auth_header, customer_analyst, other_org, make_event
):
    event = make_event(org=other_org, title="Not yours")
    response = client.get(
        f"/api/events/{event.id}", headers=auth_header(customer_analyst)
    )
    assert response.status_code == 404
    assert _error(response)["code"] == "not_found"


def test_get_event_missing_returns_404(client, auth_header, customer_analyst):
    response = client.get("/api/events/9999999", headers=auth_header(customer_analyst))
    assert response.status_code == 404
    assert _error(response)["code"] == "not_found"


def test_cross_tenant_is_indistinguishable_from_missing(
    client, auth_header, customer_analyst, other_org, make_event
):
    event = make_event(org=other_org)
    cross_tenant = client.get(
        f"/api/events/{event.id}", headers=auth_header(customer_analyst)
    )
    missing = client.get("/api/events/9999999", headers=auth_header(customer_analyst))

    assert cross_tenant.status_code == missing.status_code
    cross_body, missing_body = _error(cross_tenant), _error(missing)
    cross_body.pop("request_id")
    missing_body.pop("request_id")
    assert cross_body == missing_body


def test_get_event_requires_auth(client, customer_org, make_event):
    event = make_event(org=customer_org)
    response = client.get(f"/api/events/{event.id}")
    assert response.status_code == 401


def test_get_event_rejects_non_integer_id(client, auth_header, customer_analyst):
    response = client.get("/api/events/abc", headers=auth_header(customer_analyst))
    assert response.status_code == 404


def test_cross_tenant_lookup_is_logged_as_denied(
    client, auth_header, customer_analyst, customer_org, other_org, make_event, caplog
):
    event = make_event(org=other_org)
    event_id = event.id

    with caplog.at_level(logging.INFO, logger="app.services.event_service"):
        client.get(f"/api/events/{event_id}", headers=auth_header(customer_analyst))

    denied = [record for record in caplog.records if record.msg == "event_lookup_denied"]
    assert len(denied) == 1
    assert denied[0].levelno == logging.WARNING
    assert denied[0].actor_org_id == customer_org.id
    assert denied[0].owner_org_id == other_org.id
    assert denied[0].event_id == event_id
    assert denied[0].request_id is not None


def test_missing_lookup_is_not_logged_as_denied(
    client, auth_header, customer_analyst, caplog
):
    with caplog.at_level(logging.INFO, logger="app.services.event_service"):
        client.get("/api/events/9999999", headers=auth_header(customer_analyst))

    messages = [record.msg for record in caplog.records]
    assert "event_lookup_missing" in messages
    assert "event_lookup_denied" not in messages
