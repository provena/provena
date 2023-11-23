from typing import Dict
from enum import Enum


class API_NAME(str, Enum):
    auth_api = "auth-api"
    data_store_api = "data-store-api"
    prov_api = "prov-api"
    registry_api = "registry-api"
    search_api = "search-api"
    identity_api = "identity-api"
    job_api = "job-api"


API_NAME_MAP: Dict[str, API_NAME] = {
    "auth-api": API_NAME.auth_api,
    "data-store-api": API_NAME.data_store_api,
    "prov-api": API_NAME.prov_api,
    "registry-api": API_NAME.registry_api,
    "search-api": API_NAME.search_api,
    "identity-api": API_NAME.identity_api,
    "job-api": API_NAME.job_api,
}

API_LOCATIONS_MAP: Dict[str, str] = {
    "auth-api": "auth-api",
    "data-store-api": "data-store-api",
    "prov-api": "prov-api",
    "registry-api": "registry-api",
    "search-api": "search-api",
    "identity-api": "id-service-api",
    "job-api": "job-api"
}

CONFIG_ENDPOINT_POSTFIX = "/admin/config"
REQUIRED_PARAM = "required_only"
RELATIVE_TO_HOME = "../../"

LOCAL_STORAGE_TOKEN_LOCATION = ".tokens.json"
