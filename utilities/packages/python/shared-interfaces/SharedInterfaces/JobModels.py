from pydantic import BaseModel
from enum import Enum
from typing import Optional, Dict, Type, List

try:
    from SharedInterfaces.ProvenanceModels import ModelRunRecord
except:
    from .ProvenanceModels import ModelRunRecord


class JobType(str, Enum):
    LODGE_MODEL_RUN_RECORD = "LODGE_MODEL_RUN_RECORD"


class JobStatus(str, Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"


class JobLogBase(BaseModel):
    # unique ID in dynamoDB
    id: str

    # job status
    job_status: JobStatus

    # can provide error info if something failed
    error_info: Optional[str] = None

    # job type
    job_type: JobType

    # unix timestamps
    created_time: int
    updated_time: int


class LodgeModelRunJob(JobLogBase):
    model_run_record_id: Optional[str] = None
    # This overrides to provide a default job type
    job_type: JobType = JobType.LODGE_MODEL_RUN_RECORD
    # This is used in case we need to retry a job - this is a record of what should be lodged
    # This isn't exposed in the describe info response
    model_run_record: ModelRunRecord
    # username
    username: str


class JobRequestBase(BaseModel):
    # job ID, same as job log
    id: str

    # username
    username: str

    # job type
    job_type: JobType

    # when was this request submitted?
    submitted_time: int


class LodgeModelRunJobRequest(JobRequestBase):
    # This is a record of what should be lodged
    model_run_record: ModelRunRecord
    # This overrides to provide a default job type
    job_type: JobType = JobType.LODGE_MODEL_RUN_RECORD


JOB_TYPE_CLASS_MAP: Dict[JobType, Type[JobLogBase]] = {
    JobType.LODGE_MODEL_RUN_RECORD: LodgeModelRunJob
}

# Check that the job type class map contains all types
for job_type in JobType:
    assert job_type in JOB_TYPE_CLASS_MAP


class BatchJob(BaseModel):
    # the unique batch id
    batch_id: str
    # created timestamp
    created_time: int
    # the list of job IDs
    jobs: List[str]


class BatchRecord(BaseModel):
    # primary key
    username: str

    # list batches
    # map batch_id -> BatchJob
    batch_jobs: Dict[str, BatchJob]
