from SharedInterfaces.JobModels import *
from SharedInterfaces.ProvenanceAPI import *
from SharedInterfaces.SharedTypes import Status
from dependencies.dependencies import read_user_protected_role_dependency, read_write_user_protected_role_dependency
from KeycloakFastAPI.Dependencies import User, ProtectedRole
from fastapi import APIRouter, Depends, HTTPException
from config import get_settings, Config
from datetime import datetime
from helpers.job_helpers import *
import uuid

router = APIRouter()


def check_unique(model_run: ModelRunRecord) -> bool:
    # De-stub TODO
    return True


@router.post("/submit", operation_id="bulk_submit", response_model=BulkSubmissionResponse)
async def bulk_submit(
    records: BulkSubmission,
    role: ProtectedRole = Depends(read_write_user_protected_role_dependency),
    config: Config = Depends(get_settings)
) -> BulkSubmissionResponse:
    model_runs = records.jobs
    
    # pull out username from token 
    username = role.user.username

    # make sure there are actually some runs
    if len(model_runs) == 0:
        raise HTTPException(
            status_code=400,
            detail="You provided no model run records to lodge, no action taken."
        )

    # for each job add a hook to validate uniqueness (?)
    for index, model_run in enumerate(model_runs):
        if not check_unique(model_run):
            raise HTTPException(
                status_code=400, detail=f"Non unique model run record! Index: {index}. Description: {model_run.description}."
            )

    # generate a unique job ID for each (or use the users?)
    def generate_job_log(model_run: ModelRunRecord) -> LodgeModelRunJobRequest:
        return LodgeModelRunJobRequest(
            id=str(uuid.uuid4()),
            username=username,
            model_run_record=model_run,
            submitted_time=int(datetime.now().timestamp())
        )

    batch_id = str(uuid.uuid4())
    job_requests = list(map(generate_job_log, model_runs))

    # update the batch table in user username - this is a way to track collections
    # of jobs for the specified user identified by username
    add_user_batch_job(
        username=username,
        batch_id=batch_id,
        jobs=[req.id for req in job_requests],
        config=config
    )

    # then publish an SNS topic for each record
    # this will add them to a job queue which will be handled asynchronously
    for job in job_requests:
        publish_job_request(job_request=job, config=config)

    return BulkSubmissionResponse(
        status=Status(
            success=True, details=f"Successfully lodged {len(job_requests)} jobs."),
        jobs=job_requests,
        batch_id=batch_id
    )


@router.get("/describe_job", operation_id="describe_job", response_model=DescribeJobResponse)
async def describe_job(
    job_id: str,
    _: User = Depends(read_user_protected_role_dependency),
    config: Config = Depends(get_settings)
) -> DescribeJobResponse:
    log_item = get_model_run_log_item(id=job_id, config=config)
    if log_item is None:
        return DescribeJobResponse(
            status=Status(
                success=False, details=f"Job with id {job_id} does not exist in log.")
        )
    else:
        return DescribeJobResponse(
            status=Status(
                success=True, details=f"Found job with id {job_id}."),
            job_info=log_item
        )


@router.get("/describe_batch", operation_id="describe_batch", response_model=DescribeBatchResponse)
async def describe_batch(
    batch_id: str,
    role: ProtectedRole = Depends(read_user_protected_role_dependency),
    config: Config = Depends(get_settings)
) -> DescribeBatchResponse:
    # pull out the username
    username = role.user.username

    # lookup the batch ID in batch table ID by user username
    batch_record = get_batch_record(username=username, config=config)

    if batch_record is None:
        return DescribeBatchResponse(
            status=Status(
                success=False, details=f"User {username} does not have any batch jobs."),
            job_info=None,
            missing=None,
            all_successful=False
        )

    # batch record was found - get job IDs for the given batch id
    batch_job: Optional[BatchJob] = batch_record.batch_jobs.get(batch_id)

    if batch_job is None:
        return DescribeBatchResponse(
            status=Status(
                success=False, details=f"User {username} does not have any batch jobs which match the specified batch_id {batch_id}."),
            job_info=None,
            missing=None,
            all_successful=False
        )

    job_ids = batch_job.jobs

    found: List[LodgeModelRunJob] = []
    missing: List[str] = []

    for job_id in job_ids:
        item = get_model_run_log_item(id=job_id, config=config)
        if item is None:
            missing.append(job_id)
        else:
            found.append(item)

    # a flag for UI consumers marking whether everything was good := all records
    # present and successful
    all_successful = len(missing) == 0 and all([
        job.job_status == JobStatus.SUCCEEDED for job in found
    ])

    # return successful description of jobs
    return DescribeBatchResponse(
        status=Status(
            success=True, details=f"Successfully described {len(found)} jobs. There were {len(missing)} missing jobs."),
        job_info=found,
        missing=missing,
        all_successful=all_successful
    )


@router.get("/batch_history", operation_id="batch_history", response_model=BatchHistoryResponse)
async def get_batch_history(
    role: ProtectedRole = Depends(read_user_protected_role_dependency),
    config: Config = Depends(get_settings)
) -> BatchHistoryResponse:
    # pull out the username
    username = role.user.username

    # lookup the batch ID in batch table ID by user username
    batch_record = get_batch_record(username=username, config=config)

    if batch_record is None:
        return BatchHistoryResponse(
            status=Status(
                success=False, details=f"User {username} does not have any batch jobs."),
            batch_jobs=None
        )

    # pull out list of jobs and put most recent first
    batch_list = list(batch_record.batch_jobs.values())
    sorted_batch_list = sorted(
        batch_list, key=lambda batch: batch.created_time, reverse=True)

    return BatchHistoryResponse(
        status=Status(
            success=True,
            details=f"Returned {len(sorted_batch_list)} batch jobs sorted most recent first."
        ),
        batch_jobs=sorted_batch_list
    )
