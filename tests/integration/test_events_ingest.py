VALID_EVENT = {
    "source": "crowdstrike",
    "external_id": "evt-001",
    "title": "Suspicious Login",
    "event_type": "authentication",
    "severity": "high",
    "source_ip": "203.0.113.7",
    "occurred_at": "2026-08-03T12:00:00+00:00",
    "raw": {"vendor": "crowdstrike", "score": 92},
}


def test_ingest_creates_events(client, auth_header, customer_analyst, customer_org):
    response = client.post("/api/events", json=VALID_EVENT, headers=auth_header(customer_analyst))

    assert response.status_code == 201
    body = response.get_json()
    assert body["org_id"] == customer_org.id
    assert body["status"] == "new"
    assert body["severity"] == "high"
    assert body["source_ip"] == "203.0.113.7"
    assert "raw" not in body
    assert body["occurred_at"] == "2026-08-03T12:00:00Z"


def test_ingest_is_idempotent(client, auth_header, customer_analyst):
    headers = auth_header(customer_analyst)
    first = client.post("/api/events", json=VALID_EVENT, headers=headers)
    second = client.post("/api/events", json=VALID_EVENT, headers=headers)

    assert first.status_code == 201
    assert second.status_code == 200
    assert first.get_json()["id"] == second.get_json()["id"]


def test_ingest_rejects_org_id_in_body(client, auth_header, customer_analyst):
    payload = {**VALID_EVENT, "org_id": 99999}
    response = client.post("/api/events", json=payload, headers=auth_header(customer_analyst))

    assert response.status_code == 422


def test_ingest_requires_authentication(client):
    response = client.post("/api/events", json=VALID_EVENT)

    assert response.status_code == 401


def test_ingest_rejects_unknown_severity(client, auth_header, customer_analyst):
    payload = {**VALID_EVENT, "severity": "catastrophic"}
    response = client.post("/api/events", json=payload, headers=auth_header(customer_analyst))

    assert response.status_code == 422
