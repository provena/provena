import tests.env_setup
import pytest
from typing import Tuple, Generator
from fastapi.testclient import TestClient
from main import app
from dependencies.dependencies import user_general_dependency, read_user_protected_role_dependency, read_write_user_protected_role_dependency, admin_user_protected_role_dependency
from SharedInterfaces.DataStoreAPI import *
from KeycloakFastAPI.Dependencies import User, ProtectedRole
from config import Config, get_settings, base_config
from tests.test_config import *

auth_test_config = Config(
    stage=stage,
    keycloak_endpoint=base_config.keycloak_endpoint,
    service_account_secret_arn="",
    # This should not be used
    job_api_endpoint="",
    registry_api_endpoint="",
    mock_graph_db=False,
    neo4j_host="",
    neo4j_port=0
)

client = TestClient(app)


write_role_secured_endpoints = [
    ("/check-access/check-write-access", "GET"),
    ("/model_run/register", "POST")
]

read_role_secured_endpoints = [
    ("/check-access/check-read-access", "GET"),
    ("/explore/upstream", "GET"),
    ("/explore/downstream", "GET"),
]

admin_role_secured_endpoints: List[Tuple[str, str]] = [
    ("/model_run/register_sync", "POST")
]

all_secured_endpoints = write_role_secured_endpoints + \
    read_role_secured_endpoints + admin_role_secured_endpoints

general_secured_endpoints = [
    ("/check-access/check-general-access", "GET"),
]

unsecured_endpoints = [
    ("/", "GET"),
]


@pytest.fixture(scope="function", autouse=True)
def config_override() -> Generator:
    # setup settings
    app.dependency_overrides[get_settings] = lambda: auth_test_config
    # run test
    yield
    # clean up
    app.dependency_overrides = {}


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
    # override app config
    app.dependency_overrides[get_settings] = lambda: auth_test_config

    # Checks general access once overridden

    # Override the auth dependency
    app.dependency_overrides[user_general_dependency] = user_general_dependency_override

    response = client.get("/check-access/check-general-access")
    assert response.status_code == 200
    assert response.json() == {
        "username": test_email,
        "roles": ["test-role"],
        "access_token": "faketoken1234",
        "email": test_email
    }


def test_check_write_protected_access() -> None:
    # override app config
    app.dependency_overrides[get_settings] = lambda: auth_test_config

    # Checks protected role access once overridden

    # Override the auth dependency
    app.dependency_overrides[read_write_user_protected_role_dependency] = user_protected_dependency_override

    response = client.get("/check-access/check-write-access")
    assert response.status_code == 200
    assert response.json() == {
        "username": test_email,
        "roles": ["test-role"],
        "access_token": "faketoken1234",
        "email": test_email
    }


def test_check_admin_protected_access() -> None:
    # Checks protected role access once overridden

    # Override the auth dependency
    app.dependency_overrides[admin_user_protected_role_dependency] = user_protected_dependency_override

    response = client.get("/check-access/check-admin-access")
    assert response.status_code == 200
    assert response.json() == {
        "username": test_email,
        "roles": ["test-role"],
        "access_token": "faketoken1234",
        "email": test_email
    }


def test_check_read_protected_access() -> None:
    # Checks protected role access once overridden
    # Override the auth dependency
    app.dependency_overrides[read_user_protected_role_dependency] = user_protected_dependency_override

    response = client.get("/check-access/check-read-access")
    assert response.status_code == 200
    assert response.json() == {
        "username": test_email,
        "roles": ["test-role"],
        "access_token": "faketoken1234",
        "email": test_email
    }


def access_denied_check_role_secured(client: Any, headers: Dict[str, str]) -> None:

    # Testing harness which checks all secured endpoints to
    # ensure 401 http codes (role secured)
    for endpoint, method in all_secured_endpoints:
        if method == "GET":
            response = client.get(endpoint, headers=headers)
        elif method == "POST":
            response = client.post(endpoint, headers=headers)
        else:
            assert False, f"Unknown {method =}"

        assert response.status_code == 401


def access_denied_check_general_secured(client: Any, headers: Dict[str, str]) -> None:
    # Testing harness which checks all secured endpoints to
    # ensure 401 http codes (general secured)
    for endpoint, method in general_secured_endpoints:
        if method == "GET":
            response = client.get(endpoint, headers=headers)
        elif method == "POST":
            response = client.post(endpoint, headers=headers)
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
    forms = ['Bearer 12345', 'Bearer ', 'Bearer', '12345', '']
    token = str(open('tests/resources/expired_token.txt', 'r').read())
    headers = {
        'Authorization': f'Bearer {token}'
    }
    access_denied_check_role_secured(client, headers)
    access_denied_check_general_secured(client, headers)

# Deprecated
# def test_access_denied_invalid_token() -> None:
#    # Checks that providing valid token but for an invalid
#    # idp/signature denies access
#    token = str(open('tests/resources/invalid_token.txt', 'r').read())
#    headers = {
#        'Authorization': f'Bearer {token}'
#    }
#    access_denied_check_role_secured(client, headers)
#    access_denied_check_general_secured(client, headers)
