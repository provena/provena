from pydantic import BaseModel, AnyHttpUrl, EmailStr, root_validator, validator, Extra, Field, schema
from pydantic.fields import ModelField
from pydantic.generics import GenericModel
from enum import Enum
from typing import Optional, List, Tuple, TypeVar, Dict, Type, Any, Set, Generic, Type
import itertools
from isodate import parse_duration  # type: ignore
from datetime import datetime, date

try:
    from ProvenaInterfaces.helpers.types import AnyUri
    from ProvenaInterfaces.helpers.helpers import duplicates
except:
    from .helpers.types import AnyUri
    from .helpers.helpers import duplicates

# Type alias to denote that a string references an ID
IdentifiedResource = str

# Apply pydantic patch from https://github.com/tiangolo/fastapi/issues/1378


def field_schema(field: ModelField, **kwargs: Any) -> Any:
    if field.field_info.extra.get("hidden_from_schema", False):
        raise schema.SkipField(f"{field.name} field is being hidden")
    else:
        return original_field_schema(field, **kwargs)


original_field_schema = schema.field_schema
schema.field_schema = field_schema


class ItemCategory(str, Enum):
    ACTIVITY = "ACTIVITY"
    AGENT = "AGENT"
    ENTITY = "ENTITY"


class ItemSubType(str, Enum):
    # Activities
    WORKFLOW_RUN = "WORKFLOW_RUN"
    MODEL_RUN = "MODEL_RUN"  # is a WORKFLOW_RUN
    STUDY = "STUDY"
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

    # all item types can also contain customised user metadata (optionally)
    # for datasets - this is kept in sync with the duplicated field in the collection format
    user_metadata: Optional[Dict[str, str]] = Field(
        None,
        title="Custom User Metadata",
        description="Optionally provide a collection of key value annotations describing this resource."
    )

    @staticmethod
    def get_searchable_fields() -> List[str]:
        return ['display_name', 'user_metadata']

    def get_search_ready_object(self) -> Dict[str, str]:
        base = {
            'display_name': self.display_name,
        }
        if self.user_metadata is not None:
            compacted = ""
            for k, v in self.user_metadata.items():
                compacted += f"{k} {v} "
            base['user_metadata'] = compacted
        else:
            base['user_metadata'] = ""

        return base


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

    # RRAPIS-1580 - move this to the run itself to avoid weird churn on template
    # software_version: str

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
            # RRAPIS-1580 moves this to model run payload
            # "software_version": self.software_version,
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
            # RRAPIS-1580 moves this to model run payload
            # "software_version",
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


class CollectionFormatAssociations(BaseModel):
    """
    Please provide information about the people and organisations related to this dataset.
    """
    # Registered organisation id
    organisation_id: str = Field(
        ...,
        title="Record Creator Organisation",
        description="Please select the organisation on behalf of which you are registering this data."
    )

    # ID of the registered Person Custodian
    data_custodian_id: Optional[str] = Field(
        None,
        title="Dataset Custodian",
        description="Please select the Registered Person who is the dataset custodian.",
    )

    # Free text info for point of contact
    point_of_contact: Optional[str] = Field(
        None,
        title="Point of Contact",
        description="Please provide a point of contact for enquiries about this data e.g. email address. Please ensure you have sought consent to include these details in the record.",
    )

    class Config:
        # Set all strings to not be empty
        min_anystr_length = 1
        # don't allow extra fields
        extra = Extra.forbid

        # JSON Schema
        title = "Dataset Associations"


class AccessInfo(BaseModel):
    """
    Please specify whether data is going to be stored in the Data Store, or referenced from an existing, externally hosted, source.
    """
    # is this going to be stored in the provena data store?
    reposited: bool = Field(
        True,
        title="Data Storage",
        description="Is the data going to be stored in the Data Store?"
    )

    # What is the best URI to access this data
    uri: Optional[AnyUri] = Field(
        None,
        title="Dataset URI",
        description="Provide the best URI of the externally hosted data.",
        format="uri"
    )
    # Instructions/advice on how to retrieve it
    description: Optional[str] = Field(
        None,
        title="Access Description",
        description="Provide information about how to access the externally hosted data, or other relevant notes."
    )

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
        else:
            # it is reposited, ensure URI and description are None
            if uri is not None:
                raise ValueError(
                    "Cannot provide a URI for external access if data is reposited in the Data Store.")
            if description is not None:
                raise ValueError(
                    "Cannot provide a description for external access if data is reposited in the Data Store.")
        return values

    class Config:
        # Set all strings to not be empty
        min_anystr_length = 1
        # don't allow extra fields
        extra = Extra.forbid

        title = "Access Info"


class OptionallyRequiredCheck(BaseModel):
    # default to False to ensure forms require explicit inclusion
    relevant: bool = False
    # default to true so forms default to satisfied state
    obtained: bool = False


# both of these controls are instances of optionally required check
class ExportControls(OptionallyRequiredCheck):
    """
    Is this dataset subject to any export controls permits? If so, has this dataset cleared any required due diligence checks and have you obtained any required permits?
    """
    class Config:
        # don't allow extra fields
        extra = Extra.forbid

        title = "Export Controls"


class IndigenousKnowledgeCheck(OptionallyRequiredCheck):
    """
    Does this dataset contain Indigenous Knowledge? If so, do you have consent from the relevant Aboriginal and Torres Strait Islander communities for its use and access via this data store?
    """
    class Config:
        # don't allow extra fields
        extra = Extra.forbid

        title = "Indigenous Knowledge and Consent"


class DatasetEthicsRegistrationCheck(OptionallyRequiredCheck):
    """
    Does this dataset include any human data or require ethics/privacy approval for its registration? If so, have you included any required ethics approvals, consent from the participants and/or appropriate permissions to register this dataset in this information system?
    """
    class Config:
        # don't allow extra fields
        extra = Extra.forbid

        title = "Dataset Registration Ethics and Privacy"


class DatasetEthicsAccessCheck(OptionallyRequiredCheck):
    """
    Does this dataset include any human data or require ethics/privacy approval for enabling its access by users of the information system? If so, have you included any required consent from the participants and/or appropriate permissions to facilitate access to this dataset in this information system?
    """
    class Config:
        # Set all strings to not be empty
        min_anystr_length = 1
        # don't allow extra fields
        extra = Extra.forbid

        title = "Dataset Access Ethics and Privacy"


class CollectionFormatSpatialInfo(BaseModel):
    """
    If your dataset includes spatial data, you can indicate the coverage, resolution and extent of this spatial data.
    """
    # What is the spatial coverage of the dataset? EWKT TODO validator
    coverage: Optional[str] = Field(
        None,
        title="Spatial Coverage",
        # TODO clarity here re: format and expectations of geometry features e.g. Geometry Collection?
        description="The geographic area applicable to the data asset. Please specify spatial coverage using the EWKT format.",
        # 50000 characters limit TODO justify this limit
        max_length=50000
    )

    # Decimal Degrees spatial resolution TODO validator
    resolution: Optional[str] = Field(
        None,
        title="Spatial Resolution",
        description="The spatial resolution applicable to the data asset. Please use the Decimal Degrees standard."
    )

    # Spatial extent i.e. bounding box - EWKT TODO validator
    extent: Optional[str] = Field(
        None,
        title="Spatial Extent",
        # TODO clarity here re: format and expectations of geometry features e.g. Geometry Collection, Polygon?
        description="The range of spatial coordinates applicable to the data asset. Please provide a bounding box extent using the EWKT format.",
        # 50000 characters limit TODO justify this limit
        max_length=50000
    )

    @validator('resolution')
    def validate_spatial_resolution(cls: Any, v: Optional[str]) -> Optional[str]:
        # None is okay as the field is optional
        if v is None:
            return v

        # val must be parsable as float
        try:
            val = float(v)
            assert val > 0, f"Spatial resolution must be non-negative and greater than than 0. Got '{val}'."
        except Exception as e:
            raise ValueError(
                f"Invalid spatial resolution. The value must conform to the Decimal Degrees format. Please provide a positive decimal value. Failed to parse the spatial resolution as a positive float. Details: {e}")
        return v

    class Config:
        # Set all strings to not be empty
        min_anystr_length = 1
        # don't allow extra fields
        extra = Extra.forbid

        title = "Dataset Spatial Information"


class TemporalDurationInfo(BaseModel):
    """
    You can specify the duration of temporal coverage by including both start and end date.
    """
    begin_date: date = Field(
        ...,
        title="Start Date",
        description="Please provide the start date of the dataset's temporal coverage."
    )
    end_date: date = Field(
        ...,
        title="End Date",
        description="Please provide the end date of the dataset's temporal coverage."
    )

    # validator to ensure that if both are set, they are in the correct order
    @root_validator(pre=False, skip_on_failure=True)
    def check_dates_in_order(cls: Any, values: Dict[str, Any]) -> Dict[str, Any]:
        begin_date: Optional[date] = values.get('begin_date')
        end_date: Optional[date] = values.get('end_date')

        if begin_date is not None and end_date is not None:
            if begin_date > end_date:
                raise ValueError(
                    "Begin Date must be before or equal to End Date.")
        return values

    class Config:
        # Set all strings to not be empty
        min_anystr_length = 1
        # don't allow extra fields
        extra = Extra.forbid

        title = "Temporal Duration"


class CollectionFormatTemporalInfo(BaseModel):
    """
    If your dataset provides data over a specified time period, you can include the duration and resolution of this temporal coverage.
    """
    # Supplying duration is optional but both fields within it required
    duration: Optional[TemporalDurationInfo] = None

    # Temporal resolution - ISO8601 Duration format e.g. "P1Y2M10DT2H30M"
    resolution: Optional[str] = Field(
        None,
        title="Temporal Resolution",
        description="The temporal resolution (i.e. time step) of the data. Please use the [ISO8601 duration format](https://en.wikipedia.org/wiki/ISO_8601#Durations) e.g. \"P1Y2M10DT2H30M\".",
    )

    # validate the temporal resolution conforms to expected format: "P1Y2M10DT2H30M\".
    @validator('resolution', always=True)  # run even for default value.
    def validate_temporal_resolution(cls: Any, v: str) -> str:
        try:
            if v is not None:
                parse_duration(v)
        except Exception as e:
            raise ValueError(
                f"Invalid temporal resolution. The value must conform to the ISO8601 Time Duration format (e.g.'P1Y2M10DT2H30M'). Details: {e}")
        return v

    class Config:
        # Set all strings to not be empty
        min_anystr_length = 1
        # don't allow extra fields
        extra = Extra.forbid

        title = "Dataset Temporal Information"


class OptionallyRequiredDate(BaseModel):
    relevant: bool = False
    value: Optional[date] = None

    @root_validator(pre=False, skip_on_failure=True)
    def check_value_provided(cls: Any, values: Dict[str, Any]) -> Dict[str, Any]:
        relevant: Optional[bool] = values.get('relevant')
        value: Optional[date] = values.get('value')

        assert relevant is not None

        if relevant == True:
            if value is None:
                raise ValueError(
                    "Must provide a date if the relevant field is set to True.")
        else:
            if value is not None:
                raise ValueError(
                    "Cannot provide a date if the relevant field is set to False.")
        return values


class PublishedDate(OptionallyRequiredDate):
    """
    Has the dataset been published? If so, please provide the date on which this version of the dataset was first published.
    """
    class Config:
        # disallow extra fields
        extra = Extra.forbid

        title = "Dataset Publication Date"


class CreatedDate(OptionallyRequiredDate):
    """
    Has the dataset been created? If so, please provide the date on which this version of the dataset was produced or generated.
    """
    class Config:
        # disallow extra fields
        extra = Extra.forbid

        title = "Dataset Creation Date"


class CollectionFormatDatasetInfo(BaseModel):
    """
    Please provide information about this dataset, including the name, description, creation date and publisher information.
    """
    name: str = Field(
        ...,
        title="Dataset name",
        description="Please provide a readable name for the dataset.",
    )
    description: str = Field(
        ...,
        title="Description",
        description="Please provide a more detailed description of the dataset. This should include the nature of the data, the intended usage, and any other relevant information.",
    )

    # information about whether the dataset is reposited or not
    access_info: AccessInfo

    # linked publisher in registry
    publisher_id: str = Field(
        ...,
        title="Publisher",
        description="Please provide information about the organisation which is publishing or producing this dataset. If this is your organisation, please select it again using the tool below.",
    )

    # created/published dates
    created_date: CreatedDate

    published_date: PublishedDate

    # License field - selected by drop down
    license: AnyHttpUrl = Field(
        ...,
        title="Usage license",
        description="Please select a standard license for usage, by default it will be 'Copyright'.",
        format="uri"
    )

    # What is the purpose of this dataset?
    purpose: Optional[str] = Field(
        None,
        title="Dataset Purpose",
        description="A brief description of the reason a data asset was created. Should be a good guide to the potential usefulness of a data asset to other users.",
    )

    # Who holds the rights to this dataset? Free text input
    rights_holder: Optional[str] = Field(
        None,
        title="Dataset Rights Holder",
        description="Specify the party owning or managing rights over the resource. Please ensure you have sought consent to include these details in the record.",
    )

    # Usage limitations? Free text input
    usage_limitations: Optional[str] = Field(
        None,
        title="Usage Limitations",
        description="A statement that provides information on any caveats or restrictions on access or on the use of the data asset, including legal, security, privacy, commercial or other limitations.",
    )

    preferred_citation: Optional[str] = Field(
        None,
        title="Preferred dataset citation",
        description="If you would like to specify how this dataset should be cited, please use the checkbox below to indicate this preference, and enter your preferred citation in the text box.",
    )

    # Spatial information?
    spatial_info: Optional[CollectionFormatSpatialInfo] = None

    # Temporal information?
    temporal_info: Optional[CollectionFormatTemporalInfo] = None

    # What formats are included in the dataset files e.g. txt, pdf, html, css, json etc
    formats: Optional[List[str]] = Field(
        None,
        title="Dataset File Formats",
        description="What file formats are present in this dataset? E.g. \"pdf\", \"csv\" etc.",
    )

    # Keywords associated with this dataset

    # TODO validate this JSON schema is suitable
    keywords: Optional[List[str]] = Field(
        None,
        title="Keywords",
        description="Provide a list of keywords which describe your dataset [Optional].",
    )

    # Custom user metadata if desired - this field is kept synchronised with the
    # base domain info user metadata TODO consider how we can more naturally
    # include move the dataset collection format into the domain info while
    # allowing for immutable fields/properties such as s3 location etc
    user_metadata: Optional[Dict[str, str]] = Field(
        None, title="Custom User Metadata", description="Optionally provide a collection of key value annotations for this dataset.")

    # this is not going to be shown in schema anymore, but will remain in the
    # actual model in case existing versions are relevant
    version: Optional[str] = Field(None, hidden_from_schema=True)

    class Config:
        # Set all strings to not be empty
        min_anystr_length = 1
        # don't allow extra fields
        extra = Extra.forbid

        title = "Dataset Information"
        field = {'version': {'exclude': True}}


class CollectionFormatApprovals(BaseModel):
    """
    Please ensure that the following approvals are considered. Your dataset may not be fit for inclusion in the Data Store if it does not meet the following requirements.
    """
    ethics_registration: DatasetEthicsRegistrationCheck
    ethics_access: DatasetEthicsAccessCheck
    indigenous_knowledge: IndigenousKnowledgeCheck
    export_controls: ExportControls

    class Config:
        # Set all strings to not be empty
        min_anystr_length = 1
        # don't allow extra fields
        extra = Extra.forbid

        # JSON Schema
        title = "Dataset Approvals"


class CollectionFormat(BaseModel):
    """
    This form collects metadata about the dataset you are registering as well as the registration itself. Please ensure the fields below are completed accurately.
    """
    # Required
    associations: CollectionFormatAssociations
    approvals: CollectionFormatApprovals
    dataset_info: CollectionFormatDatasetInfo

    class Config:
        # Set all strings to not be empty
        min_anystr_length = 1
        # don't allow extra fields
        extra = Extra.forbid

        # JSON Schema
        title = "Dataset Metadata"


class S3Location(BaseModel):
    bucket_name: str
    path: str
    s3_uri: str


class ReleasedStatus(str, Enum):
    # If changing this, also update QueryDatasetReleaseStatusType in RegistryAPI
    # which should mirror this but python doesnt allow for inheriting enum classes.

    # Aprroval status for release of datasets
    NOT_RELEASED = "NOT_RELEASED"
    PENDING = "PENDING"
    RELEASED = "RELEASED"


class ReleaseAction(str, Enum):
    # Action taken on a dataset regarding releasing
    REQUEST = "REQUEST"
    APPROVE = "APPROVE"
    REJECT = "REJECT"


class ReleaseHistoryEntry(BaseModel):
    # What action was taken
    action: ReleaseAction

    # What time did this occur?
    timestamp: int

    # All actions relate to an approver
    approver: IdentifiedResource

    # Some actions relate to a requester - i.e. Requesting
    requester: Optional[IdentifiedResource]

    # All actions are associated with some notes/details
    notes: str


class DatasetDomainInfo(DomainInfoBase):
    # main dataset metadata that data store front end collects
    collection_format: CollectionFormat

    # the s3 location information NOTE This is now optional as not all
    # registered datasets allow data repositing
    s3: S3Location

    release_history: List[ReleaseHistoryEntry] = []

    # need here for Global Secondary Index to search by approver.
    release_status: ReleasedStatus
    release_approver: Optional[IdentifiedResource]
    # timestamp when release status was last updated
    release_timestamp: Optional[int]
    # collection_format.access_info.uri for non-reposited datasets to enable fetch/list by uri.
    access_info_uri: Optional[str]

    # validate access_info_uri and collection_format.dataset_info.access_info.uri are always the same
    @root_validator(pre=False, skip_on_failure=True)
    def check_access_info_uri(cls: Any, values: Dict[str, Any]) -> Dict[str, Any]:
        access_info_uri: Optional[str] = values.get('access_info_uri')
        collection_format: Optional[CollectionFormat] = values.get(
            'collection_format')
        assert collection_format, "collection_format must be present"
        access_info = collection_format.dataset_info.access_info
        assert (access_info.uri and access_info_uri) or (
            not access_info.uri and not access_info_uri), f"access_info_uri must always match collection_format.access_info.uri. Got access_info_uri={access_info_uri} and collection_format.access_info.uri={access_info.uri}"

        if collection_format.dataset_info.access_info.uri != access_info_uri:
            raise ValueError(
                f"access_info_uri must always match collection_format.access_info.uri. Got access_info_uri={access_info_uri} and collection_format.access_info.uri={access_info.uri}")
        return values

    # validate release_approver and release_timestamp are both present or both absent
    @root_validator(skip_on_failure=True)
    def check_release_status(cls: Any, values: Dict[str, Any]) -> Dict[str, Any]:
        release_approver: Optional[IdentifiedResource] = values.get(
            'release_approver')
        release_timestamp: Optional[int] = values.get('release_timestamp')

        # make sure both fields are present or both are absent
        if (release_approver is None) != (release_timestamp is None):
            raise ValueError(
                f"Cannot provide a release activity timestamp without release approver and vice versa. Got release_approver={release_approver} and release_timestamp={release_timestamp}")
        return values


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
            'description',
            'name',
            'publisher',
            'organisation',
            'keywords^2',
            'formats',
            'preferred_citation',
            'usage_limitations',
            'rights_holder',
            'purpose',
            'data_custodian'
        ]

    def get_search_ready_object(self) -> Dict[str, str]:
        # get base info
        item_base = ItemBase.parse_obj(self.dict())
        base = item_base.get_search_ready_object()

        # pull out relevant sub fields
        cf = self.collection_format
        di: CollectionFormatDatasetInfo = cf.dataset_info
        assoc: CollectionFormatAssociations = cf.associations
        org = assoc.organisation_id

        extended: Dict[str, str] = {
            'description': di.description,
            'name': di.name,
            'publisher': di.publisher_id,
            'organisation': org,
            'keywords': " ".join(di.keywords or []),
            'formats': " ".join(di.formats or []),
            'preferred_citation': di.preferred_citation or "",
            'usage_limitations': di.usage_limitations or "",
            'rights_holder': di.rights_holder or "",
            'purpose': di.purpose or "",
            'data_custodian': assoc.data_custodian_id or ""
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
    from ProvenaInterfaces.ProvenanceModels import ModelRunRecord
except:
    from .ProvenanceModels import ModelRunRecord


class WorkflowRunCompletionStatus(str, Enum):
    INCOMPLETE = "INCOMPLETE"
    COMPLETE = "COMPLETE"
    LODGED = "LODGED"

# =========================
# Study (Activity <- Study)
# =========================


class StudyDomainInfo(DomainInfoBase):
    title: str
    description: str
    study_alternative_id: Optional[str] = None


class ItemStudy(ActivityBase, StudyDomainInfo):
    item_subtype: ItemSubType = ItemSubType.STUDY

    # override history
    history: List[HistoryEntry[StudyDomainInfo]]  # type: ignore

    _validate_subtype = validate_subtype(
        'item_subtype', ItemSubType.STUDY)

    def get_search_ready_object(self) -> Dict[str, str]:
        # no extra searchable info - just return parent
        item_base = ItemBase.parse_obj(self.dict())
        base = item_base.get_search_ready_object()
        extended: Dict[str, str] = {
            'title': self.title,
            'description': self.title,
            'study_alternative_id': self.study_alternative_id or "",
        }
        base.update(extended)
        return base

    @staticmethod
    def get_searchable_fields() -> List[str]:
        # no extra searchable info - just return parent
        return ItemBase.get_searchable_fields() + [
            'title',
            'description',
            'study_alternative_id'
        ]

    @validator('history')
    def unique_history(cls: Any, v: List[HistoryEntry[Any]]) -> Any:
        # validate that the ids are unique in the history
        unique_history_ids(v)
        return v


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
            'new_version_number': str(self.new_version_number)
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
    (ItemCategory.ACTIVITY, ItemSubType.STUDY): ItemStudy,
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
    (ItemCategory.ACTIVITY, ItemSubType.STUDY): StudyDomainInfo,
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


# ================
#  DISPLAY PATCHES
# ================

# patch to move the custom user metadata field to bottom of pydantic models

# This list includes the objects for which to move
patched_objects: List[Type[BaseModel]] = [
    StudyDomainInfo,
    ModelRunDomainInfo,
    CreateDomainInfo,
    VersionDomainInfo,
    PersonDomainInfo,
    OrganisationDomainInfo,
    ModelDomainInfo,
    ModelRunWorkflowTemplateDomainInfo,
    DatasetTemplateDomainInfo,
    DatasetDomainInfo,
]

for target_model in patched_objects:
    # this moves the user metadata field to the end of each domain info model so
    # that it displays last in forms

    # TODO consider instead spinning off a separate model and inherting it last in the models (bit more repetition)
    fields = target_model.__fields__.copy()
    u_data = fields.pop("user_metadata")
    target_model.__fields__ = {**fields, "user_metadata": u_data}
