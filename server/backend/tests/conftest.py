import os
import sys
from pathlib import Path
import sqlite3
from typing import Generator
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

# Ensure 'server' directory and repository root are on sys.path
SERVER_DIR = Path(__file__).resolve().parent.parent.parent  # .../server
REPO_ROOT = SERVER_DIR.parent  # .../CleanFix_AI
BACKEND_DIR = Path(__file__).resolve().parent.parent  # .../server/backend

for path_dir in (str(SERVER_DIR), str(REPO_ROOT), str(BACKEND_DIR)):
    if path_dir not in sys.path:
        sys.path.insert(0, path_dir)

from backend.app.core.security import create_access_token
from backend.app.db.base import Base
from backend.app.db.session import get_db
from backend.app.main import app
from backend.app.models.enums import UserRole
from backend.app.models.user import User
import backend.app.models  # noqa: F401

# In-memory SQLite engine with StaticPool to keep single in-memory database across connections
TEST_DATABASE_URL = "sqlite:///:memory:"

test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)


# Enforce foreign key constraints in SQLite test engine
@event.listens_for(test_engine, "connect")
def set_sqlite_pragma_test(dbapi_connection, connection_record):
    if isinstance(dbapi_connection, sqlite3.Connection):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


TestingSessionLocal = sessionmaker(
    bind=test_engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)


@pytest.fixture(scope="function")
def db_session() -> Generator[Session, None, None]:
    """Provide a fresh in-memory database session for each test."""
    Base.metadata.create_all(bind=test_engine)
    session: Session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="function")
def client(db_session: Session) -> Generator[TestClient, None, None]:
    """TestClient configured with dependency overrides for database session."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def admin_user(db_session: Session) -> User:
    user = User(
        email="test.admin@classroom.edu",
        name="Test Admin",
        role=UserRole.ADMIN,
        google_sub="test_google_sub_admin",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def faculty_user(db_session: Session) -> User:
    user = User(
        email="test.faculty@classroom.edu",
        name="Test Faculty",
        role=UserRole.FACULTY,
        google_sub="test_google_sub_faculty",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def technician_user(db_session: Session) -> User:
    user = User(
        email="test.technician@classroom.edu",
        name="Test Technician",
        role=UserRole.TECHNICIAN,
        google_sub="test_google_sub_tech",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def inactive_user(db_session: Session) -> User:
    user = User(
        email="test.inactive@classroom.edu",
        name="Test Inactive",
        role=UserRole.FACULTY,
        google_sub="test_google_sub_inactive",
        is_active=False,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def admin_token(admin_user: User) -> str:
    return create_access_token({"sub": admin_user.id, "email": admin_user.email, "role": admin_user.role.value})


@pytest.fixture
def faculty_token(faculty_user: User) -> str:
    return create_access_token({"sub": faculty_user.id, "email": faculty_user.email, "role": faculty_user.role.value})


@pytest.fixture
def technician_token(technician_user: User) -> str:
    return create_access_token({"sub": technician_user.id, "email": technician_user.email, "role": technician_user.role.value})


@pytest.fixture
def inactive_token(inactive_user: User) -> str:
    return create_access_token({"sub": inactive_user.id, "email": inactive_user.email, "role": inactive_user.role.value})
