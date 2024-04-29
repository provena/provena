import tests.env_setup
import pytest  # type: ignore
from moto import mock_dynamodb  # type: ignore
import json
import pydantic
from dependencies.dependencies import read_user_protected_role_dependency, read_write_user_protected_role_dependency, admin_user_protected_role_dependency
from fastapi.testclient import TestClient
from main import app, UI_SCHEMA_OVERRIDES
from ProvenaSharedFunctionality.Registry.TestConfig import ModelExamples
from ProvenaInterfaces.RegistryModels import *
from ProvenaInterfaces.RegistryAPI import *
from KeycloakFastAPI.Dependencies import User, ProtectedRole
from config import Config, base_config, get_settings
from typing import Generator, Any, Dict
from tests.helpers import *
from tests.config import *
import os

client = TestClient(app)


# test wide scope for creating config

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
        auth_table_name=test_auth_table_name,
        lock_table_name=test_lock_table_name,
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


@pytest.fixture(scope="session", autouse=True)
def provide_perform_validation_config() -> Config:
    return Config(
        # no user auth testing!
        enforce_user_auth=False,
        enforce_special_proxy_roles=False,
        auth_api_endpoint="",
        job_api_endpoint="",

        keycloak_endpoint=base_config.keycloak_endpoint,
        stage=base_config.stage,
        registry_table_name=test_resource_table_name,
        auth_table_name=test_auth_table_name,
        lock_table_name=test_lock_table_name,
        handle_api_endpoint="",
        service_account_secret_arn="",
        mock_handle=True,
        perform_validation=True,
        # dont perform user link validation
        enforce_user_links=False,
        test_mode=True
    )


@pytest.fixture(scope="session", autouse=True)
def provide_enforce_user_auth_config() -> Config:
    return Config(
        # no user auth testing!
        enforce_user_auth=True,  # Perform user auth!
        enforce_special_proxy_roles=False,
        auth_api_endpoint="",
        job_api_endpoint="",

        keycloak_endpoint=base_config.keycloak_endpoint,
        stage=base_config.stage,
        registry_table_name=test_resource_table_name,
        auth_table_name=test_auth_table_name,
        lock_table_name=test_lock_table_name,
        handle_api_endpoint="",
        service_account_secret_arn="",
        mock_handle=True,
        perform_validation=False,
        # dont perform user link validation
        enforce_user_links=False,
        test_mode=True
    )

# for each function, override settings and clear deps at end


@pytest.fixture(scope="function", autouse=True)
def override_config_dependency(provide_global_config: Config) -> Generator:
    app.dependency_overrides[get_settings] = lambda: provide_global_config
    yield
    app.dependency_overrides = {}


@pytest.fixture(scope="function")
def override_perform_validation_config_dependency(provide_perform_validation_config: Config) -> Generator:
    app.dependency_overrides[get_settings] = lambda: provide_perform_validation_config
    yield
    app.dependency_overrides = {}


@pytest.fixture(scope="function")
def override_enforce_user_auth_dependency(provide_enforce_user_auth_config: Config) -> Generator:
    app.dependency_overrides[get_settings] = lambda: provide_enforce_user_auth_config
    yield
    app.dependency_overrides = {}


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


@pytest.fixture(scope='function')
def aws_credentials() -> None:
    """Mocked AWS Credentials for moto."""
    os.environ['AWS_ACCESS_KEY_ID'] = 'testing'
    os.environ['AWS_SECRET_ACCESS_KEY'] = 'testing'
    os.environ['AWS_SECURITY_TOKEN'] = 'testing'
    os.environ['AWS_SESSION_TOKEN'] = 'testing'
    os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'


def test_health_check() -> None:
    # Checks that the health check endpoint responds
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Health check successful."}


async def user_general_dependency_override() -> User:
    # Creates an override for user dependency
    return User(username=test_email, roles=['test-role'], access_token="faketoken1234", email=test_email)

# use to 'make more users'


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


@pytest.mark.parametrize("route", route_params, ids=make_specialised_list("Schema"))
def test_schema(route: RouteParameters) -> None:
    # Checks that the schema endpoint provides valid
    # Json and that it matches the file contents exactly

    # Override the auth dependency
    app.dependency_overrides[read_user_protected_role_dependency] = user_protected_dependency_override

    curr_route = get_route(RouteActions.SCHEMA, params=route)
    response = client.get(curr_route)
    assert response.status_code == 200

    # Retrieve the json dat a from json_schema field of response
    json_content = response.json()['json_schema']

    # Check that it is valid
    assert json_content, "JSON object was none"

    # Check that it can be serialized and deserialized
    assert json.loads(json.dumps(json_content)) == json_content
    # TODO
    # Schema test could be improved


@mock_dynamodb
@pytest.mark.parametrize("params", route_params, ids=make_specialised_list("General list"))
def test_general_list(params: RouteParameters) -> None:
    # Checks that the general list API endpoint returns sensible results
    # from a mocked dynamodb table

    # Override the auth dependency
    app.dependency_overrides[read_user_protected_role_dependency] = user_protected_dependency_override
    default_table_setup()

    # get all items from the general list endpoint
    items = general_list_exhaust(client)

    # should be zero items
    assert len(items) == 0

    # now add items to the table and test if the list comes
    # back with > 0 items

    # add items to the table via create function
    app.dependency_overrides[read_write_user_protected_role_dependency] = user_protected_dependency_override

    # load file for sending to the create API
    input_items: List[DomainInfoBase] = params.model_examples.domain_info

    curr_route = get_route(action=RouteActions.CREATE, params=params)
    # create items from parsed file
    for domain_info_example in input_items:
        # Create the item
        response = client.post(
            curr_route, json=json.loads(domain_info_example.json()))
        assert response.status_code == 200
        json_content = response.json()
        # Check that it is valid
        assert json_content, "JSON object was none"

    items = general_list_exhaust(client)
    assert len(items) == len(input_items), "Incorrect number of entries"

    for item in items:
        item_obj = ItemBase.parse_obj(item)
        assert item_obj.record_type == RecordType.COMPLETE_ITEM


def create_dynamodb_table_with_data(model_examples: ModelExamples, ddb_client: Any) -> None:
    default_table_setup()

    model_params = get_item_subtype_route_params(
        ItemSubType.MODEL
    )
    curr_route = get_route(action=RouteActions.CREATE, params=model_params)
    # create items from parsed file
    for domain_info_model in model_examples.domain_info:
        response = client.post(
            curr_route, json=json.loads(domain_info_model.json()))
        assert response.status_code == 200
        json_content = response.json()
        # Check that it is valid
        assert json_content, "JSON object was none"


@mock_dynamodb
@pytest.mark.parametrize("params", route_params, ids=make_specialised_list("Create"))
def test_create(params: RouteParameters) -> None:
    # Add items to the registry for type and subtype based on file inputs and route params

    # Override the auth dependency
    app.dependency_overrides[read_user_protected_role_dependency] = user_protected_dependency_override
    app.dependency_overrides[read_write_user_protected_role_dependency] = user_protected_dependency_override

    default_table_setup()

    # print(route)
    # load file to use to create
    route = params.route
    input_items: List[DomainInfoBase] = params.model_examples.domain_info
    response_model = params.typing_information.create_response
    assert response_model
    item_model = params.typing_information.item_model

    curr_route = get_route(action=RouteActions.CREATE, params=params)

    # create items from parsed file
    for domain_info_object in input_items:
        # Create safe serialisation
        safe_serialisation = json.loads(domain_info_object.json())

        # Try to post object to appropriate endpoint
        response = client.post(curr_route, json=safe_serialisation)

        assert response.status_code == 200, f"Non 200 response code: {response.status_code}. Details: {response.json()}"

        # parse response using special response format typed as GenericCreateResponse
        create_response: GenericCreateResponse = response_model.parse_obj(
            response.json())

        # Check that it is valid
        assert create_response, "JSON object was none"

        # Since did not throw error it means that the response parsed successfully
        # Check that the response was successful
        assert create_response.status.success, "Response for create had success false"

        # Check that the item is present
        assert create_response.created_item, "Response was successful but had no item"

        # Make sure item is parsable as item model type
        specialised_response: ItemBase = item_model.parse_obj(
            create_response.dict()['created_item'])

        # Ensure domain specific fields are equal in response object
        safe_json = json.loads(specialised_response.json())
        for k, v in json.loads(domain_info_object.json()).items():
            assert k in safe_json.keys()
            assert safe_json[k] == v


@mock_dynamodb
@pytest.mark.parametrize("params", route_params, ids=make_specialised_list("Create Invalid"))
def test_create_invalid_object(params: RouteParameters) -> None:

    # Override the auth dependency
    app.dependency_overrides[read_user_protected_role_dependency] = user_protected_dependency_override
    app.dependency_overrides[read_write_user_protected_role_dependency] = user_protected_dependency_override

    # Set up DB
    default_table_setup()

    route = params.route

    # Domain info of input items for uploading
    input_domain_info: DomainInfoBase = params.model_examples.domain_info[0]
    input_domain_input_dict = json.loads(input_domain_info.json())

    # Invalidate input by removing field required for all items
    invalid_input_domain_info = input_domain_input_dict.pop(
        "display_name")  # invalidate the input

    curr_route = get_route(action=RouteActions.CREATE, params=params)
    response = client.post(curr_route, json=invalid_input_domain_info)
    assert response.status_code == 422, "Invalid data should not be written!!!"


@mock_dynamodb
@pytest.mark.parametrize("params", route_params, ids=make_specialised_list("Fetch"))
def test_fetch(params: RouteParameters) -> None:
    # Add items to the registry for type and subtype based on file inputs and route params

    # Override the auth dependency
    app.dependency_overrides[read_user_protected_role_dependency] = user_protected_dependency_override
    app.dependency_overrides[read_write_user_protected_role_dependency] = user_protected_dependency_override

    default_table_setup()

    # Try fetching with invalid ID
    # Should respond with 200 and status.success == False
    fetch_endpoint = get_route(action=RouteActions.FETCH, params=params)
    invalid_id = "fakeid1234"
    response = client.get(fetch_endpoint, params={
        'id': invalid_id
    })

    # check status
    assert response.status_code == 200, "Non 200 code from fetch"

    json_content = response.json()
    parsed: GenericFetchResponse = params.typing_information.fetch_response.parse_obj(
        json_content)

    # check it failed
    assert not parsed.status.success, "Invalid ID responded successful"

    # seed a new item
    route = params.route
    seed_endpoint = get_route(action=RouteActions.SEED, params=params)

    response = client.post(seed_endpoint)
    assert response.status_code == 200
    parsed_response = GenericSeedResponse.parse_obj(response.json())
    assert parsed_response.status.success, "Non successful seed of item"
    assert parsed_response.seeded_item
    seeded_id = parsed_response.seeded_item.id
    assert parsed_response.seeded_item.record_type == RecordType.SEED_ITEM

    # fetch the seeded item id without including seed allowed parameter
    fetch_endpoint = get_route(action=RouteActions.FETCH, params=params)
    response = client.get(fetch_endpoint,
                          params={
                              'id': seeded_id
                          })
    assert response.status_code == 200
    parsed_response = GenericFetchResponse.parse_obj(response.json())
    assert not parsed_response.status.success, "Seeded item was returned successfully without seed_allowed flag!"

    # fetch the seeded item id including seed allowed parameter
    response = client.get(fetch_endpoint,
                          params={
                              'id': seeded_id,
                              'seed_allowed': "true"
                          })
    assert response.status_code == 200
    parsed_response = GenericFetchResponse.parse_obj(response.json())
    assert parsed_response.status.success, "Seeded item was not returned successfully with seed_allowed flag!"
    assert parsed_response.item_is_seed, "The seeded item was not marked as a seed when fetched"
    assert parsed_response.item
    assert isinstance(parsed_response.item, SeededItem)
    assert parsed_response.item.id == seeded_id, "The returned seeded item had non matching ID"

    # create a new item
    input_items: List[DomainInfoBase] = params.model_examples.domain_info
    response_model = params.typing_information.create_response
    assert response_model
    item_model = params.typing_information.item_model

    create_endpoint = get_route(action=RouteActions.CREATE, params=params)

    # create items from parsed file
    for domain_info_object in input_items:
        # Create safe serialisation
        safe_serialisation = json.loads(domain_info_object.json())

        # Try to post object to appropriate endpoint
        response = client.post(create_endpoint, json=safe_serialisation)

        assert response.status_code == 200

        # parse response using special response format typed as GenericCreateResponse
        create_response: GenericCreateResponse = response_model.parse_obj(
            response.json())

        # Check that it is valid
        assert create_response, "JSON object was none"

        # Since did not throw error it means that the response parsed successfully
        # Check that the response was successful
        assert create_response.status.success, "Response for create had success false"

        # Check that the item is present
        item = create_response.created_item
        assert item, "Response was successful but had no item"
        parsed_item: ItemBase = item_model.parse_obj(item)
        # fetch the item
        handle: str = parsed_item.id
        response = client.get(fetch_endpoint, params={
            'id': handle
        })
        # check status
        assert response.status_code == 200, "Non 200 code from fetch"

        json_content = response.json()
        parsed_fetch: GenericFetchResponse = params.typing_information.fetch_response.parse_obj(
            json_content)

        # check it failed
        assert parsed_fetch.status.success, "Created item could not be fetched"

        # check that item seems to match
        assert parsed_fetch.item == create_response.created_item


@mock_dynamodb
@pytest.mark.parametrize("params", route_params, ids=make_specialised_list("Invalid fetch"))
def test_fetch_invalid_type_for_id(params: RouteParameters) -> None:
    """
    Test for correct behavior when attempting to fetch an item with incorrect type.
    1. Seed item of this param type
    2. Seed item of other param type
    3. Fetch an item type using the handle from the other and assert correct error response
    """

    app.dependency_overrides[read_user_protected_role_dependency] = user_protected_dependency_override
    app.dependency_overrides[read_write_user_protected_role_dependency] = user_protected_dependency_override

    default_table_setup()

    # 1. Seed item of this param type
    seed_endpoint = get_route(action=RouteActions.SEED, params=params)
    response = client.post(seed_endpoint)

    assert response.status_code == 200, f"Status code was {response.status_code}."
    seed_resp = GenericSeedResponse.parse_obj(response.json())
    assert seed_resp.status.success
    item = seed_resp.seeded_item
    assert item
    # ensure returned item type form api is correct
    assert item.item_category == params.category
    assert item.item_subtype == params.subtype

    # 2. Seed item of other param type

    # find other item type randomly until category and subtype do not match
    found = False
    lim = 20
    count = 0
    other_params: RouteParameters
    while not found and count < lim:
        other = choice(route_params)
        # make sure it is not a special proxy route, and its category and subtype are different
        if other.category != params.category and other.subtype != params.subtype and not other.use_special_proxy_modify_routes:
            found = True
            other_params = other
            break
        count += 1

    if not found:
        assert False, f"Couldn't find a distinct route parameter to compare against for cat/subtype {params.category}/{params.subtype} in {lim} random attempts."
    assert other_params

    seed_route = get_route(action=RouteActions.SEED, params=other_params)
    response = client.post(seed_route)

    assert response.status_code == 200, f"Status code was {response.status_code}."
    seed_resp = GenericSeedResponse.parse_obj(response.json())
    assert seed_resp.status.success
    item = seed_resp.seeded_item
    assert item
    other_param_handle = item.id
    # ensure returned item type from seeding another item type is not equal to type of this test
    assert item.item_category != params.category
    assert item.item_subtype != params.subtype

    # fetch first seeded item using handle of second seeded item and ensure http 400
    fetch_route = get_route(action=RouteActions.FETCH, params=params)
    response = client.get(fetch_route, params={
        'id': other_param_handle,
        'seed_allowed': "true"
    })
    assert response.status_code == 400


@mock_dynamodb
@pytest.mark.parametrize("params", route_params, ids=make_specialised_list("UI Schema"))
def test_ui_schema(params: RouteParameters) -> None:
    # Check that the ui schema delivered is equal to the configured schemas

    # Override the auth dependency
    app.dependency_overrides[read_user_protected_role_dependency] = user_protected_dependency_override

    # Make a request to ui_schema endpoint
    ui_route = get_route(action=RouteActions.UI_SCHEMA, params=params)
    response = client.get(ui_route)

    assert response.status_code == 200, f"Status code was {response.status_code}."

    # Parse as UI response
    ui_response = UiSchemaResponse.parse_obj(response.json())

    # Check successful
    assert ui_response.status.success, "Had non successful ui schema response"

    # Check that the value equals the override
    assert ui_response.ui_schema == UI_SCHEMA_OVERRIDES[params.typing_information.item_model]


@mock_dynamodb
@pytest.mark.parametrize("params", route_params, ids=make_specialised_list("Seed"))
def test_seed(params: RouteParameters) -> None:

    # Override the auth dependency
    app.dependency_overrides[read_user_protected_role_dependency] = user_protected_dependency_override
    app.dependency_overrides[read_write_user_protected_role_dependency] = user_protected_dependency_override

    default_table_setup()

    seed_route = get_route(action=RouteActions.SEED, params=params)
    response = client.post(seed_route)

    assert response.status_code == 200, f"Status code was {response.status_code}."

    seed_resp = GenericSeedResponse.parse_obj(response.json())
    # Ensure successful seeding
    assert seed_resp.status.success
    item = seed_resp.seeded_item
    assert item

    # ensure returned item type form api is correct
    assert item.item_category == params.category
    assert item.item_subtype == params.subtype
    assert item.record_type == RecordType.SEED_ITEM


@mock_dynamodb
@pytest.mark.parametrize("params", route_params, ids=make_specialised_list("delete-seed-item"))
def test_delete_seeded_item(params: RouteParameters) -> None:
    """
    Order of operations:
    1. Seed an item to be deleted
    2. Fetch to ensure it is in the db
    3. Send delete request
    4. Assert successful deletion by fetching and ensuring the fetch fails.

    To prevent too much re writing/copying code, this delete test relies on (perhaps too many) other endpoints.
    Albeit the other endpoints do have focussed tests enabling failure tracing.
    """

    app.dependency_overrides[read_user_protected_role_dependency] = user_protected_dependency_override
    app.dependency_overrides[read_write_user_protected_role_dependency] = user_protected_dependency_override
    # admin for deleting
    app.dependency_overrides[admin_user_protected_role_dependency] = user_protected_dependency_override

    default_table_setup()

    fetch_response_model = params.typing_information.fetch_response
    seed_response_model = params.typing_information.seed_response
    assert seed_response_model

    # 1. Seed
    seed_route = get_route(action=RouteActions.SEED, params=params)
    seed_response = client.post(seed_route)
    # assert successful seeding
    assert seed_response.status_code == 200, f"Status code was {seed_response.status_code}."
    seed_resp: GenericSeedResponse = seed_response_model.parse_obj(
        seed_response.json())
    assert seed_resp.status.success
    item = seed_resp.seeded_item
    assert item
    assert item.item_category == params.category
    assert item.item_subtype == params.subtype

    item_handle = item.id

    fetch_params: Dict[str, Any] = {
        "id": item_handle,
        "seed_allowed": True
    }

    # 2) Fetch item and ensure it is there
    fetch_route = get_route(action=RouteActions.FETCH, params=params)
    fetch_response = client.get(
        fetch_route,
        params=fetch_params,
    )
    assert fetch_response.status_code == 200
    fetch_response: GenericFetchResponse = fetch_response_model.parse_obj(
        fetch_response.json())
    assert fetch_response.status.success
    # change for when creating and deleting a full item
    assert fetch_response.item_is_seed

    fetched_item = fetch_response.item
    assert fetched_item
    assert fetched_item.item_category == params.category
    assert fetched_item.item_subtype == params.subtype

    # 3) delete item
    delete_params = {"id": item_handle}

    delete_route = get_route(action=RouteActions.DELETE, params=params)
    delete_response = client.delete(
        delete_route,
        params=delete_params
    )
    assert delete_response.status_code == 200, f"Status code was {delete_response.status_code}."
    delete_response: StatusResponse = StatusResponse.parse_obj(
        delete_response.json())
    # True even if no item existed to be deleted
    assert delete_response.status.success

    # 4. Attempt to fetch item and ensure it was deleted
    fetch_response = client.get(
        fetch_route,
        params=fetch_params,
    )
    assert fetch_response.status_code == 200
    fetch_response: GenericFetchResponse = fetch_response_model.parse_obj(
        fetch_response.json())
    assert fetch_response.status.success == False, "Item should have been deleted, but is successfully fetched instead."


@mock_dynamodb
@pytest.mark.parametrize("params", route_params, ids=make_specialised_list("delete-non-seed-item"))
def test_delete_nonseed_item(params: RouteParameters) -> None:
    """
    Order of operations:
    1. Create an item to be deleted
    2. Fetch to ensure it is in the db
    3. Send delete request
    4. Assert successful deletion by fetching and ensuring the fetch fails.

    To prevent too much re writing/copying code, this delete test relies on (perhaps too many) other endpoints.
    Albeit the other endpoints do have focussed tests.
    """

    app.dependency_overrides[read_user_protected_role_dependency] = user_protected_dependency_override
    app.dependency_overrides[read_write_user_protected_role_dependency] = user_protected_dependency_override
    # admin for deletion
    app.dependency_overrides[admin_user_protected_role_dependency] = user_protected_dependency_override

    default_table_setup()

    # load file to use to create
    route = params.route
    input_items: List[DomainInfoBase] = params.model_examples.domain_info
    create_response_model = params.typing_information.create_response
    assert create_response_model
    fetch_response_model = params.typing_information.fetch_response
    item_model = params.typing_information.item_model

    create_route = get_route(action=RouteActions.CREATE, params=params)
    fetch_route = get_route(action=RouteActions.FETCH, params=params)
    delete_route = get_route(action=RouteActions.DELETE, params=params)

    # create items from parsed file
    for domain_info_object in input_items:
        # Create safe serialisation
        safe_serialisation = json.loads(domain_info_object.json())
        response = client.post(create_route, json=safe_serialisation)

        assert response.status_code == 200
        create_response: GenericCreateResponse = create_response_model.parse_obj(
            response.json())
        assert create_response, "JSON object was none"
        assert create_response.status.success, "Response for create had success false"
        created_item = create_response.created_item
        assert created_item, "Response was successful but had no item"
        assert created_item.item_category == params.category
        assert created_item.item_subtype == params.subtype

        item_handle = created_item.id

        fetch_params: Dict[str, Any] = {
            "id": item_handle,
            "seed_allowed": False
        }

        # 2) Fetch item and ensure it is there
        fetch_response = client.get(
            fetch_route,
            params=fetch_params,
        )

        assert fetch_response.status_code == 200
        fetch_response: GenericFetchResponse = fetch_response_model.parse_obj(
            fetch_response.json())
        assert fetch_response.status.success
        # change for when creating and deleting a full item
        assert fetch_response.item_is_seed == False
        fetched_item = fetch_response.item
        assert fetched_item
        assert fetched_item.item_category == params.category
        assert fetched_item.item_subtype == params.subtype
        # try parse item as correct type
        fetched_item: ItemBase = item_model.parse_obj(fetched_item)

        # 3) delete item
        delete_params = {"id": item_handle}

        delete_response = client.delete(
            delete_route,
            params=delete_params
        )
        assert delete_response.status_code == 200, f"Status code was {delete_response.status_code}."
        delete_response = StatusResponse.parse_obj(delete_response.json())
        # True even if no item existed to be deleted
        assert delete_response.status.success

        # 4. Attempt to fetch item and ensure it was deleted
        fetch_response = client.get(
            fetch_route,
            params=fetch_params,
        )
        assert fetch_response.status_code == 200
        fetch_response: GenericFetchResponse = fetch_response_model.parse_obj(
            fetch_response.json())
        # should be false to ensure deletion
        assert fetch_response.status.success == False, "Item should have been deleted, but is successfully fetched instead."


@mock_dynamodb
@pytest.mark.parametrize("params", route_params, ids=make_specialised_list("List"))
def test_entity_list(params: RouteParameters) -> None:
    """
        1. Create registry with items to list
        2. Create some seed items
        2. Attempt to list the items ensuring filters operate properly
    """

    app.dependency_overrides[read_user_protected_role_dependency] = user_protected_dependency_override
    app.dependency_overrides[read_write_user_protected_role_dependency] = user_protected_dependency_override

    default_table_setup()

    # 1.
    # load file to use to create
    route = params.route
    input_items: List[DomainInfoBase] = params.model_examples.domain_info
    create_response_model = params.typing_information.create_response
    assert create_response_model
    item_model = params.typing_information.item_model

    curr_route = get_route(action=RouteActions.CREATE, params=params)

    full_items = len(input_items)
    # create items from parsed file
    for domain_info_object in input_items:
        # Create safe serialisation
        safe_serialisation = json.loads(domain_info_object.json())
        response = client.post(curr_route, json=safe_serialisation)

        assert response.status_code == 200
        create_response: GenericCreateResponse = create_response_model.parse_obj(
            response.json())
        assert create_response, "JSON object was none"
        assert create_response.status.success, "Response for create had success false"
        created_item = create_response.created_item
        assert created_item, "Response was successful but had no item"
        assert created_item.item_category == params.category
        assert created_item.item_subtype == params.subtype

    # 2. create some seed items
    seed_count = 3
    curr_route = get_route(action=RouteActions.SEED, params=params)
    for _ in range(seed_count):
        response = client.post(curr_route)
        assert response.status_code == 200
        parsed_response = GenericSeedResponse.parse_obj(response.json())
        assert parsed_response.status.success

    # 3.
    list_resp_model = params.typing_information.list_response

    # get only complete items (no parameter needed - default behaviour)
    complete, seed = entity_list_exhaust(
        client=client,
        params=params
    )

    assert len(complete) == full_items
    assert len(seed) == 0

    # now get only seed
    complete, seed = entity_list_exhaust(
        client=client,
        params=params,
        subtype_list_request=SubtypeListRequest(
            filter_by=SubtypeFilterOptions(
                record_type=QueryRecordTypes.SEED_ONLY
            )
        )
    )
    assert len(complete) == 0
    assert len(seed) == seed_count

    # now get both
    complete, seed = entity_list_exhaust(
        client=client,
        params=params,
        subtype_list_request=SubtypeListRequest(
            filter_by=SubtypeFilterOptions(
                record_type=QueryRecordTypes.ALL
            )
        )
    )
    assert len(complete) == full_items
    assert len(seed) == seed_count

    # ensure all returned items can be parsed in the item model
    for item in complete:
        item_model.parse_obj(item)


@mock_dynamodb
@pytest.mark.parametrize("params", route_params, ids=make_specialised_list("multi-item-type-list"))
def test_list_filtering(params: RouteParameters) -> None:
    """
        1. Create registry with items of different types to list
        2. Attempt to list the items and ensure only the correct items are present
    """

    app.dependency_overrides[read_user_protected_role_dependency] = user_protected_dependency_override
    app.dependency_overrides[read_write_user_protected_role_dependency] = user_protected_dependency_override

    default_table_setup()

    # load file to use to create
    route = params.route
    input_items: List[DomainInfoBase] = params.model_examples.domain_info
    create_response_model = params.typing_information.create_response
    assert create_response_model
    curr_route = get_route(action=RouteActions.CREATE, params=params)
    # create items from parsed file
    for domain_info_object in input_items:
        # Create safe serialisation
        safe_serialisation = json.loads(domain_info_object.json())
        response = client.post(curr_route, json=safe_serialisation)

        assert response.status_code == 200
        create_response: GenericCreateResponse = create_response_model.parse_obj(
            response.json())
        assert create_response, "JSON object was none"
        assert create_response.status.success, "Response for create had success false"
        created_item = create_response.created_item
        assert created_item, "Response was successful but had no item"
        assert created_item.item_category == params.category
        assert created_item.item_subtype == params.subtype

    # also seed other item types by first getting a different route.
    for param_type in route_params:
        other_item_route = param_type.route
        if other_item_route == route:  # ( == this route)
            continue
        # else, different item type ... seed!
        other_seed_route = get_route(
            action=RouteActions.SEED, params=param_type)
        response = client.post(other_seed_route)
        assert response.status_code == 200, f"Status code was {response.status_code}."
        seed_resp = GenericSeedResponse.parse_obj(response.json())
        assert seed_resp.status.success
        item = seed_resp.seeded_item
        assert item

    # 2. Send list request for this test's item type and ensure the other items are excluded

    # Make request with ALL query filter ensuring all items of all types are present)
    items = general_list_exhaust(
        client=client,
        general_list_request=GeneralListRequest(
            filter_by=FilterOptions(
                record_type=QueryRecordTypes.ALL
            )
        )
    )
    assert len(items) == len(
        input_items) + len(route_params) - 1

    # make request for particular item type (i.e., with filter) and ensure only filtered ones are present
    list_resp_model = params.typing_information.list_response
    complete, seed = entity_list_exhaust(
        client=client,
        params=params,
    )
    assert len(complete) == len(input_items)
    assert len(complete) != len(
        input_items) + len(route_params) - 1
    assert len(seed) == 0

    # of the filtered items, try to parse them as what they should be
    for current_item in complete:
        params.typing_information.item_model.parse_obj(current_item.dict())


@pytest.mark.parametrize("params", route_params, ids=make_specialised_list("Update"))
def test_check_param_integrity(params: RouteParameters) -> None:
    # Ensures 2 different items can be sourced.
    # Used before the test_update function which requires 2 items
    input_items: List[DomainInfoBase] = params.model_examples.domain_info
    assert len(
        input_items) >= 2, "Was not able to source 2 items to upload and update with"
    item1 = input_items[0]
    item2 = input_items[1]
    assert item1 != item2, "Was not able to source 2 different items"


@mock_dynamodb
@pytest.mark.parametrize("params", route_params, ids=make_specialised_list("Update"))
@pytest.mark.depends(on=['test_check_param_integrity'])
def test_update(params: RouteParameters) -> None:
    """
    1. Source 2 different items
    2. Write item1 to the registry
    3. Update w item2
    4. Ensure successful update
    """

    # Override the auth dependency
    app.dependency_overrides[read_user_protected_role_dependency] = user_protected_dependency_override
    app.dependency_overrides[read_write_user_protected_role_dependency] = user_protected_dependency_override

    default_table_setup()

    # load file to use to create
    route = params.route
    input_items: List[DomainInfoBase] = params.model_examples.domain_info

    create_response_model = params.typing_information.create_response
    assert create_response_model
    item_model = params.typing_information.item_model
    fetch_response_model = params.typing_information.fetch_response
    original_domain_info = input_items[0]
    updated_domain_info = input_items[1]

    create_route = get_route(action=RouteActions.CREATE, params=params)
    original_resp = client.post(
        create_route,
        json=json.loads(original_domain_info.json())
    )

    assert original_resp.status_code == 200, f"Status code was {original_resp.status_code}. Details: {original_resp.json()}"
    original_resp: GenericCreateResponse = create_response_model.parse_obj(
        original_resp.json())
    assert original_resp.status.success
    created_item = original_resp.created_item
    assert created_item
    created_original_domain_info: DomainInfoBase = params.typing_information.domain_info(
        **created_item.dict())

    assert original_domain_info == created_original_domain_info
    handle = created_item.id

    # 2. Send update request with item2.
    reason = "fake reason"
    handle_params = {"id": handle, "reason": reason}

    update_route = get_route(action=RouteActions.UPDATE, params=params)
    update_item_resp = client.put(
        update_route,
        params=handle_params,
        json=py_to_dict(updated_domain_info)
    )

    assert update_item_resp.status_code == 200

    # Check if update was successful by fetching and comparing to what is should have updated to

    fetch_route = get_route(action=RouteActions.FETCH, params=params)
    fetch_resp = client.get(
        fetch_route,
        params=handle_params
    )

    assert fetch_resp.status_code == 200
    fetch_resp: GenericFetchResponse = fetch_response_model.parse_obj(
        fetch_resp.json())
    fetched_item = fetch_resp.item
    assert fetched_item
    fetched_updated_domain_info: DomainInfoBase = params.typing_information.domain_info(
        **fetched_item.dict())

    assert fetched_updated_domain_info == updated_domain_info
    assert fetched_updated_domain_info != original_domain_info


@mock_dynamodb
@pytest.mark.parametrize("params", route_params, ids=make_specialised_list("Update seeded item"))
def test_update_seeded_item(params: RouteParameters) -> None:
    """
    1. Seed an update
    2. Update the item with content (and hence complete item creation)
    """

    # Override the auth dependency
    app.dependency_overrides[read_user_protected_role_dependency] = user_protected_dependency_override
    app.dependency_overrides[read_write_user_protected_role_dependency] = user_protected_dependency_override

    default_table_setup()

    # load file to use to create
    route = params.route
    # Don't need an original as we are seeding
    domain_info_for_update: DomainInfoBase = params.model_examples.domain_info[0]

    seed_response_model = params.typing_information.seed_response
    assert seed_response_model
    fetch_response_model = params.typing_information.fetch_response

    seed_route = get_route(action=RouteActions.SEED, params=params)
    seed_resp = client.post(
        seed_route
    )

    assert seed_resp.status_code == 200
    seed_resp: GenericSeedResponse = seed_response_model.parse_obj(
        seed_resp.json())
    assert seed_resp.status.success
    seeded_item = seed_resp.seeded_item
    assert seeded_item
    handle = seeded_item.id
    assert seeded_item.record_type == RecordType.SEED_ITEM

    # 2. Update request for the item
    reason = "fake reason"
    handle_params = {"id": handle, "reason": reason}

    update_route = get_route(action=RouteActions.UPDATE, params=params)
    update_item_resp = client.put(
        update_route,
        params=handle_params,
        json=py_to_dict(domain_info_for_update)
    )

    assert update_item_resp.status_code == 200

    # Check if update was successful by fetching and comparing to what is should have updated to

    fetch_route = get_route(action=RouteActions.FETCH, params=params)
    fetch_resp = client.get(
        fetch_route,
        params=handle_params
    )

    assert fetch_resp.status_code == 200
    fetch_resp: GenericFetchResponse = fetch_response_model.parse_obj(
        fetch_resp.json())
    fetched_item = fetch_resp.item
    assert fetched_item
    fetched_updated_domain_info: DomainInfoBase = params.typing_information.domain_info(
        **fetched_item.dict())

    assert fetched_updated_domain_info == domain_info_for_update
    assert not fetch_resp.item_is_seed
    assert fetched_item.record_type == RecordType.COMPLETE_ITEM


@mock_dynamodb
@pytest.mark.parametrize("params", route_params, ids=make_specialised_list("Invalid Update"))
def test_invalid_update(params: RouteParameters) -> None:
    """
    1. Seed an item
    2. Attempt update with invalid domain_info
    3. Assert correct error handling by API
    """

    # Override the auth dependency
    app.dependency_overrides[read_user_protected_role_dependency] = user_protected_dependency_override
    app.dependency_overrides[read_write_user_protected_role_dependency] = user_protected_dependency_override

    default_table_setup()

    # load file to use to create
    route = params.route

    seed_response_model = params.typing_information.seed_response
    assert seed_response_model
    fetch_response_model = params.typing_information.fetch_response
    # 1.
    seed_route = get_route(action=RouteActions.SEED, params=params)
    seed_resp = client.post(
        seed_route
    )

    assert seed_resp.status_code == 200
    seed_resp: GenericSeedResponse = seed_response_model.parse_obj(
        seed_resp.json())
    assert seed_resp.status.success
    seeded_item = seed_resp.seeded_item
    assert seeded_item
    handle = seeded_item.id
    # 2. Attempt Item Update
    reason = "fake reason"
    handle_params = {"id": handle, "reason": reason}

    input_domain: DomainInfoBase = params.model_examples.domain_info[0]
    input_domain_dict = json.loads(input_domain.json())
    # invalidate the input
    input_domain_dict.pop("display_name")

    update_route = get_route(action=RouteActions.UPDATE, params=params)
    update_item_resp = client.put(
        update_route,
        params=handle_params,
        json=json.loads(json.dumps(input_domain_dict))
    )

    # 3. Ensure correct error handling by API
    assert update_item_resp.status_code == 422, "Uh oh, invalid domain info was written!"

    handle_params["seed_allowed"] = "True"
    fetch_route = get_route(action=RouteActions.FETCH, params=params)
    fetch_resp = client.get(
        fetch_route,
        params=handle_params,
    )

    fetch_resp: GenericFetchResponse = fetch_response_model.parse_obj(
        fetch_resp.json())
    assert fetch_resp.item_is_seed  # Should still be a seed


@pytest.mark.parametrize("params", route_params, ids=make_specialised_list("Validate"))
def test_validate_valid(params: RouteParameters) -> None:
    # ensure endpoint returns 200 if given valid input to validate

    # Override the auth dependency
    app.dependency_overrides[read_user_protected_role_dependency] = user_protected_dependency_override
    app.dependency_overrides[read_write_user_protected_role_dependency] = user_protected_dependency_override

    route = params.route
    valid_domain_info: DomainInfoBase = params.model_examples.domain_info[0]

    validate_route = get_route(action=RouteActions.VALIDATE, params=params)
    validate_resp = client.post(
        validate_route,
        json=json.loads(valid_domain_info.json())
    )

    assert validate_resp.status_code == 200


@pytest.mark.parametrize("params", route_params, ids=make_specialised_list("Invalid Validate"))
def test_validate_with_invalid(params: RouteParameters) -> None:
    # Ensure endpoint returns 422 if given invalid input to validate

    # Override the auth dependency
    app.dependency_overrides[read_user_protected_role_dependency] = user_protected_dependency_override
    app.dependency_overrides[read_write_user_protected_role_dependency] = user_protected_dependency_override

    route = params.route
    input_domain: DomainInfoBase = params.model_examples.domain_info[0]
    input_domain_dict = json.loads(input_domain.json())
    # invalid the input
    input_domain_dict.pop("display_name")  # invalidate the input

    validate_route = get_route(action=RouteActions.VALIDATE, params=params)
    validate_resp = client.post(
        validate_route,
        json=input_domain_dict
    )

    assert validate_resp.status_code == 422


@mock_dynamodb
def test_create_dataset_validation(override_perform_validation_config_dependency: Generator) -> None:
    """Test for validation processes for the creation of model_run_workflow_def's.
    Need to ensure API does not allow for the creation of model run workflow defs that reference software or dataset templates that:
        1. Do not exist,
        2. Are not complete items
        3. Are not actually software's or dataset templates, respectively.
    4. Need to also ensure the validation passes for correct payloads too.
    Parameters
    ----------
    override_perform_validation_config_dependency : Generator
        Overriding of global config with a config local to this test which has
        perform_validation = True.
    """

    # Override the auth dependency
    app.dependency_overrides[read_user_protected_role_dependency] = user_protected_dependency_override
    app.dependency_overrides[read_write_user_protected_role_dependency] = user_protected_dependency_override

    # Set up fresh (empty) DB
    default_table_setup()

    # Route Parameters for model_run_workflow_def
    params = get_item_subtype_route_params(
        ItemSubType.DATASET)

    response_model = params.typing_information.create_response
    assert response_model
    # Validation for model run workflow defn's

    # 1. Ensure failure to create dataset with items that do not exist
    dataset_domain_info: DatasetDomainInfo = params.model_examples.domain_info[0]
    create_resp = create_item_from_domain_info(client=client, domain_info=dataset_domain_info, params=params)
    create_resp: GenericCreateResponse = response_model.parse_obj(create_resp.json())
    # should fail due to items not existing (db empty)
    assert not create_resp.status.success

    # 2. Ensure failure when payload references seed Items

    # seed agent, and organisation
    org_item =  seed_item_successfully(client=client, item_subtype=ItemSubType.ORGANISATION)
    org_id = org_item.id

    # seed person
    person_item =  seed_item_successfully(client=client, item_subtype=ItemSubType.PERSON)
    person_id = person_item.id

    # swap payload references to use newly seeded items that exist.
    dataset_domain_info.collection_format.associations.organisation_id = org_id
    dataset_domain_info.collection_format.dataset_info.publisher_id = org_id
    dataset_domain_info.collection_format.associations.data_custodian_id = person_id

    # attempt creation with seed items and ensure failure
    create_resp = create_resp = create_item_from_domain_info(client=client, domain_info=dataset_domain_info, params=params)
    create_resp: GenericCreateResponse = response_model.parse_obj(
        create_resp.json())
    # should fail due to refering to seed items
    assert not create_resp.status.success

    # update both items to be complete items, then ensure successful validation
    # organisation update
    update_item_resp = update_item_from_domain_info(client=client, id=org_id, updated_domain_info=get_model_example(item_subtype=ItemSubType.ORGANISATION), subtype=ItemSubType.ORGANISATION)
    assert update_item_resp.status_code == 200

    # person update
    update_item_resp = update_item_from_domain_info(client=client, id=person_id, updated_domain_info=get_model_example(item_subtype=ItemSubType.PERSON), subtype=ItemSubType.PERSON)
    assert update_item_resp.status_code == 200, f"Status code was {update_item_resp.status_code}. Details: {update_item_resp.json()}"

    # 4. (3. below) now ensure the creation will succeed with correct payload
    create_item_from_domain_info_successfully(client=client, domain_info=dataset_domain_info, params=params)
    valid_domain_info = DatasetDomainInfo.parse_obj(py_to_dict(dataset_domain_info)) # make object copy for later

    # now swap the person/organisation IDs and ensure the type validation causes an error
    dataset_domain_info.collection_format.associations.organisation_id = person_id
    # 3. now ensure the creation will fail due to the id for software in payload actually being for a dataset template
    create_resp = create_item_from_domain_info(client=client, domain_info=dataset_domain_info, params=params)

    create_resp: GenericCreateResponse = response_model.parse_obj(create_resp.json())
    # should fail due to referencing wrong item types.
    assert not create_resp.status.success

    # Testing New domain info validation in f-1524

    # check success first
    create_item_from_domain_info_successfully(client=client, domain_info=valid_domain_info, params=params)
    
    # Test invalid spatial coverage
    domain_info_invalid_spatial = DatasetDomainInfo.parse_obj(py_to_dict(valid_domain_info))
    assert domain_info_invalid_spatial.collection_format.dataset_info.spatial_info
    invalid_spatial_coverages = ["invalid spatial coverage", "SRID=123123123123;POINT(-73.987587 40.757929)", "SRID=a6;POINT(-73.987587 40.757929)", "SRID=4326POINT(-73.987587 40.757929)", "SRID=4326;POINT(-73.987587)", "SRID 4326;POINT(-73.987587 40.757929)", "SRID=4326;POINT(-73.987vvxz587 40.757929)"]
    for invalid_spatial_coverage in invalid_spatial_coverages:
        domain_info_invalid_spatial.collection_format.dataset_info.spatial_info.coverage = invalid_spatial_coverage
        create_item_from_domain_info_not_successfully(client=client, domain_info=domain_info_invalid_spatial, params=params)

    # test with valid spatial converage so we know it was failing for the right reasons
    domain_info_invalid_spatial.collection_format.dataset_info.spatial_info.coverage = "SRID=4326;POINT(-73.987587 40.757929)"
    create_item_from_domain_info_successfully(client=client, domain_info=domain_info_invalid_spatial, params=params)

    # repeat for the spatial extent
    for invalid_spatial_coverage in invalid_spatial_coverages:
        domain_info_invalid_spatial.collection_format.dataset_info.spatial_info.extent = invalid_spatial_coverage
        create_item_from_domain_info_not_successfully(client=client, domain_info=domain_info_invalid_spatial, params=params)
    
    # test with valid spatial converage so we know it was failing for the right reasons
    domain_info_invalid_spatial.collection_format.dataset_info.spatial_info.extent = "SRID=4326;POINT(-73.987587 40.757929)"
    create_item_from_domain_info_successfully(client=client, domain_info=domain_info_invalid_spatial, params=params)

    invalid_spatial_resolutions = ["abc", "-1.2"]
    for invalid_spatial_res in invalid_spatial_resolutions:
        domain_info_invalid_spatial.collection_format.dataset_info.spatial_info.resolution = invalid_spatial_res
        resp = create_item_from_domain_info(client=client, domain_info=domain_info_invalid_spatial, params=params)
        assert resp.status_code == 422, f"Expected 422 for invalid spatial resolution. Got {resp.status_code} instead."

    # test with valid spatial res so we know it was failing for the right reasons
    domain_info_invalid_spatial.collection_format.dataset_info.spatial_info.resolution = "1.2"
    create_item_from_domain_info_successfully(client=client, domain_info=domain_info_invalid_spatial, params=params)

    # invalid temporal info 
    domain_info_invalid_temporal = DatasetDomainInfo.parse_obj(py_to_dict(valid_domain_info))
    temporal_info = domain_info_invalid_temporal.collection_format.dataset_info.temporal_info # reference
    assert temporal_info

    invalid_temporal_resolutions = ["123_invalid", "1Y2M10DT2H30M",  "P1Y2M10DT2", "1Y2M10DT2H"]
    for invalid_temp_res in invalid_temporal_resolutions:
        temporal_info.resolution = invalid_temp_res
        resp = create_item_from_domain_info(client=client, domain_info=domain_info_invalid_temporal, params=params)
        assert resp.status_code == 422, f"Expected 422 for invalid temporal resolution ({invalid_temp_res}). Got {resp.status_code} instead. Details: {resp.json()}"

    temporal_info.resolution="P1Y2M10DT2H30M" # reset to acceptable and test missing one date time
    create_item_from_domain_info_successfully(client=client, domain_info=domain_info_invalid_temporal, params=params)

    assert temporal_info.duration, f"Expected example item in example models to have a duration, but is None."
    temporal_info.duration.begin_date = None # type: ignore
    resp = create_item_from_domain_info(client=client, domain_info=domain_info_invalid_temporal, params=params)
    assert resp.status_code == 422

    # invalid data custodian
    domain_info_invalid_custodian = DatasetDomainInfo.parse_obj(py_to_dict(valid_domain_info))
    domain_info_invalid_custodian.collection_format.associations.data_custodian_id = "invalid id 234"
    resp = create_item_from_domain_info(client=client, domain_info=domain_info_invalid_custodian, params=params)
    create_resp: GenericCreateResponse = response_model.parse_obj(resp.json())
    assert not create_resp.status.success
    # and check OK with valid custodian ID
    domain_info_invalid_custodian.collection_format.associations.data_custodian_id = person_id
    create_resp = create_item_from_domain_info_successfully(client=client, domain_info=domain_info_invalid_custodian, params=params)


@mock_dynamodb
def test_create_model_run_workflow_def_validation(override_perform_validation_config_dependency: Generator) -> None:
    """Test for validation processes for the creation of model_run_workflow_def's.

    Need to ensure API does not allow for the creation of model run workflow defs that reference software or dataset templates that:
        1. Do not exist,
        2. Are not complete items
        3. Are not actually software's or dataset templates, respectively.
    4. Need to also ensure the validation passes for correct payloads too.

    Parameters
    ----------
    override_perform_validation_config_dependency : Generator
        Overriding of global config with a config local to this test which has
        perform_validation = True.
    """

    # Override the auth dependency
    app.dependency_overrides[read_user_protected_role_dependency] = user_protected_dependency_override
    app.dependency_overrides[read_write_user_protected_role_dependency] = user_protected_dependency_override

    # Set up fresh (empty) DB
    default_table_setup()

    # Route Parameters for model_run_workflow_def
    params = get_item_subtype_route_params(
        ItemSubType.MODEL_RUN_WORKFLOW_TEMPLATE)

    response_model = params.typing_information.create_response
    assert response_model
    # Validation for model run workflow defn's

    # 1. Ensure failure to create model run def with items that do not exist
    model_run_def_domain: WorkflowTemplateDomainInfo = params.model_examples.domain_info[0]
    create_route = get_route(action=RouteActions.CREATE, params=params)
    create_resp = client.post(
        create_route,
        json=model_run_def_domain.dict()
    )
    create_resp: GenericCreateResponse = response_model.parse_obj(
        create_resp.json())

    # should fail due to items not existing (db empty)
    assert not create_resp.status.success

    # 2. Ensure failure when payload references seed Items
    # seed software model and dataset templates
    model_route_params = get_item_subtype_route_params(ItemSubType.MODEL)

    # seed software model
    seed_route = get_route(action=RouteActions.SEED, params=model_route_params)
    response = client.post(seed_route)
    assert response.status_code == 200, f"Status code was {response.status_code}."
    seed_resp = GenericSeedResponse.parse_obj(response.json())
    assert seed_resp.status.success
    item = seed_resp.seeded_item
    assert item
    model_id = item.id

    # seed dataset template
    dataset_template_route_params = get_item_subtype_route_params(
        ItemSubType.DATASET_TEMPLATE)
    seed_route = get_route(action=RouteActions.SEED,
                           params=dataset_template_route_params)
    response = client.post(seed_route)

    assert response.status_code == 200, f"Status code was {response.status_code}."
    seed_resp = GenericSeedResponse.parse_obj(response.json())
    assert seed_resp.status.success
    item = seed_resp.seeded_item
    assert item
    template_id = item.id

    # swap payload references to use newly seeded items that exist.
    model_run_def_domain.software_id = model_id
    model_run_def_domain.input_templates = [
        TemplateResource(template_id=template_id)]
    model_run_def_domain.output_templates = [
        TemplateResource(template_id=template_id)]
    # attempt creation with seed items and ensure failure
    create_route = get_route(action=RouteActions.CREATE, params=params)
    create_resp = client.post(
        create_route,
        json=model_run_def_domain.dict()
    )
    create_resp: GenericCreateResponse = response_model.parse_obj(
        create_resp.json())
    # should fail due to refering to seed items
    assert not create_resp.status.success

    # update both items to be complete items, then ensure successful validation

    # model update
    model_domain_info = model_route_params.model_examples.domain_info[0]
    update_route = get_route(action=RouteActions.UPDATE,
                             params=model_route_params)
    reason = "fake reason"
    update_params = {"id": model_id, "reason": reason}
    update_item_resp = client.put(
        update_route,
        params=update_params,
        json=model_domain_info.dict()
    )
    assert update_item_resp.status_code == 200

    # template update
    model_domain_info = dataset_template_route_params.model_examples.domain_info[0]
    update_route = get_route(action=RouteActions.UPDATE,
                             params=dataset_template_route_params)
    update_params = {"id": template_id, "reason": reason}
    update_item_resp = client.put(
        update_route,
        params=update_params,
        json=model_domain_info.dict()
    )
    assert update_item_resp.status_code == 200

    # 4. (3. below) now ensure the creation will succeed with correct payload
    create_route = get_route(action=RouteActions.CREATE, params=params)
    create_resp = client.post(
        create_route,
        json=model_run_def_domain.dict()
    )
    create_resp: GenericCreateResponse = response_model.parse_obj(
        create_resp.json())
    assert create_resp.status.success  # should succeed as created full items

    # now swap the IDs so the dataset ID refers to a software and vice versa, then ensure failure
    tmp_id = model_run_def_domain.software_id
    model_run_def_domain.software_id = model_run_def_domain.input_templates[0].template_id
    model_run_def_domain.input_templates = [
        TemplateResource(template_id=tmp_id)]

    # 3. now ensure the creation will fail due to the id for software in payload actually being for a dataset template
    create_resp = client.post(
        create_route,
        json=model_run_def_domain.dict()  # json.dumps(input_domain_dict)
    )

    create_resp: GenericCreateResponse = response_model.parse_obj(
        create_resp.json())
    # should fail due to referencing wrong item types.
    assert not create_resp.status.success


def test_nullable_property() -> None:
    """
    1. Choose a model which has an optional field (orcid or person agent)
    2. Get the schema object
    3. Ensure the types include the null type as an option
    4. Get the actual client schema response and check it is also correct
    5. Generate the open api spec from the app endpoint and ensure it has
    anyOf with a null type for the specified property
    6. Check that the anyOf schema selection includes a title property "None"
    """
    app.dependency_overrides[read_user_protected_role_dependency] = user_protected_dependency_override

    person_params = get_item_subtype_route_params(ItemSubType.PERSON)

    model = PersonDomainInfo
    schema = model.schema()

    # Pull out orcid property
    orcid_type = schema['properties']['orcid']['type']

    # Check that the schema has a list of types for orcid property
    assert isinstance(orcid_type, list)

    # Check that the types are correct
    assert set(orcid_type) == set(["string", "null"])

    # Get schema from endpoint
    schema_route = get_route(RouteActions.SCHEMA, params=person_params)
    response = client.get(schema_route)
    assert response.status_code == 200, f"Non 200 code: {response.status_code}"

    # retrieve after parsing
    contents = JsonSchemaResponse.parse_obj(response.json()).json_schema

    # assert that the returned schema is correct
    assert contents
    client_orcid_type = contents['properties']['orcid']['type']

    # make sure it matches
    assert isinstance(client_orcid_type, list)
    assert set(client_orcid_type) == set(orcid_type)

    # So the model itself and schema endpoint work - check the open api spec
    # can be generated and uses the anyOf schema properly
    response = client.get("/openapi.json")

    # Get the openAPI json out
    assert response.status_code == 200, f"Non 200 code: {response.status_code}"
    open_api_text = response.text
    open_api_dict = json.loads(open_api_text)

    # Get the PersonDomainInfo definition
    # from the open API spec
    person_definition = open_api_dict['components']['schemas']['PersonDomainInfo']
    required_fields: List[str] = person_definition['required']

    # required fields present, but orcid not (optional)
    assert 'orcid' not in required_fields
    assert 'first_name' in required_fields

    # check orcid property itself
    orcid_property = person_definition['properties']['orcid']

    # check it has anyOf field and that its a list of length 2
    any_of: Optional[List[Dict[str, Any]]] = orcid_property.get('anyOf')
    assert any_of
    assert len(any_of) == 2

    # check that at least one of the anyOf schemas has type null
    null_properties = list(filter(
        lambda props: props.get('type') == "null",
        any_of))
    assert (len(null_properties) == 1)

    # get the null schema
    null_property: Dict[str, Any] = null_properties[0]

    # check that it has a title field and that the title is None
    # this means that the schema form will have a nice title for the schema
    assert null_property.get('title')
    assert null_property['title'] == "None"


@mock_dynamodb
def test_general_list_seed_filtering() -> None:
    """
    Checks that the seed filtering capability of the general list endpoint
    correctly filters seed vs non seed.

    1. Seed all item types and ensure they have record_type SEEDED_ITEM
    2. create all item types and ensure they have record type COMPLETE_ITEM
    3. request all items from registry - ensure correct amount and type
    4. request all nonseed items from registry - ensure correct amount and type

    """

    app.dependency_overrides[read_user_protected_role_dependency] = user_protected_dependency_override
    app.dependency_overrides[read_write_user_protected_role_dependency] = user_protected_dependency_override

    default_table_setup()

    complete_repeat_count: int = 2
    seed_repeat_count: int = 1

    # 1 and 2 in same for loop
    for param_type in route_params:
        seed_route = get_route(RouteActions.SEED, params=param_type)
        create_route = get_route(RouteActions.CREATE, params=param_type)

        # 1. Seed item of this type
        def create_seed() -> None:
            response = client.post(seed_route)
            assert response.status_code == 200, f"Status code was {response.status_code}."
            seed_resp = GenericSeedResponse.parse_obj(response.json())
            assert seed_resp.status.success
            item = seed_resp.seeded_item
            assert item
            # check seed item status
            assert item.record_type == RecordType.SEED_ITEM

        # 2. Create item of this type
        def create_full() -> None:
            domain_info = param_type.model_examples.domain_info[0]
            response = client.post(
                create_route, json=json.loads(domain_info.json()))
            assert response.status_code == 200, f"Status code was {response.status_code}."
            create_resp = GenericCreateResponse.parse_obj(response.json())
            assert create_resp.status.success
            item = create_resp.created_item
            assert item
            # check complete item status
            assert item.record_type == RecordType.COMPLETE_ITEM

        # Create x complete items
        for _ in range(complete_repeat_count):
            create_full()

        # create y seed items
        for _ in range(seed_repeat_count):
            create_seed()

        # this creates a different number of seed vs
        # complete to ensure filtering is correct

    num_complete_items = len(route_params) * complete_repeat_count
    num_seed_items = len(route_params) * seed_repeat_count
    num_total_items = num_seed_items + num_complete_items

    # 3.

    # now do query with filter specifying all - should get both
    items = general_list_exhaust(
        client=client,
        general_list_request=GeneralListRequest(
            filter_by=FilterOptions(
                record_type=QueryRecordTypes.ALL
            )
        )
    )

    # check item count
    assert len(items) == num_total_items

    # 4.

    # Make request with empty query filter - this should only allow complete items
    items = general_list_exhaust(
        client=client,
    )

    # check item count
    assert len(items) == num_complete_items


@mock_dynamodb
@pytest.mark.parametrize("params", route_params, ids=make_specialised_list("Test Model Validators"))
def test_model_validators(params: RouteParameters) -> None:
    """
    Test to ensure the static model validators defined with the models will not allow
    for the creation of Items with invalid categories and sub types.
    """

    app.dependency_overrides[read_user_protected_role_dependency] = user_protected_dependency_override
    app.dependency_overrides[read_write_user_protected_role_dependency] = user_protected_dependency_override

    default_table_setup()

    item_model = params.typing_information.item_model
    response_model = params.typing_information.create_response
    assert response_model
    # get an example object out from the examples in params.
    example_domain_info = params.model_examples.domain_info[0]

    curr_route = get_route(RouteActions.CREATE, params=params)
    create_resp = client.post(
        curr_route, json=json.loads(example_domain_info.json()))
    assert create_resp.status_code == 200
    create_resp: GenericCreateResponse = response_model.parse_obj(
        create_resp.json())
    created_item_1 = create_resp.created_item
    assert created_item_1

    # make duplicates so we can test different validations
    # 2 for not even using a define subtype or category, just random strings
    created_item_2: ItemBase = item_model.parse_obj(created_item_1.dict())

    # 2 more for testing using a category and subtype for different types
    created_item_3: ItemBase = item_model.parse_obj(created_item_1.dict())
    created_item_4: ItemBase = item_model.parse_obj(created_item_1.dict())

    # invalidate first 2 items (and ignore assignment of str to var of type ItemCategory)

    created_item_1.item_category = "an_incorrect_item_category"  # type: ignore[assignment] # nopep8
    created_item_2.item_subtype = "an_incorrect_item_subtype"  # type: ignore[assignment] # nopep8

    # invalidate second 2 items
    created_item_3.item_category = get_other_category(
        created_item_3.item_category)
    created_item_4.item_subtype = get_other_subtype(
        created_item_4.item_subtype)

    # Ensure validation failures for items (dumping and parsing must all error for test to pass)
    with pytest.raises(pydantic.error_wrappers.ValidationError) as e_info:
        created_item_1 = item_model.parse_obj(created_item_1.dict())

    with pytest.raises(pydantic.error_wrappers.ValidationError) as e_info:
        created_item_2 = item_model.parse_obj(created_item_2.dict())

    with pytest.raises(pydantic.error_wrappers.ValidationError) as e_info:
        created_item_3 = item_model.parse_obj(created_item_3.dict())

    with pytest.raises(pydantic.error_wrappers.ValidationError) as e_info:
        created_item_4 = item_model.parse_obj(created_item_4.dict())


def create_items(param_type: RouteParameters, just_one: bool = False) -> None:
    """Creates an entity for each of the provided defined examples in the
    param_type.model_examples for that entity type.

    Parameters
    ----------
    param_type : RouteParameters
        The current parameter information for the item type we are creating
        examples of.

    just_one : bool
        Optional boolean. If true, will only create one item of each type. 
    """
    for domain_info in param_type.model_examples.domain_info:
        # domain_info = param_type.model_examples.domain_info[0]
        curr_route = get_route(action=RouteActions.CREATE, params=param_type)
        response = client.post(
            curr_route, json=json.loads(domain_info.json()))
        assert response.status_code == 200, f"Status code was {response.status_code}. Details {response.json()}"

        if just_one:
            return


@mock_dynamodb
@pytest.mark.parametrize("params", route_params, ids=make_specialised_list("Test Query List"))
def test_query_list(params: RouteParameters) -> None:

    # Test to ensure the static model validators defined with the models will not allow
    # for the creation of Items with invalid categories and sub types.

    app.dependency_overrides[read_user_protected_role_dependency] = user_protected_dependency_override
    app.dependency_overrides[read_write_user_protected_role_dependency] = user_protected_dependency_override

    default_table_setup()

    small_page_size = 2

    # Create 3 of each item type.
    num_per_item = 3
    total_num_items = num_per_item * len(route_params)
    for route_param in route_params:
        for _ in range(num_per_item):
            create_items(param_type=route_param, just_one=True)

    # Query using this tests parametirised item type and with a limit of 1 to also test the pagination is working.
    total_items: List[Dict[str, Any]] = []

    items = general_list_exhaust(
        client=client,
        general_list_request=GeneralListRequest(page_size=small_page_size)
    )
    assert len(items) == total_num_items

    items = general_list_exhaust(
        client=client,
        general_list_request=GeneralListRequest(
            sort_by=SortOptions(
                sort_type=SortType.UPDATED_TIME,
                ascending=True
            ),
            filter_by=FilterOptions(
                item_subtype=params.subtype
            ),
            page_size=small_page_size
        )
    )

    assert len(items) == num_per_item

    # check items are correct type and ordered.
    updated_time = 0
    for item in total_items:
        item_pydantic: ItemBase = params.typing_information.item_model.parse_obj(
            item)
        assert item_pydantic.updated_timestamp >= updated_time
        updated_time = item_pydantic.updated_timestamp

    # sort options using name for sort


def make_query(
    client: Any,
    general_list_request: GeneralListRequest
) -> Tuple[List[Dict[str, Any]], Optional[PaginationKey]]:
    json_payload = json.loads(general_list_request.json())
    list_response = client.post(
        "/registry/general/list", json=json_payload)
    # check the status is 200
    assert list_response.status == 200
    # parse as json
    json_response = list_response.json()
    # parse as list resposne
    parsed_response = PaginatedListResponse.parse_obj(json_response)
    # check status
    assert parsed_response.status.success
    # check that the response includes items
    assert parsed_response.items
    # return the list of items and the pagination key
    return (parsed_response.items, parsed_response.pagination_key)


@mock_dynamodb
@pytest.mark.parametrize("params", route_params, ids=make_specialised_list("Test Resource Locks"))
def test_resource_lock(params: RouteParameters) -> None:

    app.dependency_overrides[read_user_protected_role_dependency] = user_protected_dependency_override
    app.dependency_overrides[read_write_user_protected_role_dependency] = user_protected_dependency_override

    default_table_setup()

    item_model = params.typing_information.item_model

    item = item_model.parse_obj(
        create_one_item_successfully(client=client, params=params))

    id = item.id

    # lock item and check status shows locked
    lock_resp = lock_item(client=client, id=id, params=params)
    assert lock_resp.status.success

    lock_status = get_lock_status(client=client, id=id, params=params)
    assert lock_status.locked

    # attempt to edit and ensure failure
    update_item_resp = update_item(client=client, id=id, params=params)
    assert update_item_resp.status_code == 401

    # unlock item and check status shows unlocked
    unlock_resp = unlock_item(client=client, id=id, params=params)
    assert unlock_resp.status.success

    lock_status = get_lock_status(client=client, id=id, params=params)
    assert not lock_status.locked

    # attempt to edit and ensure success
    update_item_resp = update_item(client=client, id=id, params=params)
    assert update_item_resp.status_code == 200

    # fetch lock history
    lock_history = fetch_lock_history(client=client, id=id, params=params)
    assert lock_history.history
    assert len(lock_history.history) == 2

    # ensure failure if entering item id pointing to different type to this route.
    other_params = get_item_subtype_route_params(
        get_other_subtype(params.subtype))
    other_item_model = other_params.typing_information.item_model
    other_item = other_item_model.parse_obj(
        create_one_item_successfully(client=client, params=other_params))

    with pytest.raises(AssertionError):
        lock_item(client=client, id=other_item.id, params=params)
    with pytest.raises(AssertionError):
        unlock_item(client=client, id=other_item.id, params=params)


@mock_dynamodb
@pytest.mark.parametrize("params", route_params, ids=make_specialised_list("Test Auth"))
def test_auth(params: RouteParameters) -> None:

    app.dependency_overrides[read_user_protected_role_dependency] = user_protected_dependency_override
    app.dependency_overrides[read_write_user_protected_role_dependency] = user_protected_dependency_override

    default_table_setup()

    item_model = params.typing_information.item_model
    item = item_model.parse_obj(
        create_one_item_successfully(client=client, params=params))
    id = item.id

    # test evaluate access
    access_roles = evaluate_access(client=client, id=id, params=params).roles
    assert access_roles

    # get initial auth settings (as default)
    initial_auth_settings = get_auth_config(
        client=client, id=id, params=params)

    # add some auth configs (new group and write for general)
    new_acccess_settings = AccessSettings(
        owner=initial_auth_settings.owner,
        general=[
            "metadata-read",
            "metadata-write"
        ],
        groups={
            "CoralLovers 2.0": [
                "metadata-write",
                "metadata-read"
            ]
        }
    )

    new_auth_payload = new_acccess_settings.dict()
    put_response = put_auth_config(
        client=client, id=id, auth_payload=new_auth_payload, params=params)
    assert put_response.status.success

    # get new auth settings
    post_auth_settings = get_auth_config(
        client=client, id=id, params=params)

    # check new auth setings have changed and are correct
    assert initial_auth_settings != post_auth_settings
    assert post_auth_settings == new_acccess_settings

    # finally, check auth roles
    auth_roles = get_auth_roles(client=client, params=params).dict()
    assert auth_roles

    # ensure failure if entering item id pointing to different type to this route.
    other_params = get_item_subtype_route_params(
        get_other_subtype(params.subtype))
    other_item_model = other_params.typing_information.item_model
    other_item = other_item_model.parse_obj(
        create_one_item_successfully(client=client, params=other_params))

    with pytest.raises(AssertionError):
        get_auth_config(client=client, id=other_item.id, params=params)
    with pytest.raises(AssertionError):
        put_auth_config(client=client, id=other_item.id,
                        auth_payload=new_auth_payload, params=params)


@mock_dynamodb
@pytest.mark.parametrize("params", route_params, ids=make_specialised_list("Test Auth Implicit General Access"))
# @pytest.mark.depends(on=['test_auth'])  # depends on explicit tests
def test_auth_implicit_general_access(params: RouteParameters, override_enforce_user_auth_dependency: Generator, monkeypatch: Any) -> None:
    user1 = TestingUser("Penny")
    user2 = TestingUser("Passie")

    def set_active_user(user: TestingUser) -> None:

        set_read_write_protected_role(app=app, username=user.name)
        mock_user_group_set(user_groups=user.groups, monkeypatch=monkeypatch)

    default_table_setup()

    # * user1 creates an item and privatises it
    set_active_user(user=user1)
    item_model = params.typing_information.item_model
    user1_item = item_model.parse_obj(
        create_one_item_successfully(client=client, params=params))
    remove_general_access_from_item(
        client=client, item=user1_item, params=params)
    # * user2 attempt to read item and fails
    set_active_user(user=user2)
    # test scope which has access to the local variables user1_groups and user2_groups
    response = fetch_item_basic(client=client, params=params, id=user1_item.id)
    assert response.status_code == 401, "Response did not fail to fetch item due to authorisation issue when it should have"
    assert not accessible_via_registry_list(
        client=client, item_id=user1_item.id)

    # * user 1 adds general access read, then user2 can read
    set_active_user(user=user1)
    give_general_read_access(client=client, item=user1_item, params=params)
    set_active_user(user=user2)
    response = fetch_item_basic(client=client, params=params, id=user1_item.id)
    assert response.status_code == 200
    response = GenericFetchResponse.parse_obj(response.json())
    assert response.status.success
    assert response.item
    assert accessible_via_registry_list(client=client, item_id=user1_item.id)

    # * user2 tries to update and fails
    response = update_item(client=client, id=user1_item.id, params=params)
    assert response.status_code == 401, "Response did not fail to fetch item due to authorisation issue when it should have"

    # * user1 adds write permissions and user2 successfully updates
    set_active_user(user=user1)
    give_general_read_write_access(
        client=client, item=user1_item, params=params)
    set_active_user(user=user2)
    response = update_item(client=client, id=user1_item.id, params=params)
    assert response.status_code == 200
    response = GenericFetchResponse.parse_obj(response.json())
    assert response.status.success


@mock_dynamodb
@pytest.mark.parametrize("params", route_params, ids=make_specialised_list("Test auth implicit group access and owner"))
# @pytest.mark.depends(on=['test_auth'])  # depends on explicit tests
def test_auth_implicit_group_access_and_owner(params: RouteParameters, override_enforce_user_auth_dependency: Generator, monkeypatch: Any) -> None:
    user1 = TestingUser("Penny")
    user2 = TestingUser("Clooney")

    def set_active_user(user: TestingUser) -> None:

        set_read_write_protected_role(app=app, username=user.name)
        mock_user_group_set(user_groups=user.groups, monkeypatch=monkeypatch)

    default_table_setup()

    # * user1 creates an item and privatises it
    set_active_user(user=user1)
    item_model = params.typing_information.item_model
    user1_item = item_model.parse_obj(
        create_one_item_successfully(client=client, params=params))
    remove_general_access_from_item(
        client=client, item=user1_item, params=params)

    # * user2 attempt to read item and fails
    set_active_user(user=user2)
    # test scope which has access to the local variables user1_groups and user2_groups
    response = fetch_item_basic(client=client, params=params, id=user1_item.id)
    assert response.status_code == 401, "Response did not fail to fetch item due to authorisation issue when it should have"
    # now try to read via general list all
    assert not accessible_via_registry_list(
        client=client, item_id=user1_item.id)

    # * user1 adds group permission that user2 is a member of and gives the group reading perms
    set_active_user(user=user1)
    test_group = 'test_group'
    user2.addToGroup(test_group)
    item1_group_roles = {
        test_group: ['metadata-read']
    }
    set_group_access_roles(client=client, item=user1_item,
                           params=params, group_access_roles=item1_group_roles)

    # * user2 reads item successfully
    set_active_user(user=user2)
    response = fetch_item_basic(client=client, params=params, id=user1_item.id)
    assert response.status_code == 200
    response = GenericFetchResponse.parse_obj(response.json())
    assert response.status.success
    assert response.item
    assert accessible_via_registry_list(client=client, item_id=user1_item.id)

    # * user2 tries to update and fails
    response = update_item(client=client, id=user1_item.id, params=params)
    assert response.status_code == 401, "Response did not fail to fetch item due to authorisation issue when it should have"

    # * user1 gives the group write permissions and user2 can write successfully
    set_active_user(user=user1)
    item1_group_roles[test_group].append('metadata-write')
    set_active_user(user=user1)
    set_group_access_roles(client=client, item=user1_item,
                           params=params, group_access_roles=item1_group_roles)
    set_active_user(user=user2)
    response = update_item(client=client, id=user1_item.id, params=params)
    assert response.status_code == 200

    # * now ensure that user2 cant change the auth config of the item to give themselves access
    item1_group_roles[test_group].append('admin')
    with pytest.raises(PermissionError):
        # should fail as wont be able to get the auth to update
        set_group_access_roles(client=client, item=user1_item,
                               params=params, group_access_roles=item1_group_roles)

    # get auth config as user1 then try directly put with user 2 should fail
    set_active_user(user=user1)
    auth_payload = get_auth_config(
        client=client, id=user1_item.id, params=params).dict()
    auth_payload['groups'] = item1_group_roles
    set_active_user(user=user2)
    with pytest.raises(PermissionError):
        put_auth_config(client=client, id=user1_item.id,
                        auth_payload=auth_payload, params=params)

    # * Test for changing owner
    # attempting to change owner as either should also fail as not even allowed to change owner at all.
    auth_payload['owner'] = user2.name
    with pytest.raises(PermissionError):
        put_auth_config(client=client, id=user1_item.id,
                        auth_payload=auth_payload, params=params)
    set_active_user(user=user1)
    with pytest.raises(AssertionError):
        put_auth_config(client=client, id=user1_item.id,
                        auth_payload=auth_payload, params=params)


@mock_dynamodb
@pytest.mark.parametrize("params", route_params, ids=make_specialised_list("History"))
def test_history(params: RouteParameters) -> None:
    """
    1. Create item and check history is single entry with reasonable owner/contents
    2. Update item, check history is two entries with correct owner/contents
    3. Update item from a different user, check history is correct 
    4. Intentially modify id to be non unique and check validator picks it up
    5. Seed item then update item and check history is correct
    6. Create item with multiple updates and check export observes
    """
    # Override the auth dependency

    app.dependency_overrides[read_user_protected_role_dependency] = user_protected_dependency_override
    app.dependency_overrides[read_write_user_protected_role_dependency] = user_protected_dependency_override

    default_table_setup()

    # parse some models
    create_response_model = params.typing_information.create_response
    assert create_response_model
    fetch_response_model = params.typing_information.fetch_response
    domain_info_model = params.typing_information.domain_info
    item_model = params.typing_information.item_model

    # 1. Create item and check history is single entry with reasonable owner/contents
    # ===============================================================================

    # get create route and payload
    create_route = get_route(action=RouteActions.CREATE, params=params)
    domain_info_for_create: DomainInfoBase = params.model_examples.domain_info[0]

    # run the post op
    response = client.post(
        create_route, json=py_to_dict(domain_info_for_create))
    check_status_success_true(response)

    # get the item
    item: GenericCreateResponse = create_response_model.parse_obj(
        response.json())

    # check the item has correct history
    assert item.created_item
    item_id = item.created_item.id
    history = item.created_item.history

    # check length
    assert len(
        history) == 1, f"Should have single item in history but had {len(history)}."

    # check item is parsable as type and is equal
    entry = domain_info_model.parse_obj(history[0].item)
    check_equal_models(entry, domain_info_model.parse_obj(item.created_item))

    # check basic properties of the history item
    history_item = history[0]

    # timestamp is reasonable?
    check_current_with_buffer(history_item.timestamp)

    # make sure username is correct
    assert history_item.username == test_username

    # check reason is not empty
    assert history_item.reason != ""

    # 2. Update item, check history is two entries with correct owner/contents
    # ===============================================================================

    # get other domain info
    domain_info_for_update: DomainInfoBase = params.model_examples.domain_info[1]
    update_route = get_route(action=RouteActions.UPDATE, params=params)

    # run the update op and check status

    # try updating without reason - should fail
    response = client.put(
        update_route, params={'id': item_id}, json=py_to_dict(domain_info_for_update))
    assert response.status_code == 400, f"Expected 400 status code due to missing update reason but got {response.status_code}."

    # now include
    reason = "fake reason"
    response = client.put(
        update_route, params={'id': item_id, 'reason': reason}, json=py_to_dict(domain_info_for_update))
    check_status_success_true(response)

    # fetch updated item and check status
    fetch_route = get_route(action=RouteActions.FETCH, params=params)
    response = client.get(
        fetch_route, params={'id': item_id})
    check_status_success_true(response)

    # parse contents
    updated_item = fetch_response_model.parse_obj(response.json()).item
    assert updated_item

    # check the history is updated appropriately
    history = updated_item.history

    # check length
    assert len(
        history) == 2, f"Should have two items in history but had {len(history)}."

    # check item is parsable as type and is equal - check first and second version
    # note that this is a stack i.e. first history should be latest
    new_entry = history[0]
    old_entry = history[1]

    entry = domain_info_model.parse_obj(new_entry.item)
    check_equal_models(entry, domain_info_for_update)

    entry = domain_info_model.parse_obj(old_entry.item)
    check_equal_models(entry, domain_info_for_create)

    # timestamp is reasonable?
    check_current_with_buffer(new_entry.timestamp)

    # make sure username is correct
    assert new_entry.username == test_username

    # check reason is not empty
    assert new_entry.reason == reason

    # 3. Update item from a different user, check history is correct
    # ===============================================================================

    # Reuse some auth logic to update the current dep overrides
    new_username_1 = "PedroThePowerfulPrince"
    user = TestingUser(new_username_1)

    def set_active_user(user: TestingUser) -> None:
        set_read_write_protected_role(app=app, username=user.name)

    set_active_user(user=user)

    # update back to version 0
    response = client.put(
        update_route, params={'id': item_id, 'reason': reason}, json=py_to_dict(domain_info_for_create))
    check_status_success_true(response)

    # fetch updated item and check status
    response = client.get(
        fetch_route, params={'id': item_id})
    check_status_success_true(response)

    # parse contents
    updated_item = fetch_response_model.parse_obj(response.json()).item
    assert updated_item

    # check the history is updated appropriately
    history = updated_item.history

    # check length
    assert len(
        history) == 3, f"Should have three items in history but had {len(history)}."

    # check item is parsable as type and is equal - check all versions
    # note that this is a stack i.e. first history should be latest
    new_entry = history[0]
    middle_entry = history[1]
    old_entry = history[2]

    # v3
    entry = domain_info_model.parse_obj(new_entry.item)
    check_equal_models(entry, domain_info_for_create)

    # v2
    entry = domain_info_model.parse_obj(middle_entry.item)
    check_equal_models(entry, domain_info_for_update)

    # v1
    entry = domain_info_model.parse_obj(old_entry.item)
    check_equal_models(entry, domain_info_for_create)

    # timestamp is reasonable?
    check_current_with_buffer(new_entry.timestamp)

    # make sure username is correct
    assert new_entry.username == new_username_1

    # check reason is not empty
    assert new_entry.reason == reason

    # return to default user
    app.dependency_overrides[read_user_protected_role_dependency] = user_protected_dependency_override
    app.dependency_overrides[read_write_user_protected_role_dependency] = user_protected_dependency_override

    # 4. Create duplicated ID and check validator
    # ===============================================================================

    # create a copy of item
    item_copy = py_to_dict(updated_item)

    # set the id of history item 2 to the same as 1
    item_copy['history'][1]['id'] = item_copy['history'][0]['id']

    # check parse fails with Validation error
    failed = False
    try:
        item_model.parse_obj(item_copy)
    except pydantic.ValidationError:
        failed = True

    assert failed, "Did not throw expected validation error with non unique Ids."

    # 5. Seed item then update item and check history is correct
    # ===============================================================================
    seed_route = get_route(action=RouteActions.SEED, params=params)
    seed_response_model = params.typing_information.seed_response
    assert seed_response_model
    # run the seed op
    response = client.post(seed_route)
    check_status_success_true(response)

    # get the item
    seed: GenericSeedResponse = seed_response_model.parse_obj(
        response.json())

    assert seed.seeded_item
    item_id = seed.seeded_item.id

    # now update the item - no reason provided (no reason needed for seed updates)
    response = client.put(
        update_route, params={'id': item_id}, json=py_to_dict(domain_info_for_create))
    check_status_success_true(response)

    # fetch updated item and check status
    fetch_route = get_route(action=RouteActions.FETCH, params=params)
    response = client.get(
        fetch_route, params={'id': item_id})
    check_status_success_true(response)

    # parse contents
    updated_item = fetch_response_model.parse_obj(response.json()).item
    assert updated_item

    # check the history is updated appropriately
    history = updated_item.history

    # check length
    assert len(
        history) == 1, f"Should have one item in history but had {len(history)}."

    # check item is parsable as type and is equal - check first and second version
    # note that this is a stack i.e. first history should be latest
    new_entry = history[0]

    entry = domain_info_model.parse_obj(new_entry.item)
    check_equal_models(entry, domain_info_for_create)

    # timestamp is reasonable?
    check_current_with_buffer(new_entry.timestamp)

    # make sure username is correct
    assert new_entry.username == test_username

    # check reason is not empty
    assert new_entry.reason != ""

    # 6. Create item with multiple updates and check export observes
    # ===============================================================================

    # override admin role
    app.dependency_overrides[admin_user_protected_role_dependency] = user_protected_dependency_override

    # delete the second item
    delete_route = get_route(action=RouteActions.DELETE, params=params)
    response = client.delete(delete_route, params={'id': item_id})
    check_status_success_true(response)

    # run the export
    response = client.get(admin_export_endpoint)

    # make sure it succeeded
    check_status_success_true(response)

    # now parse response
    export_response = RegistryExportResponse.parse_obj(response.json())
    items = export_response.items
    assert items is not None, "Items should not be none"
    assert len(
        items) == 1, f"There should be 2 items, but there was {len(items)}"

    # get first item and check history
    payload = items[0].item_payload

    # parse as model and pull out history
    history = item_model.parse_obj(payload).history

    # check length
    assert len(
        history) == 3, f"Should have three items in history but had {len(history)}."

    # check item is parsable as type and is equal - check all versions
    # note that this is a stack i.e. first history should be latest
    new_entry = history[0]
    middle_entry = history[1]
    old_entry = history[2]

    # v3
    entry = domain_info_model.parse_obj(new_entry.item)
    check_equal_models(entry, domain_info_for_create)

    # v2
    entry = domain_info_model.parse_obj(middle_entry.item)
    check_equal_models(entry, domain_info_for_update)

    # v1
    entry = domain_info_model.parse_obj(old_entry.item)
    check_equal_models(entry, domain_info_for_create)

    # =========================================================================
    # 7. Create an item, produce multiple versions, revert to previous version
    # =========================================================================

    # setup a fresh table context
    tname = "testrevert"
    empty_table_setup(tname)
    activate_registry_table(tname)

    # produce an item
    domain_info_for_create = params.model_examples.domain_info[0]

    # create a copy and modify with v1 tag
    item_1 = domain_info_model.parse_obj(
        py_to_dict(domain_info_for_create))
    item_1.display_name += "v1"

    # run the post op
    response = client.post(
        create_route, json=py_to_dict(item_1))
    check_status_success_true(response)

    # get the item
    item = create_response_model.parse_obj(
        response.json())

    # now modify the item and update a few times
    assert item.created_item

    item_id = item.created_item.id

    # create and update some versions
    # v2
    item_2 = domain_info_model.parse_obj(py_to_dict(domain_info_for_create))
    item_2.display_name += "v2"
    response = client.put(
        update_route, params={'id': item_id, 'reason': 'v2 update'}, json=py_to_dict(item_2))
    check_status_success_true(response)

    # v3
    item_3 = domain_info_model.parse_obj(py_to_dict(domain_info_for_create))
    item_3.display_name += "v3"
    response = client.put(
        update_route, params={'id': item_id, 'reason': 'v3 update'}, json=py_to_dict(item_3))
    check_status_success_true(response)

    # v4
    item_4 = domain_info_model.parse_obj(py_to_dict(domain_info_for_create))
    item_4.display_name += "v4"
    response = client.put(
        update_route, params={'id': item_id, 'reason': 'v4 update'}, json=py_to_dict(item_4))
    check_status_success_true(response)

    # look at the history after fetching
    response = client.get(
        fetch_route, params={'id': item_id})
    check_status_success_true(response)

    # parse contents
    returned_item_4 = fetch_response_model.parse_obj(response.json()).item
    assert returned_item_4

    # check the history is updated appropriately
    history = returned_item_4.history

    # check length
    assert len(
        history) == 4, f"Should have four items in history but had {len(history)}."

    # now revert to v1 -> v4 and check
    revert_route = get_route(action=RouteActions.REVERT, params=params)

    # V1

    # create payload and revert
    v1_revert_payload = ItemRevertRequest(
        id=item_id,
        history_id=history[-1].id,
        reason="test revert to v1"
    )
    response = client.put(
        url=revert_route, json=py_to_dict(v1_revert_payload))
    check_status_success_true(response)

    # fetch item
    response = client.get(
        fetch_route, params={'id': item_id})
    check_status_success_true(response)
    returned_item = fetch_response_model.parse_obj(response.json()).item
    assert returned_item

    # check item contains vX content
    assert returned_item.display_name.endswith("v1")

    # V2

    # create payload and revert
    v2_revert_payload = ItemRevertRequest(
        id=item_id,
        history_id=history[-2].id,
        reason="test revert to v2"
    )
    response = client.put(
        url=revert_route, json=py_to_dict(v2_revert_payload))
    check_status_success_true(response)

    # fetch item
    response = client.get(
        fetch_route, params={'id': item_id})
    check_status_success_true(response)
    returned_item = fetch_response_model.parse_obj(response.json()).item
    assert returned_item

    # check item contains vX content
    assert returned_item.display_name.endswith("v2")

    # V3

    # create payload and revert
    v3_revert_payload = ItemRevertRequest(
        id=item_id,
        history_id=history[-3].id,
        reason="test revert to v3"
    )
    response = client.put(
        url=revert_route, json=py_to_dict(v3_revert_payload))
    check_status_success_true(response)

    # fetch item
    response = client.get(
        fetch_route, params={'id': item_id})
    check_status_success_true(response)
    returned_item = fetch_response_model.parse_obj(response.json()).item
    assert returned_item

    # check item contains vX content
    assert returned_item.display_name.endswith("v3")

    # V4

    # create payload and revert
    v4_revert_payload = ItemRevertRequest(
        id=item_id,
        history_id=history[-4].id,
        reason="test revert to v4"
    )
    response = client.put(
        url=revert_route, json=py_to_dict(v4_revert_payload))
    check_status_success_true(response)

    # fetch item
    response = client.get(
        fetch_route, params={'id': item_id})
    check_status_success_true(response)
    returned_item = fetch_response_model.parse_obj(response.json()).item
    assert returned_item

    # check item contains vX content
    assert returned_item.display_name.endswith("v4")

    # now check that after those 4 reverts, we have 8 history items
    history = returned_item.history
    assert len(
        history) == 8, f"After four versions and four updates, we should have 8 updates."

    # check the v4 revert domain info contents seems reasonable
    # i.e. that the latest version is == v4 domain contents
    check_equal_models(item_4, history[0].item)

    # revert as other user and check username is present
    new_username_2 = "JonoTheJubilantJock"
    user = TestingUser(new_username_2)
    set_active_user(user=user)

    # revert back to v1
    response = client.put(
        url=revert_route, json=py_to_dict(v1_revert_payload))
    check_status_success_true(response)

    # fetch item
    response = client.get(
        fetch_route, params={'id': item_id})
    check_status_success_true(response)
    returned_item = fetch_response_model.parse_obj(response.json()).item
    assert returned_item

    # check item contains vX content
    assert returned_item.display_name.endswith("v1")

    history = returned_item.history
    assert len(
        history) == 9, f"After four versions and five updates, we should have 9 updates."

    # check the v1 revert domain info contents seems reasonable
    # i.e. that the latest version is == v1 domain contents
    check_equal_models(item_1, history[0].item)

    entry = history[0]

    # check username
    assert entry.username == new_username_2, f"Expected username {new_username_2} but had {entry.username}."

    # check previous update uses other username
    assert history[1].username == test_username, f"Expected username {test_username} but had {history[1].username}."


@mock_dynamodb
def test_create_person_ethics_approved_validation(override_perform_validation_config_dependency: Generator) -> None:
    """Test that a person can be created with ethics approved"""

    # overide auth dependency

    app.dependency_overrides[read_user_protected_role_dependency] = user_protected_dependency_override
    app.dependency_overrides[read_write_user_protected_role_dependency] = user_protected_dependency_override

    default_table_setup()

    person_params = get_item_subtype_route_params(
        item_subtype=ItemSubType.PERSON)
    person_domain_info = person_params.model_examples.domain_info[0]
    person_domain_info.ethics_approved = True

    # should succeed
    create_item_from_domain_info_successfully(
        client=client, params=person_params, domain_info=person_domain_info)

    # now try create person item without ethics approved
    person_domain_info.ethics_approved = False
    create_resp = create_item_from_domain_info(
        client=client, params=person_params, domain_info=person_domain_info)
    # curr_route = get_route(RouteActions.CREATE, params=person_params)
    # create_resp = client.post(
    #    curr_route, json=json.loads(person_domain_info.json()))

    # assert returns ok but with error
    assert create_resp.status_code == 200
    created_item = GenericCreateResponse.parse_obj(create_resp.json())
    assert not created_item.status.success, "Item should not have been created as ethics approved was not set to true"
