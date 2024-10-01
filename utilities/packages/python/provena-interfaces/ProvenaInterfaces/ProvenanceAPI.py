try:
    from ProvenaInterfaces.SharedTypes import StatusResponse
    from ProvenaInterfaces.ProvenanceModels import *
except:
    from .SharedTypes import StatusResponse
    from .ProvenanceModels import *

from typing import Optional, Any, Dict, Type
from pydantic import BaseModel


class ProvenanceRecordInfo(BaseModel):
    # Handle ID
    id: str
    # Prov serialised document
    prov_json: str
    # Identified version of input format
    record: ModelRunRecord


class RegisterModelRunResponse(StatusResponse):
    session_id: Optional[str]


class SyncRegisterModelRunResponse(StatusResponse):
    record_info: ProvenanceRecordInfo


class RegisterBatchModelRunRequest(BaseModel):
    records: List[ModelRunRecord]


class RegisterBatchModelRunResponse(StatusResponse):
    session_id: Optional[str]


class LineageResponse(StatusResponse):
    record_count: Optional[int]
    graph: Optional[Dict[str, Any]]


class ConvertModelRunsResponse(StatusResponse):
    # list of model run records
    new_records: Optional[List[ModelRunRecord]]

    # list of job ids of validated existing jobs which don't need to be lodged
    existing_records: Optional[List[str]]

    warnings: Optional[List[str]]


class AddStudyLinkQueryParameters(BaseModel):
    # the model run that is being linked to the study
    model_run_id: str
    # the study that is being linked to the model run
    study_id: str


class AddStudyLinkResponse(StatusResponse):
    # the model run that was linked to the study
    model_run_id: str
    # the study that was linked to the model run
    study_id: str
    # the session id for the provenance graph update job
    session_id: str


class PostUpdateModelRunInput(BaseModel):
    model_run_id: str
    reason: str
    record: ModelRunRecord


class PostUpdateModelRunResponse(BaseModel):
    session_id: str