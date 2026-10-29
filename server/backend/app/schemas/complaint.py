from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field

from backend.app.models.enums import ComplaintPriority, ComplaintStatus


class RepairRecordRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    complaint_id: str
    technician_id: str
    confirmed_cause: str
    repair_action: str
    resolution_notes: Optional[str] = None
    parts_replaced: Optional[str] = None
    verified_by: Optional[str] = None
    created_at: datetime


class ComplaintCreate(BaseModel):
    device_id: str
    classroom_id: Optional[str] = None
    description: str = Field(..., min_length=5, max_length=2000)
    priority: str = Field(default="MEDIUM", max_length=50)


class ComplaintAssignmentUpdate(BaseModel):
    technician_id: str


class ComplaintStatusUpdate(BaseModel):
    status: ComplaintStatus


class ComplaintResolutionCreate(BaseModel):
    confirmed_cause: str = Field(..., min_length=3, max_length=1000)
    repair_action: str = Field(..., min_length=3, max_length=1000)
    resolution_notes: Optional[str] = Field(None, max_length=2000)
    parts_replaced: Optional[str] = Field(None, max_length=500)


class ComplaintRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    session_id: Optional[str] = None
    device_id: str
    classroom_id: str
    reported_by: str
    assigned_technician_id: Optional[str] = None
    description: str
    priority: str
    status: ComplaintStatus
    created_at: datetime
    assigned_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    repair_record: Optional[RepairRecordRead] = None

