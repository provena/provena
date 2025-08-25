from pydantic.fields import ModelField
import pydantic
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum
import uvicorn  # type: ignore
from ProvenaInterfaces.RegistryModels import *
from ProvenaInterfaces.RegistryAPI import *
from helpers.item_type_route_generator import *
from routes.check_access import checks
from routes.dataset import dataset
from routes.registry_general import registry_general    
from routes.admin import import_export_restore, general_admin
from typing import Dict, Type, List, Generic
from config import base_config, dispatch_cors
from ProvenaSharedFunctionality.Registry.RegistryRouteActions import DATA_STORE_SERVICE_ROLE_NAME, PROV_SERVICE_ROLE_NAME
import warnings
from schemas import UI_SCHEMA_OVERRIDES, JSON_SCHEMA_OVERRIDES
from ProvenaSharedFunctionality.Registry.RegistryRouteActions import RouteActions, PROXY_EDIT_ROUTE_ACTIONS, STANDARD_ROUTE_ACTIONS, DATASET_ROUTE_ACTIONS, MODEL_RUN_ROUTE_ACTIONS
from route_models import RouteConfig
from ProvenaSharedFunctionality.SentryMonitoring import init_sentry
import sentry_sdk


# Patch for HTTPException to improve string representation
from fastapi import HTTPException

def httpexception_str_patch(self: HTTPException) -> str:
    return f"Status code: {self.status_code}, details: {self.detail}."

# Apply the patch
HTTPException.__str__ = httpexception_str_patch  # type: ignore


app = FastAPI()
init_sentry(
    dsn=base_config.sentry_dsn if base_config.monitoring_enabled else None,
    environment=base_config.sentry_environment,
    release=base_config.git_commit_id,
)
sentry_sdk.set_tag("API", "registry")
sentry_sdk.set_tag("Environment", base_config.sentry_environment)

# Get CORS middleware established

# Get the desired origins
origin_info = dispatch_cors(stage=base_config.stage,
                            base_domain=base_config.domain_base)

# If it is an origin list
if isinstance(origin_info, list):
    app.add_middleware(CORSMiddleware,
                       allow_credentials=True,
                       allow_origins=origin_info,
                       allow_methods=["*"],
                       allow_headers=["*"])
# Otherwise it is an origin regex
else:
    app.add_middleware(CORSMiddleware,
                       allow_credentials=True,
                       allow_origin_regex=origin_info,
                       allow_methods=["*"],
                       allow_headers=["*"])

app.include_router(checks.router, prefix="/check-access",
                   tags=["Access check"])

# route configs

BASE_REGISTRY_PREFIX = "/registry"

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
        # API in proxy mode where user context is passed through - this is for
        # all the proxy style routes
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
        # in proxy mode where user context is passed through - this is for all
        # the proxy style routes
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
    prefix = BASE_REGISTRY_PREFIX + \
        f"/{ITEM_CATEGORY_ROUTE_MAP[r_config.desired_category]}/{ITEM_SUB_TYPE_ROUTE_MAP[r_config.desired_subtype]}"

    # Include the router
    app.include_router(
        router,
        prefix=prefix,
        tags=r_config.tags  # type: ignore
    )

# general registry route
app.include_router(
    registry_general.router,
    prefix="/registry/general",
    tags=['General Registry']
)

# general registry route
app.include_router(
    dataset.router,
    prefix="/registry/entity/dataset",
    tags=['Entity Dataset']
)

# admin management routes
app.include_router(
    import_export_restore.router,
    prefix="/admin",
    tags=['Admin']
)

app.include_router(
    general_admin.router,
    prefix="/admin",
    tags=['Admin']
)


@app.get("/", operation_id="root")
async def root(
    config: Config = Depends(get_settings)
) -> Dict[str, str]:
    """
    Function Description
    --------------------

    Demonstration unauthenticated endpoint.


    Returns
    -------
    Json
        Basic message response



    See Also (optional)
    --------

    Examples (optional)
    --------

    """
    return {"message": "Health check successful."}

"""
==============
PYDANTIC PATCH
==============
"""

# FROM https://github.com/pydantic/pydantic/issues/1270#issuecomment-1209704699
# Explanation: Pydantic (as of 05/09/22) has improper JSON schema/open api generation
# for optional fields - the null type isn't in allowable list. The openAPI spec
# doesn't like multiple types, so instead used the anyOf with a null type to
# enable this optional functionality. (nullable=True is also possible but is not
# going to be supported in upcoming openAPI specs). This below method matches the
# field schema generator method and also the openapi generator method.
# There is a unit test in tests/test_functionality called test_nullable_property
# which asserts the output of this patch.


pydantic_field_type_schema = pydantic.schema.field_type_schema


def patch_pydantic_field_type_schema() -> None:
    """
    This ugly patch fixes the serialization of models containing Optional in them.
    https://github.com/samuelcolvin/pydantic/issues/1270
    """
    warnings.warn("Patching fastapi.applications.get_openapi")
    import fastapi.applications
    from fastapi.openapi.utils import get_openapi
    fastapi.applications.get_openapi = get_openapi

    warnings.warn("Patching pydantic.schema.field_type_schema")

    def field_type_schema(field: ModelField, **kwargs):  # type: ignore
        null_type_schema = {"type": "null", "title": "None"}
        f_schema, definitions, nested_models = pydantic_field_type_schema(
            field, **kwargs)
        if field.allow_none:
            s_type = f_schema.get('type')
            if s_type:
                # Hack to detect whether we are generating for openapi
                # fastapi sets the ref_prefix to '#/components/schemas/'.
                # When using for openapi, swagger does not seem to support an array
                # for type, so use anyOf instead.
                if kwargs.get('ref_prefix') == '#/components/schemas/':
                    f_schema = {'anyOf': [f_schema, null_type_schema]}
                else:
                    if not isinstance(s_type, list):
                        f_schema['type'] = [s_type]
                    f_schema['type'].append("null")
            elif "$ref" in f_schema:
                f_schema["anyOf"] = [
                    {**f_schema},
                    null_type_schema,
                ]
                del f_schema["$ref"]

            elif "allOf" in f_schema:
                f_schema['anyOf'] = f_schema['allOf']
                del f_schema['allOf']
                f_schema['anyOf'].append(null_type_schema)

            elif "anyOf" in f_schema or "oneOf" in f_schema:
                one_or_any = f_schema.get('anyOf') or f_schema.get('oneOf')
                for item in one_or_any:  # type: ignore
                    if item.get('type') == 'null':
                        break
                else:
                    one_or_any.append(null_type_schema)  # type: ignore

        return f_schema, definitions, nested_models

    pydantic.schema.field_type_schema = field_type_schema


patch_pydantic_field_type_schema()

"""
========
HANDLERS
========
"""

# Add lambda function
handler = Mangum(app)

if __name__ == "__main__":
    uvicorn.run(app, port=8000)
