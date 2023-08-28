from SharedInterfaces.AsyncJobAPI import *
import helpers.dynamo as dynamo
from typing import Tuple, Optional
from SharedInterfaces.AsyncJobAPI import PaginationKey


def get_job_by_session_id(session_id: str, table_name: str) -> Optional[JobStatusTable]:
    """
    
    Given a session id and table name, gets the job status table entry if present.

    Args:
        session_id (str): The session ID partition key
        table_name (str): The table name to hit

    Returns:
        Optional[JobStatusTable]: Item if present
    """    
    item = dynamo.get_job_by_session_id(
        session_id=session_id, table_name=table_name)
    return item


def list_jobs_by_username(username: str, table_name: str,  username_index: str, pagination_key: Optional[PaginationKey], limit: int) -> dynamo.PaginatedStatusList:
    """
    
    Lists jobs by username.
    
    Uses the username <- timestamp secondary index
    
    Respects the pagination key if provided and returns a paginated response.

    Args:
        username (str): The username
        table_name (str): The table name
        username_index (str): The index name
        pagination_key (Optional[PaginationKey]): Pag key
        limit (int): page size

    Returns:
        dynamo.PaginatedStatusList: pag key if present and list of items
    """    
    return dynamo.list_jobs_by_username(
        username=username,
        table_name=table_name,
        username_index=username_index,
        pagination_key=pagination_key,
        limit=limit
    )

def list_batch_by_batch_id(batch_id: str, table_name: str,  batch_id_index: str, pagination_key: Optional[PaginationKey], limit: int) -> dynamo.PaginatedStatusList:
    """
    
    Lists entries by batch id.
    
    Uses the batch id <- timestamp secondary index
    
    Respects pag key for pagination

    Args:
        batch_id (str): The batch ID
        table_name (str): table name
        batch_id_index (str): index name
        pagination_key (Optional[PaginationKey]): Pag key if present
        limit (int): page size

    Returns:
        dynamo.PaginatedStatusList: The pag key and items
    """    
    return dynamo.get_items_by_batch_id(
        batch_id=batch_id,
        table_name=table_name,
        pagination_key=pagination_key,
        batch_id_index_name=batch_id_index,
        limit=limit
    )
