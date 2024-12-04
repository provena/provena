from tests.config import config
import requests
from KeycloakRestUtilities.Token import BearerAuth
from typing import Dict
from ProvenaInterfaces.AuthAPI import *
from requests import Response
from tests.helpers.general_helpers import display_failed_cleanups, py_to_dict

# TODO - use user endpoints for some of these?
add_group_route = "/groups/admin/add_group"
remove_group_route = "/groups/admin/remove_group"
add_member_route = "/groups/admin/add_member"
check_member_route = "/groups/admin/check_membership"
list_members_route = "/groups/admin/list_members"
list_user_groups = "/groups/admin/list_user_membership"
remove_member_route = "/groups/admin/remove_member"
update_group_route = "/groups/admin/update_group"
describe_group_route = "/groups/admin/describe_group"


def add_group_successfully(group_metadata: Dict[str, str], token: str) -> AddGroupResponse:
    resp = requests.post(
        config.AUTH_API_ENDPOINT + add_group_route,
        auth=BearerAuth(token),
        json=group_metadata,
    )

    assert resp.status_code == 200, f"Non 200 status code recieved for add group: {resp}. Response: {resp.text}."
    resp = AddGroupResponse.parse_obj(resp.json())
    assert resp.status.success, f"Failed to successfully create group. Details: {resp.status.details}."

    return resp


def remove_group(id: str, token: str) -> Response:
    resp = requests.delete(
        config.AUTH_API_ENDPOINT + remove_group_route,
        auth=BearerAuth(token),
        params={"id": id},
    )

    return resp


def remove_member_successfully(username: str, group_id: str, token: str) -> RemoveMemberResponse:
    resp = requests.delete(
        config.AUTH_API_ENDPOINT + remove_member_route,
        auth=BearerAuth(token),
        params={"group_id": group_id, "username": username},
    )

    assert resp.status_code == 200, f"Non 200 status code recieved for remove member from group: {resp.status_code}. Response: {resp.text}."
    resp = RemoveMemberResponse.parse_obj(resp.json())
    assert resp.status.success, f"Failed to successfully remove member from group. Details: {resp.status.details}."

    return resp


def remove_group_successfully(id: str, token: str) -> RemoveGroupResponse:
    resp = requests.delete(
        config.AUTH_API_ENDPOINT + remove_group_route,
        auth=BearerAuth(token),
        params={"id": id},
    )
    assert resp.status_code == 200, f"Non 200 status code recieved for remove group: {resp.status_code}. Response: {resp.text}."
    resp = RemoveGroupResponse.parse_obj(resp.json())
    assert resp.status.success, f"Failed to successfully create group. Details: {resp.status.details}."

    return resp


def add_member_to_group_successfully(user: GroupUser, group_id: str, token: str) -> AddMemberResponse:
    resp = requests.post(
        config.AUTH_API_ENDPOINT + add_member_route,
        auth=BearerAuth(token),
        params={
            'group_id': group_id
        },
        json=py_to_dict(user),
    )

    assert resp.status_code == 200, f"Non 200 status code recieved for add member to group: {resp.status_code}. Response: {resp.text}."
    resp = AddMemberResponse.parse_obj(resp.json())
    assert resp.status.success, f"Failed to successfully create group. Details: {resp.status.details}."

    return resp


def check_member(username: str, group_id: str, token: str) -> CheckMembershipResponse:

    resp = requests.get(
        config.AUTH_API_ENDPOINT + check_member_route,
        auth=BearerAuth(token),
        params={
            'username': username,
            'group_id': group_id
        },
    )

    assert resp.status_code == 200, f"Non 200 status code recieved for check membership: {resp.status_code}. Response: {resp.text}."
    resp = CheckMembershipResponse.parse_obj(resp.json())
    assert resp.status.success, f"Failed to successfully check membership. Details: {resp.status.details}."

    return resp


def user_is_member(username: str, group_id: str, token: str) -> bool:
    check_member_resp = check_member(
        username=username, group_id=group_id, token=token)
    if check_member_resp.is_member is not None:
        return check_member_resp.is_member
    else:
        raise Exception(
            f"Failed to check whether user is a member of group or not. Response: {check_member_resp}")


def get_group_membership_list(group_id: str, token: str) -> ListMembersResponse:
    resp = requests.get(
        config.AUTH_API_ENDPOINT + list_members_route,
        auth=BearerAuth(token),
        params={
            'id': group_id
        },
    )

    assert resp.status_code == 200, f"Non 200 status code recieved for members list: {resp.status_code}.. Response: {resp.text}."
    resp = ListMembersResponse.parse_obj(resp.json())
    assert resp.status.success, f"Failed to successfully list members. Details: {resp.status.details}."

    return resp


def get_user_groups(username: str, token: str) -> ListUserMembershipResponse:
    resp = requests.get(
        config.AUTH_API_ENDPOINT + list_user_groups,
        auth=BearerAuth(token),
        params={
            'username': username
        },
    )

    assert resp.status_code == 200, f"Non 200 status code recieved for list user memberships: {resp.status_code}. Response: {resp.text}."
    resp = ListUserMembershipResponse.parse_obj(resp.json())
    assert resp.status.success, f"Failed to successfully list user membeships. Details: {resp.status.details}."

    return resp


class FailedGroupDelete:
    group_id: str
    error_msg: str

    def __init__(self, group_id: str, error_msg: str) -> None:
        self.group_id = group_id
        self.error_msg = error_msg

    # overide to string method.
    def __str__(self) -> str:
        return f"group_id: {self.group_id}. Error: {self.error_msg}."


def perform_group_cleanup(cleanup_group_ids: List[str], token: str) -> None:
    failed_group_removals: List[FailedGroupDelete] = []
    for group_id in cleanup_group_ids:
        try:
            remove_group_successfully(id=group_id, token=token)
        except Exception as e:
            failed_group_removals.append(FailedGroupDelete(
                group_id=group_id,
                error_msg=str(e)
            ))

    # removed all items - clear - don't want to remove the same elements multiple times
    cleanup_group_ids.clear()
    if failed_group_removals:
        display_failed_cleanups(failed_group_removals)
        assert False, "Failed to cleanup groups."


def update_group_successfully(group_metadata: Dict[str, Any], token: str) -> UpdateGroupResponse:

    resp = requests.put(
        config.AUTH_API_ENDPOINT + update_group_route,
        auth=BearerAuth(token),
        json=group_metadata
    )

    assert resp.status_code == 200, f"Non 200 status code recieved for update group: {resp.status_code}. Response: {resp.text}."
    resp = UpdateGroupResponse.parse_obj(resp.json())
    assert resp.status.success, f"Failed to successfully update group. Details: {resp.status.details}."

    return resp


def describe_group(group_id: str, token: str) -> DescribeGroupResponse:
    resp = requests.get(
        config.AUTH_API_ENDPOINT + describe_group_route,
        auth=BearerAuth(token),
        params={
            'id': group_id
        },
    )

    assert resp.status_code == 200, f"Non 200 status code recieved for describe group: {resp.status_code}. Response: {resp.text}."
    resp = DescribeGroupResponse.parse_obj(resp.json())
    assert resp.status.success, f"Failed to successfully describe group. Details: {resp.status.details}."

    return resp
