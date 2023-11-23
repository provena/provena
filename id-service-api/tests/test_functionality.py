import tests.env_setup
from tests.test_config import *
from main import app
from fastapi.testclient import TestClient
from config import Config, base_config, get_settings
import pytest
from typing import Generator
from KeycloakFastAPI.Dependencies import ProtectedRole, User
from dependencies.dependencies import read_user_protected_role_dependency, read_write_user_protected_role_dependency
from SharedInterfaces.HandleAPI import *
from SharedInterfaces.HandleModels import *
from tests.helpers import *


client = TestClient(app)


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


@pytest.fixture(scope="session", autouse=True)
def provide_global_config() -> Config:
    return Config(
        stage=base_config.stage,
        keycloak_endpoint=base_config.keycloak_endpoint,
    )


@pytest.fixture(scope="function", autouse=True)
def override_config_dependency(provide_global_config: Config) -> Generator:
    app.dependency_overrides[get_settings] = lambda: provide_global_config
    yield
    app.dependency_overrides = {}


def test_health_check() -> None:
    # Checks that the health check endpoint responds
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Health check successful."}


def test_schema() -> None:
    # Checks that the schema endpoint provides valid
    # Json and that it matches the file contents exactly

    # Override the auth dependency
    app.dependency_overrides[read_user_protected_role_dependency] = user_protected_dependency_override

    assert True


def test_full_handle_workflow() -> None:
    # NOTE we don't test list as it's very slow and uses a lot of bandwidth

    # override dependencies
    app.dependency_overrides[read_write_user_protected_role_dependency] = user_protected_dependency_override
    app.dependency_overrides[read_user_protected_role_dependency] = user_protected_dependency_override

    # =============
    # mint a handle
    # =============

    endpoint = mint_endpoint
    request = MintRequest(value_type=default_value_type, value=test_url_1)

    handle = parse_handle_object_successfully(
        client.post(url=endpoint, json=py_to_dict(request)))

    # =============
    # get a handle
    # =============
    endpoint = get_endpoint

    # failure case (incorrect id)
    parse_handle_unsuccessfully(
        client.get(url=endpoint, params={'id': incorrect_id}))

    # success case
    retrieved_handle = parse_handle_object_successfully(
        client.get(url=endpoint, params={'id': handle.id}))

    assert retrieved_handle.id == handle.id
    assert handle.properties[0] == retrieved_handle.properties[0]

    # ============
    # add a value
    # ============
    endpoint = add_endpoint
    request = AddValueRequest(
        id=handle.id, value_type=default_value_type, value=test_url_2)

    added_handle = parse_handle_object_successfully(
        client.post(url=endpoint, json=py_to_dict(request)))

    # check property index 1 and 2 match as expected
    prop_index_1 = get_property_by_index(
        handle=added_handle,
        index=1
    )
    prop_index_2 = get_property_by_index(
        handle=added_handle,
        index=2
    )
    assert prop_index_1.value == test_url_1
    assert prop_index_2.value == test_url_2

    # =====================
    # add a value by index
    # =====================
    endpoint = add_by_index_endpoint

    # failure case (add at existing index)
    bad_index = 1
    request = AddValueIndexRequest(
        id=handle.id, index=bad_index, value_type=default_value_type, value=test_url_1)
    parse_handle_unsuccessfully(
        client.post(url=endpoint, json=py_to_dict(request)))

    # success case
    test_index = 10
    request = AddValueIndexRequest(
        id=handle.id, index=test_index, value_type=default_value_type, value=test_url_1)

    index_added_handle = parse_handle_object_successfully(
        client.post(url=endpoint, json=py_to_dict(request)))

    # check property index 1, 2 and 10 match as expected
    prop_index_1 = get_property_by_index(
        handle=index_added_handle,
        index=1
    )
    prop_index_2 = get_property_by_index(
        handle=index_added_handle,
        index=2
    )
    prop_index_10 = get_property_by_index(
        handle=index_added_handle,
        index=10
    )
    assert prop_index_1.value == test_url_1
    assert prop_index_2.value == test_url_2
    assert prop_index_10.value == test_url_1

    # ======================
    # modify value by index
    # ======================
    endpoint = modify_by_index_endpoint

    # failure case (non existent index)
    bad_index = 5
    request = ModifyRequest(
        id=handle.id, index=bad_index, value=test_url_2)
    parse_handle_unsuccessfully(
        client.put(url=endpoint, json=py_to_dict(request)))

    # success case
    test_index = 10
    request = ModifyRequest(
        id=handle.id, index=test_index, value=test_url_2)

    index_modified_handle = parse_handle_object_successfully(
        client.put(url=endpoint, json=py_to_dict(request)))

    prop_index_10 = get_property_by_index(
        handle=index_modified_handle,
        index=10
    )
    assert prop_index_10.value == test_url_2

    # ================
    # remove by index
    # ================
    endpoint = remove_by_index_endpoint

    # failure case (non existent index)
    bad_index = 5
    request = RemoveRequest(
        id=handle.id, index=bad_index)
    parse_handle_unsuccessfully(
        client.post(url=endpoint, json=py_to_dict(request)))

    # success case
    request = RemoveRequest(
        id=handle.id, index=test_index)
    index_removed_handle = parse_handle_object_successfully(
        client.post(url=endpoint, json=py_to_dict(request)))

    # check index 10 no longer exists
    check_no_property_by_index(handle=index_removed_handle, index=test_index)
