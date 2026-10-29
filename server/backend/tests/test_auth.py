from unittest.mock import MagicMock, patch
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.core.exceptions import UnauthorizedException
from backend.app.core.security import verify_google_id_token
from backend.app.models.audit_log import AuditLog
from backend.app.models.enums import UserRole
from backend.app.models.user import User


# =============================================================================
# 1. TOKEN VALIDATION REJECTION TESTS (MALFORMED, WRONG AUDIENCE, EXPIRED)
# =============================================================================

def test_auth_google_invalid_token(client: TestClient):
    """Test that an invalid or malformed Google ID token is rejected with 401."""
    with patch(
        "backend.app.services.auth_service.verify_google_id_token",
        side_effect=UnauthorizedException("Google ID token verification failed: Invalid signature"),
    ):
        response = client.post(
            "/api/v1/auth/google",
            json={"id_token": "malformed_dummy_token_xyz_123"},
        )
        assert response.status_code == 401
        payload = response.json()
        assert "error" in payload
        assert payload["error"]["code"] == "UNAUTHORIZED"
        assert "Google ID token verification failed" in payload["error"]["message"]


def test_auth_google_wrong_audience(client: TestClient):
    """Test that a Google token with wrong audience is rejected with 401."""
    with patch(
        "backend.app.core.security.google_id_token.verify_oauth2_token",
        side_effect=ValueError("Token used with wrong audience"),
    ):
        response = client.post(
            "/api/v1/auth/google",
            json={"id_token": "token_with_wrong_audience_321"},
        )
        assert response.status_code == 401
        payload = response.json()
        assert payload["error"]["code"] == "UNAUTHORIZED"
        assert "audience" in payload["error"]["message"].lower()


def test_auth_google_expired_token(client: TestClient):
    """Test that an expired Google token is rejected with 401."""
    with patch(
        "backend.app.core.security.google_id_token.verify_oauth2_token",
        side_effect=ValueError("Token used after expiry"),
    ):
        response = client.post(
            "/api/v1/auth/google",
            json={"id_token": "expired_google_jwt_token_456"},
        )
        assert response.status_code == 401
        payload = response.json()
        assert payload["error"]["code"] == "UNAUTHORIZED"
        assert "expired" in payload["error"]["message"].lower()


# =============================================================================
# 2. EMAIL VERIFIED & UNPROVISIONED / INACTIVE REJECTION TESTS
# =============================================================================

def test_auth_google_unverified_email_rejected(client: TestClient, db_session: Session):
    """Test that Google token with unverified email claim is rejected."""
    provisioned_user = User(
        email="unverified.prof@classroom.edu",
        name="Unverified Prof",
        role=UserRole.FACULTY,
        google_sub=None,
        is_active=True,
    )
    db_session.add(provisioned_user)
    db_session.commit()

    mock_claims = {
        "iss": "https://accounts.google.com",
        "sub": "mock_sub_unverified_999",
        "email": "unverified.prof@classroom.edu",
        "name": "Unverified Prof",
        "email_verified": False,
    }
    with patch("backend.app.core.security.google_id_token.verify_oauth2_token", return_value=mock_claims):
        response = client.post(
            "/api/v1/auth/google",
            json={"id_token": "token_unverified_email"},
        )
        assert response.status_code == 401
        payload = response.json()
        assert payload["error"]["code"] == "UNAUTHORIZED"
        assert "unverified" in payload["error"]["message"].lower()


def test_auth_google_unknown_account_rejected(client: TestClient):
    """Test that a valid Google token for an unprovisioned user is rejected."""
    mock_claims = {
        "iss": "https://accounts.google.com",
        "sub": "unknown_google_sub_9999",
        "email": "stranger@classroom.edu",
        "name": "Unknown Stranger",
        "email_verified": True,
    }
    with patch("backend.app.core.security.google_id_token.verify_oauth2_token", return_value=mock_claims):
        response = client.post(
            "/api/v1/auth/google",
            json={"id_token": "valid_token_unregistered_user"},
        )
        assert response.status_code == 401
        payload = response.json()
        assert "error" in payload
        assert "Account not found" in payload["error"]["message"]
        assert payload["error"]["details"]["email"] == "stranger@classroom.edu"


def test_auth_google_deactivated_account_rejected(client: TestClient, inactive_user: User):
    """Test that a deactivated user cannot log in and receives 403 Forbidden."""
    mock_claims = {
        "iss": "https://accounts.google.com",
        "sub": inactive_user.google_sub,
        "email": inactive_user.email,
        "name": inactive_user.name,
        "email_verified": True,
    }
    with patch("backend.app.core.security.google_id_token.verify_oauth2_token", return_value=mock_claims):
        response = client.post(
            "/api/v1/auth/google",
            json={"id_token": "valid_token_deactivated_user"},
        )
        assert response.status_code == 403
        payload = response.json()
        assert "error" in payload
        assert payload["error"]["code"] == "FORBIDDEN"
        assert "deactivated" in payload["error"]["message"]


def test_auth_google_mismatched_identity_rejected(client: TestClient, db_session: Session):
    """Test that if an account is already linked to Google sub A, attempting to log in with sub B is rejected."""
    user = User(
        email="linked.user@classroom.edu",
        name="Linked User",
        role=UserRole.FACULTY,
        google_sub="original_google_sub_111",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()

    mock_claims = {
        "iss": "https://accounts.google.com",
        "sub": "impostor_google_sub_222",
        "email": "linked.user@classroom.edu",
        "name": "Linked User",
        "email_verified": True,
    }
    with patch("backend.app.core.security.google_id_token.verify_oauth2_token", return_value=mock_claims):
        response = client.post(
            "/api/v1/auth/google",
            json={"id_token": "valid_token_mismatched_sub"},
        )
        assert response.status_code == 401
        payload = response.json()
        assert payload["error"]["code"] == "UNAUTHORIZED"
        assert "mismatch" in payload["error"]["message"].lower()


# =============================================================================
# 3. SUCCESSFUL AUTHENTICATION & ALL THREE ROLES
# =============================================================================

@pytest.mark.parametrize(
    "email,name,role,sub",
    [
        ("praveenj.cs24@bitsathy.ac.in", "Praveen J (Admin)", UserRole.ADMIN, "google_sub_admin_praveen"),
        ("dhanushm.cs24@bitsathy.ac.in", "Dhanush M (Faculty)", UserRole.FACULTY, "google_sub_faculty_dhanush"),
        ("thiyaneshd.ad24@bitsathy.ac.in", "Thiyanesh D (Technician)", UserRole.TECHNICIAN, "google_sub_tech_thiyanesh"),
    ],
)
def test_auth_google_all_three_roles_successful(
    client: TestClient,
    db_session: Session,
    email: str,
    name: str,
    role: UserRole,
    sub: str,
):
    """Verify successful authentication and JWT issuance for each of the three required roles."""
    # Ensure provisioned user exists in database
    stmt = select(User).where(User.email == email)
    user = db_session.execute(stmt).scalar_one_or_none()
    if not user:
        user = User(
            email=email,
            name=name,
            role=role,
            google_sub=None,  # First time login links sub
            is_active=True,
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

    mock_claims = {
        "iss": "https://accounts.google.com",
        "sub": sub,
        "email": email,
        "name": name,
        "email_verified": True,
    }
    with patch("backend.app.core.security.google_id_token.verify_oauth2_token", return_value=mock_claims):
        response = client.post(
            "/api/v1/auth/google",
            json={"id_token": f"valid_token_{role.value.lower()}"},
        )
        assert response.status_code == 200
        payload = response.json()
        assert "data" in payload
        data = payload["data"]
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["email"] == email
        assert data["user"]["role"] == role.value
        assert data["user"]["is_active"] is True

        # Verify Google sub was linked
        db_session.refresh(user)
        assert user.google_sub == sub

        # Check audit log recorded
        audit = db_session.execute(
            select(AuditLog).where(AuditLog.actor_id == user.id, AuditLog.action == "USER_LOGIN")
        ).scalar_one_or_none()
        assert audit is not None

        # Verify access token works with GET /api/v1/auth/me
        me_res = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {data['access_token']}"},
        )
        assert me_res.status_code == 200
        me_data = me_res.json()["data"]
        assert me_data["email"] == email
        assert me_data["role"] == role.value


# =============================================================================
# 4. UNIT TEST FOR verify_google_id_token DIRECTLY
# =============================================================================

def test_unit_verify_google_id_token():
    """Unit test verify_google_id_token behavior for valid, bad issuer, and unverified claims."""
    # 1. Valid claims
    good_claims = {
        "iss": "https://accounts.google.com",
        "sub": "sub_valid_123",
        "email": "test@domain.com",
        "email_verified": True,
    }
    with patch("backend.app.core.security.google_id_token.verify_oauth2_token", return_value=good_claims):
        claims = verify_google_id_token("dummy_token", "target_client_id")
        assert claims["sub"] == "sub_valid_123"

    # 2. Bad issuer
    bad_iss_claims = {
        "iss": "https://fake-google-auth.com",
        "sub": "sub_bad_iss",
        "email": "test@domain.com",
        "email_verified": True,
    }
    with patch("backend.app.core.security.google_id_token.verify_oauth2_token", return_value=bad_iss_claims):
        with pytest.raises(UnauthorizedException) as exc_info:
            verify_google_id_token("dummy_token", "target_client_id")
        assert "issuer" in str(exc_info.value.message).lower()

    # 3. Unverified email
    unverified_claims = {
        "iss": "https://accounts.google.com",
        "sub": "sub_unverified",
        "email": "test@domain.com",
        "email_verified": False,
    }
    with patch("backend.app.core.security.google_id_token.verify_oauth2_token", return_value=unverified_claims):
        with pytest.raises(UnauthorizedException) as exc_info:
            verify_google_id_token("dummy_token", "target_client_id")
        assert "unverified" in str(exc_info.value.message).lower()
