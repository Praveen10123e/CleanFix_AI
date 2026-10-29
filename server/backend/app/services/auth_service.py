import logging
from typing import Tuple
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.core.config import get_settings
from backend.app.core.exceptions import ForbiddenException, UnauthorizedException
from backend.app.core.security import create_access_token, verify_google_id_token
from backend.app.models.audit_log import AuditLog
from backend.app.models.user import User

logger = logging.getLogger(__name__)
settings = get_settings()


class AuthService:
    """Service handling Google OAuth verification and user session authentication."""

    def authenticate_google_user(self, db: Session, id_token_str: str) -> Tuple[User, str]:
        # 1. Verify Google ID token claims server-side
        claims = verify_google_id_token(id_token_str, settings.google_client_id)

        google_sub = claims.get("sub")
        email = claims.get("email")

        if not google_sub or not email:
            raise UnauthorizedException("Google token missing required subject or email claims.")

        # Validate verified email claim
        email_verified = claims.get("email_verified")
        if email_verified is not True and str(email_verified).lower() != "true":
            raise UnauthorizedException("Google email address is unverified. Verified email claim required.")

        normalized_email = email.strip().lower()

        # 2. Look up provisioned user by email
        stmt = select(User).where(User.email == normalized_email)
        user = db.execute(stmt).scalar_one_or_none()

        # Reject unprovisioned accounts
        if not user:
            logger.warning("Unprovisioned login attempt: %s (sub: %s)", normalized_email, google_sub)
            raise UnauthorizedException(
                message="Account not found. Your Google account must be provisioned by a system administrator.",
                details={"email": normalized_email},
            )

        # 3. Check for Google identity mismatch
        if user.google_sub is not None and user.google_sub != google_sub:
            logger.warning(
                "Google subject mismatch for %s: provisioned=%s, incoming=%s",
                user.email,
                user.google_sub,
                google_sub,
            )
            raise UnauthorizedException(
                message="Google identity mismatch. This account is already linked to a different Google account.",
                details={"email": normalized_email},
            )

        # 4. First-time login: link google_sub to provisioned account
        if user.google_sub is None:
            # Check if this google_sub was somehow associated with another user
            stmt_sub = select(User).where(User.google_sub == google_sub)
            existing_sub_user = db.execute(stmt_sub).scalar_one_or_none()
            if existing_sub_user and existing_sub_user.id != user.id:
                raise UnauthorizedException(
                    message="This Google identity is already linked to another provisioned account.",
                    details={"google_sub": google_sub},
                )

            user.google_sub = google_sub
            db.add(user)
            db.commit()
            db.refresh(user)
            logger.info("Successfully linked google_sub '%s' to user '%s'", google_sub, user.email)

        # 5. Check if user is active
        if not user.is_active:
            logger.warning("Deactivated user login attempt: %s", user.email)
            raise ForbiddenException(
                message="Your account has been deactivated. Please contact your administrator.",
                details={"user_id": user.id},
            )

        # 6. Issue application JWT access token
        access_token = create_access_token(
            data={
                "sub": user.id,
                "email": user.email,
                "role": user.role.value,
            }
        )

        # 7. Record login audit log
        audit = AuditLog(
            actor_id=user.id,
            action="USER_LOGIN",
            entity_type="USER",
            entity_id=user.id,
        )
        db.add(audit)
        db.commit()

        logger.info("User authenticated successfully: %s [%s]", user.email, user.role.value)
        return user, access_token


auth_service = AuthService()
