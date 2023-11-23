from SharedInterfaces.AuthAPI import AccessLevel, HANDLE_SERVICE_COMPONENT
from KeycloakFastAPI.Dependencies import User, build_keycloak_auth, build_test_keycloak_auth
from config import base_config
from helpers.keycloak_helpers import setup_secret_cache

# Setup auth -> test mode means no sig enforcement on validation
kc_auth = build_keycloak_auth(
    keycloak_endpoint=base_config.keycloak_endpoint) if not base_config.test_mode else build_test_keycloak_auth()

# Create dependencies
# This is from the shared authorisation model
read_usage_role = HANDLE_SERVICE_COMPONENT.get_role_at_level(
    AccessLevel.READ).role_name
write_usage_role = HANDLE_SERVICE_COMPONENT.get_role_at_level(
    AccessLevel.WRITE).role_name
admin_usage_role = HANDLE_SERVICE_COMPONENT.get_role_at_level(
    AccessLevel.ADMIN).role_name

user_general_dependency = kc_auth.get_user_dependency()
read_user_protected_role_dependency = kc_auth.get_all_protected_role_dependency(
    [read_usage_role]
)
read_write_user_protected_role_dependency = kc_auth.get_all_protected_role_dependency(
    [read_usage_role, write_usage_role]
)
admin_user_protected_role_dependency = kc_auth.get_all_protected_role_dependency(
    [read_usage_role, write_usage_role, admin_usage_role]
)

secret_cache = setup_secret_cache()
