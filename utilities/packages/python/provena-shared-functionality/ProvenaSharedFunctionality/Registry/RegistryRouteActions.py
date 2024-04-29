from enum import Enum
from typing import List, Dict, Optional
from ProvenaInterfaces.RegistryModels import Roles
from dataclasses import dataclass
# moving service role names into here
# from dependencies.dependencies import PROV_SERVICE_ROLE_NAME, DATA_STORE_SERVICE_ROLE_NAME

DATA_STORE_SERVICE_ROLE_NAME = "data-store-api"
PROV_SERVICE_ROLE_NAME = "prov-api"


class RouteAccessLevel(str, Enum):
    READ = "READ"
    WRITE = "WRITE"
    ADMIN = "ADMIN"


class RouteMethod(str, Enum):
    GET = "GET"
    PUT = "PUT"
    POST = "POST"
    DELETE = "DELETE"


@dataclass
class RouteActionConfig():
    path: str
    method: RouteMethod

    op_id: str
    access_level: RouteAccessLevel
    hide: bool = False
    # all routes with this action type will have these special limited access
    # roles enforced
    limited_access_roles: Optional[Roles] = None

    # Should this endpoint require that the user (direct or proxied) have a
    # linked Person in the Registry? The route config instantiated can still
    # enable/disable this on a per type basis - this is for the action
    enforce_linked_owner: bool = False


class RouteActions(str, Enum):
    FETCH = "FETCH"
    LIST = "LIST"
    SEED = "SEED"
    UPDATE = "UPDATE"
    CREATE = "CREATE"
    REVERT = "REVERT"
    SCHEMA = "SCHEMA"
    UI_SCHEMA = "UI_SCHEMA"
    VALIDATE = "VALIDATE"
    AUTH_EVALUATE = "AUTH_EVALUATE"
    AUTH_CONFIGURATION_GET = "AUTH_CONFIGURATION_GET"
    AUTH_CONFIGURATION_PUT = "AUTH_CONFIGURATION_PUT"
    AUTH_ROLES = "AUTH_ROLES"
    DELETE = "DELETE"

    # Versioning only
    VERSION = "VERSION"

    # Lock management
    LOCK = "LOCK"
    UNLOCK = "UNLOCK"
    LOCK_HISTORY = "LOCK_HISTORY"
    LOCKED = "LOCKED"

    # These are special proxy routes which enable the username to be specified -
    # need to be protected by special role protections - currently only used for
    # datasets through the data store API
    PROXY_SEED = "PROXY_SEED"
    PROXY_CREATE = "PROXY_CREATE"
    PROXY_UPDATE = "PROXY_UPDATE"
    PROXY_REVERT = "PROXY_REVERT"
    # Versioning only
    PROXY_VERSION = "PROXY_VERSION"

    # Proxy fetch is only accessible via either prov/data store service accounts
    # and accepts a username to use for checking authorisation
    PROXY_FETCH = "PROXY_FETCH"


STANDARD_ROUTE_ACTIONS: List[RouteActions] = [
    RouteActions.SEED,
    RouteActions.UPDATE,
    RouteActions.CREATE,
    RouteActions.REVERT,
    RouteActions.DELETE,
    RouteActions.FETCH,
    # all item types may need to be proxy fetched
    RouteActions.PROXY_FETCH,
    RouteActions.LIST,
    RouteActions.SCHEMA,
    RouteActions.UI_SCHEMA,
    RouteActions.VALIDATE,
    RouteActions.AUTH_EVALUATE,
    RouteActions.AUTH_CONFIGURATION_GET,
    RouteActions.AUTH_CONFIGURATION_PUT,
    RouteActions.AUTH_ROLES,
    RouteActions.LOCK,
    RouteActions.UNLOCK,
    RouteActions.LOCK_HISTORY,
    RouteActions.LOCKED,
]

STANDARD_PROVENANCE_VERSIONING_ROUTE_ACTIONS: List[RouteActions] = [
    RouteActions.VERSION
]

PROXY_PROVENANCE_VERSIONING_ROUTE_ACTIONS: List[RouteActions] = [
    RouteActions.PROXY_VERSION
]

READ_ONLY_ROUTE_ACTIONS: List[RouteActions] = [
    # Remove all create/update actions
    # RouteActions.SEED,
    # RouteActions.UPDATE,
    # RouteActions.CREATE,
    # RouteActions.REVERT,

    # ADMIN only delete still used
    RouteActions.DELETE,

    # All fetch list etc still usable
    RouteActions.FETCH,
    RouteActions.PROXY_FETCH,
    RouteActions.LIST,
    RouteActions.SCHEMA,
    RouteActions.UI_SCHEMA,
    RouteActions.VALIDATE,
    RouteActions.AUTH_EVALUATE,
    RouteActions.AUTH_CONFIGURATION_GET,
    RouteActions.AUTH_CONFIGURATION_PUT,
    RouteActions.AUTH_ROLES,

    # Lock actions still okay
    RouteActions.LOCK,
    RouteActions.UNLOCK,
    RouteActions.LOCK_HISTORY,
    RouteActions.LOCKED,
]

SERVICE_PROXY_ROUTE_ACTIONS: List[RouteActions] = [
    # uses proxy instead of standard edit routes
    RouteActions.PROXY_SEED,
    RouteActions.PROXY_CREATE,
    RouteActions.PROXY_UPDATE,
    RouteActions.PROXY_REVERT,

    RouteActions.DELETE,
    RouteActions.FETCH,
    RouteActions.PROXY_FETCH,
    RouteActions.LIST,
    RouteActions.SCHEMA,
    RouteActions.UI_SCHEMA,
    RouteActions.VALIDATE,
    RouteActions.AUTH_EVALUATE,
    RouteActions.AUTH_CONFIGURATION_GET,
    RouteActions.AUTH_CONFIGURATION_PUT,
    RouteActions.AUTH_ROLES,
    RouteActions.LOCK,
    RouteActions.UNLOCK,
    RouteActions.LOCK_HISTORY,
    RouteActions.LOCKED,
]

# Datasets have proxy actions + provenance versioning enabled through proxy
DATASET_ROUTE_ACTIONS = SERVICE_PROXY_ROUTE_ACTIONS + \
    PROXY_PROVENANCE_VERSIONING_ROUTE_ACTIONS
MODEL_RUN_ROUTE_ACTIONS = SERVICE_PROXY_ROUTE_ACTIONS

EDIT_ROUTE_ACTIONS: List[RouteActions] = [
    # these are modifying actions on the item
    RouteActions.SEED,
    RouteActions.UPDATE,
    RouteActions.CREATE,
    RouteActions.DELETE,
    RouteActions.REVERT
]

PROXY_EDIT_ROUTE_ACTIONS: List[RouteActions] = [
    # these are modifying actions on the item
    RouteActions.PROXY_SEED,
    RouteActions.PROXY_CREATE,
    RouteActions.PROXY_VERSION,
    RouteActions.PROXY_UPDATE,
    RouteActions.PROXY_REVERT
]

# only prov/data store APIs can use the proxy fetch route
PROXY_FETCH_LIMITED_ACCESS_ROLES: Roles = [
    PROV_SERVICE_ROLE_NAME, DATA_STORE_SERVICE_ROLE_NAME]

ROUTE_ACTION_CONFIG_MAP: Dict[RouteActions, RouteActionConfig] = {
    # Primary actions
    RouteActions.FETCH: RouteActionConfig(
        method=RouteMethod.GET,
        access_level=RouteAccessLevel.READ,
        path="/fetch",
        op_id="fetch_"
    ),
    RouteActions.LIST: RouteActionConfig(
        # this method is a post for request library compat with complex payload
        method=RouteMethod.POST,
        access_level=RouteAccessLevel.READ,
        path="/list",
        op_id="list_"
    ),
    RouteActions.SEED: RouteActionConfig(
        method=RouteMethod.POST,
        access_level=RouteAccessLevel.WRITE,
        path="/seed",
        op_id="seed_",
        enforce_linked_owner=True
    ),
    RouteActions.UPDATE: RouteActionConfig(
        method=RouteMethod.PUT,
        access_level=RouteAccessLevel.WRITE,
        path="/update",
        op_id="update_",
        enforce_linked_owner=True
    ),
    RouteActions.REVERT: RouteActionConfig(
        method=RouteMethod.PUT,
        access_level=RouteAccessLevel.WRITE,
        path="/revert",
        op_id="revert_",
        enforce_linked_owner=True
    ),
    RouteActions.CREATE: RouteActionConfig(
        method=RouteMethod.POST,
        access_level=RouteAccessLevel.WRITE,
        path="/create",
        op_id="create_",
        enforce_linked_owner=True
    ),
    RouteActions.VERSION: RouteActionConfig(
        method=RouteMethod.POST,
        # Need to be write generally, but admin on item to revise an item
        access_level=RouteAccessLevel.WRITE,
        path="/version",
        op_id="version_",
        enforce_linked_owner=True
    ),
    RouteActions.SCHEMA: RouteActionConfig(
        method=RouteMethod.GET,
        access_level=RouteAccessLevel.READ,
        path="/schema",
        op_id="schema_"
    ),
    RouteActions.UI_SCHEMA: RouteActionConfig(
        method=RouteMethod.GET,
        access_level=RouteAccessLevel.READ,
        path="/ui_schema",
        op_id="ui_schema_"
    ),
    RouteActions.VALIDATE: RouteActionConfig(
        method=RouteMethod.POST,
        access_level=RouteAccessLevel.READ,
        path="/validate",
        op_id="validate_"
    ),
    RouteActions.DELETE: RouteActionConfig(
        method=RouteMethod.DELETE,
        access_level=RouteAccessLevel.ADMIN,
        path="/delete",
        op_id="delete_",
        hide=True
    ),

    # Auth actions
    RouteActions.AUTH_EVALUATE: RouteActionConfig(
        method=RouteMethod.GET,
        access_level=RouteAccessLevel.READ,
        path="/auth/evaluate",
        op_id="auth_evaluate_"
    ),
    RouteActions.AUTH_CONFIGURATION_GET: RouteActionConfig(
        method=RouteMethod.GET,
        access_level=RouteAccessLevel.READ,
        path="/auth/configuration",
        op_id="auth_configuration_get_"
    ),
    RouteActions.AUTH_CONFIGURATION_PUT: RouteActionConfig(
        method=RouteMethod.PUT,
        access_level=RouteAccessLevel.WRITE,
        path="/auth/configuration",
        op_id="auth_configuration_put_"
    ),
    RouteActions.AUTH_ROLES: RouteActionConfig(
        method=RouteMethod.GET,
        access_level=RouteAccessLevel.READ,
        path="/auth/roles",
        op_id="auth_roles_"
    ),

    # Proxy actions - these are hidden to the user so that they know to use the
    # prov/data store API instead to manage creation/updates of these entities
    RouteActions.PROXY_SEED: RouteActionConfig(
        method=RouteMethod.POST,
        access_level=RouteAccessLevel.WRITE,
        path="/proxy/seed",
        op_id="proxy_seed_",
        hide=True,
        enforce_linked_owner=True
    ),
    RouteActions.PROXY_CREATE: RouteActionConfig(
        method=RouteMethod.POST,
        access_level=RouteAccessLevel.WRITE,
        path="/proxy/create",
        op_id="proxy_create_",
        hide=True,
        enforce_linked_owner=True
    ),
    RouteActions.PROXY_VERSION: RouteActionConfig(
        method=RouteMethod.POST,
        access_level=RouteAccessLevel.WRITE,
        path="/proxy/version",
        op_id="proxy_version_",
        hide=True,
        enforce_linked_owner=True
    ),
    RouteActions.PROXY_UPDATE: RouteActionConfig(
        method=RouteMethod.PUT,
        access_level=RouteAccessLevel.WRITE,
        path="/proxy/update",
        op_id="proxy_update_",
        hide=True,
        enforce_linked_owner=True
    ),
    RouteActions.PROXY_REVERT: RouteActionConfig(
        method=RouteMethod.PUT,
        access_level=RouteAccessLevel.WRITE,
        path="/proxy/revert",
        op_id="proxy_revert_",
        hide=True,
        enforce_linked_owner=True
    ),
    RouteActions.PROXY_FETCH: RouteActionConfig(
        method=RouteMethod.GET,
        access_level=RouteAccessLevel.READ,
        path="/proxy/fetch",
        op_id="proxy_fetch_",
        hide=True,
        limited_access_roles=PROXY_FETCH_LIMITED_ACCESS_ROLES
    ),

    # Lock actions
    RouteActions.LOCK: RouteActionConfig(
        method=RouteMethod.PUT,
        access_level=RouteAccessLevel.WRITE,
        path="/locks/lock",
        op_id="lock_lock"
    ),
    RouteActions.UNLOCK: RouteActionConfig(
        method=RouteMethod.PUT,
        access_level=RouteAccessLevel.WRITE,
        path="/locks/unlock",
        op_id="lock_unlock"
    ),
    RouteActions.LOCK_HISTORY: RouteActionConfig(
        method=RouteMethod.GET,
        access_level=RouteAccessLevel.READ,
        path="/locks/history",
        op_id="lock_history"
    ),
    RouteActions.LOCKED: RouteActionConfig(
        method=RouteMethod.GET,
        access_level=RouteAccessLevel.READ,
        path="/locks/locked",
        op_id="lock_locked"
    ),
}

for route_action in RouteActions:
    assert route_action in ROUTE_ACTION_CONFIG_MAP.keys()
