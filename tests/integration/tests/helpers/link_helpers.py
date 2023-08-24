from typing import Optional, Any, Dict, List
from requests import Response
import requests
from tests.config import *
from SharedInterfaces.AuthAPI import UserLinkUserLookupResponse, UserLinkReverseLookupResponse
from KeycloakRestUtilities.Token import BearerAuth
from dataclasses import dataclass
from tests.helpers.general_helpers import display_failed_cleanups


def assert_x_ok(res: Response, desired_status_code: int = 200) -> None:
    status_code = res.status_code
    text = res.text
    if status_code != desired_status_code:
        raise Exception(
            f"Failed request, expected {desired_status_code}, got {status_code}. Text: {text}")


def assert_200_ok(res: Response) -> None:
    assert_x_ok(res=res, desired_status_code=200)


def lookup_user_user(token: str,  username: Optional[str] = None) -> UserLinkUserLookupResponse:
    endpoint = user_lookup
    params: Dict[str, Any] = {}
    if username is not None:
        params['username'] = username

    res = requests.get(
        url=endpoint,
        params=params,
        auth=BearerAuth(token)
    )

    # check the status code is 200 ok
    assert_200_ok(res)

    # parse and return
    return UserLinkUserLookupResponse.parse_obj(res.json())


def lookup_user_user_assert_missing(token: str,  username: Optional[str] = None) -> None:
    res = lookup_user_user(token=token, username=username)
    assert res.person_id is None and not res.success, f"Should have been missing person id but included it. Contents: {res.json()}"


def lookup_user_user_assert_success(token: str, username: Optional[str] = None, check_id: Optional[str] = None) -> str:
    res = lookup_user_user(token=token, username=username)
    assert res.person_id is not None and res.success, f"Should have succeeded lookup - but failed. Contents: {res.json()}"
    # check if expected
    if check_id:
        assert res.person_id == check_id, f"Returned an ID succesfully from user lookup, expected {check_id} got {res.person_id}."
    return res.person_id


def assign_user_admin(token: str, person_id: str, username: str, force: bool, succeed: bool, fail_status_override: int = 400) -> None:
    endpoint = admin_assign
    # use dict to enable 422 at api endpoint
    request = {"username": username,
               "person_id": person_id,
               "validate_item": False,
               "force": force
               }

    res = requests.post(
        url=endpoint,
        json=request,
        auth=BearerAuth(token)
    )

    # check the status code is 200 ok
    if succeed:
        assert_x_ok(res, desired_status_code=200)
    else:
        # use the override (desired status code, defaults to 400)
        assert_x_ok(res, desired_status_code=fail_status_override)


def assign_user_user(token: str,  person_id: str, succeed: bool, fail_status_override: int = 400) -> None:
    endpoint = user_assign
    # use dict to enable 422 at api endpoint
    request = {"person_id": person_id}

    res = requests.post(
        url=endpoint,
        json=request,
        auth=BearerAuth(token)
    )

    # check the status code is 200 ok
    if succeed:
        assert_x_ok(res, desired_status_code=200)
    else:
        # use the override (desired status code, defaults to 400)
        assert_x_ok(res, desired_status_code=fail_status_override)


def assign_user_user_assert_fail(token: str, person_id: str) -> None:
    assign_user_user(token=token,
                     person_id=person_id, succeed=False)


def assign_user_user_assert_success(token: str, person_id: str) -> None:
    assign_user_user(token=token,
                     person_id=person_id, succeed=True)


def assign_user_user_assert_parse_error(token: str, person_id: str) -> None:
    assign_user_user(token=token,  person_id=person_id,
                     succeed=False, fail_status_override=422)


def assign_user_admin_assert_fail(token: str, person_id: str, force: bool, username: str) -> None:
    assign_user_admin(token=token, person_id=person_id,
                      succeed=False, force=force, username=username)


def assign_user_admin_assert_success(token: str, person_id: str, force: bool, username: str) -> None:
    assign_user_admin(token=token, person_id=person_id,
                      succeed=True, force=force, username=username)


def assign_user_admin_assert_parse_error(token: str, person_id: str, force: bool, username: str) -> None:
    assign_user_admin(token=token, person_id=person_id,
                      succeed=False, fail_status_override=422, force=force, username=username)


def clear_user_admin(token: str, username: str) -> None:
    endpoint = admin_clear
    # use dict to enable 422 at api endpoint
    params = {"username": username,
              }

    res = requests.delete(
        url=endpoint,
        params=params,
        auth=BearerAuth(token)
    )

    assert_200_ok(res)


def reverse_lookup(token: str, person_id: str) -> List[str]:
    endpoint = admin_reverse_lookup
    # use dict to enable 422 at api endpoint
    params = {"person_id": person_id,
              }

    res = requests.get(
        url=endpoint,
        params=params,
        auth=BearerAuth(token)
    )

    assert_200_ok(res)

    return UserLinkReverseLookupResponse.parse_obj(res.json()).usernames


def reverse_lookup_assert_list(token: str, person_id: str, usernames: List[str]) -> None:
    usernames = reverse_lookup(token=token, person_id=person_id)

    assert len(usernames) == len(
        usernames), f"Lengths of lists don't match, received: {usernames}, wanted {usernames}."
    assert len(set(usernames)) == len(
        usernames), f"Non unique elements in returned username list."

    for want in usernames:
        assert want in usernames, f"Missing username: {want} from {usernames}."


@dataclass
class FailedLinkCleanup():
    username: str
    error_msg: str


def perform_link_cleanup(link_usernames: List[str], token: str) -> None:
    print(f"Starting cleanup of link service links, {len(link_usernames) =}")
    failed_cleanups: List[FailedLinkCleanup] = []

    for username in link_usernames:
        try:
            clear_user_admin(token=token, username=username)
        except Exception as e:
            failed_cleanups.append(
                FailedLinkCleanup(
                    username=username,
                    error_msg=str(e)
                ))

    # removed all items - clear - don't want to remove the same elements
    # multiple times
    link_usernames.clear()
    
    if len(failed_cleanups) > 0:
        display_failed_cleanups(failed_cleanups)
        assert False, "Failed to clean up all links"

    return
