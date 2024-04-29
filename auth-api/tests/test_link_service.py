import tests.env_setup
from config import Config, get_settings, base_config
from dataclasses import dataclass
from KeycloakFastAPI.Dependencies import User
from ProvenaInterfaces.AuthAPI import *
from ProvenaInterfaces.DataStoreAPI import *
from main import app
from dependencies.dependencies import sys_admin_write_dependency, sys_admin_read_dependency, sys_admin_admin_dependency, user_general_dependency
from fastapi.testclient import TestClient
from typing import Callable, Optional, List, Any, Generator
import os
import json
from moto import mock_dynamodb  # type: ignore
from tests.config import *
import pytest  # type: ignore
import boto3  # type: ignore
import random
from tests.helpers import *
from tests.username_person_link_helpers import *

client = TestClient(app)

# test wide scope for creating config


def default_config() -> Config:
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


@pytest.fixture(scope="session", autouse=True)
def provide_global_config() -> Config:
    return default_config()

# for each function, override settings and clear deps at end


@pytest.fixture(scope="function", autouse=True)
def override_config_dependency(provide_global_config: Config) -> Generator:
    app.dependency_overrides[get_settings] = lambda: provide_global_config
    yield
    app.dependency_overrides = {}


@pytest.fixture(scope='function', autouse=True)
def aws_credentials() -> None:
    """Mocked AWS Credentials for moto."""
    os.environ['AWS_ACCESS_KEY_ID'] = 'testing'
    os.environ['AWS_SECRET_ACCESS_KEY'] = 'testing'
    os.environ['AWS_SECURITY_TOKEN'] = 'testing'
    os.environ['AWS_SESSION_TOKEN'] = 'testing'
    os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'


@pytest.fixture(scope="function")
def config_link_table(provide_global_config: Config) -> Config:
    config = provide_global_config
    config.username_person_link_table_name = link_table_name
    config.username_person_link_table_person_index_name = link_gsi_name
    return config


def test_health_check() -> None:
    # Checks that the health check endpoint responds
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Health check successful."}


def generate_dep_override(username: str, email: str) -> Any:
    async def dep_override() -> User:
        # Creates an override for user dependency
        return User(username=username, roles=['test-role'], access_token="faketoken1234", email=email)
    return dep_override


user_general_dependency_override = generate_dep_override(
    username=test_email, email=test_email)


def checkout_email_all_deps(email: str) -> None:
    dep = generate_dep_override(username=email, email=email)
    app.dependency_overrides[sys_admin_read_dependency] = dep
    app.dependency_overrides[sys_admin_write_dependency] = dep
    app.dependency_overrides[user_general_dependency] = dep


@mock_dynamodb
def test_user_lookup(config_link_table: Config) -> None:
    # config
    config = config_link_table

    # setup the link table
    botoclient = boto3.client('dynamodb')
    setup_link_table(botoclient=botoclient, table_name=config.username_person_link_table_name,
                     gsi_name=config.username_person_link_table_person_index_name)

    # checkout to 1@gmail.com
    email_1 = "1@gmail.com"
    checkout_email_all_deps(email_1)

    # lookup with no entry (no username)
    user_lookup_user_assert_missing(client=client)

    # lookup with no entry (specify username)
    user_lookup_user_assert_missing(client=client, username=email_1)

    # assign entry successfully
    person_1_id = "1"
    user_assign_link_assert_success(client=client, person_id=person_1_id)

    # lookup with successful entry (no username)
    user_lookup_user_assert_success(client=client, check_id=person_1_id)

    # lookup with successful entry (specify username)
    user_lookup_user_assert_success(
        client=client, check_id=person_1_id, username=email_1)

    # make sure that user 2 fails from user 1
    email_2 = "2@gmail.com"

    # lookup with no entry (specify username)
    user_lookup_user_assert_missing(client=client, username=email_2)

    # checkout to new username
    checkout_email_all_deps(email_2)

    # lookup with no entry (no username)
    user_lookup_user_assert_missing(client=client)

    # lookup with no entry (specify username)
    user_lookup_user_assert_missing(client=client, username=email_2)

    # make sure user 2 can see user 1
    user_lookup_user_assert_success(
        client=client, check_id=person_1_id, username=email_1)

    # assign entry successfully
    person_2_id = "2"
    user_assign_link_assert_success(client=client, person_id=person_2_id)

    # lookup other username and ensure succeeds (no username)
    user_lookup_user_assert_success(client=client, check_id=person_2_id)

    # lookup other username and ensure succeeds (specify username)
    user_lookup_user_assert_success(
        client=client, check_id=person_2_id, username=email_2)


@mock_dynamodb
def test_user_assign(config_link_table: Config) -> None:
    # config
    config = config_link_table

    # setup the link table
    botoclient = boto3.client('dynamodb')
    setup_link_table(botoclient=botoclient, table_name=config.username_person_link_table_name,
                     gsi_name=config.username_person_link_table_person_index_name)

    # checkout to 1@gmail.com
    email_1 = "1@gmail.com"
    checkout_email_all_deps(email_1)

    # lookup with no entry
    user_lookup_user_assert_missing(client=client)

    # assign entry - empty string
    person_1_id = ""
    user_assign_user_assert_parse_error(client=client, person_id=person_1_id)

    # assign successfully
    person_1_id = "1"
    user_assign_link_assert_success(client=client, person_id=person_1_id)

    # assign same payload - should fail
    user_assign_link_assert_fail(client=client, person_id=person_1_id)

    # assign different payload - should fail
    new_id = person_1_id + "1"
    user_assign_link_assert_fail(client=client, person_id=new_id)

    # lookup with successful entry (no username)
    user_lookup_user_assert_success(client=client, check_id=person_1_id)


@mock_dynamodb
def test_admin_assign_and_clear(config_link_table: Config) -> None:
    # config
    config = config_link_table

    # setup the link table
    botoclient = boto3.client('dynamodb')
    setup_link_table(botoclient=botoclient, table_name=config.username_person_link_table_name,
                     gsi_name=config.username_person_link_table_person_index_name)

    # assign on self - check force behaviour

    # checkout to 1@gmail.com
    email_1 = "1@gmail.com"
    checkout_email_all_deps(email_1)

    # lookup with no entry
    user_lookup_user_assert_missing(client=client)

    # assign entry - empty string
    person_1_id = ""
    admin_assign_link_assert_parse_error(
        username=email_1, force=False, client=client, person_id=person_1_id)

    # assign successfully
    person_1_id = "1"
    admin_assign_link_assert_success(
        username=email_1, force=False, client=client, person_id=person_1_id)

    # assign same payload - should fail (force= False)
    admin_assign_link_assert_fail(
        username=email_1, force=False, client=client, person_id=person_1_id)

    # assign same payload - should succeed (force= True)
    admin_assign_link_assert_success(
        username=email_1, force=True, client=client, person_id=person_1_id)

    # assign new payload - should fail (force= False)
    person_1_id = "1v2"
    admin_assign_link_assert_fail(
        username=email_1, force=False, client=client, person_id=person_1_id)

    # assign same payload - should succeed (force= True)
    admin_assign_link_assert_success(
        username=email_1, force=True, client=client, person_id=person_1_id)

    # now run on person 2 from person 1
    email_2 = "2@gmail.com"

    # lookup with no entry
    user_lookup_user_assert_missing(client=client, username=email_2)

    # assign entry - empty string
    person_2_id = ""
    admin_assign_link_assert_parse_error(
        username=email_2, force=False, client=client, person_id=person_2_id)

    # assign successfully
    person_2_id = "2"
    admin_assign_link_assert_success(
        username=email_2, force=False, client=client, person_id=person_2_id)

    # assign same payload - should fail (force= False)
    admin_assign_link_assert_fail(
        username=email_2, force=False, client=client, person_id=person_2_id)

    # assign same payload - should succeed (force= True)
    admin_assign_link_assert_success(
        username=email_2, force=True, client=client, person_id=person_2_id)

    # assign new payload - should fail (force= False)
    person_2_id = "2v2"
    admin_assign_link_assert_fail(
        username=email_2, force=False, client=client, person_id=person_2_id)

    # assign same payload - should succeed (force= True)
    admin_assign_link_assert_success(
        username=email_2, force=True, client=client, person_id=person_2_id)

    # now lookup from person 2
    checkout_email_all_deps(email_2)
    user_lookup_user_assert_success(client=client, check_id=person_2_id)

    # check back out to 'admin'
    checkout_email_all_deps(email_1)

    # clear person 2 item
    admin_clear_link(client=client, username=email_2)

    # go back to person 2
    checkout_email_all_deps(email_2)

    # make sure gone
    user_lookup_user_assert_missing(client=client)


@mock_dynamodb
def test_reverse_lookup(config_link_table: Config) -> None:
    # config
    config = config_link_table

    # setup the link table
    botoclient = boto3.client('dynamodb')
    setup_link_table(botoclient=botoclient, table_name=config.username_person_link_table_name,
                     gsi_name=config.username_person_link_table_person_index_name)

    # checkout to 1@gmail.com
    emails = [
        "1@gmail.com",
        "2@gmail.com",
        "3@gmail.com",
        "4@gmail.com",
    ]
    persons = [
        "1",
        "2",
    ]

    # become person 0
    checkout_email_all_deps(emails[0])

    # do reverse lookup with empty result
    admin_reverse_lookup_assert_equality(
        client=client, person_id=persons[0], usernames=[])

    # do reverse lookup with single result
    # assign 0 -> 0
    admin_assign_link_assert_success(
        client=client,
        username=emails[0],
        person_id=persons[0],
        force=False
    )
    admin_reverse_lookup_assert_equality(
        client=client, person_id=persons[0], usernames=emails[:0])

    # do reverse lookup with multiple results
    # assign 1 -> 0
    admin_assign_link_assert_success(
        client=client,
        username=emails[1],
        person_id=persons[0],
        force=False
    )
    # assign 2 -> 0
    admin_assign_link_assert_success(
        client=client,
        username=emails[2],
        person_id=persons[0],
        force=False
    )
    admin_reverse_lookup_assert_equality(
        client=client, person_id=persons[0], usernames=emails[:2])

    # add other ids and make sure no change
    # assign 3 -> 1
    admin_assign_link_assert_success(
        client=client,
        username=emails[3],
        person_id=persons[1],
        force=False
    )
    # should be the same
    admin_reverse_lookup_assert_equality(
        client=client, person_id=persons[0], usernames=emails[:2])

    # remove relevant ids and make sure shrinks
    # clear 2
    admin_clear_link(client=client, username=emails[2])
    admin_reverse_lookup_assert_equality(
        client=client, person_id=persons[0], usernames=emails[:1])
    # clear 1
    admin_clear_link(client=client, username=emails[1])
    admin_reverse_lookup_assert_equality(
        client=client, person_id=persons[0], usernames=emails[:0])

    # clear completely and make sure empty
    # clear 0
    admin_clear_link(client=client, username=emails[0])
    admin_reverse_lookup_assert_equality(
        client=client, person_id=persons[0], usernames=[])
