from pydantic import BaseModel, root_validator
from typing import Optional, Dict,  List

try:
    from ProvenaInterfaces.AsyncJobModels import *
except:
    from .AsyncJobModels import *

JOBS_USER_PREFIX = "/jobs/user"
JOBS_ADMIN_PREFIX = "/jobs/admin"

# API Actions and routes


PaginationKey = Dict[str, Any]
class JobsUserActions(str, Enum):
    FETCH = "FETCH"
    LIST = "LIST"
    LIST_BATCH = "LIST_BATCH"


JOBS_USER_ACTIONS_MAP: Dict[JobsUserActions, str] = {
    JobsUserActions.FETCH: "/fetch",
    JobsUserActions.LIST: "/list",
    JobsUserActions.LIST_BATCH: "/list_batch",
}


class JobsAdminActions(str, Enum):
    LAUNCH = "LAUNCH"
    FETCH = "FETCH"
    LIST = "LIST"
    LIST_BATCH = "LIST_BATCH"


JOBS_ADMIN_ACTIONS_MAP: Dict[JobsAdminActions, str] = {
    JobsAdminActions.LAUNCH: "/launch",
    JobsAdminActions.FETCH: "/fetch",
    JobsAdminActions.LIST: "/list",
    JobsAdminActions.LIST_BATCH: "/list_batch",
}

# ====
# USER
# ====

# -------
# get job
# -------

# req
# GET

# resp


class GetJobResponse(BaseModel):
    job: JobStatusTable

# ------------
# list by batch
# ------------


# req
# POST


class ListByBatchRequest(BaseModel):
    batch_id: str
    pagination_key: Optional[PaginationKey] = None
    limit: int = 10

# resp


class ListByBatchResponse(BaseModel):
    jobs: List[JobStatusTable]
    pagination_key: Optional[PaginationKey]

# ----------
# list jobs
# ----------


# req
# POST


class ListJobsRequest(BaseModel):
    pagination_key: Optional[PaginationKey] = None
    limit: int = 10

# resp


class ListJobsResponse(BaseModel):
    jobs: List[JobStatusTable]
    pagination_key: Optional[PaginationKey]

# ----------
# retry job
# ----------

# req
# POST

# resp


class RetryJobResponse(BaseModel):
    session_id: str


# =====
# ADMIN
# =====

# ----------
# launch job
# ----------

# req
# POST
class AdminLaunchJobRequest(BaseModel):
    # Who is this being lodged for? Defaults to token username
    username: Optional[str] = None
    # Does it need a batch id?
    request_batch_id: bool = False
    # Is it part of a batch?
    add_to_batch: Optional[str] = None
    # What type of job?
    job_type: JobType
    # What subtype?
    job_sub_type: JobSubType
    # Validated against job types expected payload
    job_payload: Dict[str, Any]

    @root_validator(pre=False, skip_on_failure=True)
    def check_batch_setup(cls: Any, values: Dict[str, Any]) -> Dict[str, Any]:
        request_batch_id: bool = values['request_batch_id']
        add_to_batch: Optional[str] = values['add_to_batch']

        if request_batch_id:
            if add_to_batch is not None:
                raise ValueError(
                    "Cannot specify both a new batch and an existing batch id.")

        return values


# resp


class AdminLaunchJobResponse(BaseModel):
    # session id (unique)
    session_id: str

    # if requested, return the batch id
    batch_id: Optional[str] = None

# -------
# get job
# -------

# req
# GET (session_id)

# resp


class AdminGetJobResponse(BaseModel):
    job: JobStatusTable

# ----------
# list jobs
# ----------

# req
# POST


class AdminListJobsRequest(BaseModel):
    # Defaults to sorting by latest using global index

    # Optionally specify username which uses username index instead
    username_filter: Optional[str] = None
    limit: int = 10
    pagination_key: Optional[PaginationKey] = None

# resp


class AdminListJobsResponse(BaseModel):
    jobs: List[JobStatusTable]
    pagination_key: Optional[PaginationKey]


# -------------
# list by batch
# -------------


# req
# POST


class AdminListByBatchRequest(BaseModel):
    batch_id: str
    username_filter: Optional[str]
    pagination_key: Optional[PaginationKey] = None
    limit: int = 10

# resp


class AdminListByBatchResponse(BaseModel):
    jobs: List[JobStatusTable]
    pagination_key: Optional[PaginationKey]

# ----------
# retry job
# ----------

# req
# POST

# resp


class AdminRetryJobResponse(BaseModel):
    # session id (unique)
    session_id: str
