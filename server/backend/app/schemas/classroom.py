from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class ClassroomBase(BaseModel):
    room_number: str = Field(..., min_length=1, max_length=50)
    building: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None


class ClassroomCreate(ClassroomBase):
    pass


class ClassroomUpdate(BaseModel):
    room_number: Optional[str] = Field(None, min_length=1, max_length=50)
    building: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    is_active: Optional[bool] = None


class ClassroomRead(ClassroomBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
