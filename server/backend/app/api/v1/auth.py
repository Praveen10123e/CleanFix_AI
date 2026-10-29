from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from backend.app.core.dependencies import get_current_active_user
from backend.app.db.session import get_db
from backend.app.models.user import User
from backend.app.schemas.auth import AuthTokenData, GoogleAuthRequest
from backend.app.schemas.common import SingleResponse
from backend.app.schemas.user import UserRead
from backend.app.services.auth_service import auth_service

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/google",
    response_model=SingleResponse[AuthTokenData],
    status_code=status.HTTP_200_OK,
    summary="Authenticate with Google OAuth ID Token",
    description="Validates a Google ID token, verifies the user exists and is active, and issues an application JWT access token.",
)
def authenticate_google(
    payload: GoogleAuthRequest,
    db: Session = Depends(get_db),
):
    user, access_token = auth_service.authenticate_google_user(db, payload.id_token)
    return SingleResponse(
        data=AuthTokenData(
            access_token=access_token,
            token_type="bearer",
            user=UserRead.model_validate(user),
        )
    )


@router.get(
    "/me",
    response_model=SingleResponse[UserRead],
    status_code=status.HTTP_200_OK,
    summary="Get Current Authenticated User",
    description="Returns the profile and role of the currently authenticated active user.",
)
def get_current_user_profile(
    current_user: User = Depends(get_current_active_user),
):
    return SingleResponse(
        data=UserRead.model_validate(current_user)
    )
