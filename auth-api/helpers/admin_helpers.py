from typing import Callable, Set, Dict, List, Any, Tuple
from helpers.groups_table_helpers import *
from config import Config
from fastapi import HTTPException


def validate_add_only(old_items: Dict[str, Dict[str, Any]], new_items: Dict[str, Dict[str, Any]], allow_deletion: bool = False) -> List[Tuple[str, Dict[str, Any]]]:
    """
    Validates the ADD_ONLY import mode.

    Parameters
    ----------
    old_items : Dict[str, Dict[str, Any]]
        A map from id -> old item
    new_items : Dict[str, Dict[str, Any]]
        A map from id -> new item
    allow_deletion : bool, optional
        Allow deletion flag, by default False

    Returns
    -------
    List[Tuple[str, Dict[str, Any]]]
        A list of errors, empty list if no errors
    """
    error_list: List[Tuple[str, Dict[str, Any]]] = []

    new_ids_set: Set[str] = set(new_items.keys())
    old_ids_set: Set[str] = set(old_items.keys())

    # overwrite
    intersecting: Set[str] = old_ids_set.intersection(
        new_ids_set)

    if len(intersecting) > 0:
        for key in intersecting:
            error_list.append(
                (f"Overlapping item on add only mode {key}", new_items[key]))

    return error_list


def validate_add_or_overwrite(old_items: Dict[str, Dict[str, Any]], new_items: Dict[str, Dict[str, Any]], allow_deletion: bool = False) -> List[Tuple[str, Dict[str, Any]]]:
    """
    Validates the ADD_OR_OVERWRITE import mode.

    Parameters
    ----------
    old_items : Dict[str, Dict[str, Any]]
        A map from id -> old item
    new_items : Dict[str, Dict[str, Any]]
        A map from id -> new item
    allow_deletion : bool, optional
        Allow deletion flag, by default False

    Returns
    -------
    List[Tuple[str, Dict[str, Any]]]
        A list of errors, empty list if no errors
    """
    error_list: List[Tuple[str, Dict[str, Any]]] = []

    # there is no way this can be invalid items are either overridden or added,
    # no deletion

    return error_list


def validate_overwrite_only(old_items: Dict[str, Dict[str, Any]], new_items: Dict[str, Dict[str, Any]], allow_deletion: bool = False) -> List[Tuple[str, Dict[str, Any]]]:
    """
    Validates the OVERWRITE_ONLY import mode.

    Parameters
    ----------
    old_items : Dict[str, Dict[str, Any]]
        A map from id -> old item
    new_items : Dict[str, Dict[str, Any]]
        A map from id -> new item
    allow_deletion : bool, optional
        Allow deletion flag, by default False

    Returns
    -------
    List[Tuple[str, Dict[str, Any]]]
        A list of errors, empty list if no errors
    """
    error_list: List[Tuple[str, Dict[str, Any]]] = []

    new_ids_set: Set[str] = set(new_items.keys())
    old_ids_set: Set[str] = set(old_items.keys())

    # new
    ids_to_add: Set[str] = new_ids_set - old_ids_set

    if len(ids_to_add) > 0:
        for key in ids_to_add:
            error_list.append(
                (f"Item {key} does not already exist", new_items[key]))

    return error_list


def validate_sync_add_or_overwrite(old_items: Dict[str, Dict[str, Any]], new_items: Dict[str, Dict[str, Any]], allow_deletion: bool = False) -> List[Tuple[str, Dict[str, Any]]]:
    """
    Validates the SYNC_ADD_OR_OVERWRITE import mode.

    Parameters
    ----------
    old_items : Dict[str, Dict[str, Any]]
        A map from id -> old item
    new_items : Dict[str, Dict[str, Any]]
        A map from id -> new item
    allow_deletion : bool, optional
        Allow deletion flag, by default False

    Returns
    -------
    List[Tuple[str, Dict[str, Any]]]
        A list of errors, empty list if no errors
    """
    error_list: List[Tuple[str, Dict[str, Any]]] = []

    new_ids_set: Set[str] = set(new_items.keys())
    old_ids_set: Set[str] = set(old_items.keys())

    # deleted
    ids_to_delete: Set[str] = old_ids_set - new_ids_set

    if len(ids_to_delete) > 0:
        for key in ids_to_delete:
            error_list.append(
                (f"Item {key} currently exists but not provided in update", old_items[key]))

    return error_list


def validate_sync_deletion_allowed(old_items: Dict[str, Dict[str, Any]], new_items: Dict[str, Dict[str, Any]], allow_deletion: bool = False) -> List[Tuple[str, Dict[str, Any]]]:
    """
    Validates the SYNC_DELETION_ALLOWED import mode.

    Parameters
    ----------
    old_items : Dict[str, Dict[str, Any]]
        A map from id -> old item
    new_items : Dict[str, Dict[str, Any]]
        A map from id -> new item
    allow_deletion : bool, optional
        Allow deletion flag, by default False

    Returns
    -------
    List[Tuple[str, Dict[str, Any]]]
        A list of errors, empty list if no errors
    """
    error_list: List[Tuple[str, Dict[str, Any]]] = []

    new_ids_set: Set[str] = set(new_items.keys())
    old_ids_set: Set[str] = set(old_items.keys())

    # deleted
    ids_to_delete: Set[str] = old_ids_set - new_ids_set

    # items will be deleted - but only raise error if allow deletion was not
    # explicitly enabled
    if len(ids_to_delete) > 0 and not allow_deletion:
        for key in ids_to_delete:
            error_list.append(
                (f"Item {key} will be deleted but deletion not explicitly enabled", old_items[key]))

    return error_list


def action_add_only(config: Config, old_items: Dict[str, Dict[str, Any]], new_items: Dict[str, Dict[str, Any]], trial_mode: bool = True) -> GroupsImportStatistics:
    """
    Action function for the ADD_ONLY import mode. Must apply changes IFF the
    trial mode == False. Responds with a statistics for items that either
    were/would be changed.

    Parameters
    ----------
    config : Config
        The fastapi config
    old_items : Dict[str, Dict[str, Any]]
        Map from id -> old items
    new_items : Dict[str, Dict[str, Any]]
        Map from id -> new items
    trial_mode : bool, optional
        Is this a trial mode?, by default True

    Returns
    -------
    GroupsImportStatistics
        The statistics for the changes applied

    Raises
    ------
    HTTPException
        Raises an exception if a write error occurs
    """
    new_ids_set: Set[str] = set(new_items.keys())
    old_ids_set: Set[str] = set(old_items.keys())

    # just add the new ids - we already know these are all new

    if not trial_mode:
        groups_table = get_groups_table(config)
        for entry in new_items.values():
            try:
                assert entry['id'] not in old_ids_set
                write_dynamo_db_entry_raw(
                    item=entry, table=groups_table)
            except Exception as e:
                raise HTTPException(
                    status_code=500,
                    detail=f"Error occurred while writing to dynamo DB table, error: {e}"
                )

    return GroupsImportStatistics(
        old_size=len(old_ids_set),
        new_size=len(old_ids_set) + len(new_ids_set),
        deleted_entries=0,
        overwritten_entries=0,
        new_entries=len(new_ids_set)
    )


def action_add_or_overwrite(config: Config, old_items: Dict[str, Dict[str, Any]], new_items: Dict[str, Dict[str, Any]], trial_mode: bool = True) -> GroupsImportStatistics:
    """
    Action function for the ADD_OR_OVERWRITE import mode. Must apply changes IFF the
    trial mode == False. Responds with a statistics for items that either
    were/would be changed.

    Parameters
    ----------
    config : Config
        The fastapi config
    old_items : Dict[str, Dict[str, Any]]
        Map from id -> old items
    new_items : Dict[str, Dict[str, Any]]
        Map from id -> new items
    trial_mode : bool, optional
        Is this a trial mode?, by default True

    Returns
    -------
    GroupsImportStatistics
        The statistics for the changes applied

    Raises
    ------
    HTTPException
        Raises an exception if a write error occurs
    """
    new_ids_set: Set[str] = set(new_items.keys())
    old_ids_set: Set[str] = set(old_items.keys())

    # just add the new ids - we already know these are all new
    if not trial_mode:
        groups_table = get_groups_table(config)
        for entry in new_items.values():
            try:
                write_dynamo_db_entry_raw(
                    item=entry, table=groups_table)
            except Exception as e:
                raise HTTPException(
                    status_code=500,
                    detail=f"Error occurred while writing to dynamo DB table, error: {e}"
                )

    # work out sets for counting
    new_and_old_overlap: Set[str] = old_ids_set.intersection(
        new_ids_set)
    new_only = new_ids_set - old_ids_set
    old_and_new: Set[str] = old_ids_set.union(new_ids_set)

    return GroupsImportStatistics(
        old_size=len(old_ids_set),
        new_size=len(old_and_new),
        deleted_entries=0,
        overwritten_entries=len(new_and_old_overlap),
        new_entries=len(new_only)
    )


def action_overwrite_only(config: Config, old_items: Dict[str, Dict[str, Any]], new_items: Dict[str, Dict[str, Any]], trial_mode: bool = True) -> GroupsImportStatistics:
    """
    Action function for the OVERWRITE_ONLY import mode. Must apply changes IFF the
    trial mode == False. Responds with a statistics for items that either
    were/would be changed.

    Parameters
    ----------
    config : Config
        The fastapi config
    old_items : Dict[str, Dict[str, Any]]
        Map from id -> old items
    new_items : Dict[str, Dict[str, Any]]
        Map from id -> new items
    trial_mode : bool, optional
        Is this a trial mode?, by default True

    Returns
    -------
    GroupsImportStatistics
        The statistics for the changes applied

    Raises
    ------
    HTTPException
        Raises an exception if a write error occurs
    """
    new_ids_set: Set[str] = set(new_items.keys())
    old_ids_set: Set[str] = set(old_items.keys())

    # just add the new ids - we already know these are all overwrites
    if not trial_mode:
        groups_table = get_groups_table(config)
        for entry in new_items.values():
            try:
                assert entry['id'] in old_ids_set
                write_dynamo_db_entry_raw(
                    item=entry, table=groups_table)
            except Exception as e:
                raise HTTPException(
                    status_code=500,
                    detail=f"Error occurred while writing to dynamo DB table, error: {e}"
                )

    return GroupsImportStatistics(
        old_size=len(old_ids_set),
        new_size=len(old_ids_set),
        deleted_entries=0,
        overwritten_entries=len(new_ids_set),
        new_entries=0
    )


def action_sync_add_or_overwrite(config: Config, old_items: Dict[str, Dict[str, Any]], new_items: Dict[str, Dict[str, Any]], trial_mode: bool = True) -> GroupsImportStatistics:
    """
    Action function for the SYNC_ADD_OR_OVERWRITE import mode. Must apply changes IFF
    the trial mode == False. Responds with a statistics for items that either
    were/would be changed.

    Parameters
    ----------
    config : Config
        The fastapi config
    old_items : Dict[str, Dict[str, Any]]
        Map from id -> old items
    new_items : Dict[str, Dict[str, Any]]
        Map from id -> new items
    trial_mode : bool, optional
        Is this a trial mode?, by default True

    Returns
    -------
    GroupsImportStatistics
        The statistics for the changes applied

    Raises
    ------
    HTTPException
        Raises an exception if a write error occurs
    """
    new_ids_set: Set[str] = set(new_items.keys())
    old_ids_set: Set[str] = set(old_items.keys())

    # we know that all new handle items are either new or
    # overwrite and that there are no items in old but not in
    # new

    if not trial_mode:
        groups_table = get_groups_table(config)
        for entry in new_items.values():
            try:
                write_dynamo_db_entry_raw(
                    item=entry, table=groups_table)
            except Exception as e:
                raise HTTPException(
                    status_code=500,
                    detail=f"Error occurred while writing to dynamo DB table, error: {e}"
                )

    new_and_old_overlap: Set[str] = old_ids_set.intersection(
        new_ids_set)
    new_only = new_ids_set - old_ids_set
    old_and_new: Set[str] = old_ids_set.union(new_ids_set)

    return GroupsImportStatistics(
        old_size=len(old_ids_set),
        new_size=len(old_and_new),
        deleted_entries=0,
        overwritten_entries=len(new_and_old_overlap),
        new_entries=len(new_only)
    )


def action_sync_deletion_allowed(config: Config, old_items: Dict[str, Dict[str, Any]], new_items: Dict[str, Dict[str, Any]], trial_mode: bool = True) -> GroupsImportStatistics:
    """
    Action function for the SYNC_DELETION_ALLOWED import mode. Must apply
    changes IFF the trial mode == False. Responds with a statistics for items
    that either were/would be changed.

    Parameters
    ----------
    config : Config
        The fastapi config
    old_items : Dict[str, Dict[str, Any]]
        Map from id -> old items
    new_items : Dict[str, Dict[str, Any]]
        Map from id -> new items
    trial_mode : bool, optional
        Is this a trial mode?, by default True

    Returns
    -------
    GroupsImportStatistics
        The statistics for the changes applied

    Raises
    ------
    HTTPException
        Raises an exception if a write error occurs
    """
    new_ids_set: Set[str] = set(new_items.keys())
    old_ids_set: Set[str] = set(old_items.keys())

    # new
    ids_to_add: Set[str] = new_ids_set - old_ids_set

    # overwrite
    intersecting: Set[str] = old_ids_set.intersection(
        new_ids_set)

    # deleted
    ids_to_delete: Set[str] = old_ids_set - new_ids_set

    # add all the items in the new items - either overwrite or add
    if not trial_mode:
        groups_table = get_groups_table(config)
        for entry in new_items.values():
            try:
                write_dynamo_db_entry_raw(
                    item=entry, table=groups_table)
            except Exception as e:
                raise HTTPException(
                    status_code=500,
                    detail=f"Error occurred while writing to dynamo DB table, error: {e}"
                )

        # now delete all items which are in the old set but not the new!
        # we have validated multiple times that deletion is allowed
        for handle_to_delete in ids_to_delete:
            try:
                assert handle_to_delete not in new_ids_set
                delete_entry_with_table(
                    id=handle_to_delete, table=groups_table)
            except Exception as e:
                raise HTTPException(
                    status_code=500,
                    detail=f"Error occurred while deleting from dynamo DB table, error: {e}"
                )

    return GroupsImportStatistics(
        old_size=len(old_ids_set),
        new_size=len(new_ids_set),
        deleted_entries=len(ids_to_delete),
        overwritten_entries=len(intersecting),
        new_entries=len(ids_to_add)
    )


# This defines a map between import modes and functions which take old item id maps, new item id maps,
# and the allow deletion flag, and return a list of errors, if any. See above functions
# for a template to implement more
ValidatorFunc = Callable[[Dict[str, Any], Dict[str,
                                               Any], bool], List[Tuple[str, Dict[str, Any]]]]
ActionFunc = Callable[[Config, Dict[str, Any],
                       Dict[str, Any], bool], GroupsImportStatistics]

IMPORT_MODE_FUNCTION_MAP: Dict[ImportMode, Tuple[ValidatorFunc, ActionFunc]] = {
    ImportMode.ADD_ONLY: (validate_add_only, action_add_only),
    ImportMode.ADD_OR_OVERWRITE: (validate_add_or_overwrite, action_add_or_overwrite),
    ImportMode.OVERWRITE_ONLY: (validate_overwrite_only, action_overwrite_only),
    ImportMode.SYNC_ADD_OR_OVERWRITE: (validate_sync_add_or_overwrite, action_sync_add_or_overwrite),
    ImportMode.SYNC_DELETION_ALLOWED: (
        validate_sync_deletion_allowed, action_sync_deletion_allowed)
}

# Check that all import types have a validator and action
for import_mode in ImportMode:
    assert import_mode in IMPORT_MODE_FUNCTION_MAP.keys()


def import_parsed(import_request: GroupsImportRequest, config: Config) -> GroupsImportResponse:
    """
    Performs a parsed import by validating that the items are parsable as
    RecordInfo objects, and that they are parsable either as a seeded item or as
    a complete item of the specified category/subtype. Then uses the unparsed
    import function to complete the import.

    Parameters
    ----------
    import_request : GroupsImportRequest
        The import request
    config : Config
        The fastAPI config

    Returns
    -------
    GroupsImportResponse
        A response to the import - which includes stats
    """
    # Validate the provided items

    # Collect errors
    error_list: List[Tuple[str, Dict[str, Any]]] = []

    for item in import_request.items:
        # Try to parse into base level record info
        try:
            group = UserGroup.parse_obj(item)
        except Exception as e:
            error_list.append(
                (f"Could not parse item as valid group, exception: {e}", item))
            continue

    # now we have parsed all objects
    if len(error_list) > 0:
        return GroupsImportResponse(
            status=Status(
                success=False,
                details=f"There were {len(error_list)} items with parsing issues! See failure list."
            ),
            trial_mode=import_request.trial_mode,
            failure_list=error_list
        )

    # Then perform a regular unparsed import if everything okay
    return import_unparsed(
        import_request=import_request,
        config=config
    )


def import_unparsed(import_request: GroupsImportRequest, config: Config) -> GroupsImportResponse:
    """
    Performs an unparsed import of the specified items. Adheres to the import
    mode by performing a two stage validation -> action step for each import
    type. 

    Returns config information or throws handled HTTP exceptions if something
    goes wrong.

    Parameters
    ----------
    import_request : GroupsImportRequest
        The import request including import mode and other config
    config : Config
        The fastAPI config

    Returns
    -------
    GroupsImportResponse
        The response including stats

    Raises
    ------
    HTTPException
        If something goes wrong during writing
    """
    # get the current list of items
    old_items_list = list_all_items(get_groups_table(config))
    new_items_list = import_request.items

    # build lookups against identifiers assumes that field 'id' is present on
    # all entries
    new_items_lookup: Dict[str, Dict[str, Any]] = {}
    for i in new_items_list:
        new_items_lookup[i["id"]] = i
    old_items_lookup: Dict[str, Dict[str, Any]] = {}
    for i in old_items_list:
        old_items_lookup[i["id"]] = i

    # perform validation based on the import type
    importer_functions = IMPORT_MODE_FUNCTION_MAP.get(
        import_request.import_mode)
    if not importer_functions:
        raise HTTPException(
            status_code=500, detail=f'Import mode {import_request.import_mode} was missing a validator function...')

    # extract the functions for the validator
    import_mode_validator, import_mode_action = importer_functions

    # check for errors in cardinalities of sets as per import mode
    error_list = import_mode_validator(
        old_items_lookup, new_items_lookup, import_request.allow_entry_deletion)

    if len(error_list) > 0:
        return GroupsImportResponse(
            status=Status(
                success=False,
                details="There were errors during validation of the import mode, see the failure list."
            ),
            trial_mode=import_request.trial_mode,
            failure_list=error_list
        )

    # now perform the migration if required
    stats: GroupsImportStatistics = import_mode_action(
        config, old_items_lookup, new_items_lookup, import_request.trial_mode)

    return GroupsImportResponse(
        status=Status(
            success=True, details=f"{'TRIAL: ' if import_request.trial_mode else ''}Successfully imported with mode: {import_request.import_mode}."),
        trial_mode=import_request.trial_mode,
        statistics=stats
    )


def export_all_items(config: Config) -> List[Dict[str, Any]]:
    """
    Given fastAPI config, will perform an unfiltered scan of the groups table
    to dump all the info.

    Parameters
    ----------
    config : Config
        The fastAPI config

    Returns
    -------
    List[Dict[str, Any]]
        A list of untyped items.
    """
    # Run a list all items operation to scan the current table with filter
    # applied which specifies all
    try:
        return list_all_items(table=get_groups_table(config))
    # Managed exception
    except HTTPException as http_exception:
        raise http_exception
    # Non managed exception
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected exception occurred during database listing: {e}"
        )


def export_from_external_table(table_name: str, config: Config) -> List[Dict[str, Any]]:
    """Runs an export on the specified external table.

    Parameters
    ----------
    table_name : str
        The name of the dynamoDB table to import from
    config : Config
        The fastAPI config

    Returns
    -------
    List[Dict[str, Any]]
        The list of untyped items

    Raises
    ------
    HTTPException
        If something goes wrong getting the table, or reading from it.
    """
    # Run a list all items operation to scan the current table with filter
    # applied which specifies all

    # get the external table object
    try:
        table = get_table_from_name(table_name=table_name)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Couldn't create the boto table resource! {e}")

    # try to list all the items at the external table
    try:
        return list_all_items(table=table)
    # Managed exception
    except HTTPException as http_exception:
        raise http_exception
    # Non managed exception
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected exception occurred during database listing: {e}"
        )
