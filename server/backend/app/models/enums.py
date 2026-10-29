from enum import Enum


class UserRole(str, Enum):
    ADMIN = "ADMIN"
    FACULTY = "FACULTY"
    TECHNICIAN = "TECHNICIAN"


class DeviceStatus(str, Enum):
    OPERATIONAL = "OPERATIONAL"
    DEGRADED = "DEGRADED"
    FAULTY = "FAULTY"
    UNDER_MAINTENANCE = "UNDER_MAINTENANCE"
    DECOMMISSIONED = "DECOMMISSIONED"


class DeviceType(str, Enum):
    PROJECTOR = "PROJECTOR"
    SMART_BOARD = "SMART_BOARD"
    AUDIO_SYSTEM = "AUDIO_SYSTEM"
    MICROPHONE = "MICROPHONE"
    DISPLAY = "DISPLAY"
    OTHER = "OTHER"


class TroubleshootingStatus(str, Enum):
    IN_PROGRESS = "IN_PROGRESS"
    RESOLVED = "RESOLVED"
    ESCALATED_TO_COMPLAINT = "ESCALATED_TO_COMPLAINT"
    ABANDONED = "ABANDONED"


class StepResult(str, Enum):
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"


class ComplaintStatus(str, Enum):
    PENDING = "PENDING"
    ASSIGNED = "ASSIGNED"
    IN_PROGRESS = "IN_PROGRESS"
    RESOLVED = "RESOLVED"
    CANCELLED = "CANCELLED"


class ComplaintPriority(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class DocumentType(str, Enum):
    MANUAL = "MANUAL"
    TROUBLESHOOTING_GUIDE = "TROUBLESHOOTING_GUIDE"
    SPEC_SHEET = "SPEC_SHEET"
    FAQ = "FAQ"


class DocumentStatus(str, Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    INDEXED = "INDEXED"
    FAILED = "FAILED"


class IngestionStatus(str, Enum):
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class ChangeType(str, Enum):
    CREATED = "CREATED"
    STATUS_CHANGE = "STATUS_CHANGE"
    RELOCATED = "RELOCATED"
    REPAIRED = "REPAIRED"
    UPDATED = "UPDATED"
