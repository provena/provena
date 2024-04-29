from fastapi import APIRouter, Depends, HTTPException
from config import get_settings, Config
from KeycloakFastAPI.Dependencies import User, ProtectedRole
from dependencies.dependencies import admin_user_protected_role_dependency, read_user_protected_role_dependency, read_write_user_protected_role_dependency
from ProvenaInterfaces.AsyncJobAPI import *
import logging
import service.jobs.admin as admin_service
import service.jobs.user as user_service

# setup logger
logging.config.fileConfig('logging.conf', disable_existing_loggers=False)

# get logger for this module
logger_key = "adminService"
logger = logging.getLogger(logger_key)

router = APIRouter()


@router.post(JOBS_ADMIN_ACTIONS_MAP[JobsAdminActions.LAUNCH], operation_id="launch_job")
async def launch_job(
    request: AdminLaunchJobRequest,
    roles: ProtectedRole = Depends(read_write_user_protected_role_dependency),
    config: Config = Depends(get_settings)
) -> AdminLaunchJobResponse:
    logging.info(f"Launching task. Request: {request}.")

    # determine appropriate username to use
    username = request.username or roles.user.username
    logging.info(f"Lodging with username {username}.")

    logging.info(f"Validating payload")
    try:
        admin_service.validate_payload(
            job_sub_type=request.job_sub_type,
            job_specific_payload=request.job_payload
        )
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid payload supplied: {e}."
        )

    logging.info("Lodging job.")
    try:
        service_response = admin_service.launch_job(
            username=username,
            request_batch_id=request.request_batch_id,
            batch_id=request.add_to_batch,
            job_type=request.job_type,
            job_sub_type=request.job_sub_type,
            job_specific_payload=request.job_payload,
            table_name=config.status_table_name,
            sns_topic_arn=admin_service.get_correct_topic_arn(
                job_type=request.job_type,
                config=config
            ),
            batch_id_index_name=config.batch_id_index_name
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to lodge job, error: {e}."
        )

    return AdminLaunchJobResponse(
        session_id=service_response.session_id,
        batch_id=service_response.batch_id
    )


@router.get(JOBS_ADMIN_ACTIONS_MAP[JobsAdminActions.FETCH], operation_id="admin_get_job")
async def get_job(
    session_id: str,
    _: User = Depends(read_user_protected_role_dependency),
    config: Config = Depends(get_settings)
) -> AdminGetJobResponse:
    logging.info("Starting user fetch operation.")

    # get the item
    try:
        item = user_service.get_job_by_session_id(
            session_id=session_id,
            table_name=config.status_table_name
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Unexpected internal error occurred: {e}")

    if item is None:
        raise HTTPException(
            status_code=400,
            detail=f"Item was not found."
        )

    return AdminGetJobResponse(
        job=item
    )


@router.post(JOBS_ADMIN_ACTIONS_MAP[JobsAdminActions.LIST], operation_id="admin_list_jobs")
async def list_jobs(
    request: AdminListJobsRequest,
    _: User = Depends(read_user_protected_role_dependency),
    config: Config = Depends(get_settings)
) -> AdminListJobsResponse:
    logging.info(f"Querying all jobs. Request: {request}.")
    try:
        items, pag_key = admin_service.list_jobs(
            username=request.username_filter,
            table_name=config.status_table_name,
            username_index=config.username_index_name,
            pagination_key=request.pagination_key,
            global_index_name=config.global_list_index_name,
            limit=request.limit
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list jobs, error: {e}."
        )

    return AdminListJobsResponse(
        jobs=items,
        pagination_key=pag_key
    )


@router.post(JOBS_ADMIN_ACTIONS_MAP[JobsAdminActions.LIST_BATCH], operation_id="admin_list_batch")
async def list_batch(
    request: AdminListByBatchRequest,
    user: User = Depends(read_user_protected_role_dependency),
    config: Config = Depends(get_settings)
) -> AdminListByBatchResponse:
    logging.info("Starting admin batch list operation.")

    # get the item
    try:
        items, pag_key = user_service.list_batch_by_batch_id(
            batch_id=request.batch_id,
            table_name=config.status_table_name,
            batch_id_index=config.batch_id_index_name,
            pagination_key=request.pagination_key,
            limit=request.limit
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Unexpected internal error occurred: {e}")

    if request.username_filter:
        for item in items:
            if item.username != user.username:
                raise HTTPException(
                    status_code=400,
                    detail=f"Batch contains items which do not adhere to the username filter. Aborting."
                )

    return AdminListByBatchResponse(
        jobs=items,
        pagination_key=pag_key
    )


@router.post("/retry", operation_id="admin_retry_job",
             # Remove this annotation once destubbed
             include_in_schema=False)
async def retry_job(
    session_id: str,
    _: User = Depends(read_write_user_protected_role_dependency),
    config: Config = Depends(get_settings)
) -> AdminRetryJobResponse:
    # TODO Destub
    logging.info("Stubbed method - not yet implemented")
    raise HTTPException(
        status_code=400,
        detail="Not yet implemented"
    )
