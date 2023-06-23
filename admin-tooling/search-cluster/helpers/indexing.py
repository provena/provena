import logging
import requests
from typing import Dict, Any
from config import SearchableObject, LINEARISED_FIELD
import json
from SharedInterfaces.RegistryModels import *


def get_index_endpoint(search_domain_name: str, search_index: str) -> str:
    type = '_doc'
    return search_domain_name + '/' + search_index + '/' + type + '/'


headers = {"Content-Type": "application/json"}

# setup logger
log = logging.getLogger()
log.setLevel(logging.DEBUG)

# status codes we are okay with
good_status_codes = [200, 201]


# the lambda function must return a list of failed event Ids if any, these flags
# control whether failures indexing/deleting reports an error back to the queue
# for retry

# no retry on delete
FAIL_ON_DELETE_ISSUE = False

# retry on index fail
FAIL_ON_INDEX_ISSUE = True


def delete_document_from_index(url: str, awsauth: Any, id: str, event_id: str, error_ids: List[str]) -> bool:
    try:
        response = requests.delete(url + id, auth=awsauth)
        # force an error
        response.raise_for_status()
    except requests.exceptions.HTTPError as he:
        if FAIL_ON_DELETE_ISSUE:
            fail_with_error(
                id=event_id,
                message=f"Tried to delete record {id} but delete request failed. Requests error: {he}.",
                error_ids=error_ids
            )
        else:
            log.error(
                f"Tried to delete record {id} but delete request failed. Requests error: {he}. Not reporting batch failure.")

        return False

    # all is well
    log.info(f"Deleted id {id}. Status code: {response.status_code}.")
    return True


def lodge_document_into_index(url: str, awsauth: Any, id: str, event_id: str, object: Dict[str, str], error_ids: List[str]) -> bool:
    try:
        response = requests.put(url + id, auth=awsauth,
                                json=object, headers=headers)
        # force an error
        response.raise_for_status()
    except requests.exceptions.HTTPError as he:
        if FAIL_ON_INDEX_ISSUE:
            fail_with_error(
                id=event_id,
                message=f"Tried to lodge record {id} but index request failed. Requests error: {he}.",
                error_ids=error_ids
            )
        else:
            log.error(
                f"Tried to index record {id} but index request failed. Requests error: {he}. Not reporting batch failure.")
        return False

    # all is well
    log.info(
        f"Indexed document with id {id}. Status code: {response.status_code}.")
    return True


def sanitize_id(id: str) -> str:
    return id.replace("/", "_")


def fail_with_error(id: str, message: str, error_ids: List[str]) -> None:
    log.error(f"Failed processing event id {id}, error: {message}.")
    log.debug(f"Adding message id {id} to the batch failure list.")
    error_ids.append(id)


def linearise_search_object(object: Dict[str, str]) -> Dict[str, str]:
    # retains item subtype if present
    output = " ".join(object.values())
    return {LINEARISED_FIELD: output, "item_subtype": object.get("item_subtype") or "", "id": object.get("id") or ""}


def modified_handler(awsauth: Any, records: List[Dict[str, Any]], record_id_field: str, index_name: str, search_service_endpoint: str, item_type: SearchableObject) -> None:
    error_ids: List[str] = []

    index_success_count = 0
    index_fail_count = 0
    delete_success_count = 0
    delete_fail_count = 0
    unknown_fail_count = 0

    for record in records:
        # try and pull out ID
        try:
            # Get the primary key for use as the OpenSearch ID
            id = record[record_id_field]
        except Exception as e:
            fail_with_error(
                id=id,
                message=f"Failed to pull out model specific ID field, exception: {e}.",
                error_ids=error_ids
            )
            unknown_fail_count += 1
            continue

        # try and sanitize IDs
        try:
            sanitized_id = sanitize_id(id)
        except Exception as e:
            fail_with_error(
                id=id,
                message=f"Tried to sanitize the handle ID, but failed, error: {e}.",
                error_ids=error_ids
            )
            unknown_fail_count += 1
            continue

        # deletion not implemented

        # if event_name == 'REMOVE':
        #    # attempt to delete the document and update error IDs if failed
        #    success = delete_document_from_index(
        #        id=sanitized_id,
        #        event_id=event_id,
        #        error_ids=error_ids
        #    )
        #    # move to the next item if it fails
        #    if not success:
        #        delete_fail_count += 1
        #        continue

        #    delete_success_count += 1

        # already ready to go json
        json_document = record

        # ready to pull out search object
        search_object: Dict[str, str] = {}

        # now parse as the desired object type
        if item_type == SearchableObject.REGISTRY_ITEM:
            # parse the item as RecordInfo
            try:
                record_info = RecordInfo.parse_obj(json_document)
            except Exception as e:
                # Failed parsing into record info - this object is probably invalid
                fail_with_error(
                    id=id,
                    message=f"Can't parse registry item with id {id} as RecordInfo - invalid item. Aborting. Error {e}",
                    error_ids=error_ids
                )
                index_fail_count += 1
                continue

            # check the item type
            record_type = record_info.record_type

            if record_type == RecordType.SEED_ITEM:
                # parse as seed item
                try:
                    seeded_item = SeededItem.parse_obj(json_document)
                except Exception as e:
                    fail_with_error(
                        id=id,
                        message=f"Item with {id = } is marked as a seed item but failed to be parsed. Error: {e}.",
                        error_ids=error_ids
                    )
                    index_fail_count += 1
                    continue

                # get the searchable object
                try:
                    search_object = seeded_item.get_search_ready_object()
                except Exception as e:
                    fail_with_error(
                        id=id,
                        message=f"get_search_ready_object method failed for item with {id = }. Error {e}.",
                        error_ids=error_ids
                    )
                    index_fail_count += 1
                    continue

            elif record_type == RecordType.COMPLETE_ITEM:
                # get the correct model type
                cat = record_info.item_category
                type = record_info.item_subtype
                model_type = MODEL_TYPE_MAP.get((cat, type))

                if model_type is None:
                    fail_with_error(
                        id=id,
                        message=f"Item {id = } had invalid category/subtype combination {cat}/{type}...",
                        error_ids=error_ids
                    )
                    index_fail_count += 1
                    continue

                # parse as model type
                try:
                    full_item = model_type.parse_obj(json_document)
                except Exception as e:
                    fail_with_error(
                        id=id,
                        message=f"Item {id = } could not be parsed as it's type, error: {e}.",
                        error_ids=error_ids
                    )
                    index_fail_count += 1
                    continue

                # get the searchable object
                try:
                    search_object = full_item.get_search_ready_object()
                except Exception as e:
                    fail_with_error(
                        id=id,
                        message=f"get_search_ready_object method failed for item with {id = }. Error {e}.",
                        error_ids=error_ids
                    )
                    index_fail_count += 1
                    continue
            else:
                fail_with_error(
                    id=id,
                    message=f"Item {id = } with unknown record type: {record_type}.",
                    error_ids=error_ids
                )
                index_fail_count += 1
                continue

            # lodge the search object
            log.debug("Parsed searchable item - ready to lodge")
            try:
                log.debug(json.dumps(search_object, indent=2))
            except Exception as e:
                log.warning(
                    f"Couldn't dump JSON contents - continuing. Exception {e}")

        elif item_type == SearchableObject.DATA_STORE_ITEM:
            print("Cannot index dataset! Deprecated")

        linearised = linearise_search_object(object=search_object)
        # lodge the item
        success = lodge_document_into_index(
            id=sanitized_id,
            event_id=id,
            object=linearised,
            error_ids=error_ids,
            url=get_index_endpoint(
                search_domain_name=search_service_endpoint,
                search_index=index_name
            ),
            awsauth=awsauth
        )

        if not success:
            index_fail_count += 1
            continue

        index_success_count += 1

    # return failed IDs and print statistics
    report = f"""
    Total items handled: {len(records)} 
    
    {index_success_count = }
    {delete_success_count = }
    
    {index_fail_count = }
    {delete_fail_count = }
    {unknown_fail_count = }
    """

    if (len(error_ids) > 0):
        log.warning("Errors occurred, report:")
        log.warning(report)
    else:
        log.info("All successful! Report:")
        log.info(report)
