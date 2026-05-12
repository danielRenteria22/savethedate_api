from enum import Enum

class InvitationStatus(str, Enum):
    NOT_SENT = "NOT_SENT"
    IN_PROGRESS = "IN_PROGRESS"
    FAILED = "FAILED"
    SUCCESS = "SUCCESS"
