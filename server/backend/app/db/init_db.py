import logging
import sys
from pathlib import Path

# Ensure 'server' directory and repo root are in sys.path
_SERVER_DIR = Path(__file__).resolve().parent.parent.parent.parent  # .../server
_REPO_ROOT = _SERVER_DIR.parent
_BACKEND_DIR = Path(__file__).resolve().parent.parent.parent  # .../server/backend

for _p in (str(_SERVER_DIR), str(_REPO_ROOT), str(_BACKEND_DIR)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from sqlalchemy import inspect
from backend.app.db.base import Base
from backend.app.db.session import engine
# Import all models to ensure they are registered with Base.metadata
import backend.app.models  # noqa: F401

logger = logging.getLogger(__name__)


def init_db() -> None:
    """Initialize database tables for all declared models and run schema upgrades."""
    logger.info("Initializing database schema...")
    Base.metadata.create_all(bind=engine)
    inspector = inspect(engine)
    tables = inspector.get_table_names()

    # Safe upgrade for SQLite existing columns if not present
    with engine.begin() as conn:
        if "complaints" in tables:
            complaint_cols = [c["name"] for c in inspector.get_columns("complaints")]
            if "priority" not in complaint_cols:
                logger.info("Upgrading complaints table: adding 'priority' column...")
                conn.exec_driver_sql("ALTER TABLE complaints ADD COLUMN priority VARCHAR(50) DEFAULT 'MEDIUM' NOT NULL")

        if "repair_records" in tables:
            repair_cols = [c["name"] for c in inspector.get_columns("repair_records")]
            if "parts_replaced" not in repair_cols:
                logger.info("Upgrading repair_records table: adding 'parts_replaced' column...")
                conn.exec_driver_sql("ALTER TABLE repair_records ADD COLUMN parts_replaced TEXT")

    logger.info("Database initialized successfully with tables: %s", tables)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    init_db()
    print("Database tables initialized successfully.")
