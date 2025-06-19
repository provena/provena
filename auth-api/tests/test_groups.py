import tests.env_setup
import os
from dataclasses import dataclass
from KeycloakFastAPI.Dependencies import User
from ProvenaInterfaces.AuthAPI import *
from ProvenaInterfaces.DataStoreAPI import *
from main import app
from dependencies.dependencies import sys_admin_write_dependency, sys_admin_read_dependency, sys_admin_admin_dependency, user_general_dependency
from fastapi.testclient import TestClient
from typing import Callable, Optional, List, Any, Generator
import json
from moto import mock_dynamodb  # type: ignore
from tests.config import *
import pytest  # type: ignore
import boto3  # type: ignore
import random
from tests.helpers import *

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


def generate_user_general_dependency_override(email: Optional[str]) -> Callable[[], Any]:
    if email is not None:
        email_used = email
    else:
        email_used = test_email

    async def dep_override() -> User:
        # Creates an override for user dependency
        return User(username=email_used, roles=['test-role'], access_token="faketoken1234", email=email_used)

    return dep_override


@mock_dynamodb
def test_list_groups(provide_global_config: Config, aws_credentials: Any) -> None:
    # config
    config: Config = provide_global_config

    # override admin dependencies
    # TODO only use appropriate
    app.dependency_overrides[sys_admin_read_dependency] = user_general_dependency_override
    app.dependency_overrides[sys_admin_write_dependency] = user_general_dependency_override
    app.dependency_overrides[user_general_dependency] = user_general_dependency_override

    # Setup table
    db_client = boto3.client('dynamodb')
    setup_user_group_table(
        client=db_client,
        table_name=config.user_groups_table_name
    )

    # Setup n groups
    group_count = 5
    desired_groups = setup_n_empty_groups(client, group_count)

    # admin endpoint
    # list the groups and check success
    list_response: ListGroupsResponse = parse_status_response(
        response=client.get(group_admin_endpoints.LIST_GROUPS),
        model=ListGroupsResponse
    )

    assert list_response.groups
    assert len(list_response.groups) == group_count

    # Check all groups present
    for desired_group in desired_groups:
        found = False
        for group in list_response.groups:
            if group.id == desired_group.id:
                found = True
                break
        assert found, f"Group ID {desired_group.id} not found!"

    # user endpoint
    # list the groups and check success
    list_response: ListGroupsResponse = parse_status_response(
        response=client.get(group_user_endpoints.LIST_GROUPS),
        model=ListGroupsResponse
    )

    assert list_response.groups
    assert len(list_response.groups) == group_count

    # Check all groups present
    for desired_group in desired_groups:
        found = False
        for group in list_response.groups:
            if group.id == desired_group.id:
                found = True
                break
        assert found, f"Group ID {desired_group.id} not found!"


@mock_dynamodb
def test_describe_group(provide_global_config: Config, aws_credentials: Any) -> None:
    # config
    config: Config = provide_global_config

    # override admin dependencies
    # TODO only use appropriate
    app.dependency_overrides[sys_admin_read_dependency] = user_general_dependency_override
    app.dependency_overrides[sys_admin_write_dependency] = user_general_dependency_override
    app.dependency_overrides[user_general_dependency] = user_general_dependency_override

    # Setup table
    db_client = boto3.client('dynamodb')
    setup_user_group_table(
        client=db_client,
        table_name=config.user_groups_table_name
    )

    # Setup n groups
    group_count = 5
    created_groups = setup_n_empty_groups(client, group_count)

    # choose one
    chosen_group = random.choice(created_groups)
    id = chosen_group.id
    params = {
        'id': id
    }

    # admin endpoint
    describe_response: DescribeGroupResponse = parse_status_response(
        response=client.get(
            group_admin_endpoints.DESCRIBE_GROUP,
            params=params
        ),
        model=DescribeGroupResponse
    )

    # check it was fetched accurately
    assert smart_model_compare(chosen_group, describe_response.group)

    # user endpoint
    describe_response: DescribeGroupResponse = parse_status_response(
        response=client.get(
            group_user_endpoints.DESCRIBE_GROUP,
            params=params
        ),
        model=DescribeGroupResponse
    )

    # check it was fetched accurately
    assert smart_model_compare(chosen_group, describe_response.group)

    # add a user to the group and check metadata is still correct
    fake_user = generate_fake_user()
    payload = json.loads(fake_user.json())
    _ = parse_status_response(
        response=client.post(
            group_admin_endpoints.ADD_MEMBER,
            params={
                'group_id': chosen_group.id
            },
            json=payload
        ),
        model=AddMemberResponse
    )

    # admin endpoint
    describe_response: DescribeGroupResponse = parse_status_response(
        response=client.get(
            group_admin_endpoints.DESCRIBE_GROUP,
            params=params
        ),
        model=DescribeGroupResponse
    )

    # check it was fetched accurately
    assert smart_model_compare(chosen_group, describe_response.group)

    # user endpoint
    describe_response: DescribeGroupResponse = parse_status_response(
        response=client.get(
            group_user_endpoints.DESCRIBE_GROUP,
            params=params
        ),
        model=DescribeGroupResponse
    )

    # check it was fetched accurately
    assert smart_model_compare(chosen_group, describe_response.group)


@mock_dynamodb
def test_list_members(provide_global_config: Config, aws_credentials: Any) -> None:
    # config
    config: Config = provide_global_config

    # override admin dependencies
    # TODO only use appropriate
    app.dependency_overrides[sys_admin_read_dependency] = user_general_dependency_override
    app.dependency_overrides[sys_admin_write_dependency] = user_general_dependency_override

    # setup table
    db_client = boto3.client('dynamodb')
    setup_user_group_table(
        client=db_client,
        table_name=config.user_groups_table_name
    )

    # setup 5 groups with 10 members
    groups = setup_n_populated_groups(
        client,
        group_count=5,
        user_count=10
    )

    # choose a group
    group = random.choice(groups)

    # list the members
    members_response: ListMembersResponse = parse_status_response(
        response=client.get(
            group_admin_endpoints.LIST_MEMBERS,
            params={
                'id': group.id
            }
        ),
        model=ListMembersResponse
    )

    desired_group_username_set = set([u.username for u in group.users])
    assert members_response.group
    actual_group_username_set = set(
        [u.username for u in members_response.group.users])
    assert desired_group_username_set == actual_group_username_set

    # check the user list members

    # get a user who is not a member
    group_a, group_b = tuple(random.sample(groups, 2))
    group_a_member = random.choice(group_a.users)

    # override dependency to specify user for a
    app.dependency_overrides[user_general_dependency] = generate_user_general_dependency_override(
        email=group_a_member.email)

    # try and list members of group b
    response = client.get(
        group_user_endpoints.LIST_MEMBERS,
        params={
            'id': group_b.id
        }
    )

    # should be a 200 status code with success false due to not being welcome
    assert response.status_code == 200, f"Status code should be 200 but was {response.status_code}"
    parsed_response = ListMembersResponse.parse_obj(response.json())
    assert not parsed_response.status.success
    assert parsed_response.group is None

    # now try for group a of which we are a member
    members_response: ListMembersResponse = parse_status_response(
        response=client.get(
            group_admin_endpoints.LIST_MEMBERS,
            params={
                'id': group_a.id
            }
        ),
        model=ListMembersResponse
    )

    desired_group_username_set = set([u.username for u in group_a.users])
    assert members_response.group
    actual_group_username_set = set(
        [u.username for u in members_response.group.users])
    assert desired_group_username_set == actual_group_username_set


@mock_dynamodb
def test_list_user_membership(provide_global_config: Config, aws_credentials: Any) -> None:
    # config
    config: Config = provide_global_config

    # override admin dependencies
    app.dependency_overrides[sys_admin_read_dependency] = user_general_dependency_override
    app.dependency_overrides[sys_admin_write_dependency] = user_general_dependency_override

    # setup table
    db_client = boto3.client('dynamodb')
    setup_user_group_table(
        client=db_client,
        table_name=config.user_groups_table_name
    )

    # setup 5 groups with 10 members
    group_count = 6
    user_count = 5
    groups = setup_n_populated_groups(
        client,
        group_count=group_count,
        user_count=user_count
    )

    # choose a random user from a random group
    selected_group = random.choice(groups)
    assert selected_group.users
    selected_user = random.choice(selected_group.users)

    # check that currently the user is only in the one group
    membership_response: ListUserMembershipResponse = parse_status_response(
        response=client.get(
            group_admin_endpoints.LIST_USER_MEMBERSHIP,
            params={
                'username': selected_user.username
            }
        ),
        model=ListUserMembershipResponse
    )

    assert membership_response.groups
    assert len(membership_response.groups) == 1
    assert membership_response.groups[0].id == selected_group.id

    # check with user endpoint - override dependency to specify user
    app.dependency_overrides[user_general_dependency] = generate_user_general_dependency_override(
        email=selected_user.email)

    membership_response: ListUserMembershipResponse = parse_status_response(
        response=client.get(
            group_user_endpoints.LIST_USER_MEMBERSHIP,
        ),
        model=ListUserMembershipResponse
    )

    assert membership_response.groups
    assert len(membership_response.groups) == 1
    assert membership_response.groups[0].id == selected_group.id

    # now add the user to some of the other groups and check everything works
    other_groups = random.sample(groups, int(group_count / 2))
    for group in other_groups:
        if group.id == selected_group.id:
            # already in this group
            continue
        else:
            payload = json.loads(selected_user.json())
            _ = parse_status_response(
                response=client.post(
                    group_admin_endpoints.ADD_MEMBER,
                    params={
                        'group_id': group.id
                    },
                    json=payload
                ),
                model=AddMemberResponse
            )

    # now check that the membership has been updated
    membership_response: ListUserMembershipResponse = parse_status_response(
        response=client.get(
            group_admin_endpoints.LIST_USER_MEMBERSHIP,
            params={
                'username': selected_user.username
            }
        ),
        model=ListUserMembershipResponse
    )

    # Make sure all groups are present
    assert membership_response.groups
    for group in other_groups + [selected_group]:
        id = group.id
        found = False
        for returned_group in membership_response.groups:
            if returned_group.id == id:
                found = True
                break
        assert found

    # and that there are no extras += 1 for the possible overlap
    assert len(membership_response.groups) <= len(other_groups) + 1

    # for user endpoint as well
    membership_response: ListUserMembershipResponse = parse_status_response(
        response=client.get(
            group_user_endpoints.LIST_USER_MEMBERSHIP,
        ),
        model=ListUserMembershipResponse
    )

    # Make sure all groups are present
    assert membership_response.groups
    for group in other_groups + [selected_group]:
        id = group.id
        found = False
        for returned_group in membership_response.groups:
            if returned_group.id == id:
                found = True
                break
        assert found

    # and that there are no extras += 1 for the possible overlap
    assert len(membership_response.groups) <= len(other_groups) + 1


@mock_dynamodb
def test_remove_members(provide_global_config: Config, aws_credentials: Any) -> None:
    # config
    config: Config = provide_global_config

    # override admin dependencies
    app.dependency_overrides[sys_admin_read_dependency] = user_general_dependency_override
    app.dependency_overrides[sys_admin_write_dependency] = user_general_dependency_override

    # setup table
    db_client = boto3.client('dynamodb')
    setup_user_group_table(
        client=db_client,
        table_name=config.user_groups_table_name
    )

    # setup groups
    group_count = 2
    user_count = 10
    groups = setup_n_populated_groups(
        client,
        group_count=group_count,
        user_count=user_count
    )

    # select half of the first group and remove in bulk
    selected_group = random.choice(groups)
    selected_users = random.sample(selected_group.users, int(user_count / 2))

    # remove these users
    payload = json.loads(RemoveMembersRequest(
        member_usernames=list(map(lambda user: user.username, selected_users)),
        group_id=selected_group.id
    ).json())

    _ = parse_status_response(
        response=client.request(
            method="POST",
            url=group_admin_endpoints.REMOVE_MEMBERS,
            json=payload),
        model=RemoveMemberResponse
    )

    # now list the members and check its only got the non removed
    members_response: ListMembersResponse = parse_status_response(
        response=client.get(
            group_admin_endpoints.LIST_MEMBERS,
            params={
                'id': selected_group.id
            }
        ),
        model=ListMembersResponse
    )

    returned_group = members_response.group
    assert returned_group and returned_group.users
    returned_users = returned_group.users

    # check the returned username list is correct
    returned_usernames = set([u.username for u in returned_users])
    desired_usernames = set([u.username for u in selected_group.users]
                         ) - set([u.username for u in selected_users])
    assert returned_usernames == desired_usernames


@mock_dynamodb
def test_add_remove_and_check_membership(provide_global_config: Config, aws_credentials: Any) -> None:
    # config
    config: Config = provide_global_config

    # override admin dependencies
    # TODO only use appropriate
    app.dependency_overrides[sys_admin_read_dependency] = user_general_dependency_override
    app.dependency_overrides[sys_admin_write_dependency] = user_general_dependency_override

    # setup table
    db_client = boto3.client('dynamodb')
    setup_user_group_table(
        client=db_client,
        table_name=config.user_groups_table_name
    )

    # setup groups
    group_count = 20
    groups = setup_n_empty_groups(
        client,
        count=group_count,
    )

    # create a fake user
    user = generate_fake_user()

    # select half the groups and make id sets
    member_groups = random.sample(groups, int(group_count / 2))
    selected_ids = set([g.id for g in member_groups])

    # add user to the selected groups
    for id in selected_ids:
        payload = json.loads(user.json())
        _ = parse_status_response(
            response=client.post(
                group_admin_endpoints.ADD_MEMBER,
                params={
                    'group_id': id
                },
                json=payload
            ),
            model=AddMemberResponse
        )

    # check membership and make sure id set matches
    membership_response: ListUserMembershipResponse = parse_status_response(
        response=client.get(
            group_admin_endpoints.LIST_USER_MEMBERSHIP,
            params={
                'username': user.username
            }
        ),
        model=ListUserMembershipResponse
    )

    user_groups = membership_response.groups
    assert user_groups
    found_id_set = set([g.id for g in user_groups])
    assert found_id_set == selected_ids

    # and same for user endpoint
    app.dependency_overrides[user_general_dependency] = generate_user_general_dependency_override(
        email=user.email)

    membership_response: ListUserMembershipResponse = parse_status_response(
        response=client.get(
            group_user_endpoints.LIST_USER_MEMBERSHIP,
        ),
        model=ListUserMembershipResponse
    )

    user_groups = membership_response.groups
    assert user_groups
    found_id_set = set([g.id for g in user_groups])
    assert found_id_set == selected_ids

    # now iterate through each group and make sure the check membership responds
    # correctly
    for group in groups:
        check_membership_response: CheckMembershipResponse = parse_status_response(
            response=client.get(
                group_admin_endpoints.CHECK_MEMBERSHIP,
                params={
                    'username': user.username,
                    'group_id': group.id
                }
            ),
            model=CheckMembershipResponse
        )
        assert check_membership_response.is_member is not None
        assert check_membership_response.is_member == (
            group.id in selected_ids)

        # and same for user endpoint
        check_membership_response: CheckMembershipResponse = parse_status_response(
            response=client.get(
                group_user_endpoints.CHECK_MEMBERSHIP,
                params={
                    'group_id': group.id
                }
            ),
            model=CheckMembershipResponse
        )
        assert check_membership_response.is_member is not None
        assert check_membership_response.is_member == (
            group.id in selected_ids)

    # now remove the user from some of the group, add a second user to make sure
    # we don't smash it away
    selected_removed_groups = random.sample(
        member_groups, int(len(member_groups) / 2))
    selected_removed_ids = set([g.id for g in selected_removed_groups])
    second_user = generate_fake_user()

    for remove_group_id in selected_removed_ids:
        # add the second user
        payload = json.loads(second_user.json())
        _ = parse_status_response(
            response=client.post(
                group_admin_endpoints.ADD_MEMBER,
                params={
                    'group_id': remove_group_id
                },
                json=payload
            ),
            model=AddMemberResponse
        )
        # remove the first user
        _ = parse_status_response(
            response=client.delete(
                group_admin_endpoints.REMOVE_MEMBER,
                params={
                    'group_id': remove_group_id,
                    'username': user.username
                },
            ),
            model=RemoveMemberResponse
        )

    # now go through all groups and make sure status is correct
    desired_membership = selected_ids - selected_removed_ids
    for group in groups:
        check_membership_response = parse_status_response(
            response=client.get(
                group_admin_endpoints.CHECK_MEMBERSHIP,
                params={
                    'username': user.username,
                    'group_id': group.id
                }
            ),
            model=CheckMembershipResponse
        )
        assert check_membership_response.is_member is not None
        assert check_membership_response.is_member == (
            group.id in desired_membership)
        # user endpoint as well
        check_membership_response = parse_status_response(
            response=client.get(
                group_user_endpoints.CHECK_MEMBERSHIP,
                params={
                    'group_id': group.id
                }
            ),
            model=CheckMembershipResponse
        )
        assert check_membership_response.is_member is not None
        assert check_membership_response.is_member == (
            group.id in desired_membership)

    # and check that those conflicting users remain
    for check_group_id in selected_removed_ids:
        members_response: ListMembersResponse = parse_status_response(
            response=client.get(
                group_admin_endpoints.LIST_MEMBERS,
                params={
                    'id': check_group_id
                }
            ),
            model=ListMembersResponse
        )
        populated_group = members_response.group
        assert populated_group is not None
        assert populated_group.users is not None
        assert len(populated_group.users) == 1
        assert smart_model_compare(populated_group.users[0], second_user)


@mock_dynamodb
def test_remove_group(provide_global_config: Config, aws_credentials: Any) -> None:
    # config
    config: Config = provide_global_config

    # override admin dependencies
    # TODO only use appropriate
    app.dependency_overrides[sys_admin_read_dependency] = user_general_dependency_override
    app.dependency_overrides[sys_admin_write_dependency] = user_general_dependency_override
    app.dependency_overrides[sys_admin_admin_dependency] = user_general_dependency_override

    # setup table
    db_client = boto3.client('dynamodb')
    setup_user_group_table(
        client=db_client,
        table_name=config.user_groups_table_name
    )

    # setup groups
    group_count = 10
    groups = setup_n_empty_groups(
        client,
        count=group_count,
    )

    # now remove half of them
    removed_groups = random.sample(groups, int(len(groups) / 2))
    original_ids = set([g.id for g in groups])
    removed_ids = set([g.id for g in removed_groups])

    # remove the groups
    for remove_id in removed_ids:
        _ = parse_status_response(
            response=client.delete(
                group_admin_endpoints.REMOVE_GROUP,
                params={
                    'id': remove_id
                }
            ),
            model=RemoveGroupResponse
        )

    # list the groups
    list_response: ListGroupsResponse = parse_status_response(
        response=client.get(group_admin_endpoints.LIST_GROUPS),
        model=ListGroupsResponse
    )

    # check group id set
    assert list_response.groups
    found_ids = set([g.id for g in list_response.groups])
    desired_ids = original_ids - removed_ids
    assert found_ids == desired_ids


@mock_dynamodb
def test_update_group(provide_global_config: Config, aws_credentials: Any) -> None:
    # config
    config: Config = provide_global_config

    # override admin dependencies
    # TODO only use appropriate
    app.dependency_overrides[sys_admin_read_dependency] = user_general_dependency_override
    app.dependency_overrides[sys_admin_write_dependency] = user_general_dependency_override

    # setup table
    db_client = boto3.client('dynamodb')
    setup_user_group_table(
        client=db_client,
        table_name=config.user_groups_table_name
    )

    # setup groups
    group_count = 10
    groups = setup_n_empty_groups(
        client,
        count=group_count,
    )

    # choose a group
    group = random.choice(groups)

    # update the metadata
    postfix = "updated"
    group.description += postfix
    payload = json.loads(group.json())
    _ = parse_status_response(
        response=client.put(
            group_admin_endpoints.UPDATE_GROUP,
            json=payload
        ),
        model=UpdateGroupResponse
    )

    # describe the group
    describe_response: DescribeGroupResponse = parse_status_response(
        response=client.get(
            group_admin_endpoints.DESCRIBE_GROUP,
            params={
                'id': group.id
            }
        ),
        model=DescribeGroupResponse
    )

    assert smart_raw_compare(describe_response.dict()['group'], group.dict())
