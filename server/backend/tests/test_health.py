from fastapi.testclient import TestClient


def test_root_health_endpoint(client: TestClient):
    """Test root /health endpoint returns healthy status and standard data format."""
    response = client.get("/health")
    assert response.status_code == 200
    payload = response.json()
    assert "data" in payload
    data = payload["data"]
    assert data["status"] == "healthy"
    assert "timestamp" in data
    assert data["services"]["database"] == "connected"


def test_api_v1_health_endpoint(client: TestClient):
    """Test versioned /api/v1/health endpoint."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    payload = response.json()
    assert "data" in payload
    data = payload["data"]
    assert data["status"] == "healthy"
    assert data["services"]["database"] == "connected"


def test_openapi_documentation_accessible(client: TestClient):
    """Test that FastAPI OpenAPI swagger documentation and schema are accessible."""
    docs_response = client.get("/docs")
    assert docs_response.status_code == 200
    assert "Swagger UI" in docs_response.text or "swagger-ui" in docs_response.text

    schema_response = client.get("/openapi.json")
    assert schema_response.status_code == 200
    schema = schema_response.json()
    assert "openapi" in schema
    assert "/health" in schema["paths"]
    assert "/api/v1/health" in schema["paths"]
    assert "/api/v1/auth/google" in schema["paths"]
    assert "/api/v1/auth/me" in schema["paths"]
