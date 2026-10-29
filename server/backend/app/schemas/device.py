from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field

from backend.app.models.enums import DeviceStatus, DeviceType


class DeviceBase(BaseModel):
    classroom_id: str
    device_type: str = Field(..., min_length=1, max_length=100)
    brand: str = Field(..., min_length=1, max_length=100)
    model: str = Field(..., min_length=1, max_length=100)
    serial_number: Optional[str] = Field(None, max_length=100)
    status: DeviceStatus = Field(default=DeviceStatus.OPERATIONAL)


class DeviceCreate(DeviceBase):
    pass


class DeviceUpdate(BaseModel):
    classroom_id: Optional[str] = None
    device_type: Optional[str] = Field(None, min_length=1, max_length=100)
    brand: Optional[str] = Field(None, min_length=1, max_length=100)
    model: Optional[str] = Field(None, min_length=1, max_length=100)
    serial_number: Optional[str] = Field(None, max_length=100)
    status: Optional[DeviceStatus] = None


class DeviceRead(DeviceBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    created_at: datetime
    updated_at: datetime
