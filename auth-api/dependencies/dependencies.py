
from KeycloakFastAPI.Dependencies import User, build_keycloak_auth, build_test_keycloak_auth
from SharedInterfaces.AuthAPI import *
from config import base_config

# Setup auth -> test mode means no sig enforcement on validation
kc_auth = build_keycloak_auth(
    keycloak_endpoint=base_config.keycloak_endpoint) if not base_config.test_mode else build_test_keycloak_auth()

# Create dependencies
user_general_dependency = kc_auth.get_user_dependency()

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
