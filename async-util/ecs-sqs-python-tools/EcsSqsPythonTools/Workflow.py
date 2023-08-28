from SharedInterfaces.AsyncJobModels import *
from EcsSqsPythonTools.SqsTools import *
import json
from typing import Type, cast
from dataclasses import dataclass
from EcsSqsPythonTools.DynamoTools import update_job_status_table
from EcsSqsPythonTools.Types import CallbackResponse


def parse_sns_payload_into_body(payload: str) -> str:
    # Handles parsing SNS payload into body content
    print(
        f"Attempting to parse payload {payload} to decode the Message contents")
    return json.loads(payload)['Message']


def parse_sns_into_model(contents: str, model: Type[BaseModel]) -> BaseModel:
    # Handles parsing SNS contents into specified model
    print(f"Attempting to parse raw body {contents} into Pydantic model.")
    return model.parse_raw(contents)


def parse_sns_payload_into_model(payload: str, model: Type[BaseModel]) -> BaseModel:
    # Handles parsing sns payload into model (combines the above)
    print(f"Attempting parse of raw payload {payload} into model.")
    return parse_sns_into_model(contents=parse_sns_payload_into_body(payload), model=model)


@dataclass
class ReceivedPayload():
    # The payload
    payload: JobSnsPayload
    # Receipt handle for SQS
    receipt_handle: str


def check_for_work(job_type: JobType, queue_url: str, status_table_name: str, jobs_per_poll: int) -> List[ReceivedPayload]:
    """
    Read from queue, if item to process, returns validated payload of the
    appropriate type based on type map.

    Args:
        job_type (JobType): The job type to process queue_url (str): The SQS
        queue arn

    Returns:
        Optional[BaseModel]: The parsed model if found
    """

    # look for messages (one at time for now)
    messages: List[MessageContents] = consume_raw_messages_from_queue(
        queue_url=queue_url, max_count=jobs_per_poll)

    # collect parsed payloads
    payloads: List[ReceivedPayload] = []

    for message in messages:
        # now parse the contents
        try:
            parsed_model: JobSnsPayload = cast(JobSnsPayload, parse_sns_payload_into_model(
                payload=message.message_raw, model=JobSnsPayload))
        except Exception as e:
            print(
                f"Failed to parse a model, error: {e}. Skipping item as cannot proceed.")
            continue

        # now mark the status item as dequeued
        print(f"Updating job table to mark as dequeud")
        update_job_status_table(
            job_sns_payload=parsed_model,
            status=JobStatus.DEQUEUED,
            table_name=status_table_name,
            info="Job removed from queue ready for processing by worker task."
        )

        # This is ready to be consumed by the ECS worker - it can type cast it into
        # it's desired model to have valid typing
        payloads.append(ReceivedPayload(payload=parsed_model,
                        receipt_handle=message.receipt_handle))

    return payloads


def parse_job_specific_payload(payload: JobSnsPayload, job_sub_type: JobSubType) -> BaseModel:
    """
    Returns the job specific parsed payload - this uses the job type map to
    dispatch into a pydantic model allowing a typed interface into specific job
    types.

    Some types have further typing (e.g. PROV_LODGE has a nested payload). This
    is the responsibility of the consuming ECS worker not this shared library.

    Args:
        message (ReceivedPayload): The payload object job_type (JobType): The
        type of job to parse

    Returns:
        BaseModel: The parsed model - can be type cast in consuming worker.
    """
    desired_model = JOB_TYPE_PAYLOAD_MAP[job_sub_type]
    return desired_model.parse_obj(payload.payload)


def finish_work(queue_url: str, status_table_name: str, received_payload: ReceivedPayload, callback_response: CallbackResponse) -> None:
    """
    Closes out a job in the ECS job consumer workflow. 

    This includes
    - updating the entry in the status table according to the defined status and info
    - clearing the message from the queue using helper from SqsTools

    Args:
        queue_url (str): The URL of the queue
        status_table_name (str): The name of the dynamodb status table
        received_payload (ReceivedPayload): The payload received initially - see helper above
        status (JobStatus): The status - i.e. did it succeed or fail?
        info (Optional[str], optional): If error -> provide info. Defaults to None.

    Returns: None
    """

    # Start by updating the job status table
    print("Updating job status table")
    update_job_status_table(job_sns_payload=received_payload.payload,
                            status=callback_response.status, table_name=status_table_name, info=callback_response.info, result=callback_response.result)

    # Now clear out the message
    print(
        f"Deleting message from queue using receipt handle {received_payload.receipt_handle}.")
    delete_message_from_queue(
        queue_url=queue_url, receipt_handle=received_payload.receipt_handle)
