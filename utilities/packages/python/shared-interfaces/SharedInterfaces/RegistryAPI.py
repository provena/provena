from pydantic import BaseModel
try:
    from SharedInterfaces.RegistryModels import *
    from SharedInterfaces.SharedTypes import StatusResponse, Status, ImportMode
except:
    from .RegistryModels import *
    from .SharedTypes import Status, StatusResponse, ImportMode

from typing import Any, Dict, Union, List

'''
LOCK
'''


class LockHistoryResponse(StatusResponse):
    history: Optional[List[LockEvent]]


class LockChangeRequest(BaseModel):
    id: str
    reason: str


class LockStatusResponse(BaseModel):
    locked: bool


"""
===============
VERSION REVERT
===============
"""


class ItemRevertRequest(BaseModel):
    # id of the item to revert
    id: str
    # id of the history entry for the item
    history_id: int
    # the reason for this revert
    reason: str


class ItemRevertResponse(StatusResponse):
    pass


"""
==============
AUTH RESPONSES
==============
"""


class DescribeAccessResponse(BaseModel):
    # combines the status and access description responses
    roles: Roles


class AuthRolesResponse(BaseModel):
    # the list of available roles for a given type
    roles: List[DescribedRole]

# Shared models


class QueryRecordTypes(str, Enum):
    # All types are returned - no filters
    ALL = "ALL"
    # Only seed items are returned
    SEED_ONLY = "SEED_ONLY"
    # Only complete items are returned (DEFAULT)
    COMPLETE_ONLY = "COMPLETE_ONLY"


class QueryFilter(BaseModel):
    item_category: Optional[ItemCategory]
    item_subtype: Optional[ItemSubType]
    # Defaults to complete only
    record_type: QueryRecordTypes = QueryRecordTypes.COMPLETE_ONLY


class SortType(str, Enum):
    CREATED_TIME = "CREATED_TIME"
    UPDATED_TIME = "UPDATED_TIME"
    DISPLAY_NAME = "DISPLAY_NAME"


# newest first (assuming timestamp)
DEFAULT_SORTING_ASCENDING = False


class SortOptions(BaseModel):
    sort_type: Optional[SortType]
    ascending: bool = DEFAULT_SORTING_ASCENDING


class SubtypeFilterOptions(BaseModel):
    # all filters that are not subtype specific
    record_type: QueryRecordTypes = QueryRecordTypes.COMPLETE_ONLY


class FilterOptions(SubtypeFilterOptions):
    item_subtype: Optional[ItemSubType]


class FilterType(str, Enum):
    ITEM_SUBTYPE = "ITEM_SUBTYPE"


PaginationKey = Dict[str, Any]

DEFAULT_PAGE_SIZE = 20


class SubtypeListRequest(BaseModel):
    filter_by: Optional[SubtypeFilterOptions]
    sort_by: Optional[SortOptions]
    pagination_key: Optional[PaginationKey]
    page_size: int = DEFAULT_PAGE_SIZE


class NoFilterSubtypeListRequest(BaseModel):
    sort_by: Optional[SortOptions]
    pagination_key: Optional[PaginationKey]
    page_size: int = DEFAULT_PAGE_SIZE


class GeneralListRequest(BaseModel):
    filter_by: Optional[FilterOptions]
    sort_by: Optional[SortOptions]
    pagination_key: Optional[PaginationKey]
    page_size: int = DEFAULT_PAGE_SIZE


class SchemaResponse(BaseModel):
    json_schema: Dict[str, Any]


class GenericFetchResponse(StatusResponse):
    item: Optional[Union[ItemBase, SeededItem]]
    roles: Optional[Roles]
    locked: Optional[bool]
    item_is_seed: Optional[bool]


class UntypedFetchResponse(StatusResponse):
    item: Optional[Dict[str, Any]]


class GenericListResponse(StatusResponse):
    # items
    items: Optional[List[Any]]
    seed_items: Optional[List[SeededItem]]
    unparsable_items: Optional[List[Dict[str, Any]]]

    # counts
    total_item_count: Optional[int]
    complete_item_count: Optional[int]
    seed_item_count: Optional[int]
    unparsable_item_count: Optional[int]
    not_authorised_count: Optional[int]

    # Pagination info
    pagination_key: Optional[PaginationKey]


class PaginatedListResponse(StatusResponse):
    # items
    items: Optional[List[Any]]
    # counts
    total_item_count: Optional[int]
    # Returned by previous paginations and used to indicate start of next query
    pagination_key: Optional[PaginationKey]


class UpdateResponse(StatusResponse):
    # if this item has provenance enabled versioning AND the update was from
    # seed -> complete
    register_create_activity_session_id: Optional[str]


class GenericSeedResponse(StatusResponse):
    seeded_item: Optional[SeededItem]


class GenericCreateResponse(StatusResponse):
    created_item: Optional[ItemBase]

    # if this item has provenance enabled versioning, this job spins off from
    # creation to create and then lodge the CreateActivity
    register_create_activity_session_id: Optional[str]


class VersionResponse(BaseModel):
    new_version_id: str

    # Whenever versioning occurs, there is a job spun off to create the
    # associated Version activity, update various models, and lodge the
    # Version activity provenance
    version_job_session_id: str


class VersionRequest(BaseModel):
    # Which item to create version of
    id: str

    # Reason for the version being required
    reason: str


class ProxyVersionRequest(VersionRequest):
    username: str


class UiSchemaResponse(StatusResponse):
    ui_schema: Optional[Dict[str, Any]]


class JsonSchemaResponse(StatusResponse):
    json_schema: Optional[Dict[str, Any]]


"""
========
ENTITIES
========
"""

# ==========================
# Dataset (Entity - Dataset)
# ==========================


class DatasetFetchResponse(GenericFetchResponse):
    item: Optional[Union[ItemDataset, SeededItem]]


class DatasetSeedResponse(GenericSeedResponse):
    None


class DatasetCreateResponse(GenericCreateResponse):
    created_item: Optional[ItemDataset]


class DatasetListResponse(GenericListResponse):
    items: Optional[List[ItemDataset]]

# =============================================
# Dataset Template (Entity - Dataset Template)
# =============================================


class DatasetTemplateFetchResponse(GenericFetchResponse):
    item: Optional[Union[ItemDatasetTemplate, SeededItem]]


class DatasetTemplateSeedResponse(GenericSeedResponse):
    None


class DatasetTemplateCreateResponse(GenericCreateResponse):
    created_item: Optional[ItemDatasetTemplate]


class DatasetTemplateListResponse(GenericListResponse):
    items: Optional[List[ItemDatasetTemplate]]

# ===============================================
# Software Base (Entity - Software) (NO ENDPOINT)
# ===============================================

# ===================================
# Model (Entity - Software <- Model)
# ===================================


class ModelFetchResponse(GenericFetchResponse):
    item: Optional[Union[ItemModel, SeededItem]]


class ModelSeedResponse(GenericSeedResponse):
    None


class ModelCreateResponse(GenericCreateResponse):
    created_item: Optional[ItemModel]


class ModelListResponse(GenericListResponse):
    items: Optional[List[ItemModel]]

# ============================================
# Registry Version (Activity - Registry Version)
# ============================================


class VersionFetchResponse(GenericFetchResponse):
    item: Optional[Union[ItemVersion, SeededItem]]


class VersionListResponse(GenericListResponse):
    items: Optional[List[ItemVersion]]

# ============================================
# Registry Create (Activity - Registry Create)
# ============================================


class CreateFetchResponse(GenericFetchResponse):
    item: Optional[Union[ItemCreate, SeededItem]]


class CreateListResponse(GenericListResponse):
    items: Optional[List[ItemCreate]]


# ================================================================
# Workflow Template (Entity - Workflow Template) (NO ENDPOINT)
# ================================================================

# ======================================================================================
# Model Workflow Template (Entity - Workflow Template <- Model Workflow Template)
# ======================================================================================


class ModelRunWorkflowTemplateFetchResponse(GenericFetchResponse):
    item: Optional[Union[ItemModelRunWorkflowTemplate, SeededItem]]


class ModelRunWorkflowTemplateSeedResponse(GenericSeedResponse):
    None


class ModelRunWorkflowTemplateCreateResponse(GenericCreateResponse):
    created_item: Optional[ItemModelRunWorkflowTemplate]


class ModelRunWorkflowTemplateListResponse(GenericListResponse):
    items: Optional[List[ItemModelRunWorkflowTemplate]]


"""
==========
ACTIVITIES
==========
"""

# ====================================================
# Workflow Run (Activity - Workflow Run) (NO ENDPOINT)
# ====================================================

# =================================================
# Model Run (Activity - Workflow Run <- Model Run)
# =================================================


class ModelRunFetchResponse(GenericFetchResponse):
    item: Optional[Union[ItemModelRun, SeededItem]]


class ModelRunSeedResponse(GenericSeedResponse):
    None


class ModelRunCreateResponse(GenericCreateResponse):
    created_item: Optional[ItemModelRun]


class ModelRunListResponse(GenericListResponse):
    items: Optional[List[ItemModelRun]]


"""
========
AGENTS
========
"""

# ========================
# Person (Agent - Person)
# ========================


class PersonFetchResponse(GenericFetchResponse):
    item: Optional[Union[ItemPerson, SeededItem]]


class PersonSeedResponse(GenericSeedResponse):
    None


class PersonCreateResponse(GenericCreateResponse):
    created_item: Optional[ItemPerson]


class PersonListResponse(GenericListResponse):
    items: Optional[List[ItemPerson]]

# ====================================
# Organisation (Agent - Organisation)
# ====================================


class OrganisationFetchResponse(GenericFetchResponse):
    item: Optional[Union[ItemOrganisation, SeededItem]]


class OrganisationSeedResponse(GenericSeedResponse):
    None


class OrganisationCreateResponse(GenericCreateResponse):
    created_item: Optional[ItemOrganisation]


class OrganisationListResponse(GenericListResponse):
    items: Optional[List[ItemOrganisation]]


# Admin endpoints and interfaces

class BundledItem(BaseModel):
    id: str
    item_payload: Dict[str, Any]
    auth_payload: Dict[str, Any]
    lock_payload: Dict[str, Any]


class TableNames(BaseModel):
    resource_table_name: str
    auth_table_name: str
    lock_table_name: str


class RegistryExportResponse(StatusResponse):
    items: Optional[List[BundledItem]]


class RegistryImportSettings(BaseModel):
    import_mode: ImportMode

    # Should the items supplied be parsed before being
    # added/overwritten
    parse_items: bool = True

    # Always force explicit deletion flag even if mode enables it
    allow_entry_deletion: bool = False

    # Should the changes be written - true means no writing false means write
    # the changes
    trial_mode: bool = True


class RegistryRestoreRequest(RegistryImportSettings):
    table_names: TableNames


class RegistryImportRequest(RegistryImportSettings):
    items: List[BundledItem]


class RegistryImportStatistics(BaseModel):
    old_registry_size: int
    new_registry_size: int
    deleted_entries: int
    overwritten_entries: int
    new_entries: int


class RegistryImportResponse(StatusResponse):
    status: Status
    trial_mode: bool
    statistics: Optional[RegistryImportStatistics]
    failure_list: Optional[List[Tuple[str, Dict[str, Any]]]]
