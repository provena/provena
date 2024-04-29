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
