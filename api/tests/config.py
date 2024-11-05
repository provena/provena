from ProvenaInterfaces.RegistryAPI import *
from ProvenaInterfaces.ProvenanceModels import *
from ProvenaSharedFunctionality.Registry.RegistryRouteActions import RouteActions
from dataclasses import dataclass
from ProvenaInterfaces.SharedTypes import ImportMode
from typing import List

test_resource_table_name = "testregistryresource"
test_lock_table_name = "testregistrylock"
test_auth_table_name = "testregistryauth"

NUM_FAKE_ENTRIES = 100  # Implement batch put for very large writing
test_email = "testuser@gmail.com"
test_username = test_email
test_stage = "TEST"
admin_import_endpoint = "/registry/admin/import"
admin_export_endpoint = "/registry/admin/export"
admin_restore_endpoint = "/registry/admin/restore_from_table"

# Type vars, dataclasses, route params have been moved into provena shared functionality package

# tests are pararmetrised for all endpoints,
# not all entities implement all endpoints (actions)
# any tests that attempt to perform an action on an entity that
# does not support that action should be skipped
to_skip: set[Tuple[ItemSubType, RouteActions]] = {
    (ItemSubType.CREATE, RouteActions.CREATE),
    (ItemSubType.CREATE, RouteActions.UPDATE),
    (ItemSubType.CREATE, RouteActions.SEED),
}

default_user_count = 3
test_access_request_table_name = "test_table_requests"
test_user_group_table_name = "test_table_users"
test_email = "testuser@gmail.com"
test_stage = "TEST"
admin_import_endpoint = "/groups/admin/import"
admin_export_endpoint = "/groups/admin/export"
admin_restore_endpoint = "/groups/admin/restore_from_table"
group_admin_prefix = "/groups/admin"
group_user_prefix = "/groups/user"
link_table_name = "linktable"
link_gsi_name = "linktablegsi"

# link endpoints
link_prefix = "link"
user_prefix = "user"
admin_prefix = "admin"

lookup_action = "lookup"
assign_action = "assign"
clear_action = "clear"
reverse_action = "reverse_lookup"

user_lookup = f"/{link_prefix}/{user_prefix}/{lookup_action}"
user_assign = f"/{link_prefix}/{user_prefix}/{assign_action}"

admin_lookup = f"/{link_prefix}/{admin_prefix}/{lookup_action}"
admin_assign = f"/{link_prefix}/{admin_prefix}/{assign_action}"
admin_clear = f"/{link_prefix}/{admin_prefix}/{clear_action}"
admin_reverse_lookup = f"/{link_prefix}/{admin_prefix}/{reverse_action}"


@dataclass
class GroupAdminEndpoints():
    LIST_GROUPS = group_admin_prefix + '/list_groups'
    DESCRIBE_GROUP = group_admin_prefix + '/describe_group'
    LIST_MEMBERS = group_admin_prefix + '/list_members'
    LIST_USER_MEMBERSHIP = group_admin_prefix + '/list_user_membership'
    CHECK_MEMBERSHIP = group_admin_prefix + '/check_membership'
    ADD_MEMBER = group_admin_prefix + '/add_member'
    REMOVE_MEMBER = group_admin_prefix + '/remove_member'
    REMOVE_MEMBERS = group_admin_prefix + '/remove_members'
    ADD_GROUP = group_admin_prefix + '/add_group'
    REMOVE_GROUP = group_admin_prefix + '/remove_group'
    UPDATE_GROUP = group_admin_prefix + '/update_group'


@dataclass
class GroupUserEndpoints():
    LIST_GROUPS = group_user_prefix + '/list_groups'
    DESCRIBE_GROUP = group_user_prefix + '/describe_group'
    LIST_MEMBERS = group_user_prefix + '/list_members'
    LIST_USER_MEMBERSHIP = group_user_prefix + '/list_user_membership'
    CHECK_MEMBERSHIP = group_user_prefix + '/check_membership'


group_admin_endpoints = GroupAdminEndpoints()
group_user_endpoints = GroupUserEndpoints()

# Create parameter set for import mode. Used for testing trial mode features
# against each import mode.
import_modes: List[ImportMode] = list(ImportMode)
