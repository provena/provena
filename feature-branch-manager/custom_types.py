from enum import Enum
from dataclasses import dataclass
from typing import Optional
from typing import Dict, Any

StackData = Dict[str, Any]

class CfnStatus(str, Enum):
    CREATE_IN_PROGRESS = 'CREATE_IN_PROGRESS'
    CREATE_FAILED = "CREATE_FAILED"
    CREATE_COMPLETE = "CREATE_COMPLETE"
    ROLLBACK_IN_PROGRESS = "ROLLBACK_IN_PROGRESS"
    ROLLBACK_FAILED = "ROLLBACK_FAILED"
    ROLLBACK_COMPLETE = "ROLLBACK_COMPLETE"
    DELETE_IN_PROGRESS = "DELETE_IN_PROGRESS"
    DELETE_FAILED = "DELETE_FAILED"
    DELETE_COMPLETE = "DELETE_COMPLETE"
    UPDATE_IN_PROGRESS = "UPDATE_IN_PROGRESS"
    UPDATE_COMPLETE_CLEANUP_IN_PROGRESS = "UPDATE_COMPLETE_CLEANUP_IN_PROGRESS"
    UPDATE_COMPLETE = "UPDATE_COMPLETE"
    UPDATE_ROLLBACK_IN_PROGRESS = "UPDATE_ROLLBACK_IN_PROGRESS"
    UPDATE_ROLLBACK_FAILED = "UPDATE_ROLLBACK_FAILED"
    UPDATE_ROLLBACK_COMPLETE_CLEANUP_IN_PROGRESS = "UPDATE_ROLLBACK_COMPLETE_CLEANUP_IN_PROGRESS"
    UPDATE_ROLLBACK_COMPLETE = "UPDATE_ROLLBACK_COMPLETE"
    REVIEW_IN_PROGRESS = "REVIEW_IN_PROGRESS"


class PRStatus(str, Enum):
    NONE = "NONE"
    PENDING = "PENDING"
    CLOSED_NOT_MERGED = "CLOSED"
    MERGED = "MERGED"


class DeploymentStatus(str, Enum):
    DEPLOYED = "DEPLOYED"
    NOT_DEPLOYED = "NOT_DEPLOYED"


class StackType(str, Enum):
    APP = "APP"
    PIPELINE = "PIPELINE"


@dataclass
class StackInfo():
    stack_data: Dict[str, Any]
    stack_type: StackType
    ticket_num: int


@dataclass
class PRInfo():
    pr_status: PRStatus
    ticket_num: int
    pr_num: int


@dataclass
class TotalStatus():
    pr_status: Optional[PRInfo]
    app_stack: Optional[StackInfo]
    pipeline_stack: Optional[StackInfo]
    ticket_num: int

    def __str__(self) -> str:
        return f"""
                Feat Ticket Num: {self.ticket_num}
                PR Status: {self.pr_status or "No PR Found"}
                App Stack: {"Deployed" if self.app_stack else "Not deployed or found"}
                Pipeline Stack: {"Deployed" if self.pipeline_stack else "Not deployed or found"}
                """
