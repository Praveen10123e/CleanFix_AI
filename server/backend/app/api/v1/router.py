from fastapi import APIRouter
from backend.app.api.v1.admin import router as admin_router
from backend.app.api.v1.auth import router as auth_router
from backend.app.api.v1.classrooms import router as classrooms_router
from backend.app.api.v1.complaints import router as complaints_router
from backend.app.api.v1.devices import router as devices_router
from backend.app.api.v1.health import router as health_router
from backend.app.api.v1.knowledge import router as knowledge_router
from backend.app.api.v1.troubleshooting import router as troubleshooting_router

api_v1_router = APIRouter(prefix="/api/v1")

# Mount v1 route groups
api_v1_router.include_router(health_router)
api_v1_router.include_router(auth_router)
api_v1_router.include_router(admin_router)
api_v1_router.include_router(classrooms_router)
api_v1_router.include_router(devices_router)
api_v1_router.include_router(troubleshooting_router)
api_v1_router.include_router(complaints_router)
api_v1_router.include_router(knowledge_router)
