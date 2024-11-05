from ProvenaInterfaces.AuthAPI import ENTITY_REGISTRY_COMPONENT, AccessLevel, SYS_ADMIN_COMPONENT
from KeycloakFastAPI.Dependencies import User, build_keycloak_auth, build_test_keycloak_auth
from config import base_config
from helpers.registry.keycloak_helpers import setup_secret_cache

# Setup auth -> test mode means no sig enforcement on validation
kc_auth = build_keycloak_auth(
    keycloak_endpoint=base_config.keycloak_endpoint) if not base_config.test_mode else build_test_keycloak_auth()

# Create dependencies
# This is from the shared authorisation model
registry_read_role = ENTITY_REGISTRY_COMPONENT.get_role_at_level(
    AccessLevel.READ).role_name
registry_write_role = ENTITY_REGISTRY_COMPONENT.get_role_at_level(
    AccessLevel.WRITE).role_name
registry_admin_role = ENTITY_REGISTRY_COMPONENT.get_role_at_level(
    AccessLevel.ADMIN).role_name

user_general_dependency = kc_auth.get_user_dependency()
read_user_protected_role_dependency = kc_auth.get_all_protected_role_dependency(
    [registry_read_role]
)
read_write_user_protected_role_dependency = kc_auth.get_all_protected_role_dependency(
    [registry_read_role, registry_write_role]
)
admin_user_protected_role_dependency = kc_auth.get_all_protected_role_dependency(
    [registry_read_role, registry_write_role, registry_admin_role]
)

# Required role for sys admin read and write
sys_admin_admin_role = SYS_ADMIN_COMPONENT.get_role_at_level(
    AccessLevel.ADMIN).role_name
sys_admin_write_role = SYS_ADMIN_COMPONENT.get_role_at_level(
    AccessLevel.WRITE).role_name
sys_admin_read_role = SYS_ADMIN_COMPONENT.get_role_at_level(
    AccessLevel.READ).role_name

# Setup auth dependencies
sys_admin_write_dependency = kc_auth.get_all_protected_role_dependency([
                                                                       sys_admin_write_role])
sys_admin_read_dependency = kc_auth.get_all_protected_role_dependency([
                                                                      sys_admin_read_role])
sys_admin_admin_dependency = kc_auth.get_all_protected_role_dependency([
                                                                       sys_admin_admin_role])


secret_cache = setup_secret_cache()


def user_is_admin(user: User) -> bool:
    """
    
    Determines if the user is an admin based on inclusion of the admin usage
    role, defined above

    Parameters
    ----------
    user : User
        The user with roles parsed

    Returns
    -------
    bool
        True iff is admin
    """    
    return registry_admin_role in user.roles
