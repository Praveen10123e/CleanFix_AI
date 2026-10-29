from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ReportSummaryData(BaseModel):
    total_active_classrooms: int = Field(..., ge=0)
    total_active_devices: int = Field(..., ge=0)
    device_counts_by_category: Dict[str, int] = Field(default_factory=dict)
    device_counts_by_brand: Dict[str, int] = Field(default_factory=dict)
    device_counts_by_status: Dict[str, int] = Field(default_factory=dict)
    total_complaints: int = Field(..., ge=0)
    open_complaints: int = Field(..., ge=0)
    complaints_by_status: Dict[str, int] = Field(default_factory=dict)
    complaints_by_priority: Dict[str, int] = Field(default_factory=dict)
    assigned_complaints: int = Field(..., ge=0)
    unassigned_complaints: int = Field(..., ge=0)
    completed_repairs: int = Field(..., ge=0)
    common_symptoms: List[Dict[str, Any]] = Field(default_factory=list)
    recent_complaints: List[Dict[str, Any]] = Field(default_factory=list)

