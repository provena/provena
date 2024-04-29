import logging
from fastapi import APIRouter, Depends, HTTPException
from config import get_settings, Config
from KeycloakFastAPI.Dependencies import User
from dependencies.dependencies import user_general_dependency
from ProvenaInterfaces.AsyncJobAPI import *
from service.jobs.user import *

# setup logger
logging.config.fileConfig('logging.conf', disable_existing_loggers=False)

# get logger for this module
logger_key = "userService"
logger = logging.getLogger(logger_key)

router = APIRouter()


@router.get(JOBS_USER_ACTIONS_MAP[JobsUserActions.FETCH], operation_id="get_job")
async def get_job(
    session_id: str,
    user: User = Depends(user_general_dependency),
    config: Config = Depends(get_settings)
) -> GetJobResponse:
    logging.info("Starting user fetch operation.")

    # get the item
    try:
        item = get_job_by_session_id(
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

    if item.username != user.username:
        raise HTTPException(status_code=401,
                            detail=f"Not authorised to view this record.")

    return GetJobResponse(
        job=item
    )


@router.post(JOBS_USER_ACTIONS_MAP[JobsUserActions.LIST], operation_id="list_jobs")
async def list_jobs(
    request: ListJobsRequest,
    user: User = Depends(user_general_dependency),
    config: Config = Depends(get_settings)
) -> ListJobsResponse:
    logging.info("Starting user list operation.")

    # get the item
    try:
        items, pag_key = list_jobs_by_username(
            username=user.username,
            table_name=config.status_table_name,
            username_index=config.username_index_name,
            pagination_key=request.pagination_key,
            limit=request.limit
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Unexpected internal error occurred: {e}")

    return ListJobsResponse(
        jobs=items,
        pagination_key=pag_key
    )


@router.post(JOBS_USER_ACTIONS_MAP[JobsUserActions.LIST_BATCH], operation_id="list_batch")
async def list_batch(
    request: ListByBatchRequest,
    user: User = Depends(user_general_dependency),
    config: Config = Depends(get_settings)
) -> ListByBatchResponse:
    logging.info("Starting batch list operation.")

    # get the item
    try:
        items, pag_key = list_batch_by_batch_id(
            batch_id=request.batch_id,
            table_name=config.status_table_name,
            batch_id_index=config.batch_id_index_name,
            pagination_key=request.pagination_key,
            limit=request.limit
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Unexpected internal error occurred: {e}")

    for item in items:
        if item.username != user.username:
            raise HTTPException(
                status_code=401,
                detail=f"Batch contains items which you do not own. Not authorised."
            )

    return ListByBatchResponse(
        jobs=items,
        pagination_key=pag_key
    )


@router.post("/retry", operation_id="retry_job",
             # Remove this annotation once destubbed
             include_in_schema=False)
async def retry_job(
    session_id: str,
    _: User = Depends(user_general_dependency),
    config: Config = Depends(get_settings)
) -> RetryJobResponse:
    # TODO Destub
    logging.info("Stubbed method - not yet implemented")
    raise HTTPException(
        status_code=400,
        detail="Not yet implemented"
    )
