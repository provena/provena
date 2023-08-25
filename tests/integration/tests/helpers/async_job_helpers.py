from typing import Dict, Any, Callable, Optional, cast, Tuple
from SharedInterfaces.AsyncJobModels import JobStatusTable
from SharedInterfaces.AsyncJobAPI import *
from KeycloakRestUtilities.Token import BearerAuth
import requests
from requests import Response
from datetime import datetime
from time import sleep
from tests.config import config, TokenGenerator
from tests.helpers.shared_lists import cleanup_items
from SharedInterfaces.RegistryModels import ItemBase, ItemCategory
from SharedInterfaces.DataStoreAPI import MintResponse

# How long to wait for various states
JOB_POLLING_INTERVAL = 2  # poll every 2 seconds

# how long do we wait for the entry to be present in table?
JOB_ASYNC_QUEUE_DELAY_POLLING_TIMEOUT = 20  # 20 seconds

# How long do we wait for it to leave pending?
JOB_ASYNC_PENDING_POLLING_TIMEOUT = 600  # 10 minutes

# How long do we wait for it to become in progress?
JOB_ASYNC_IN_PROGRESS_POLLING_TIMEOUT = 300  # 5 minutes


JOB_FINISHED_STATES = [JobStatus.FAILED, JobStatus.SUCCEEDED]

Payload = Dict[str, Any]


def get_user_route(action: JobsUserActions) -> str:
    return config.JOB_API_ENDPOINT + JOBS_USER_PREFIX + JOBS_USER_ACTIONS_MAP[action]


def get_admin_route(action: JobsAdminActions) -> str:
    return config.JOB_API_ENDPOINT + JOBS_ADMIN_PREFIX + JOBS_ADMIN_ACTIONS_MAP[action]


def user_fetch_session_id(session_id: str, token: str) -> Response:
    endpoint = get_user_route(action=JobsUserActions.FETCH)
    params = {'session_id': session_id}
    return requests.get(
        url=endpoint,
        params=params,
        auth=BearerAuth(token),
    )


def user_fetch_session_id_assert_correct(session_id: str, token: str) -> JobStatusTable:
    response = user_fetch_session_id(
        session_id=session_id, token=token)
    assert response.status_code == 200, f"Expected 200 code for correct session id, got {response.status_code}. Text: {response.text}"
    payload = response.json()
    parsed = GetJobResponse.parse_obj(payload)
    return parsed.job


def timestamp() -> int:
    return int(datetime.now().timestamp())


# finished? optional data
PollCallbackData = Optional[Any]
PollCallbackResponse = Tuple[bool, PollCallbackData]
PollCallbackFunction = Callable[[TokenGenerator], PollCallbackResponse]


class PollTimeoutException(Exception):
    "Raised when poll operation exceeds timeout"
    pass


class PollFunctionErrorException(Exception):
    "Raised when poll operation callback errors"
    pass


def poll_callback(poll_interval_seconds: int, timeout_seconds: int, get_token: TokenGenerator, callback: PollCallbackFunction) -> PollCallbackData:
    start_time = timestamp()
    completed = False
    data = None

    def timeout_condition_check() -> bool:
        curr = timestamp()
        return curr - start_time <= timeout_seconds

    def print_status() -> None:
        print(
            f"Polling Job API. Wait time: {round(timestamp() - start_time,2)}sec out of {timeout_seconds}sec.")

    while (not completed) and timeout_condition_check():
        print_status()

        try:
            fin, res_data = callback(get_token)
        except Exception as e:
            raise PollFunctionErrorException(
                f"Polling callback function raised an error. Aborting. Error: {e}.")

        if fin:
            data = res_data
            completed = True
        else:
            print("Callback registered incomplete. Waiting for polling interval.")
            sleep(poll_interval_seconds)

    if completed:
        return data
    else:
        raise PollTimeoutException("Timed out during polling operation.")


def wait_for_in_progress(session_id: str, get_token: TokenGenerator) -> JobStatusTable:
    timeout = JOB_ASYNC_PENDING_POLLING_TIMEOUT
    interval = JOB_POLLING_INTERVAL

    def callback(get_token: TokenGenerator) -> PollCallbackResponse:
        print(
            f"Running wait for in progress callback. Session ID: {session_id}.")
        entry = user_fetch_session_id_assert_correct(
            session_id=session_id,
            token=get_token()
        )
        # stop if we exit pending - could jump straight to error/success otherwise
        if entry.status != JobStatus.PENDING:
            print(
                f"200OK response for user fetch of {session_id} in non pending state {entry.status}.")
            return True, entry
        else:
            print(
                f"200OK response for user fetch of {session_id} in state {entry.status}.")
            return False, None

    # poll
    print(f"Starting wait_for_in_progress polling stage.")
    data = poll_callback(
        poll_interval_seconds=interval,
        timeout_seconds=timeout,
        get_token=get_token,
        callback=callback
    )
    print(f"Finished wait_for_in_progress polling stage.")

    assert data is not None
    return cast(JobStatusTable, data)


def wait_for_entry_in_queue(session_id: str, get_token: TokenGenerator) -> JobStatusTable:
    timeout = JOB_ASYNC_QUEUE_DELAY_POLLING_TIMEOUT
    interval = JOB_POLLING_INTERVAL

    def callback(get_token: TokenGenerator) -> PollCallbackResponse:
        print(
            f"Running wait_for_entry_in_queue callback. Session ID: {session_id}.")
        response = user_fetch_session_id(
            session_id=session_id,
            token=get_token()
        )

        if response.status_code == 200:
            print(f"200OK response for user fetch of {session_id}.")
            # Parse and return the 200OK data
            parsed_res = GetJobResponse.parse_obj(response.json())
            entry: JobStatusTable = parsed_res.job
            return True, entry
        if response.status_code != 400:
            raise Exception(
                f"Unexpected error state when waiting for job. Code: {response.status_code}. Error: {response.text}.")
        else:
            return False, None

    # poll
    print(f"Starting wait_for_entry_in_queue polling stage.")
    data = poll_callback(
        poll_interval_seconds=interval,
        timeout_seconds=timeout,
        get_token=get_token,
        callback=callback
    )
    print(f"Finished wait_for_entry_in_queue polling stage.")

    return cast(JobStatusTable, data)


def wait_for_completion(session_id: str, get_token: TokenGenerator) -> JobStatusTable:
    timeout = JOB_ASYNC_IN_PROGRESS_POLLING_TIMEOUT
    interval = JOB_POLLING_INTERVAL

    def callback(get_token: TokenGenerator) -> PollCallbackResponse:
        print(
            f"Running wait for completion callback. Session ID: {session_id}.")
        entry = user_fetch_session_id_assert_correct(
            session_id=session_id,
            token=get_token()
        )
        # stop if we exit pending - could jump straight to error/success otherwise
        if entry.status in JOB_FINISHED_STATES:
            print(
                f"200OK response for user fetch of {session_id} in completed state.")
            return True, entry
        else:
            print(
                f"200OK response for user fetch of {session_id} in state {entry.status}.")
            return False, None

    # poll
    print(f"Starting wait_for_completion polling stage.")
    data = poll_callback(
        poll_interval_seconds=interval,
        timeout_seconds=timeout,
        get_token=get_token,
        callback=callback
    )
    print(f"Finished wait_for_completion polling stage.")

    assert data is not None
    return cast(JobStatusTable, data)


def wait_for_full_lifecycle(session_id: str, get_token: TokenGenerator) -> JobStatusTable:
    # wait for item to be present in job table - could take a few seconds
    data = wait_for_entry_in_queue(session_id=session_id, get_token=get_token)

    # backout early
    if data.status in JOB_FINISHED_STATES:
        return data

    # block into two steps to time separately
    data = wait_for_in_progress(session_id=session_id, get_token=get_token)

    # backout early
    if data.status in JOB_FINISHED_STATES:
        return data

    return wait_for_completion(session_id=session_id, get_token=get_token)


def wait_for_full_successful_lifecycle(session_id: str, get_token: TokenGenerator) -> JobStatusTable:
    res = wait_for_full_lifecycle(session_id=session_id, get_token=get_token)

    assert res.status == JobStatus.SUCCEEDED,\
        f"Job failed, error {res.info or 'None provided'}. Session ID {session_id}."

    assert res.result is not None,\
        f"Job succeeded, but did not include a result payload!"

    return res


def cleanup_create_activity_from_item_base(item: ItemBase, get_token: TokenGenerator) -> None:
    assert item.item_category == ItemCategory.ENTITY, f"Cleaning up registry create for non Entity will freeze because no such item exists"
    if item.workflow_links is not None and\
            item.workflow_links.create_activity_workflow_id is not None:
        # Ensure the workflow links were updated

        # wait for the complete lifecycle - step 1
        create_response = wait_for_full_successful_lifecycle(
            session_id=item.workflow_links.create_activity_workflow_id,
            get_token=get_token
        )

        assert create_response.result is not None
        parsed_result = RegistryRegisterCreateActivityResult.parse_obj(
            create_response.result)
        creation_activity_id = parsed_result.creation_activity_id
        cleanup_items.append(
            (ItemSubType.CREATE, creation_activity_id))


def cleanup_create_activity_from_dataset_mint(mint_response: MintResponse, get_token: TokenGenerator) -> None:
    assert mint_response.register_create_activity_session_id is not None
    # Ensure the workflow links were updated

    # wait for the complete lifecycle - step 1
    create_response = wait_for_full_successful_lifecycle(
        session_id=mint_response.register_create_activity_session_id,
        get_token=get_token
    )

    assert create_response.result is not None
    parsed_result = RegistryRegisterCreateActivityResult.parse_obj(
        create_response.result)
    creation_activity_id = parsed_result.creation_activity_id
    cleanup_items.append((ItemSubType.CREATE, creation_activity_id))
