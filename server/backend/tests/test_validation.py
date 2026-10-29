import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from backend.app.models.enums import UserRole
from backend.app.schemas.user import UserCreate


def test_validation_error_structure_on_bad_request(client: TestClient):
    """Verify that 422 validation errors conform strictly to the standard error response shape."""
    # POST /api/v1/auth/google expects {"id_token": str}
    response = client.post("/api/v1/auth/google", json={"wrong_field": 123})
    assert response.status_code == 422
    payload = response.json()

    assert "error" in payload
    error = payload["error"]
    assert error["code"] == "VALIDATION_ERROR"
    assert "message" in error
    assert "details" in error
    assert "validation_errors" in error["details"]
    assert len(error["details"]["validation_errors"]) > 0


def test_auth_google_short_token_validation(client: TestClient):
    """Verify that id_token min_length constraint triggers validation error."""
    response = client.post("/api/v1/auth/google", json={"id_token": "tiny"})
    assert response.status_code == 422
    payload = response.json()
    assert payload["error"]["code"] == "VALIDATION_ERROR"


def test_user_schema_invalid_role():
    """Verify that Pydantic rejects invalid user roles during schema instantiation."""
    with pytest.raises(ValidationError) as exc_info:
        UserCreate(
            email="valid@classroom.edu",
            name="Valid Name",
            role="SUPER_HACKER",  # Invalid role
        )
    assert "Input should be 'ADMIN', 'FACULTY' or 'TECHNICIAN'" in str(exc_info.value)


def test_404_error_structure_on_unknown_endpoint(client: TestClient):
    """Verify that 404 response on unknown endpoints returns consistent error structure."""
    response = client.get("/api/v1/non-existent-endpoint")
    assert response.status_code == 404
    payload = response.json()
    assert "error" in payload
    assert payload["error"]["code"] == "HTTP_ERROR"
