import json
from typing import Callable, Set, Dict, List
from helpers.registry.dynamo_helpers import *
from config import Config
from fastapi import HTTPException
from ProvenaInterfaces.SharedTypes import ImportMode

# action types


class RequiredAction(str, Enum):
    WRITE = "WRITE"
    DELETE = "DELETE"


@dataclass
class ImportExportAction():
    action: RequiredAction
    id: str
    bundled_item: Optional[BundledItem]


# Type aliases to simplify function signatures
IdItemMapType = Dict[str, BundledItem]
OldItemsType = IdItemMapType
NewItemsType = IdItemMapType
AllowDeletionType = bool
TrialModeType = bool
ErrorListType = List[Tuple[str, BundledItem]]
ValidatorFunc = Callable[[OldItemsType,
                          NewItemsType, AllowDeletionType], ErrorListType]
ActionFuncResponse = Tuple[List[ImportExportAction], RegistryImportStatistics]
ActionFunc = Callable[[Config, OldItemsType,
                       NewItemsType, TrialModeType], ActionFuncResponse]


def validate_add_only(old_items: OldItemsType, new_items: NewItemsType, allow_deletion: AllowDeletionType) -> ErrorListType:
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
    error_list: ErrorListType = []

    new_handles_set: Set[str] = set(new_items.keys())
    old_handles_set: Set[str] = set(old_items.keys())

    # overwrite
    intersecting: Set[str] = old_handles_set.intersection(
        new_handles_set)

    if len(intersecting) > 0:
        for key in intersecting:
            error_list.append(
                (f"Overlapping item on add only mode {key}", new_items[key]))

    return error_list


def validate_add_or_overwrite(old_items: OldItemsType, new_items: NewItemsType, allow_deletion: AllowDeletionType) -> ErrorListType:
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
    error_list: ErrorListType = []

    # there is no way this can be invalid items are either overridden or added,
    # no deletion

    return error_list


def validate_overwrite_only(old_items: OldItemsType, new_items: NewItemsType, allow_deletion: AllowDeletionType) -> ErrorListType:
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
    error_list: ErrorListType = []

    new_handles_set: Set[str] = set(new_items.keys())
    old_handles_set: Set[str] = set(old_items.keys())

    # new
    handles_to_add: Set[str] = new_handles_set - old_handles_set

    if len(handles_to_add) > 0:
        for key in handles_to_add:
            error_list.append(
                (f"Item {key} does not already exist", new_items[key]))

    return error_list


def validate_sync_add_or_overwrite(old_items: OldItemsType, new_items: NewItemsType, allow_deletion: AllowDeletionType) -> ErrorListType:
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
    error_list: ErrorListType = []

    new_handles_set: Set[str] = set(new_items.keys())
    old_handles_set: Set[str] = set(old_items.keys())

    # deleted
    handles_to_delete: Set[str] = old_handles_set - new_handles_set

    if len(handles_to_delete) > 0:
        for key in handles_to_delete:
            error_list.append(
                (f"Item {key} currently exists but not provided in update", old_items[key]))

    return error_list


def validate_sync_deletion_allowed(old_items: OldItemsType, new_items: NewItemsType, allow_deletion: AllowDeletionType) -> ErrorListType:
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
    error_list: ErrorListType = []

    new_handles_set: Set[str] = set(new_items.keys())
    old_handles_set: Set[str] = set(old_items.keys())

    # deleted
    handles_to_delete: Set[str] = old_handles_set - new_handles_set

    # items will be deleted - but only raise error if allow deletion was not
    # explicitly enabled
    if len(handles_to_delete) > 0 and not allow_deletion:
        for key in handles_to_delete:
            error_list.append(
                (f"Item {key} will be deleted but deletion not explicitly enabled", old_items[key]))

    return error_list


def action_add_only(config: Config, old_items: OldItemsType, new_items: NewItemsType, trial_mode: TrialModeType) -> ActionFuncResponse:
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
    ImportStatistics
        The statistics for the changes applied

    Raises
    ------
    HTTPException
        Raises an exception if a write error occurs
    """
    new_handles_set: Set[str] = set(new_items.keys())
    old_handles_set: Set[str] = set(old_items.keys())

    # just add the new handles - we already know these are all new
    actions: List[ImportExportAction] = [ImportExportAction(
        action=RequiredAction.WRITE, id=item.id, bundled_item=item) for item in new_items.values()]

    return actions, RegistryImportStatistics(
        old_registry_size=len(old_handles_set),
        new_registry_size=len(old_handles_set) + len(new_handles_set),
        deleted_entries=0,
        overwritten_entries=0,
        new_entries=len(new_handles_set)
    )


def action_add_or_overwrite(config: Config, old_items: OldItemsType, new_items: NewItemsType, trial_mode: TrialModeType) -> ActionFuncResponse:
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
    ImportStatistics
        The statistics for the changes applied

    Raises
    ------
    HTTPException
        Raises an exception if a write error occurs
    """
    new_handles_set: Set[str] = set(new_items.keys())
    old_handles_set: Set[str] = set(old_items.keys())

    # just add the new handles - we already know these are all new
    actions: List[ImportExportAction] = [ImportExportAction(
        action=RequiredAction.WRITE, id=item.id, bundled_item=item) for item in new_items.values()]

    # work out sets for counting
    new_and_old_overlap: Set[str] = old_handles_set.intersection(
        new_handles_set)
    new_only = new_handles_set - old_handles_set
    old_and_new: Set[str] = old_handles_set.union(new_handles_set)

    return actions, RegistryImportStatistics(
        old_registry_size=len(old_handles_set),
        new_registry_size=len(old_and_new),
        deleted_entries=0,
        overwritten_entries=len(new_and_old_overlap),
        new_entries=len(new_only)
    )


def action_overwrite_only(config: Config, old_items: OldItemsType, new_items: NewItemsType, trial_mode: TrialModeType) -> ActionFuncResponse:
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
    ImportStatistics
        The statistics for the changes applied

    Raises
    ------
    HTTPException
        Raises an exception if a write error occurs
    """
    new_handles_set: Set[str] = set(new_items.keys())
    old_handles_set: Set[str] = set(old_items.keys())

    # just add the new handles - we already know these are all overwrites
    actions: List[ImportExportAction] = [ImportExportAction(
        action=RequiredAction.WRITE, id=item.id, bundled_item=item) for item in new_items.values()]

    return actions, RegistryImportStatistics(
        old_registry_size=len(old_handles_set),
        new_registry_size=len(old_handles_set),
        deleted_entries=0,
        overwritten_entries=len(new_handles_set),
        new_entries=0
    )


def action_sync_add_or_overwrite(config: Config, old_items: OldItemsType, new_items: NewItemsType, trial_mode: TrialModeType) -> ActionFuncResponse:
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
    ImportStatistics
        The statistics for the changes applied

    Raises
    ------
    HTTPException
        Raises an exception if a write error occurs
    """
    new_handles_set: Set[str] = set(new_items.keys())
    old_handles_set: Set[str] = set(old_items.keys())

    # we know that all new handle items are either new or
    # overwrite and that there are no items in old but not in
    # new
    actions: List[ImportExportAction] = [ImportExportAction(
        action=RequiredAction.WRITE, id=item.id, bundled_item=item) for item in new_items.values()]

    new_and_old_overlap: Set[str] = old_handles_set.intersection(
        new_handles_set)
    new_only = new_handles_set - old_handles_set
    old_and_new: Set[str] = old_handles_set.union(new_handles_set)

    return actions, RegistryImportStatistics(
        old_registry_size=len(old_handles_set),
        new_registry_size=len(old_and_new),
        deleted_entries=0,
        overwritten_entries=len(new_and_old_overlap),
        new_entries=len(new_only)
    )


def action_sync_deletion_allowed(config: Config, old_items: OldItemsType, new_items: NewItemsType, trial_mode: TrialModeType) -> ActionFuncResponse:
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
    ImportStatistics
        The statistics for the changes applied

    Raises
    ------
    HTTPException
        Raises an exception if a write error occurs
    """
    new_handles_set: Set[str] = set(new_items.keys())
    old_handles_set: Set[str] = set(old_items.keys())

    # new
    handles_to_add: Set[str] = new_handles_set - old_handles_set

    # overwrite
    intersecting: Set[str] = old_handles_set.intersection(
        new_handles_set)

    # deleted
    handles_to_delete: Set[str] = old_handles_set - new_handles_set

    # compile actions
    actions: List[ImportExportAction] = []

    # write actions
    actions.extend([ImportExportAction(
        action=RequiredAction.WRITE, id=item.id, bundled_item=item) for item in new_items.values()])

    # delete actions
    actions.extend([ImportExportAction(
        action=RequiredAction.DELETE, id=id, bundled_item=None) for id in handles_to_delete])

    return actions, RegistryImportStatistics(
        old_registry_size=len(old_handles_set),
        new_registry_size=len(new_handles_set),
        deleted_entries=len(handles_to_delete),
        overwritten_entries=len(intersecting),
        new_entries=len(handles_to_add)
    )


# This defines a map between import modes and functions which take old item id maps, new item id maps,
# and the allow deletion flag, and return a list of errors, if any. See above functions
# for a template to implement more

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


def parse_item_payload(item: Dict[str, Any]) -> Optional[str]:
    # Try to parse into base level record info
    try:
        record_info = RecordInfo.parse_obj(item)
    except Exception as e:
        return (f"Could not parse registry item as Record Info: {e}")

    # If the record is a seeded item, then continue
    if record_info.record_type == RecordType.SEED_ITEM:
        return None

    # assert complete item
    assert record_info.record_type == RecordType.COMPLETE_ITEM

    # item was parsed properly - check types and parse as model of that type
    cat_subtype_tuple = (record_info.item_category,
                         record_info.item_subtype)

    # get the model that should be parsable for it
    item_model = MODEL_TYPE_MAP.get(cat_subtype_tuple)

    # if there is no known type for this category/subtype combination
    if not item_model:
        return (f"The item could be parsed as a record but had a category/subtype combination that was not known.")

    try:
        parsed_item = item_model.parse_obj(item)
    except Exception as e:
        return (f"Could not parse registry item as it's matched type: {e}")

    return None


def parse_auth_payload(item: Dict[str, Any]) -> Optional[str]:
    try:
        AuthTableEntry.parse_obj(item)
    except Exception as e:
        return (f"Failed to parse the auth payload of item as a AuthTableEntry.")

    return None


def parse_lock_payload(item: Dict[str, Any]) -> Optional[str]:
    try:
        LockTableEntry.parse_obj(item)
    except Exception as e:
        return (f"Failed to parse the lock payload of item as a LockTableEntry.")

    return None


def import_parsed(import_request: RegistryImportRequest, config: Config) -> RegistryImportResponse:
    """
    Performs a parsed import by validating that the items are parsable as
    RecordInfo objects, and that they are parsable either as a seeded item or as
    a complete item of the specified category/subtype. Then uses the unparsed
    import function to complete the import.

    Parameters
    ----------
    import_request : RegistryImportRequest
        The import request
    config : Config
        The fastAPI config

    Returns
    -------
    RegistryImportResponse
        A response to the import - which includes stats
    """
    # Validate the provided items

    # Collect errors
    error_list: ErrorListType = []

    for item in import_request.items:
        # parse item payload
        err: Optional[str] = None
        err = parse_item_payload(item.item_payload)
        if err:
            error_list.append((err, item))
            continue
        # parse lock payload
        err = parse_lock_payload(item.lock_payload)
        if err:
            error_list.append((err, item))
            continue
        # parse auth payload
        err = parse_auth_payload(item.auth_payload)
        if err:
            error_list.append((err, item))
            continue

    # now we have parsed all objects
    if len(error_list) > 0:
        return RegistryImportResponse(
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


def take_actions(actions: List[ImportExportAction], config: Config) -> None:
    # perform all required actions
    write_bundles: List[BundledItem] = [
        action.bundled_item for action in actions if action.action == RequiredAction.WRITE]  # type: ignore
    delete_ids = [
        action.id for action in actions if action.action == RequiredAction.DELETE]

    # write all items
    batch_write_bundled_item(
        items=write_bundles, config=config)

    # delete all items
    batch_delete_bundled_item(
        ids=delete_ids, config=config)


def import_unparsed(import_request: RegistryImportRequest, config: Config) -> RegistryImportResponse:
    """
    Performs an unparsed import of the specified items. Adheres to the import
    mode by performing a two stage validation -> action step for each import
    type. 

    Returns config information or throws handled HTTP exceptions if something
    goes wrong.

    Parameters
    ----------
    import_request : RegistryImportRequest
        The import request including import mode and other config
    config : Config
        The fastAPI config

    Returns
    -------
    RegistryImportResponse
        The response including stats

    Raises
    ------
    HTTPException
        If something goes wrong during writing
    """
    # get the current list of items - bundled
    old_items_list = export_all_items(config=config)
    new_items_list = import_request.items

    # build lookups against identifiers
    new_items_lookup: Dict[str, BundledItem] = {}
    for i in new_items_list:
        new_items_lookup[i.id] = i
    old_items_lookup: Dict[str, BundledItem] = {}
    for i in old_items_list:
        old_items_lookup[i.id] = i

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
        return RegistryImportResponse(
            status=Status(
                success=False,
                details="There were errors during validation of the import mode, see the failure list."
            ),
            trial_mode=import_request.trial_mode,
            failure_list=error_list
        )

    # now perform the migration if required
    actions, stats = import_mode_action(
        config, old_items_lookup, new_items_lookup, import_request.trial_mode)

    # take actions if not trial mode
    if (not import_request.trial_mode):
        take_actions(actions, config)

    return RegistryImportResponse(
        status=Status(
            success=True, details=f"{'TRIAL: ' if import_request.trial_mode else ''}Successfully imported with mode: {import_request.import_mode}."),
        trial_mode=import_request.trial_mode,
        statistics=stats
    )


def export_all_items_external_tables(table_names: TableNames) -> List[BundledItem]:
    """
    Given fastAPI config, will perform an unfiltered scan of the external
    registry table to dump all the info.

    Parameters
    ----------
    table_names:
         A collection of all required table names

    Returns
    -------
    List[BundledItem]
        A list of untyped items.
    """

    # Run a list all items operation to scan the current table with filter
    # applied which specifies all
    reg_table = get_table_from_name(table_names.resource_table_name)
    try:
        resource_items = list_all_items(
            table=reg_table, filter=None)
    # Managed exception
    except HTTPException as http_exception:
        raise http_exception
    # Non managed exception
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected exception occurred during resource database listing: {e}"
        )
    lock_table = get_table_from_name(table_names.lock_table_name)
    try:
        lock_items = list_all_items(table=lock_table, filter=None)
    # Managed exception
    except HTTPException as http_exception:
        raise http_exception
    # Non managed exception
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected exception occurred during lock database listing: {e}"
        )
    auth_table = get_table_from_name(table_names.auth_table_name)
    try:
        auth_items = list_all_items(table=auth_table, filter=None)
    # Managed exception
    except HTTPException as http_exception:
        raise http_exception
    # Non managed exception
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected exception occurred during resource database listing: {e}"
        )

    # pull the tables together into bundled items
    try:
        return consolidate_table_items(
            resource_items=resource_items,
            lock_items=lock_items,
            auth_items=auth_items
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to export items as there was an issue consolidating the tables. Error: {e}."
        )


def export_all_items(config: Config) -> List[BundledItem]:
    """
    Given fastAPI config, will perform an unfiltered scan of the registry table
    to dump all the info.

    Parameters
    ----------
    config : Config
        The fastAPI config

    Returns
    -------
    List[BundledItem]
        A list of untyped items.
    """
    # Run a list all items operation to scan the current table with filter
    # applied which specifies all
    try:
        resource_items = list_all_items(
            table=get_registry_table(config), filter=None)
    # Managed exception
    except HTTPException as http_exception:
        raise http_exception
    # Non managed exception
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected exception occurred during resource database listing: {e}"
        )
    try:
        lock_items = list_all_items(table=get_lock_table(config), filter=None)
    # Managed exception
    except HTTPException as http_exception:
        raise http_exception
    # Non managed exception
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected exception occurred during lock database listing: {e}"
        )
    try:
        auth_items = list_all_items(table=get_auth_table(config), filter=None)
    # Managed exception
    except HTTPException as http_exception:
        raise http_exception
    # Non managed exception
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected exception occurred during resource database listing: {e}"
        )

    # pull the tables together into bundled items
    try:
        return consolidate_table_items(
            resource_items=resource_items,
            lock_items=lock_items,
            auth_items=auth_items
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to export items as there was an issue consolidating the tables. Error: {e}."
        )


class TableType(str, Enum):
    RESOURCE = "RESOURCE"
    LOCK = "LOCK"
    AUTH = "AUTH"


def build_id_map(
    item_list: List[Dict[str, Any]]
) -> Dict[str, Dict[str, Any]]:
    item_map: Dict[str, Dict[str, Any]] = {}

    for item in item_list:
        if 'id' not in item:
            dump = "Failed to dump contents."
            try:
                dump = json.dumps(item)
            except Exception:
                None
            raise ValueError(f"Item was missing id property. Payload: {dump}.")
        item_map[item['id']] = item

    return item_map


def consolidate_table_items(
    resource_items: List[Dict[str, Any]],
    lock_items: List[Dict[str, Any]],
    auth_items: List[Dict[str, Any]],
    source_of_truth: TableType = TableType.RESOURCE,
) -> List[BundledItem]:
    id_set: Set[str] = set()
    truth_items: Optional[List[Dict[str, Any]]] = None

    if source_of_truth == TableType.RESOURCE:
        truth_items = resource_items
    if source_of_truth == TableType.LOCK:
        truth_items = lock_items
    if source_of_truth == TableType.AUTH:
        truth_items = auth_items

    if truth_items is None:
        raise ValueError(
            f"The specified source of truth {source_of_truth} is not handled.")

    for item in truth_items:
        # check if id is present
        if 'id' not in item:
            dump = "Failed to dump contents."
            try:
                dump = json.dumps(item)
            except Exception:
                None
            raise ValueError(f"Item was missing id field. Payload: {dump}.")

        # add to id set
        id_set.add(item['id'])

    resource_map = build_id_map(resource_items)
    lock_map = build_id_map(lock_items)
    auth_map = build_id_map(auth_items)

    bundled_items: List[BundledItem] = []
    for id in id_set:
        if id not in resource_map:
            raise KeyError(
                f"The resource item list does not contain the id {id} that was expected from the source of truth table {source_of_truth}.")
        if id not in lock_map:
            raise KeyError(
                f"The lock item list does not contain the id {id} that was expected from the source of truth table {source_of_truth}.")
        if id not in auth_map:
            raise KeyError(
                f"The auth item list does not contain the id {id} that was expected from the source of truth table {source_of_truth}.")

        # all items present
        bundled_items.append(BundledItem(
            id=id,
            item_payload=resource_map[id],
            lock_payload=lock_map[id],
            auth_payload=auth_map[id]
        ))

    return bundled_items


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
        return list_all_items(table=table, filter=None)
    # Managed exception
    except HTTPException as http_exception:
        raise http_exception
    # Non managed exception
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected exception occurred during database listing: {e}"
        )
