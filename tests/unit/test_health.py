from app import create_app


def test_health_endpoint_returns_200():
    client = create_app("test").test_client()
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}
