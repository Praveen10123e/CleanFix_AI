from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field

from backend.app.models.enums import StepResult, TroubleshootingStatus
from backend.app.schemas.device import DeviceRead


class TroubleshootingStepRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    session_id: str
    step_number: int
    instruction: str
    reason: Optional[str] = None
    source_refs: Optional[Dict[str, Any]] = None
    result: Optional[StepResult] = None
    result_note: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None


class TroubleshootingSessionCreate(BaseModel):
    device_id: str
    symptom_text: str = Field(..., min_length=3, max_length=1000)


class TroubleshootingSessionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    faculty_id: str
    device_id: str
    symptom_text: str
    status: TroubleshootingStatus
    current_step: int
    started_at: datetime
    ended_at: Optional[datetime] = None
    steps: List[TroubleshootingStepRead] = Field(default_factory=list)
    complaint_id: Optional[str] = None


class StepResultSubmit(BaseModel):
    result: StepResult
    result_note: Optional[str] = Field(None, max_length=1000)


class TroubleshootingComplaintCreate(BaseModel):
    description: Optional[str] = Field(None, max_length=2000)
    priority: Optional[str] = Field("MEDIUM", max_length=50)

