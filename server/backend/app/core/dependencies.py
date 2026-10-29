from typing import Callable, List
from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.core.exceptions import ForbiddenException, UnauthorizedException
from backend.app.core.security import decode_access_token
from backend.app.db.session import get_db
from backend.app.models.enums import UserRole
from backend.app.models.user import User

bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    """Dependency that authenticates the user via JWT Bearer token."""
    if not credentials or not credentials.credentials:
        raise UnauthorizedException("Authentication token is missing. Please log in.")

    token = credentials.credentials
    payload = decode_access_token(token)

    user_id = payload.get("sub")
    if not user_id:
        raise UnauthorizedException("Invalid token payload: missing subject")

    stmt = select(User).where(User.id == user_id)
    user = db.execute(stmt).scalar_one_or_none()

    if not user:
        raise UnauthorizedException("User associated with this token no longer exists")

    return user


def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Dependency that verifies the authenticated user account is active."""
    if not current_user.is_active:
        raise ForbiddenException("Your account is deactivated. Contact an administrator.")
    return current_user


def require_role(*allowed_roles: UserRole) -> Callable[[User], User]:
    """Dependency factory enforcing role-based access control."""

    def role_checker(
        current_user: User = Depends(get_current_active_user),
    ) -> User:
        if current_user.role not in allowed_roles:
            allowed_names = [r.value for r in allowed_roles]
            raise ForbiddenException(
                message=f"Access forbidden: role '{current_user.role.value}' lacks required permissions. Allowed roles: {allowed_names}",
                details={"user_role": current_user.role.value, "required_roles": allowed_names},
            )
        return current_user

    return role_checker


# Canonical role-based authorization dependencies
require_admin = require_role(UserRole.ADMIN)
require_faculty = require_role(UserRole.FACULTY)
require_technician = require_role(UserRole.TECHNICIAN)
require_faculty_or_admin = require_role(UserRole.FACULTY, UserRole.ADMIN)
require_technician_or_admin = require_role(UserRole.TECHNICIAN, UserRole.ADMIN)
