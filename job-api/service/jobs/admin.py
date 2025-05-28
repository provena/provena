import uuid
import helpers.dynamo as dynamo
import helpers.sns as sns
from ProvenaInterfaces.AsyncJobAPI import *
from helpers.time import get_timestamp
from config import Config
from dataclasses import dataclass

import logging

# setup logger
logging.config.fileConfig('logging.conf', disable_existing_loggers=False)

# get logger for this module
logger_key = "adminService"
logger = logging.getLogger(logger_key)


def get_correct_topic_arn(job_type: JobType, config: Config) -> str:
    """

    Looks up in the config object the correct topic ARN for a given job type.

    This will need to be updated if/when we add additional job types.

    Args:
        job_type (JobType): The job type to fetch 
        config (Config): Config

    Raises:
        Exception: If the job type isn't defined in the config

    Returns:
        str: The SNS topic arn
    """
    if job_type == JobType.PROV_LODGE:
        return config.prov_lodge_topic_arn
    elif job_type == JobType.REGISTRY:
        return config.registry_topic_arn
    elif job_type == JobType.EMAIL:
        return config.email_topic_arn
    elif job_type == JobType.REPORT:
        return config.report_topic_arn

    err = f"Cannot handle job type: {job_type}"
    logging.error(err)
    raise Exception(err)


def generate_unique_batch_id(table_name: str, batch_id_index_name: str) -> str:
    """

    Generates a unique batch ID with a UUID-4.

    Checks the item is not present in table.

    Args:
        table_name (str): The table name to check
        batch_id_index_name (str): Batch ID index

    Raises:
        Exception: Lookup failure
        Exception: Count failure

    Returns:
        str: The unique batch ID
    """
    unique = False
    limit = 10
    count = 0
    logging.info("Starting unique batch id check")

    while not unique and count < limit:
        logging.info(f"{count = }, {limit = }")
        count = count + 1
        id = str(uuid.uuid4())
        logging.info(f"Generated id {id}")

        # very very low chance this is used already - test it to be sure
        try:
            logging.info("Fetching from DB")
            items, _ = dynamo.get_items_by_batch_id(
                batch_id=id,
                table_name=table_name,
                batch_id_index_name=batch_id_index_name,
                pagination_key=None,
                # Only need a single item if present to verify uniqueness
                limit=1
            )
        except Exception as e:
            raise Exception(f"Failed lookup to validate unique id: {e}.")

        if len(items) == 0:
            logging.info(f"Batch ID does not exist - unique id {id}.")
            unique = True

    if count >= limit and not unique:
        raise Exception(f"Failed to generate unique ID. Tried {limit} times.")

    return id


def generate_unique_session_id(table_name: str) -> str:
    """

    Generates a unique session ID with a UUID-4.

    Checks the item is not present in table.

    Args:
        table_name (str): The table name to check

    Raises:
        Exception: Lookup failure
        Exception: Count failure

    Returns:
        str: The unique session ID
    """
    unique = False
    limit = 10
    count = 0
    logging.info("Starting unique session id check")

    while not unique and count < limit:
        logging.info(f"{count = }, {limit = }")
        count = count + 1
        id = str(uuid.uuid4())
        logging.info(f"Generated id {id}")

        # very very low chance this is used already - test it to be sure
        try:
            logging.info("Fetching from DB")
            item = dynamo.get_job_by_session_id(
                session_id=id, table_name=table_name)
        except Exception as e:
            raise Exception(f"Failed lookup to validate unique id: {e}.")

        if item is None:
            logging.info(f"Item does not exist - unique id {id}.")
            unique = True

    if count >= limit and not unique:
        raise Exception(f"Failed to generate unique ID. Tried {limit} times.")

    return id


def validate_payload(job_sub_type: JobSubType, job_specific_payload: Dict[str, Any]) -> None:
    """

    Looks up the correct payload model by job sub type

    Validates the payload against that pydantic model

    Args:
        job_sub_type (JobSubType): The job sub type to validate
        job_specific_payload (Dict[str, Any]): The payload

    Raises:
        Exception: Validation exception
    """
    logger.info("Validating payload")
    try:
        desired_model = JOB_TYPE_PAYLOAD_MAP[job_sub_type]
        desired_model.parse_obj(job_specific_payload)
    except Exception as e:
        err = f"Failed to parse the payload as specified job type. Err: {e}"
        logging.error(err)
        raise Exception(err)


@dataclass
class LaunchJobServiceResponse():
    session_id: str
    batch_id: Optional[str]


def launch_job(
    username: str,
    job_type: JobType,
    job_sub_type: JobSubType,
    job_specific_payload: Dict[str, Any],
    table_name: str,
    sns_topic_arn: str,
    request_batch_id: bool,
    batch_id: Optional[str],
    batch_id_index_name: str
) -> LaunchJobServiceResponse:
    """

    Combines the above logic to launch a job.

    1) generate session id
    2) generate batch id if needed
    3) publish to SNS topic

    Args:
        username (str): The username for entry
        job_type (JobType): job type
        job_sub_type (JobSubType): sub type
        job_specific_payload (Dict[str, Any]): payload
        table_name (str): table name
        sns_topic_arn (str): The SNS topic to publish to
        request_batch_id (bool): Do we want a batch ID?
        batch_id (Optional[str]): Current batch ID
        batch_id_index_name (str): Index for batches

    Raises:
        ValueError: Inappropriate reques combination

    Returns:
        LaunchJobServiceResponse: The dataclass representing returned values
    """
    # get a unique session ID
    logger.info("Generating unique session ID")
    id = generate_unique_session_id(table_name=table_name)

    desired_batch_id = batch_id

    if request_batch_id and (batch_id is not None):
        raise ValueError("Cannot both request a batch and add to a batch.")

    if request_batch_id:
        desired_batch_id = generate_unique_batch_id(
            table_name=table_name, batch_id_index_name=batch_id_index_name)

    logger.info("Building payload")

    # Using either provided batch ID or generated if requested
    payload = JobSnsPayload(
        session_id=id,
        username=username,
        job_type=job_type,
        job_sub_type=job_sub_type,
        created_timestamp=get_timestamp(),
        payload=job_specific_payload,
        batch_id=desired_batch_id
    )

    logger.info("Submitting to SNS topic")
    sns.publish_model_to_sns(
        model=payload,
        topic_arn=sns_topic_arn
    )

    logger.info("Published successfully. Returning session id.")

    return LaunchJobServiceResponse(
        session_id=id,
        batch_id=desired_batch_id
    )


def list_jobs(username: Optional[str], table_name: str,  username_index: str, pagination_key: Optional[PaginationKey], limit: int, global_index_name: str) -> dynamo.PaginatedStatusList:
    """

    list jobs for admin

    paginated

    optionally queries by username (which uses username index)

    otherwise scans

    Args:
        username (Optional[str]): The optional username index filter
        table_name (str): table name
        username_index (str): username index name
        pagination_key (Optional[PaginationKey]): pag key for pagination
        limit (int): page size

    Returns:
        dynamo.PaginatedStatusList: paginated response
    """
    if username is not None:
        return dynamo.list_jobs_by_username(
            username=username,
            table_name=table_name,
            username_index=username_index,
            pagination_key=pagination_key,
            limit=limit
        )
    else:
        return dynamo.list_all_jobs(
            table_name=table_name,
            pagination_key=pagination_key,
            global_index_name=global_index_name,
            limit=limit
        )
