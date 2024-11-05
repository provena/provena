from ProvenaInterfaces.AsyncJobAPI import *
from config import Config
from helpers.util import py_to_dict
from helpers.registry.keycloak_helpers import get_service_token
from dependencies.dependencies import secret_cache
from helpers.registry.async_requests import async_post_request


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


async def submit_register_create_activity(username: str, payload: RegistryRegisterCreateActivityPayload, config: Config) -> str:
    """
    Lodges the specified job payload using the job API, returns the session ID
    to monitor result

    Args:
        payload (RegistryRegisterCreateActivityPayload): Payload for job

    Returns:
        str: The session_id
    """
    payload = AdminLaunchJobRequest(
        username=username,
        job_type=JobType.REGISTRY,
        job_sub_type=JobSubType.REGISTER_CREATE_ACTIVITY,
        job_payload=py_to_dict(payload)
    )
    return (await launch_generic_job(
        payload=payload,
        config=config
    )).session_id


async def submit_register_version_activity(username: str, payload: RegistryRegisterVersionActivityPayload, config: Config) -> str:
    """
    Lodges the specified job payload using the job API, returns the session ID
    to monitor result

    Args:
        payload (RegistryRegisterVersionActivityPayload): Payload for job

    Returns:
        str: The session_id
    """
    payload = AdminLaunchJobRequest(
        username=username,
        job_type=JobType.REGISTRY,
        job_sub_type=JobSubType.REGISTER_VERSION_ACTIVITY,
        job_payload=py_to_dict(payload)
    )
    return (await launch_generic_job(
        payload=payload,
        config=config
    )).session_id


async def submit_lodge_create_activity(username: str, payload: ProvLodgeCreationPayload, config: Config) -> str:
    """
    Lodges the specified job payload using the job API, returns the session ID
    to monitor result

    Args:
        payload (ProvLodgeCreationPayload): Payload for job

    Returns:
        str: The session_id
    """
    payload = AdminLaunchJobRequest(
        username=username,
        job_type=JobType.PROV_LODGE,
        job_sub_type=JobSubType.LODGE_CREATE_ACTIVITY,
        job_payload=py_to_dict(payload)
    )
    return (await launch_generic_job(
        payload=payload,
        config=config
    )).session_id


async def submit_lodge_version_activity(username: str, payload: ProvLodgeVersionPayload, config: Config) -> str:
    """
    Lodges the specified job payload using the job API, returns the session ID
    to monitor result

    Args:
        payload (ProvLodgeVersionPayload): Payload for job

    Returns:
        str: The session_id
    """
    payload = AdminLaunchJobRequest(
        username=username,
        job_type=JobType.PROV_LODGE,
        job_sub_type=JobSubType.LODGE_VERSION_ACTIVITY,
        job_payload=py_to_dict(payload)
    )
    return (await launch_generic_job(
        payload=payload,
        config=config
    )).session_id
