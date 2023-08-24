import tests.env_setup
import pytest
from fastapi.testclient import TestClient
from moto import mock_dynamodb  # type: ignore
from datetime import datetime
import os
from dataclasses import dataclass
import boto3  # type: ignore
from config import Config, get_settings, base_config
from main import app
from typing import Generator, Any
import service.jobs.admin as admin_service
from SharedInterfaces.AsyncJobModels import *
from KeycloakFastAPI.Dependencies import User, ProtectedRole
from dependencies.dependencies import user_general_dependency, read_user_protected_role_dependency, read_write_user_protected_role_dependency, admin_user_protected_role_dependency
from tests.api_helpers import *

client = TestClient(app)


def global_config_provider() -> Config:
    return Config(
        keycloak_endpoint=base_config.keycloak_endpoint,
        stage=base_config.stage,
        domain_base="google.com",
        test_mode=True,

        # Not used
        email_topic_arn="",

        # these are outfitted when needed
        status_table_name="",
        username_index_name="",
        batch_id_index_name="",
        prov_lodge_topic_arn="",
        global_list_index_name="",
        registry_topic_arn="",
    )


@pytest.fixture(scope="session", autouse=True)
def provide_global_config() -> Config:
    return global_config_provider()


@pytest.fixture(scope="function", autouse=True)
def override_config_dependency(provide_global_config: Config) -> Generator:
    app.dependency_overrides[get_settings] = lambda: provide_global_config
    yield
    app.dependency_overrides = {}


@pytest.fixture(scope='session', autouse=True)
def setup_aws_environment() -> None:
    # mock creds
    os.environ['AWS_DEFAULT_REGION'] = "us-east-1"
    os.environ['AWS_ACCOUNT_ID'] = "1234"
    os.environ['AWS_SECRET_ACCESS_KEY'] = "1234"


@dataclass
class JobTable():
    dynamo_table_name: str
    username_index_name: str
    batch_id_index_name: str
    global_index_name: str


@dataclass
class JobInfra():
    job_table: JobTable


def checkout_user(username: str) -> None:
    """

    Checks out a specified user. 

    This creates a user override and updates overrides.

    Args:
        username (str): The username to checkout
    """
    async def user_general_dependency_override() -> User:
        # Creates an override for user dependency
        return User(username=username, roles=['test-role'], access_token="faketoken1234", email=f"{username}@gmail.com")

    async def user_protected_override() -> ProtectedRole:
        # Creates override for the role protected user dependency
        return ProtectedRole(
            access_roles=['test-role'],
            user=User(
                username=username,
                roles=['test-role'],
                access_token="faketoken1234",
                email=f"{username}@gmail.com"
            )
        )

    # override all the deps
    app.dependency_overrides[user_general_dependency] = user_general_dependency_override
    app.dependency_overrides[read_user_protected_role_dependency] = user_protected_override
    app.dependency_overrides[read_write_user_protected_role_dependency] = user_protected_override
    app.dependency_overrides[admin_user_protected_role_dependency] = user_protected_override


def setup_dynamodb_job_table(client: Any, table_name: str) -> JobTable:
    """

    Sets up the status table according to current infra. 

    Includes indexes. 

    Reports the infra details.

    Args:
        client (Any): The DDB client
        table_name (str): The desired table name

    Returns:
        JobTable: The infra info
    """
    # Setup dynamo db
    username_index = 'username-created_timestamp-index'
    batch_index = 'batch_id-created_timestamp-index'
    global_index = f'{GSI_FIELD_NAME}-created_timestamp-index'
    client.create_table(
        AttributeDefinitions=[
            {
                'AttributeName': 'session_id',
                'AttributeType': 'S'
            },
            {
                'AttributeName': 'batch_id',
                'AttributeType': 'S'
            },
            {
                'AttributeName': 'username',
                'AttributeType': 'S'
            },
            {
                'AttributeName': 'created_timestamp',
                'AttributeType': 'N'
            },
            {
                'AttributeName': GSI_FIELD_NAME,
                'AttributeType': 'S'
            },
        ],
        TableName=table_name,
        KeySchema=[
            {
                'AttributeName': 'session_id',
                'KeyType': 'HASH'
            }
        ],
        BillingMode='PAY_PER_REQUEST',
        GlobalSecondaryIndexes=[
            {
                'IndexName': username_index,
                'KeySchema': [
                    {
                        'AttributeName': 'username',
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
                'IndexName': batch_index,
                'KeySchema': [
                    {
                        'AttributeName': 'batch_id',
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
                'IndexName': global_index,
                'KeySchema': [
                    {
                        'AttributeName': GSI_FIELD_NAME,
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
        ],
    )
    return JobTable(
        dynamo_table_name=table_name,
        username_index_name=username_index,
        batch_id_index_name=batch_index,
        global_index_name=global_index
    )


def setup_job_status_table(id: str) -> JobTable:
    # Wrapper for table setup which includes unique id postfix
    table_name = f"status_table{id}"
    ddb_client = boto3.client('dynamodb')
    return setup_dynamodb_job_table(client=ddb_client, table_name=table_name)


def setup_job_infra(id: str) -> JobInfra:
    # sets up ddb table and sqs queue
    return JobInfra(
        job_table=setup_job_status_table(id)
    )


def checkout_infra(config: Config, infra: JobInfra) -> Config:
    """

    Checks out the current infra by

    1) returning an updated config (non mutated)
    2) updates the config override dep

    Args:
        config (Config): The existing config
        infra (JobInfra): The infra target

    Returns:
        Config: The updated config
    """
    config_dict = config.dict()
    config_dict.update({
        'status_table_name': infra.job_table.dynamo_table_name,
        'username_index_name': infra.job_table.username_index_name,
        'batch_id_index_name': infra.job_table.batch_id_index_name,
        'global_list_index_name': infra.job_table.global_index_name
    })
    new_config = Config(**config_dict)

    def new_config_gen() -> Config:
        return new_config
    app.dependency_overrides[get_settings] = new_config_gen
    return new_config


def setup_checkout_infra(id: str, config: Config) -> Config:
    # Sets up and checkouts infra
    infra = setup_job_infra(id)
    new = checkout_infra(config, infra)
    return new


def timestamp() -> int:
    # Returns current timestamp as int
    return int(datetime.now().timestamp())


def write_status_entry(table: Any, entry: JobStatusTable) -> None:
    """

    Writes an entry to the specified table

    Args:
        table (Any): The ddb table
        entry (JobStatusTable): Model
    """
    payload = py_to_dict(entry)
    kargs = {
        "Item": payload
    }
    table.put_item(**kargs)


def add_job_status_entry(
    username: str,
    status: JobStatus,
    job_type: JobType,
    job_sub_type: JobSubType,
    payload: Payload,
    info: Optional[str],
    result: Optional[Payload],
    batch_id: Optional[str],
    config: Config
) -> JobStatusTable:
    # Writes to the job status table with specified values

    # get unique session id (reads from table)
    session_id = admin_service.generate_unique_session_id(
        table_name=config.status_table_name)
    # post new entry
    table_entry = JobStatusTable(
        session_id=session_id,
        created_timestamp=timestamp(),
        username=username,
        batch_id=batch_id,
        payload=payload,
        job_type=job_type,
        job_sub_type=job_sub_type,
        status=status,
        info=info,
        result=result
    )

    # client
    table = boto3.resource('dynamodb').Table(config.status_table_name)

    # write the entry
    write_status_entry(table=table, entry=table_entry)

    # returns the session id
    return table_entry


def add_blank_entry(username: str, config: Config, gen_batch: bool = False, batch_id: Optional[str] = None) -> JobStatusTable:
    """

    Uses the above writer method with sensible defaults

    Args:
        username (str): The username to target
        config (Config): Infra config etc
        gen_batch (bool, optional): Should this entry give a batch id?. Defaults to False.
        batch_id (Optional[str], optional): Existing batch id. Defaults to None.

    Returns:
        JobStatusTable: The entry written
    """
    generated_batch_id:  Optional[str] = None
    if gen_batch:
        generated_batch_id = admin_service.generate_unique_batch_id(
            table_name=config.status_table_name, batch_id_index_name=config.batch_id_index_name)

    return add_job_status_entry(
        username=username,
        status=JobStatus.PENDING,
        job_type=JobType.PROV_LODGE,
        job_sub_type=JobSubType.LODGE_VERSION_ACTIVITY,
        payload=py_to_dict(ProvLodgeVersionPayload(from_version_id="1234", to_version_id="1234",
                           version_activity_id="1234", linked_person_id="1234", item_subtype=ItemSubType.MODEL)),
        info=None,
        result=None,
        batch_id=batch_id if batch_id is not None else generated_batch_id,
        config=config
    )


def test_health_check() -> None:
    # Checks that the health check endpoint responds
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Health check successful."}

# ==========
# USER TESTS
# ==========


@mock_dynamodb
def test_user_fetch(provide_global_config: Config) -> None:
    config = provide_global_config

    # setup and checkout infra default table name
    id = "default"
    config = setup_checkout_infra(id=id, config=config)

    # user 1
    username1 = "user1"
    checkout_user(username1)

    # try fetching with an incorrect ID
    user_fetch_session_id_assert_missing(client=client, session_id="fake")

    # now add a basic entry
    entry = add_blank_entry(username=username1, config=config)

    # try fetching with an incorrect id with entry in table
    user_fetch_session_id_assert_missing(client=client, session_id="fake")

    # try getting the right ID
    entry_response = user_fetch_session_id_assert_correct(
        client=client, session_id=entry.session_id)
    assert entry.session_id == entry_response.session_id, f"Mismatched session ids {entry.session_id} and {entry_response.session_id}."

    # now add another entry
    entry2 = add_blank_entry(username=username1, config=config)

    # try getting entry 1 again
    entry_response = user_fetch_session_id_assert_correct(
        client=client, session_id=entry.session_id)
    assert entry.session_id == entry_response.session_id, f"Mismatched session ids {entry.session_id} and {entry_response.session_id}."

    # try getting entry 2
    entry_response = user_fetch_session_id_assert_correct(
        client=client, session_id=entry2.session_id)
    assert entry2.session_id == entry_response.session_id, f"Mismatched session ids {entry2.session_id} and {entry_response.session_id}."

    # make sure a diff user can't get it
    username2 = "user2"
    checkout_user(username=username2)

    response = user_fetch_session_id(
        client=client, session_id=entry2.session_id)
    assert response.status_code == 401, f"Expected auth error, got {response.status_code}. Text {response.text}."


@mock_dynamodb
def test_user_list(provide_global_config: Config) -> None:
    config = provide_global_config

    # setup and checkout infra default table name
    id = "default"
    config = setup_checkout_infra(id=id, config=config)

    # user 1
    username1 = "user1"
    checkout_user(username1)

    # list - we should have no entries
    entries = user_list_all(client=client)

    assert len(
        entries) == 0, f"Expected no entries, had {len(entries)} entries. Entries: {entries}."

    num = 10
    for _ in range(num):
        add_blank_entry(username=username1, config=config)

    # list - we should have 10 entries
    entries = user_list_all(client=client)

    assert len(
        entries) == num, f"Expected {num} entries, had {len(entries)} entries. Entries: {entries}."

    # now check pagination only returns the desired limit
    desired = 2
    entries = user_list_parsed(client=client, pag_key=None, limit=desired)
    assert len(
        entries) == desired, f"Expected {desired} entries, had {len(entries)} entries. Entries: {entries}."

    # checkout to new user and ensure empty list
    username2 = "user2"
    checkout_user(username=username2)

    # list - we should have no entries
    entries = user_list_all(client=client)

    assert len(
        entries) == 0, f"Expected no entries, had {len(entries)} entries. Entries: {entries}."

    # now add some for user 2
    num = 10
    for _ in range(num):
        add_blank_entry(username=username2, config=config)

    # list - we should have 10 entries
    entries = user_list_all(client=client)

    assert len(
        entries) == num, f"Expected {num} entries, had {len(entries)} entries. Entries: {entries}."


@mock_dynamodb
def test_user_list_batch(provide_global_config: Config) -> None:
    config = provide_global_config

    # setup and checkout infra default table name
    id = "default"
    config = setup_checkout_infra(id=id, config=config)

    # user 1
    username1 = "user1"
    checkout_user(username1)

    # list - we should have no entries
    entries = user_list_all(client=client)

    assert len(
        entries) == 0, f"Expected no entries, had {len(entries)} entries. Entries: {entries}."

    # now, create some entries without any batch

    no_batch_count = 5
    for _ in range(no_batch_count):
        add_blank_entry(username=username1, config=config)

    no_batch_list = user_list_all(client=client)
    assert len(
        no_batch_list) == no_batch_count, f"Expected {no_batch_count} entries, had {len(entries)} entries. Entries: {entries}."

    # now create batch 1
    batch_one_count = 5
    batch_one_id = add_blank_entry(
        username=username1,
        config=config,
        gen_batch=True
    ).batch_id
    assert batch_one_id is not None, f"Expected instantiated batch id when requested."

    for _ in range(1, batch_one_count):
        add_blank_entry(username=username1, config=config,
                        batch_id=batch_one_id)

    # list batch 1 records
    batch_one_list = user_list_batch_all(batch_id=batch_one_id, client=client)
    assert len(
        batch_one_list) == batch_one_count, f"Expected {batch_one_count} entries, had {len(entries)} entries. Entries: {entries}."

    # now create batch 2
    batch_two_count = 7
    batch_two_id = add_blank_entry(
        username=username1,
        config=config,
        gen_batch=True
    ).batch_id
    assert batch_two_id is not None, f"Expected instantiated batch id when requested."

    for _ in range(1, batch_two_count):
        add_blank_entry(username=username1, config=config,
                        batch_id=batch_two_id)

    # list batch 2 records
    batch_two_list = user_list_batch_all(batch_id=batch_two_id, client=client)
    assert len(
        batch_two_list) == batch_two_count, f"Expected {batch_two_count} entries, had {len(entries)} entries. Entries: {entries}."

    # now list batch one again
    batch_one_list = user_list_batch_all(batch_id=batch_one_id, client=client)
    assert len(
        batch_one_list) == batch_one_count, f"Expected {batch_one_count} entries, had {len(entries)} entries. Entries: {entries}."

    # and finally, list all
    all_batch_list = user_list_all(client=client)
    target = no_batch_count + batch_one_count + batch_two_count
    assert len(
        all_batch_list) == target, f"Expected {target} entries, had {len(entries)} entries. Entries: {entries}."

    # checkout to new user and ensure empty list
    username2 = "user2"
    checkout_user(username=username2)

    # list - we should have no entries
    entries = user_list_all(client=client)

    # check 401 when trying to get someone else's batch
    response = user_list_batch(
        batch_id=batch_one_id, client=client, pag_key=None, limit=5)
    assert response.status_code == 401, f"Expected auth error, got {response.status_code}. Text {response.text}."

# ===========
# ADMIN TESTS
# ===========


@mock_dynamodb
def test_admin_fetch(provide_global_config: Config) -> None:
    config = provide_global_config

    # setup and checkout infra default table name
    id = "default"
    config = setup_checkout_infra(id=id, config=config)

    # user 1
    username1 = "user1"
    checkout_user(username1)

    # try fetching with an incorrect ID
    admin_fetch_session_id_assert_missing(client=client, session_id="fake")

    # now add a basic entry
    entry = add_blank_entry(username=username1, config=config)

    # try fetching with an incorrect id with entry in table
    admin_fetch_session_id_assert_missing(client=client, session_id="fake")

    # try getting the right ID
    entry_response = admin_fetch_session_id_assert_correct(
        client=client, session_id=entry.session_id)
    assert entry.session_id == entry_response.session_id, f"Mismatched session ids {entry.session_id} and {entry_response.session_id}."

    # now add another entry
    entry2 = add_blank_entry(username=username1, config=config)

    # try getting entry 1 again
    entry_response = admin_fetch_session_id_assert_correct(
        client=client, session_id=entry.session_id)
    assert entry.session_id == entry_response.session_id, f"Mismatched session ids {entry.session_id} and {entry_response.session_id}."

    # try getting entry 2
    entry_response = admin_fetch_session_id_assert_correct(
        client=client, session_id=entry2.session_id)
    assert entry2.session_id == entry_response.session_id, f"Mismatched session ids {entry2.session_id} and {entry_response.session_id}."

    # make sure admin users can get it regardless of username
    username2 = "user2"
    checkout_user(username=username2)

    admin_fetch_session_id_assert_correct(
        client=client, session_id=entry2.session_id)


@mock_dynamodb
def test_admin_list(provide_global_config: Config) -> None:
    config = provide_global_config

    # setup and checkout infra default table name
    id = "default"
    config = setup_checkout_infra(id=id, config=config)

    # user 1
    username1 = "user1"
    checkout_user(username1)

    # list - we should have no entries
    entries = admin_list_all(client=client)

    assert len(
        entries) == 0, f"Expected no entries, had {len(entries)} entries. Entries: {entries}."

    num = 10
    for _ in range(num):
        add_blank_entry(username=username1, config=config)

    # list - we should have 10 entries
    entries = admin_list_all(client=client)

    assert len(
        entries) == num, f"Expected {num} entries, had {len(entries)} entries. Entries: {entries}."

    # now check pagination only returns the desired limit
    desired = 2
    entries = admin_list_parsed(client=client, pag_key=None, limit=desired)
    assert len(
        entries) == desired, f"Expected {desired} entries, had {len(entries)} entries. Entries: {entries}."

    # checkout to new user
    username2 = "user2"
    checkout_user(username=username2)

    # if no filter supplied, should have all entries
    entries = admin_list_all(client=client)

    assert len(
        entries) == num, f"Expected {num} entries, had {len(entries)} entries. Entries: {entries}."

    # list - with filter should have none
    entries = admin_list_all(client=client, username_filter=username2)

    assert len(
        entries) == 0, f"Expected no entries, had {len(entries)} entries. Entries: {entries}."

    # now add some for user 2
    num = 10
    for _ in range(num):
        add_blank_entry(username=username2, config=config)

    # list - we should have 10 entries
    entries = admin_list_all(client=client, username_filter=username2)

    assert len(
        entries) == num, f"Expected {num} entries, had {len(entries)} entries. Entries: {entries}."


@mock_dynamodb
def test_admin_list_batch(provide_global_config: Config) -> None:
    config = provide_global_config

    # setup and checkout infra default table name
    id = "default"
    config = setup_checkout_infra(id=id, config=config)

    # user 1
    username1 = "user1"
    checkout_user(username1)

    # list - we should have no entries
    entries = admin_list_all(client=client)

    assert len(
        entries) == 0, f"Expected no entries, had {len(entries)} entries. Entries: {entries}."

    # now, create some entries without any batch

    no_batch_count = 5
    for _ in range(no_batch_count):
        add_blank_entry(username=username1, config=config)

    no_batch_list = admin_list_all(client=client)
    assert len(
        no_batch_list) == no_batch_count, f"Expected {no_batch_count} entries, had {len(entries)} entries. Entries: {entries}."

    # now create batch 1
    batch_one_count = 5
    batch_one_id = add_blank_entry(
        username=username1,
        config=config,
        gen_batch=True
    ).batch_id
    assert batch_one_id is not None, f"Expected instantiated batch id when requested."

    for _ in range(1, batch_one_count):
        add_blank_entry(username=username1, config=config,
                        batch_id=batch_one_id)

    # list batch 1 records
    batch_one_list = admin_list_batch_all(batch_id=batch_one_id, client=client)
    assert len(
        batch_one_list) == batch_one_count, f"Expected {batch_one_count} entries, had {len(entries)} entries. Entries: {entries}."

    # now create batch 2
    batch_two_count = 7
    batch_two_id = add_blank_entry(
        username=username1,
        config=config,
        gen_batch=True
    ).batch_id
    assert batch_two_id is not None, f"Expected instantiated batch id when requested."

    for _ in range(1, batch_two_count):
        add_blank_entry(username=username1, config=config,
                        batch_id=batch_two_id)

    # list batch 2 records
    batch_two_list = admin_list_batch_all(batch_id=batch_two_id, client=client)
    assert len(
        batch_two_list) == batch_two_count, f"Expected {batch_two_count} entries, had {len(entries)} entries. Entries: {entries}."

    # now list batch one again
    batch_one_list = admin_list_batch_all(batch_id=batch_one_id, client=client)
    assert len(
        batch_one_list) == batch_one_count, f"Expected {batch_one_count} entries, had {len(entries)} entries. Entries: {entries}."

    # and finally, list all
    all_batch_list = admin_list_all(client=client)
    target = no_batch_count + batch_one_count + batch_two_count
    assert len(
        all_batch_list) == target, f"Expected {target} entries, had {len(entries)} entries. Entries: {entries}."

    # checkout to new user and ensure empty list
    username2 = "user2"
    checkout_user(username=username2)

    # list - we should have no entries
    entries = admin_list_all(client=client, username_filter=username2)
    assert len(
        entries) == 0, f"Expected no entries, had {len(entries)} entries. Entries: {entries}."

    # should be fine for admin to list someone else's batch
    batch_one_list = admin_list_batch_all(batch_id=batch_one_id, client=client)
    assert len(
        batch_one_list) == batch_one_count, f"Expected {batch_one_count} entries, had {len(entries)} entries. Entries: {entries}."
