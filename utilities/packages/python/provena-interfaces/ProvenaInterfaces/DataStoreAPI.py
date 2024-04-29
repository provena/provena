from __future__ import annotations
from typing import Dict, Any, List, Optional, Tuple, Union, ForwardRef
from pydantic import BaseModel, Field, HttpUrl, AnyHttpUrl, Extra, validator
from datetime import datetime, date
from enum import Enum

HOURS_TO_SECS = 3600


# Interface exports prefer relative imports
# where as pip install prefers module level import
try:
    from ProvenaInterfaces.SharedTypes import Status, StatusResponse
    from ProvenaInterfaces.RegistryModels import ItemDataset, S3Location, CollectionFormat, Roles, IdentifiedResource
except:
    from .SharedTypes import Status, StatusResponse
    from .RegistryModels import ItemDataset, S3Location, CollectionFormat, Roles, IdentifiedResource

Handle = str
ROCrate = Dict[str, Any]

# RONode = ForwardRef('RONode')


class ROConnectionFlat(BaseModel):
    name: str
    value: Union[str, List[str]]

    class Config:
        # Set all strings to not be empty
        min_anystr_length = 1
        # don't allow extra fields
        extra = Extra.forbid


class ROConnectionIDNonExpanded(BaseModel):
    name: str
    value_id: str

    class Config:
        # Set all strings to not be empty
        min_anystr_length = 1
        # don't allow extra fields
        extra = Extra.forbid


class ROConnectionExpandedUniqueName(BaseModel):
    name: str
    to: RONode

    class Config:
        # Set all strings to not be empty
        min_anystr_length = 1
        # don't allow extra fields
        extra = Extra.forbid


class ROConnectionExpandedIdName(BaseModel):
    name: str
    to: RONode
    special_id: str

    class Config:
        # Set all strings to not be empty
        min_anystr_length = 1
        # don't allow extra fields
        extra = Extra.forbid


ROConnectionType = Union[ROConnectionFlat, ROConnectionIDNonExpanded,
                         ROConnectionExpandedUniqueName, ROConnectionExpandedIdName]


class RONode(BaseModel):
    connections: Dict[str, ROConnectionType]
    type: Union[str, List[str]]

    class Config:
        # Set all strings to not be empty
        min_anystr_length = 1
        # don't allow extra fields
        extra = Extra.forbid


ROConnectionExpandedUniqueName.update_forward_refs()
ROConnectionExpandedIdName.update_forward_refs()


class ROGraph(BaseModel):
    root_node: RONode

    class Config:
        # Set all strings to not be empty
        min_anystr_length = 1
        # don't allow extra fields
        extra = Extra.forbid


class Schema(BaseModel):
    json_schema: Dict[Any, Any]


class MintResponse(BaseModel):
    status: Status
    handle: Optional[str]
    s3_location: Optional[S3Location]
    register_create_activity_session_id: Optional[str]


class UpdateMetadataResponse(BaseModel):
    status: Status
    handle: str
    s3_location: S3Location

class Credentials(BaseModel):
    aws_access_key_id: str
    aws_secret_access_key: str
    aws_session_token: str
    expiry: datetime


class CredentialsRequest(BaseModel):
    dataset_id: str
    console_session_required: bool


class CredentialResponse(BaseModel):
    status: Status
    credentials: Credentials
    console_session_url: Optional[str]


# class LockActionType(str, Enum):
#    LOCK = "LOCK"
#    UNLOCK = "UNLOCK"
#
#
# class LockEvent(BaseModel):
#    # Locked or unlocked
#    action_type: LockActionType
#    # Who did it?
#    actor_email: str
#    # Why did they lock/unlock it
#    reason: str
#    # When did this happen? (unix timestamp)
#    timestamp: int
#
#
# class DatasetLockConfiguration(BaseModel):
#    # is the dataset locked down?
#    locked: bool
#    # what is the history of lock changes
#    history: List[LockEvent]


class RegistryFetchResponse(StatusResponse):
    item: Optional[ItemDataset]
    roles: Optional[Roles]
    locked: Optional[bool]


class ListRegistryResponse(BaseModel):
    status: Status
    num_items: int
    registry_items: List[ItemDataset]
    pagination_key: Optional[Dict[str, Any]]


class InputConvertRocrateCollectionFormat(BaseModel):
    rocrate_items: List[Dict[str, Any]]


class CollectionFormatConversion(BaseModel):
    handle: str
    collection_format: CollectionFormat
    s3: S3Location
    created_time: datetime
    updated_time: datetime


class InputConvertCollectionFormatRocrate(BaseModel):
    collection_format_items: List[CollectionFormatConversion]


class PossibleCollectionFormat(BaseModel):
    success: bool
    collection_format: Optional[CollectionFormat]
    error_message: Optional[str]


class PossibleRocrate(BaseModel):
    success: bool
    rocrate: Optional[ROCrate]
    error_message: Optional[str]


class ResponseConvertRocrateCollectionFormat(BaseModel):
    collection_format_items: List[PossibleCollectionFormat]


class ResponseConvertCollectionFormatRocrate(BaseModel):
    rocrate_items: List[PossibleRocrate]


class ReleaseApprovalRequest(BaseModel):
    dataset_id: IdentifiedResource
    approver_id: IdentifiedResource
    notes: str

class ReleaseApprovalRequestResponse(BaseModel):
    dataset_id: IdentifiedResource
    approver_id: IdentifiedResource
    details: str


class ActionApprovalRequest(BaseModel):
    dataset_id: IdentifiedResource
    approve: bool
    notes: str

class ActionApprovalRequestResponse(BaseModel):
    dataset_id: IdentifiedResource
    approved: bool
    details: str


class PresignedURLRequest(BaseModel):
    dataset_id: IdentifiedResource
    file_path: str
    expires_in: int = Field(
        HOURS_TO_SECS*3, 
        description="The number of seconds the presigned URL is valid for. Defaults to 3 hours (3600*3).",
        ge=1,
        le=HOURS_TO_SECS*24,
    )

class PresignedURLResponse(BaseModel):
    dataset_id: IdentifiedResource
    file_path: str
    presigned_url: str