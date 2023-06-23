import boto3  # type: ignore
import json
from typing import Dict, Any, Optional
from datetime import datetime
from config import config
from SharedInterfaces.JobModels import *
from dataclasses import dataclass
from SharedInterfaces.ProvenanceAPI import RegisterModelRunResponse
import logging
from helpers.service_account_helpers import *

# setup logger
log = logging.getLogger()
log.setLevel(logging.DEBUG)

# setup secret cache
secret_cache = setup_secret_cache()


def get_job_log(job_id: str) -> Optional[JobLogBase]:
    table = boto3.resource('dynamodb').Table(config.JOB_TABLE_NAME)
    item = table.get_item(
        Key={'id': job_id}
    )
    if 'Item' in item.keys():
        job_log = item['Item']
        try:
            parsed_log = JobLogBase.parse_obj(job_log)
            return parsed_log
        except Exception as e:
            log.warning(
                "A job existed with specified ID but it was not parsable as the current model.")
            return None
    else:
        return None


def write_job(job_log: JobLogBase) -> None:
    table = boto3.resource('dynamodb').Table(config.JOB_TABLE_NAME)
    log.info("Writing job to job log")
    table.put_item(
        Item=json.loads(job_log.json(exclude_none=True))
    )


def pull_event_payload(event: Dict[str, Any]) -> Dict[str, Any]:
    try:
        return json.loads(json.loads(event['Records'][0]['body'])['Message'])
    except Exception as e:
        raise Exception(
            f"Failed to parse the provided event body, error: {e}.")


def generate_auth_header(token: str) -> Dict[str, str]:
    return {
        'Authorization': 'Bearer ' + token
    }


def access_check(token: str) -> None:
    # embed token into request
    headers = generate_auth_header(token)
    # check access
    endpoint = config.PROV_API_ENDPOINT + "/check-access/check-write-access"
    response = requests.get(endpoint, headers=headers)
    assert response.status_code == 200, f"Status code was {response.status_code} on write access check"


def touch_with_status(job_log: JobLogBase, status: JobStatus) -> None:
    job_log.job_status = status
    job_log.updated_time = int(datetime.now().timestamp())
    write_job(job_log)


@dataclass
class LodgeStatus():
    status: bool
    message: Optional[str] = None
    record_id: Optional[str] = None


def lodge_model_run_record(username: str, token: str, model_run_record: ModelRunRecord) -> LodgeStatus:
    log.info(f"Lodging model run record for user {username}!")

    # make request
    endpoint = config.PROV_API_ENDPOINT + "/model_run/proxy/register_complete"
    # include the user proxy username - this is passed through so that the user owns the record
    params = {
        'username': username
    }
    json_payload = json.loads(model_run_record.json(exclude_none=True))
    headers = generate_auth_header(token)
    response = requests.post(
        url=endpoint,
        params=params,
        json=json_payload,
        headers=headers
    )

    log.info("Received response, parsing")

    # check the status code
    if response.status_code != 200:
        status = response.status_code
        details = "Unknown"
        try:
            details = response.json()['detail']
        except:
            None
        return LodgeStatus(
            status=False,
            message=f"Model run record lodge failed, status {status}, details {details}."
        )

    # parse the model response
    try:
        reg_response = RegisterModelRunResponse.parse_obj(response.json())
    except Exception as e:
        return LodgeStatus(
            status=False,
            message=f"Model run lodge response was 200 OK but the response was unparsable."
        )

    # check the status
    if not reg_response.status.success:
        return LodgeStatus(
            status=False,
            message=f"Model run lodge failed, reason: {reg_response.status.details}."
        )

    # all is well!
    record_info = reg_response.record_info
    assert record_info

    return LodgeStatus(
        status=True,
        record_id=record_info.id
    )


def handle_job(payload: Dict[str, Any]) -> None:
    log.info(f"Event payload: {payload}")

    # parse the payload as a job request base
    try:
        job_request_base = JobRequestBase.parse_obj(payload)
    except Exception as e:
        log.error(
            "Could not parse the job as a valid JobRequestBase model. Aborting...")
        log.error(e)
        raise e

    # check that the job type can be handled
    job_type = job_request_base.job_type
    if job_type != JobType.LODGE_MODEL_RUN_RECORD:
        raise Exception(f"Unknown job request type: {job_type}.")

    # parse as a lodge model run job request
    try:
        model_run_lodge_request = LodgeModelRunJobRequest.parse_obj(payload)
    except Exception as e:
        log.error(
            "Could not parse the job as a valid LodgeModelRunJobRequest model. Aborting...")
        log.error(e)
        raise e

    # check that the job isn't already in existence
    log.info("Checking job with ID doesn't exist")
    existing_job = get_job_log(model_run_lodge_request.id)

    # the job is already being processed or has failed
    # TODO make this more sophisticated
    if existing_job is not None:
        log.warning(
            f"The job with id {existing_job.id} already exists in the job database with status {existing_job.job_status} - returning - no action taken.")
        return

    # Create a new job log with pending status
    current_time = int(datetime.now().timestamp())

    # expires after set time
    job_log = LodgeModelRunJob(
        id=model_run_lodge_request.id,
        job_status=JobStatus.PENDING,
        created_time=current_time,
        updated_time=current_time,
        model_run_record=model_run_lodge_request.model_run_record,
        username=model_run_lodge_request.username
    )

    # write the pending job
    write_job(job_log)

    # now check that the prov API is healthy

    # get a service token
    try:
        token = get_service_token(secret_cache)
    except Exception as e:
        raise Exception(f"Failed to retrieve service token, error: {e}")

    # health check
    try:
        access_check(token)
    except Exception as e:
        log.error(f"Failed write access check, error {e}")
        raise e

    # mark as in progress
    touch_with_status(
        job_log=job_log,
        status=JobStatus.IN_PROGRESS
    )

    # try lodging the model run record
    status: LodgeStatus = lodge_model_run_record(
        username=model_run_lodge_request.username,
        token=token,
        model_run_record=model_run_lodge_request.model_run_record
    )

    # interpret the status
    if status.status:
        # success
        assert status.record_id
        job_log.model_run_record_id = status.record_id
        touch_with_status(
            job_log,
            JobStatus.SUCCEEDED
        )
    else:
        job_log.error_info = status.message
        touch_with_status(
            job_log,
            JobStatus.FAILED
        )

    return


def handler(event: Dict[str, Any], context: Any) -> None:
    # need to

    # a) parse the model run record and job id from the SNS topic event
    # b) lodge the record into the job table as pending
    # c) do a health check on the prov API to make sure we are happy
    # d) mark as started
    # e) make API request
    # f) await the result
    # g) report results to table

    # display table name
    log.info(f"Table name {config.JOB_TABLE_NAME}")

    # display received event
    log.info(f"Event: {event}")

    # pull out the event payload
    payload = pull_event_payload(event=event)

    # handle the job
    handle_job(payload)
