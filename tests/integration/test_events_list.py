from app.models.security_event import SEVERITY_HIGH, SEVERITY_LOW, STATUS_NEW, STATUS_RESOLVED


def _titles(body):
    return [item["title"] for item in body ["items"]]


def test_list_returns_only_own_org_events(
    client, auth_header, customer_analyst, customer_org, other_org, make_event
):
    make_event(org=customer_org, title="mine-1")
    make_event(org=customer_org, title="mine-2")
    make_event(org=other_org, title="theirs")

    response = client.get("/api/events", headers=auth_header(customer_analyst))

    assert response.status_code == 200
    body = response.get_json()
    assert {item["title"] for item in body["items"]} == {"mine-1", "mine-2"}
    assert all(item["org_id"] == customer_org.id for item in body["items"])
    assert body["has_more"] is False
    assert body["next_cursor"] is None


def test_list_is_newest_first(
    client, auth_header, customer_analyst, customer_org, make_event
):
    make_event(org=customer_org, title="oldest")
    make_event(org=customer_org, title="middle")
    make_event(org=customer_org, title="newest")

    response = client.get("/api/events", headers=auth_header(customer_analyst))

    assert _titles(response.get_json()) == ["newest", "middle", "oldest"]


def test_list_empty_when_no_events(client, auth_header, customer_analyst):
    response = client.get("/api/events", headers=auth_header(customer_analyst))

    body = response.get_json()
    assert body["items"] == []
    assert body["has_more"] is False
    assert body["next_cursor"] is None


def test_keyset_walk_has_no_dupes_or_skips(
    client, auth_header, customer_analyst, customer_org, make_event
):
    for i in range(5):
        make_event(org=customer_org, title=f"evt-{i}")

    seen = []
    cursor = None
    pages = 0
    while True:
        params = {"limit": 2}
        if cursor:
            params["after"] = cursor
        response = client.get(
            "/api/events",
            query_string=params,
            headers=auth_header(customer_analyst)
        )
        assert response.status_code == 200
        body = response.get_json()
        seen.extend(_titles(body))
        pages += 1
        if not body["has_more"]:
            assert body["next_cursor"] is None
            break
        cursor = body["next_cursor"]
        assert cursor is not None

    assert seen == ["evt-4", "evt-3", "evt-2", "evt-1", "evt-0"]
    assert pages == 3


def test_list_filters_by_status(
    client, auth_header, customer_analyst, customer_org, make_event
):
    make_event(org=customer_org, title="new-one", status=STATUS_NEW)
    make_event(org=customer_org, title="resolved-one", status=STATUS_RESOLVED)

    response = client.get(
        "/api/events",
        query_string={"status": STATUS_RESOLVED},
        headers=auth_header(customer_analyst)
    )

    assert _titles(response.get_json()) == ["resolved-one"]


def test_list_filters_by_severity(
    client, auth_header, customer_analyst, customer_org, make_event
):
    make_event(org=customer_org, title="low-one", severity=SEVERITY_LOW)
    make_event(org=customer_org, title="high-one", severity=SEVERITY_HIGH)

    response = client.get(
        "/api/events",
        query_string={"severity": SEVERITY_HIGH},
        headers=auth_header(customer_analyst)
    )
    assert _titles(response.get_json()) == ["high-one"]


def test_list_rejects_bad_filter_value(client, auth_header, customer_analyst):
    response = client.get(
        "/api/events",
        query_string={"status": "not-a-status"},
        headers=auth_header(customer_analyst)
    )
    assert response.status_code == 422


def test_list_rejects_bad_cursor(client, auth_header, customer_analyst):
    response = client.get(
        "/api/events",
        query_string={"after": "not-a-cursor"},
        headers=auth_header(customer_analyst)
    )
    assert response.status_code == 400
    assert response.get_json()["error"]["code"] == "invalid_cursor"


def test_list_rejects_unknown_query_param(client, auth_header, customer_analyst):
    response = client.get(
        "/api/events",
        query_string={"not-a-param": "0"},
        headers=auth_header(customer_analyst)
    )
    assert response.status_code == 422


def test_list_requires_authentication(client):
    response = client.get("/api/events")
    assert response.status_code == 401
