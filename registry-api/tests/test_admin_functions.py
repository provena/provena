import tests.env_setup
from tests.config import *
import os
import pytest  # type: ignore
import boto3  # type: ignore
from moto import mock_dynamodb  # type: ignore
from KeycloakFastAPI.Dependencies import User, ProtectedRole
from dependencies.dependencies import read_user_protected_role_dependency, read_write_user_protected_role_dependency, admin_user_protected_role_dependency, get_user_context
from fastapi.testclient import TestClient
from tests.helpers import put_context_mock
from main import app, route_configs, ITEM_CATEGORY_ROUTE_MAP
from config import Config, base_config, get_settings
from typing import Generator, Any, Dict
from tests.helpers import *
from random import sample
import json

client = TestClient(app)

# Setup pytest paramterisation for per route functions
for r_config in route_configs:
    if (r_config.desired_subtype not in route_config_exclusions):
        # Get the prefix
        prefix = f"/{ITEM_CATEGORY_ROUTE_MAP[r_config.desired_category]}/{ITEM_SUB_TYPE_ROUTE_MAP[r_config.desired_subtype]}"

        found = False
        for rp in route_params:
            if rp.route == prefix:
                found = True
                break

        assert found, f"Couldn't find the route {prefix} in the test route params!"

id_base_list = [params.name for params in route_params]

# provides a test wide config scope


def global_config_provider() -> Config:
    return Config(
        # no user auth testing!
        enforce_user_auth=False,
        enforce_special_proxy_roles=False,
        auth_api_endpoint="",
        job_api_endpoint="",

        keycloak_endpoint=base_config.keycloak_endpoint,
        stage=base_config.stage,
        registry_table_name=test_resource_table_name,
        auth_table_name=test_resource_table_name,
        lock_table_name=test_resource_table_name,
        handle_api_endpoint="",
        service_account_secret_arn="",
        mock_handle=True,
        # mocking validation to always succeed and then testing validation separately.
        perform_validation=False,
        # dont perform user link validation
        enforce_user_links=False,
        test_mode=True
    )


@pytest.fixture(scope="session", autouse=True)
def provide_global_config() -> Config:
    return global_config_provider()

# for each function, override settings and clear deps at end


@pytest.fixture(scope="function", autouse=True)
def override_config_dependency(provide_global_config: Config) -> Generator:
    app.dependency_overrides[get_settings] = lambda: provide_global_config
    yield
    app.dependency_overrides = {}

# ensure that fake creds are used to double check no real interactions with aws
# resources

@pytest.fixture(scope="function", autouse=True)
def override_context_dependency() -> Generator:
    put_context_mock(app, username=test_email, roles=['test-role'], access_token="faketoken1234", email=test_email)
    yield
    app.dependency_overrides = {}

@pytest.fixture(scope='function')
def aws_credentials() -> None:
    """Mocked AWS Credentials for moto."""
    os.environ['AWS_ACCESS_KEY_ID'] = 'testing'
    os.environ['AWS_SECRET_ACCESS_KEY'] = 'testing'
    os.environ['AWS_SECURITY_TOKEN'] = 'testing'
    os.environ['AWS_SESSION_TOKEN'] = 'testing'
    os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'


async def user_general_dependency_override() -> User:
    # Creates an override for user dependency
    return User(username=test_email, roles=['test-role'], access_token="faketoken1234", email=test_email)


async def user_protected_dependency_override() -> ProtectedRole:
    # Creates override for the role protected user dependency
    return ProtectedRole(
        access_roles=['test-role'],
        user=User(
            username=test_email,
            roles=['test-role'],
            access_token="faketoken1234",
            email=test_email
        )
    )


def test_health_check() -> None:
    # Checks that the health check endpoint responds
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Health check successful."}


def test_authorized() -> None:
    # Override the auth dependency
    app.dependency_overrides[read_user_protected_role_dependency] = user_protected_dependency_override
    response = client.get("/check-access/check-read-access")
    assert response.status_code == 200


def activate_registry_table_set(names: TestTableNames) -> None:
    """
    Updates the dependency overrides for the app object by using the global
    config object then overriding the registry table name.

    Parameters
    ----------
    names: TestTableNames
        The set of tables to activate
    """
    def config_override() -> Config:
        global_config = global_config_provider()

        # override all of the tables
        global_config.registry_table_name = names.resource_table_name
        global_config.auth_table_name = names.auth_table_name
        global_config.lock_table_name = names.lock_table_name
        return global_config
    app.dependency_overrides[get_settings] = config_override


def activate_registry_table(name: str) -> None:
    """
    Updates the dependency overrides for the app object by using the global
    config object then overriding the registry table name.

    Parameters
    ----------
    name: str
        The base name of table set to activate
    """
    activate_registry_table_set(
        names=table_names_from_base(name)
    )


def setup_tables(table_definitions: Dict[str, int], table_context: str, create_tables: bool = True) -> Dict[str, Dict[str, TypedItemBundle]]:
    """
    Helper function to assist with setting up tables with items.

    You specify a dictionary of base table names -> number of items to populate the
    table with.

    You also specify which table context you would like active when the function
    finishes. 

    The create_tables can be switched off if you have already created the
    dynamodb tables in the current mocked environment and just want items in
    them.

    Returns a map of table name -> (map of item id -> ItemBase) i.e. a set of
    items created randomly for each table.

    Parameters
    ----------
    table_definitions : Dict[str, int]
        A map from base table name -> number of items to add to the table
    table_context : str
        Which table base name do you want active when this function finishes?
    create_tables : bool, optional
        Should the tables be created using dynamodb mock - turn off if you have
        already created them, by default True

    Returns
    -------
    Dict[str, Dict[str, ItemBase]]
        Map of table name -> (map of item id -> ItemBase) i.e. a set of items
        created randomly for each table.

    """
    # setup table items and client
    table_items: Dict[str, Dict[str, TypedItemBundle]] = {}

    # create tables if required
    if create_tables:
        create_dynamo_tables(list(table_definitions.keys()))

    # for each table definition, optionally create the table
    # and populate items, collecting as we go
    for table_name, table_item_count in table_definitions.items():
        activate_registry_table(table_name)
        returned_items = write_n_items_to_registry(client, table_item_count)
        table_items[table_name] = returned_items

    # return the context to specified table
    activate_registry_table(table_context)

    # return a map from table name -> items
    return table_items


@mock_dynamodb
def test_restore_inappropriate_table() -> None:
    """
    Tests that the API correctly responds with a status failure if the provided
    table_name to a restore operation is the current registry table.
    """
    app.dependency_overrides[read_user_protected_role_dependency] = user_protected_dependency_override
    app.dependency_overrides[read_write_user_protected_role_dependency] = user_protected_dependency_override
    app.dependency_overrides[admin_user_protected_role_dependency] = user_protected_dependency_override

    # Setup demo tables
    main_table_name = "testTable"
    aux_table_name = "secondTestTable"
    table_items = setup_tables(
        {main_table_name: 1, aux_table_name: 1}, main_table_name)

    # pull out the items
    main_table_items = bundled_item_dict_to_import_format(
        table_items[main_table_name])
    aux_table_items = bundled_item_dict_to_import_format(
        table_items[aux_table_name])

    # try restoring from the main table -> main table
    names = import_names_from_base_name(main_table_name)

    restore_request = RegistryRestoreRequest(
        import_mode=ImportMode.ADD_OR_OVERWRITE,
        parse_items=True,
        allow_entry_deletion=False,
        trial_mode=False,
        table_names=names
    )
    restore_response = client.post(
        admin_restore_endpoint, json=py_to_dict(restore_request))

    # check that restore with incorrect name fails
    check_status_success_false(restore_response)

    # check that no state was changed
    assert_registry_state(client, main_table_items)

    # try restoring from the aux table -> main table

    # try restoring from the aux table -> main table
    names = import_names_from_base_name(aux_table_name)
    restore_request = RegistryRestoreRequest(
        import_mode=ImportMode.ADD_ONLY,
        parse_items=True,
        allow_entry_deletion=False,
        trial_mode=False,
        table_names=names
    )
    restore_response = client.post(
        admin_restore_endpoint, json=py_to_dict(restore_request))

    # check that restore with correct name succeeds
    check_status_success_true(restore_response)

    # check that state is result of addition of main and aux table
    assert_registry_state(client, main_table_items + aux_table_items)


@mock_dynamodb
def test_admin_export() -> None:
    """
    Tests that the admin export feature correctly dumps all items from a table
    backend.

    NOTE the admin test helper functions implicitly rely on export working
    properly - this test does not use these helper functions for export, and
    test it more rigorously.

    Failure conditions to test

    No meaningful failure conditions for this test. There is no payload and even
    an empty table should work.

    Successful tests

    a) Export from empty table and make sure it works

    b) Produce some new items and make sure export contains all items
    """
    app.dependency_overrides[read_user_protected_role_dependency] = user_protected_dependency_override
    app.dependency_overrides[read_write_user_protected_role_dependency] = user_protected_dependency_override
    app.dependency_overrides[admin_user_protected_role_dependency] = user_protected_dependency_override
    
    

    # Successful conditions

    # A + B
    # setup a table set for export test
    table_name = "exportTable"
    create_dynamo_tables([table_name])
    activate_registry_table(table_name)

    # make sure that export works with empty table
    response = client.get(admin_export_endpoint)

    # make sure it succeeded
    check_status_success_true(response)

    # now get the response
    export_response = RegistryExportResponse.parse_obj(response.json())
    items = export_response.items
    assert items is not None, "Items should not be none even if registry is empty"
    assert len(items) == 0, "Empty registry had non empty items list"

    # now add some items
    num_items = 20

    # keep track of a map of id -> item
    item_map = write_n_items_to_registry(client, num_items)

    # export the items
    response = client.get(admin_export_endpoint)
    export_response = RegistryExportResponse.parse_obj(response.json())
    items = export_response.items
    assert items, "Items should not be none for non empty registry"
    assert len(items) == len(item_map), "Incorrect number of items exported"

    # check that all items are present
    returned_item_map: Dict[str, BundledItem] = {}
    for returned_item in items:
        returned_id = returned_item.id
        if returned_id in returned_item_map:
            assert False, f"Duplicate items returned from the export: {returned_id}."
        returned_item_map[returned_id] = returned_item

    returned_set = set(returned_item_map.keys())
    export_set = set(item_map.keys())
    assert returned_set == export_set

    # check that items are equal/valid
    for export_id, export_item in item_map.items():
        returned_item = returned_item_map[export_id]
        returned_record_info = RecordInfo.parse_obj(returned_item.item_payload)
        category_subtype = (returned_record_info.item_category,
                            returned_record_info.item_subtype)
        correct_model_type = MODEL_TYPE_MAP[category_subtype]
        parsed_returned_record = correct_model_type.parse_obj(
            returned_item.item_payload)
        parsed_export_record = correct_model_type.parse_obj(
            export_item.item_payload.dict())
        assert parsed_returned_record == parsed_export_record


@mock_dynamodb
def test_admin_no_universal_key() -> None:
    """
    Test that if no universal partition key is present in the import items, it
    is properly added. We can tell it is added by the item being present in the
    general query.

    """
    app.dependency_overrides[read_user_protected_role_dependency] = user_protected_dependency_override
    app.dependency_overrides[read_write_user_protected_role_dependency] = user_protected_dependency_override
    app.dependency_overrides[admin_user_protected_role_dependency] = user_protected_dependency_override

    # setup import mode for reuse
    import_mode = ImportMode.ADD_ONLY

    # =========
    # Failure A
    # =========

    # setup table with an item in it
    main_table_name = "mainTable"
    secondary_table_name = "secondaryTable"
    table_items = setup_tables(
        {main_table_name: 0, secondary_table_name: 1}, main_table_name)

    # get the item
    item = list(table_items[secondary_table_name].values())[0]
    item_dict = item.dict()

    # remove the universal partition key
    try:
        del item_dict['item_payload']['universal_partition_key']
    except:
        pass

    # import into empty main table
    import_payload = RegistryImportRequest(
        import_mode=import_mode,
        parse_items=True,
        allow_entry_deletion=False,
        trial_mode=False,
        items=[item_dict]
    )

    # try importing
    import_response = client.post(
        admin_import_endpoint, json=py_to_dict(import_payload))

    # make sure response suceeds
    check_status_success_true(import_response)

    # now run a general untyped query and ensure the item is present

    # get all items from the general list endpoint
    items = general_list_exhaust(client)

    # should be one items
    assert len(items) == 1


@mock_dynamodb
def test_admin_import_add_only() -> None:
    """
    Part of a series of import tests which tests functionality in various import
    modes. This is the ADD_ONLY mode.

    Failure conditions to test
    a) Trying to import items which already exist in the table

    Successful tests
    a) Import new item into empty table - make sure it exists after being added
    b) Import new item into table with existing entries - make sure it exists after being added
    """
    app.dependency_overrides[read_user_protected_role_dependency] = user_protected_dependency_override
    app.dependency_overrides[read_write_user_protected_role_dependency] = user_protected_dependency_override
    app.dependency_overrides[admin_user_protected_role_dependency] = user_protected_dependency_override

    # setup import mode for reuse
    import_mode = ImportMode.ADD_ONLY

    # =========
    # Failure A
    # =========

    # setup table with an item in it
    table_name = "failureTable"
    table_items = setup_tables({table_name: 1}, table_name)

    # get the item
    item = list(table_items[table_name].values())[0]
    item_dict = item.dict()

    import_payload = RegistryImportRequest(
        import_mode=import_mode,
        parse_items=True,
        allow_entry_deletion=False,
        trial_mode=False,
        items=[item_dict]
    )

    # try importing with existing item
    import_response = client.post(
        admin_import_endpoint, json=py_to_dict(import_payload))

    # make sure response fails
    check_status_success_false(import_response)

    # ==============
    # Success A + B
    # ==============

    # create tables
    table_from = "table1"
    table_to = "table2"
    definition = {table_from: 1, table_to: 0}
    items = setup_tables(definition, table_to, True)
    # get item from first table
    item = list(items[table_from].values())[0]

    # add item to table 2 through import
    import_payload = RegistryImportRequest(
        import_mode=import_mode,
        parse_items=True,
        allow_entry_deletion=False,
        trial_mode=False,
        items=[item.dict()]
    )

    # Check success of import
    response = client.post(admin_import_endpoint,
                           json=json.loads(import_payload.json()))
    check_status_success_true(response)

    # check that the item exists in export
    check_exported_table_size(client, 1)

    # Create an item in table 1
    activate_registry_table(table_from)

    # create an item
    item = write_random_item(client)

    # change to table 2
    activate_registry_table(table_to)

    # add item to table 2 through import
    import_payload = RegistryImportRequest(
        import_mode=import_mode,
        parse_items=True,
        allow_entry_deletion=False,
        trial_mode=False,
        items=[item.dict()]
    )

    # Check success of import
    response = client.post(admin_import_endpoint,
                           json=json.loads(import_payload.json()))
    check_status_success_true(response)

    # check that the item exists in export
    check_exported_table_size(client, 2)


@mock_dynamodb
def test_admin_import_overwrite_only() -> None:
    """
    Part of a series of import tests which tests functionality in various import
    modes. This is the OVERWRITE_ONLY mode.

    Failure conditions to test
    a) Try to add a new item to an empty registry
    b) Try to add a new item to a registry with existing entries

    Successful tests
    a) Override existing item in registry by supplying overlapping IDs

    """
    app.dependency_overrides[read_user_protected_role_dependency] = user_protected_dependency_override
    app.dependency_overrides[read_write_user_protected_role_dependency] = user_protected_dependency_override
    app.dependency_overrides[admin_user_protected_role_dependency] = user_protected_dependency_override

    # setup import mode for reuse
    import_mode = ImportMode.OVERWRITE_ONLY

    # Setup tables as required
    ddb_client = boto3.client('dynamodb')

    # =========
    # Failure A
    # =========

    # try to add to empty

    # setup two tables
    table_from = "failureA1"
    table_to = "failureA2"
    table_items = setup_tables({table_from: 1, table_to: 0}, table_to)

    # get item
    item = list(table_items[table_from].values())[0]
    item_dict = item.dict()

    # Now try to import new item into empty table
    import_payload = RegistryImportRequest(
        import_mode=import_mode,
        parse_items=True,
        allow_entry_deletion=False,
        trial_mode=False,
        items=[item_dict]
    )

    # try importing with existing item
    import_response = client.post(
        admin_import_endpoint, json=json.loads(import_payload.json()))

    # make sure response fails
    check_status_success_false(import_response)

    # =========
    # Failure B
    # =========

    # try to add new item to existing entries
    table_from = "failureB1"
    table_to = "failureB2"
    table_items = setup_tables({table_from: 1, table_to: 2}, table_to)
    new_item = list(table_items[table_from].values())[0]
    item_dict = new_item.dict()

    # Now try to import new item into table with entries
    import_payload = RegistryImportRequest(
        import_mode=import_mode,
        parse_items=True,
        allow_entry_deletion=False,
        trial_mode=False,
        items=[item_dict]
    )

    # try importing with existing item
    import_response = client.post(
        admin_import_endpoint, json=json.loads(import_payload.json()))

    # make sure response fails
    check_status_success_false(import_response)

    # =========
    # Success A
    # =========

    # setup table
    table_name = "successA1"
    num_items = 5
    table_items = setup_tables({table_name: num_items}, table_name)
    item_lookup = table_items[table_name]

    # for each item, modify the contents
    new_items: List[Dict[str, Any]] = []
    for item_id, item in item_lookup.items():
        # modify the display name
        item.item_payload.display_name += "modified"
        new_items.append(py_to_dict(item))

    # construct the import payload
    import_payload = RegistryImportRequest(
        import_mode=import_mode,
        parse_items=True,
        allow_entry_deletion=False,
        trial_mode=False,
        items=new_items
    )

    # Check success of import
    response = client.post(admin_import_endpoint,
                           json=json.loads(import_payload.json()))
    check_status_success_true(response)

    # make sure the items are updated
    assert_registry_state(client, new_items)


@mock_dynamodb
def test_admin_sync_deletion_allowed() -> None:
    """
    Part of a series of import tests which tests functionality in various import
    modes. This is the SYNC_DELETION_ALLOWED mode.

    Failure conditions to test
    a) Try to run a sync which requires deletion where deletion allowed flag is false

    Successful tests
    a) Run a sync which adds items only
    b) Run a sync which overrides items only
    c) Run a sync which adds and overrides items only
    d) Run a sync which deletes, adds and overrides items

    """
    # TODO only use required dep overrides
    app.dependency_overrides[read_user_protected_role_dependency] = user_protected_dependency_override
    app.dependency_overrides[read_write_user_protected_role_dependency] = user_protected_dependency_override
    app.dependency_overrides[admin_user_protected_role_dependency] = user_protected_dependency_override

    # setup import mode for reuse
    import_mode = ImportMode.SYNC_DELETION_ALLOWED

    # =========
    # Failure A
    # =========

    # try to add to empty

    # setup table
    table_name = "failureA1"
    num_items = 5
    items = setup_tables({table_name: num_items}, table_name)[table_name]

    # now remove some
    to_remove = 2
    for _ in range(to_remove):
        id_to_remove = choice(list(items.keys()))
        del items[id_to_remove]

    # now try to perform an import without the delete flag set
    item_payload = [item.dict() for item in items.values()]

    # construct the import payload
    import_payload = RegistryImportRequest(
        import_mode=import_mode,
        parse_items=True,
        # explicitly not including flag to make sure
        # default remains safe
        # allow_entry_deletion = False,
        trial_mode=False,
        items=item_payload
    )

    # Check success of import
    response = client.post(admin_import_endpoint,
                           json=json.loads(import_payload.json()))
    check_status_success_false(response)

    # =======
    # Success
    # =======

    # =====================================================
    # a) Run a sync which adds items only
    # =====================================================

    # Produce a set of items, export them, then add some more

    # setup tables
    table_old = "successA1"
    table_new = "successA2"
    num_from = 5
    num_to = 3
    table_items = setup_tables(
        {table_old: num_from, table_new: num_to}, table_old)

    # get items from the new table to use as new items
    common_items = table_items[table_old]
    new_items = table_items[table_new]

    # create a combined payload
    expected_state = [py_to_dict(item) for item in list(
        common_items.values()) + list(new_items.values())]

    # construct the import payload
    import_payload = RegistryImportRequest(
        import_mode=import_mode,
        parse_items=True,
        # don't need deletion here
        allow_entry_deletion=False,
        trial_mode=False,
        items=expected_state
    )

    # run import and make sure succeeds
    response = client.post(admin_import_endpoint,
                           json=json.loads(import_payload.json()))
    check_status_success_true(response)

    # now check that the current registry state matches expected
    actual_state = assert_registry_state(client, expected_state)

    # =====================================================
    # b) Run a sync which overrides items only
    # =====================================================

    # setup table
    table_name = "successB1"
    num_items = 10
    original_items = setup_tables(
        {table_name: num_items}, table_name)[table_name]

    new_items: List[Dict[str, Any]] = []
    for original_item in original_items.values():
        original_item.item_payload.display_name += "some change"
        new_items.append(py_to_dict(original_item))

    # import to the expected state
    import_payload = RegistryImportRequest(
        import_mode=import_mode,
        parse_items=True,
        # don't need deletion here
        allow_entry_deletion=False,
        trial_mode=False,
        items=new_items
    )

    # run import and make sure succeeds
    response = client.post(admin_import_endpoint,
                           json=json.loads(import_payload.json()))
    check_status_success_true(response)

    # now check that the current registry state matches expected
    assert_registry_state(client, new_items)

    # =====================================================
    # c) Run a sync which adds and overrides items only
    # =====================================================

    # setup table
    table_old = "successC1"
    table_new = "successC2"

    # create some items - these will be the new items added later
    num_new_items = 5
    num_common_items = 10
    table_items = setup_tables(
        {table_old: num_common_items, table_new: num_new_items}, table_old)
    common_items = table_items[table_old]
    new_items = table_items[table_new]

    # now produce an import payload which is a combination of modified items and
    # new items
    expected_items: List[Dict[str, Any]] = []
    for item in new_items.values():
        expected_items.append(py_to_dict(item))
    for item in common_items.values():
        item.item_payload.display_name += "some change"
        expected_items.append(py_to_dict(item))

    # run the import
    import_payload = RegistryImportRequest(
        import_mode=import_mode,
        parse_items=True,
        # don't need deletion here
        allow_entry_deletion=False,
        trial_mode=False,
        items=expected_items
    )

    # run import and make sure succeeds
    response = client.post(admin_import_endpoint,
                           json=json.loads(import_payload.json()))
    check_status_success_true(response)

    # now check that the current registry state matches expected
    assert_registry_state(client, expected_items)

    # =====================================================
    # d) Run a sync which deletes, adds and overrides items
    # =====================================================

    # setup table
    table_old = "successD1"
    table_new = "successD2"

    # create some items

    # 5 new items to add
    num_new_items = 5
    # 10 existing items
    num_common_items = 15
    # delete 5
    num_delete_items = 5

    table_items = setup_tables(
        {table_old: num_common_items, table_new: num_new_items}, table_old)
    common_items = table_items[table_old]
    new_items = table_items[table_new]
    deleted_item_ids = sample(sorted(common_items.keys()), num_delete_items)

    # now produce an import payload which is a combination of modified items,
    # new items and deleted items (removed)
    expected_items: List[Dict[str, Any]] = []
    for item in new_items.values():
        expected_items.append(py_to_dict(item))
    for item in common_items.values():
        # don't include if deleted!
        if item.id not in deleted_item_ids:
            item.item_payload.display_name += "some change"
            expected_items.append(py_to_dict(item))

    # run the import with deletion not enabled - ensure it fails
    import_payload = RegistryImportRequest(
        import_mode=import_mode,
        parse_items=True,
        # explicitly don't enable deletion
        allow_entry_deletion=False,
        trial_mode=False,
        items=expected_items
    )

    # run import and make sure fails
    response = client.post(admin_import_endpoint,
                           json=json.loads(import_payload.json()))
    check_status_success_false(response)

    # run the import with deletion enabled - ensure it succeeds
    import_payload = RegistryImportRequest(
        import_mode=import_mode,
        parse_items=True,
        # enable deletion explicitly
        allow_entry_deletion=True,
        trial_mode=False,
        items=expected_items
    )

    # run import and make sure fails
    response = client.post(admin_import_endpoint,
                           json=json.loads(import_payload.json()))
    check_status_success_true(response)

    # now check that the current registry state matches expected
    actual_state = assert_registry_state(client, expected_items)


@mock_dynamodb
def test_admin_table_restore() -> None:
    """
    Tests the admin restore from table endpoint. This just creates a few
    realistic scenarios using import and validation settings which are suitable.
    See the validation test, and the import mode tests for more detailed testing
    of these features. The restore endpoint just uses a dump from the specified
    table as the items input to an import op behind the scenes.

    NOTE no realistic failure conditions worth testing exist here - all failure
    conditions would be tested by the various failures in each of the import
    modes and also the validation test.

    Failure conditions to test

    None

    Successful tests

    a) Run a restore empty -> empty
    b) Run a restore full -> empty
    c) Run a restore full -> partial (adding and overriding entries - no mismatch)
    d) Run a restore full -> partial (some in current not in backup - keep both)
    e) Run a restore full -> partial (full sync - remove the current entries)

    """
    # TODO only use required dep overrides
    app.dependency_overrides[read_user_protected_role_dependency] = user_protected_dependency_override
    app.dependency_overrides[read_write_user_protected_role_dependency] = user_protected_dependency_override
    app.dependency_overrides[admin_user_protected_role_dependency] = user_protected_dependency_override

    # =======
    # Success
    # =======

    # ===========================================================================
    # a) Run a restore empty -> empty
    # ===========================================================================

    # setup backup and restore tables
    backup_table_name = "successA1"
    restore_table_name = "successA2"

    # empty tables - activate restore table
    setup_tables({backup_table_name: 0, restore_table_name: 0},
                 restore_table_name)

    # expected state of the restore table after restore op
    expected_state: List[Dict[str, Any]] = []

    # Run a sync add or overwrite restore from the first table
    names = import_names_from_base_name(backup_table_name)
    restore_payload = RegistryRestoreRequest(
        import_mode=ImportMode.SYNC_ADD_OR_OVERWRITE,
        parse_items=True,
        allow_entry_deletion=False,
        trial_mode=False,
        table_names=names
    )

    # run import and make sure succeeds
    response = client.post(admin_restore_endpoint,
                           json=py_to_dict(restore_payload))
    check_status_success_true(response)

    # now check that the current registry state matches expected
    assert_registry_state(client, expected_state)

    # ===========================================================================
    # b) Run a restore full -> empty
    # ===========================================================================

    # setup backup and restore tables
    backup_table_name = "successB1"
    restore_table_name = "successB2"
    backup_item_count = 20

    # create, populate and activate restore table
    table_items = setup_tables(
        {backup_table_name: backup_item_count, restore_table_name: 0}, restore_table_name)

    backup_items = bundled_item_dict_to_import_format(
        table_items[backup_table_name])
    restore_items = bundled_item_dict_to_import_format(
        table_items[restore_table_name])

    # Run a sync add or overwrite restore from the first table
    names = import_names_from_base_name(backup_table_name)
    restore_payload = RegistryRestoreRequest(
        import_mode=ImportMode.SYNC_ADD_OR_OVERWRITE,
        parse_items=True,
        allow_entry_deletion=False,
        trial_mode=False,
        table_names=names
    )

    # run import and make sure succeeds
    response = client.post(admin_restore_endpoint,
                           json=py_to_dict(restore_payload))
    check_status_success_true(response)

    # now check that the current registry state matches expected
    assert_registry_state(client, backup_items)

    # ==============================================================================
    # c) Run a restore full -> partial (adding and overriding entries - no mismatch)
    # ==============================================================================

    # setup backup and restore tables
    backup_table_name = "successC1"
    restore_table_name = "successC2"
    backup_item_count = 20
    restore_item_count = 20

    # create, populate and activate backup table
    table_items = setup_tables(
        {backup_table_name: backup_item_count,
            restore_table_name: restore_item_count},
        backup_table_name
    )

    backup_items = bundled_item_dict_to_import_format(
        table_items[backup_table_name])
    restore_items = bundled_item_dict_to_import_format(
        table_items[restore_table_name])

    # produce the restore payload -> backup
    names = import_names_from_base_name(restore_table_name)
    restore_payload = RegistryRestoreRequest(
        import_mode=ImportMode.ADD_OR_OVERWRITE,
        parse_items=True,
        allow_entry_deletion=False,
        trial_mode=False,
        table_names=names
    )

    # run restore, this should make backup = backup + restore
    response = client.post(admin_restore_endpoint,
                           json=py_to_dict(restore_payload))
    check_status_success_true(response)

    # now context swap back to the restore table
    activate_registry_table(restore_table_name)

    # Now perform a restore into the restore table using the sync add or overwrite
    names = import_names_from_base_name(backup_table_name)
    restore_payload = RegistryRestoreRequest(
        import_mode=ImportMode.SYNC_ADD_OR_OVERWRITE,
        parse_items=True,
        allow_entry_deletion=False,
        trial_mode=False,
        table_names=names
    )

    # this should succeed since backup contains strictly MORE items than the restore
    # table - see next success condition for case where we need to turn off sync mode
    response = client.post(admin_restore_endpoint,
                           json=py_to_dict(restore_payload))
    check_status_success_true(response)

    # now check that the state of the registry === combination of backup
    # and restore items
    assert_registry_state(client, backup_items + restore_items)

    # ==============================================================================
    # d) Run a restore full -> partial (some in current not in backup - keep both)
    # ==============================================================================

    # setup backup and restore tables
    backup_table_name = "successD1"
    restore_table_name = "successD2"
    backup_item_count = 20
    restore_item_count = 20

    # create, populate and activate restore table
    table_items = setup_tables(
        {backup_table_name: backup_item_count,
            restore_table_name: restore_item_count},
        restore_table_name
    )

    backup_items = bundled_item_dict_to_import_format(
        table_items[backup_table_name])
    restore_items = bundled_item_dict_to_import_format(
        table_items[restore_table_name])

    # Now perform a restore into the restore table using the sync add or overwrite
    names = import_names_from_base_name(backup_table_name)
    restore_payload = RegistryRestoreRequest(
        import_mode=ImportMode.SYNC_ADD_OR_OVERWRITE,
        parse_items=True,
        allow_entry_deletion=False,
        trial_mode=False,
        table_names=names
    )

    response = client.post(admin_restore_endpoint,
                           json=py_to_dict(restore_payload))
    # this should fail because there are items in the restore table
    # which are not in the backup table
    check_status_success_false(response)

    # now use the add or override non sync method
    names = import_names_from_base_name(backup_table_name)
    restore_payload = RegistryRestoreRequest(
        import_mode=ImportMode.ADD_OR_OVERWRITE,
        parse_items=True,
        allow_entry_deletion=False,
        trial_mode=False,
        table_names=names
    )

    response = client.post(admin_restore_endpoint,
                           json=py_to_dict(restore_payload))
    check_status_success_true(response)

    # now check that the state of the registry === combination of backup
    # and restore items
    assert_registry_state(client, backup_items + restore_items)

    # ===========================================================================
    # e) Run a restore full -> partial (full sync - remove the current entries)
    # ===========================================================================

    # setup backup and restore tables
    backup_table_name = "successE1"
    restore_table_name = "successE2"
    backup_item_count = 20
    restore_item_count = 20

    # create, populate and activate restore table
    table_items = setup_tables(
        {backup_table_name: backup_item_count,
            restore_table_name: restore_item_count},
        restore_table_name
    )

    backup_items = bundled_item_dict_to_import_format(
        table_items[backup_table_name])

    # Now perform a restore into the restore table using the sync
    # mode without deletion explicitly enabled
    names = import_names_from_base_name(backup_table_name)
    restore_payload = RegistryRestoreRequest(
        import_mode=ImportMode.SYNC_DELETION_ALLOWED,
        parse_items=True,
        allow_entry_deletion=False,
        trial_mode=False,
        table_names=names
    )

    response = client.post(admin_restore_endpoint,
                           json=py_to_dict(restore_payload))
    # this should fail because we didn't enable the deletion flag
    check_status_success_false(response)

    # now use the add or override non sync method
    names = import_names_from_base_name(backup_table_name)
    restore_payload = RegistryRestoreRequest(
        import_mode=ImportMode.SYNC_DELETION_ALLOWED,
        parse_items=True,
        allow_entry_deletion=True,
        trial_mode=False,
        table_names=names
    )

    response = client.post(admin_restore_endpoint,
                           json=py_to_dict(restore_payload))

    # this should succeed because we enabled the deletion flag
    check_status_success_true(response)

    # now check that the state of the registry === backup items
    assert_registry_state(client, backup_items)


@mock_dynamodb
def test_admin_import_add_or_overwrite() -> None:
    """
    Part of a series of import tests which tests functionality in various import
    modes. This is the ADD_OR_OVERWRITE mode.

    Failure conditions to test:
    None - will always validate as only adding or overwriting existing items.

    Success conditions to test:

    a) Import new items into empty table - make sure they exist after being added
    b) Import new item into table with existing entries - make sure it exists after being added
    c) Overwrite items in table. Ensure they are actually updated.
    d) Overwrite just 1 item in a table that has many items
    """
    # TODO only use required dep overrides
    app.dependency_overrides[read_user_protected_role_dependency] = user_protected_dependency_override
    app.dependency_overrides[read_write_user_protected_role_dependency] = user_protected_dependency_override
    app.dependency_overrides[admin_user_protected_role_dependency] = user_protected_dependency_override

    import_mode = ImportMode.ADD_OR_OVERWRITE

    # =======
    # SUCCESS
    # =======

    # ==========================================================================================
    # a) Import new items into empty table - make sure they exist after being added
    # ==========================================================================================

    # setup table
    table1_name = "tableA1"
    table2_name = "tableA2"
    num_items = 10
    table_items = setup_tables(
        {table1_name: num_items, table2_name: 0}, table2_name)
    to_import = bundled_item_dict_to_import_format(table_items[table1_name])

    # run an import of the items from table 1 into the new table
    import_payload = RegistryImportRequest(
        import_mode=import_mode,
        parse_items=True,
        allow_entry_deletion=False,
        trial_mode=False,
        items=to_import
    )

    # try importing with existing items
    import_response = client.post(
        admin_import_endpoint, json=json.loads(import_payload.json()))

    # make sure response succeeds
    check_status_success_true(import_response)

    # check that the item exists in export
    assert_registry_state(client, to_import)

    # ==========================================================================================
    # b) Import new item into table with existing entries - make sure it exists after being added
    # ==========================================================================================

    table1_name = "tableB1"
    table2_name = "tableB2"
    new_item_count = 10
    existing_item_count = 10
    table_items = setup_tables(
        {table1_name: new_item_count, table2_name: existing_item_count}, table2_name)
    new_items = bundled_item_dict_to_import_format(table_items[table1_name])
    existing_items = bundled_item_dict_to_import_format(
        table_items[table2_name])

    # use the new items in table1 -> import to table2 with existing items

    # add item to table 2 through import
    import_payload = RegistryImportRequest(
        import_mode=import_mode,
        parse_items=True,
        allow_entry_deletion=False,
        trial_mode=False,
        items=new_items
    )

    # Check success of import
    response = client.post(admin_import_endpoint,
                           json=json.loads(import_payload.json()))
    check_status_success_true(response)

    # check the state to make sure update + new items worked properly
    assert_registry_state(client, existing_items + new_items)

    # ==========================================================================================
    # c) Overwrite items in table. Ensure they are actually updated.
    # ==========================================================================================

    # setup one table with some items
    table_name = "successC1"
    num_items = 5
    table_items = setup_tables({table_name: num_items}, table_name)

    # get the current items
    current_items = bundled_item_dict_to_import_format(table_items[table_name])
    # modify them
    modified_items = produce_modified_items(current_items)

    # construct the import payload
    import_payload = RegistryImportRequest(
        import_mode=import_mode,
        parse_items=True,
        allow_entry_deletion=False,
        trial_mode=False,
        items=modified_items
    )

    # Check success of import
    response = client.post(admin_import_endpoint,
                           json=json.loads(import_payload.json()))
    check_status_success_true(response)

    # check modifications applied
    assert_registry_state(client, modified_items)

    # ==========================================================================================
    # d) Overwrite just 1 item in a table that has many items
    # ==========================================================================================
    # original_items = new_items # original items here are the new items form end of test C

    # setup one table with some items
    table_name = "successD1"
    num_items = 5
    table_items = setup_tables({table_name: num_items}, table_name)

    # get the current items
    current_items = bundled_item_dict_to_import_format(table_items[table_name])

    # choose an item
    item_to_change = current_items.pop()
    modified_item = produce_modified_items([item_to_change])[0]
    modified_items = current_items
    modified_items.append(modified_item)

    # construct the import payload
    import_payload = RegistryImportRequest(
        import_mode=import_mode,
        parse_items=True,
        allow_entry_deletion=False,
        trial_mode=False,
        items=modified_items
    )

    # Check success of import
    response = client.post(admin_import_endpoint,
                           json=json.loads(import_payload.json()))
    check_status_success_true(response)

    # check modifications applied
    assert_registry_state(client, modified_items)


@mock_dynamodb
def test_admin_sync_add_or_overwrite() -> None:
    """
    Part of a series of import tests which tests functionality in various import
    modes. This is the SYNC_ADD_OR_OVERWRITE mode.

    Can add items, can overwrite items.
    Every item already in the registry already must be overwritten/updated.

    Fail tests
    a) ensure fail if just adding items to non empty registry
    b) ensure fail when sending payload with a subset (missing at least 1 item) of registry's items
    c) ensure fail when sending payload of a subset (missing at least 1 item) of registry's items + some new items
    Warning: Ensure they fail for the correct reason!

    Success tests.
    d) Can add to empty registry
    e) can overwrite all items in registry
    f) can overwrite all items and add to registry

    """

    # TODO only use required dep overrides
    app.dependency_overrides[read_user_protected_role_dependency] = user_protected_dependency_override
    app.dependency_overrides[read_write_user_protected_role_dependency] = user_protected_dependency_override
    app.dependency_overrides[admin_user_protected_role_dependency] = user_protected_dependency_override

    import_mode = ImportMode.SYNC_ADD_OR_OVERWRITE

    # =============
    # Failure Tests
    # =============

    # ================================================================================================
    # a) ensure fail if just adding items to non empty registry
    # ================================================================================================

    # Create table with items + another table to get new items
    main_table_name = "failureA1"
    main_table_count = 10
    new_item_table_name = "failureA2"
    new_item_table_count = 1

    # create
    table_items = setup_tables({main_table_name: main_table_count,
                               new_item_table_name: new_item_table_count}, main_table_name)

    # pull out the new item(s)
    new_item_payload = bundled_item_dict_to_import_format(
        table_items[new_item_table_name])
    current_items = bundled_item_dict_to_import_format(
        table_items[main_table_name])

    # import
    import_payload = RegistryImportRequest(
        import_mode=import_mode,
        parse_items=True,
        allow_entry_deletion=False,
        trial_mode=False,
        items=new_item_payload
    )
    import_response = client.post(
        admin_import_endpoint, json=json.loads(import_payload.json()))

    # should fail writing new item as there is existing items not being overwritten
    # TODO add check for correct error and not some other parsing error
    check_status_success_false(import_response)

    # check nothing was written
    assert_registry_state(client, current_items)

    # ================================================================================================
    # b) ensure fail when sending payload with a subset (missing at least 1 item) of registry's items
    # ================================================================================================

    # Failure B - sending payload with a subset (missing at least 1 item) of registry's items

    # Create table with items
    main_table_name = "failureB1"
    main_table_count = 10
    table_items = setup_tables(
        {main_table_name: main_table_count}, main_table_name)

    # pull out the new item(s)
    current_items = bundled_item_dict_to_import_format(
        table_items[main_table_name])

    # get rid of one of them to invalidate import
    removed_item = current_items.pop()

    # import
    import_payload = RegistryImportRequest(
        import_mode=import_mode,
        parse_items=True,
        allow_entry_deletion=False,
        trial_mode=False,
        items=current_items
    )
    import_response = client.post(
        admin_import_endpoint, json=json.loads(import_payload.json()))

    # should fail writing new item as there is an existing item not being overwritten
    # TODO add check for correct error and not some other parsing error
    check_status_success_false(import_response)

    # check nothing was written
    # add removed item back
    current_items.append(removed_item)
    assert_registry_state(client, current_items)

    # ================================================================================================
    # c) ensure fail when sending payload of a subset (missing at least 1 item)
    #   of registry's items + some new items
    # ================================================================================================

    # Failure C - sending payload with 1 item in registry missing but also a new item trying to be added

    # Create table with items + another table to get new items
    main_table_name = "failureC1"
    main_table_count = 10
    new_item_table_name = "failureC2"
    new_item_table_count = 5

    # create
    table_items = setup_tables({main_table_name: main_table_count,
                               new_item_table_name: new_item_table_count}, main_table_name)

    # pull out the new item(s)
    new_item_payload = bundled_item_dict_to_import_format(
        table_items[new_item_table_name])
    current_items = bundled_item_dict_to_import_format(
        table_items[main_table_name])

    # now remove an item from current
    removed_item = current_items.pop()

    # now produce combined payload
    combined_payload = new_item_payload + current_items

    # import
    import_payload = RegistryImportRequest(
        import_mode=import_mode,
        parse_items=True,
        allow_entry_deletion=False,
        trial_mode=False,
        items=combined_payload
    )
    import_response = client.post(
        admin_import_endpoint, json=json.loads(import_payload.json()))

    # should fail because we are missing the popped items
    # TODO add check for correct error and not some other parsing error
    check_status_success_false(import_response)

    # add item back
    current_items.append(removed_item)

    # check nothing was written
    assert_registry_state(client, current_items)

    # =============
    # Success Tests
    # =============

    # ==============================================
    # d) Can add to empty registry
    # ==============================================

    # Create table with items + another table to get new items
    main_table_name = "successD1"
    main_table_count = 0
    new_item_table_name = "successD2"
    new_item_table_count = 5

    # create
    table_items = setup_tables({main_table_name: main_table_count,
                               new_item_table_name: new_item_table_count}, main_table_name)

    # pull out the new items and current items
    new_item_payload = bundled_item_dict_to_import_format(
        table_items[new_item_table_name])
    current_items = bundled_item_dict_to_import_format(
        table_items[main_table_name])

    # produce import request
    import_payload = RegistryImportRequest(
        import_mode=import_mode,
        parse_items=True,
        allow_entry_deletion=False,
        trial_mode=False,
        items=new_item_payload
    )

    # run the request
    import_response = client.post(
        admin_import_endpoint, json=json.loads(import_payload.json()))

    # make sure it succeeded and that state is correct
    check_status_success_true(import_response)
    assert_registry_state(client, new_item_payload)

    # ==============================================
    # e) can overwrite all items in registry
    # ==============================================

    # Create table with items
    main_table_name = "successE1"
    main_table_count = 10

    # create
    table_items = setup_tables(
        {main_table_name: main_table_count}, main_table_name)

    # pull out the new items and current items
    current_items = bundled_item_dict_to_import_format(
        table_items[main_table_name])

    # check that the registry has current items
    assert_registry_state(client, current_items)

    # produce modified list
    modified_items = produce_modified_items(current_items)

    # produce import request
    import_payload = RegistryImportRequest(
        import_mode=import_mode,
        parse_items=True,
        allow_entry_deletion=False,
        trial_mode=False,
        items=modified_items
    )

    # run the request
    import_response = client.post(
        admin_import_endpoint, json=json.loads(import_payload.json()))

    # make sure it succeeded and that state is correct
    check_status_success_true(import_response)
    assert_registry_state(client, modified_items)

    # ==============================================
    # f) can overwrite all items and add to registry
    # ==============================================

    # Create table with items + another table to get new items
    main_table_name = "successF1"
    main_table_count = 10
    new_item_table_name = "successF2"
    new_item_table_count = 5

    # create
    table_items = setup_tables({main_table_name: main_table_count,
                               new_item_table_name: new_item_table_count}, main_table_name)

    # pull out the new items and current items
    new_item_payload = bundled_item_dict_to_import_format(
        table_items[new_item_table_name])
    current_items = bundled_item_dict_to_import_format(
        table_items[main_table_name])

    # check that current items is correct
    assert_registry_state(client, current_items)

    # produce modified list
    modified_items = produce_modified_items(current_items)
    full_payload = new_item_payload + modified_items

    # produce import request
    import_payload = RegistryImportRequest(
        import_mode=import_mode,
        parse_items=True,
        allow_entry_deletion=False,
        trial_mode=False,
        items=full_payload
    )

    # run the request
    import_response = client.post(
        admin_import_endpoint, json=json.loads(import_payload.json()))

    # make sure it succeeded and that state is correct
    check_status_success_true(import_response)

    assert_registry_state(client, full_payload)


def remove_key(d: Dict[Any, Any], key: str) -> Dict[Any, Any]:
    # https://stackoverflow.com/questions/5844672/delete-an-element-from-a-dictionary
    # given a ditionary, return a new dictionary without one of the elements
    r = dict(d)
    del r[key]
    return r


@mock_dynamodb
@pytest.mark.parametrize("params", route_params, ids=make_specialised_list("Parse validation"))
def test_admin_import_validation(params: RouteParameters) -> None:
    """
    Tests in more depth the validation mode for the import. This validation mode
    should ensure that items being added are of the correct type, and parse as
    that model type.


    SUCCESS
    a) Send valid complete item and ensure succeeds
    b) Send valid seed item and ensure succeeds

    Failures
    a) Provide record with invalid RecordInfo (e.g. missing field)
    b) Provide record with unknown type combination (e.g. Entity/Person)
    c) Provide complete item with invalid Domain info

    """
    app.dependency_overrides[read_user_protected_role_dependency] = user_protected_dependency_override
    app.dependency_overrides[read_write_user_protected_role_dependency] = user_protected_dependency_override
    app.dependency_overrides[admin_user_protected_role_dependency] = user_protected_dependency_override

    # =======
    # SUCCESS
    # =======

    # ====================================================================
    # a) Send valid complete item and ensure succeeds
    # ====================================================================

    # Setup a table to work in - put some items in
    main_table = "successA1"
    aux_table = "successA2"
    num_items = 5

    table_items = setup_tables(
        {main_table: num_items, aux_table: 0}, aux_table)
    main_items = bundled_item_dict_to_import_format(table_items[main_table])

    # post an example item to aux table
    example_item = post_example_item(client, params)

    # validate the state of the registry
    aux_state = assert_registry_state(
        client, [json.loads(example_item.json())])

    # checkout main table
    activate_registry_table(main_table)

    # import the item
    item_payload = list(aux_state.values())
    import_payload = RegistryImportRequest(
        import_mode=ImportMode.ADD_ONLY,
        parse_items=True,
        allow_entry_deletion=False,
        trial_mode=False,
        items=item_payload
    )

    # run the request
    import_response = client.post(
        admin_import_endpoint, json=json.loads(import_payload.json()))

    # make sure it succeeded and that state is correct
    check_status_success_true(import_response)
    assert_registry_state(client, item_payload + main_items)

    # ====================================================================
    # b) Send valid seed item and ensure succeeds
    # ====================================================================

    # Setup a table to work in - put some items in
    main_table = "successB1"
    aux_table = "successB2"
    num_items = 5

    table_items = setup_tables(
        {main_table: num_items, aux_table: 0}, aux_table)
    main_items = bundled_item_dict_to_import_format(table_items[main_table])

    # post an example seed to aux table
    example_seed = seed_example_item(client, params)

    # validate the state of the registry
    aux_state = assert_registry_state(
        client, [py_to_dict(example_seed)])

    # checkout main table
    activate_registry_table(main_table)

    # import the item
    item_payload = list(aux_state.values())
    import_payload = RegistryImportRequest(
        import_mode=ImportMode.ADD_ONLY,
        parse_items=True,
        allow_entry_deletion=False,
        trial_mode=False,
        items=item_payload
    )

    # run the request
    import_response = client.post(
        admin_import_endpoint, json=json.loads(import_payload.json()))

    # make sure it succeeded and that state is correct
    check_status_success_true(import_response)
    assert_registry_state(client, item_payload + main_items)

    # ========
    # FAILURES
    # ========

    # ====================================================================
    # a) Provide record with invalid RecordInfo (e.g. missing field)
    # ====================================================================

    # Create an item of a known type using the aux table, get it back
    # then modify the payload to have inappropriate record info

    # Setup a table to work in - put some items in
    main_table = "failureA1"
    aux_table = "failureA2"
    num_items = 5

    table_items = setup_tables(
        {main_table: num_items, aux_table: 0}, aux_table)
    main_items = bundled_item_dict_to_import_format(table_items[main_table])

    # post an example item to aux table
    example_item = post_example_item(client, params)

    # validate the state of the registry
    aux_state = assert_registry_state(
        client, [json.loads(example_item.json())])

    # item contents
    item_contents = list(aux_state.values())[0]

    # analyse the RecordInfo model to find keys which are required
    required_fields: List[str] = get_required_fields(
        RecordInfo)  # type: ignore

    # checkout main table
    activate_registry_table(main_table)

    # for each required key, remove this key and ensure that import fails
    for required_key in required_fields:
        # Make a copy of the original item
        item_copy = deepcopy(item_contents)

        # remove a required key, ensuring it is included in the first place
        assert required_key in item_copy['item_payload'].keys()
        del item_copy['item_payload'][required_key]

        # import the item
        import_payload = RegistryImportRequest(
            import_mode=ImportMode.ADD_ONLY,
            parse_items=True,
            allow_entry_deletion=False,
            trial_mode=False,
            items=[item_copy]
        )

        # run the request
        import_response = client.post(
            admin_import_endpoint, json=json.loads(import_payload.json()))

        # make sure it failed and that state has not changed
        check_status_success_false(import_response)
        assert_registry_state(client, main_items)

    # ====================================================================
    # b) Provide record with unknown type combination (e.g. Entity/Person)
    # ====================================================================

    # Create an item of a known type using the aux table, get it back
    # then modify the payload to have inappropriate category/subtype

    # Setup a table to work in - put some items in
    main_table = "failureB1"
    aux_table = "failureB2"
    num_items = 5

    table_items = setup_tables(
        {main_table: num_items, aux_table: 0}, aux_table)
    main_items = bundled_item_dict_to_import_format(table_items[main_table])

    # post an example item to aux table
    example_item = post_example_item(client, params)
    example_dict = json.loads(example_item.json())

    # validate the state of the registry
    aux_state = assert_registry_state(client, [example_dict])

    # checkout main table
    activate_registry_table(main_table)

    # find an invalid combination of category-subtype
    cat_subtype_combo = produce_invalid_category_subtype_combination()
    example_dict['item_payload']['item_category'] = cat_subtype_combo[0]
    example_dict['item_payload']['item_subtype'] = cat_subtype_combo[1]

    # import the item
    import_payload = RegistryImportRequest(
        import_mode=ImportMode.ADD_ONLY,
        parse_items=True,
        allow_entry_deletion=False,
        trial_mode=False,
        items=[example_dict]
    )

    # run the request
    import_response = client.post(
        admin_import_endpoint, json=json.loads(import_payload.json()))

    # make sure it failed and that state has not changed
    check_status_success_false(import_response)
    assert_registry_state(client, main_items)

    # ====================================================================
    # c) Provide complete item with invalid Domain info
    # ====================================================================

    # Create an item of a known type using the aux table, get it back
    # then modify the payload to have inappropriate domain info

    # Setup a table to work in - put some items in
    main_table = "failureC1"
    aux_table = "failureC2"
    num_items = 5

    table_items = setup_tables(
        {main_table: num_items, aux_table: 0}, aux_table)
    main_items = bundled_item_dict_to_import_format(table_items[main_table])

    # post an example item to aux table
    example_item = post_example_item(client, params)

    # validate the state of the registry
    aux_state = assert_registry_state(
        client, [json.loads(example_item.json())])

    # item contents
    item_contents = list(aux_state.values())[0]

    # analyse the domain info model to find keys which are required
    domain_info_type = params.typing_information.domain_info
    required_fields: List[str] = get_required_fields(
        domain_info_type)  # type: ignore

    # checkout main table
    activate_registry_table(main_table)

    # for each required key, remove this key and ensure that import fails
    for required_key in required_fields:
        # Make a copy of the original item
        item_copy = deepcopy(item_contents)

        # remove a required key, ensuring it is included in the first place
        assert required_key in item_copy['item_payload'].keys()
        del item_copy['item_payload'][required_key]

        # import the item
        import_payload = RegistryImportRequest(
            import_mode=ImportMode.ADD_ONLY,
            parse_items=True,
            allow_entry_deletion=False,
            trial_mode=False,
            items=[item_copy]
        )

        # run the request
        import_response = client.post(
            admin_import_endpoint, json=json.loads(import_payload.json()))

        # make sure it failed and that state has not changed
        check_status_success_false(import_response)
        assert_registry_state(client, main_items)


@mock_dynamodb
@pytest.mark.parametrize("import_mode", import_modes, ids=["Trial mode: " + import_mode.value for import_mode in ImportMode])
def test_admin_import_trial_mode(import_mode: ImportMode) -> None:
    """
    This is a basic test for each import mode to make sure the trial mode is
    working as expected.

    For each import mode, we run a suitable import which would result in changes
    to the registry if the trial mode was set to False. We assert that for both
    default trial mode value, and explicit trial mode = True, the import
    succeeds but results in a trial_mode=True flag and no changes to the actual
    registry.

    We then confirm that with trial mode set to false, the registry changes
    successfully.

    NOTE the OVERWRITE_ONLY mode has a separate test condition because it cannot
    produce new items. Otherwise all import modes are covered by a single
    parameterised test case in which items are added to an empty registry.
    """

    app.dependency_overrides[read_user_protected_role_dependency] = user_protected_dependency_override
    app.dependency_overrides[read_write_user_protected_role_dependency] = user_protected_dependency_override
    app.dependency_overrides[admin_user_protected_role_dependency] = user_protected_dependency_override

    if import_mode != ImportMode.OVERWRITE_ONLY:
        # every import mode except overwrite only can be satisfied by just
        # writing a new entry into an empty table and ensuring nothing happens
        # until trial mode is turned on
        table1_name = "table1"
        table2_name = "table2"
        new_item_count = 10

        # if we want this test to be as generic as possible we can't have
        # existing items since sync deletion vs add only vs add or override will
        # have different behaviour for registries with existing items
        existing_item_count = 0
        table_items = setup_tables(
            {table1_name: new_item_count, table2_name: existing_item_count}, table2_name)
        new_items = bundled_item_dict_to_import_format(
            table_items[table1_name])
        existing_items = bundled_item_dict_to_import_format(
            table_items[table2_name])

        # use the new items in table1 -> import to table2 with existing items

        # leave trial mode default True - this ensures that trial mode remains true by default
        import_payload = RegistryImportRequest(
            import_mode=import_mode,
            parse_items=True,
            allow_entry_deletion=False,
            # trial_mode=False,
            items=new_items
        )

        # Check success of import
        response = client.post(admin_import_endpoint,
                               json=json.loads(import_payload.json()))

        # this should succeed
        check_status_success_true(response)

        # however nothing should have changed
        assert_registry_state(client, existing_items)

        # also check that the trial mode flag is set to true in response
        parsed_response = RegistryImportResponse.parse_obj(response.json())
        assert parsed_response.trial_mode, "Trial mode was left default True but wasn't in the response"

        # now set it explicitly to true - and ensure the same behaviour occurs
        import_payload = RegistryImportRequest(
            import_mode=import_mode,
            parse_items=True,
            allow_entry_deletion=False,
            trial_mode=True,
            items=new_items
        )

        # Check success of import
        response = client.post(admin_import_endpoint,
                               json=json.loads(import_payload.json()))

        # this should succeed
        check_status_success_true(response)

        # however nothing should have changed
        assert_registry_state(client, existing_items)

        # also check that the trial mode flag is set to true in response
        parsed_response = RegistryImportResponse.parse_obj(response.json())
        assert parsed_response.trial_mode, "Trial mode was set to True but wasn't in the response"

        # now set it explicitly to False - and ensure the write works
        import_payload = RegistryImportRequest(
            import_mode=import_mode,
            parse_items=True,
            allow_entry_deletion=False,
            trial_mode=False,
            items=new_items
        )

        # Check success of import
        response = client.post(admin_import_endpoint,
                               json=json.loads(import_payload.json()))

        # this should succeed
        check_status_success_true(response)

        # and items should be updated
        assert_registry_state(client, existing_items + new_items)

        # also check that the trial mode flag is set to false in response
        parsed_response = RegistryImportResponse.parse_obj(response.json())
        assert not parsed_response.trial_mode, "Trial mode was set to False but wasn't in the response"

    else:
        # OVERWRITE ONLY mode will fail if a new entry is created, so we need to
        # have a special overwrite test

        # create a table with 10 items in it
        table1_name = "table1"
        existing_item_count = 10
        table_items = setup_tables(
            {table1_name: existing_item_count}, table1_name)
        existing_items = bundled_item_dict_to_import_format(
            table_items[table1_name])
        # produce set of modified items from copies
        modified_items = produce_modified_items(
            [deepcopy(item) for item in existing_items])

        # try importing - if trial mode is working properly this should succeed but have no impact

        # leave trial mode default True - this ensures that trial mode remains true by default
        import_payload = RegistryImportRequest(
            import_mode=import_mode,
            parse_items=True,
            allow_entry_deletion=False,
            # trial_mode=False,
            items=modified_items
        )

        # Check success of import
        response = client.post(admin_import_endpoint,
                               json=json.loads(import_payload.json()))

        # this should succeed
        check_status_success_true(response)

        # however nothing should have changed
        assert_registry_state(client, existing_items)

        # also check that the trial mode flag is set to true in response
        parsed_response = RegistryImportResponse.parse_obj(response.json())
        assert parsed_response.trial_mode, "Trial mode was left default True but wasn't in the response"

        # now set it explicitly to true - and ensure the same behaviour occurs
        import_payload = RegistryImportRequest(
            import_mode=import_mode,
            parse_items=True,
            allow_entry_deletion=False,
            trial_mode=True,
            items=modified_items
        )

        # Check success of import
        response = client.post(admin_import_endpoint,
                               json=json.loads(import_payload.json()))

        # this should succeed
        check_status_success_true(response)

        # however nothing should have changed
        assert_registry_state(client, existing_items)

        # also check that the trial mode flag is set to true in response
        parsed_response = RegistryImportResponse.parse_obj(response.json())
        assert parsed_response.trial_mode, "Trial mode was set to True but wasn't in the response"

        # now set it explicitly to False - and ensure the write works
        import_payload = RegistryImportRequest(
            import_mode=import_mode,
            parse_items=True,
            allow_entry_deletion=False,
            trial_mode=False,
            items=modified_items
        )

        # Check success of import
        response = client.post(admin_import_endpoint,
                               json=json.loads(import_payload.json()))

        # this should succeed
        check_status_success_true(response)

        # and items should be updated
        assert_registry_state(client, modified_items)

        # also check that the trial mode flag is set to false in response
        parsed_response = RegistryImportResponse.parse_obj(response.json())
        assert not parsed_response.trial_mode, "Trial mode was set to False but wasn't in the response"
