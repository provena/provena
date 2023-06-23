import tests.env_setup
from tests.config import test_resource_table_name, test_email, test_stage
from typing import Dict, Generator
from KeycloakFastAPI.Dependencies import User, ProtectedRole
from SharedInterfaces.RegistryAPI import *
from dependencies.dependencies import user_general_dependency, read_user_protected_role_dependency, read_write_user_protected_role_dependency, admin_user_protected_role_dependency
from main import app, route_configs, ITEM_CATEGORY_ROUTE_MAP, ITEM_SUB_TYPE_ROUTE_MAP
from fastapi.testclient import TestClient
from SharedInterfaces.RegistryModels import *
from config import Config, get_settings, base_config
from RegistrySharedFunctionality.RegistryRouteActions import ROUTE_ACTION_CONFIG_MAP, RouteAccessLevel
import pytest

client = TestClient(app)

# test wide scope for creating config
@pytest.fixture(scope="session", autouse=True)
def provide_global_config() -> Config:
    return Config(
        # no user auth testing!
        enforce_user_auth=False,
        enforce_special_proxy_roles=False,
        auth_api_endpoint="",

        keycloak_endpoint=base_config.keycloak_endpoint,
        stage=base_config.stage,
        registry_table_name=test_resource_table_name,
        auth_table_name=test_resource_table_name,
        lock_table_name=test_resource_table_name,
        handle_api_endpoint="",
        service_account_secret_arn="",
        mock_handle=True,
        # dont perform user link validation
        enforce_user_links=False,
    )

# for each function, override settings and clear deps at end


@pytest.fixture(scope="function", autouse=True)
def override_config_dependency(provide_global_config: Config) -> Generator:
    app.dependency_overrides[get_settings] = lambda: provide_global_config
    yield
    app.dependency_overrides = {}


read_role_secured_endpoints = [
    ("/check-access/check-read-access", "GET"),
    ("/registry/general/list", "POST"),
]

write_role_secured_endpoints = [
    ("/check-access/check-write-access", "GET"),
]


admin_role_secured_endpoints = [
    ("/check-access/check-admin-access", "GET"),
]

for r_config in route_configs:
    prefix = f"/{ITEM_CATEGORY_ROUTE_MAP[r_config.desired_category]}/{ITEM_SUB_TYPE_ROUTE_MAP[r_config.desired_subtype]}"
    for r_action in r_config.desired_actions:
        action_config = ROUTE_ACTION_CONFIG_MAP[r_action]
        if action_config.access_level == RouteAccessLevel.READ:
            read_role_secured_endpoints.append(
                (f"/registry{prefix}{action_config.path}",
                 action_config.method.value)
            )
        if action_config.access_level == RouteAccessLevel.WRITE:
            read_role_secured_endpoints.append(
                (f"/registry{prefix}{action_config.path}",
                 action_config.method.value)
            )
            write_role_secured_endpoints.append(
                (f"/registry{prefix}{action_config.path}",
                 action_config.method.value)
            )
        if action_config.access_level == RouteAccessLevel.ADMIN:
            read_role_secured_endpoints.append(
                (f"/registry{prefix}{action_config.path}",
                 action_config.method.value)
            )
            write_role_secured_endpoints.append(
                (f"/registry{prefix}{action_config.path}",
                 action_config.method.value)
            )
            admin_role_secured_endpoints.append(
                (f"/registry{prefix}{action_config.path}",
                 action_config.method.value)
            )

all_secured_endpoints = write_role_secured_endpoints + \
    read_role_secured_endpoints + admin_role_secured_endpoints

general_secured_endpoints = [
    ("/check-access/check-general-access", "GET"),
]

unsecured_endpoints = [
    ("/", "GET"),
]


def test_health_check() -> None:
    # Checks that the health check endpoint responds
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Health check successful."}


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


def test_check_general_access() -> None:
    # Checks general access once overridden

    # Override the auth dependency
    app.dependency_overrides[user_general_dependency] = user_general_dependency_override

    response = client.get("/check-access/check-general-access")
    assert response.status_code == 200
    assert response.json() == {
        "username": "testuser@gmail.com",
        "roles": ["test-role"],
        "access_token": "faketoken1234",
        "email": test_email
    }

    # Clean up dependencies
    app.dependency_overrides = {}


def test_check_write_protected_access() -> None:
    # Checks protected role access once overridden

    # Override the auth dependency
    app.dependency_overrides[read_write_user_protected_role_dependency] = user_protected_dependency_override

    response = client.get("/check-access/check-write-access")
    assert response.status_code == 200
    assert response.json() == {
        "username": "testuser@gmail.com",
        "roles": ["test-role"],
        "access_token": "faketoken1234",
        "email": test_email
    }
    # Clean up dependencies
    app.dependency_overrides = {}


def test_check_admin_protected_access() -> None:
    # Checks protected role access once overridden

    # Override the auth dependency
    app.dependency_overrides[admin_user_protected_role_dependency] = user_protected_dependency_override

    response = client.get("/check-access/check-admin-access")
    assert response.status_code == 200
    assert response.json() == {
        "username": "testuser@gmail.com",
        "roles": ["test-role"],
        "access_token": "faketoken1234",
        "email": test_email
    }
    # Clean up dependencies
    app.dependency_overrides = {}


def test_check_read_protected_access() -> None:
    # Checks protected role access once overridden

    # Override the auth dependency
    app.dependency_overrides[read_user_protected_role_dependency] = user_protected_dependency_override

    response = client.get("/check-access/check-read-access")
    assert response.status_code == 200
    assert response.json() == {
        "username": "testuser@gmail.com",
        "roles": ["test-role"],
        "access_token": "faketoken1234",
        "email": test_email
    }
    # Clean up dependencies
    app.dependency_overrides = {}


def access_denied_check_role_secured(client: Any, headers: Dict[str, str]) -> None:
    # Testing harness which checks all secured endpoints to
    # ensure 401 http codes (role secured)
    for endpoint, method in all_secured_endpoints:
        if method == "GET":
            response = client.get(endpoint, headers=headers)
        elif method == "PUT":
            response = client.put(endpoint, headers=headers)
        elif method == "POST":
            response = client.post(endpoint, headers=headers)
        elif method == "DELETE":
            response = client.delete(endpoint, headers=headers)
        else:
            assert False, f"Unknown {method =}"

        if response.status_code != 401:
            print("hello")

        assert response.status_code == 401


def access_denied_check_general_secured(client: Any, headers: Dict[str, str]) -> None:
    # Testing harness which checks all secured endpoints to
    # ensure 401 http codes (general secured)
    for endpoint, method in general_secured_endpoints:
        if method == "GET":
            response = client.get(endpoint, headers=headers)
        elif method == "PUT":
            response = client.put(endpoint, headers=headers)
        elif method == "POST":
            response = client.post(endpoint, headers=headers)
        elif method == "DELETE":
            response = client.delete(endpoint, headers=headers)
        else:
            assert False, f"Unknown {method =}"

        assert response.status_code == 401


def test_access_denied_no_token() -> None:
    # Checks that providing no auth header denies access
    access_denied_check_role_secured(client, {})
    access_denied_check_general_secured(client, {})


def test_access_denied_misformed_token() -> None:
    # Checks that providing misformed header denies access
    forms = ['Bearer 12345', 'Bearer ', 'Bearer', '12345', '']
    for header in forms:
        headers = {
            'Authorization': header
        }
        access_denied_check_role_secured(client, headers)
        access_denied_check_general_secured(client, headers)


def test_access_denied_expired_token() -> None:
    # Checks that providing expired valid denies access
    token = str(open('tests/resources/expired_token.txt', 'r').read())
    headers = {
        'Authorization': f'Bearer {token}'
    }
    access_denied_check_role_secured(client, headers)
    access_denied_check_general_secured(client, headers)