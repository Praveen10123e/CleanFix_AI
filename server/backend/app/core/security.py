from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional
import jwt
from google.auth.transport import requests
from google.oauth2 import id_token as google_id_token

from backend.app.core.config import get_settings
from backend.app.core.exceptions import UnauthorizedException

settings = get_settings()


def create_access_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Create a signed JWT access token for application authorization."""
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.jwt_access_token_expire_minutes)

    to_encode.update({"iat": now, "exp": expire})
    encoded_jwt = jwt.encode(
        to_encode,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )
    return encoded_jwt


def decode_access_token(token: str) -> Dict[str, Any]:
    """Decode and validate a signed JWT access token."""
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise UnauthorizedException("Access token has expired")
    except jwt.InvalidTokenError:
        raise UnauthorizedException("Invalid access token")


def verify_google_id_token(token: str, client_id: Optional[str] = None) -> Dict[str, Any]:
    """Verify Google OAuth 2.0 ID token against Google certs and target audience.

    Validates token signature, issuer, audience against GOOGLE_CLIENT_ID,
    expiry, and email_verified claim.
    """
    target_client_id = client_id or settings.google_client_id
    try:
        request = requests.Request()
        id_info = google_id_token.verify_oauth2_token(
            token,
            request,
            audience=target_client_id,
        )

        # Validate issuer
        iss = id_info.get("iss")
        if iss not in ("accounts.google.com", "https://accounts.google.com"):
            raise UnauthorizedException(f"Invalid Google token issuer: '{iss}'.")

        # Validate email_verified claim
        email_verified = id_info.get("email_verified")
        if email_verified is not True and str(email_verified).lower() != "true":
            raise UnauthorizedException("Google account email is unverified.")

        return id_info
    except ValueError as e:
        err_msg = str(e)
        if "expir" in err_msg.lower():
            raise UnauthorizedException("Google ID token has expired. Please sign in again.")
        elif "audience" in err_msg.lower() or "recipient" in err_msg.lower():
            raise UnauthorizedException("Google ID token audience mismatch. Invalid Client ID.")
        raise UnauthorizedException(f"Google ID token verification failed: {err_msg}")
    except UnauthorizedException:
        raise
    except Exception as e:
        raise UnauthorizedException(f"Authentication token verification error: {str(e)}")
