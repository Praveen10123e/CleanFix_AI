import logging
import sys
from contextlib import asynccontextmanager
from pathlib import Path

# Ensure 'server' directory and repo root are in sys.path so 'backend.app' imports succeed regardless of invocation directory
_SERVER_DIR = Path(__file__).resolve().parent.parent.parent  # .../server
_REPO_ROOT = _SERVER_DIR.parent
_BACKEND_DIR = Path(__file__).resolve().parent.parent  # .../server/backend

for _p in (str(_SERVER_DIR), str(_REPO_ROOT), str(_BACKEND_DIR)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.app.api.v1.health import get_health
from backend.app.api.v1.router import api_v1_router
from backend.app.core.config import get_settings
from backend.app.core.exceptions import AppException
from backend.app.db.init_db import init_db
from backend.app.db.session import get_db

# Configure application logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
)
logger = logging.getLogger(__name__)

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager: initialize database tables upon startup."""
    logger.info("Starting up %s (env: %s)...", settings.app_name, settings.app_env)
    try:
        init_db()
        logger.info("Database tables initialized successfully on startup.")
    except Exception as e:
        logger.error("Failed to initialize database on startup: %s", str(e), exc_info=True)
    yield
    logger.info("Shutting down %s...", settings.app_name)


app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# Configure CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Root-level health check endpoint
app.add_api_route(
    "/health",
    get_health,
    methods=["GET"],
    tags=["Health"],
    summary="Root Health Check",
    description="Root level health and database liveness endpoint.",
)

# Mount versioned API routes
app.include_router(api_v1_router)


# -----------------------------------------------------------------------------
# Global Exception Handlers (Standardized JSON format)
# -----------------------------------------------------------------------------

@app.exception_handler(AppException)
async def handle_app_exception(request: Request, exc: AppException):
    """Handler for custom application exceptions."""
    logger.warning("Application exception [%s]: %s (Details: %s)", exc.code, exc.message, exc.details)
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message,
                "details": exc.details,
            }
        },
    )


@app.exception_handler(RequestValidationError)
async def handle_validation_error(request: Request, exc: RequestValidationError):
    """Handler for Pydantic and request body validation errors."""
    errors = exc.errors()
    # Format details safely
    details = {
        "validation_errors": [
            {
                "field": " -> ".join(str(loc) for loc in err.get("loc", [])),
                "issue": err.get("msg"),
                "type": err.get("type"),
            }
            for err in errors
        ]
    }
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "The request payload failed validation.",
                "details": details,
            }
        },
    )


from starlette.exceptions import HTTPException as StarletteHTTPException


@app.exception_handler(StarletteHTTPException)
async def handle_http_exception(request: Request, exc: StarletteHTTPException):
    """Handler for standard FastAPI / Starlette HTTP exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": "HTTP_ERROR",
                "message": str(exc.detail),
                "details": {},
            }
        },
    )


@app.exception_handler(Exception)
async def handle_unhandled_exception(request: Request, exc: Exception):
    """Handler for unexpected internal server errors. Does not leak stack traces."""
    logger.error("Unhandled server exception on %s %s: %s", request.method, request.url.path, str(exc), exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected server error occurred. Please try again later.",
                "details": {},
            }
        },
    )
