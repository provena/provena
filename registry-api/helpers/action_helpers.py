from ProvenaInterfaces.RegistryAPI import *
from ProvenaInterfaces.RegistryModels import *
from dependencies.dependencies import user_is_admin
from KeycloakFastAPI.Dependencies import ProtectedRole
from helpers.dynamo_helpers import *
from helpers.time_helpers import get_timestamp
from helpers.handle_helpers import *
from helpers.custom_exceptions import SeedItemError, ItemTypeError
from helpers.auth_helpers import *
from helpers.lock_helpers import *
from helpers.util import py_to_dict
import json
from typing import TypeVar, Type, Callable, Any
from jsonschema import validate  # type: ignore
from helpers.id_fetch_helpers import parse_unknown_record_type, validate_item_type
from helpers.type_validators import custom_type_validators, ValidatorFunc

# Type var which captures the item base
# can be used with Type[type var] to denote
# a 'class' which is bounded by that type (rather)
# than an instance of that class
item_base_type = TypeVar('item_base_type', bound=ItemBase)
item_domain_info_type = TypeVar('item_domain_info_type', bound=DomainInfoBase)

# any of these roles will enable the specified action
FETCH_ACTION_ACCEPTED_ROLES = [
    METADATA_READ_ROLE, METADATA_WRITE_ROLE, ADMIN_ROLE]
EDIT_ACTION_ACCEPTED_ROLES = [METADATA_WRITE_ROLE, ADMIN_ROLE]
AUTH_ADMIN_ACCEPTED_ROLES = [ADMIN_ROLE]


def item_list_validate_and_filter_helper(
    items: List[Dict[str, Any]],
    pagination_key: Optional[PaginationKey],
    category: ItemCategory,
    subtype: ItemSubType,
    item_model_type: Type[item_base_type],
    user: User,
    config: Config,
    available_roles: Roles,
) -> GenericListResponse:
    # filter the items based on user membership (if enforcing auth)
    if config.enforce_user_auth:
        # get user groups once
        user_group_id_set = get_user_group_id_set(
            user=user,
            config=config
        )

        def item_permission_filter(item: Dict[str, Any]) -> bool:
            # check that the item at least has an ID
            if 'id' not in item:
                # we can't evaluate access if no id is present
                return False

            # pull out the item ID
            id = item['id']

            # return true if access OK false otherwise this returns a list of roles
            # the user is allowed to take against this resource
            role_list = describe_access_helper(
                id=id,
                config=config,
                user=user,
                available_roles=available_roles,
                already_checked_existence=True,
                user_group_ids=user_group_id_set
            ).roles

            # requires one of the acceptable fetch roles - filter based on this
            # response
            return evaluate_user_access(
                user_roles=role_list,
                acceptable_roles=FETCH_ACTION_ACCEPTED_ROLES
            )

        # filter items to only return visible items based on access roles and count
        # how many removed
        orig_count = len(items)
        items = list(
            filter(lambda item: item_permission_filter(item), items))
        access_filtered_count = orig_count - len(items)
    else:
        access_filtered_count = 0

    # collate complete items, seed items and failures
    complete_items: List[ItemBase] = []
    seed_items: List[SeededItem] = []
    unparsable_items: List[Dict[str, Any]] = []

    for item in items:
        # success:= parsable as item model type
        # failure:= not parsable as item model type
        try:
            parsed_record_type, record = parse_unknown_record_type(
                raw_item=item, item_model_type=item_model_type)
            if parsed_record_type == RecordType.COMPLETE_ITEM:
                assert isinstance(record, ItemBase)
                complete_items.append(record)
            if parsed_record_type == RecordType.SEED_ITEM:
                assert isinstance(record, SeededItem)
                seed_items.append(record)
        except Exception as e:
            unparsable_items.append(item)

    warning = len(unparsable_items) > 0
    return GenericListResponse(
        # status
        status=Status(
            success=not warning,
            details="Successfully listed items." + "" if not warning else
            " WARNING at least one unparsable entity exists in the registry."
        ),
        # items
        items=complete_items,
        seed_items=seed_items,
        unparsable_items=unparsable_items,

        # counts
        total_item_count=len(items),
        complete_item_count=len(complete_items),
        seed_item_count=len(seed_items),
        unparsable_item_count=len(unparsable_items),
        not_authorised_count=access_filtered_count,

        # pagination key passthrough
        pagination_key=pagination_key
    )


async def seed_item_helper(
        category: ItemCategory,
        subtype: ItemSubType,
        default_roles: Roles,
        versioning_enabled: bool,
        user: User,
        config: Config,
) -> GenericSeedResponse:
    """    seed_item_helper
        Generates a seed item with the specified category and sub
        type.

        Arguments
        ----------
        category : ItemCategory
            The intended category
        subtype : ItemSubType
            The intended sub type

        Returns
        -------
         : GenericSeedResponse
            Returns a generic seed response which is later
            specialised into the item types seed response.

        Raises
        ------
        HTTPException
            If something goes wrong with dynamoDB interactions.

        See Also (optional)
        --------

        Examples (optional)
        --------
    """

    # Create a handle which points to <registry URL>/item/<handle>
    handle = await mint_self_describing_handle(config=config)

    # create seed object
    seed_object: SeededItem = SeededItem(
        id=handle,
        owner_username=user.username,
        created_timestamp=get_timestamp(),
        updated_timestamp=get_timestamp(),
        item_category=category,
        item_subtype=subtype,
        record_type=RecordType.SEED_ITEM,
        versioning_info=VersioningInfo(
            previous_version=None,
            version=1,
            next_version=None
            # No reason required as first version
        ) if versioning_enabled else None
    )

    # write auth object first
    seed_auth_configuration(
        id=handle,
        username=user.username,
        config=config,
        default_roles=default_roles
    )

    # write lock object first
    seed_lock_configuration(
        id=handle,
        config=config,
    )

    # write the object to the registry
    friendly_format = json.loads(seed_object.json(exclude_none=True))
    try:
        write_registry_dynamo_db_entry_raw(
            registry_item=friendly_format,
            config=config
        )
    # Raise 500 if something goes wrong
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to write seed item to registry. Aborting. Contact administrator. Error {e}."
        )

    return GenericSeedResponse(
        status=Status(
            success=True, details="Successfully seeded an empty entity."),
        seeded_item=seed_object
    )


def fetch_helper(
    id: str,
    seed_allowed: bool,
    item_model_type: Type[item_base_type],
    category: ItemCategory,
    subtype: ItemSubType,
    available_roles: Roles,
    user: User,
    config: Config,
    service_proxy: bool
) -> GenericFetchResponse:
    """    fetch_helper
        Fetches item with the given ID.

        Arguments
        ----------
        id : str
            The handle ID
        seed_allowed : bool
            Should seed items be returned successfully.
        item_model_type : Type[item_base_type]
            The class/object which subclasses the item base
            pydantic model to parse into.

        Returns
        -------
         : GenericFetchResponse
            Returns a generic fetch response. This will later be parsed
            into the specialised fetch response for the item.

        Raises
        ------
        HTTPException
            Something went wrong with getting the item, either a key error
            or a 500 error for comm errors.

        See Also (optional)
        --------

        Examples (optional)
        --------
    """
    # Try to read the raw item with given key from registry
    try:
        raw_item: Dict[str, Any] = get_entry_raw(id=id, config=config)

    # The item wasn't present
    except KeyError as e:
        return GenericFetchResponse(
            status=Status(
                success=False, details=f"Could not find the given key ({id}) in the registry. Details {e}.")
        )

    except ValueError as e:
        return GenericFetchResponse(
            status=Status(
                success=False, details=f"Value error. Details {e}.")
        )

    # Error occurred which was caught and handled in fastAPI format
    except HTTPException as e:
        raise e

    # Unknown error occurred
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"An unexpected error occurred while reading from the registry: {e}.")

    # now make sure the user is allowed to read the contents of the item metadata
    roles = describe_access_helper(
        id=id,
        config=config,
        user=user,
        available_roles=available_roles,
        # don't look it up again - we already know it's present
        already_checked_existence=True,
        service_proxy=service_proxy
    ).roles

    # the user can fetch the record iff they have at least one of the acceptable roles
    access = evaluate_user_access(
        user_roles=roles, acceptable_roles=FETCH_ACTION_ACCEPTED_ROLES)

    if not access:
        raise HTTPException(
            status_code=401,
            detail=f"You are not authorised to fetch this item."
        )

    # Parse the type and record
    try:
        record_type, parsed_obj = parse_unknown_record_type(
            raw_item=raw_item,
            item_model_type=item_model_type
        )
    except Exception as e:
        return GenericFetchResponse(
            status=Status(
                success=False,
                details=f"The record was found but could not parsed as an appropriate type: Error {e}."
            )
        )

    # If seed item and seed not allowed, throw an error
    if record_type == RecordType.SEED_ITEM and not seed_allowed:
        return GenericFetchResponse(
            status=Status(
                success=False,
                details=f"A valid seed item was found, but seed_allowed was set to false."
            ),
        )

    # Check types
    validate_item_type(
        item=parsed_obj,
        category=category,
        subtype=subtype
    )

    # Everything good, return item
    is_seed = (record_type == RecordType.SEED_ITEM)

    # Check if item is locked
    try:
        locked = get_lock_status(
            id=id,
            config=config
        )
    except HTTPException as he:
        raise HTTPException(
            status_code=he.status_code,
            detail=f"Failed to check if locked. Error: {he.detail}."
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error occurred. Failed to check if locked.  Error: {e}."
        )

    return GenericFetchResponse(
        status=Status(
            success=True, details=f"Successfully retrieved {'seed' if is_seed else 'complete'} item and parsed into current data model."),
        roles=roles,
        item=parsed_obj,
        item_is_seed=is_seed,
        locked=locked
    )


def revert_item_helper(
        id: str,
        history_id: int,
        reason: str,
        correct_category: ItemCategory,
        correct_subtype: ItemSubType,
        domain_info_type: Type[item_domain_info_type],
        item_model_type: Type[item_base_type],
        available_roles: Roles,
        user: User,
        config: Config,
        service_proxy: bool = False
) -> ItemRevertResponse:
    # Try to read the raw item with given key from registry
    try:
        raw_item: Dict[str, Any] = get_entry_raw(id=id, config=config)
    # The item wasn't present
    except KeyError as e:
        return ItemRevertResponse(
            status=Status(
                success=False, details=f"Could not find the given key ({id}) in the registry.")
        )
    # Error occurred which was caught and handled in fastAPI format
    except HTTPException as e:
        raise e
    # Unknown error occurred
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"An unexpected error occurred while reading from the registry: {e}.")

    # since the item exists, let's now check that the user should be able to update it
    roles = describe_access_helper(
        id=id,
        config=config,
        user=user,
        available_roles=available_roles,
        # don't look it up again - we already know it's present
        already_checked_existence=True,
        # user groups are looked up differently if we are in service proxy mode
        service_proxy=service_proxy
    ).roles

    authorised = evaluate_user_access(
        user_roles=roles,
        # requires any of the edit action roles to enable an update
        acceptable_roles=EDIT_ACTION_ACCEPTED_ROLES
    )

    if not authorised:
        raise HTTPException(
            status_code=401,
            detail=f"You are not authorised to edit the item ({id=})."
        )

    # status of item can be either a blank seed or a complete item
    try:
        record_type, record = parse_unknown_record_type(
            raw_item=raw_item,
            item_model_type=item_model_type
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Item with id {id} is neither a seed item nor a valid entry. Not sure how to handle this item. Aborting.")

    # Check that the category matches
    try:
        validate_item_type(
            item=record, category=correct_category, subtype=correct_subtype)
    except Exception as e:
        return ItemRevertResponse(status=Status(
            success=False,
            details=f"The existing item is a valid item, but has a different subtype or category than the specified subroute. Ensure the item is the correct type."
        ))

    # seed items cannot be reverted to a previous version
    if record_type == RecordType.SEED_ITEM:
        raise HTTPException(
            status_code=400,
            detail=f"You cannot revert a seed item to a previous version. The item with id {id} is not a complete item."
        )

    # Get creation date and categories
    created_timestamp = record.created_timestamp

    # determine appropriate history
    history: List[HistoryEntry] = []

    # should be complete item
    assert isinstance(record, ItemBase)

    # find the new domain info from existing
    existing_history = record.history

    # mypy doesn't like this - just ignore - we validate the contents anyway
    revert_point: Optional[  # type: ignore
        HistoryEntry[domain_info_type]] = None

    for entry in existing_history:
        if entry.id == history_id:
            revert_point = entry

    if revert_point is None:
        raise HTTPException(
            status_code=400,
            detail=f"The item with id {id} does not have a history entry with id matching {history_id}. No action taken."
        )

    # we have found the revert point - now validate it is a good domain info
    try:
        # ensure we can parse this historical item as valid domain info
        domain_info_type.parse_obj(py_to_dict(revert_point.item))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"The historical entry for item with id {id} and history entry id {history_id} had contents which could not be parsed against the current data model. Please contact an administrator."
        )

    # now perform proper validation
    if config.perform_validation:
        validate_resp = validate_item_helper(
            item=revert_point.item,  # type: ignore
            desired_category=correct_category,
            desired_subtype=correct_subtype,
            json_schema_override=None,
            config=config
        )

        if not validate_resp.status.success:
            return ItemRevertResponse(
                status=validate_resp.status
            )

    # we have a valid past entry to revert to - create new history entry
    history = [
        create_revert_history(
            username=user.username, history_id=history_id, item_domain_info=revert_point.item, reason=reason, previous_history=existing_history)
    ] + existing_history

    # Construct new complete object using record info
    # from existing record, and domain and other item info
    # from the domain specialised item
    assert revert_point
    new_item = item_model_type(
        # record info
        id=id,
        # the owner's username
        owner_username=record.owner_username,
        created_timestamp=created_timestamp,
        updated_timestamp=get_timestamp(),
        record_type=RecordType.COMPLETE_ITEM,
        # Retain workflow links
        workflow_links=record.workflow_links,
        # Don't change any versioning info, if present
        versioning_info=record.versioning_info,
        history=history,
        # domain info - this is replaced
        **revert_point.item.dict()  # type: ignore
    )

    # The provided item is in the store, with a matching ID, let's update it
    friendly_format = py_to_dict(new_item)

    try:
        write_registry_dynamo_db_entry_raw(
            registry_item=friendly_format,
            config=config
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Something went wrong when trying to write the updated item. Details: {e}"
        )

    return ItemRevertResponse(
        status=Status(
            success=True,
            details=f"Successfully reverted item {id} to v{history_id}."
        )
    )


@dataclass
class VersionHelperResponse():
    new_handle_id: str
    version_number: int
    new_item: Any


async def version_helper(
        id: str,
        reason: str,
        item_model_type: Type[item_base_type],
        domain_info_type: Type[item_domain_info_type],
        correct_category: ItemCategory,
        correct_subtype: ItemSubType,
        available_roles: Roles,
        default_roles: Roles,
        user: User,
        config: Config,
        service_proxy: bool = False
) -> VersionHelperResponse:
    """

    Creates a new version of an existing item, checking the authorisation and
    other constraints.

    Parameters
    ----------
    id : str
        The id of the item to version
    reason : str
        Reason for update
    item_model_type : Type[item_base_type]
        The item model type
    domain_info_type : Type[item_domain_info_type]
        The domain info model type
    correct_category : ItemCategory
        The category for item
    correct_subtype : ItemSubType
        The subtype to validate
    available_roles : Roles
        The roles available for the new item
    default_roles : Roles
        The default roles for the new item
    user : User
        The user to do this for
    config : Config
        Config
    service_proxy : bool, optional
        True if this is a proxy route, doesn't rely on user token, by default
        False

    Returns
    -------
    VersionHelperResponse
        Response including the new ID etc
    """
    # Try to read the raw item with given key from registry
    try:
        raw_item: Dict[str, Any] = get_entry_raw(id=id, config=config)
    # The item wasn't present
    except KeyError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Could not find the given key ({id}) in the registry."
        )
    # Error occurred which was caught and handled in fastAPI format
    except HTTPException as e:
        raise e
    # Unknown error occurred
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"An unexpected error occurred while reading from the registry: {e}.")

    # since the item exists, let's now check that the user should be able to update it
    roles = describe_access_helper(
        id=id,
        config=config,
        user=user,
        available_roles=available_roles,
        # don't look it up again - we already know it's present
        already_checked_existence=True,
        # user groups are looked up differently if we are in service proxy mode
        service_proxy=service_proxy
    ).roles

    authorised = evaluate_user_access(
        user_roles=roles,
        # Must be admin of item to perform version
        acceptable_roles=AUTH_ADMIN_ACCEPTED_ROLES
    )

    if not authorised:
        raise HTTPException(
            status_code=401,
            detail=f"You are not authorised to revise the item ({id=})."
        )

    # status of item must be a complete item
    try:
        record_type, record = parse_unknown_record_type(
            raw_item=raw_item,
            item_model_type=item_model_type
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Item with id {id} is neither a seed item nor a valid entry. Not sure how to handle this item. Aborting.")

    if record_type != RecordType.COMPLETE_ITEM:
        raise HTTPException(
            status_code=400,
            detail=f"Item with id {id} is a Seed Item. Cannot create version of seed items.")

    # Check that the category/subtype matches
    try:
        validate_item_type(
            item=record, category=correct_category, subtype=correct_subtype)
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"The existing item is a valid item, but has a different subtype or category. These fields cannot be modified."
        )

    # Check status of existing item is okay
    if record.versioning_info is None:
        raise HTTPException(
            status_code=500,
            detail=f"Versioning cannot proceed as versioning enabled item has no versioning info!"
        )

    if record.versioning_info.next_version is not None:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot create a new version for an item ({id=}) which is not the latest version. Next version {record.versioning_info.next_version} already exists!"
        )

    # parse into domain info item
    existing_domain_info = domain_info_type.parse_obj(py_to_dict(record))

    # create initial history entry
    history = [create_seed_history(
        username=user.username, item_domain_info=existing_domain_info, from_ver=id)]

    # Construct new complete object based on existing
    new_item = item_model_type.parse_obj(py_to_dict(record))

    # Update some fields which change
    ts = get_timestamp()
    new_item.created_timestamp = ts
    new_item.updated_timestamp = ts

    # Potentially update the owner
    new_item.owner_username = user.username

    # Reset workflow info
    new_item.workflow_links = WorkflowLinks()

    # Update the versioning parameters
    assert new_item.versioning_info
    if new_item.versioning_info is None:
        raise HTTPException(
            status_code=500,
            detail=f"Versioning cannot proceed as versioning enabled item has no versioning info!"
        )
    else:
        # Pivot to using current record id as prev version, increment version
        # number, disassociate forward version
        new_info = VersioningInfo(
            previous_version=record.id,
            version=new_item.versioning_info.version + 1,
            next_version=None,
            # Reason must be provided for non V1 entries
            reason=reason
        )
        new_item.versioning_info = new_info

    # Update history of new item
    new_item.history = history

    # New item is ready to be created

    # Create a handle which points to <registry URL>/item/<handle>
    new_handle = await mint_self_describing_handle(config=config)

    # Update the new item with the minted handle
    new_item.id = new_handle

    # Find existing auth configuration from previous object
    existing_access_settings = get_item_from_auth_table(
        id=id, config=config).access_settings

    # write auth object first - this uses default roles
    seed_auth_configuration(
        id=new_handle,
        username=user.username,
        config=config,
        default_roles=default_roles,
        base_settings=existing_access_settings
    )

    # write lock object first
    seed_lock_configuration(
        id=new_handle,
        config=config,
    )

    # write the new version object to the registry
    friendly_format = py_to_dict(new_item)
    try:
        write_registry_dynamo_db_entry_raw(
            registry_item=friendly_format,
            config=config
        )
    # Raise 500 if something goes wrong
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to write revised item to registry. Aborting. Contact administrator. Error {e}."
        )

    # Now update the old item with the new forward version ID
    assert record.versioning_info
    record.versioning_info.next_version = new_handle

    # write the new version object to the registry
    friendly_format = py_to_dict(record)
    try:
        write_registry_dynamo_db_entry_raw(
            registry_item=friendly_format,
            config=config
        )
    # Raise 500 if something goes wrong
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update forward link to new version for existing item in the registry. Aborting. Contact administrator. Error {e}."
        )

    # Return the ID of the new handle
    return VersionHelperResponse(
        new_handle_id=new_handle,
        version_number=new_item.versioning_info.version,
        new_item=new_item
    )


@dataclass
class RetrieveItemResponse():
    status_response: Optional[StatusResponse] = None
    record: Optional[Union[ItemBase, SeededItem]] = None
    record_type: Optional[RecordType] = None


def retrieve_and_type_item(
        id: str,
        item_model_type: Type[item_base_type],
        correct_category: ItemCategory,
        correct_subtype: ItemSubType,
        config: Config,
) -> RetrieveItemResponse:
    # Try to read the raw item with given key from registry
    try:
        raw_item: Dict[str, Any] = get_entry_raw(id=id, config=config)
    # The item wasn't present
    except KeyError as e:
        return RetrieveItemResponse(
            status_response=StatusResponse(
                status=Status(
                    success=False, details=f"Could not find the given key ({id}) in the registry.")
            ))
    # Error occurred which was caught and handled in fastAPI format
    except HTTPException as e:
        raise e
    # Unknown error occurred
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"An unexpected error occurred while reading from the registry: {e}.")

    # status of item can be either a blank seed or a complete item
    try:
        record_type, record = parse_unknown_record_type(
            raw_item=raw_item,
            item_model_type=item_model_type
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Item with id {id} is neither a seed item nor a valid entry. Not sure how to handle this item. Aborting.")

    # Check that the category matches
    try:
        validate_item_type(
            item=record, category=correct_category, subtype=correct_subtype)
    except Exception as e:
        return RetrieveItemResponse(
            status_response=StatusResponse(status=Status(
                success=False,
                details=f"The existing item is a valid item, but has a different subtype or category."
            )))

    return RetrieveItemResponse(
        record_type=record_type,
        record=record
    )


def update_item_helper(
        id: str,
        record: Union[ItemBase, SeededItem],
        record_type: RecordType,
        replacement_domain_info: DomainInfoBase,
        reason: Optional[str],
        item_model_type: Type[item_base_type],
        available_roles: Roles,
        user: User,
        config: Config,
        service_proxy: bool = False,
        exclude_history_update: bool = False,
        manual_grant: bool = False
) -> ItemBase:
    """    update_item_helper
        Updates the given item using the domain specific information. The item
        model type is a class (not an instance) and represents the type of
        object that we are trying to upload/update.

        Arguments
        ----------
        id : str
            The id of the record to replace.
        replacement_domain_info : DomainInfoBase
            The item domain information to overwrite in the existing record.
        item_model_type : Type[item_base_type]
            The model type which is being uploaded.
        record: ItemBase | SeededItem
            The already fetched record of either type
        record_type: RecordType
            Which type of record?
        exclude_history_update: bool , optional
            For excluding the history update. This should be true iff
            informaiton being updated is not user editable information and
            therefore should not constitue a new (loose) "version" for the user
            to view. This is set to true if release information is updating
            during a release process.
        manual_grant: bool
            If the authorised client (i.e. the data store API / prov store API)
            has additional info about the user/context which means the normal
            auth checks should be bypassed, this flag can be used


        Returns
        -------
         : StatusResponse
            Was the action successful.

        Raises
        ------
        HTTPException
            HTTP exceptions are raised for various possible errors.

        See Also (optional)
        --------

        Examples (optional)
        --------
    """
    # since the item exists, let's now check that the user should be able to update it
    roles = describe_access_helper(
        id=id,
        config=config,
        user=user,
        available_roles=available_roles,
        # don't look it up again - we already know it's present
        already_checked_existence=True,
        # user groups are looked up differently if we are in service proxy mode
        service_proxy=service_proxy,
        # add the manual granted roles if applicable
    ).roles

    authorised = evaluate_user_access(
        user_roles=roles,
        # requires any of the edit action roles to enable an update
        acceptable_roles=EDIT_ACTION_ACCEPTED_ROLES
    ) or manual_grant

    if not authorised:
        raise HTTPException(
            status_code=401,
            detail=f"You are not authorised to edit the item ({id=})."
        )

    # Get creation date and categories
    created_timestamp = record.created_timestamp

    # determine appropriate history
    history: List[HistoryEntry] = []
    if record_type == RecordType.SEED_ITEM:
        # create initial history entry
        history = [create_seed_history(
            username=user.username, item_domain_info=replacement_domain_info)]
    else:
        assert isinstance(record, ItemBase)
        if not exclude_history_update:
            if reason is None:
                raise HTTPException(
                    status_code=400,
                    detail=f"Cannot update item {id} as no reason was provided and this item is not a seed item. Please provide a reason for this update."
                )
            # prepend history due to update of existing complete item
            history = [
                create_update_history(
                    username=user.username, item_domain_info=replacement_domain_info, reason=reason, previous_history=record.history)
            ] + record.history
        else:  # exclude history update and use existing.
            history = record.history

    # Construct new complete object using record info from existing record, and
    # domain and other item info from the domain specialised item
    new_item = item_model_type(
        # record info
        id=id,
        # the owner's username
        owner_username=record.owner_username,
        created_timestamp=created_timestamp,
        updated_timestamp=get_timestamp(),
        record_type=RecordType.COMPLETE_ITEM,
        # retain the workflow links
        workflow_links=record.workflow_links,
        # Don't change any versioning info
        versioning_info=record.versioning_info,
        # Updated hisotry
        history=history,
        # domain info
        **replacement_domain_info.dict()
    )

    # The provided item is in the store, with a matching ID, let's update it
    friendly_format = py_to_dict(new_item)

    try:
        write_registry_dynamo_db_entry_raw(
            registry_item=friendly_format,
            config=config
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Something went wrong when trying to write the updated item. Details: {e}"
        )

    return new_item


def create_seed_history(
    username: str,
    item_domain_info: DomainInfoBase,
    from_ver: Optional[str] = None
) -> HistoryEntry:
    return HistoryEntry(
        id=0,
        timestamp=get_timestamp(),
        reason="Initial record creation" if from_ver is None else f"New version of existing item (id={from_ver}).",
        username=username,
        item=item_domain_info
    )


def create_update_history(
    username: str,
    item_domain_info: DomainInfoBase,
    reason: str,
    previous_history: List[HistoryEntry]
) -> HistoryEntry:
    previous_id = max(map(lambda h: h.id, previous_history))
    return HistoryEntry(
        id=previous_id + 1,
        timestamp=get_timestamp(),
        reason=reason,
        username=username,
        item=item_domain_info
    )


def create_revert_history(
    username: str,
    history_id: int,
    item_domain_info: DomainInfoBase,
    reason: str,
    previous_history: List[HistoryEntry]
) -> HistoryEntry:
    previous_id = max(map(lambda h: h.id, previous_history))
    return HistoryEntry(
        id=previous_id + 1,
        timestamp=get_timestamp(),
        reason=f"(Restoring to v{history_id}) " + reason,
        username=username,
        item=item_domain_info
    )


async def create_item_helper(
    item_domain_info: DomainInfoBase,
    item_model_type: Type[item_base_type],
    category: ItemCategory,
    subtype: ItemSubType,
    versioning_enabled: bool,
    default_roles: Roles,
    user: User,
    config: Config
) -> GenericCreateResponse:
    """    create_item_helper
        Creates a new item. The item will be pre-validated
        as an item of the correct type. But will need to validate
        that the category and subtype are also correct.
        TODO apply category/subtype validation at the model level.

        This methods adds a new item to the registry, including seeding
        the handle identity, updating the handle value to redirect
        properly, then adding the item to the registry with id=handle.

        Arguments
        ----------
        item : ItemBase
            The item - this will be a specialised subclass of ItemBase.
        category : ItemCategory
            The category that the item should be.
        subtype : ItemSubType
            The subtype that the item should be.

        Returns
        -------
         : GenericCreateResponse
            A create response - this will be parsed into specialised
            create response once handled.

        Raises
        ------
        HTTPException
            HTTP exception if minting fails, or writing fails.

        See Also (optional)
        --------

        Examples (optional)
        --------
    """

    # check the user has an email
    if user.email is None:
        raise HTTPException(
            status_code=400,
            detail=f"User does not have an email address. Item creation not possible."
        )

    # Create a handle which points to <registry URL>/item/<handle>
    handle = await mint_self_describing_handle(config=config)

    # write auth object first - this uses default roles
    seed_auth_configuration(
        id=handle,
        username=user.username,
        config=config,
        default_roles=default_roles
    )

    # write lock object first
    seed_lock_configuration(
        id=handle,
        config=config,
    )

    item = item_model_type(
        id=handle,
        owner_username=user.username,
        created_timestamp=get_timestamp(),
        updated_timestamp=get_timestamp(),
        history=[
            create_seed_history(
                username=user.username,
                item_domain_info=item_domain_info
            )
        ],
        # Let other functions handle instantiating this where required
        workflow_links=None,
        versioning_info=VersioningInfo(
            previous_version=None,
            version=1,
            next_version=None
            # No reason required for first entry
        ) if versioning_enabled else None,
        ** item_domain_info.dict(),
        record_type=RecordType.COMPLETE_ITEM
    )

    # write the object to the registry
    friendly_format = py_to_dict(item)
    try:
        write_registry_dynamo_db_entry_raw(
            registry_item=friendly_format,
            config=config
        )
    # Raise 500 if something goes wrong
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to write complete item to registry. Aborting. Contact administrator. Error {e}."
        )

    return GenericCreateResponse(
        status=Status(
            success=True, details="Successfully uploaded the complete item. Return item includes handle id."),
        created_item=item,
        # This is infilled later if required
        register_create_activity_session_id=None
    )


def validate_item_helper(
    item: DomainInfoBase,
    desired_category: ItemCategory,
    desired_subtype: ItemSubType,
    json_schema_override: Optional[Dict[str, Any]],
    config: Config
) -> StatusResponse:
    """    validate_item_helper
        Validates the item that is provided. Since validation already occurs
        at the API level through 422 unprocessable entity rejection, this
        method assumes that the fields etc are correct, and instead just
        checks the category and subtype.
        (code was commented but this doc strings remains. Does this mean the type is being
        checked by pydantic in the parsing of the item?)
        Arguments
        ----------
        item : ItemBase
            The item to validate.
        desired_category : ItemCategory
            The correct category
        desired_subtype : ItemSubType
            The correct subtype

        Returns
        -------
         : StatusResponse
            Success or failure

        See Also (optional)
        --------

        Examples (optional)
        --------
    """

    # Item specific validations
    validator_func: Optional[ValidatorFunc] = custom_type_validators.get(
        desired_subtype)

    # if specific validator is available and configured to use it
    if validator_func is not None:
        try:
            # then validate object
            validator_func(item, config)
        except Exception as e:
            return StatusResponse(
                status=Status(
                    success=False, details=f"Validation Error: {e}")
            )

    # if a json schema override was supplied, also validate against it
    if json_schema_override:
        try:
            validate(instance=item.dict(exclude_none=True),
                     schema=json_schema_override)
        except Exception as e:
            return StatusResponse(
                status=Status(
                    success=False, details=f"Validation of overriden JSON schema failed. Parsing error: {e}.")
            )

    # all other items don't currently need further validation than "pydantic parsing".
    return StatusResponse(
        status=Status(success=True, details=f"Validation successful.")
    )


def delete_item_helper(
    id: str,
    config: Config
) -> StatusResponse:
    """    delete_item_helper
        Simple helper function to remove an element with the
        given id. This doesn't care about type/subtype at this
        stage.
        TODO validate that the item being removed has the same
        type as this endpoint is dealing with.
        Arguments
        ----------
        id : str
            The id of the item to remove.
        Returns
        -------
         : StatusResponse
            True means no errors, may not mean that item existed.
        Raises
        ------
        HTTPException
            If something goes wrong in delete op.
        See Also (optional)
        --------
        Examples (optional)
        --------
    """
    try:
        delete_dynamo_db_entry(id=id, table=get_registry_table(config=config))
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to delete from the resource table, exception: {e}.")
    try:
        delete_dynamo_db_entry(id=id, table=get_auth_table(config=config))
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to delete from the auth table, exception: {e}.")
    try:
        delete_dynamo_db_entry(id=id, table=get_lock_table(config=config))
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to delete from the lock table, exception: {e}.")

    return StatusResponse(
        status=Status(success=True, details="Item deleted.")
    )


def general_list_items(
    table: Any,
    filter: QueryFilter
) -> List[Dict[str, Any]]:

    # apply filter and search dynamodb
    items: List[Dict[str, Any]] = list_all_items(
        table=table,
        filter=filter,
    )

    # Successfully sourced items.
    return items


def list_items_paginated(
    table: Any,
    sort_by: Optional[SortOptions],
    filter_by: Optional[FilterOptions],
    pagination_key: Optional[PaginationKey],
    page_size: int,
) -> Tuple[List[Dict[str, Any]], Optional[PaginationKey]]:

    # apply filter and search dynamodb
    (items, new_pagination_key) = query_dbb(
        table=table,
        sort_by=sort_by,
        filter_by=filter_by,
        pagination_key=pagination_key,
        page_size=page_size,
    )

    # Successfully sourced items.
    return (items, new_pagination_key)


def list_items_paginated_and_filter(
    config: Config,
    sort_by: Optional[SortOptions],
    filter_by: Optional[FilterOptions],
    pagination_key: Optional[PaginationKey],
    page_size: int,
    protected_roles: ProtectedRole,
) -> Tuple[List[Dict[str, Any]], Optional[Dict[str, Any]]]:

    # get the paginated item list using a ddb query
    items, returned_pagination_key = list_items_paginated(
        table=get_registry_table(config=config),
        sort_by=sort_by,
        filter_by=filter_by,
        pagination_key=pagination_key,
        page_size=page_size,
    )

    if config.enforce_user_auth:
        # filter items based on access
        user = protected_roles.user

        # get user groups once
        user_group_id_set = get_user_group_id_set(
            user=user,
            config=config
        )

        def item_permission_filter(item: Dict[str, Any]) -> bool:
            # check that the item at least has an ID
            if 'id' not in item:
                # we can't evaluate access if no id is present
                return False

            # pull out the item ID
            id = item['id']

            # return true if access OK false otherwise this returns a list of roles
            # the user is allowed to take against this resource
            role_list = describe_access_helper(
                id=id,
                config=config,
                user=user,
                # use the fetch action roles as this is all we need
                available_roles=FETCH_ACTION_ACCEPTED_ROLES,
                already_checked_existence=True,
                user_group_ids=user_group_id_set
            ).roles

            # requires one of the acceptable fetch roles - filter based on this
            # response
            return evaluate_user_access(
                user_roles=role_list,
                acceptable_roles=FETCH_ACTION_ACCEPTED_ROLES
            )

        # filter items to only return visible items based on access roles and count
        # how many removed
        items = list(
            filter(lambda item: item_permission_filter(item), items))

    return items, returned_pagination_key


def get_user_group_id_set(user: User, config: Config, service_proxy: bool = False) -> Set[str]:
    # otherwise, get the groups of the user and check access for each protection
    # type at each level
    try:
        # depending on if service proxy mode, either make a user token request
        # or service token request asking by username
        if service_proxy:
            user_groups = get_proxy_user_groups(user=user, config=config)
        else:
            user_groups = get_user_groups(user=user, config=config)
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while trying to fetch the users group membership. Access denied. Error: {e}."
        )

    return set([group.id for group in user_groups])


def describe_access_helper(
    id: str,
    config: Config,
    user: User,
    available_roles: Roles,
    already_checked_existence: bool = False,
    user_group_ids: Optional[Set[str]] = None,
    service_proxy: bool = False,
) -> DescribeAccessResponse:

    # this is a flag to enable a skip of the existence check
    if not already_checked_existence:
        # check that the item exists in main registry
        try:
            _ = get_entry_raw(id=id, config=config)
        # The item wasn't present
        except KeyError as e:
            raise HTTPException(
                status_code=400,
                detail=f"Item ({id=}) was not present in the registry. Are you sure the id is correct?"
            )
        except HTTPException as he:
            raise he
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Unexpected error occurred while trying to fetch item."
            )
    # if the config specifies bypassing auth
    if not config.enforce_user_auth:
        return DescribeAccessResponse(
            roles=available_roles
        )

    # if the user is admin - always return all roles
    if user_is_admin(user):
        return DescribeAccessResponse(
            roles=available_roles
        )

    # lookup the item in the auth table
    try:
        auth_table_entry = get_item_from_auth_table(
            id=id,
            config=config
        )
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while trying to fetch the authorisation configuration of the object. Access denied. Error: {e}."
        )

    access_settings = auth_table_entry.access_settings

    # if owner, then return all access for all protection types
    if auth_table_entry.access_settings.owner == user.username:
        # the user is the owner - return all access for all protection types
        return DescribeAccessResponse(
            roles=available_roles
        )

    # if the user groups are already fetched, all good, otherwise, get them
    if user_group_ids is None:
        try:
            user_group_ids = get_user_group_id_set(
                user=user,
                config=config,
                service_proxy=service_proxy
            )
        except HTTPException as he:
            raise he
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"An error occurred while trying to fetch the users group membership. Access denied. Error: {e}."
            )

    # this is a list of roles the user can apply against this particular resource
    roles: Roles = determine_user_access(
        access_settings=access_settings,
        user_group_ids=user_group_ids
    )

    # conservatively limit this role list to only available roles
    roles = list(filter(lambda role: role in available_roles, roles))

    # return the determined access
    return DescribeAccessResponse(
        roles=roles
    )


def check_raw_item_subtype(
    id: str,
    item: dict[str, Any],
    expected_subtype: ItemSubType,
    item_model: Type[item_base_type]
) -> None:
    """ensures the id supplied points to an item of the expected subtype. Where the expected subtype is given by the route
    in which this function is called.

    Args:
        id (str): id of recieved by the api
        item (dict[str, Any]): the item the id points to
        expected_subtype (ItemSubType): the expected subtype the item should conform to
        item_model (Type[item_base_type]): the correct item model (complete) used to parse the raw item

    Raises:
        Exception: _description_
        HTTPException: 500. If the the item has the correct field value for item_subtype but cannot be parsed. 
            This could happen if the models are updated with new fields and items are not migrated.
        HTTPException: 400. If the item cannot be parsed using the item model and does not have the correct subtype either. (Most likely cause for failure)
        HTTPException: 400. If the item can be parsed using the item model but does not have the correct item_subtype field.
    """

    try:
        parsed_item: Union[SeededItem, item_base_type]
        # if complete item, can use the full model to parse the item
        if item['record_type'] == RecordType.COMPLETE_ITEM:
            parsed_item = item_model.parse_obj(item)
        # if seed item, use the seed model to parse the item - otherwise the complete model will fail
        elif item['record_type'] == RecordType.SEED_ITEM:
            parsed_item = SeededItem.parse_obj(item)
        else:
            raise Exception(f"Unhandled record type: {item['record_type']}")
    # item could not be parsed correctly
    except Exception as e:
        # check if subtype field is correct potentially meaning item is of an old format
        if expected_subtype == item["item_subtype"]:
            raise HTTPException(
                status_code=500,
                detail=f'''Failed to parse item of subtype {item['item_subtype']} with the associated route's subtype pydanctic model of {expected_subtype}. Does the stored item have an old format? Error: {e}.'''
            )
        # else, couldnt be parsed and not the correct subtype field, most likely user is using the wrong endpoint.
        else:
            raise HTTPException(
                status_code=400,
                detail=f'''Failed to parse item with the associated route's subtype model of {expected_subtype}. Are you using the correct endpoint route for id {id} pointing to an item subtype of {item['item_subtype']}? Error: {e}.'''
            )

    # this should rarely happen as discrepancy likely to be caught in parsing
    # Maybe 2 items have similar format resulting in successful parsing -> Check field too.
    if parsed_item.item_subtype != expected_subtype:
        raise HTTPException(
            status_code=400,
            detail=f'''Fetched item with handle {(id)} has item subtype of {parsed_item.item_subtype} but expected {expected_subtype}. Are you using the correct endpoint route for {parsed_item.item_subtype}'s?.'''
        )


def get_and_check_access_settings_helper(
    id: str,
    config: Config,
    available_roles: Roles,
    user: User,
    expected_subtype: ItemSubType,
    item_model: Type[item_base_type]
) -> AccessSettings:

    # check that the item exists in main registry
    try:
        item = get_entry_raw(id=id, config=config)
    # The item wasn't present
    except KeyError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Item ({id=}) was not present in the registry. Are you sure the id is correct?"
        )
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error occurred while trying to fetch the ID from the main registry."
        )

    # lookup the item in the auth table
    try:
        auth_table_entry = get_item_from_auth_table(
            id=id,
            config=config
        )
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while trying to fetch the authorisation configuration of the object. Access denied. Error: {e}."
        )

    is_authorised = False
    access_settings = auth_table_entry.access_settings

    # if owner or registry admin, then return config - or if config bypasses auth
    if not config.enforce_user_auth or user_is_admin(user) or auth_table_entry.access_settings.owner == user.username:
        # the user is the owner - return all access for all protection types
        is_authorised = True

    if not is_authorised:
        # get the groups that the user is in
        try:
            user_group_ids = get_user_group_id_set(
                user=user,
                config=config
            )
        except HTTPException as he:
            raise he
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"An error occurred while trying to fetch the users group membership. Access denied. Error: {e}."
            )

        # this is a list of roles the user can apply against this particular resource
        roles: Roles = determine_user_access(
            access_settings=access_settings,
            user_group_ids=user_group_ids
        )

        # conservatively limit this role list to only available roles
        roles = list(filter(lambda role: role in available_roles, roles))

        # evaluate access to see if admin
        is_authorised = evaluate_user_access(
            user_roles=roles,
            acceptable_roles=AUTH_ADMIN_ACCEPTED_ROLES
        )

    if not is_authorised:
        raise HTTPException(
            status_code=401,
            detail=f"You are not authorised to view the access configuration for item {id=}."
        )
    # user is authorised, check subtype
    # throws HTTPExceptions
    check_raw_item_subtype(
        id=id, item=item, expected_subtype=expected_subtype, item_model=item_model)

    # Authorised and correct type - return the settings object
    return access_settings


def check_and_update_access_settings_helper(
    id: str,
    new_access_settings: AccessSettings,
    config: Config,
    available_roles: Roles,
    user: User,
    expected_subtype: ItemSubType,
    item_model: Type[item_base_type]
) -> None:
    # check that the item exists in main registry
    try:
        item = get_entry_raw(id=id, config=config)
    # The item wasn't present
    except KeyError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Item ({id=}) was not present in the registry. Are you sure the id is correct?"
        )
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error occurred while trying to fetch the ID from the main registry."
        )

    # lookup the item in the auth table
    try:
        auth_table_entry = get_item_from_auth_table(
            id=id,
            config=config
        )
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while trying to fetch the authorisation configuration of the object. Access denied. Error: {e}."
        )

    current_access_settings = auth_table_entry.access_settings

    authorised = False

    # if owner or registry admin, then return config - or if config bypasses auth
    if not config.enforce_user_auth or user_is_admin(user) or auth_table_entry.access_settings.owner == user.username:
        # the user is the owner - return all access for all protection types
        authorised = True

    # get the groups that the user is in if they don't own the resource
    if not authorised:
        try:
            user_group_ids = get_user_group_id_set(
                user=user,
                config=config
            )
        except HTTPException as he:
            raise he
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"An error occurred while trying to fetch the users group membership. Access denied. Error: {e}."
            )

        # this is a list of roles the user can apply against this particular resource
        roles: Roles = determine_user_access(
            access_settings=current_access_settings,
            user_group_ids=user_group_ids
        )

        # conservatively limit this role list to only available roles
        roles = list(filter(lambda role: role in available_roles, roles))

        # evaluate access to see if admin
        authorised = evaluate_user_access(
            user_roles=roles,
            acceptable_roles=AUTH_ADMIN_ACCEPTED_ROLES
        )

    if not authorised:
        raise HTTPException(
            status_code=401,
            detail=f"You are not authorised to edit the access configuration for item {id=}."
        )

    # the user is authorised to put the new access configuration, check subtype
    # throws HTTPExceptions
    check_raw_item_subtype(
        id=id, item=item, expected_subtype=expected_subtype, item_model=item_model)

    # check that it doesnt change the owner
    if current_access_settings.owner != new_access_settings.owner:
        raise HTTPException(
            status_code=400,
            detail=f"The owner of a resource cannot be changed. Old: {current_access_settings.owner}, New: {new_access_settings.owner}."
        )

    # check that all the roles are within the available roles
    proposed_roles = set(new_access_settings.general)
    for _, roles in new_access_settings.groups.items():
        proposed_roles.update(roles)

    available_role_set = set(available_roles)

    diff = proposed_roles - available_role_set

    if len(diff) != 0:
        # there are roles in the proposed set which are not in the available set for this item type
        raise HTTPException(
            status_code=400,
            detail=f"Inappropriate roles are being added to the role configuration - ensure these roles are available for the resource type. Invalid roles: {diff}. Available roles: {available_role_set}."
        )

    # all proposed roles are valid, the owner hasn't changed, all is well

    # produce new entry
    auth_entry = AuthTableEntry(
        id=id,
        access_settings=new_access_settings
    )

    # write entry
    write_auth_table_entry(
        auth_entry=auth_entry,
        config=config
    )


def lock_resource_route_helper(
    lock_request: LockChangeRequest,
    config: Config,
    user: User,
    available_roles: Roles,
    expected_subtype: ItemSubType,
    item_model: Type[item_base_type]
) -> None:
    # Requires general write, and resource admin permission

    # fetch the lock metadata based on id
    try:
        lock_item: LockTableEntry = get_item_from_lock_table(
            id=lock_request.id,
            config=config
        )
    except KeyError as e:  # handle not in table.
        raise HTTPException(
            status_code=400,
            detail=f"Failed to retrieve ID {lock_request.id} from the lock table, are you sure it exists?"
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        raise Exception(
            f"Something unexpected went wrong during resource data retrieval. Error: {e}")

    # now make sure the user is allowed to lock the resource
    roles = describe_access_helper(
        id=lock_request.id,
        config=config,
        user=user,
        available_roles=available_roles,
        # don't look it up again - we already know it's present
        already_checked_existence=True
    ).roles

    # the user can lock the resource iff they have at least one of the
    # acceptable roles
    access = evaluate_user_access(
        user_roles=roles, acceptable_roles=AUTH_ADMIN_ACCEPTED_ROLES)

    if not access:
        raise HTTPException(
            status_code=401,
            detail=f"You are not authorised to lock this item."
        )

    # throws HTTPExceptions
    check_raw_item_subtype(
        id=lock_item.id, item=get_entry_raw(id=lock_item.id, config=config), expected_subtype=expected_subtype, item_model=item_model)

    # update the lock
    lock_item.lock_information = apply_lock(
        lock_information=lock_item.lock_information,
        reason=lock_request.reason,
        user=user
    )

    # Write the udpated info
    try:
        write_lock_table_entry(
            lock_entry=lock_item,
            config=config
        )
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to write updated lock configuration to lock table. Error: {e}. Contact admin."
        )


def unlock_resource_route_helper(
    unlock_request: LockChangeRequest,
    config: Config,
    user: User,
    available_roles: Roles,
    expected_subtype: ItemSubType,
    item_model: Type[item_base_type]
) -> None:
    # Requires general write, and resource admin permission

    # fetch the lock metadata based on id
    try:
        lock_item: LockTableEntry = get_item_from_lock_table(
            id=unlock_request.id,
            config=config
        )
    except KeyError as e:  # handle not in table.
        raise HTTPException(
            status_code=400,
            detail=f"Failed to retrieve ID {unlock_request.id} from the lock table, are you sure it exists?"
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        raise Exception(
            f"Something unexpected went wrong during resource data retrieval. Error: {e}")

    # now make sure the user is allowed to lock the resource
    roles = describe_access_helper(
        id=unlock_request.id,
        config=config,
        user=user,
        available_roles=available_roles,
        # don't look it up again - we already know it's present
        already_checked_existence=True
    ).roles

    # the user can lock the resource iff they have at least one of the
    # acceptable roles
    access = evaluate_user_access(
        user_roles=roles, acceptable_roles=AUTH_ADMIN_ACCEPTED_ROLES)

    if not access:
        raise HTTPException(
            status_code=401,
            detail=f"You are not authorised to lock this item."
        )

    # throws HTTPExceptions
    check_raw_item_subtype(
        id=lock_item.id, item=get_entry_raw(id=lock_item.id, config=config), expected_subtype=expected_subtype, item_model=item_model)

    # update the lock
    lock_item.lock_information = apply_unlock(
        lock_information=lock_item.lock_information,
        reason=unlock_request.reason,
        user=user
    )

    # Write the udpated info
    try:
        write_lock_table_entry(
            lock_entry=lock_item,
            config=config
        )
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to write updated lock configuration to lock table. Error: {e}. Contact admin."
        )


def lock_history_route_helper(
    id: str,
    config: Config,
    user: User,
    available_roles: Roles,
) -> LockHistoryResponse:
    # Requires general read + resource metadata read

    # fetch the lock metadata based on id
    try:
        lock_item: LockTableEntry = get_item_from_lock_table(
            id=id,
            config=config
        )
    except KeyError as e:  # handle not in table.
        raise HTTPException(
            status_code=400,
            detail=f"Failed to retrieve ID {id} from the lock table, are you sure it exists?"
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        raise Exception(
            f"Something unexpected went wrong during resource data retrieval. Error: {e}")

    # now make sure the user is allowed to lock the resource
    roles = describe_access_helper(
        id=id,
        config=config,
        user=user,
        available_roles=available_roles,
        # don't look it up again - we already know it's present
        already_checked_existence=True
    ).roles

    # the user can read the lock history iff they have at least one of the
    # acceptable roles
    access = evaluate_user_access(
        user_roles=roles, acceptable_roles=FETCH_ACTION_ACCEPTED_ROLES)

    if not access:
        raise HTTPException(
            status_code=401,
            detail=f"You are not authorised to view the lock history of this item."
        )

    return LockHistoryResponse(
        status=Status(
            success=True, details=f"Successfully fetched the lock history"),
        history=lock_item.lock_information.history
    )


def lock_status_route_helper(
    id: str,
    config: Config,
    user: User,
    available_roles: Roles,
) -> LockStatusResponse:
    # Requires general read + resource metadata read

    # fetch the lock metadata based on id
    try:
        lock_item: LockTableEntry = get_item_from_lock_table(
            id=id,
            config=config
        )
    except KeyError as e:  # handle not in table.
        raise HTTPException(
            status_code=400,
            detail=f"Failed to retrieve ID {id} from the lock table, are you sure it exists?"
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        raise Exception(
            f"Something unexpected went wrong during resource data retrieval. Error: {e}")

    # now make sure the user is allowed to lock the resource
    roles = describe_access_helper(
        id=id,
        config=config,
        user=user,
        available_roles=available_roles,
        # don't look it up again - we already know it's present
        already_checked_existence=True
    ).roles

    # the user can read the lock history iff they have at least one of the
    # acceptable roles
    access = evaluate_user_access(
        user_roles=roles, acceptable_roles=FETCH_ACTION_ACCEPTED_ROLES)

    if not access:
        raise HTTPException(
            status_code=401,
            detail=f"You are not authorised to view the lock history of this item."
        )

    return LockStatusResponse(
        locked=lock_item.lock_information.locked
    )
