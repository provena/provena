from SharedInterfaces.AsyncJobAPI import *
from config import Config
from helpers.util import py_to_dict
import httpx
from helpers.keycloak_helpers import get_service_token
from dependencies.dependencies import secret_cache
from helpers.async_requests import async_post_request, async_get_request


async def launch_generic_job(payload: AdminLaunchJobRequest, config: Config) -> AdminLaunchJobResponse:
    """

    Lodges the specified job payload using the job API, returns the session ID
    to monitor result

    Args:
        payload (ProvLodgeModelRunPayload): The prov lodge model run job payload

    Returns:
        str: The session_id
    """
    base = config.job_api_endpoint
    postfix = "/jobs/admin/launch"
    endpoint = base + postfix

    request = py_to_dict(payload)

    # Use client auth
    token = get_service_token(secret_cache=secret_cache, config=config)

    try:
        response = await async_post_request(
            endpoint=endpoint,
            params={},
            token=token,
            json_body=request
        )
    except Exception as e:
        raise Exception(f"Failed to launch job using Job API, error: {e}.")

    if response.status_code != 200:
        raise Exception(
            f"Non 200 status code ({response.status_code}) from Job API. Body: {response.text}.")
    try:
        parsed = AdminLaunchJobResponse.parse_obj(response.json())
    except Exception as e:
        raise Exception(
            f"Failed to parse launch job response despite 200OK code. Error: {e}."
        )

    return parsed


async def submit_model_run_lodge_job(username: str, payload: ProvLodgeModelRunPayload, config: Config) -> str:
    """
    Lodges the specified job payload using the job API, returns the session ID
    to monitor result

    Args:
        payload (ProvLodgeModelRunPayload): The prov lodge model run job payload

    Returns:
        str: The session_id
    """
    payload = AdminLaunchJobRequest(
        username=username,
        job_type=JobType.PROV_LODGE,
        job_sub_type=JobSubType.MODEL_RUN_PROV_LODGE,
        job_payload=py_to_dict(payload)
    )
    return (await launch_generic_job(
        payload=payload,
        config=config
    )).session_id


async def submit_batch_lodge_job(username: str, payload: ProvLodgeBatchSubmitPayload, config: Config) -> str:
    """
    Lodges the specified job payload using the job API, returns the session ID
    to monitor result

    Args:
        payload (ProvLodgeModelRunPayload): The prov lodge model run job payload

    Returns:
        str: The session_id
    """
    payload = AdminLaunchJobRequest(
        username=username,
        job_type=JobType.PROV_LODGE,
        job_sub_type=JobSubType.MODEL_RUN_BATCH_SUBMIT,
        job_payload=py_to_dict(payload)
    )
    return (await launch_generic_job(
        payload=payload,
        config=config
    )).session_id


async def fetch_job_by_id_admin(session_id: str, config: Config) -> Optional[JobStatusTable]:
    base = config.job_api_endpoint
    postfix = "/jobs/admin/fetch"
    endpoint = base + postfix
    params = {"session_id": session_id}

    # Use client auth
    token = get_service_token(secret_cache=secret_cache, config=config)

    try:
        response = await async_get_request(
            endpoint=endpoint,
            params=params,
            token=token,
        )
    except Exception as e:
        raise Exception(f"Failed to launch job using Job API, error: {e}.")

    if response.status_code != 200:
        # This is expected 400 err if no item
        if response.status_code == 400:
            return None
        else:
            raise Exception(
                f"Non 200 status code ({response.status_code}) from Job API. Body: {response.text}.")
    try:
        parsed = AdminGetJobResponse.parse_obj(response.json())
    except Exception as e:
        raise Exception(
            f"Failed to parse launch job response despite 200OK code. Error: {e}."
        )

    return parsed.job


async def fetch_jobs_by_batch_id(batch_id: str, token: str, pagination_key: Optional[PaginationKey], config: Config) -> ListByBatchResponse:
    base = config.job_api_endpoint
    postfix = "/jobs/user/list_batch"
    endpoint = base + postfix
    payload = py_to_dict(ListByBatchRequest(
        batch_id=batch_id,
        pagination_key=pagination_key
    ))

    try:
        response = await async_post_request(
            endpoint=endpoint,
            params={},
            json_body=payload,
            token=token,
        )
    except Exception as e:
        raise Exception(f"Failed to launch job using Job API, error: {e}.")

    if response.status_code != 200:
        raise Exception(
            f"Non 200 status code ({response.status_code}) from Job API. Body: {response.text}.")
    try:
        parsed = ListByBatchResponse.parse_obj(response.json())
    except Exception as e:
        raise Exception(
            f"Failed to parse list job response despite 200OK code. Error: {e}."
        )

    return parsed


async def fetch_all_jobs_by_batch_id(batch_id: str, token: str, config: Config) -> List[JobStatusTable]:
    pag_key = None
    first = True
    items: List[JobStatusTable] = []

    while first or (pag_key is not None):
        res = await fetch_jobs_by_batch_id(
            batch_id=batch_id,
            token=token,
            pagination_key=pag_key,
            config=config
        )

        items.extend(res.jobs)
        pag_key = res.pagination_key
        first = False

    return items