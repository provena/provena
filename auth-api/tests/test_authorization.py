import tests.env_setup
import pytest
from KeycloakFastAPI.Dependencies import User, ProtectedRole
from SharedInterfaces.AuthAPI import *
from main import app
from dependencies.dependencies import user_general_dependency
from config import Config, get_settings, base_config
from typing import Any, Generator
from fastapi.testclient import TestClient
from tests.config import *

client = TestClient(app)


# test wide scope for creating config


@pytest.fixture(scope="session", autouse=True)
def provide_global_config() -> Config:
    return Config(
        keycloak_endpoint=base_config.keycloak_endpoint,
        stage=base_config.stage,
        access_request_table_name=test_access_request_table_name,
        user_groups_table_name=test_user_group_table_name,

        # disable registry lookups and set null values
        link_update_registry_connection=False,
        registry_api_endpoint="",
        username_person_link_table_name="",
        username_person_link_table_person_index_name="",
        service_account_secret_arn="",
        job_api_endpoint="",
        access_request_email_address="",

    )

# for each function, override settings and clear deps at end


@pytest.fixture(scope="function", autouse=True)
def override_config_dependency(provide_global_config: Config) -> Generator:
    app.dependency_overrides[get_settings] = lambda: provide_global_config
    yield
    app.dependency_overrides = {}


role_secured_endpoints = [
    ("/access-control/admin/change-request-state", "POST"),
    ("/access-control/admin/all-pending-request-history", "GET"),
    ("/access-control/admin/all-request-history", "GET"),
    ("/access-control/admin/user-pending-request-history", "GET"),
    ("/access-control/admin/user-request-history", "GET"),
    ("/groups/admin/list_groups", "GET"),
    ("/groups/admin/describe_group", "GET"),
    ("/groups/admin/list_members", "GET"),
    ("/groups/admin/list_user_membership", "GET"),
    ("/groups/admin/check_membership", "GET"),
    ("/groups/admin/add_member", "POST"),
    ("/groups/admin/remove_member", "DELETE"),
    ("/groups/admin/add_group", "POST"),
    ("/groups/admin/remove_group", "DELETE"),
    ("/groups/admin/update_group", "PUT"),
    ("/link/admin/assign", "POST"),
    ("/link/admin/lookup", "GET"),
]

general_secured_endpoints = [
    ("/check-access/general", "GET"),
    ("/access-control/user/request-change", "POST"),
    ("/access-control/user/generate-access-report", "GET"),
    ("/access-control/user/request-history", "GET"),
    ("/access-control/user/pending-request-history", "GET"),
    ("/link/user/assign", "POST"),
    ("/link/user/lookup", "GET"),
]

unsecured_endpoints = [
    ("/", "GET"),
    ("/check-access/public", "GET")
]


def test_health_check() -> None:
    # Checks that the health check endpoint responds
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Health check successful."}


async def user_general_dependency_override() -> User:
    """    user_general_dependency_override
        Creates an override for user dependency

        Returns
        -------
         : User
            The overide.

        See Also (optional)
        --------

        Examples (optional)
        --------
    """
    return User(username=test_email, roles=['test-role'], access_token="faketoken1234", email=test_email)


async def user_protected_dependency_override() -> ProtectedRole:
    """    user_protected_dependency_override
        Creates override for the role protected user dependency

        Returns
        -------
         : ProtectedRole
            The overide. 

        See Also (optional)
        --------

        Examples (optional)
        --------
    """

    return ProtectedRole(access_roles=['test-role'],
                         user=User(username=test_email,
                                   roles=['test-role'],
                                   access_token="faketoken1234",
                                   email=test_email)
                         )


def test_check_general_access() -> None:
    # Checks general access once overridden

    # Override the auth dependency
    app.dependency_overrides[user_general_dependency] = user_general_dependency_override

    response = client.get("/check-access/general")
    assert response.status_code == 200
    assert response.json() == {
        "username": test_email,
        "roles": ["test-role"],
        "access_token": "faketoken1234",
        "email": test_email
    }

    # Clean up dependencies
    app.dependency_overrides = {}


def access_denied_check_role_secured(client: Any, headers: Any) -> None:
    # Testing harness which checks all secured endpoints to
    # ensure 401 http codes (role secured)
    for endpoint, method in role_secured_endpoints:
        if method == "GET":
            response = client.get(endpoint, headers=headers)
        elif method == "POST":
            response = client.post(endpoint, headers=headers)
        elif method == "PUT":
            response = client.put(endpoint, headers=headers)
        elif method == "DELETE":
            response = client.delete(endpoint, headers=headers)
        else:
            assert False, f"Unknown {method =}"

        assert response.status_code == 401


def access_denied_check_general_secured(client: Any, headers: Any) -> None:
    # Testing harness which checks all secured endpoints to
    # ensure 401 http codes (general secured)
    for endpoint, method in general_secured_endpoints:
        if method == "GET":
            response = client.get(endpoint, headers=headers)
        elif method == "POST":
            response = client.post(endpoint, headers=headers)
        elif method == "PUT":
            response = client.put(endpoint, headers=headers)
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


# Deprecated
# def test_access_denied_expired_token() -> None:
#    # Checks that providing expired valid denies access
#    forms = ['Bearer 12345', 'Bearer ', 'Bearer', '12345', '']
#    token = str(open('tests/resources/expired_token.txt', 'r').read())
#    headers = {
#        'Authorization': f'Bearer {token}'
#    }
#    access_denied_check_role_secured(client, headers)
#    access_denied_check_general_secured(client, headers)
