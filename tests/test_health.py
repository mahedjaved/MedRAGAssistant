def test_health_endpoint_returns_200(client):
    response = client.get("/health")
    assert response.status_code == 200


def test_health_endpoint_has_expected_structure(client):
    response = client.get("/health")
    data = response.json()
    assert "status" in data
    assert "version" in data
    assert "checks" in data
    assert data["version"] == "1.0"
    assert data["status"] in ("healthy", "degraded", "unhealthy")
    assert "pinecone" in data["checks"]
    assert "groq_api" in data["checks"]