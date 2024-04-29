from typing import Optional, Any, Dict
from fastapi.testclient import TestClient
from httpx import Response
from tests.config import *
from ProvenaInterfaces.AuthAPI import UserLinkUserLookupResponse, UserLinkReverseLookupResponse


def assert_x_ok(res: Response, desired_status_code: int = 200) -> None:
    status_code = res.status_code
    text = res.text
    if status_code != desired_status_code:
        raise Exception(
            f"Failed request, expected {desired_status_code}, got {status_code}. Text: {text}")


def assert_200_ok(res: Response) -> None:
    assert_x_ok(res=res, desired_status_code=200)


def user_lookup_user(client: TestClient, username: Optional[str] = None) -> UserLinkUserLookupResponse:
    endpoint = user_lookup
    params: Dict[str, Any] = {}
    if username is not None:
        params['username'] = username

    res = client.get(
        url=endpoint,
        params=params,
    )

    # check the status code is 200 ok
    assert_200_ok(res)

    # parse and return
    return UserLinkUserLookupResponse.parse_obj(res.json())


def user_lookup_user_assert_missing(client: TestClient, username: Optional[str] = None) -> None:
    res = user_lookup_user(client=client, username=username)
    assert res.person_id is None and not res.success, f"Should have been missing person id but included it. Contents: {res.json()}"


def user_lookup_user_assert_success(client: TestClient, username: Optional[str] = None, check_id: Optional[str] = None) -> str:
    res = user_lookup_user(client=client, username=username)
    assert res.person_id is not None and res.success, f"Should have succeeded lookup - but failed. Contents: {res.json()}"
    # check if expected
    if check_id:
        assert res.person_id == check_id, f"Returned an ID succesfully from user lookup, expected {check_id} got {res.person_id}."
    return res.person_id


def admin_assign_link(client: TestClient, person_id: str, username: str, force: bool, succeed: bool, fail_status_override: int = 400) -> None:
    endpoint = admin_assign
    # use dict to enable 422 at api endpoint
    request = {"username": username,
               "person_id": person_id,
               "validate_item": False,
               "force": force
               }

    res = client.post(
        url=endpoint,
        json=request
    )

    # check the status code is 200 ok
    if succeed:
        assert_x_ok(res, desired_status_code=200)
    else:
        # use the override (desired status code, defaults to 400)
        assert_x_ok(res, desired_status_code=fail_status_override)


def user_assign_link(client: TestClient, person_id: str, succeed: bool, fail_status_override: int = 400) -> None:
    endpoint = user_assign
    # use dict to enable 422 at api endpoint
    request = {"person_id": person_id}

    res = client.post(
        url=endpoint,
        json=request
    )

    # check the status code is 200 ok
    if succeed:
        assert_x_ok(res, desired_status_code=200)
    else:
        # use the override (desired status code, defaults to 400)
        assert_x_ok(res, desired_status_code=fail_status_override)


def user_assign_link_assert_fail(client: TestClient, person_id: str) -> None:
    user_assign_link(client=client, person_id=person_id, succeed=False)


def user_assign_link_assert_success(client: TestClient, person_id: str) -> None:
    user_assign_link(client=client, person_id=person_id, succeed=True)


def user_assign_user_assert_parse_error(client: TestClient, person_id: str) -> None:
    user_assign_link(client=client, person_id=person_id,
                     succeed=False, fail_status_override=422)


def admin_assign_link_assert_fail(client: TestClient, person_id: str, force: bool, username: str) -> None:
    admin_assign_link(client=client, person_id=person_id,
                      succeed=False, force=force, username=username)


def admin_assign_link_assert_success(client: TestClient, person_id: str, force: bool, username: str) -> None:
    admin_assign_link(client=client, person_id=person_id,
                      succeed=True, force=force, username=username)


def admin_assign_link_assert_parse_error(client: TestClient, person_id: str, force: bool, username: str) -> None:
    admin_assign_link(client=client, person_id=person_id,
                      succeed=False, fail_status_override=422, force=force, username=username)


def admin_clear_link(client: TestClient, username: str) -> None:
    endpoint = admin_clear
    # use dict to enable 422 at api endpoint
    params = {"username": username,
              }

    res = client.delete(
        url=endpoint,
        params=params
    )

    assert_200_ok(res)


def admin_person_lookup(client: TestClient, person_id: str) -> List[str]:
    endpoint = admin_reverse_lookup
    # use dict to enable 422 at api endpoint
    params = {"person_id": person_id,
              }

    res = client.get(
        url=endpoint,
        params=params
    )

    assert_200_ok(res)

    return UserLinkReverseLookupResponse.parse_obj(res.json()).usernames


def admin_reverse_lookup_assert_equality(client: TestClient, person_id: str, usernames: List[str]) -> None:
    usernames = admin_person_lookup(client=client, person_id=person_id)

    assert len(usernames) == len(
        usernames), f"Lengths of lists don't match, received: {usernames}, wanted {usernames}."
    assert len(set(usernames)) == len(
        usernames), f"Non unique elements in returned username list."

    for want in usernames:
        assert want in usernames, f"Missing username: {want} from {usernames}."
