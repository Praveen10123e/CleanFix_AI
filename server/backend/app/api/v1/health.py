from datetime import datetime, timezone
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from backend.app.core.config import get_settings
from backend.app.db.session import get_db
from backend.app.schemas.common import SingleResponse

router = APIRouter(tags=["Health"])
settings = get_settings()


@router.get("/health", response_model=SingleResponse[dict])
def get_health(db: Session = Depends(get_db)):
    """Health check endpoint checking application liveness and database connectivity."""
    db_status = "connected"
    overall_status = "healthy"

    try:
        # Verify database responsiveness with a lightweight ping
        db.execute(text("SELECT 1"))
    except Exception as e:
        db_status = f"disconnected: {type(e).__name__}"
        overall_status = "degraded"

    return SingleResponse(
        data={
            "status": overall_status,
            "app_name": settings.app_name,
            "environment": settings.app_env,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "services": {
                "database": db_status,
            },
        }
    )
