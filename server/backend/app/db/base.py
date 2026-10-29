import uuid
from datetime import datetime, timezone
from sqlalchemy import DateTime, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def utc_now() -> datetime:
    """Generate timezone-aware UTC datetime."""
    return datetime.now(timezone.utc)


def generate_uuid() -> str:
    """Generate string UUID4."""
    return str(uuid.uuid4())


class Base(DeclarativeBase):
    """Base model class for all SQLAlchemy 2.x declarative entities."""
    pass
