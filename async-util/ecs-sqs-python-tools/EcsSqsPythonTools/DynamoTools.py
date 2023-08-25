import boto3  # type: ignore
from pydantic import BaseModel
from typing import Dict, Optional
from SharedInterfaces.AsyncJobModels import *
import json


def py_to_dict(model: BaseModel) -> Dict[str, Any]:
    # converts a model to safe json dict
    return json.loads(model.json(exclude_none=True))


def setup_boto_table(table_name: str) -> Any:
    # create boto resources
    dynamodb_resource = boto3.resource(
        "dynamodb", region_name="ap-southeast-2")
    return dynamodb_resource.Table(table_name)


def write_record(entry: JobStatusTable, table: Any) -> None:
    # Writes job status table entry
    payload = py_to_dict(entry)

    # Store the item in DynamoDB
    print(f"Writing record {entry} to job status table.")
    try:
        table.put_item(Item=payload)
    except Exception as e:
        print(
            f"Failed to write item to job status table! Session id: {entry.session_id}. Error: {e}.")


def convert_to_status(job: JobSnsPayload, status: JobStatus, info: Optional[str], result: Optional[Dict[str, Any]]) -> JobStatusTable:
    # Converts an SNS payload to status table entry
    return JobStatusTable(
        session_id=job.session_id,
        batch_id=job.batch_id,
        username=job.username,
        job_type=job.job_type,
        job_sub_type=job.job_sub_type,
        created_timestamp=job.created_timestamp,
        status=status,
        payload=job.payload,
        info=info,
        result=result
    )


def update_job_status_table(job_sns_payload: JobSnsPayload, status: JobStatus, table_name: str, info: Optional[str] = None, result: Optional[Dict[str, Any]] = None) -> None:
    # Updates an existing job status table entry based on the callback response.
    status_payload = convert_to_status(
        job=job_sns_payload, status=status, info=info, result=result)
    table = setup_boto_table(table_name=table_name)
    write_record(entry=status_payload, table=table)
