from ProvenaInterfaces.RegistryModels import *
from ProvenaInterfaces.RegistryAPI import *
from helpers.registry.item_type_route_generator import *
from routes.registry.dataset import dataset
from routes.registry.registry_general import registry_general    
from routes.registry.admin import import_export_restore
from typing import Dict, List
from ProvenaSharedFunctionality.Registry.RegistryRouteActions import DATA_STORE_SERVICE_ROLE_NAME, PROV_SERVICE_ROLE_NAME
from schemas import UI_SCHEMA_OVERRIDES, JSON_SCHEMA_OVERRIDES
from ProvenaSharedFunctionality.Registry.RegistryRouteActions import RouteActions, PROXY_EDIT_ROUTE_ACTIONS, STANDARD_ROUTE_ACTIONS, DATASET_ROUTE_ACTIONS, MODEL_RUN_ROUTE_ACTIONS
from route_models import RouteConfig

# route configs
BASE_REGISTRY_PREFIX = "/registry"
app = APIRouter(prefix=BASE_REGISTRY_PREFIX)


ITEM_CATEGORY_ROUTE_MAP: Dict[ItemCategory, str] = {
    ItemCategory.ACTIVITY: "activity",
    ItemCategory.ENTITY: "entity",
    ItemCategory.AGENT: "agent"
}
ITEM_SUB_TYPE_ROUTE_MAP: Dict[ItemSubType, str] = {
    ItemSubType.MODEL_RUN: "model_run",
    ItemSubType.MODEL: "model",
    ItemSubType.ORGANISATION: "organisation",
    ItemSubType.PERSON: "person",
    ItemSubType.MODEL_RUN_WORKFLOW_TEMPLATE: "model_run_workflow",
    ItemSubType.DATASET_TEMPLATE: "dataset_template",
    ItemSubType.DATASET: "dataset",
    ItemSubType.STUDY: "study",

    # These are read only routes which are directly controlled by async
    # jobs/side effects
    ItemSubType.CREATE: "create",
    ItemSubType.VERSION: "version"
}


# Can add more registry sub routes by adding to this config
# list - might need to add more models in the ProvenaInterfaces
# RegistryModels file.
normal_default_roles: Roles = [METADATA_READ_ROLE]
dataset_default_roles: Roles = [METADATA_READ_ROLE, DATASET_READ_ROLE]


# define some special permission overrides

# dataset

dataset_limited_access_roles = {ra: [DATA_STORE_SERVICE_ROLE_NAME]
                                for ra in PROXY_EDIT_ROUTE_ACTIONS +\
                                # Datasets have versioning enabled only with
                                # proxy route
                                    [RouteActions.PROXY_VERSION]}

model_run_limited_access_roles = {ra: [PROV_SERVICE_ROLE_NAME]
                                  for ra in PROXY_EDIT_ROUTE_ACTIONS}

PROV_VERSIONING_ENABLED_SUBTYPES: List[ItemSubType] = [
    # ItemSubType.WORKFLOW_RUN,
    # ItemSubType.MODEL_RUN,
    # ItemSubType.CREATE,
    # ItemSubType.VERSION,
    # ItemSubType.PERSON,
    # ItemSubType.ORGANISATION,
    # ItemSubType.SOFTWARE,

    # Currently only instantiable Entities
    ItemSubType.MODEL,
    ItemSubType.MODEL_RUN_WORKFLOW_TEMPLATE,
    ItemSubType.DATASET,
    ItemSubType.DATASET_TEMPLATE,
]


def outfit_with_prov_versioning(base_actions: List[RouteActions], subtype: ItemSubType, proxy: bool) -> List[RouteActions]:
    base = base_actions.copy()
    if subtype in PROV_VERSIONING_ENABLED_SUBTYPES:
        if proxy:
            base.extend(PROXY_PROVENANCE_VERSIONING_ROUTE_ACTIONS)
        else:
            base.extend(STANDARD_PROVENANCE_VERSIONING_ROUTE_ACTIONS)
    return base


route_configs: List[RouteConfig] = [
    # AGENT
    # organisation
    RouteConfig(
        desired_actions=outfit_with_prov_versioning(
            base_actions=STANDARD_ROUTE_ACTIONS,
            subtype=ItemSubType.ORGANISATION,
            proxy=False
        ),
        tags=['Organisation'],
        item_model_type=ItemOrganisation,
        item_domain_info_type=OrganisationDomainInfo,
        seed_response_type=OrganisationSeedResponse,
        fetch_response_type=OrganisationFetchResponse,
        create_response_type=OrganisationCreateResponse,
        list_response_type=OrganisationListResponse,
        desired_category=ItemCategory.AGENT,
        desired_subtype=ItemSubType.ORGANISATION,
        ui_schema=UI_SCHEMA_OVERRIDES.get(ItemOrganisation),
        json_schema_override=JSON_SCHEMA_OVERRIDES.get(ItemOrganisation),
        library_postfix="agent_organisation",
        available_roles=ENTITY_BASE_ROLE_LIST,
        default_roles=normal_default_roles,
        enforce_username_person_link=False,
        provenance_enabled_versioning=False
    ),
    # person
    RouteConfig(
        desired_actions=outfit_with_prov_versioning(
            base_actions=STANDARD_ROUTE_ACTIONS,
            subtype=ItemSubType.PERSON,
            proxy=False
        ),
        tags=['Person'],
        item_model_type=ItemPerson,
        item_domain_info_type=PersonDomainInfo,
        seed_response_type=PersonSeedResponse,
        fetch_response_type=PersonFetchResponse,
        create_response_type=PersonCreateResponse,
        list_response_type=PersonListResponse,
        desired_category=ItemCategory.AGENT,
        desired_subtype=ItemSubType.PERSON,
        ui_schema=UI_SCHEMA_OVERRIDES.get(ItemPerson),
        json_schema_override=JSON_SCHEMA_OVERRIDES.get(ItemPerson),
        library_postfix="agent_person",
        available_roles=ENTITY_BASE_ROLE_LIST,
        default_roles=normal_default_roles,
        enforce_username_person_link=False,
        provenance_enabled_versioning=False

    ),
    # ENTITY
    # model
    RouteConfig(
        desired_actions=outfit_with_prov_versioning(
            base_actions=STANDARD_ROUTE_ACTIONS,
            subtype=ItemSubType.MODEL,
            proxy=False
        ),
        tags=['Model'],
        item_model_type=ItemModel,
        item_domain_info_type=ModelDomainInfo,
        seed_response_type=ModelSeedResponse,
        fetch_response_type=ModelFetchResponse,
        create_response_type=ModelCreateResponse,
        list_response_type=ModelListResponse,
        desired_category=ItemCategory.ENTITY,
        desired_subtype=ItemSubType.MODEL,
        ui_schema=UI_SCHEMA_OVERRIDES.get(ItemModel),
        json_schema_override=JSON_SCHEMA_OVERRIDES.get(ItemModel),
        library_postfix="entity_model",
        available_roles=ENTITY_BASE_ROLE_LIST,
        default_roles=normal_default_roles,
        enforce_username_person_link=True,
        provenance_enabled_versioning=True

    ),
    RouteConfig(
        desired_actions=outfit_with_prov_versioning(
            base_actions=STANDARD_ROUTE_ACTIONS,
            subtype=ItemSubType.MODEL_RUN_WORKFLOW_TEMPLATE,
            proxy=False
        ),
        tags=['Model Run Workflow Template'],
        item_model_type=ItemModelRunWorkflowTemplate,
        item_domain_info_type=ModelRunWorkflowTemplateDomainInfo,
        seed_response_type=ModelRunWorkflowTemplateSeedResponse,
        fetch_response_type=ModelRunWorkflowTemplateFetchResponse,
        create_response_type=ModelRunWorkflowTemplateCreateResponse,
        list_response_type=ModelRunWorkflowTemplateListResponse,
        desired_category=ItemCategory.ENTITY,
        desired_subtype=ItemSubType.MODEL_RUN_WORKFLOW_TEMPLATE,
        ui_schema=UI_SCHEMA_OVERRIDES.get(ItemModelRunWorkflowTemplate),
        json_schema_override=JSON_SCHEMA_OVERRIDES.get(
            ItemModelRunWorkflowTemplate),
        library_postfix="entity_model_run_workflow_template",
        available_roles=ENTITY_BASE_ROLE_LIST,
        default_roles=normal_default_roles,
        enforce_username_person_link=True,
        provenance_enabled_versioning=True
    ),
    RouteConfig(
        desired_actions=outfit_with_prov_versioning(
            base_actions=STANDARD_ROUTE_ACTIONS,
            subtype=ItemSubType.DATASET_TEMPLATE,
            proxy=False
        ),
        tags=['Dataset Template'],
        item_model_type=ItemDatasetTemplate,
        item_domain_info_type=DatasetTemplateDomainInfo,
        seed_response_type=DatasetTemplateSeedResponse,
        fetch_response_type=DatasetTemplateFetchResponse,
        create_response_type=DatasetTemplateCreateResponse,
        list_response_type=DatasetTemplateListResponse,
        desired_category=ItemCategory.ENTITY,
        desired_subtype=ItemSubType.DATASET_TEMPLATE,
        ui_schema=UI_SCHEMA_OVERRIDES.get(ItemDatasetTemplate),
        json_schema_override=JSON_SCHEMA_OVERRIDES.get(ItemDatasetTemplate),
        library_postfix="entity_dataset_template",
        available_roles=ENTITY_BASE_ROLE_LIST,
        default_roles=normal_default_roles,
        enforce_username_person_link=True,
        provenance_enabled_versioning=True
    ),
    RouteConfig(
        desired_actions=DATASET_ROUTE_ACTIONS,
        tags=['Dataset'],
        item_model_type=ItemDataset,
        item_domain_info_type=DatasetDomainInfo,
        seed_response_type=DatasetSeedResponse,
        fetch_response_type=DatasetFetchResponse,
        create_response_type=DatasetCreateResponse,
        list_response_type=DatasetListResponse,
        desired_category=ItemCategory.ENTITY,
        desired_subtype=ItemSubType.DATASET,
        ui_schema=UI_SCHEMA_OVERRIDES.get(ItemDataset),
        json_schema_override=JSON_SCHEMA_OVERRIDES.get(ItemDataset),
        library_postfix="entity_dataset",
        available_roles=DATASET_ROLE_LIST,
        default_roles=dataset_default_roles,
        # the datasets can only be created and modified through the data store
        # API in proxy mode where username is passed through - this is for all
        # the proxy style routes
        limited_access_roles=dataset_limited_access_roles,

        # Datasets require linked Person before any modification actions
        enforce_username_person_link=True,

        # Special prov versioning for datasets
        provenance_enabled_versioning=True
    ),
    # ACTIVITY
    # Study
    RouteConfig(
        desired_actions=outfit_with_prov_versioning(
            base_actions=STANDARD_ROUTE_ACTIONS,
            subtype=ItemSubType.STUDY,
            proxy=False
        ),
        tags=['Study'],
        item_model_type=ItemStudy,
        item_domain_info_type=StudyDomainInfo,
        seed_response_type=StudySeedResponse,
        fetch_response_type=StudyFetchResponse,
        create_response_type=StudyCreateResponse,
        list_response_type=StudyListResponse,
        desired_category=ItemCategory.ACTIVITY,
        desired_subtype=ItemSubType.STUDY,
        ui_schema=UI_SCHEMA_OVERRIDES.get(ItemStudy),
        json_schema_override=JSON_SCHEMA_OVERRIDES.get(ItemStudy),
        library_postfix="activity_study",
        available_roles=ENTITY_BASE_ROLE_LIST,
        default_roles=normal_default_roles,
        # We will associate with a person in the lodged prov job - let's enforce
        # it
        enforce_username_person_link=True,
        # TODO implement 'create only' provenance versioning mode
        provenance_enabled_versioning=False
    ),
    # Activity: Registry Create
    RouteConfig(
        desired_actions=READ_ONLY_ROUTE_ACTIONS,
        tags=['Create Activity'],
        item_model_type=ItemCreate,
        item_domain_info_type=CreateDomainInfo,
        seed_response_type=None,
        fetch_response_type=CreateFetchResponse,
        create_response_type=None,
        list_response_type=CreateListResponse,
        desired_category=ItemCategory.ACTIVITY,
        desired_subtype=ItemSubType.CREATE,
        # These are None for now
        ui_schema=UI_SCHEMA_OVERRIDES.get(ItemCreate),
        json_schema_override=JSON_SCHEMA_OVERRIDES.get(ItemCreate),
        library_postfix="activity_create",
        available_roles=ENTITY_BASE_ROLE_LIST,
        default_roles=normal_default_roles,
        enforce_username_person_link=True,
        provenance_enabled_versioning=False
    ),
    # Activity: Registry VERSION
    RouteConfig(
        desired_actions=READ_ONLY_ROUTE_ACTIONS,
        tags=['Version Activity'],
        item_model_type=ItemVersion,
        item_domain_info_type=VersionDomainInfo,
        seed_response_type=None,
        fetch_response_type=VersionFetchResponse,
        create_response_type=None,
        list_response_type=VersionListResponse,
        desired_category=ItemCategory.ACTIVITY,
        desired_subtype=ItemSubType.VERSION,
        # These are None for now
        ui_schema=UI_SCHEMA_OVERRIDES.get(ItemVersion),
        json_schema_override=JSON_SCHEMA_OVERRIDES.get(ItemVersion),
        library_postfix="activity_version",
        available_roles=ENTITY_BASE_ROLE_LIST,
        default_roles=normal_default_roles,
        enforce_username_person_link=True,
        provenance_enabled_versioning=False
    ),
    # model run
    RouteConfig(
        desired_actions=MODEL_RUN_ROUTE_ACTIONS,
        tags=['Model Run'],
        item_model_type=ItemModelRun,
        item_domain_info_type=ModelRunDomainInfo,
        seed_response_type=ModelRunSeedResponse,
        fetch_response_type=ModelRunFetchResponse,
        create_response_type=ModelRunCreateResponse,
        list_response_type=ModelRunListResponse,
        desired_category=ItemCategory.ACTIVITY,
        desired_subtype=ItemSubType.MODEL_RUN,
        ui_schema=UI_SCHEMA_OVERRIDES.get(ItemModelRun),
        json_schema_override=JSON_SCHEMA_OVERRIDES.get(ItemModelRun),
        library_postfix="activity_model_run",
        available_roles=ENTITY_BASE_ROLE_LIST,
        default_roles=normal_default_roles,
        # the model runs can only be created and modified through the prov API
        # in proxy mode where username is passed through - this is for all the
        # proxy style routes
        limited_access_roles=model_run_limited_access_roles,
        enforce_username_person_link=False,
        provenance_enabled_versioning=False
    ),
]

# For each config, use the router generator
# function to generate a fully typed sub route
for r_config in route_configs:
    # Generate router
    router = generate_router(
        route_config=r_config,
    )

    # Work out nice prefix
    prefix = f"/{ITEM_CATEGORY_ROUTE_MAP[r_config.desired_category]}/{ITEM_SUB_TYPE_ROUTE_MAP[r_config.desired_subtype]}"

    # Include the router
    app.include_router(
        router,
        prefix=prefix,
        tags=r_config.tags  # type: ignore
    )

# general registry route
app.include_router(
    registry_general.router,
    prefix="/general",
    tags=['General Registry']
)

# general dataset route
app.include_router(
    dataset.router,
    prefix="/entity/dataset",
    tags=['Entity Dataset']
)

# admin management routes
app.include_router(
    import_export_restore.router,
    prefix="/admin",
    tags=['Admin']
)