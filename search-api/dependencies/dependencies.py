from ProvenaInterfaces.AuthAPI import SYS_ADMIN_COMPONENT, AccessLevel, ENTITY_REGISTRY_COMPONENT
from KeycloakFastAPI.Dependencies import User, build_keycloak_auth, build_test_keycloak_auth
from config import base_config
from helpers.keycloak_helpers import setup_secret_cache

# Setup auth -> test mode means no sig enforcement on validation
kc_auth = build_keycloak_auth(
    keycloak_endpoint=base_config.keycloak_endpoint) if not base_config.test_mode else build_test_keycloak_auth()

# Create dependencies
# This is from the shared authorisation model

# Search
sys_admin_read_usage_role = SYS_ADMIN_COMPONENT.get_role_at_level(
    AccessLevel.READ).role_name
sys_admin_write_usage_role = SYS_ADMIN_COMPONENT.get_role_at_level(
    AccessLevel.WRITE).role_name
sys_admin_admin_usage_role = SYS_ADMIN_COMPONENT.get_role_at_level(
    AccessLevel.ADMIN).role_name

# Registry
registry_read_usage_role = ENTITY_REGISTRY_COMPONENT.get_role_at_level(
    AccessLevel.READ).role_name
registry_write_usage_role = ENTITY_REGISTRY_COMPONENT.get_role_at_level(
    AccessLevel.WRITE).role_name
registry_admin_usage_role = ENTITY_REGISTRY_COMPONENT.get_role_at_level(
    AccessLevel.ADMIN).role_name

user_general_dependency = kc_auth.get_user_dependency()

# Searching entity registry
search_entity_registry_protected_role_dependency = kc_auth.get_all_protected_role_dependency(
    [registry_read_usage_role]
)

# Searching global alias index
search_global_protected_role_dependency = kc_auth.get_all_protected_role_dependency(
    [registry_read_usage_role]
)


# other search API roles
sys_admin_read_user_protected_role_dependency = kc_auth.get_all_protected_role_dependency(
    [sys_admin_read_usage_role]
)
sys_admin_read_write_user_protected_role_dependency = kc_auth.get_all_protected_role_dependency(
    [sys_admin_read_usage_role, sys_admin_write_usage_role]
)
sys_admin_admin_user_protected_role_dependency = kc_auth.get_all_protected_role_dependency(
    [sys_admin_read_usage_role, sys_admin_write_usage_role, sys_admin_admin_usage_role]
)

secret_cache = setup_secret_cache()
