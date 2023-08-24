from pydantic import BaseModel, AnyHttpUrl, EmailStr, root_validator, validator, HttpUrl, Extra
from pydantic.generics import GenericModel
from enum import Enum
from typing import Optional, List, Tuple, TypeVar, Dict, Type, Any, Set, Generic
import itertools
from datetime import datetime, date

try:
    from SharedInterfaces.helpers.types import AnyUri
    from SharedInterfaces.helpers.helpers import duplicates
except:
    from .helpers.types import AnyUri
    from .helpers.helpers import duplicates

# Type alias to denote that a string references an ID
IdentifiedResource = str


class ItemCategory(str, Enum):
    ACTIVITY = "ACTIVITY"
    AGENT = "AGENT"
    ENTITY = "ENTITY"


class ItemSubType(str, Enum):
    # Activities
    WORKFLOW_RUN = "WORKFLOW_RUN"
    MODEL_RUN = "MODEL_RUN"  # is a WORKFLOW_RUN
    CREATE = "CREATE"
    VERSION = "VERSION"

    # Agents
    PERSON = "PERSON"  # ✓
    ORGANISATION = "ORGANISATION"  # ✓

    # Entities
    SOFTWARE = "SOFTWARE"  # ✓
    MODEL = "MODEL"  # is a SOFTWARE # ✓
    WORKFLOW_TEMPLATE = "WORKFLOW_TEMPLATE"  # ✓
    MODEL_RUN_WORKFLOW_TEMPLATE = \
        "MODEL_RUN_WORKFLOW_TEMPLATE"  # is a WORKFLOW_DEF'N # ✓
    DATASET = "DATASET"  # ✓
    DATASET_TEMPLATE = "DATASET_TEMPLATE"  # ✓


"""
==========
VALIDATORS
=========
"""
# taken from https://github.com/pydantic/pydantic/discussions/2938


def validate_subtype_helper(defined_subtype: ItemSubType, required_subtype: ItemSubType) -> ItemSubType:
    assert defined_subtype == required_subtype, f"Incorrect item_subtype provided. The required type is {required_subtype}."
    return defined_subtype


def validate_subtype(defined_subtype: str, required_subtype: ItemSubType) -> Any:
    return validator(defined_subtype, allow_reuse=True, pre=False)(lambda v: validate_subtype_helper(v, required_subtype))


def validate_category_helper(defined_category: ItemCategory, required_category: ItemCategory) -> ItemCategory:
    assert defined_category == required_category, f"Incorrect item_category provided. The required category is {required_category}."
    return defined_category


def validate_category(defined_category: str, required_category: ItemCategory) -> Any:
    return validator(defined_category, allow_reuse=True, pre=False)(lambda v: validate_category_helper(v, required_category))


"""
===========
LOCK MODELS
===========
"""


class LockActionType(str, Enum):
    LOCK = "LOCK"
    UNLOCK = "UNLOCK"


class LockEvent(BaseModel):
    # Locked or unlocked
    action_type: LockActionType
    # Who did it?

    # user
    username: str
    # email
    email: Optional[str]

    # Why did they lock/unlock it
    reason: str
    # When did this happen? (unix timestamp)
    timestamp: int


class LockInformation(BaseModel):
    # is the resource locked?
    locked: bool
    # what is the history of lock actions
    history: List[LockEvent]

# maps to the lock table deployed in parallel to main registry table


class LockTableEntry(BaseModel):
    # the id (handle) primary key
    id: str
    # the access settings
    lock_information: LockInformation


"""
============
AUTH MODELS 
============
"""

# A role is a string
Role = str

# A role list is a collection of roles
Roles = List[Role]

# Basic read/write for metadata - common to all entities
METADATA_READ_ROLE = "metadata-read"
METADATA_WRITE_ROLE = "metadata-write"

metadata_read_write: Roles = [
    METADATA_READ_ROLE,
    METADATA_WRITE_ROLE
]

# Roles for datasets
DATASET_READ_ROLE = "dataset-data-read"
DATASET_WRITE_ROLE = "dataset-data-write"

dataset_data_read_write: Roles = [
    DATASET_READ_ROLE,
    DATASET_WRITE_ROLE,
]

# owner role - this is a special role
ADMIN_ROLE = "admin"
admin_role: Roles = [
    ADMIN_ROLE
]


# These are role lists for the various entity types
ENTITY_BASE_ROLE_LIST = metadata_read_write + admin_role
DATASET_ROLE_LIST = ENTITY_BASE_ROLE_LIST + dataset_data_read_write


ALL_ROLES = set(DATASET_ROLE_LIST + ENTITY_BASE_ROLE_LIST)


class DescribedRole(BaseModel):
    role_display_name: str
    role_name: str
    description: str
    also_grants: List[str]


# for each role - provides some metadata
ROLE_METADATA_MAP: Dict[str, DescribedRole] = {
    METADATA_READ_ROLE: DescribedRole(
        role_display_name="Metadata Read",
        role_name=METADATA_READ_ROLE,
        also_grants=[],
        description="Enables visibility of a resource and it's metadata."
    ),
    METADATA_WRITE_ROLE: DescribedRole(
        role_display_name="Metadata Write",
        role_name=METADATA_WRITE_ROLE,
        also_grants=[METADATA_READ_ROLE],
        description="Enables the modification of a resource's metadata."
    ),
    DATASET_READ_ROLE: DescribedRole(
        role_display_name="Dataset Data Read",
        role_name=DATASET_READ_ROLE,
        also_grants=[METADATA_READ_ROLE],
        description="Enables the downloading of the contents of a dataset."
    ),
    DATASET_WRITE_ROLE: DescribedRole(
        role_display_name="Dataset Data Write",
        role_name=DATASET_WRITE_ROLE,
        also_grants=[METADATA_READ_ROLE,
                     METADATA_WRITE_ROLE, DATASET_READ_ROLE],
        description="Enables the uploading, modification and deletion of dataset files."
    ),
    ADMIN_ROLE: DescribedRole(
        role_display_name="Admin",
        role_name=ADMIN_ROLE,
        also_grants=[METADATA_READ_ROLE, METADATA_WRITE_ROLE,
                     DATASET_READ_ROLE, DATASET_WRITE_ROLE],
        description="Enables all actions on a resource and it's contents, including changes to access settings."
    )
}

# Check that all roles are described
for role in ALL_ROLES:
    assert role in ROLE_METADATA_MAP


class AccessSettings(BaseModel):
    # who owns this thing - established via username (persistent unchangeable unique keycloak user identifier)
    owner: str

    # What can all registry users do bounded by registry access
    general: Roles

    # map of Group ID from Auth API -> AccessModel
    groups: Dict[str, Roles]


# maps to the auth table deployed in parallel to main registry table
class AuthTableEntry(BaseModel):
    # the id (handle) primary key
    id: str
    # the access settings
    access_settings: AccessSettings


class DomainInfoBase(BaseModel):
    # This is the base for the seed item
    # input - each sub type will extend this
    # to specify additional required domain
    # information

    # what is the minimal display name
    # for this item
    display_name: str

    @staticmethod
    def get_searchable_fields() -> List[str]:
        # stub method
        return ['display_name']

    def get_search_ready_object(self) -> Dict[str, str]:
        return {
            'display_name': self.display_name,
        }


class RecordType(str, Enum):
    SEED_ITEM = "SEED_ITEM"
    COMPLETE_ITEM = "COMPLETE_ITEM"


DomainInfoTypeVar = TypeVar('DomainInfoTypeVar', bound=DomainInfoBase)


class HistoryEntry(GenericModel, Generic[DomainInfoTypeVar]):
    # unique id within scope of record - incremented
    id: int
    # When was this entry created
    timestamp: int
    # Why was this update performed?
    reason: str
    # What is the username of the user who performed this update?
    username: str
    # The contents of the domain info as of this update
    item: DomainInfoTypeVar


def unique_history_ids(history_list: List[HistoryEntry[Any]]) -> None:
    ids = list(map(lambda h: h.id, history_list))
    assert len(ids) == len(set(ids)), "Non unique ID list in item history"


class HistoryBase(GenericModel, Generic[DomainInfoTypeVar]):
    # History is just a list of history entries - this is a generic type base class
    history: List[HistoryEntry[DomainInfoTypeVar]]


class VersioningInfo(BaseModel):
    previous_version: Optional[str]
    version: int
    reason: Optional[str]
    next_version: Optional[str]

    @root_validator(pre=False, skip_on_failure=True)
    def check_reason_provided(cls: Any, values: Dict[str, Any]) -> Dict[str, Any]:
        prev_version = values['previous_version']
        reason = values['reason']
        if prev_version is not None:
            if reason is None:
                raise ValueError(
                    "Items with a previous version must specify a reason for the updated version.")
        return values


class WorkflowLinks(BaseModel):
    # Create prov session id spinoff (optionally)
    create_activity_workflow_id: Optional[str] = None

    # Version prov session id spinoff
    version_activity_workflow_id: Optional[str] = None


class RecordInfo(BaseModel):
    # Handle ID
    # optional for unseeded identities
    id: str

    # owners username - this links to a registered Person through the link service
    owner_username: str

    # when was this item created
    # unix timestamp
    # optional - added in at seed time
    created_timestamp: int

    # when was this item last updated
    # optional - added in on update/seed
    updated_timestamp: int

    # what is the overall type
    item_category: ItemCategory

    # what is the sub type
    item_subtype: ItemSubType

    # is this seed or complete
    record_type: RecordType

    # Not all types have workflow links - only prov versioning enabled
    workflow_links: Optional[WorkflowLinks] = None

    # Versioning (all optional)
    versioning_info: Optional[VersioningInfo] = None

    @staticmethod
    def get_searchable_fields() -> List[str]:
        # this is a special elastic search syntax
        return ['id^4', 'item_category', 'item_subtype']

    def get_search_ready_object(self) -> Dict[str, str]:
        return {
            'id': self.id,
            'item_category': self.item_category.value,
            'item_subtype': self.item_subtype.value,
            'owner_username': self.owner_username
        }


class SeededItem(RecordInfo):
    # inherits all values from RecordInfo including search term generators
    None


class ItemBase(RecordInfo, DomainInfoBase, HistoryBase[DomainInfoBase]):
    def get_search_ready_object(self) -> Dict[str, str]:
        record_info = RecordInfo.parse_obj(self.dict())
        ri_base = record_info.get_search_ready_object()
        domain_info = DomainInfoBase.parse_obj(self.dict())
        di_base = domain_info.get_search_ready_object()
        ri_base.update(di_base)
        return ri_base

    @staticmethod
    def get_searchable_fields() -> List[str]:
        # return combination of record info and domain info
        return RecordInfo.get_searchable_fields() +\
            DomainInfoBase.get_searchable_fields()


# Entity/activity/agent extension of item base


class EntityBase(ItemBase):
    # override item category
    item_category: ItemCategory = ItemCategory.ENTITY

    _validate_category = validate_category(
        'item_category', ItemCategory.ENTITY)


class AgentBase(ItemBase):
    # override item category
    item_category: ItemCategory = ItemCategory.AGENT

    _validate_category = validate_category('item_category', ItemCategory.AGENT)
    # no non domain specific entity information
    # at the moment


class ActivityBase(ItemBase):
    # override item category
    item_category: ItemCategory = ItemCategory.ACTIVITY

    _validate_category = validate_category(
        'item_category', ItemCategory.ACTIVITY)


"""
========
ENTITIES
========
"""

# =============================================
# Dataset Template (Entity - Dataset Template)
# =============================================


class ResourceUsageType(str, Enum):
    # This is a parameter file
    PARAMETER_FILE = "PARAMETER_FILE"
    # This is a config file
    CONFIG_FILE = "CONFIG_FILE"
    # This is forcing data
    FORCING_DATA = "FORCING_DATA"
    # This is unspecified general input data
    GENERAL_DATA = "GENERAL_DATA"


class ResourceSpatialMetadata(BaseModel):
    # TODO how do we define spatial information?
    None


class ResourceTemporalMetadata(BaseModel):
    # TODO how do we define temporal information?

    # temporal extent
    # unix timestamp
    start_time: int
    # unix timestamp
    end_time: int

    # temporal jump
    # timestep
    # TODO collaborate on whether this is useful
    # interval: int


class DatasetParameter(BaseModel):
    # TODO collaborate on this - starting ideas
    parameter_name: Optional[str] = None
    column_name: Optional[str] = None
    column_index: Optional[int] = None
    description: Optional[str] = None
    vocabulary_id: Optional[str] = None


# class BaseResourceInformation(BaseModel):
#    # e.g. "This file/folder describes the expected coral values under xyz
#    # assumptions"
#    description: str
#
#    # Will the model run be rejected if no path is provided for this resource?
#    optional: Optional[bool] = None
#
#    # usage - what is this thing being used for
#    usage_type: ResourceUsageType
#
#    # type of thing - assumes file but could be folder
#    is_folder: Optional[bool] = None
#
#    # additional metadata (free form KVPs for users to add things)
#    additional_metadata: Optional[Dict[str, str]] = None
#
#    # Simplifying payload for now...
#
#    # e.g. ".csv"
#    # extension: Optional[str] = None
#
#    # description of parameters that this dataset reports
#    # parameters: Optional[List[DatasetParameter]] = None
#
#    # associated temporal/spatial information
#    # spatial_metadata: Optional[ResourceSpatialMetadata] = None
#    # temporal_metadata: Optional[ResourceTemporalMetadata] = None
#
#    # size estimates (MB)
#    # size_estimate: Optional[int] = None
#    # size_min: Optional[int] = None
#    # size_max: Optional[int] = None
#
#    # enforce size constraints?
#    # enforce_size_constraints: Optional[bool] = False


class DefinedResource(BaseModel):
    # Contains all base information + the known path relative to the dataset
    # base
    path: str

    # e.g. "This file/folder describes the expected coral values under xyz
    # assumptions"
    description: str

    # usage - what is this thing being used for
    usage_type: ResourceUsageType

    # Will the model run be rejected if no path is provided for this resource?
    optional: Optional[bool] = None

    # type of thing - assumes file but could be folder
    is_folder: Optional[bool] = None

    # additional metadata (free form KVPs for users to add things)
    additional_metadata: Optional[Dict[str, str]] = None

    def get_search_ready_string(self) -> str:
        return " ".join(
            [
                # resource path
                self.path,
                # description
                self.description,
                # annotations
                " ".join([f"{key} {value}" for key, value in (
                    self.additional_metadata.items() if self.additional_metadata else {})])
            ]
        )


class DeferredResource(BaseModel):
    # Contains all the base information and,

    # a resource key - at model run time, this resource key must be matched with
    # a path that fulfils it
    key: str

    # e.g. "This file/folder describes the expected coral values under xyz
    # assumptions"
    description: str

    # usage - what is this thing being used for
    usage_type: ResourceUsageType

    # Will the model run be rejected if no path is provided for this resource?
    optional: Optional[bool] = None

    # type of thing - assumes file but could be folder
    is_folder: Optional[bool] = None

    # additional metadata (free form KVPs for users to add things)
    additional_metadata: Optional[Dict[str, str]] = None

    def get_search_ready_string(self) -> str:
        return " ".join(
            [
                # resource key
                self.key,
                # description
                self.description,
                # annotations
                " ".join([f"{key} {value}" for key, value in (
                    self.additional_metadata.items() if self.additional_metadata else {})])
            ]
        )


class DatasetTemplateDomainInfo(DomainInfoBase):
    # Provide a basic description of the nature of this template - if the
    # resources are adequately described within the resource payloads then this
    # is optional
    description: Optional[str] = None

    # These are resources known/defined at template time - covers the use case
    # in which the user has a pre-specified file path/name within the dataset
    # which is known at template time consistently
    defined_resources: List[DefinedResource] = []

    # Deferred resources represents a 'placeholder' in which the exact file path
    # information will be supplied at model run time.
    deferred_resources: List[DeferredResource] = []

    @root_validator(pre=False, skip_on_failure=True)
    def check_unique_deferred_keys(cls: Any, values: Dict[str, Any]) -> Dict[str, Any]:
        deferred_resources: Optional[List[DeferredResource]
                                     ] = values['deferred_resources']
        if deferred_resources is not None:
            key_set: Set[str] = set()
            for resource in deferred_resources:
                key_set.add(resource.key)
            if len(key_set) != len(deferred_resources):
                raise ValueError(
                    "Non unique resource_key properties in provided deferred resources.")
        return values


class ItemDatasetTemplate(EntityBase, DatasetTemplateDomainInfo):
    item_subtype: ItemSubType = ItemSubType.DATASET_TEMPLATE

    # override history
    history: List[HistoryEntry[DatasetTemplateDomainInfo]]  # type: ignore

    _validate_subtype = validate_subtype(
        'item_subtype', ItemSubType.DATASET_TEMPLATE)

    def get_search_ready_object(self) -> Dict[str, str]:
        item_base = ItemBase.parse_obj(self.dict())
        base = item_base.get_search_ready_object()
        extended: Dict[str, str] = {
            "description": self.description or "",
            "deferred_resources": " ".join([
                r.get_search_ready_string() for r in self.deferred_resources
            ]),
            "defined_resources": " ".join([
                r.get_search_ready_string() for r in self.defined_resources
            ]),
        }
        base.update(extended)
        return base

    @staticmethod
    def get_searchable_fields() -> List[str]:
        return ItemBase.get_searchable_fields() + [
            "description",
            "deferred_resources",
            "defined_resources",
        ]

    @validator('history')
    def unique_history(cls: Any, v: List[HistoryEntry[Any]]) -> Any:
        # validate that the ids are unique in the history
        unique_history_ids(v)
        return v


# ==================================
# Software Base (Entity - Software)
# ==================================
class SoftwareDomainInfo(DomainInfoBase):
    # name of piece of software
    name: str

    # description
    # what is this software?
    description: str

    # URL to more information
    documentation_url: AnyHttpUrl

    # where to find the source
    source_url: AnyHttpUrl

    # TODO this can be expanded as per https://confluence.csiro.au/display/RRAPIS/Provenance+Entities
    # keep this generic information about software rather than model specific


class ItemSoftware(EntityBase, SoftwareDomainInfo):
    # override sub type
    item_subtype: ItemSubType = ItemSubType.SOFTWARE

    # override history
    history: List[HistoryEntry[SoftwareDomainInfo]]  # type: ignore

    _validate_subtype = validate_subtype('item_subtype', ItemSubType.SOFTWARE)

    def get_search_ready_object(self) -> Dict[str, str]:
        item_base = ItemBase.parse_obj(self.dict())
        base = item_base.get_search_ready_object()
        extended: Dict[str, str] = {
            "name": self.name,
            "description": self.description,
            "documentation_url": self.documentation_url,
            "source_url": self.source_url,
        }
        base.update(extended)
        return base

    @staticmethod
    def get_searchable_fields() -> List[str]:
        return ItemBase.get_searchable_fields() + [
            "name",
            "description",
            "documentation_url",
            "source_url"
        ]

    @validator('history')
    def unique_history(cls: Any, v: List[HistoryEntry[Any]]) -> Any:
        # validate that the ids are unique in the history
        unique_history_ids(v)
        return v


# ===================================
# Model (Entity - Software <- Model)
# ===================================


class ModelDomainInfo(SoftwareDomainInfo):
    # TODO specialty model information here
    # maybe reference to registered model?
    # e.g. coconet?
    None


class ItemModel(EntityBase, ModelDomainInfo):
    # override sub type
    item_subtype: ItemSubType = ItemSubType.MODEL

    # override history
    history: List[HistoryEntry[ModelDomainInfo]]  # type: ignore

    _validate_subtype = validate_subtype('item_subtype', ItemSubType.MODEL)

    def get_search_ready_object(self) -> Dict[str, str]:
        item_base = ItemBase.parse_obj(self.dict())
        base = item_base.get_search_ready_object()
        extended: Dict[str, str] = {
            "name": self.name,
            "description": self.description,
            "documentation_url": self.documentation_url,
            "source_url": self.source_url,
        }
        base.update(extended)
        return base

    @staticmethod
    def get_searchable_fields() -> List[str]:
        return ItemBase.get_searchable_fields() + [
            "name",
            "description",
            "documentation_url",
            "source_url"
        ]

    @validator('history')
    def unique_history(cls: Any, v: List[HistoryEntry[Any]]) -> Any:
        # validate that the ids are unique in the history
        unique_history_ids(v)
        return v

# ===================================================
# Workflow Template (Entity - Workflow Template)
# ===================================================


class AutomationSchedule(BaseModel):
    # TODO define this
    None


class WorkflowTemplateAnnotations(BaseModel):
    required: List[str] = []
    optional: List[str] = []

    # Check that these keys are unique
    @root_validator(pre=False, skip_on_failure=True)
    def check_unique_keys(cls: Any, values: Dict[str, Any]) -> Dict[str, Any]:
        required = values.get('required')
        optional = values.get('optional')
        if required is not None and optional is not None:
            key_set: Set[str] = set(required).union(set(optional))
            if not (len(key_set) == len(required) + len(optional)):
                raise ValueError(
                    "Provided required and/or optional field keys are non-unique.")
        return values

    def make_searchable(self) -> str:
        return " ".join(self.required) + " ".join(self.optional)


class TemplateResource(BaseModel):
    template_id: IdentifiedResource
    optional: Optional[bool] = None


class WorkflowTemplateDomainInfo(DomainInfoBase):
    # Specify the software ID and version at time of template the validity of a
    # definition is tied to the lifecycle of the software
    software_id: IdentifiedResource
    software_version: str

    # inputs? List of dataset templates
    input_templates: List[TemplateResource] = []

    # outputs? List of dataset templates
    output_templates: List[TemplateResource] = []

    # Expected KVPs
    annotations: Optional[WorkflowTemplateAnnotations] = None

    @validator('input_templates', 'output_templates')
    def template_ids_unique_per_end(cls, v: List[TemplateResource]) -> List[TemplateResource]:
        id_list = [template.template_id for template in v]
        if len(duplicates(id_list)):
            raise ValueError(
                f"Cannot support duplicate templates being used twice in just input templates, or twice in just output templates. Duplicates: {duplicates(id_list)}.")
        return v


class ItemWorkflowTemplate(EntityBase, WorkflowTemplateDomainInfo):
    # override sub type
    item_subtype: ItemSubType = ItemSubType.WORKFLOW_TEMPLATE

    # override history
    history: List[HistoryEntry[WorkflowTemplateDomainInfo]]  # type: ignore

    _validate_subtype = validate_subtype(
        'item_subtype', ItemSubType.WORKFLOW_TEMPLATE)

    def get_search_ready_object(self) -> Dict[str, str]:
        item_base = ItemBase.parse_obj(self.dict())
        base = item_base.get_search_ready_object()
        extended: Dict[str, str] = {
            "software_id": self.software_id,
            "software_version": self.software_version,
            "input_templates": " ".join([t.template_id for t in self.input_templates]),
            "output_templates": " ".join([t.template_id for t in self.output_templates]),
            "annotations": self.annotations.make_searchable() if self.annotations else ""
        }
        base.update(extended)
        return base

    @staticmethod
    def get_searchable_fields() -> List[str]:
        return ItemBase.get_searchable_fields() + [
            "software_id",
            "software_version",
            "input_templates",
            "output_templates",
            "annotations"
        ]

    @validator('history')
    def unique_history(cls: Any, v: List[HistoryEntry[Any]]) -> Any:
        # validate that the ids are unique in the history
        unique_history_ids(v)
        return v

# ======================================================================================
# Dataset (Entity <- Dataset)
# ======================================================================================


class CollectionFormatOrganisation(BaseModel):
    # Required
    name: str

    # Optional
    ror: Optional[HttpUrl]

    class Config:
        # Set all strings to not be empty
        min_anystr_length = 1
        # don't allow extra fields
        extra = Extra.forbid


class CollectionFormatAssociations(BaseModel):
    # Registered organisation id
    organisation_id: str

    class Config:
        # Set all strings to not be empty
        min_anystr_length = 1
        # don't allow extra fields
        extra = Extra.forbid


class AccessInfo(BaseModel):
    # is this going to be stored in the provena data store?
    reposited: bool
    # What is the best URI to access this data
    uri: Optional[AnyUri]
    # Instructions/advice on how to retrieve it
    description: Optional[str]

    @root_validator(skip_on_failure=True)
    def check_external_access_provided(cls: Any, values: Dict[str, Any]) -> Dict[str, Any]:
        # This validator ensures that if reposited is False, external access
        # info is not None and fields are populated
        reposited: Optional[bool] = values.get('reposited')
        uri: Optional[str] = values.get('uri')
        description: Optional[str] = values.get('description')

        # arbitrary change
        assert reposited is not None

        if not reposited:
            if (uri is None):
                raise ValueError(
                    "Must provide a URI for external access if data is not reposited in the Data Store.")
            if (description is None):
                raise ValueError(
                    "Must provide a description for external access if data is not reposited in the Data Store.")
        return values


class OptionallyRequiredCheck(BaseModel):
    # default to False to ensure forms require explicit inclusion
    relevant: bool = False
    # default to true so forms default to satisfied state
    obtained: bool = False


# both of these controls are instances of optionally required check
class ExportControls(OptionallyRequiredCheck):
    pass


class IndigenousKnowledgeCheck(OptionallyRequiredCheck):
    pass


class DatasetEthicsRegistrationCheck(OptionallyRequiredCheck):
    pass


class DatasetEthicsAccessCheck(OptionallyRequiredCheck):
    pass


class CollectionFormatDatasetInfo(BaseModel):
    # Required
    name: str
    description: str

    # information about whether the dataset is reposited or not
    access_info: AccessInfo

    # linked publisher in registry
    publisher_id: str

    created_date: date
    published_date: date
    license: AnyHttpUrl

    # Optional
    preferred_citation: Optional[str]

    keywords: Optional[List[str]]

    # this is not going to be shown in schema anymore, but will remain in the
    # actual model in case existing versions are relevant
    version: Optional[str] = None

    class Config:
        # Set all strings to not be empty
        min_anystr_length = 1
        # don't allow extra fields
        extra = Extra.forbid


class CollectionFormatApprovals(BaseModel):
    ethics_registration: DatasetEthicsRegistrationCheck
    ethics_access: DatasetEthicsAccessCheck
    indigenous_knowledge: IndigenousKnowledgeCheck
    export_controls: ExportControls

    class Config:
        # Set all strings to not be empty
        min_anystr_length = 1
        # don't allow extra fields
        extra = Extra.forbid


class CollectionFormat(BaseModel):
    # Required
    associations: CollectionFormatAssociations
    dataset_info: CollectionFormatDatasetInfo
    approvals: CollectionFormatApprovals

    class Config:
        # Set all strings to not be empty
        min_anystr_length = 1
        # don't allow extra fields
        extra = Extra.forbid


class S3Location(BaseModel):
    bucket_name: str
    path: str
    s3_uri: str


class DatasetDomainInfo(DomainInfoBase):
    # main dataset metadata that data store front end collects
    collection_format: CollectionFormat

    # the s3 location information NOTE This is now optional as not all
    # registered datasets allow data repositing
    s3: S3Location


class ItemDataset(EntityBase, DatasetDomainInfo):
    # override sub type
    item_subtype: ItemSubType = ItemSubType.DATASET

    # override history
    history: List[HistoryEntry[DatasetDomainInfo]]  # type: ignore

    _validate_subtype = validate_subtype(
        'item_subtype', ItemSubType.DATASET)

    @staticmethod
    def get_searchable_fields() -> List[str]:
        # this is a special elastic search syntax
        return ItemBase.get_searchable_fields() + [
            'description', 'name', 'publisher', 'author', 'keywords^2'
        ]

    def get_search_ready_object(self) -> Dict[str, str]:
        # get base info
        item_base = ItemBase.parse_obj(self.dict())
        base = item_base.get_search_ready_object()

        # pull out relevant sub fields
        cf = self.collection_format
        di = cf.dataset_info
        org = cf.associations.organisation_id

        extended: Dict[str, str] = {
            'description': di.description,
            'name': di.name,
            'publisher': di.publisher_id,
            'organisation': org,
            'keywords': " ".join(di.keywords or [])
        }
        base.update(extended)

        return base

    @validator('history')
    def unique_history(cls: Any, v: List[HistoryEntry[Any]]) -> Any:
        # validate that the ids are unique in the history
        unique_history_ids(v)
        return v

# ======================================================================================
# Model Workflow Template (Entity - Workflow Template <- Model Workflow Template)
# ======================================================================================


class ModelRunWorkflowTemplateDomainInfo(WorkflowTemplateDomainInfo):
    # TODO expand model work flow def'n
    # expects that the software references a Model rather than just generic software
    # this can be enforced at ingestion time
    None


class ItemModelRunWorkflowTemplate(EntityBase, ModelRunWorkflowTemplateDomainInfo):
    # override sub type
    item_subtype: ItemSubType = ItemSubType.MODEL_RUN_WORKFLOW_TEMPLATE

    # override history
    history: List[  # type: ignore
        HistoryEntry[ModelRunWorkflowTemplateDomainInfo]]

    _validate_subtype = validate_subtype(
        'item_subtype', ItemSubType.MODEL_RUN_WORKFLOW_TEMPLATE)

    def get_search_ready_object(self) -> Dict[str, str]:
        item_base = ItemBase.parse_obj(self.dict())
        base = item_base.get_search_ready_object()
        extended: Dict[str, str] = {
            "software_id": self.software_id,
            "software_version": self.software_version,
            "input_templates": " ".join([t.template_id for t in self.input_templates]),
            "output_templates": " ".join([t.template_id for t in self.output_templates]),
            "annotations": self.annotations.make_searchable() if self.annotations else ""
        }
        base.update(extended)
        return base

    @staticmethod
    def get_searchable_fields() -> List[str]:
        return ItemBase.get_searchable_fields() + [
            "software_id",
            "software_version",
            "input_templates",
            "output_templates",
            "annotations"
        ]

    @validator('history')
    def unique_history(cls: Any, v: List[HistoryEntry[Any]]) -> Any:
        # validate that the ids are unique in the history
        unique_history_ids(v)
        return v


"""
==========
ACTIVITIES
==========
"""

# model run

# avoid circular imports by importing late
try:
    from SharedInterfaces.ProvenanceModels import ModelRunRecord
except:
    from .ProvenanceModels import ModelRunRecord


class WorkflowRunCompletionStatus(str, Enum):
    INCOMPLETE = "INCOMPLETE"
    COMPLETE = "COMPLETE"
    LODGED = "LODGED"

# ==========================================
# Registry Version (Activity <- Registry Version)
# ==========================================


class VersionDomainInfo(DomainInfoBase):
    # Should include link to the created item
    reason: str
    from_item_id: str
    to_item_id: str
    new_version_number: int


class ItemVersion(ActivityBase, VersionDomainInfo):
    item_subtype: ItemSubType = ItemSubType.VERSION

    # override history
    history: List[HistoryEntry[VersionDomainInfo]]  # type: ignore

    _validate_subtype = validate_subtype(
        'item_subtype', ItemSubType.VERSION)

    def get_search_ready_object(self) -> Dict[str, str]:
        # no extra searchable info - just return parent
        item_base = ItemBase.parse_obj(self.dict())
        base = item_base.get_search_ready_object()
        extended: Dict[str, str] = {
            'from_item_id': self.from_item_id,
            'to_item_id': self.to_item_id,
            'new_version_number': self.new_version_number
        }
        base.update(extended)
        return base

    @staticmethod
    def get_searchable_fields() -> List[str]:
        # no extra searchable info - just return parent
        return ItemBase.get_searchable_fields() + [
            'from_item_id',
            'to_item_id',
            'new_version_number'
        ]

    @validator('history')
    def unique_history(cls: Any, v: List[HistoryEntry[Any]]) -> Any:
        # validate that the ids are unique in the history
        unique_history_ids(v)
        return v


# ==========================================
# Registry Create (Activity <- Workflow Run)
# ==========================================


class CreateDomainInfo(DomainInfoBase):
    # The base info includes other important info e.g. person, time etc

    # Should include link to the created item
    created_item_id: str


class ItemCreate(ActivityBase, CreateDomainInfo):
    item_subtype: ItemSubType = ItemSubType.CREATE

    # override history
    history: List[HistoryEntry[CreateDomainInfo]]  # type: ignore

    _validate_subtype = validate_subtype(
        'item_subtype', ItemSubType.CREATE)

    def get_search_ready_object(self) -> Dict[str, str]:
        # no extra searchable info - just return parent
        item_base = ItemBase.parse_obj(self.dict())
        base = item_base.get_search_ready_object()
        extended: Dict[str, str] = {
            "created_item_id": self.created_item_id
        }
        base.update(extended)
        return base

    @staticmethod
    def get_searchable_fields() -> List[str]:
        # no extra searchable info - just return parent
        return ItemBase.get_searchable_fields() + [
            "created_item_id"
        ]

    @validator('history')
    def unique_history(cls: Any, v: List[HistoryEntry[Any]]) -> Any:
        # validate that the ids are unique in the history
        unique_history_ids(v)
        return v

# ========================================
# Workflow Run (Activity - Workflow Run)
# ========================================


class WorkflowRunDomainInfo(DomainInfoBase):
    # status of the record
    record_status: WorkflowRunCompletionStatus
    None


class ItemWorkflowRun(ActivityBase, WorkflowRunDomainInfo):
    item_subtype: ItemSubType = ItemSubType.WORKFLOW_RUN

    # override history
    history: List[HistoryEntry[WorkflowRunDomainInfo]]  # type: ignore

    _validate_subtype = validate_subtype(
        'item_subtype', ItemSubType.WORKFLOW_RUN)

    def get_search_ready_object(self) -> Dict[str, str]:
        # no extra searchable info - just return parent
        item_base = ItemBase.parse_obj(self.dict())
        base = item_base.get_search_ready_object()
        extended: Dict[str, str] = {
        }
        base.update(extended)
        return base

    @staticmethod
    def get_searchable_fields() -> List[str]:
        # no extra searchable info - just return parent
        return ItemBase.get_searchable_fields() + [
        ]

    @validator('history')
    def unique_history(cls: Any, v: List[HistoryEntry[Any]]) -> Any:
        # validate that the ids are unique in the history
        unique_history_ids(v)
        return v


# =================================================
# Model Run (Activity - Workflow Run <- Model Run)
# =================================================


class ModelRunDomainInfo(WorkflowRunDomainInfo):
    # original input format
    record: ModelRunRecord
    # serialised prov document
    prov_serialisation: str


class ItemModelRun(ActivityBase, ModelRunDomainInfo):
    # override sub type
    item_subtype: ItemSubType = ItemSubType.MODEL_RUN

    # override history
    history: List[HistoryEntry[ModelRunDomainInfo]]  # type: ignore

    _validate_subtype = validate_subtype('item_subtype', ItemSubType.MODEL_RUN)

    def get_search_ready_object(self) -> Dict[str, str]:
        item_base = ItemBase.parse_obj(self.dict())
        base = item_base.get_search_ready_object()

        # base info
        extended: Dict[str, str] = {
            "prov_serialisation": self.prov_serialisation,
        }

        # and extend based on model run records make searchable function
        model_run_record_search_object = self.record.get_search_ready_object()
        extended.update(model_run_record_search_object)
        base.update(extended)
        return base

    @staticmethod
    def get_searchable_fields() -> List[str]:
        item_base = ItemBase.get_searchable_fields()
        model_run_record_fields = ModelRunRecord.get_searchable_fields()
        above_fields = [
            "prov_serialisation"
        ]
        return item_base + model_run_record_fields + above_fields

    @validator('history')
    def unique_history(cls: Any, v: List[HistoryEntry[Any]]) -> Any:
        # validate that the ids are unique in the history
        unique_history_ids(v)
        return v


"""
========
AGENTS
========
"""

# ========================
# Person (Agent - Person)
# ========================


class PersonDomainInfo(DomainInfoBase):
    email: EmailStr

    # person info
    first_name: str
    last_name: str

    # optional info
    orcid: Optional[AnyHttpUrl]

    # Consent to make this person
    ethics_approved: bool = False


class ItemPerson(AgentBase, PersonDomainInfo):
    # override sub type
    item_subtype: ItemSubType = ItemSubType.PERSON

    # override history
    history: List[HistoryEntry[PersonDomainInfo]]  # type: ignore

    _validate_subtype = validate_subtype('item_subtype', ItemSubType.PERSON)

    def get_search_ready_object(self) -> Dict[str, str]:
        item_base = ItemBase.parse_obj(self.dict())
        base = item_base.get_search_ready_object()
        extended: Dict[str, str] = {
            "first_name": self.first_name,
            "last_name": self.first_name,
            "email": self.email,
            "orcid": str(self.orcid) if self.orcid else ""
        }
        base.update(extended)
        return base

    @staticmethod
    def get_searchable_fields() -> List[str]:
        return ItemBase.get_searchable_fields() + [
            "first_name",
            "last_name",
            "email",
            "orcid"
        ]

    @validator('history')
    def unique_history(cls: Any, v: List[HistoryEntry[Any]]) -> Any:
        # validate that the ids are unique in the history
        unique_history_ids(v)
        return v

# ====================================
# Organisation (Agent - Organisation)
# ====================================


class OrganisationDomainInfo(DomainInfoBase):
    # organisation info
    name: str

    # optional info
    ror: Optional[AnyHttpUrl]


class ItemOrganisation(AgentBase, OrganisationDomainInfo):
    # override sub type
    item_subtype: ItemSubType = ItemSubType.ORGANISATION

    # override history
    history: List[HistoryEntry[OrganisationDomainInfo]]  # type: ignore

    _validate_subtype = validate_subtype(
        'item_subtype', ItemSubType.ORGANISATION)

    def get_search_ready_object(self) -> Dict[str, str]:
        item_base = ItemBase.parse_obj(self.dict())
        base = item_base.get_search_ready_object()
        extended: Dict[str, str] = {
            "name": self.name,
            "ror": str(self.ror) if self.ror else ""
        }
        base.update(extended)
        return base

    @staticmethod
    def get_searchable_fields() -> List[str]:
        return ItemBase.get_searchable_fields() + [
            "name",
            "ror"
        ]

    @validator('history')
    def unique_history(cls: Any, v: List[HistoryEntry[Any]]) -> Any:
        # validate that the ids are unique in the history
        unique_history_ids(v)
        return v


MODEL_TYPE_MAP: Dict[Tuple[ItemCategory, ItemSubType], Type[ItemBase]] = {
    (ItemCategory.ACTIVITY, ItemSubType.MODEL_RUN): ItemModelRun,
    (ItemCategory.ACTIVITY, ItemSubType.CREATE): ItemCreate,
    (ItemCategory.ACTIVITY, ItemSubType.VERSION): ItemVersion,
    (ItemCategory.AGENT, ItemSubType.PERSON): ItemPerson,
    (ItemCategory.AGENT, ItemSubType.ORGANISATION): ItemOrganisation,
    (ItemCategory.ENTITY, ItemSubType.MODEL): ItemModel,
    (ItemCategory.ENTITY, ItemSubType.MODEL_RUN_WORKFLOW_TEMPLATE): ItemModelRunWorkflowTemplate,
    (ItemCategory.ENTITY, ItemSubType.DATASET_TEMPLATE): ItemDatasetTemplate,
    (ItemCategory.ENTITY, ItemSubType.DATASET): ItemDataset,
}
MODEL_DOMAIN_INFO_TYPE_MAP: Dict[Tuple[ItemCategory, ItemSubType], Type[DomainInfoBase]] = {
    (ItemCategory.ACTIVITY, ItemSubType.MODEL_RUN): ModelRunDomainInfo,
    (ItemCategory.ACTIVITY, ItemSubType.CREATE): CreateDomainInfo,
    (ItemCategory.ACTIVITY, ItemSubType.VERSION): VersionDomainInfo,
    (ItemCategory.AGENT, ItemSubType.PERSON): PersonDomainInfo,
    (ItemCategory.AGENT, ItemSubType.ORGANISATION): OrganisationDomainInfo,
    (ItemCategory.ENTITY, ItemSubType.MODEL): ModelDomainInfo,
    (ItemCategory.ENTITY, ItemSubType.MODEL_RUN_WORKFLOW_TEMPLATE): ModelRunWorkflowTemplateDomainInfo,
    (ItemCategory.ENTITY, ItemSubType.DATASET_TEMPLATE): DatasetTemplateDomainInfo,
    (ItemCategory.ENTITY, ItemSubType.DATASET): DatasetDomainInfo,
}


# create a merged collection of all unique searchable fields of registry models
# as per above map
ALL_SEARCHABLE_FIELDS = list(set(
    itertools.chain(*[model_type.get_searchable_fields()
                    for model_type in MODEL_TYPE_MAP.values()])
))
