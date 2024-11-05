from ProvenaInterfaces.RegistryAPI import *
from ProvenaInterfaces.ProvenanceModels import *
from ProvenaSharedFunctionality.Registry.RegistryRouteActions import RouteActions

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
