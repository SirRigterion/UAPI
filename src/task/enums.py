from enum import Enum

class TaskStatus(str, Enum):
    ACTIVE = "ACTIVE"
    POSTPONED = "POSTPONED"
    COMPLETED = "COMPLETED"

class TaskPriority(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
