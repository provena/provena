from pydantic import BaseModel
from enum import Enum
from typing import Dict, Any, Type, Optional, List

GSI_VALUE = "ok"
GSI_FIELD_NAME = "gsi_status"

try:
    from ProvenaInterfaces.ProvenanceModels import ModelRunRecord
    from ProvenaInterfaces.ProvenanceAPI import ProvenanceRecordInfo
    from ProvenaInterfaces.RegistryModels import ItemSubType
except:
    from .ProvenanceModels import ModelRunRecord
    from .ProvenanceAPI import ProvenanceRecordInfo
    from .RegistryModels import ItemSubType


class JobType(str, Enum):
    PROV_LODGE = "PROV_LODGE"
    REGISTRY = "REGISTRY"
    EMAIL = "EMAIL"


class JobSubType(str, Enum):
    # PROV LODGE
    PROV_LODGE_WAKE_UP = "PROV_LODGE_WAKE_UP"
    MODEL_RUN_PROV_LODGE = "MODEL_RUN_PROV_LODGE"
    MODEL_RUN_LODGE_ONLY = "MODEL_RUN_LODGE_ONLY"
    MODEL_RUN_BATCH_SUBMIT = "MODEL_RUN_BATCH_SUBMIT"
    LODGE_CREATE_ACTIVITY = "LODGE_CREATE_ACTIVITY"
    LODGE_VERSION_ACTIVITY = "LODGE_VERSION_ACTIVITY"
    MODEL_RUN_UPDATE = "MODEL_RUN_UPDATE"
    MODEL_RUN_UPDATE_LODGE_ONLY = "MODEL_RUN_UPDATE_LODGE_ONLY"

    # REGISTRY
    REGISTRY_WAKE_UP = "REGISTRY_WAKE_UP"
    REGISTER_CREATE_ACTIVITY = "REGISTER_CREATE_ACTIVITY"
    REGISTER_VERSION_ACTIVITY = "REGISTER_VERSION_ACTIVITY"

    # EMAIL
    EMAIL_WAKE_UP = "EMAIL_WAKE_UP"
    SEND_EMAIL = "SEND_EMAIL"


class JobStatus(str, Enum):
    PENDING = "PENDING"
    DEQUEUED = "DEQUEUED"
    IN_PROGRESS = "IN_PROGRESS"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"


class JobTableBase(BaseModel):
    # partition key
    session_id: str

    # timestamp (unix timestamp)
    # sort key
    created_timestamp: int

    # who owns this job?
    username: str

    # batch id - optional for batches
    # GSI on batch id
    batch_id: Optional[str]

    # this contains the specific job info
    payload: Dict[str, Any]

    # job type
    job_type: JobType
    # job sub type
    job_sub_type: JobSubType

    # universal gsi field
    gsi_status: str = GSI_VALUE


# SNS Topic payload
class JobSnsPayload(JobTableBase):
    pass

# Job Status Table Entry


class JobStatusTable(JobTableBase):
    # What is the status of the job?
    status: JobStatus

    # Contains any error info if relevant to status
    info: Optional[str]

    # If the result has completed successfully, payload associated with it
    result: Optional[Dict[str, Any]]

# =====================
# JOB SUB TYPE PAYLOADS
# =====================

# All wake up models are the same


class WakeUpPayload(BaseModel):
    reason: Optional[str]


class WakeUpResult(BaseModel):
    pass

# PROV LODGE
# ----------

# PROV LODGE MODEL RUN


class ProvLodgeModelRunPayload(BaseModel):
    record: ModelRunRecord
    revalidate: bool


class ProvLodgeModelRunResult(BaseModel):
    record: ProvenanceRecordInfo

# PROV UPDATE MODEL RUN


class ProvLodgeUpdatePayload(BaseModel):
    model_run_record_id: str
    updated_record: ModelRunRecord
    reason: str
    revalidate: bool


class ProvLodgeUpdateResult(BaseModel):
    # The updated record
    record: ProvenanceRecordInfo

# PROV UPDATE LODGE ONLY


class ProvLodgeUpdateLodgeOnlyPayload(BaseModel):
    model_run_record_id: str
    updated_record: ModelRunRecord
    revalidate: bool


class ProvLodgeUpdateLodgeOnlyResult(BaseModel):
    pass

# PROV LODGE ONLY MODEL RUN


class ProvLodgeModelRunLodgeOnlyPayload(BaseModel):
    model_run_record_id: str
    record: ModelRunRecord
    revalidate: bool


class ProvLodgeModelRunLodgeOnlyResult(BaseModel):
    record: ProvenanceRecordInfo


# PROV LODGE BATCH SUBMIT


class ProvLodgeBatchSubmitPayload(BaseModel):
    # The list of records to lodge
    records: List[ModelRunRecord]


class ProvLodgeBatchSubmitResult(BaseModel):
    # The batch which contains spin off jobs
    batch_id: str

# PROV LODGE CREATION


class ProvLodgeCreationPayload(BaseModel):
    # needs to know the created item ID and the activity ID
    created_item_id: str
    creation_activity_id: str
    # easier to resolve this in registry context for now
    linked_person_id: str
    created_item_subtype: ItemSubType


class ProvLodgeCreationResult(BaseModel):
    # No meaningful response
    pass

# PROV LODGE VERSION


class ProvLodgeVersionPayload(BaseModel):
    # needs to know the created item ID and the activity ID
    from_version_id: str
    to_version_id: str
    version_activity_id: str
    linked_person_id: str
    item_subtype: ItemSubType


class ProvLodgeVersionResult(BaseModel):
    # No meaningful response
    pass

# REGISTRY
# --------

# REGISTER CREATE ACTIVITY


class RegistryRegisterCreateActivityPayload(BaseModel):
    created_item_id: str
    created_item_subtype: ItemSubType
    # easier to resolve this in registry context for now
    linked_person_id: str


class RegistryRegisterCreateActivityResult(BaseModel):
    creation_activity_id: str
    lodge_session_id: str

# REGISTER VERSION ACTIVITY


class RegistryRegisterVersionActivityPayload(BaseModel):
    # Why was this version performed
    reason: str

    # New version number
    version_number: int

    # FROM
    from_version_id: str
    # TO
    to_version_id: str
    # WHO
    linked_person_id: str

    # Which subtype?
    item_subtype: ItemSubType


class RegistryRegisterVersionActivityResult(BaseModel):
    version_activity_id: str
    lodge_session_id: str


# EMAIL
# -----

# SEND EMAIL

class EmailSendEmailPayload(BaseModel):
    email_to: str
    subject: str
    body: str
    reason: str


class EmailSendEmailResult(BaseModel):
    # No meaningful payload in result - error reported if failed
    pass


# ====================
# JOB TYPE PAYLOAD MAP
# ====================
JOB_TYPE_PAYLOAD_MAP: Dict[JobSubType, Type[BaseModel]] = {
    # Prov Lodge
    JobSubType.PROV_LODGE_WAKE_UP: WakeUpPayload,
    JobSubType.MODEL_RUN_PROV_LODGE: ProvLodgeModelRunPayload,
    JobSubType.MODEL_RUN_LODGE_ONLY: ProvLodgeModelRunLodgeOnlyPayload,
    JobSubType.MODEL_RUN_BATCH_SUBMIT: ProvLodgeBatchSubmitPayload,
    JobSubType.LODGE_CREATE_ACTIVITY: ProvLodgeCreationPayload,
    JobSubType.LODGE_VERSION_ACTIVITY: ProvLodgeVersionPayload,
    JobSubType.MODEL_RUN_UPDATE: ProvLodgeUpdatePayload,
    JobSubType.MODEL_RUN_UPDATE_LODGE_ONLY: ProvLodgeUpdateLodgeOnlyPayload,

    # Registry
    JobSubType.REGISTRY_WAKE_UP: WakeUpPayload,
    JobSubType.REGISTER_CREATE_ACTIVITY: RegistryRegisterCreateActivityPayload,
    JobSubType.REGISTER_VERSION_ACTIVITY: RegistryRegisterVersionActivityPayload,

    # Email
    JobSubType.EMAIL_WAKE_UP: WakeUpPayload,
    JobSubType.SEND_EMAIL: EmailSendEmailPayload,
}

# ===================
# JOB TYPE RESULT MAP
# ===================

JOB_TYPE_RESULT_MAP: Dict[JobSubType, Type[BaseModel]] = {
    # Prov Lodge
    JobSubType.PROV_LODGE_WAKE_UP: WakeUpResult,
    JobSubType.MODEL_RUN_PROV_LODGE: ProvLodgeModelRunResult,
    JobSubType.MODEL_RUN_LODGE_ONLY: ProvLodgeModelRunLodgeOnlyResult,
    JobSubType.MODEL_RUN_BATCH_SUBMIT: ProvLodgeBatchSubmitResult,
    JobSubType.LODGE_CREATE_ACTIVITY: ProvLodgeCreationResult,
    JobSubType.LODGE_VERSION_ACTIVITY: ProvLodgeVersionResult,
    JobSubType.MODEL_RUN_UPDATE: ProvLodgeUpdateResult,
    JobSubType.MODEL_RUN_UPDATE_LODGE_ONLY: ProvLodgeUpdateLodgeOnlyResult,

    # Registry
    JobSubType.REGISTRY_WAKE_UP: WakeUpResult,
    JobSubType.REGISTER_CREATE_ACTIVITY: RegistryRegisterCreateActivityResult,
    JobSubType.REGISTER_VERSION_ACTIVITY: RegistryRegisterVersionActivityResult,

    # Email
    JobSubType.EMAIL_WAKE_UP: WakeUpResult,
    JobSubType.SEND_EMAIL: EmailSendEmailResult,
}
