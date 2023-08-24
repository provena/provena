import tests.env_setup
import os
from KeycloakFastAPI.Dependencies import User
from SharedInterfaces.AuthAPI import *
from main import app
from dependencies.dependencies import user_general_dependency, sys_admin_write_dependency, sys_admin_read_dependency, sys_admin_admin_dependency
from fastapi.testclient import TestClient
from typing import Callable, Optional, List
import json
from moto import mock_dynamodb  # type: ignore
from tests.config import *
import pytest  # type: ignore
import boto3  # type: ignore
from helpers.access_report_helpers import *
from helpers.request_table_helpers import *
from typing import Generator
from httpx import Response
from config import Config, get_settings, base_config

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


def generate_dependency_with_roles(roles: Optional[List[str]] = ['test-role']) -> Callable[[], Any]:
    """    generate_dependency_with_roles
        Generates the dependants with roles

        Arguments
        ----------
        roles : Optional[List[str]], optional
            The list of roles to generate dependency with. By default is ['test-role']

        Returns
        -------
         : Callable[[], Any]
            Asynchronous callable function for generating user general dependency.

        See Also (optional)
        --------

        Examples (optional)
        --------
    """
    async def user_general_dependency_override() -> User:
        # Creates an override for user dependency
        return User(username=test_email, roles=roles, access_token="faketoken1234", email=test_email)
    return user_general_dependency_override


async def user_general_dependency_override() -> User:
    # Creates an override for user dependency
    return User(username=test_email, roles=['test-role'], access_token="faketoken1234", email=test_email)


def test_check_general_access() -> None:
    # Checks general access once overridden

    # Override the auth dependency
    app.dependency_overrides[user_general_dependency] = user_general_dependency_override

    response = client.get("/check-access/general")
    assert response.status_code == 200
    assert response.json() == {
        "username": "testuser@gmail.com",
        "roles": ["test-role"],
        "access_token": "faketoken1234",
        "email": test_email
    }

    # Clean up dependencies
    app.dependency_overrides = {}


def generate_report_from_roles(role_list: List[str]) -> Response:
    """    generate_report_from_roles
        Get response of generation of access report from roles.

        Arguments
        ----------
        role_list : List[str]
            The roles to generate access report of of.

        Returns
        -------
         : Response
            the response object from .get().

        See Also (optional)
        --------

        Examples (optional)
        --------
    """
    # Override the auth dependency with custom role list
    app.dependency_overrides[user_general_dependency] = generate_dependency_with_roles(
        role_list)

    # Call the generate report endpoint
    response = client.get('access-control/user/generate-access-report')

    # Clean up
    app.dependency_overrides = {}

    return response


def test_generate_access_report_no_access() -> None:

    # Produce response from no roles
    response = generate_report_from_roles(role_list=[])

    # Check response was successful
    assert response.status_code == 200

    # Check that the object is parsable
    report_response = AccessReportResponse.parse_obj(response.json())

    assert report_response

    # Check that the status was successful
    assert report_response.status.success

    report = report_response.report

    for component in AUTHORISATION_MODEL.components:
        for role in component.component_roles:
            # Get the correct role
            comp_found = False
            role_found = False
            details_match = False

            for report_component in report.components:
                if report_component.component_name == component.component_name:
                    comp_found = True
                    for report_role in report_component.component_roles:
                        if report_role.role_name == role.role_name:
                            role_found = True
                            if report_role.role_display_name == role.role_display_name:
                                details_match = True
                            assert not report_role.access_granted

                            # no need to keep searching
                            break
        assert comp_found
        assert role_found
        assert details_match

    # Check all roles are negative
    for comp in report.components:
        for access_role in comp.component_roles:
            assert not access_role.access_granted

    # Check no extra roles
    all_role_name_set = set()
    for comp in AUTHORISATION_MODEL.components:
        for comp_role in comp.component_roles:
            all_role_name_set.add(comp_role.role_name)

    for comp in report.components:
        for report_role in comp.component_roles:
            assert report_role.role_name in all_role_name_set


def test_generate_access_report_read_only() -> None:

    # Produce response from no roles
    read_role = ENTITY_REGISTRY_COMPONENT.get_role_at_level(
        AccessLevel.READ).role_name
    response = generate_report_from_roles(role_list=[read_role])

    # Check response was successful
    assert response.status_code == 200

    # Check that the object is parsable
    report_response = AccessReportResponse.parse_obj(response.json())

    assert report_response

    # Check that the status was successful
    assert report_response.status.success

    report = report_response.report

    # Check that all the components and roles in the role knowledge map are
    # negative EXCEPT data-store-read
    for component in AUTHORISATION_MODEL.components:
        for role in component.component_roles:
            # Get the correct role
            comp_found = False
            role_found = False
            details_match = False

            for report_component in report.components:
                if report_component.component_name == component.component_name:
                    comp_found = True
                    for report_role in report_component.component_roles:
                        if report_role.role_name == role.role_name:
                            role_found = True
                            if report_role.role_display_name == role.role_display_name:
                                details_match = True
                            if report_role.role_name == read_role:
                                assert report_role.access_granted
                            else:
                                assert not report_role.access_granted
                            # no need to keep searching
                            break
        assert comp_found
        assert role_found
        assert details_match


def test_generate_access_report_multi_role() -> None:
    # Produce response from no roles
    read_role = HANDLE_SERVICE_COMPONENT.get_role_at_level(
        AccessLevel.READ).role_name
    write_role = HANDLE_SERVICE_COMPONENT.get_role_at_level(
        AccessLevel.WRITE).role_name
    role_list = [read_role, write_role]
    response = generate_report_from_roles(role_list=role_list)

    # Check response was successful
    assert response.status_code == 200

    # Check that the object is parsable
    report_response = AccessReportResponse.parse_obj(response.json())

    assert report_response

    # Check that the status was successful
    assert report_response.status.success

    report = report_response.report

    # Check that all the components and roles in the role knowledge map are
    # negative EXCEPT data-store-read
    for component in AUTHORISATION_MODEL.components:
        for role in component.component_roles:
            # Get the correct role
            comp_found = False
            role_found = False
            details_match = False

            for report_component in report.components:
                if report_component.component_name == component.component_name:
                    comp_found = True
                    for report_role in report_component.component_roles:
                        if report_role.role_name == role.role_name:
                            role_found = True
                            if report_role.role_display_name == role.role_display_name:
                                details_match = True
                            if report_role.role_name in role_list:
                                assert report_role.access_granted
                            else:
                                assert not report_role.access_granted
                            # no need to keep searching
                            break
        assert comp_found
        assert role_found
        assert details_match


def setup_access_request_table(client: Any, table_name: str) -> None:
    # Setup dynamo db
    client.create_table(
        AttributeDefinitions=[
            {
                'AttributeName': 'username',
                'AttributeType': 'S'
            },
            {
                'AttributeName': 'request_id',
                'AttributeType': 'N'
            }
        ],
        TableName=table_name,
        KeySchema=[
            {
                'AttributeName': 'username',
                'KeyType': 'HASH'
            },
            {
                'AttributeName': 'request_id',
                'KeyType': 'RANGE'
            }
        ],
        BillingMode='PAY_PER_REQUEST'
    )


@mock_dynamodb
def test_request_added_and_updated_correctly(provide_global_config: Config, aws_credentials: Any) -> None:
    # pull out config from fixture
    config: Config = provide_global_config

    # Override general auth
    app.dependency_overrides[user_general_dependency] = user_general_dependency_override

    # Setup table
    db_client = boto3.client('dynamodb')
    setup_access_request_table(db_client, test_access_request_table_name)

    # Get access report
    access_report_response = AccessReportResponse.parse_obj(
        client.get('/access-control/user/generate-access-report').json())

    # Check status
    assert access_report_response.status.success

    # Get the report
    report = access_report_response.report
    original_report = report.copy(deep=True)

    # make an arbitrary change to the report

    # get first component
    components = report.components
    assert len(components) > 0
    first_component = components[0]

    # get first role
    access_roles = first_component.component_roles
    assert len(access_roles) > 0
    first_access_role = access_roles[0]

    # swap access
    first_access_role.access_granted = not first_access_role.access_granted

    # define the correct diff
    diff = AccessReport(
        components=[
            ReportAuthorisationComponent(
                component_name=first_component.component_name,
                component_roles=[first_access_role]
            )
        ]
    )

    # Make a request access change with updated roles
    params = {
        'send_email': False
    }
    response = client.post(
        '/access-control/user/request-change', json=report.dict(), params=params)

    # Unpack response and make sure it is valid
    assert response.status_code == 200
    access_request_response = AccessRequestResponse.parse_obj(response.json())
    assert access_request_response.status.success

    # Now let's check the table and make sure the entry is present
    entries = get_access_request_entries(username=test_email, config=config)

    # check the properties
    assert len(entries) == 1

    # Get the first item and check its properties
    item: RequestAccessTableItem = entries[0]

    assert item.username == test_email
    assert AccessReport.parse_obj(json.loads(
        item.complete_contents)) == original_report
    assert AccessReport.parse_obj(
        json.loads(item.request_diff_contents)) == diff

    current_time = datetime.now()
    buffer = timedelta(seconds=10)
    min_time = current_time - buffer
    max_time = current_time + buffer
    retrieved_time = datetime.fromtimestamp(float(item.created_timestamp))

    assert retrieved_time > min_time
    assert retrieved_time < max_time

    # Let's use the API endpoint to get this user's pending requests and check it
    # is present
    pending_requests = AccessRequestList.parse_obj(client.get(
        '/access-control/user/pending-request-history').json())
    items = pending_requests.items

    # And assert properties about it
    # Get the first item and check its properties
    assert len(items) == 1
    item: RequestAccessTableItem = items[0]

    assert item.username == test_email
    assert AccessReport.parse_obj(json.loads(
        item.complete_contents)) == original_report
    assert AccessReport.parse_obj(
        json.loads(item.request_diff_contents)) == diff

    current_time = datetime.now()
    buffer = timedelta(seconds=10)
    min_time = current_time - buffer
    max_time = current_time + buffer
    retrieved_time = datetime.fromtimestamp(float(item.created_timestamp))

    assert retrieved_time > min_time
    assert retrieved_time < max_time

    # Get full history and ensure it is the same
    full_requests = AccessRequestList.parse_obj(
        client.get('/access-control/user/request-history').json())
    items = full_requests.items

    # And assert properties about it
    # Get the first item and check its properties
    assert len(items) == 1
    item: RequestAccessTableItem = items[0]

    assert item.username == test_email
    assert AccessReport.parse_obj(json.loads(
        item.complete_contents)) == original_report
    assert AccessReport.parse_obj(
        json.loads(item.request_diff_contents)) == diff

    current_time = datetime.now()
    buffer = timedelta(seconds=10)
    min_time = current_time - buffer
    max_time = current_time + buffer
    retrieved_time = datetime.fromtimestamp(float(item.created_timestamp))

    assert retrieved_time > min_time
    assert retrieved_time < max_time

    # Now update the status of the request

    # Add sys admin dependency
    role_name = SYS_ADMIN_COMPONENT.get_role_at_level(
        AccessLevel.WRITE).role_name
    dep_override = generate_dependency_with_roles([role_name])
    app.dependency_overrides[sys_admin_write_dependency] = dep_override

    # make request
    note_test_content = "test note!"
    request = AccessRequestStatusChange(
        username=test_email,
        request_id=item.request_id,
        desired_state=RequestStatus.APPROVED_PENDING_ACTION,
        additional_note=note_test_content,
    )
    status = ChangeStateStatus.parse_obj(client.post(
        '/access-control/admin/change-request-state', json=request.dict()).json())
    assert status.state_change.success

    # now get the pending and check there are no entries
    pending_requests = AccessRequestList.parse_obj(client.get(
        '/access-control/user/pending-request-history').json())
    items = pending_requests.items
    assert len(items) == 0

    # now get the full history and check it has the updated state, timestamp and notes

    # Get full history and ensure it is the same
    full_requests = AccessRequestList.parse_obj(
        client.get('/access-control/user/request-history').json())
    items = full_requests.items
    assert len(items) == 1
    item: RequestAccessTableItem = items[0]

    # Check that time was updated
    current_time = datetime.now()
    buffer = timedelta(seconds=10)
    min_time = current_time - buffer
    max_time = current_time + buffer
    retrieved_time = datetime.fromtimestamp(float(item.updated_timestamp))

    assert retrieved_time > min_time
    assert retrieved_time < max_time

    # Check that note was added
    notes = item.notes
    split_notes = notes.split(',')
    assert len(split_notes) == 1
    assert split_notes[0] == note_test_content

    # Make another state change and check note contents again
    note_test_content_second = "test note 2 woo hoo!?"
    request = AccessRequestStatusChange(
        username=test_email,
        request_id=item.request_id,
        desired_state=RequestStatus.DENIED_PENDING_DELETION,
        additional_note=note_test_content_second
    )
    status = ChangeStateStatus.parse_obj(client.post(
        '/access-control/admin/change-request-state', json=request.dict()).json())
    assert status.state_change.success

    # Get full history and ensure it is the same
    full_requests = AccessRequestList.parse_obj(
        client.get('/access-control/user/request-history').json())
    items = full_requests.items
    assert len(items) == 1
    item: RequestAccessTableItem = items[0]

    # Check that note was added
    notes = item.notes
    split_notes = notes.split(',')
    assert len(split_notes) == 2
    assert split_notes[0] == note_test_content
    assert split_notes[1] == note_test_content_second

    app.dependency_overrides = {}


@mock_dynamodb
def test_admin_controls(aws_credentials: Any) -> None:
    # Don't worry about getting role name correct
    dep_override = generate_dependency_with_roles(["fake-role-name"])

    # We don't enforce role names if overridden so this is fine
    app.dependency_overrides[sys_admin_read_dependency] = dep_override
    app.dependency_overrides[sys_admin_write_dependency] = dep_override
    app.dependency_overrides[sys_admin_admin_dependency] = dep_override
    app.dependency_overrides[user_general_dependency] = user_general_dependency_override

    # Setup table
    db_client = boto3.client('dynamodb')
    setup_access_request_table(db_client, test_access_request_table_name)

    # Get sample access report
    report = AccessReportResponse.parse_obj(client.get(
        '/access-control/user/generate-access-report').json()).report

    # Get the report
    original_report = report.copy(deep=True)

    # make an arbitrary change to the report
    # so we can force changes into the request table

    # get first component
    components = report.components
    assert len(components) > 0
    first_component = components[0]

    # get first role
    access_roles = first_component.component_roles
    assert len(access_roles) > 0
    first_access_role = access_roles[0]

    # swap access
    first_access_role.access_granted = not first_access_role.access_granted

    # Add fake entries
    # each entry will use a unique username
    num_entries = 20
    base_user = "test"
    for i in range(num_entries):
        username = base_user + str(i)

        async def unique_dependency_override() -> User:
            # Creates an override for user dependency
            return User(username=username, roles=['test-role'], access_token="faketoken1234")

        # Set the dep override to make the username unique
        app.dependency_overrides[user_general_dependency] = unique_dependency_override

        # Make a request access change with updated roles
        response = client.post('/access-control/user/request-change',
                               json=report.dict(), params={'send_email': False})
        assert response.status_code == 200

    # Check all requests
    response = client.get('/access-control/admin/all-request-history')
    assert response.status_code == 200
    item_list = AccessRequestList.parse_obj(response.json()).items

    # Check we have all entries
    assert len(item_list) == num_entries

    # Check all pending requests
    response = client.get('/access-control/admin/all-pending-request-history')
    assert response.status_code == 200
    item_list = AccessRequestList.parse_obj(response.json()).items

    # Check we have all entries
    assert len(item_list) == num_entries

    # Change status of first item and make sure it is no longer pending
    first: RequestAccessTableItem = item_list[0]

    # pull out details
    id = first.request_id
    username = first.username

    # Change status
    request = AccessRequestStatusChange(
        username=username,
        request_id=id,
        desired_state=RequestStatus.ACTIONED_PENDING_DELETION,
    )
    status = ChangeStateStatus.parse_obj(client.post(
        '/access-control/admin/change-request-state', json=request.dict()).json())
    assert status.state_change.success

    # Now get all and pending again and ensure list sizes are correct
    # Check all requests
    response = client.get('/access-control/admin/all-request-history')
    assert response.status_code == 200
    item_list = AccessRequestList.parse_obj(response.json()).items

    # Check we have all entries
    assert len(item_list) == num_entries

    # Check all pending requests
    response = client.get('/access-control/admin/all-pending-request-history')
    assert response.status_code == 200
    item_list = AccessRequestList.parse_obj(response.json()).items

    # Check we have all entries
    # Should be one less due to state change
    assert len(item_list) == num_entries - 1

    # Now choose a pending user
    first = item_list[0]
    id = first.request_id
    username = first.username

    # Check the list for this user
    params = {'username': username}
    response = client.get(
        '/access-control/admin/user-request-history', params=params)
    assert response.status_code == 200
    item_list = AccessRequestList.parse_obj(response.json()).items

    # Should be a single item
    assert len(item_list) == 1

    # Should match details before
    assert item_list[0].username == username
    assert item_list[0].request_id == id

    # now get pending
    params = {'username': username}
    response = client.get(
        '/access-control/admin/user-pending-request-history', params=params)
    assert response.status_code == 200
    item_list = AccessRequestList.parse_obj(response.json()).items

    # should have single element
    assert len(item_list) == 1

    # Should match details before
    assert item_list[0].username == username
    assert item_list[0].request_id == id

    # Change status
    request = AccessRequestStatusChange(
        username=username,
        request_id=id,
        desired_state=RequestStatus.DENIED_PENDING_DELETION,
    )
    status = ChangeStateStatus.parse_obj(client.post(
        '/access-control/admin/change-request-state', json=request.dict()).json())
    assert status.state_change.success

    # and add note
    note_contents = "test note contents woo hoo"
    request = RequestAddNote(
        username=username,
        request_id=id,
        note=note_contents
    )
    status = Status.parse_obj(client.post(
        '/access-control/admin/add-note', json=request.dict()).json())
    assert status.success

    # Check the list for this user
    params = {'username': username}
    response = client.get(
        '/access-control/admin/user-request-history', params=params)
    assert response.status_code == 200
    item_list = AccessRequestList.parse_obj(response.json()).items

    # Should be a single item
    assert len(item_list) == 1

    # Should match details before
    assert item_list[0].username == username
    assert item_list[0].request_id == id

    # And should have updated state
    assert item_list[0].status == RequestStatus.DENIED_PENDING_DELETION
    assert item_list[0].ui_friendly_status == REQUEST_STATUS_TO_USER_EXPLANATION[RequestStatus.DENIED_PENDING_DELETION]

    # And new note
    assert item_list[0].notes.split(',')[-1] == note_contents

    # now get pending
    params = {'username': username}
    response = client.get(
        '/access-control/admin/user-pending-request-history', params=params)
    assert response.status_code == 200
    item_list = AccessRequestList.parse_obj(response.json()).items

    # should not have any elements
    assert len(item_list) == 0

    # Now delete this request completely
    # Change status
    request = DeleteAccessRequest(
        username=username,
        request_id=id
    )
    status = Status.parse_obj(client.post(
        '/access-control/admin/delete-request', json=request.dict()).json())
    assert status.success

    # Now check no items in history for that user
    # Check the list for this user
    params = {'username': username}
    response = client.get(
        '/access-control/admin/user-request-history', params=params)
    assert response.status_code == 200
    item_list = AccessRequestList.parse_obj(response.json()).items

    # Should be a single item
    assert len(item_list) == 0

    # And check correct length of total list (-1)
    response = client.get('/access-control/admin/all-request-history')
    assert response.status_code == 200
    item_list = AccessRequestList.parse_obj(response.json())

    # Check we have all entries
    assert len(item_list.items) == num_entries - 1

    app.dependency_overrides = {}
