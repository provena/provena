from typing import Any, Dict, List, Optional
from ProvenaInterfaces.AsyncJobModels import *
from config import Settings
import json
import boto3  # type: ignore


def extract_sns_payloads(event: Dict[str, Any]) -> List[Dict[str, Any]]:
    """

    Pulls out the list of SNS payloads part of the lambda event

    Args:
        event (Dict[str, Any]): The event payload

    Returns:
        List[Dict[str, Any]]: The list of payloads
    """
    # Get the records out

    payloads: List[Dict[str, Any]] = []

    records: Optional[List[Dict[str, Any]]] = event.get('Records')

    if records is None:
        print("Could not find any records in the payload...")
        return payloads

    for record in records:
        print(f"Processing record {record}")

        sns_payload: Optional[Dict[str, Any]] = record.get('Sns')

        if sns_payload is None:
            print(f"No sns payload found on the record. Continuing")
            continue

        # this is JSON encoded
        message = sns_payload.get('Message')

        if message is None:
            print(f"No message found in SNS payload, skipping")
            continue

        # parse the message as json
        try:
            payloads.append(json.loads(message))
        except Exception as e:
            print(f"Failed to parse json in message... error: {e}.")
            print("Skipping.")
            continue

    return payloads


def parse_payload(payload: Dict[str, Any]) -> Optional[JobSnsPayload]:
    """

    Parses a payload into the SNS payload format.

    Returns None instead of throwing if invalid.

    Args:
        payload (Dict[str, Any]): The payload to parse

    Returns:
        Optional[JobSnsPayload]: Payload if parsed successfully
    """
    try:
        return JobSnsPayload.parse_obj(payload)
    except Exception as e:
        print(f"Failed to parse message, payload {payload}. Exception: {e}.")
        return None


def parse_payloads(payloads: List[Dict[str, Any]]) -> List[JobSnsPayload]:
    # parse all payloads
    return [x for x in map(parse_payload, payloads) if x is not None]


def py_to_dict(model: BaseModel) -> Dict[str, Any]:
    # helper to map pydantic to json dict
    return json.loads(model.json(exclude_none=True))


def setup_boto_table(settings: Settings) -> Any:
    # create boto resources
    dynamodb_resource = boto3.resource(
        "dynamodb", region_name="ap-southeast-2")
    return dynamodb_resource.Table(settings.table_name)


def write_record(entry: JobStatusTable, table: Any) -> None:
    """

    Writes an entry to the job status table

    Args:
        entry (JobStatusTable): entry
        table (Any): ddb table
    """
    payload = py_to_dict(entry)

    # Store the item in DynamoDB
    try:
        table.put_item(Item=payload)
    except Exception as e:
        print(
            f"Failed to write item to job status table! Session id: {entry.session_id}. Error: {e}.")


def convert_to_status(job: JobSnsPayload) -> JobStatusTable:
    """

    Convers the raw SNS entry into the job status table.

    Infills defaults for connector e.g. pending status.

    Args:
        job (JobSnsPayload): The input SNS payload

    Returns:
        JobStatusTable: Output job status table entry
    """
    # produce job status table object
    return JobStatusTable(
        session_id=job.session_id,
        batch_id=job.batch_id,
        username=job.username,
        job_type=job.job_type,
        job_sub_type=job.job_sub_type,
        created_timestamp=job.created_timestamp,
        status=JobStatus.PENDING,
        payload=job.payload,
        info=None
    )


def write_payloads(jobs: List[JobSnsPayload], settings: Settings) -> None:
    """

    Write a list of SNS payloads as status entries.

    Args:
        jobs (List[JobSnsPayload]): The input jobs
        settings (Settings): The settings
    """
    print("Setting up table connection")
    table = setup_boto_table(settings=settings)

    print("Writing jobs")
    for j in jobs:
        print(f"Writing record with session id = {j.session_id}")
        status = convert_to_status(j)
        write_record(entry=status, table=table)


def handler(event: Dict[str, Any], context: Any) -> None:
    """
    
    The lambda handler. 
    
    Workflow
    
    1) pull out SNS payloads
    2) parse to SNSPayload models
    3) write all entries to job status table entries

    Args:
        event (Dict[str, Any]): The lambda event (SNS topic sub of payload)
        context (Any): The lambda context, not used
    """    
    print(f"{event = }")

    try:
        settings = Settings()
    except Exception as e:
        print(f"Missing configuration values. Error: {e}.")

    # This function needs to take the SNS topic event and publish it into the job status DB

    # First - parse the SNS payload from the event
    payloads = extract_sns_payloads(event=event)

    # For each payload - parse into pydantic model
    parsed_payloads = parse_payloads(payloads)

    # For each parsed payload - lodge into the status DB
    write_payloads(jobs=parsed_payloads, settings=settings)

    print(f"Completed connector processing")

    return
