from config import Config
from SharedInterfaces.JobModels import *
import boto3  # type: ignore
from typing import Any
from fastapi import HTTPException
import json
from datetime import datetime


def get_topic(config: Config) -> Any:
    return boto3.resource('sns').Topic(config.PROV_JOB_TOPIC_ARN)


def get_log_table(config: Config) -> Any:
    return boto3.resource('dynamodb').Table(config.PROV_JOB_TABLE_NAME)


def get_batch_table(config: Config) -> Any:
    return boto3.resource('dynamodb').Table(config.BATCH_TABLE_NAME)


def publish(topic: Any, payload: Dict[str, Any]) -> Any:
    topic.publish(
        Message=json.dumps(payload, indent=2)
    )


def get_log_item_raw(id: str, config: Config) -> Optional[Dict[str, Any]]:
    table = get_log_table(config)
    response: Dict[str, Any] = table.get_item(
        Key={
            'id': id
        }
    )
    if 'Item' in response:
        return response['Item']
    else:
        return None


def get_model_run_log_item(id: str, config: Config) -> Optional[LodgeModelRunJob]:
    item = get_log_item_raw(id=id, config=config)

    if item is None:
        return None

    try:
        return LodgeModelRunJob.parse_obj(item)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to parse job log record as LodgeModelRunJob... error: {e}"
        )


def publish_job_request(job_request: LodgeModelRunJobRequest, config: Config) -> None:
    topic = get_topic(config)
    publish(topic=topic, payload=json.loads(
        job_request.json(exclude_none=True)))


def get_batch_record(username: str, config: Config) -> Optional[BatchRecord]:
    # get the batch table
    table = get_batch_table(config)

    response: Dict[str, Any] = table.get_item(
        Key={
            'username': username
        }
    )
    if 'Item' in response:
        item: Dict[str, Any] = response['Item']
        try:
            parsed = BatchRecord.parse_obj(item)
            return parsed
        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Failed to parse existing batch job record in batch table. Exception: {e}.")
    else:
        return None


def put_batch_record(record: BatchRecord, config: Config) -> None:
    # get the batch table
    table = get_batch_table(config)

    # create a safe parse
    safe = json.loads(record.json(exclude_none=True))

    try:
        table.put_item(
            Item=safe
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to write batch record for user {record.username} to dynamoDB Batch table with error: {e}."
        )


def add_user_batch_job(username: str, batch_id: str, jobs: List[str], config: Config) -> None:
    # get the existing record if any
    record = get_batch_record(username=username, config=config)

    # if no record, then create empty record
    if record is None:
        record = BatchRecord(
            username=username,
            batch_jobs={}
        )
    # typing hint
    assert record is not None

    # check the batch ID isn't in there
    batch_jobs = record.batch_jobs
    if batch_id in batch_jobs:
        raise HTTPException(
            status_code=500,
            detail=f"Trying to add batch job with non unique batch ID!"
        )

    # add the new batch id
    batch_jobs[batch_id] = BatchJob(
        batch_id=batch_id,
        created_time=int(datetime.now().timestamp()),
        jobs=jobs
    )

    # write the updated record
    put_batch_record(
        record=record,
        config=config
    )
