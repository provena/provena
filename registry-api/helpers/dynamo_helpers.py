from dataclasses import dataclass
from ProvenaInterfaces.RegistryAPI import *
from ProvenaInterfaces.RegistryModels import *
from fastapi import HTTPException
import boto3  # type: ignore
from config import Config
from boto3.dynamodb.conditions import Attr, And, Key  # type: ignore
import json


def get_table_from_name(table_name: str) -> Any:
    """    get_table_from_name
        Generates a dynamodb resource table to be 
        used in the below methods. Uses the registry 
        table name environment variable for target
        table.

        Returns
        -------
         : DynamoDB table resource
            The botocore resource for the table

        See Also (optional)
        --------

        Examples (optional)
        --------
    """
    ddb_resource = boto3.resource('dynamodb')
    table = ddb_resource.Table(table_name)
    return table


def get_auth_table(config: Config) -> Any:
    """    get_auth_table
        Generates a dynamodb resource table to be 
        used in the below methods. Uses the auth 
        table name environment variable for target
        table.

        Returns
        -------
         : DynamoDB table resource
            The botocore resource for the table

        See Also (optional)
        --------

        Examples (optional)
        --------
    """
    return get_table_from_name(table_name=config.auth_table_name)


def get_lock_table(config: Config) -> Any:
    """    get_lock_table
        Generates a dynamodb resource table to be 
        used in the below methods. Uses the lock 
        table name environment variable for target
        table.

        Returns
        -------
         : DynamoDB table resource
            The botocore resource for the table

        See Also (optional)
        --------

        Examples (optional)
        --------
    """
    return get_table_from_name(table_name=config.lock_table_name)


def get_registry_table(config: Config) -> Any:
    """    get_table
        Generates a dynamodb resource table to be 
        used in the below methods. Uses the registry 
        table name environment variable for target
        table.

        Returns
        -------
         : DynamoDB table resource
            The botocore resource for the table

        See Also (optional)
        --------

        Examples (optional)
        --------
    """
    return get_table_from_name(table_name=config.registry_table_name)


def delete_dynamo_db_entry(id: str, table: Any) -> None:
    """    delete_dynamo_db_entry
        Deletes the entry with specified handle from table.

        Arguments
        ----------
        handle : str
            The handle to delete
        table : Any
            Dynamodb table object

        Raises
        ------
        Exception
            If something fails in boto operation

        See Also (optional)
        --------

        Examples (optional)
        --------
    """
    try:
        table.delete_item(Key={'id': id})
    except Exception as e:
        raise Exception(f"Failed to delete entry from table. Error: {e}")


def write_auth_table_entry(auth_entry: AuthTableEntry, config: Config) -> None:
    # serialise to remove unsupported datetime objects and similar
    safe = json.loads(auth_entry.json(exclude_none=True))

    # get the table
    table = get_auth_table(config=config)
    try:
        table.put_item(Item=safe)
    except Exception as e:
        raise Exception(
            f"Failed to write auth table entry to auth table. Error: {e}")


def write_lock_table_entry(lock_entry: LockTableEntry, config: Config) -> None:
    # serialise to remove unsupported datetime objects and similar
    safe = json.loads(lock_entry.json(exclude_none=True))

    # get the table
    table = get_lock_table(config=config)
    try:
        table.put_item(Item=safe)
    except Exception as e:
        raise Exception(
            f"Failed to write lock table entry to lock table. Error: {e}")

# def batch_write_items(items: List[Dict[str, Any]], table: Any) -> None:
#    """    write_dynamo_db_entry_raw
#        Given the unparsed entry and the dynamo db table will write
#        the entry to the table.
#
#        Arguments
#        ----------
#        registry_item : Dict[str, Any]
#            The registry item to write - this method is unprotected in that a validation
#            failure may occur if the item is not dynamoDB compatible
#        table : Any
#            The boto3 dynamodb table resource
#
#        Raises
#        ------
#        Exception
#            Something goes wrong during writing
#
#        See Also (optional)
#        --------
#
#        Examples (optional)
#        --------
#    """
#    table = get_registry_table(config)
#
#    # Add trivial key to facilitate sorted response of all items
#    # from table.query()
#    registry_item["universal_partition_key"] = "OK"
#    write_dynamo_db_entry_raw(
#        registry_item=registry_item, table=table
#    )


def write_registry_dynamo_db_entry_raw(registry_item: Dict[str, Any], config: Config) -> None:
    """    write_dynamo_db_entry_raw
        Given the unparsed entry and the dynamo db table will write 
        the entry to the table. 

        Arguments
        ----------
        registry_item : Dict[str, Any]
            The registry item to write - this method is unprotected in that a validation 
            failure may occur if the item is not dynamoDB compatible
        table : Any
            The boto3 dynamodb table resource

        Raises
        ------
        Exception
            Something goes wrong during writing

        See Also (optional)
        --------

        Examples (optional)
        --------
    """
    table = get_registry_table(config)

    # Add trivial key to facilitate sorted response of all items
    # from table.query()
    registry_item["universal_partition_key"] = "OK"
    write_dynamo_db_entry_raw(
        registry_item=registry_item, table=table
    )


def write_dynamo_db_entry_raw(registry_item: Dict[str, Any], table: Any) -> None:
    """    write_dynamo_db_entry_raw
        Given the unparsed entry and the dynamo db table will write 
        the entry to the table. 

        Arguments
        ----------
        registry_item : Dict[str, Any]
            The registry item to write - this method is unprotected in that a validation 
            failure may occur if the item is not dynamoDB compatible
        table : Any
            The boto3 dynamodb table resource

        Raises
        ------
        Exception
            Something goes wrong during writing

        See Also (optional)
        --------

        Examples (optional)
        --------
    """
    # serialise to remove unsupported datetime objects and similar
    try:
        table.put_item(Item=registry_item)
    except Exception as e:
        raise Exception(f"Failed to write raw entry to table. Error: {e}")


def batch_write_bundled_item(items: List[BundledItem], config: Config) -> None:
    # resources
    resource_table = get_registry_table(config=config)
    resource_table_items = [i.item_payload for i in items]

    # apply universal partition key before writing
    for registry_item in resource_table_items:
        registry_item["universal_partition_key"] = "OK"

    # write entity resource metadata
    batch_write_table(items=resource_table_items, table=resource_table)

    # locks
    lock_table = get_lock_table(config=config)
    lock_table_items = [i.lock_payload for i in items]
    batch_write_table(items=lock_table_items, table=lock_table)
    # auth
    auth_table = get_auth_table(config=config)
    auth_table_items = [i.auth_payload for i in items]
    batch_write_table(items=auth_table_items, table=auth_table)


def batch_delete_bundled_item(ids: List[str], config: Config) -> None:
    # resources
    resource_table = get_registry_table(config=config)
    batch_delete_table(ids=ids, table=resource_table)
    # locks
    lock_table = get_lock_table(config=config)
    batch_delete_table(ids=ids, table=lock_table)
    # auth
    auth_table = get_auth_table(config=config)
    batch_delete_table(ids=ids, table=auth_table)


def batch_delete_table(ids: List[str], table: Any) -> None:
    try:
        with table.batch_writer() as batch:
            for id in ids:
                batch.delete_item(Key={'id': id})
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed batch delete operation, exception: {e}.")


def batch_write_table(items: List[Dict[str, Any]], table: Any) -> None:
    try:
        with table.batch_writer() as batch:
            for item in items:
                batch.put_item(Item=item)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed batch write operation, exception: {e}.")


def write_bundled_item(bundled_item: BundledItem, config: Config) -> None:
    """
    write_bundled_item 

    For use in the admin tooling for importing - takes a bundled items and writes the items to each table. 

    Throws error with customised error message for each table. 

    Parameters
    ----------
    bundled_item : BundledItem
        The bundle to write

    Raises
    ------
    HTTPException (500)
        If any write error occurs
    """
    # item payload
    try:
        write_registry_dynamo_db_entry_raw(
            registry_item=bundled_item.item_payload, config=config)
    except HTTPException as he:
        raise HTTPException(
            status_code=he.status_code,
            detail=f"Failed to write item payload of bundled item. Error: {he.detail}."
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Unhandled failure to write item payload of bundled item. Error: {e}."
        )
    # auth payload
    try:
        write_dynamo_db_entry_raw(
            registry_item=bundled_item.auth_payload, table=get_auth_table(config))
    except HTTPException as he:
        raise HTTPException(
            status_code=he.status_code,
            detail=f"Failed to write auth payload of bundled item. Error: {he.detail}."
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Unhandled failure to write auth payload of bundled item. Error: {e}."
        )
    # lock
    try:
        write_dynamo_db_entry_raw(
            registry_item=bundled_item.lock_payload, table=get_lock_table(config))
    except HTTPException as he:
        raise HTTPException(
            status_code=he.status_code,
            detail=f"Failed to write lock payload of bundled item. Error: {he.detail}."
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Unhandled failure to write lock payload of bundled item. Error: {e}."
        )


def delete_bundled_item(id: str, config: Config) -> None:
    """
    delete_bundled_item 

    For use in the admin tooling for importing - takes a bundled items and deletes the items from each table. 

    Throws error with customised error message for each table. 

    Parameters
    ----------
    id: str
        The id of the bundle to clear

    Raises
    ------
    HTTPException (500)
        If any error occurs
    """
    # item payload
    try:
        delete_dynamo_db_entry(id=id, table=get_registry_table(config))
    except HTTPException as he:
        raise HTTPException(
            status_code=he.status_code,
            detail=f"Failed to delete item part of bundled item. Error: {he.detail}."
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Unhandled failure to delete item part of bundled item. Error: {e}."
        )
    # auth payload
    try:
        delete_dynamo_db_entry(id=id, table=get_auth_table(config))
    except HTTPException as he:
        raise HTTPException(
            status_code=he.status_code,
            detail=f"Failed to delete auth part of bundled item. Error: {he.detail}."
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Unhandled failure to delete auth part of bundled item. Error: {e}."
        )
    # lock payload
    try:
        delete_dynamo_db_entry(id=id, table=get_lock_table(config))
    except HTTPException as he:
        raise HTTPException(
            status_code=he.status_code,
            detail=f"Failed to delete lock part of bundled item. Error: {he.detail}."
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Unhandled failure to delete lock part of bundled item. Error: {e}."
        )


def get_generic_entry(id: str, table: Any, config: Config) -> Dict[str, Any]:
    try:
        response = table.get_item(
            Key={
                'id': id,
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=(f'Failed to access database. Error: {e}')
        )

    if "Item" not in response:
        # return failed status later. not a http
        raise KeyError(
            f"Failed to find item. Is the ID ('{id}') correct and in the database?")

    return response['Item']


def get_lock_entry(id: str, config: Config) -> Dict[str, Any]:
    # get the lock table
    table = get_lock_table(config=config)
    return get_generic_entry(
        id=id,
        table=table,
        config=config
    )


def get_auth_entry(id: str, config: Config) -> Dict[str, Any]:
    # get the auth table
    table = get_auth_table(config=config)
    return get_generic_entry(
        id=id,
        table=table,
        config=config
    )


def get_entry_raw(id: str, config: Config) -> Dict[str, Any]:
    """    get_registry_entry
        Given a handle id, returns a Registry item containing associated data for this handle.

        Arguments
        ----------
        handle : str
            Unique handle ID associated with dataset wishing to be returned.

        Returns
        -------
         : RegistryItem
            An object containing the data associated with the given handle as attributes.

        Raises
        ------
        Exception
            If fails to read table or if fails to find an item associated with the handle.
        KeyError
            If the handle is empty

        See Also (optional)
        --------

        Examples (optional)
        --------
    """
    
    if id == "":
        raise ValueError("ID cannot be empty")
    # get the table
    table = get_registry_table(config=config)
    return get_generic_entry(
        id=id,
        table=table,
        config=config
    )


def reduce_and_list(and_list: List[Any]) -> Union[And, Attr]:
    """Recursive method which applies And as a 
    reduction across the list of conditions.

    Parameters
    ----------
    and_list : List[Any]
        The list of and conditions

    Returns
    -------
    Union[And, Attr]
        Either an attribute or an And condition containing
        the attributes
    """
    # recursive case
    if len(and_list) > 1:
        return And(and_list[0], reduce_and_list(and_list[1:]))
    else:
        # base case
        return and_list[0]


def filter_expression_from_query_filter(filter: QueryFilter) -> Optional[Union[And, Attr]]:
    """Given the Query Filter object, will convert this pydantic
    model which was received from the general list API into a 
    dynamodb boto filter expression by And'ing a sequence of 
    conditions together. 

    Parameters
    ----------
    filter : QueryFilter
        The query filter to convert

    Returns
    -------
    Optional[Union[And, Attr]]
        The boto core condition expression (if any)
    """
    # Start empty and list
    and_list: List[Any] = []

    # For each filter, add to and list
    if filter.item_category:
        and_list.append(Attr('item_category').eq(filter.item_category.value))
    if filter.item_subtype:
        and_list.append(Attr('item_subtype').eq(filter.item_subtype.value))

    # ALL doesn't require any filter

    # COMPLETE ONLY requires a record type filter
    if filter.record_type == QueryRecordTypes.COMPLETE_ONLY:
        and_list.append(Attr('record_type').eq(RecordType.COMPLETE_ITEM.value))
    # SEED ONLY requires a record type filter
    if filter.record_type == QueryRecordTypes.SEED_ONLY:
        and_list.append(Attr('record_type').eq(RecordType.SEED_ITEM.value))

    # Return the And which compiles all filters into a single statement
    if len(and_list) > 0:
        if len(and_list) > 1:
            return reduce_and_list(and_list)
        else:
            return and_list[0]
    else:
        return None


def list_all_items(
    table: Any,
    filter: Optional[QueryFilter],
) -> List[Dict[str, Any]]:

    # Get filter expression if required
    filter_expression: Optional[And] = None
    if filter:
        filter_expression = filter_expression_from_query_filter(filter)

    # try to scan with filter query
    try:
        # compile response items
        items: List[Dict[str, Any]] = []

        # perform first scan
        if filter_expression:
            response = table.scan(FilterExpression=filter_expression)
        else:
            response = table.scan()

        # iterate through items and append - don't bother parsing yet
        for item in response["Items"]:
            items.append(item)

        # is not empty. (i.e., haven't finished scanning all the table.)
        while 'LastEvaluatedKey' in response.keys():
            if filter_expression:
                response = table.scan(
                    ExclusiveStartKey=response['LastEvaluatedKey'],
                    FilterExpression=filter_expression
                )
            else:
                response = table.scan(
                    ExclusiveStartKey=response['LastEvaluatedKey'],
                )
            for item in response["Items"]:
                items.append(item)

    # Catch any errors
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=(f"Failed to scan the Database. Error: {e}")
        )

    modified_items = [
        remove_universal_key_attribute_from_item(item) for item in items]

    # Return the list of items that was retrieved
    return modified_items


@dataclass
class QueryParams():
    index_name: str
    key_condition_expression: Any
    scan_index_forward: bool
    filter_expression: Any


subtype_key = "item_subtype"
approver_key = "release_approver"
universal_key = "universal_partition_key"
updated_timestamp_key = "updated_timestamp"
created_timestamp_key = "created_timestamp"
display_name_key = "display_name"
release_timestamp_key = "release_timestamp"
access_info_uri_key = "access_info_uri"

def sort_filter_to_key_condition(sort_options: Optional[SortOptions], filter_options: Optional[FilterOptions]) -> Any:

    if filter_options is not None:

        # * expand if more filter options are added.
        if filter_options.item_subtype is not None:
            condition = Key(subtype_key).eq(filter_options.item_subtype)
            if sort_options is not None and sort_options.sort_type == SortType.ACCESS_INFO_URI_BEGINS_WITH:
                condition = condition & Key(access_info_uri_key).begins_with(sort_options.begins_with)
            return condition
        
        if filter_options.release_reviewer is not None:
            return Key(approver_key).eq(filter_options.release_reviewer)
    else:
        # no filter was provided. Use the index we made with primary key that includes all items
        return Key(universal_key).eq("OK")

    # A filter was provided, but it was empty
    return Key(universal_key).eq("OK")


def generate_index_name(partition_key: str, sort_key: str) -> str:
    return f"{partition_key}-{sort_key}-index"


SORT_TYPE_TO_KEY_MAP: Dict[Optional[SortType], str] = {
    # Default = updated timestamp
    None: updated_timestamp_key,
    # other sort options
    SortType.CREATED_TIME:  created_timestamp_key,
    SortType.UPDATED_TIME:  updated_timestamp_key,
    SortType.DISPLAY_NAME:  display_name_key,
    SortType.RELEASE_TIMESTAMP: release_timestamp_key,
    SortType.ACCESS_INFO_URI_BEGINS_WITH: access_info_uri_key
}
FILTER_TYPE_TO_KEY_MAP: Dict[Optional[FilterType], str] = {
    # Default = all included
    None: universal_key,
    # Other filters
    FilterType.ITEM_SUBTYPE: subtype_key,
    FilterType.RELEASE_REVIEWER: approver_key
}

FilterSort = Tuple[Optional[FilterType], Optional[SortType]]

FILTER_SORT_COMBINATIONS: List[FilterSort] = [
    # Default
    (None, None),

    # Filter by subtype
    (FilterType.ITEM_SUBTYPE, None),

    # Sort by updated/created/display
    (None, SortType.UPDATED_TIME),
    (None, SortType.CREATED_TIME),
    (None, SortType.DISPLAY_NAME),

    # Filter and sort subtype + combinations
    (FilterType.ITEM_SUBTYPE, SortType.UPDATED_TIME),
    (FilterType.ITEM_SUBTYPE, SortType.CREATED_TIME),
    (FilterType.ITEM_SUBTYPE, SortType.DISPLAY_NAME),

    # Release reviewer based index
    (FilterType.RELEASE_REVIEWER, SortType.RELEASE_TIMESTAMP),
    (FilterType.RELEASE_REVIEWER, None),

    # Access info uri sort only if filtering by subtype == Dataset.
    (FilterType.ITEM_SUBTYPE, SortType.ACCESS_INFO_URI_BEGINS_WITH),
    
]


def filter_sort_to_index(filter_sort: FilterSort) -> str:
    filter, sort = filter_sort
    partition_key = FILTER_TYPE_TO_KEY_MAP[filter]
    sort_key = SORT_TYPE_TO_KEY_MAP[sort]
    return generate_index_name(
        partition_key=partition_key,
        sort_key=sort_key
    )


# TODO dont use hardcoded strings. get from cdk config.
FILTER_SORT_TO_INDEX_MAP: Dict[FilterSort, str] = {
    fs: filter_sort_to_index(fs) for fs in FILTER_SORT_COMBINATIONS
}


def filter_options_to_filter_type(filter_options: FilterOptions) -> Optional[FilterType]:

    # * expand method if more filter options are added.
    # FitlerOptions currently allows just one filter.
    if filter_options.item_subtype:
        return FilterType.ITEM_SUBTYPE

    if filter_options.release_reviewer:
        return FilterType.RELEASE_REVIEWER

    return None


def sort_filter_to_index_name(
    sort_by: Optional[SortOptions],
    filter_by: Optional[FilterOptions],
) -> str:

    # Default (nothing provided)
    sort_type: Optional[SortType] = None
    filter_type: Optional[FilterType] = None

    if filter_by is not None:
        filter_type = filter_options_to_filter_type(
            filter_by)

    if sort_by is not None:
        sort_type = sort_by.sort_type

    try:
        return FILTER_SORT_TO_INDEX_MAP[(filter_type, sort_type)]
    except Exception as e:
        raise ValueError(
            f"Could not derive an index name for filter type {filter_type} and sort type {sort_type}. If attempting to sort items by some field belonging to only" +
            " particular item subtypes, ensure to provide the item subtype filter to access its index, or utilise the specific list routes for the item subtype.")


RECORD_TYPE_TO_FILTER_EXPRESSION_MAP: Dict[Union[QueryRecordTypes, QueryDatasetReleaseStatusType], Optional[Key]] = {
    QueryRecordTypes.ALL: None,
    QueryRecordTypes.COMPLETE_ONLY: Key('record_type').eq(RecordType.COMPLETE_ITEM),
    QueryRecordTypes.SEED_ONLY: Key('record_type').eq(RecordType.SEED_ITEM),

    QueryDatasetReleaseStatusType.RELEASED: Key('release_status').eq(ReleasedStatus.RELEASED),
    QueryDatasetReleaseStatusType.NOT_RELEASED: Key('release_status').eq(ReleasedStatus.NOT_RELEASED),
    QueryDatasetReleaseStatusType.PENDING: Key('release_status').eq(ReleasedStatus.PENDING),
}

DEFAULT_FILTER_TYPE = QueryRecordTypes.COMPLETE_ONLY


def filter_to_filter_expression(filter_by: Optional[FilterOptions]) -> Any:
    # defaults to complete only
    filter_value: Union[QueryRecordTypes,
                        QueryDatasetReleaseStatusType] = DEFAULT_FILTER_TYPE
    if filter_by is not None and filter_by.record_type is not None:
        filter_value = filter_by.record_type

    if filter_by is not None and filter_by.release_status is not None:
        # override as this means recordtype is complete.
        filter_value = filter_by.release_status

    # check it's present
    if filter_value not in RECORD_TYPE_TO_FILTER_EXPRESSION_MAP.keys():
        raise ValueError(
            f"Could not derive a filter expression for {filter_value}.")

    return RECORD_TYPE_TO_FILTER_EXPRESSION_MAP[filter_value]


def remove_universal_key_attribute_from_item(item: Dict[str, Any]) -> Dict[str, Any]:

    try:
        del item["universal_partition_key"]
    except:
        pass

    return item


def remove_none_values(my_dict: Dict[str, Any]) -> Dict[str, Any]:
    return {k: v for k, v in my_dict.items() if v is not None}


def query_dbb(
    table: Any,
    sort_by: Optional[SortOptions],
    filter_by: Optional[FilterOptions],
    pagination_key: Optional[PaginationKey],
    page_size: int,
) -> Tuple[List[Dict[str, Any]], Optional[PaginationKey]]:

    # Use dict method to avoid having multiple if branches (4) for different parameters
    # table.query() doesn't allow parameters set to None if we don't use them.
    try: 
        query_params: Dict[str, Any] = {
            "IndexName": sort_filter_to_index_name(sort_by=sort_by, filter_by=filter_by),
            "KeyConditionExpression": sort_filter_to_key_condition(sort_options=sort_by, filter_options=filter_by),
            "ScanIndexForward": sort_by.ascending if sort_by else DEFAULT_SORTING_ASCENDING,
            "FilterExpression": filter_to_filter_expression(filter_by),
            "Limit": page_size,
            "ExclusiveStartKey": pagination_key
        }
    except ValueError as ve:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to generate query parameters. Error: {ve}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate query parameters. Error: {e}"
        )

    query_params = remove_none_values(query_params)

    try:
        response = table.query(**query_params)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=(f"Failed to query the database. Error: {e}")
        )

    # remove the universal partition key from items
    items = [remove_universal_key_attribute_from_item(
        item) for item in response['Items']]

    # returns None if doesn't exist.
    return (items, response.get("LastEvaluatedKey"))
