# handle ardc endpoint
TEST_ARDC_SERVICE_ENDPOINT = "https://demo.identifiers.ardc.edu.au/pids/"
PROD_ARDC_SERVICE_ENDPOINT = "https://identifiers.ardc.edu.au/pids"


# Default domain setups
# ===============================================

WARMER_DEFAULT_DOMAIN = "warmer"

BUILD_BADGE_BUILD_PREFIX = "deploy-build-badge"
BUILD_BADGE_INTERFACE_PREFIX = "interface-build-badge"
BUILD_BADGE_INTERFACE_PREFIX = "interface-build-badge"
AUTH_DEFAULT_DOMAIN = "auth"

HANDLE_DEFAULT_DOMAIN = "handle"

DATA_DEFAULT_API_DOMAIN = "data-api"
DATA_DEFAULT_UI_DOMAIN = "data"

SHARED_INTERFACES_PATH = "../utilities/packages/python/shared-interfaces"
FAST_API_KEYCLOAK_AUTH_PATH = "../utilities/packages/python/fast-api-keycloak-auth"
SHARED_REGISTRY_PATH = "../utilities/packages/python/registry-shared-functionality"
ECS_SQS_SHARED_UTILS_PATH = "../async-util/ecs-sqs-python-tools"

DEFAULT_EXTRA_HASH_DIRS = [SHARED_INTERFACES_PATH]
REGISTRY_DEPENDANT_HASH_DIRS = DEFAULT_EXTRA_HASH_DIRS + [SHARED_REGISTRY_PATH]

ASYNC_CONNECTOR_EXTRA_HASH_DIRS = DEFAULT_EXTRA_HASH_DIRS
JOB_ENABLED_API_EXTRA_HASH_DIRS = DEFAULT_EXTRA_HASH_DIRS + \
    [ECS_SQS_SHARED_UTILS_PATH]
ASYNC_INVOKER_EXTRA_HASH_DIRS = DEFAULT_EXTRA_HASH_DIRS
ASYNC_JOB_API_EXTRA_HASH_DIRS = DEFAULT_EXTRA_HASH_DIRS + \
    [FAST_API_KEYCLOAK_AUTH_PATH]

# Prov job deps

# Shared, ECS, keycloak
PROV_JOB_EXTRA_HASH_DIRS = [SHARED_INTERFACES_PATH,
                            FAST_API_KEYCLOAK_AUTH_PATH, ECS_SQS_SHARED_UTILS_PATH]
# Shared, ECS, keycloak, registry
REGISTRY_JOB_EXTRA_HASH_DIRS = [SHARED_INTERFACES_PATH,
                                FAST_API_KEYCLOAK_AUTH_PATH, ECS_SQS_SHARED_UTILS_PATH, SHARED_REGISTRY_PATH]
# Shared, ECS
EMAIL_JOB_EXTRA_HASH_DIRS = [SHARED_INTERFACES_PATH,
                             ECS_SQS_SHARED_UTILS_PATH]

AUTH_API_DEFAULT_DOMAIN = "auth-api"

ASYNC_JOBS_API_DEFAULT_DOMAIN = "job-api"

SEARCH_SERVICE_DEFAULT_DOMAIN = "search-service"
SEARCH_API_DEFAULT_DOMAIN = "search"

DEFAULT_GLOBAL_INDEX_NAME = "global_index"
DEFAULT_ENTITY_INDEX_NAME = "registry_index"
DEFAULT_DATA_STORE_INDEX_NAME = "data_store_index"

REGISTRY_API_DEFAULT_DOMAIN = "registry-api"
REGISTRY_UI_DEFAULT_DOMAIN = "registry"

PROV_API_DEFAULT_DOMAIN = "prov-api"
PROV_UI_DEFAULT_DOMAIN = "prov"
PROV_NEO4J_HTTP_DEFAULT_DOMAIN = "prov-db"
PROV_NEO4J_BOLT_DEFAULT_DOMAIN = "prov-db-bolt"

INTEGRATION_TEST_KEYCLOAK_CLIENT_ID = "integration-tests"

# This is the deployed gbrrestoration base documentation URL
# update to use Provena
# TODO PROVENA UPDATE
DEFAULT_DOCUMENTATION_BASE_URL = "https://gbrrestoration.github.io/rrap-mds-knowledge-hub"

# Compute and other config
# ===============================================
SMALL_NEO4J_CPU_SIZE = 1024
SMALL_NEO4J_MEM_SIZE = 4096
KEYCLOAK_DEFAULT_THEME_NAME = "default"
UI_DEFAULT_THEME_ID = "default"
