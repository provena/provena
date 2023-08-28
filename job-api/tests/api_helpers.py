import tests.env_setup
from fastapi.testclient import TestClient
from SharedInterfaces.AsyncJobModels import *
from SharedInterfaces.AsyncJobAPI import *
from typing import Tuple
from httpx import Response
import json


"""
A set of helpers used by the functionality tests to automate common interactions
with the API through the test client.

Reused in the integration tests but at the requests level instead of test client.
"""

Payload = Dict[str, Any]


def py_to_dict(model: BaseModel) -> Payload:
    return json.loads(model.json(exclude_none=True))


def get_user_route(action: JobsUserActions) -> str:
    return JOBS_USER_PREFIX + JOBS_USER_ACTIONS_MAP[action]


def get_admin_route(action: JobsAdminActions) -> str:
    return JOBS_ADMIN_PREFIX + JOBS_ADMIN_ACTIONS_MAP[action]

# =====
# USER
# =====


def user_fetch_session_id(client: TestClient, session_id: str) -> Response:
    endpoint = get_user_route(JobsUserActions.FETCH)
    params = {'session_id': session_id}
    return client.get(
        url=endpoint,
        params=params
    )


PaginatedJobList = Tuple[List[JobStatusTable], Optional[PaginationKey]]


def user_list(client: TestClient, pag_key: Optional[PaginationKey], limit: int) -> Response:
    endpoint = get_user_route(JobsUserActions.LIST)
    payload = ListJobsRequest(pagination_key=pag_key, limit=limit)
    return client.post(
        url=endpoint,
        json=py_to_dict(payload)
    )


def user_list_batch(client: TestClient, batch_id: str, pag_key: Optional[PaginationKey], limit: int) -> Response:
    endpoint = get_user_route(JobsUserActions.LIST_BATCH)
    payload = ListByBatchRequest(
        batch_id=batch_id, pagination_key=pag_key, limit=limit)
    return client.post(
        url=endpoint,
        json=py_to_dict(payload)
    )


def user_list_parsed(client: TestClient, pag_key: Optional[PaginationKey], limit: int) -> PaginatedJobList:
    response = user_list(client=client, pag_key=pag_key, limit=limit)

    # check 200
    assert response.status_code == 200, f"Expected 200 code for list action, got {response.status_code}. Text: {response.text}"

    # parse the model
    parsed = ListJobsResponse.parse_obj(response.json())

    return parsed.jobs, parsed.pagination_key


def user_list_all(client: TestClient) -> List[JobStatusTable]:
    pag_key = None
    first = True
    items: List[JobStatusTable] = []
    while pag_key is not None or first:
        # Get the list result
        jobs, key = user_list_parsed(client=client, pag_key=pag_key, limit=10)

        # add the new items
        items.extend(jobs)

        # update pag key for more items
        pag_key = key

        first = False

    return items


def user_list_batch_parsed(client: TestClient, batch_id: str, pag_key: Optional[PaginationKey], limit: int) -> PaginatedJobList:
    response = user_list_batch(
        batch_id=batch_id, client=client, pag_key=pag_key, limit=limit)

    # check 200
    assert response.status_code == 200, f"Expected 200 code for list action, got {response.status_code}. Text: {response.text}"

    # parse the model
    parsed = ListByBatchResponse.parse_obj(response.json())

    return parsed.jobs, parsed.pagination_key


def user_list_batch_all(batch_id: str, client: TestClient) -> List[JobStatusTable]:
    pag_key = None
    first = True
    items: List[JobStatusTable] = []
    while pag_key is not None or first:
        # Get the list result
        jobs, key = user_list_batch_parsed(
            batch_id=batch_id, client=client, pag_key=pag_key, limit=10)

        # add the new items
        items.extend(jobs)

        # update pag key for more items
        pag_key = key

        first = False

    return items


def user_fetch_session_id_assert_missing(client: TestClient, session_id: str) -> None:
    response = user_fetch_session_id(client=client, session_id=session_id)
    assert response.status_code == 400, f"Expected 400 code for wrong session id, got {response.status_code}. Text: {response.text}"


def user_fetch_session_id_assert_correct(client: TestClient, session_id: str) -> JobStatusTable:
    response = user_fetch_session_id(client=client, session_id=session_id)
    assert response.status_code == 200, f"Expected 200 code for correct session id, got {response.status_code}. Text: {response.text}"
    payload = response.json()
    parsed = GetJobResponse.parse_obj(payload)
    return parsed.job


# =====
# ADMIN
# =====

def admin_list(client: TestClient, pag_key: Optional[PaginationKey], limit: int, username_filter: Optional[str] = None) -> Response:
    endpoint = get_admin_route(JobsAdminActions.LIST)
    payload = AdminListJobsRequest(
        pagination_key=pag_key, limit=limit, username_filter=username_filter)
    return client.post(
        url=endpoint,
        json=py_to_dict(payload)
    )


def admin_list_batch(client: TestClient, batch_id: str, pag_key: Optional[PaginationKey], limit: int, username_filter: Optional[str] = None) -> Response:
    endpoint = get_admin_route(JobsAdminActions.LIST_BATCH)
    payload = AdminListByBatchRequest(
        batch_id=batch_id, pagination_key=pag_key, limit=limit, username_filter=username_filter)
    return client.post(
        url=endpoint,
        json=py_to_dict(payload)
    )


def admin_list_parsed(client: TestClient, pag_key: Optional[PaginationKey], limit: int, username_filter: Optional[str] = None) -> PaginatedJobList:
    response = admin_list(client=client, pag_key=pag_key,
                          limit=limit, username_filter=username_filter)

    # check 200
    assert response.status_code == 200, f"Expected 200 code for list action, got {response.status_code}. Text: {response.text}"

    # parse the model
    parsed = AdminListJobsResponse.parse_obj(response.json())

    return parsed.jobs, parsed.pagination_key


def admin_list_all(client: TestClient, username_filter: Optional[str] = None) -> List[JobStatusTable]:
    pag_key = None
    first = True
    items: List[JobStatusTable] = []
    while pag_key is not None or first:
        # Get the list result
        jobs, key = admin_list_parsed(
            client=client, pag_key=pag_key, limit=10, username_filter=username_filter)

        # add the new items
        items.extend(jobs)

        # update pag key for more items
        pag_key = key

        first = False

    return items


def admin_list_batch_parsed(client: TestClient, batch_id: str, pag_key: Optional[PaginationKey], limit: int, username_filter: Optional[str] = None) -> PaginatedJobList:
    response = admin_list_batch(
        batch_id=batch_id, client=client, pag_key=pag_key, limit=limit, username_filter=username_filter)

    # check 200
    assert response.status_code == 200, f"Expected 200 code for list action, got {response.status_code}. Text: {response.text}"

    # parse the model
    parsed = AdminListByBatchResponse.parse_obj(response.json())

    return parsed.jobs, parsed.pagination_key


def admin_list_batch_all(batch_id: str, client: TestClient, username_filter: Optional[str] = None) -> List[JobStatusTable]:
    pag_key = None
    first = True
    items: List[JobStatusTable] = []
    while pag_key is not None or first:
        # Get the list result
        jobs, key = admin_list_batch_parsed(
            batch_id=batch_id, client=client, pag_key=pag_key, limit=10, username_filter=username_filter)

        # add the new items
        items.extend(jobs)

        # update pag key for more items
        pag_key = key

        first = False

    return items


def admin_fetch_session_id(client: TestClient, session_id: str) -> Response:
    endpoint = get_admin_route(JobsAdminActions.FETCH)
    params = {'session_id': session_id}
    return client.get(
        url=endpoint,
        params=params
    )


def admin_fetch_session_id_assert_missing(client: TestClient, session_id: str) -> None:
    response = admin_fetch_session_id(client=client, session_id=session_id)
    assert response.status_code == 400, f"Expected 400 code for wrong session id, got {response.status_code}. Text: {response.text}"


def admin_fetch_session_id_assert_correct(client: TestClient, session_id: str) -> JobStatusTable:
    response = admin_fetch_session_id(client=client, session_id=session_id)
    assert response.status_code == 200, f"Expected 200 code for correct session id, got {response.status_code}. Text: {response.text}"
    payload = response.json()
    parsed = GetJobResponse.parse_obj(payload)
    return parsed.job
