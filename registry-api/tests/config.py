from SharedInterfaces.RegistryAPI import *
from SharedInterfaces.ProvenanceModels import *

test_resource_table_name = "testregistryresource"
test_lock_table_name = "testregistrylock"
test_auth_table_name = "testregistryauth"

NUM_FAKE_ENTRIES = 100  # Implement batch put for very large writing
test_email = "testuser@gmail.com"
test_username = test_email
test_stage = "TEST"
admin_import_endpoint = "/admin/import"
admin_export_endpoint = "/admin/export"
admin_restore_endpoint = "/admin/restore_from_table"

# Type vars, dataclasses, route params have been moved into registry shared functionality package
