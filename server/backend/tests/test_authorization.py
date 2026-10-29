from fastapi import Depends
from fastapi.testclient import TestClient

from backend.app.core.dependencies import (
    require_admin,
    require_faculty,
    require_technician,
)
from backend.app.main import app
from backend.app.models.user import User
from backend.app.schemas.common import SingleResponse

# Register temporary test routes on the app to verify RBAC dependencies
@app.get("/test/protected/admin", response_model=SingleResponse[dict], tags=["Test"])
def admin_only_test_route(current_user: User = Depends(require_admin)):
    return SingleResponse(data={"message": "Admin granted", "user": current_user.email})


@app.get("/test/protected/faculty", response_model=SingleResponse[dict], tags=["Test"])
def faculty_only_test_route(current_user: User = Depends(require_faculty)):
    return SingleResponse(data={"message": "Faculty granted", "user": current_user.email})


@app.get("/test/protected/technician", response_model=SingleResponse[dict], tags=["Test"])
def technician_only_test_route(current_user: User = Depends(require_technician)):
    return SingleResponse(data={"message": "Technician granted", "user": current_user.email})


def test_auth_me_unauthenticated(client: TestClient):
    """Test accessing /api/v1/auth/me without token returns 401."""
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401
    payload = response.json()
    assert "error" in payload
    assert payload["error"]["code"] == "UNAUTHORIZED"


def test_auth_me_authenticated(client: TestClient, faculty_user: User, faculty_token: str):
    """Test accessing /api/v1/auth/me with valid Bearer token returns user info."""
    headers = {"Authorization": f"Bearer {faculty_token}"}
    response = client.get("/api/v1/auth/me", headers=headers)
    assert response.status_code == 200
    payload = response.json()
    assert "data" in payload
    assert payload["data"]["id"] == faculty_user.id
    assert payload["data"]["email"] == faculty_user.email
    assert payload["data"]["role"] == "FACULTY"


def test_auth_me_deactivated_token_rejected(client: TestClient, inactive_token: str):
    """Test that a deactivated user's token is rejected with 403 Forbidden."""
    headers = {"Authorization": f"Bearer {inactive_token}"}
    response = client.get("/api/v1/auth/me", headers=headers)
    assert response.status_code == 403
    payload = response.json()
    assert "error" in payload
    assert payload["error"]["code"] == "FORBIDDEN"


def test_faculty_cannot_access_admin_route(client: TestClient, faculty_token: str):
    """Verify that a FACULTY role cannot access ADMIN protected dependencies."""
    headers = {"Authorization": f"Bearer {faculty_token}"}
    response = client.get("/test/protected/admin", headers=headers)
    assert response.status_code == 403
    payload = response.json()
    assert payload["error"]["code"] == "FORBIDDEN"
    assert "lacks required permissions" in payload["error"]["message"]


def test_faculty_cannot_access_technician_route(client: TestClient, faculty_token: str):
    """Verify that a FACULTY role cannot access TECHNICIAN protected dependencies."""
    headers = {"Authorization": f"Bearer {faculty_token}"}
    response = client.get("/test/protected/technician", headers=headers)
    assert response.status_code == 403
    payload = response.json()
    assert payload["error"]["code"] == "FORBIDDEN"


def test_admin_can_access_admin_route(client: TestClient, admin_token: str, admin_user: User):
    """Verify that an ADMIN role successfully accesses ADMIN route."""
    headers = {"Authorization": f"Bearer {admin_token}"}
    response = client.get("/test/protected/admin", headers=headers)
    assert response.status_code == 200
    assert response.json()["data"]["user"] == admin_user.email


def test_technician_can_access_technician_route(client: TestClient, technician_token: str, technician_user: User):
    """Verify that a TECHNICIAN role successfully accesses TECHNICIAN route."""
    headers = {"Authorization": f"Bearer {technician_token}"}
    response = client.get("/test/protected/technician", headers=headers)
    assert response.status_code == 200
    assert response.json()["data"]["user"] == technician_user.email


def test_tampered_token_rejected(client: TestClient):
    """Verify that a malformed or forged JWT is rejected with 401."""
    headers = {"Authorization": "Bearer forged.invalid.token"}
    response = client.get("/api/v1/auth/me", headers=headers)
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHORIZED"
