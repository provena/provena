from fastapi import APIRouter, Depends, HTTPException
from KeycloakFastAPI.Dependencies import ProtectedRole
from SharedInterfaces.DataStoreAPI import *
from SharedInterfaces.RegistryAPI import DatasetDomainInfo, ItemRevertRequest, ItemRevertResponse
from SharedInterfaces.RegistryModels import METADATA_WRITE_ROLE, ADMIN_ROLE, DATASET_WRITE_ROLE
from config import get_settings, Config
from typing import cast
from dependencies.dependencies import read_write_user_protected_role_dependency
from dependencies.secret_cache import secret_cache
from helpers.metadata_helpers import validate_against_schema, validate_fields
from helpers.aws_helpers import construct_s3_path, update_metadata_at_s3, seed_s3_location_with_metadata
from helpers.registry_api_helpers import *
from helpers.registry_api_helpers import seed_dataset_in_registry, validate_dataset_in_registry
from helpers.util import py_to_dict
import json

router = APIRouter()

METADATA_WRITE_ROLES = [METADATA_WRITE_ROLE, DATASET_WRITE_ROLE, ADMIN_ROLE]


@router.post("/mint-dataset", response_model=MintResponse, operation_id="mint_dataset")
async def mint_dataset(
    collection_format: CollectionFormat,
    protected_roles: ProtectedRole = Depends(
        read_write_user_protected_role_dependency),
    config: Config = Depends(get_settings)
) -> MintResponse:
    """
    Function Description
    --------------------

    Used by the front end to prepare the data store, the handle service,
    metadata etc for a new dataset. Accepts the filled out metadata which must
    validate against the current dataset schema which is provided by the
    /dataset-schema endpoint.

    If the schema validates, then a handle will be minted, a handle endpoint
    will be formed and updated for the handle service, a S3 location will be
    determined, the metadata updated with these details and uploaded to that
    location to seed the folder structure. 

    This function returns the MintResponse which includes the status, the
    handle, the S3 location information.


    Arguments
    ----------
    collection_format : CollectionFormat
        The input pre-parsed using the pydantic input model validation. Still is
        validated using the json schema as well.
    group_id : Optional[str]
        The user can specify that they are registering this dataset as part of
        this group. If the user is not a member of this group, the endpoint will
        throw an error. If this value is not specified, the default general
        access will be provided along with the defaults for all groups that the
        user is a member of. If the group is provided, then only the default
        access of that group will be provided along with the default general
        visibility. By default, None.

    Returns
    -------
    MintResponse
        The mint response object which encodes the result if successful


    Raises
    ------
    HTTPException
        400 response if metadata fails to validate
    HTTPException
        400 response if the S3 location cannot be uniquely determined

    See Also (optional)
    --------

    Examples (optional)
    --------

    """
    # Validate metadata
    # have to do a workaround here to get serialised datetime for json schema
    json_data = json.loads(collection_format.json(exclude_none=True))
    valid_schema, failure_exception = validate_against_schema(
        json_data, config=config)

    # If invalid, then return with exception
    # TODO more informative response - error message is very long if exception is printed.
    if not valid_schema:
        return MintResponse(
            status=Status(
                success=False,
                details=f"Failed to validate metadata against schema. Error {str(failure_exception).splitlines()[0:3]}"
            )
        )

    try:
        validate_fields(collection_format)
    except Exception as e:
        return MintResponse(
            status=Status(
                success=False,
                details=f"Failed field value validation. Error: {e}"
            )
        )

    # Call the validate endpoint which also checks the IDs
    if config.REMOTE_PRE_VALIDATION:
        possible_error = validate_dataset_in_registry(
            collection_format=collection_format,
            user=protected_roles.user,
            config=config
        )

        if possible_error is not None:
            return MintResponse(
                status=Status(
                    success=False,
                    details=f"Registry API responded with an error during validation, error: {possible_error}."
                )
            )

    # Mint a new seed dataset item
    handle = seed_dataset_in_registry(
        secret_cache=secret_cache,
        # use the actual username in the proxy request
        proxy_username=protected_roles.user.username,
        config=config
    )

    # Work out S3 location
    try:
        s3_location: S3Location = construct_s3_path(
            collection_format=collection_format,
            handle=handle,
            use_handle_as_name=True,
            config=config
        )
    except Exception as e:
        raise HTTPException(status_code=400,
                            detail=f"Failed to find a unique S3 path - is your dataset name a duplicate? Error: {e}")

    # Seed S3 location with metadata file
    file_metadata = py_to_dict(collection_format)
    seed_s3_location_with_metadata(
        s3_location=s3_location,
        metadata=file_metadata,
        config=config
    )

    # we are ready to build the dataset item domain info
    domain_info = DatasetDomainInfo(
        display_name=collection_format.dataset_info.name,
        user_metadata=collection_format.dataset_info.user_metadata,
        collection_format=collection_format,
        s3=s3_location,
        release_status=ReleasedStatus.NOT_RELEASED,
        access_info_uri=collection_format.dataset_info.access_info.uri
    )

    # now we can update the seeded item to a complete item with the appropriate
    # details
    update_response = update_dataset_in_registry(
        domain_info=domain_info,
        # use the actual users username - this ensures that resource level auth
        # is enforced
        proxy_username=protected_roles.user.username,
        id=handle,
        # reason is not required in this case as it's just an update from seed
        # -> complete
        reason="NA",
        secret_cache=secret_cache,
        config=config
    )

    if update_response.register_create_activity_session_id is None:
        return MintResponse(
            status=Status(
                success=False,
                details="Successfully updated dataset, but no creation job was spun off. This is unexpected. Please contact an administrator. Your dataset may still function properly."
            ),
            handle=handle,
            s3_location=s3_location,
        )

    # Update the original item with the workflow link

    # Return information and status
    return MintResponse(
        status=Status(
            success=True,
            details="Successfully seeded location - see location details."
        ),
        handle=handle,
        s3_location=s3_location,
        register_create_activity_session_id=update_response.register_create_activity_session_id
    )


@router.post("/update-metadata", response_model=UpdateMetadataResponse, operation_id="update_metadata")
async def update_metadata(
    collection_format: CollectionFormat,
    handle_id: str,
    reason: str,
    protected_roles: ProtectedRole = Depends(
        read_write_user_protected_role_dependency),
    config: Config = Depends(get_settings)
) -> UpdateMetadataResponse:
    """    get_dataset_schema
        Given the metadata and handle id, will re-parse the metadata
        as valid ro crate, then overwrite the registry entry and 
        s3 bucket metadata.

        Will also update the timestamp of the updated_time to be 
        the current time.

        Arguments
        ----------
        collection_format : CollectionFormat
            The updated metadata
        handle_id : str
            The handle for which to update the metadata

        Returns
        -------
         : UpdateMetadataResponse
            The updated metadata response

        Raises
        ------
        HTTPException
            422 - validation failure against schema at API level
        HTTPException
            400 - validation failure against schema at JSON schema level
        HTTPException
            400 - failed to transform into ro crate
        HTTPException
            500 - failed to update registry 

        See Also (optional)
        --------

        Examples (optional)
        --------
    """

    # Validate metadata
    json_data = json.loads(collection_format.json(exclude_none=True))
    valid, failure_exception = validate_against_schema(
        json_data, config=config)

    # If invalid, then return with exception
    # TODO more informative response - error message is very long if exception is printed.
    if not valid:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to validate metadata against json schema.")

    try:
        validate_fields(collection_format)
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Failed field value validation. Error: {e}"
        )

    # Call the validate endpoint which also checks the IDs
    if config.REMOTE_PRE_VALIDATION:
        possible_error = validate_dataset_in_registry(
            collection_format=collection_format,
            user=protected_roles.user,
            config=config
        )

        if possible_error is not None:
            raise HTTPException(
                status_code=400,
                detail=f"Registry API responded with an error during validation, error: {possible_error}."
            )

    # get the current entry from the registry - if 401 then not authorised
    current_item_response = user_fetch_dataset_from_registry(
        id=handle_id,
        config=config,
        user=protected_roles.user
    )

    # check if locked
    if current_item_response.locked:
        raise HTTPException(
            status_code=401,
            detail=f"This dataset is locked - you cannot update the metadata. Unlock the dataset first."
        )

    # check that the user has permission to update this metadata. The fetch
    # response includes a set of item specific roles - check we have metadata
    # write.
    registry_item_roles = current_item_response.roles

    registry_item_metadata = current_item_response.item
    assert registry_item_metadata
    assert isinstance(registry_item_metadata, ItemDataset)

    if registry_item_roles is None:
        raise HTTPException(
            status_code=401,
            detail=f"Registry API did not include roles in fetch response - no access can be granted."
        )

    authorised = False
    for role in METADATA_WRITE_ROLES:
        if role in registry_item_roles:
            authorised = True
            break

    if not authorised:
        raise HTTPException(
            status_code=401,
            detail=f"You are not authorised to write metadata for this dataset!"
        )

    # this uses the service role - need to be sure we have access at this point
    update_dataset_in_registry(
        id=handle_id,
        # use the actual username - this ensures user auth is enforced at
        # resource level
        proxy_username=protected_roles.user.username,
        secret_cache=secret_cache,
        config=config,
        domain_info=DatasetDomainInfo(
            display_name=collection_format.dataset_info.name,
            user_metadata=collection_format.dataset_info.user_metadata,
            collection_format=collection_format,
            s3=registry_item_metadata.s3,
            # Put existing release status if any here.
            # TODO cofirm this works if there is no timestamp or approver in original registry_item_metadata.
            release_status=registry_item_metadata.release_status,
            release_timestamp=registry_item_metadata.release_timestamp,
            release_approver=registry_item_metadata.release_approver,
            release_history=registry_item_metadata.release_history,
            access_info_uri=collection_format.dataset_info.access_info.uri
        ),
        reason=reason
    )

    file_metadata = py_to_dict(collection_format)
    update_metadata_at_s3(
        s3_location=registry_item_metadata.s3,
        metadata=file_metadata,
        config=config
    )

    # Return information and status
    return UpdateMetadataResponse(
        status=Status(
            success=True,
            details="Successfully updated metadata in Registry and S3 bucket - see location details."
        ),
        handle=handle_id,
        s3_location=registry_item_metadata.s3
    )


@router.put("/revert-metadata", response_model=ItemRevertResponse, operation_id="revert_metadata")
async def revert_metadata(
    revert_request: ItemRevertRequest,
    protected_roles: ProtectedRole = Depends(
        read_write_user_protected_role_dependency),
    config: Config = Depends(get_settings)
) -> ItemRevertResponse:
    """

    Reverts the metadata for a dataset to a previous identified historical version.

    Args:
        revert_request (ItemRevertRequest): The revert request, passed through to the registry API.

    Raises:
        Throws a 400 error if the history ID does not exist or the dataset ID does not exist.
        Throws a 401 error if the user is not authorised to perform the update.

    Returns:
        ItemRevertResponse: Status response
    """

    # Get the current entry from the registry - if 401 then not authorised
    current_item_response = user_fetch_dataset_from_registry(
        id=revert_request.id,
        config=config,
        user=protected_roles.user
    )

    # check if locked
    if current_item_response.locked:
        raise HTTPException(
            status_code=401,
            detail=f"This dataset is locked - you cannot update the metadata. Unlock the dataset first."
        )

    # check that the user has permission to update this metadata. The fetch
    # response includes a set of item specific roles - check we have metadata
    # write.
    registry_item_roles = current_item_response.roles

    registry_item_metadata = current_item_response.item
    assert registry_item_metadata
    assert isinstance(registry_item_metadata, ItemDataset)

    if registry_item_roles is None:
        raise HTTPException(
            status_code=401,
            detail=f"Registry API did not include roles in fetch response - no access can be granted."
        )

    authorised = False
    for role in METADATA_WRITE_ROLES:
        if role in registry_item_roles:
            authorised = True
            break

    if not authorised:
        raise HTTPException(
            status_code=401,
            detail=f"You are not authorised to write metadata for this dataset!"
        )

    # get the desired historical entry
    revert_point: Optional[HistoryEntry[DatasetDomainInfo]] = None

    for entry in registry_item_metadata.history:
        if entry.id == revert_request.history_id:
            revert_point = entry

    if revert_point is None:
        raise HTTPException(
            status_code=400,
            detail=f"The item with id {revert_request.id} does not have a history entry with id matching {revert_request.history_id}. No action taken."
        )
    # get the metadata of the target revert point
    collection_format = revert_point.item.collection_format

    # Call the validate endpoint which also checks the IDs
    if config.REMOTE_PRE_VALIDATION:
        possible_error = validate_dataset_in_registry(
            collection_format=collection_format,
            user=protected_roles.user,
            config=config
        )

        if possible_error is not None:
            raise HTTPException(
                status_code=400,
                detail=f"Registry API responded with an error during validation of the target revert point, error: {possible_error}."
            )

    # don't perform revert operation, instead perform update operation - this
    # guarantees we don't modify any protected fields

    # Produce a new domain info which is the result of replacing the collection format in the existing domain info

    # Extract domain info from full existing item
    revised_domain_info = DatasetDomainInfo.parse_obj(
        py_to_dict(registry_item_metadata))

    # update the display name to match the dataset name since user's can't
    # control this field directly
    revised_domain_info.display_name = collection_format.dataset_info.name

    # Update the collection format
    revised_domain_info.collection_format = collection_format
    
    # update the user metadata
    revised_domain_info.user_metadata = collection_format.dataset_info.user_metadata

    # Update the uri, if any.
    revised_domain_info.access_info_uri = collection_format.dataset_info.access_info.uri


    update_dataset_in_registry(
        proxy_username=protected_roles.user.username,
        domain_info=revised_domain_info,
        id=revert_request.id,
        secret_cache=secret_cache,
        reason=f"Reverting dataset to history id {revert_request.history_id}.",
        config=config
    )

    file_metadata = py_to_dict(collection_format)
    update_metadata_at_s3(
        s3_location=registry_item_metadata.s3,
        metadata=file_metadata,
        config=config
    )

    # Return information and status
    return ItemRevertResponse(
        status=Status(
            success=True,
            details="Successfully reverted metadata in Registry and S3 bucket - see location details."
        )
    )


@router.post("/version", response_model=VersionResponse, operation_id="version_dataset")
async def version_dataset(
    version_request: VersionRequest,
    protected_roles: ProtectedRole = Depends(
        read_write_user_protected_role_dependency),
    config: Config = Depends(get_settings)
) -> VersionResponse:
    """

    Versioning operation which creates a new version from the specified ID.

    This requires write access to the registry, and ADMIN access for the
    specified item.

    This will always generate an asynchronous job which creates the
    Version activity and lodges the associated provenance.

    Importantly - this also performs the generation of the new S3 location from
    the revised item ID, and updates the S3Location field of the new item to
    refer to this new storage location.

    Parameters
    ----------
    version_request : VersionRequest
        The request which includes the item ID and reason for versioning

    Returns
    -------
    VersionResponse
        The response which is more or less relayed from the proxy version
        endpoint of the registry API

    Raises
    ------
    HTTPException
        400/401/500 from either internal or registry API error
    """
    # We have write metadata permission - just pass on username and let registry
    # manage auth on item level This also checks that the item is the correct
    # subtype - so we don't need to manage that
    version_response = version_dataset_in_registry(
        version_request=version_request,
        proxy_username=protected_roles.user.username,
        secret_cache=secret_cache,
        config=config,
    )

    # Pull out the new item information
    new_item_id = version_response.new_version_id

    # Get the current entry from the registry - if 401 then not authorised
    new_item_response = user_fetch_dataset_from_registry(
        id=new_item_id,
        config=config,
        user=protected_roles.user
    )

    # Can't be seed item - versioning not enabled for seed items
    new_item: ItemDataset = cast(ItemDataset, new_item_response.item)

    collection_format = new_item.collection_format

    # Validate the new metadata
    new_metadata = py_to_dict(collection_format)

    valid_schema, failure_exception = validate_against_schema(
        new_metadata, config=config)

    # If invalid, then return with exception
    # TODO more informative response - error message is very long if exception is printed.
    if not valid_schema:
        raise HTTPException(
            status_code=500,
            detail=f"New item ID {new_item_id}. Version succeeded, but resulting item had invalid metadata. S3 storage location is not provisioned and dataset may not function correctly. Please contact an administrator."
        )

    try:
        validate_fields(collection_format)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"New item ID {new_item_id}. Version succeeded, but resulting item had invalid metadata. S3 storage location is not provisioned and dataset may not function correctly. Please contact an administrator. Error: {e}."
        )

    # Work out S3 location
    try:
        s3_location: S3Location = construct_s3_path(
            collection_format=collection_format,
            handle=new_item.id,
            use_handle_as_name=True,
            config=config
        )
    except Exception as e:
        raise HTTPException(status_code=500,
                            detail=f"Version succeeded, however failed to find a unique S3 path. No storage location provisioned, dataset may not function properly. Error: {e}")

    # Seed S3 location with metadata file
    seed_s3_location_with_metadata(
        s3_location=s3_location,
        metadata=new_metadata,
        config=config
    )

    # We need to update the associated storage location of the versioned
    # dataset
    domain_info = DatasetDomainInfo(
        display_name=new_item.display_name,
        collection_format=collection_format,
        s3=s3_location,
        # new versions automatically unreleased.
        release_status=ReleasedStatus.NOT_RELEASED,
        access_info_uri=collection_format.dataset_info.access_info.uri
    )

    # now we can update the seeded item to a complete item with the appropriate
    # details
    update_dataset_in_registry(
        domain_info=domain_info,
        # use the actual users username - this ensures that resource level auth
        # is enforced
        proxy_username=protected_roles.user.username,
        id=new_item.id,
        reason="(System) Dataset S3 path updated to new version's storage location",
        secret_cache=secret_cache,
        config=config
    )

    # Return information and status
    return VersionResponse(
        new_version_id=new_item.id,
        version_job_session_id=version_response.version_job_session_id
    )
