from backend.app.schemas.common import (
    ErrorBody,
    ErrorResponse,
    ListResponse,
    PaginationMeta,
    SingleResponse,
)
from backend.app.schemas.auth import (
    AuthTokenData,
    GoogleAuthRequest,
    TokenPayload,
)
from backend.app.schemas.user import (
    UserBase,
    UserCreate,
    UserRead,
    UserUpdate,
)
from backend.app.schemas.classroom import (
    ClassroomBase,
    ClassroomCreate,
    ClassroomRead,
    ClassroomUpdate,
)
from backend.app.schemas.device import (
    DeviceBase,
    DeviceCreate,
    DeviceRead,
    DeviceUpdate,
)

__all__ = [
    "ErrorBody",
    "ErrorResponse",
    "ListResponse",
    "PaginationMeta",
    "SingleResponse",
    "AuthTokenData",
    "GoogleAuthRequest",
    "TokenPayload",
    "UserBase",
    "UserCreate",
    "UserRead",
    "UserUpdate",
    "ClassroomBase",
    "ClassroomCreate",
    "ClassroomRead",
    "ClassroomUpdate",
    "DeviceBase",
    "DeviceCreate",
    "DeviceRead",
    "DeviceUpdate",
]
