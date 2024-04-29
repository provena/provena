from ProvenaInterfaces.AsyncJobAPI import *
from ProvenaInterfaces.AsyncJobModels import GSI_FIELD_NAME, GSI_VALUE
import boto3  # type: ignore
from typing import List, Dict, Any, Optional, Tuple
from boto3.dynamodb.conditions import Key  # type: ignore
import logging

# setup logger
logging.config.fileConfig('logging.conf', disable_existing_loggers=False)

# get logger for this module
logger_key = "helpers"
logger = logging.getLogger(logger_key)


def setup_status_table(table_name: str) -> Any:
    # create boto resources
    dynamodb_resource = boto3.resource("dynamodb")
    return dynamodb_resource.Table(table_name)


PaginatedStatusList = Tuple[List[JobStatusTable], Optional[PaginationKey]]


def read_batch_from_table(batch_id: str, table: Any, batch_id_index_name: str, limit: int, pagination_key: Optional[PaginationKey]) -> PaginatedStatusList:
    cond_expression = Key('batch_id').eq(batch_id)
    request = {
        "IndexName": batch_id_index_name,
        "Select": "ALL_ATTRIBUTES",
        "KeyConditionExpression": cond_expression,
        # sort key = timestamp -> false = reverse = descending
        "ScanIndexForward": False,
        "Limit": limit
    }
    if pagination_key is not None:
        request["ExclusiveStartKey"] = pagination_key

    try:
        response = table.query(**request)
    except Exception as e:
        err = f"Failed to query from the job status table, err: {e}."
        logging.error(err)
        raise Exception(err)

    result_items: List[JobStatusTable] = []
    items = response.get('Items')
    pagination_key = response.get('LastEvaluatedKey')

    for item in items:
        try:
            entry = JobStatusTable.parse_obj(item)
            result_items.append(entry)
        except Exception as e:
            err = f"Failed to parse item from status table, err: {e}. Continuing through list."
            logging.error(err)

    return result_items, pagination_key


def read_status_from_table(session_id: str, table: Any) -> Optional[JobStatusTable]:
    request = {
        'Key': {"session_id": session_id}
    }

    try:
        response = table.get_item(**request)
    except Exception as e:
        raise Exception(f"Failed to read from the job status table, err: {e}.")

    item = response.get('Item')

    if item is None:
        return None

    try:
        return JobStatusTable.parse_obj(item)
    except Exception as e:
        raise Exception(f"Failed to parse item from status table, err: {e}.")


def query_jobs_by_username(username: str, username_index: str, pagination_key: Optional[PaginationKey], table: Any, limit: int) -> PaginatedStatusList:
    cond_expression = Key('username').eq(username)
    request = {
        "IndexName": username_index,
        "Select": "ALL_ATTRIBUTES",
        "KeyConditionExpression": cond_expression,
        # sort key = timestamp -> false = reverse = descending
        "ScanIndexForward": False,
        "Limit": limit
    }
    if pagination_key is not None:
        request["ExclusiveStartKey"] = pagination_key

    try:
        response = table.query(**request)
    except Exception as e:
        err = f"Failed to query from the job status table, err: {e}."
        logging.error(err)
        raise Exception(err)

    result_items: List[JobStatusTable] = []
    items = response.get('Items')
    pagination_key = response.get('LastEvaluatedKey')

    for item in items:
        try:
            entry = JobStatusTable.parse_obj(item)
            result_items.append(entry)
        except Exception as e:
            err = f"Failed to parse item from status table, err: {e}. Continuing through list."
            logging.error(err)

    return result_items, pagination_key


def global_query_all_jobs(pagination_key: Optional[PaginationKey], global_index_name: str, table: Any, limit: int) -> PaginatedStatusList:
    cond_expression = Key(GSI_FIELD_NAME).eq(GSI_VALUE)
    request = {
        "IndexName": global_index_name,
        "Select": "ALL_ATTRIBUTES",
        "KeyConditionExpression": cond_expression,
        # sort key = timestamp -> false = reverse = descending
        "ScanIndexForward": False,
        "Limit": limit
    }
    if pagination_key is not None:
        request["ExclusiveStartKey"] = pagination_key

    try:
        response = table.query(**request)
    except Exception as e:
        err = f"Failed to query from the job status table, err: {e}."
        logging.error(err)
        raise Exception(err)

    result_items: List[JobStatusTable] = []
    items = response.get('Items')
    pagination_key = response.get('LastEvaluatedKey')

    for item in items:
        try:
            entry = JobStatusTable.parse_obj(item)
            result_items.append(entry)
        except Exception as e:
            err = f"Failed to parse item from status table, err: {e}. Continuing through list."
            logging.error(err)

    return result_items, pagination_key


def scan_all_jobs(pagination_key: Optional[PaginationKey], table: Any, limit: int) -> PaginatedStatusList:
    request: Dict[str, Any] = {
        'Limit': limit
    }
    if pagination_key is not None:
        request["ExclusiveStartKey"] = pagination_key

    try:
        response = table.scan(**request)
    except Exception as e:
        err = f"Failed to scan from the job status table, err: {e}."
        logging.error(err)
        raise Exception(err)

    result_items: List[JobStatusTable] = []
    items = response.get('Items')
    pagination_key = response.get('LastEvaluatedKey')

    for item in items:
        try:
            entry = JobStatusTable.parse_obj(item)
            result_items.append(entry)
        except Exception as e:
            err = f"Failed to parse item from status table, err: {e}. Continuing through list."
            logging.error(err)

    return result_items, pagination_key


def get_items_by_batch_id(batch_id: str, table_name: str, batch_id_index_name: str, pagination_key: Optional[PaginationKey], limit: int) -> PaginatedStatusList:
    logging.info("Fetching jobs by batch ID")
    logging.debug("Setting up DDB table client")
    table = setup_status_table(table_name=table_name)
    logging.debug("Using client to read from table")
    return read_batch_from_table(batch_id=batch_id,  table=table, batch_id_index_name=batch_id_index_name, pagination_key=pagination_key, limit=limit)


def get_job_by_session_id(session_id: str, table_name: str) -> Optional[JobStatusTable]:
    logging.info("Fetching job by ID")

    logging.debug("Setting up DDB table client")
    table = setup_status_table(table_name=table_name)
    logging.debug("Using client to read from table")
    return read_status_from_table(session_id=session_id,  table=table)


def list_jobs_by_username(username: str, table_name: str, username_index: str, pagination_key: Optional[PaginationKey], limit: int) -> PaginatedStatusList:
    logging.info("Listing jobs by Username")
    table = setup_status_table(table_name=table_name)
    logging.debug("Using client to query from table")
    return query_jobs_by_username(username=username, username_index=username_index, pagination_key=pagination_key, table=table, limit=limit)


def list_all_jobs(table_name: str, pagination_key: Optional[PaginationKey], limit: int, global_index_name: str) -> PaginatedStatusList:
    logging.info(
        f"Querying all jobs in table. Using index {global_index_name}. Key {GSI_FIELD_NAME} value {GSI_VALUE}.")
    table = setup_status_table(table_name=table_name)
    logging.debug("Using client to scan from table")

    # this would scan without ordering - instead use global index
    # return scan_all_jobs(pagination_key=pagination_key, table=table, limit=limit)

    # Instead do a global query using fixed gsi field name/single shard
    return global_query_all_jobs(
        pagination_key=pagination_key,
        limit=limit,
        global_index_name=global_index_name,
        table=table,
    )
