try:
    from SharedInterfaces.SharedTypes import StatusResponse
    from SharedInterfaces.ProvenanceModels import *
    from SharedInterfaces.JobModels import LodgeModelRunJobRequest, LodgeModelRunJob, BatchJob
except:
    from .SharedTypes import StatusResponse
    from .ProvenanceModels import *
    from .JobModels import LodgeModelRunJobRequest, LodgeModelRunJob, BatchJob

from typing import Optional, Any, Dict

from pydantic import BaseModel


class ProvenanceRecordInfo(BaseModel):
    # Handle ID
    id: str
    # Prov serialised document
    prov_json: str
    # Identified version of input format
    record: ModelRunRecord


class RegisterModelRunResponse(StatusResponse):
    # Includes record_info iff status.success
    record_info: Optional[ProvenanceRecordInfo]


class LineageResponse(StatusResponse):
    record_count: Optional[int]
    graph: Optional[Dict[str, Any]]


class ConvertModelRunsResponse(StatusResponse):
    # list of model run records
    new_records: Optional[List[ModelRunRecord]]

    # list of job ids of validated existing jobs which don't need to be lodged
    existing_records: Optional[List[str]]

    warnings: Optional[List[str]]


class BulkSubmission(BaseModel):
    jobs: List[ModelRunRecord]


class BulkSubmissionResponse(StatusResponse):
    jobs: Optional[List[LodgeModelRunJobRequest]]
    batch_id: Optional[str]


class DescribeJobResponse(StatusResponse):
    job_info: Optional[LodgeModelRunJob]


class DescribeBatchResponse(StatusResponse):
    job_info: Optional[List[LodgeModelRunJob]]
    # a list of job IDs which could not be found in job log
    missing: Optional[List[str]]
    # were all entries found and all of them succeeded?
    all_successful: bool


class BatchHistoryResponse(StatusResponse):
    batch_jobs: Optional[List[BatchJob]]
