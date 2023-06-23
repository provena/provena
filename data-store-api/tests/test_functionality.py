import tests.env_setup
import os
from aws_secretsmanager_caching import SecretCache  # type: ignore
import random as r
from main import app
from config import Config, get_settings
from datetime import datetime
from typing import List, Tuple, Generator
from SharedInterfaces.RegistryAPI import DatasetFetchResponse, AccessInfo, DatasetDomainInfo, RecordType, ItemDataset, OptionallyRequiredCheck
from SharedInterfaces.DataStoreAPI import *
from itertools import product
from tests.config import test_bucket_name, test_registry_name, NUM_FAKE_ENTRIES, test_email
from KeycloakFastAPI.Dependencies import User, ProtectedRole
from dependencies.dependencies import user_general_dependency, read_user_protected_role_dependency, read_write_user_protected_role_dependency, admin_user_protected_role_dependency
from helpers.metadata_helpers import validate_fields
from helpers.aws_helpers import sanitize_handle
from helpers.util import py_to_dict
from pydantic import ValidationError
from fastapi.testclient import TestClient
import json
from moto import mock_s3  # type: ignore
import boto3  # type: ignore
import pytest  # type: ignore

client = TestClient(app)


@pytest.fixture(scope="session", autouse=False)
def test_config() -> Config:
    return Config(
        HANDLE_API_ENDPOINT="",
        # these calls need to be mocked
        REGISTRY_API_ENDPOINT="",
        OIDC_SERVICE_ACCOUNT_SECRET_ARN="",
        OIDC_SERVICE_ROLE_ARN="",
        SERVICE_ACCOUNT_SECRET_ARN="",
        BUCKET_ROLE_ARN="",
        S3_STORAGE_BUCKET_NAME=test_bucket_name,
        KEYCLOAK_ISSUER="",
        SERVER_CACHING_ENABLED=False,
        # disable registry API validation
        REMOTE_PRE_VALIDATION=False
    )


@pytest.fixture(scope="function", autouse=True)
def config_override(test_config: Config) -> Generator:
    # setup settings
    app.dependency_overrides[get_settings] = lambda: test_config
    # run test
    yield
    # clean up
    app.dependency_overrides = {}


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


def get_test_user() -> User:
    return User(username=test_email, roles=['test-role'], access_token="faketoken1234", email=test_email)


async def user_general_dependency_override() -> User:
    # Creates an override for user dependency
    return get_test_user()


async def user_protected_dependency_override() -> ProtectedRole:
    # Creates override for the role protected user dependency
    return ProtectedRole(
        access_roles=['test-role'],
        user=get_test_user()
    )


def test_check_general_access() -> None:
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


def test_check_protected_access() -> None:
    # Checks protected role access once overridden

    # Override the auth dependency
    app.dependency_overrides[read_write_user_protected_role_dependency] = user_protected_dependency_override
    app.dependency_overrides[read_user_protected_role_dependency] = user_protected_dependency_override

    response = client.get("/check-access/check-write-access")
    assert response.status_code == 200
    assert response.json() == {
        "username": test_email,
        "roles": ["test-role"],
        "access_token": "faketoken1234",
        "email": test_email
    }


def test_dataset_schema() -> None:
    # Checks that the dataset schema endpoint provides valid
    # Json and that it matches the file contents exactly

    # Override the auth dependency
    app.dependency_overrides[read_user_protected_role_dependency] = user_protected_dependency_override

    response = client.get("/metadata/dataset-schema")
    assert response.status_code == 200

    # Retrieve the json dat a from json_schema field of response
    json_content = response.json()['json_schema']

    # Check that it is valid
    assert json_content, "JSON object was none"

    # Check that it can be serialized and deserialized
    assert json.loads(json.dumps(json_content)) == json_content

    # Check that the contents of the json file match
    json_file = json.loads(open('resources/schema.json', 'r').read())
    assert json_file == json_content


def test_mint_dataset_invalid_schema() -> None:
    # Override the auth dependency
    app.dependency_overrides[read_write_user_protected_role_dependency] = user_protected_dependency_override
    app.dependency_overrides[read_user_protected_role_dependency] = user_protected_dependency_override

    # update this number as more invalids are added
    invalid_max = 6
    invalid_min = 1
    invalid_schemas = []

    for i in range(invalid_min, invalid_max + 1):
        invalid_schemas.append(
            f'tests/resources/schemas/invalid_ro_raw{i}.json'
        )

    for invalid_path in invalid_schemas:
        # Create payload
        metadata = json.loads(open(invalid_path, 'r').read())
        payload = metadata

        # Fire off to validate metadata endpoint
        response = client.post('/metadata/validate-metadata', json=payload)

        # Check endpoint responds appropriately
        # Since the endpoint will parse it directly at the API level
        # it should respond with 422 (unprocessable entity)
        assert response.status_code == 422, "Invalid schema was not picked up at API level"


def test_validate_invalid_date() -> None:
    # Override the auth dependency
    app.dependency_overrides[read_write_user_protected_role_dependency] = user_protected_dependency_override
    app.dependency_overrides[read_user_protected_role_dependency] = user_protected_dependency_override

    # test update for invalid date (should fail)
    invalid_schema_path = 'tests/resources/schemas/invalid_date_ro_raw1.json'
    payload = json.loads(
        open(invalid_schema_path, 'r').read())
    response = client.post('/metadata/validate-metadata', json=payload)
    assert response.status_code == 200, f"Should have gotten 200. Got {response.status_code}. Details: {response.json()}"
    resp_stat: Status = Status.parse_obj(response.json())
    assert not resp_stat.success, "Should not have validated invalid dates."


@mock_s3
def test_mint_invalid_date() -> None:
    # Override the auth dependency
    app.dependency_overrides[read_write_user_protected_role_dependency] = user_protected_dependency_override
    app.dependency_overrides[read_user_protected_role_dependency] = user_protected_dependency_override

    # test update for invalid date (should fail)
    invalid_schema_path = 'tests/resources/schemas/invalid_date_ro_raw1.json'
    payload = json.loads(
        open(invalid_schema_path, 'r').read())

    # make request
    response = client.post('/register/mint-dataset', json=payload)
    assert response.status_code == 200, f"Should have gotten 200. Got {response.status_code}. Details: {response.json()}"
    response: MintResponse = MintResponse.parse_obj(response.json())
    assert not response.status.success, "Should not have minted dataset with invalid dates"


valid_uris: List[str] = ["file:///file/path", "file:///file", "file://file.txt", "http://google.com",
                         "https://google.com", "ftp://ftp.bom.gov.au/anon/gen/", "ftp://ftp.bom.gov.au/anon/gen/file.txt"]
invalid_uris: List[str] = ["badscheme;test", "file.txt", "google.com"]


def test_uri_validation() -> None:
    for valid_uri in valid_uris:
        try:
            result = AccessInfo.parse_obj({
                "reposited": False,
                "uri": valid_uri,
                "description": "test"
            })
        except ValidationError as e:
            assert False, f"Exception encountered - this URI should have been valid: {valid_uri}. Exception: {e}."
    for invalid_uri in invalid_uris:
        try:
            result = AccessInfo.parse_obj({
                "reposited": False,
                "uri": invalid_uri,
                "description": "test"
            })
            assert False, f"No exception encountered - this URI should have been invalid: {invalid_uri}"
        except ValidationError:
            None


def end_to_end_mint(
    monkeypatch: Any,
    s3_client: Any,
    collection_format: CollectionFormat,
    metadata: Dict[Any, Any],
    payload: Dict[Any, Any],
    other_data: Dict[Any, Any],
    other_data_path: str,
    config: Config,
) -> str:
    """
    Function Description
    --------------------

    Repeatable mint method which uses mocked s3 environment to assert behaviour
    about the mint method without modifying any real resources.
    Additionally tests the '/fetch-dataset' API.

    Arguments
    ----------
    s3_client : boto3.client
        The mocked s3 client
    metadata : dict[Any,Any]
        The request metadata
    payload : dict[Any,Any]
        The request payload
    other_data : dict[Any,Any]
        The data in the existing dataset that
        shouldn't be trampled
    other_data_path : str
        The path of the existing dataset.

    See Also (optional)
    --------

    Examples (optional)
    --------

    """

    # patch required functions to return expected values
    def generate_random_handle() -> str:
        return ''.join([str(r.randint(0, 9)) for _ in range(10)])

    import routes.register.register as register

    # need to patch
    # seed_dataset_in_registry
    def mocked_seed_dataset_in_registry(proxy_username: str, secret_cache: SecretCache, config: Config) -> str:
        return generate_random_handle()

    monkeypatch.setattr(
        register,
        'seed_dataset_in_registry',
        mocked_seed_dataset_in_registry
    )

    # update dataset in registry
    def mocked_update_dataset_in_registry(proxy_username: str, domain_info: DatasetDomainInfo, id: str, secret_cache: SecretCache, config: Config, reason: str) -> None:
        # no action required
        return None

    monkeypatch.setattr(
        register,
        'update_dataset_in_registry',
        mocked_update_dataset_in_registry
    )

    # make request
    response = client.post('/register/mint-dataset', json=payload)

    assert response.status_code == 200

    response_json = response.json()

    mint_response = MintResponse.parse_obj(response_json)
    assert mint_response

    assert mint_response.status.success, "Reported failure when minting"

    # TODO Assert more about handles here once integration is complete or mock is
    # valid
    assert mint_response.handle

    # Check that the file has been uploaded in the right spot

    # Check bucket name
    assert mint_response.s3_location
    assert mint_response.s3_location.bucket_name == test_bucket_name, "Bucket name was not correct"

    # Check file path and URI response
    san_name = sanitize_handle(mint_response.handle)
    desired_uri = f"s3://{test_bucket_name}/{config.DATASET_PATH}/{san_name}/"
    desired_path = f"{config.DATASET_PATH}/{san_name}/"
    desired_key = f"{config.DATASET_PATH}/{san_name}/{config.METADATA_FILE_NAME}"

    assert mint_response.s3_location.s3_uri == desired_uri, "Incorrect URI"
    assert mint_response.s3_location.path == desired_path, "Incorrect path"

    # Check that file was uploaded and that it matches expected contents
    metadata_json = s3_client.get_object(
        Bucket=test_bucket_name, Key=desired_key)
    assert metadata_json.get('Body')

    # Get the contents
    contents = json.loads(metadata_json['Body'].read().decode('UTF-8'))

    # Check that handle and other info was added
    assert contents != metadata, "Uploaded contents were not modified with handle and URI"

    # Add handle and other info to metadata
    updated_metadata = metadata.copy()

    # Perform ro-crate transform
    # To check that upload was successful
    expected_metadata = py_to_dict(collection_format)

    # Check equality
    assert contents == expected_metadata, "Uploaded contents don't match expected value"

    # Ensure that other data was not disturbed
    old_metadata_json = s3_client.get_object(
        Bucket=test_bucket_name, Key=other_data_path)
    assert old_metadata_json.get('Body')
    old_contents = json.loads(old_metadata_json['Body'].read().decode('UTF-8'))

    assert old_contents == other_data, "Uploading of data trampled existing dataset"

    # some mocks required here

    def mocked_user_fetch_dataset_from_registry(id: str, config: Config, user: User) -> DatasetFetchResponse:
        return DatasetFetchResponse(
            status=Status(success=True,
                          details="Fake success."),
            item=ItemDataset(
                id=id,
                owner_username=test_email,
                display_name=collection_format.dataset_info.name,
                collection_format=collection_format,
                s3=mint_response.s3_location,
                created_timestamp=datetime.now().timestamp(),
                updated_timestamp=datetime.now().timestamp(),
                record_type=RecordType.COMPLETE_ITEM,
                history=[]
            ),
            roles=[],
            locked=False,
            item_is_seed=False,
        )

    import routes.registry.items as items
    monkeypatch.setattr(
        items,
        'user_fetch_dataset_from_registry',
        mocked_user_fetch_dataset_from_registry
    )

    fetch_resp = client.get('registry/items/fetch-dataset',
                            params={"handle_id": mint_response.handle})
    assert fetch_resp.status_code == 200
    registryFetchResponse = RegistryFetchResponse.parse_obj(fetch_resp.json())
    fetched_item = registryFetchResponse.item
    assert fetched_item
    assert mint_response.handle == fetched_item.id
    assert collection_format.dataset_info.name == fetched_item.collection_format.dataset_info.name
    assert fetched_item.s3.bucket_name == test_bucket_name
    assert fetched_item.s3.s3_uri == desired_uri

    return mint_response.handle


@mock_s3
def test_mint_dataset_end_to_end(monkeypatch: Any, aws_credentials: Any, test_config: Config) -> None:
    # makes a mint-dataset requests with a mocked S3 environment and
    # ensures the expected behaviour occurs

    # The s3 client below is mocked and is prepared however we want it

    # Override the auth dependency
    app.dependency_overrides[read_write_user_protected_role_dependency] = user_protected_dependency_override
    app.dependency_overrides[read_user_protected_role_dependency] = user_protected_dependency_override

    # Get s3 client
    s3_client = boto3.client('s3')

    # Create the bucket
    s3_client.create_bucket(Bucket=test_bucket_name)

    # Create another dataset in the folder structure
    test_other_dataset_name = "OTHER_DATASET"

    # Silly test data for other dataset
    other_data = {
        'some_data': 'some other data'
    }
    encoded_test_data = json.dumps(other_data).encode('UTF-8')

    # Upload path which seeds structure
    other_data_path = f"{test_config.DATASET_PATH}/{test_other_dataset_name}/{test_config.METADATA_FILE_NAME}"

    # upload file
    s3_client.put_object(
        Body=encoded_test_data,
        Bucket=test_bucket_name,
        Key=other_data_path
    )

    # Run end to end for each schema
    valid_schema_paths = [
        'tests/resources/schemas/valid_ro_raw1.json',
        'tests/resources/schemas/valid_ro_raw2.json'
    ]

    for valid_schema_path in valid_schema_paths:
        metadata = json.loads(open(valid_schema_path, 'r').read())

        payload = metadata

        end_to_end_mint(
            monkeypatch=monkeypatch,
            s3_client=s3_client,
            metadata=metadata,
            collection_format=CollectionFormat.parse_obj(metadata),
            payload=payload,
            other_data=other_data,
            other_data_path=other_data_path,
            config=test_config
        )


def validate_optional_check_behaviour(field: OptionallyRequiredCheck, data: CollectionFormat) -> None:
    # make sure it doesn't change value
    initial_relevant = field.relevant
    initial_obtained = field.obtained

    # Test: consent obtained but not relevant (fail)
    field.relevant = False
    field.obtained = True
    with pytest.raises(Exception):
        validate_fields(data)

    # Test: consent not obtained but relevant (fail)
    field.relevant = True
    field.obtained = False
    with pytest.raises(Exception):
        validate_fields(data)

    # Test: consent obtained and relevant (succeed)
    field.relevant = True
    field.obtained = True
    validate_fields(data)

    # Test: consent not obtained and not relevant (succeed)
    field.relevant = False
    field.obtained = False
    validate_fields(data)

    field.relevant = initial_relevant
    field.obtained = initial_obtained


def test_validate_fields() -> None:
    """Test for validate_fields.
    """

    data = CollectionFormat.parse_obj(json.loads(
        open('tests/resources/schemas/valid_ro_raw1.json', 'r').read()))

    # Test: create date is after publish date
    data.dataset_info.created_date = datetime(2020, 1, 2)
    data.dataset_info.published_date = datetime(2020, 1, 1)
    with pytest.raises(Exception):
        validate_fields(data)

    # Test: create date is before publish date
    data.dataset_info.created_date = datetime(2020, 1, 1)
    data.dataset_info.published_date = datetime(2020, 1, 2)
    validate_fields(data)

    # check validation behaviour for the relevant optionally required check
    # fields
    validate_optional_check_behaviour(
        field=data.approvals.ethics_registration,
        data=data
    )

    validate_optional_check_behaviour(
        field=data.approvals.ethics_access,
        data=data
    )

    validate_optional_check_behaviour(
        field=data.approvals.indigenous_knowledge,
        data=data
    )

    validate_optional_check_behaviour(
        field=data.approvals.export_controls,
        data=data
    )
