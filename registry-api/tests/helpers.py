from copy import deepcopy
from random import choice
from typing import Any
from tests.config import *
from dataclasses import dataclass
import pytest
from fastapi.testclient import TestClient
from KeycloakFastAPI.Dependencies import ProtectedRole, User
from dependencies.dependencies import read_user_protected_role_dependency, read_write_user_protected_role_dependency
# from requests import Response
from httpx._models import Response
import json
from main import route_configs, ITEM_CATEGORY_ROUTE_MAP, ITEM_SUB_TYPE_ROUTE_MAP
from pydantic import BaseModel
import boto3  # type:ignore
from ProvenaSharedFunctionality.Registry.RegistryRouteActions import ROUTE_ACTION_CONFIG_MAP, RouteActions
from ProvenaInterfaces.TestConfig import route_params, RouteParameters

# Which subtypes are excluded from regular comprehensive testing
route_config_exclusions: List[ItemSubType] = [
    ItemSubType.CREATE,
    ItemSubType.VERSION
]

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


# Create parameter set for import mode. Used for testing trial mode features
# against each import mode.
import_modes: List[ImportMode] = list(ImportMode)


def get_route(action: RouteActions, params: RouteParameters) -> str:
    # check for special proxy types
    if params.use_special_proxy_modify_routes:
        if action == RouteActions.CREATE:
            action = RouteActions.PROXY_CREATE
        elif action == RouteActions.SEED:
            action = RouteActions.PROXY_SEED
        elif action == RouteActions.UPDATE:
            action = RouteActions.PROXY_UPDATE
        elif action == RouteActions.REVERT:
            action = RouteActions.PROXY_REVERT

    # get the route prefix
    prefix = f"/registry{params.route}"
    action_path = ROUTE_ACTION_CONFIG_MAP[action].path

    return prefix + action_path


class TypedItemBundle(BaseModel):
    id: str
    item_payload: ItemBase
    auth_payload: AuthTableEntry
    lock_payload: LockTableEntry


class SeededItemBundle(BaseModel):
    id: str
    item_payload: SeededItem
    auth_payload: AuthTableEntry
    lock_payload: LockTableEntry


def make_specialised_list(action: str) -> List[str]:
    """    make_specialised_list
        Given an action name, prepends action name in nice format
        to each test name in the base id list as above.

        Arguments
        ----------
        action : str
            The action 

        Returns
        -------
         : List[str]
            New list of test names
            Format: {action}: ({existing base id})

        See Also (optional)
        --------

        Examples (optional)
        --------
    """
    return [f"{action}: ({base})" for base in id_base_list]


def filtered_none_deep_copy(input: Any) -> Union[Dict[Any, Any], List[Any], Any]:
    """
    Helper function to make a deepcopy of a dictionary recursively - not
    including any None objects. This is because dictionary comparisons are
    sensitive to None/null values in the pydantic model/json object. We aren't
    concerned about Nones vs not including for the purposes of these test.

    Parameters
    ----------
    input : Any
        Either a dictionary or an object which will be returned (think leaf
        node)

    Returns
    -------
    Union[Dict[Any, Any], Any]
        Either a dictionary (i.e. recursively) or a leaf node 
    """
    # if dictionary - copy recursively
    if isinstance(input, dict):
        # produce a new dictionary
        new_dict: Dict[Any, Any] = {}
        # iterate through key values
        for k, v in input.items():
            # if none - don't include
            if v is None or v == "null":
                # If None for value, do nothing
                continue
            else:
                # If value is not none then include the k-v recursively
                new_dict[k] = filtered_none_deep_copy(v)
        return new_dict

    # if list - iterate through and filter none
    # returning recursively for elements
    if isinstance(input, list):
        new_list = []
        for v in input:
            # if none - don't include
            if v is None:
                # If None for value, do nothing
                continue
            else:
                # If value is not none then include the k-v recursively
                new_list.append(filtered_none_deep_copy(v))
        return new_list
    else:
        # Return a native copy of the leaf node
        return deepcopy(input)

def seed_item_successfully(client: TestClient, item_subtype: ItemSubType) -> SeededItem:
    resp = seed_item(client, item_subtype)
    check_status_success_true(resp)
    seed_resp = GenericSeedResponse.parse_obj(resp.json())
    assert seed_resp.status.success
    item = seed_resp.seeded_item
    assert item
    return item

def seed_item(client: TestClient, item_subtype: ItemSubType) -> Response:
    seed_route = get_route(action=RouteActions.SEED, params=get_item_subtype_route_params(item_subtype))
    return client.post(seed_route)

def entity_list_exhaust(client: TestClient, params: RouteParameters, subtype_list_request: Optional[SubtypeListRequest] = None) -> Tuple[List[ItemBase], List[SeededItem]]:
    list_route = get_route(action=RouteActions.LIST, params=params)

    list_request: SubtypeListRequest
    if subtype_list_request:
        list_request = subtype_list_request
    else:
        list_request = SubtypeListRequest()

    pagination_key: Optional[PaginationKey] = None

    complete_items: List[ItemBase] = []
    seed_items: List[SeededItem] = []

    exhausted = False

    while not exhausted:
        list_request.pagination_key = pagination_key
        response = client.post(
            url=list_route, json=json.loads(list_request.json()))

        # checks that the response was successful and parsable
        check_status_success_true(response)
        json_response = response.json()
        parsed_response = GenericListResponse.parse_obj(json_response)
        assert parsed_response.items is not None

        # add the items to accumulated items
        complete_items.extend([params.typing_information.item_model.parse_obj(i)
                              for i in parsed_response.items])
        seed_items.extend(
            [SeededItem.parse_obj(i) for i in parsed_response.seed_items] if parsed_response.seed_items else [])

        pagination_key = parsed_response.pagination_key
        if pagination_key is None:
            exhausted = True

    return complete_items, seed_items


def general_list_exhaust(client: TestClient, general_list_request: Optional[GeneralListRequest] = None) -> List[Dict[str, Any]]:
    """
    general_list_exhaust 

    Uses the default filter/sort options to repeatedly query the general list
    endpoint until exhaustion.

    Parameters
    ----------
    client : TestClient
        FastAPI test client

    Returns
    -------
    List[Dict[str, Any]]
        The item list
    """
    exhausted = False
    pagination_key: Optional[PaginationKey] = None
    items: List[Dict[str, Any]] = []

    base_request: GeneralListRequest

    if general_list_request:
        base_request = general_list_request
    else:
        base_request = GeneralListRequest(
            pagination_key=pagination_key
        )

    while not exhausted:
        base_request.pagination_key = pagination_key
        response = client.post("/registry/general/list",
                               json=json.loads(base_request.json()))

        # checks that the response was successful and parsable
        check_status_success_true(response)
        json_response = response.json()
        parsed_response = PaginatedListResponse.parse_obj(json_response)
        assert parsed_response.items is not None

        # add the items to accumulated items
        items.extend(parsed_response.items)

        pagination_key = parsed_response.pagination_key
        if pagination_key is None:
            exhausted = True

    return items


def create_random_domain_info() -> DomainInfoBase:
    """
    Selects a random domain info base

    Parameters
    ----------

    Returns
    -------
    DomainInfoBase
        The item that was created typed as the item base - we don't really care
        about the type.
    """
    # select a random route
    route_param: RouteParameters = choice(route_params)

    # select a model example randomly
    model_example: DomainInfoBase = choice(
        route_param.model_examples.domain_info)

    return model_example


def seed_example_item(app_client: TestClient, route_param: RouteParameters) -> SeededItemBundle:
    """
    Helper function which uses the parameterised testing context e.g. route
    params to run a client post against the seed endpoint - generating an item.

    Parameters
    ----------
    app_client : TestClient
        The fastAPI test client
    route_param : RouteParameters
        The current pytest params

    Returns
    -------
    SeededItem
        The returned seed item
    """
    # find the create route
    if route_param.use_special_proxy_modify_routes:
        seed_route = f"/registry{route_param.route}/proxy/seed"
    else:
        seed_route = f"/registry{route_param.route}/seed"

    # create the item
    response = app_client.post(seed_route)

    # check success
    assert response.status_code == 200
    seed_resp_model = route_param.typing_information.seed_response
    assert seed_resp_model, f"Seed response model not defined for {route_param.route}"
    seed_response: GenericSeedResponse = seed_resp_model.parse_obj(
        response.json())
    assert seed_response.status.success

    # return the created item
    assert seed_response.seeded_item

    id = seed_response.seeded_item.id

    # Now we want the lock information and auth information
    auth_route = f"/registry{route_param.route}/auth/configuration"
    params = {
        "id": id
    }
    response = app_client.get(auth_route, params=params)

    # check success
    assert response.status_code == 200
    # parse access settings
    access_settings = AccessSettings.parse_obj(response.json())

    # construct the complete item
    return SeededItemBundle(
        id=id,
        item_payload=seed_response.seeded_item,
        auth_payload=AuthTableEntry(
            id=id,
            access_settings=access_settings
        ),
        lock_payload=LockTableEntry(
            id=id,
            lock_information=LockInformation(
                locked=False,
                history=[]
            )
        )
    )


def standard_post_item(app_client: TestClient, route_param: RouteParameters) -> ItemBase:
    # Choose a domain example randomly
    domain_example: DomainInfoBase = choice(
        route_param.model_examples.domain_info)

    # find the create route
    create_route = f"/registry{route_param.route}/create"

    # create the item
    serialised = json.loads(domain_example.json())
    response = app_client.post(create_route, json=serialised)

    # check success
    assert response.status_code == 200, f"Non 200 response code: {response.status_code}. Details: {response.text}"
    create_resp_model = route_param.typing_information.create_response
    assert create_resp_model, f"Create response model not defined for {route_param.route}"
    create_response = create_resp_model.parse_obj(
        response.json())
    assert create_response.status.success

    assert create_response.created_item

    return create_response.created_item


def proxy_post_item(app_client: TestClient, route_param: RouteParameters) -> ItemBase:
    # Choose a domain example randomly
    domain_example: DomainInfoBase = choice(
        route_param.model_examples.domain_info)

    # find the create route - proxy version
    create_route = f"/registry{route_param.route}/proxy/create"

    # create the item
    serialised = json.loads(domain_example.json())
    response = app_client.post(create_route, json=serialised)

    # check success
    assert response.status_code == 200, f"Non 200 response code: {response.status_code}. Details: {response.text}"
    create_resp_model = route_param.typing_information.create_response
    assert create_resp_model, f"Create response model not defined for {route_param.route}"
    create_response = create_resp_model.parse_obj(
        response.json())
    assert create_response.status.success

    assert create_response.created_item

    return create_response.created_item


def post_example_item(app_client: TestClient, route_param: RouteParameters) -> TypedItemBundle:
    """
    Helper function which uses the parameterised testing context e.g. route
    params to run a client post against the /create endpoint - generating an
    item. It randomly selects a domain model from the param examples.

    Parameters
    ----------
    app_client : TestClient
        The fastAPI test client
    route_param : RouteParameters
        The current pytest params

    Returns
    -------
    ItemBase
        The returned Item, typed as the base class
    """

    # standard non proxied route
    if not route_param.use_special_proxy_modify_routes:
        item = standard_post_item(
            app_client=app_client,
            route_param=route_param
        )
    else:
        # proxy version
        item = proxy_post_item(
            app_client=app_client,
            route_param=route_param
        )

    id = item.id

    # Now we want the lock information and auth information
    auth_route = f"/registry{route_param.route}/auth/configuration"
    params = {
        "id": id
    }
    response = app_client.get(auth_route, params=params)

    # check success
    assert response.status_code == 200
    # parse access settings
    access_settings = AccessSettings.parse_obj(response.json())

    # construct the complete item
    return TypedItemBundle(
        id=id,
        item_payload=item,
        auth_payload=AuthTableEntry(
            id=id,
            access_settings=access_settings
        ),
        lock_payload=LockTableEntry(
            id=id,
            lock_information=LockInformation(
                locked=False,
                history=[]
            )
        )
    )


def write_random_item(app_client: TestClient) -> TypedItemBundle:
    """
    Creates a random item using the route params object and the model domain
    info examples. Used to quickly populate tables when we don't care about what
    is in there.

    Parameters
    ----------
    app_client : TestClient
        The fastAPI test client - make sure that the config override specifies
        the correct table that you want to write to

    Returns
    -------
    TypedItemBundle
        The item that was created typed as the item base - we don't really care
        about the type.
    """
    # select a random route
    route_param: RouteParameters = choice(route_params)

    # post the item
    return post_example_item(
        app_client=app_client,
        route_param=route_param
    )


def setup_dynamodb_registry_table(client: Any, table_name: str) -> None:
    """    setup_dynamob_registry_table
        Use boto client to produce dynamodb table which mirrors
        the registry table for testing

        Arguments
        ----------
        client: dynamodb boto client
            The mocked dynamo db client
        table_name : str
            The name of the table

        See Also (optional)
        --------

        Examples (optional)
        --------
    """

    # Setup dynamo db
    client.create_table(
        AttributeDefinitions=[
            {
                'AttributeName': 'id',
                'AttributeType': 'S'
            },
            {
                'AttributeName': 'item_subtype',
                'AttributeType': 'S'
            },
            {
                'AttributeName': 'updated_timestamp',
                'AttributeType': 'N'
            },
            {
                'AttributeName': 'created_timestamp',
                'AttributeType': 'N'
            },
            {
                'AttributeName': 'universal_partition_key',
                'AttributeType': 'S'
            },
            {
                'AttributeName': 'display_name',
                'AttributeType': 'S'
            },

        ],
        TableName=table_name,
        KeySchema=[
            {
                'AttributeName': 'id',
                'KeyType': 'HASH'
            }
        ],
        BillingMode='PAY_PER_REQUEST',
        GlobalSecondaryIndexes=[
            {
                'IndexName': 'item_subtype-updated_timestamp-index',
                'KeySchema': [
                    {
                        'AttributeName': 'item_subtype',
                        'KeyType': 'HASH'
                    },
                    {
                        'AttributeName': 'updated_timestamp',
                        'KeyType': 'RANGE'
                    },
                ],
                'Projection': {
                    'ProjectionType': 'ALL',
                },

            },
            {
                'IndexName': 'universal_partition_key-updated_timestamp-index',
                'KeySchema': [
                    {
                        'AttributeName': 'universal_partition_key',
                        'KeyType': 'HASH'
                    },
                    {
                        'AttributeName': 'updated_timestamp',
                        'KeyType': 'RANGE'
                    },
                ],
                'Projection': {
                    'ProjectionType': 'ALL',
                },

            },
            {
                'IndexName': 'item_subtype-created_timestamp-index',
                'KeySchema': [
                    {
                        'AttributeName': 'item_subtype',
                        'KeyType': 'HASH'
                    },
                    {
                        'AttributeName': 'created_timestamp',
                        'KeyType': 'RANGE'
                    },
                ],
                'Projection': {
                    'ProjectionType': 'ALL',
                },

            },
            {
                'IndexName': 'universal_partition_key-created_timestamp-index',
                'KeySchema': [
                    {
                        'AttributeName': 'universal_partition_key',
                        'KeyType': 'HASH'
                    },
                    {
                        'AttributeName': 'created_timestamp',
                        'KeyType': 'RANGE'
                    },
                ],
                'Projection': {
                    'ProjectionType': 'ALL',
                },

            },
            {
                'IndexName': 'item_subtype-display_name-index',
                'KeySchema': [
                    {
                        'AttributeName': 'item_subtype',
                        'KeyType': 'HASH'
                    },
                    {
                        'AttributeName': 'display_name',
                        'KeyType': 'RANGE'
                    },
                ],
                'Projection': {
                    'ProjectionType': 'ALL',
                },

            },
            {
                'IndexName': 'universal_partition_key-display_name-index',
                'KeySchema': [
                    {
                        'AttributeName': 'universal_partition_key',
                        'KeyType': 'HASH'
                    },
                    {
                        'AttributeName': 'display_name',
                        'KeyType': 'RANGE'
                    },
                ],
                'Projection': {
                    'ProjectionType': 'ALL',
                },

            },
        ],
    )


def create_dynamodb_table(ddb_client: Any, table_name: str = test_resource_table_name) -> None:
    """
    Given a dynamodb client and table name, will produce a dynamo table which is
    compatible with the registry.

    Parameters
    ----------
    ddb_client : Any
        The boto client
    table_name : str, optional
        The name of the table to create, by default test_registry_name
    """
    # Setup the mock registry table
    setup_dynamodb_registry_table(
        client=ddb_client,
        table_name=table_name
    )


def default_table_setup() -> None:
    ddb_client = boto3.client('dynamodb')
    setup_dynamodb_registry_table(
        client=ddb_client,
        table_name=test_resource_table_name
    )
    setup_dynamodb_registry_table(
        client=ddb_client,
        table_name=test_lock_table_name
    )
    setup_dynamodb_registry_table(
        client=ddb_client,
        table_name=test_auth_table_name
    )


def create_dynamo_tables(table_names: List[str]) -> None:
    """
    Creates a new set of dynamoDB tables in the mocked environment for each table name
    listed.

    Parameters
    ----------
    table_names : List[str]
        The list of table names - creates a resource/auth/lock table for each base name
    """
    for name in table_names:
        names = table_names_from_base(name)
        create_table_set(names)


def empty_table_setup(name: str) -> None:
    ddb_client = boto3.client('dynamodb')
    create_dynamo_tables(table_names=[name])


@dataclass
class TestTableNames():
    resource_table_name: str
    lock_table_name: str
    auth_table_name: str


def table_names_from_base(name: str) -> TestTableNames:
    return TestTableNames(
        auth_table_name=create_auth_table_name(name),
        resource_table_name=create_resource_table_name(name),
        lock_table_name=create_lock_table_name(name),
    )


def create_table_set(names: TestTableNames) -> None:
    ddb_client = boto3.client('dynamodb')
    create_dynamodb_table(ddb_client, names.resource_table_name)
    create_dynamodb_table(ddb_client, names.lock_table_name)
    create_dynamodb_table(ddb_client, names.auth_table_name)


def create_auth_table_name(base_name: str) -> str:
    return base_name + "auth"


def create_lock_table_name(base_name: str) -> str:
    return base_name + "lock"


def create_resource_table_name(base_name: str) -> str:
    return base_name + "resource"


def import_names_from_table_names(test_table_names: TestTableNames) -> TableNames:
    return TableNames(
        resource_table_name=test_table_names.resource_table_name,
        lock_table_name=test_table_names.lock_table_name,
        auth_table_name=test_table_names.auth_table_name,
    )


def import_names_from_base_name(name: str) -> TableNames:
    return import_names_from_table_names(
        table_names_from_base(name)
    )


def check_status_success_true(response: Response) -> None:
    """
    Asserts that:
    - the response has status code 200
    - the response is parsable as a StatusResponse
    - the response has status.success == True

    Parameters
    ----------
    response : Response
        The requests response
    """
    assert response.status_code == 200, f"Non 200 response code: {response.status_code}. Details: {response.text}"
    status_response = StatusResponse.parse_obj(response.json())
    assert status_response.status.success, f"Response {response} should have had status.success == True but was false."


def check_status_success_false(response: Response) -> None:
    """
    Asserts that:
    - the response has status code 200
    - the response is parsable as a StatusResponse
    - the response has status.success == False

    Parameters
    ----------
    response : Response
        The requests response
    """
    assert response.status_code == 200, f"Non 200 response code: {response.status_code}. Details: {response.text}"
    status_response = StatusResponse.parse_obj(response.json())
    assert not status_response.status.success, f"Response {response} should have had status.success == False but was true."


def check_exported_table_size(test_client: TestClient, expected_size: int) -> List[BundledItem]:
    """
    Uses the specified fastAPI test client to run an admin export of the current
    table, verifying that the number of items is equal to the expected size.

    Parameters
    ----------
    test_client : TestClient
        The FastAPI test client
    expected_size : int
        The expected size.

    Returns
    -------
    List[Dict[str, Any]]
        Returns the items
    """
    response = test_client.get(admin_export_endpoint)
    check_status_success_true(response)
    exported_response = RegistryExportResponse.parse_obj(response.json())
    exported_items = exported_response.items
    assert exported_items is not None
    assert len(exported_items) == expected_size
    return exported_items


def write_n_items_to_registry(test_client: TestClient, num_items: int) -> Dict[str, TypedItemBundle]:
    """
    Writes N items to the registry using the write random item helper function.
    Returns a map from the id of the created item to the typed item bundle.

    Parameters
    ----------
    test_client : TestClient
        The FastAPI test client to run against
    num_items : int
        The number of items to write

    Returns
    -------
    Dict[str, ItemBase]
        Map from ID -> created item
    """
    item_lookup: Dict[str, TypedItemBundle] = {}
    for _ in range(num_items):
        item = write_random_item(test_client)
        item_lookup[item.id] = item
    return item_lookup


def bundled_item_to_import_export_format(item: BundledItem) -> Dict[str, Any]:
    return json.loads(item.json(exclude_none=True))


def py_to_dict(item: BaseModel) -> Dict[str, Any]:
    return json.loads(item.json(exclude_none=True))


def assert_registry_state(test_client: TestClient, registry_state: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """
    Uses the admin export endpoint to check that the current state of the
    registry is exactly equivalent to the expected registry state (as a list of
    untyped items) - these items are in the bundled import/export format

    Parameters
    ----------
    test_client : TestClient
        The test client to use
    registry_state : List[Dict[str, Any]]
        The expected registry state (import/export format)

    Returns
    -------
    Dict[str, Dict[str, Any]]
        A mapping between id -> item in the exported items
    """
    # use an admin export to get current items and check size
    current_registry_items = check_exported_table_size(
        test_client=test_client,
        expected_size=len(registry_state)
    )

    # pull out the id -> item maps
    expected_id_map: Dict[str, Dict[str, Any]] = {}
    actual_id_map: Dict[str, Dict[str, Any]] = {}

    for item in registry_state:
        expected_id_map[item["id"]] = item
    for item in current_registry_items:
        actual_id_map[item.id] = bundled_item_to_import_export_format(item)

    # check ID sets are equal
    assert set(expected_id_map.keys()) == set(actual_id_map.keys())

    # check that each item is equal
    for expected_id, expected_item in expected_id_map.items():
        actual_item = actual_id_map[expected_id]
        assert filtered_none_deep_copy(
            actual_item) == filtered_none_deep_copy(expected_item)

    return actual_id_map


def produce_modified_items(input_items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    For a list of untyped items in the registry, updates the display name to
    indicate modification. Make sure that the dictionary has a display_name
    attribute. 

    NOTE this will change the actual items - it does not make a copy

    Parameters
    ----------
    input_items : List[Dict[str, Any]]
        The list of input items to change.

    Returns
    -------
    List[Dict[str, Any]]
        The output modified list
    """
    for input_item in input_items:
        input_item['item_payload']['display_name'] = input_item['item_payload']['display_name'] + " modified"
    return input_items


def bundled_item_dict_to_import_format(bundle_dict: Dict[str, TypedItemBundle]) -> List[Dict[str, Any]]:
    """
    Converts from the response format from setup_tables -> the recommended
    import payload format. This is to enable easy integration with the import
    request objects.

    Parameters
    ----------
    itemBase_dict : Dict[str, ItemBase]
        A mapping of id -> ItemBase 

    Returns
    -------
    List[Dict[str, Any]]
        A list of entries in this mapping, expressed as safe JSON dicts
    """
    return_dict_list = []

    for bundle in bundle_dict.values():
        return_dict_list.append(json.loads(bundle.json(exclude_none=True)))

    return return_dict_list


def produce_invalid_category_subtype_combination() -> Tuple[ItemCategory, ItemSubType]:
    """
    Uses the Model Type Map dictionary from the shared interfaces to make
    guesses of random category/subtype combinations until an invalid one is
    found.

    Returns
    -------
    Tuple[ItemCategory, ItemSubType]
        The item category and subtype combination which should cause a
        validation failure
    """
    result: Tuple[ItemCategory, ItemSubType]
    while True:
        # take a guess from the category/sub types
        result = (choice(list(ItemCategory)), choice(list(ItemSubType)))
        if result not in MODEL_TYPE_MAP.keys():
            break
    return result


def get_required_fields(pydantic_model: BaseModel) -> List[str]:
    """
    Given a pydantic model, iterates through the fields of the model itself (not
    an instance) and returns a list of keys which are required.

    Parameters
    ----------
    pydantic_model : BaseModel
        The pydantic model to explore

    Returns
    -------
    List[str]
        List of model KEYS which are required
    """
    # analyse the model to find keys which are required
    required_fields: List[str] = []

    # loop through key/field combinations
    for field_key, model_field in pydantic_model.__fields__.items():
        # add to list if required
        if model_field.required:
            required_fields.append(field_key)

    return required_fields


def get_item_subtype_route_params(item_subtype: ItemSubType) -> RouteParameters:
    """Given an item subtype, will source a its RouteParmeters
    Parameters
    ----------
    item_subtype : ItemSubType
        The desired Item subtype to source route parameters for
    Returns
    -------
    RouteParameters
        the routeparametrs for the desired item subtype
    """
    for item_route_params in route_params:
        if item_route_params.subtype == item_subtype:
            return item_route_params

    raise Exception(
        f"Was not able to source route parameters for desired item_subtype = {item_subtype}")


def get_other_category(this_category: ItemCategory) -> ItemCategory:
    """Given an ItemCategory, returns a different ItemCategory

    Parameters
    ----------
    this_category : str
        The ItemCategory to return a different ItemCategory of

    Returns
    -------
    ItemCategory
        The ItemCategory that differs to the inputted ItemCategory.
    """
    if this_category == "ENTITY":
        return ItemCategory("AGENT")
    else:
        return ItemCategory("ENTITY")


def get_other_subtype(this_subtype: ItemSubType) -> ItemSubType:
    """Given an ItemSubtype, returns a different ItemSubType.

    Parameters
    ----------
    this_subtype : ItemSubType
        The ItemSubType to return a different one of

    Returns
    -------
    ItemSubType
        An ItemSubType that differs from the inputted ItemSubType.
    """
    if this_subtype == "MODEL_RUN":
        return ItemSubType("PERSON")
    else:
        return ItemSubType("MODEL_RUN")


def create_many_types_of_items(client: TestClient, num_per_type: int = 1) -> None:
    """Creates items of all types. By default will create just 1 of each type,
    but can create more by setting the num_per_type parameter.

    Parameters
    ----------
    num_per_type : int, optional
        The amount of each type of item to create, by default 1. The total
        number of created items will then be num_per_type multiplied by the
        number of item types defined in config.RouteParameters
    """
    # For each item type
    for param_type in route_params:
        # create num_per_type amount of each.
        for _ in range(num_per_type):
            # create one of each type
            domain_info = param_type.model_examples.domain_info[0]

            # create route
            create_route = get_route(
                action=RouteActions.CREATE, params=param_type)

            client.post(create_route, json=json.loads(
                domain_info.json(exclude_none=True)))


def fetch_lock_history(client: TestClient, id: str, params: RouteParameters) -> LockHistoryResponse:
    """Fetches the lock history of an item

    Parameters
    ----------
    client : TestClient
        _description_
    id : the item's id to fetch the lock history of.
        _description_
    params : RouteParameters
        _description_

    Returns
    -------
    LockHistoryResponse
        _description_
    """
    curr_route = get_route(RouteActions.LOCK_HISTORY, params=params)
    request_params = {'id': id}
    lock_hist_resp = client.get(curr_route, params=request_params)
    assert lock_hist_resp.status_code == 200
    return LockHistoryResponse.parse_obj(lock_hist_resp.json())


def unlock_item(client: TestClient, id: str, params: RouteParameters) -> StatusResponse:
    curr_route = get_route(RouteActions.UNLOCK, params=params)
    json_payload = {
        "id": id,
        "reason": "testing unlock functionality"
    }

    unlock_resp = client.put(curr_route, json=json_payload)
    assert unlock_resp.status_code == 200
    unlock_resp = StatusResponse.parse_obj(unlock_resp.json())
    return unlock_resp


def get_model_example(item_subtype: ItemSubType) -> DomainInfoBase:
    params = get_item_subtype_route_params(item_subtype=item_subtype)
    return params.model_examples.domain_info[0]


def update_item_from_domain_info(client: TestClient, id: str, subtype: ItemSubType, updated_domain_info: DomainInfoBase) -> Response:

    params = get_item_subtype_route_params(item_subtype=subtype)
    update_route = get_route(action=RouteActions.UPDATE, params=params)
    update_item_resp = client.put(
        update_route,
        params={'id': id, 'reason': "testin' update functionality"},
        json=py_to_dict(updated_domain_info)
    )
    return update_item_resp


def update_item(client: TestClient, id: str, params: RouteParameters) -> Response:
    reason = "fake reason"
    updated_domain_info = params.model_examples.domain_info[1]
    update_route = get_route(action=RouteActions.UPDATE, params=params)
    update_item_resp = client.put(
        update_route,
        params={'id': id, 'reason': reason},
        json=py_to_dict(updated_domain_info)
    )
    return update_item_resp


def get_lock_status(client: TestClient, id: str, params: RouteParameters) -> LockStatusResponse:
    request_params = {"id": id}
    curr_route = get_route(RouteActions.LOCKED, params=params)
    lock_status_resp = client.get(curr_route, params=request_params)
    assert lock_status_resp.status_code == 200
    lock_status_resp = LockStatusResponse.parse_obj(lock_status_resp.json())
    return lock_status_resp


def lock_item(client: TestClient, id: str, params: RouteParameters) -> StatusResponse:
    curr_route = get_route(RouteActions.LOCK, params=params)

    json_payload = {
        "id": id,
        "reason": "testing lock functionality"
    }

    lock_resp = client.put(curr_route, json=json_payload)
    assert lock_resp.status_code == 200
    lock_resp = StatusResponse.parse_obj(lock_resp.json())
    return lock_resp


def create_one_item_successfully(client: TestClient, params: RouteParameters) -> ItemBase:

    # get an example object out from the examples in params.
    example_domain_info = params.model_examples.domain_info[0]
    create_resp = create_item_from_domain_info(
        client=client, domain_info=example_domain_info, params=params)
    assert create_resp.status_code == 200, f"create_resp.status_code: {create_resp.status_code}. Details: {create_resp.json()}"
    response_model = params.typing_information.create_response
    assert response_model, f"create_response not defined for {params.subtype}"
    create_resp: GenericCreateResponse = response_model.parse_obj(
        create_resp.json())
    assert create_resp.status.success
    created_item = create_resp.created_item
    assert created_item
    return created_item


def create_item_from_domain_info(client: TestClient, domain_info: DomainInfoBase, params: RouteParameters) -> Response:
    curr_route = get_route(RouteActions.CREATE, params=params)
    create_resp = client.post(
        curr_route, json=json.loads(domain_info.json()))
    return create_resp


def create_item_from_domain_info_successfully(client: TestClient, domain_info: DomainInfoBase, params: RouteParameters) -> ItemBase:
    create_resp = create_item_from_domain_info(
        client=client, domain_info=domain_info, params=params)
    assert create_resp.status_code == 200, "Create response was not 200. Details: " + create_resp.text
    response_model = params.typing_information.create_response
    assert response_model, f"Typing information for {params.subtype} does not have a create response model."
    create_resp: GenericCreateResponse = response_model.parse_obj(
        create_resp.json())
    assert create_resp.status.success
    created_item = create_resp.created_item
    assert created_item
    return created_item


def create_item_from_domain_info_not_successfully(client: TestClient, domain_info: DomainInfoBase, params: RouteParameters) -> None:
    """Used when status 200 OK is returned, but status success is false.
    """
    create_resp = create_item_from_domain_info(
        client=client, domain_info=domain_info, params=params)
    assert create_resp.status_code == 200, "Create response was not 200. Details: " + create_resp.text
    response_model = params.typing_information.create_response
    assert response_model, f"Typing information for {params.subtype} does not have a create response model."
    create_resp: GenericCreateResponse = response_model.parse_obj(
        create_resp.json())
    assert not create_resp.status.success
    

class TestingUser():

    groups: List[str] = []
    name: str

    def __init__(self, name: str):
        self.name = name

    def addToGroup(self, group: str) -> None:
        self.groups.append(group)


def fetch_item_basic(client: TestClient, params: RouteParameters, id: str,) -> Any:
    fetch_route = get_route(RouteActions.FETCH, params=params)
    return client.get(fetch_route, params={'id': id})


def evaluate_access(client: TestClient, id: str, params: RouteParameters) -> DescribeAccessResponse:
    curr_route = get_route(RouteActions.AUTH_EVALUATE, params=params)
    request_params = {'id': id}
    evaluate_access_resp = client.get(curr_route, params=request_params)
    assert evaluate_access_resp.status_code == 200
    return DescribeAccessResponse.parse_obj(evaluate_access_resp.json())


def get_auth_roles(client: TestClient, params: RouteParameters) -> AuthRolesResponse:
    curr_route = get_route(RouteActions.AUTH_ROLES, params=params)
    auth_roles_resp = client.get(curr_route)
    assert auth_roles_resp.status_code == 200
    return AuthRolesResponse.parse_obj(auth_roles_resp.json())


def put_auth_config(client: TestClient, id: str, auth_payload: Dict[str, Any], params: RouteParameters) -> StatusResponse:
    curr_route = get_route(RouteActions.AUTH_CONFIGURATION_PUT, params=params)
    request_params = {'id': id}
    auth_config_put_resp = client.put(
        curr_route, params=request_params, json=auth_payload)
    try:
        assert auth_config_put_resp.status_code == 200
    except:
        if auth_config_put_resp.status_code == 401:
            raise PermissionError(
                "user does not have authorisation to write auth config to item")
        else:
            raise AssertionError(
                f"Non 200 status code received from put auth response. {auth_config_put_resp}")
    return StatusResponse.parse_obj(auth_config_put_resp.json())


def get_auth_config(client: TestClient, id: str, params: RouteParameters) -> AccessSettings:
    curr_route = get_route(RouteActions.AUTH_CONFIGURATION_GET, params=params)
    request_params = {'id': id}
    auth_config_get_resp = client.get(curr_route, params=request_params)

    try:
        assert auth_config_get_resp.status_code == 200
    except:
        if auth_config_get_resp.status_code == 401:
            raise PermissionError(
                "User does not have authorisation to get auth config for item")
        else:
            raise AssertionError(
                f"Non 200 status code received from get auth response. {auth_config_get_resp}")

    return AccessSettings.parse_obj(auth_config_get_resp.json())


def set_group_access_roles(client: TestClient, item: ItemBase, params: RouteParameters, group_access_roles: Dict[str, List[str]]) -> None:
    """Given desired group access roles for an item, will update the items auth
    configuration to have these group access roles.

    Parameters
    ----------
    client : TestClient
        _description_
    item : ItemBase
        The item to update the group access roles of
    params : RouteParameters
        _description_
    group_access_roles : Dict[str, List[str]]
        The updated access roles. A dict of Groups to the roles for that group.
    """
    original_auth = get_auth_config(client=client, id=item.id, params=params)
    new_auth = original_auth.dict()
    new_auth["groups"] = group_access_roles
    put_auth_config(client=client, id=item.id,
                    auth_payload=new_auth, params=params)


def set_general_access_roles(client: TestClient, item: ItemBase, params: RouteParameters, general_access_roles: List[str]) -> None:
    """Given an item and desired general access roles, will update the items
    auth config to have these general access roles

    Parameters
    ----------
    client : TestClient
        _description_
    item : ItemBase
        The item to apply general access roles to
    params : RouteParameters
        _description_
    general_access_roles : List[str]
        the desired access roles for the item
    """
    original_auth = get_auth_config(client=client, id=item.id, params=params)
    new_auth = original_auth.dict()
    new_auth["general"] = general_access_roles
    put_auth_config(client=client, id=item.id,
                    auth_payload=new_auth, params=params)


def give_general_read_write_access(client: TestClient, item: ItemBase, params: RouteParameters) -> None:
    """Give general read and write access to the provided item

    Parameters
    ----------
    client : TestClient
        _description_
    item : ItemBase
        _description_
    params : RouteParameters
        _description_
    """
    set_general_access_roles(client=client, item=item, params=params, general_access_roles=[
                             'metadata-read', 'metadata-write'])


def remove_general_access_from_item(client: TestClient, item: ItemBase, params: RouteParameters) -> None:
    """removes general access reasd and write form the provided item.

    Parameters
    ----------
    client : TestClient
        _description_
    item : ItemBase
        _description_
    params : RouteParameters
        _description_
    """
    set_general_access_roles(client=client, item=item,
                             params=params, general_access_roles=[])


def give_general_read_access(client: TestClient, item: ItemBase, params: RouteParameters) -> None:
    """Gives general access for metadata read for the provided item

    Parameters
    ----------
    client : TestClient
        _description_
    item : ItemBase
        _description_
    params : RouteParameters
        _description_
    """
    set_general_access_roles(
        client=client, item=item, params=params, general_access_roles=['metadata-read'])


def generate_mocked_user_group_set(user_groups: List[str]) -> Any:
    """Provided the expected user groups to be returned by the function
    get_user_group_id_set" this returns the a used to mock
    get_user_group_id_set" function to prevent interaction with the auth
    api.

    Parameters
    ----------
    user_groups : List[str]
        The user groups that the mocked function should return when it is called
        (perhaps in lower levels).

    Returns
    -------
    Any
        A function that mocks the "get_user_group_id_set" funtion to return the
        expected user groups
    """
    def mocked_get_user_group_id_set(user: TestingUser, config: Any, service_proxy: bool = False) -> Set[str]:
        return set(user_groups)
    return mocked_get_user_group_id_set


def mock_user_group_set(user_groups: List[str], monkeypatch: Any) -> None:
    """
    Used to setup the mocked "get_user_group_id_set" function to return the expected user groups.
    """
    import helpers.action_helpers
    import routes.registry_general.registry_general
    mocked_function = generate_mocked_user_group_set(user_groups)
    # maybe not using module where it is defined, but where it is used
    monkeypatch.setattr(helpers.action_helpers,
                        "get_user_group_id_set", mocked_function)
    monkeypatch.setattr(routes.registry_general.registry_general,
                        "get_user_group_id_set", mocked_function)


def make_protected_role_user_specific(username: str) -> Any:
    def make_protected_role() -> ProtectedRole:
        # Creates override for the role protected user dependency
        return ProtectedRole(
            access_roles=['test-role'],
            user=User(
                username=username,
                roles=['test-role'],
                access_token="faketoken1234",
                email=username
            )
        )
    return make_protected_role


def set_read_write_protected_role(app: Any, username: Optional[str] = None, protected_role_callable: Optional[Any] = None) -> None:
    """Sets a user to be the actor of any api endpoint calls and gives them
    general read and write into the registry. Requires one of the user's
    username or protected roles.

    Parameters
    ----------
    app : Any
        _description_
    username : Optional[str], optional
        username of the user, by default None
    protected_role_callable : Optional[Any], optional
        The users protected role, by default None

    Raises
    ------
    Exception
        _description_
    """
    if protected_role_callable is not None:
        pass
    elif username is not None:
        protected_role_callable = make_protected_role_user_specific(
            username=username)
    else:
        raise Exception(
            "Require a username or protected role to set protected roles.")

    app.dependency_overrides[read_user_protected_role_dependency] = protected_role_callable
    app.dependency_overrides[read_write_user_protected_role_dependency] = protected_role_callable


def set_read_protected_role(app: Any, username: Optional[str] = None, protected_role_callable: Optional[Any] = None) -> None:
    """Sets a user to be the actor of any api endpoint calls and gives them
    general read into the registry. Requires one of the user's username or
    protected roles.

    Parameters
    ----------
    app : Any
        _description_
    username : Optional[str], optional
        username of the user, by default None
    protected_role_callable : Optional[Any], optional
        The users protected role, by default None

    Raises
    ------
    Exception
        _description_
    """
    if protected_role_callable is not None:
        pass
    elif username is not None:
        protected_role_callable = make_protected_role_user_specific(
            username=username)
    else:
        raise Exception(
            "Require a username or protected role to set protected roles.")

    app.dependency_overrides[read_user_protected_role_dependency] = protected_role_callable


def accessible_via_registry_list(client: TestClient, item_id: str) -> bool:
    # returns true if an item is accessible in the registry via list endpoint.
    # used to check the registry general list respects authorisation rights.
    # could be sped up by not doing exhaustive search then checking, but by doing search by pages
    # and possibly returning early if item is found. Not many items in these tests anyway.

    return item_id in set(ItemBase.parse_obj(item).id for item in general_list_exhaust(client=client))


def check_equal_models(m1: BaseModel, m2: BaseModel) -> None:
    """

    Checks that the two pydantic models are equal by converting to dictionary,
    dropping None values and deep comparing

    Parameters
    ----------
    m1 : BaseModel
        Model 1
    m2 : BaseModel
        Model 2
    """
    assert filtered_none_deep_copy(py_to_dict(
        m1)) == filtered_none_deep_copy(py_to_dict(m2))


def get_timestamp() -> int:
    """

    Gets current unix timestamp

    Returns
    -------
    int
        Timestamp
    """
    return int(datetime.now().timestamp())


def check_current_with_buffer(ts: int, buffer: int = 5) -> None:
    """

    Checks that the desired timestamp is within buffer  +/- of current timestamp

    Parameters
    ----------
    ts : int
        The target timestamp
    buffer : int, optional
        The seconds buffer, by default 5
    """
    current = get_timestamp()
    assert ts > current - buffer and ts < current + buffer


