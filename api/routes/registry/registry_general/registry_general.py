from fastapi import APIRouter, Depends
from KeycloakFastAPI.Dependencies import ProtectedRole
from dependencies.dependencies import read_user_protected_role_dependency, read_write_user_protected_role_dependency, admin_user_protected_role_dependency
from ProvenaInterfaces.RegistryAPI import *
from ProvenaInterfaces.SharedTypes import VersionDetails
from ProvenaSharedFunctionality.Registry.RegistryRouteActions import PROV_SERVICE_ROLE_NAME, DATA_STORE_SERVICE_ROLE_NAME
from helpers.action_helpers import *
from helpers.action_helpers import list_items_paginated
from helpers.dynamo_helpers import get_entry_raw
from helpers.auth_helpers import special_permission_check
from helpers.lock_helpers import get_lock_status
from config import Config, get_settings

router = APIRouter()


@router.post("/list", response_model=PaginatedListResponse, operation_id="list")
async def list_registry_items(
    general_list_request: GeneralListRequest,
    config: Config = Depends(get_settings),
    protected_roles: ProtectedRole = Depends(
        read_user_protected_role_dependency)
) -> PaginatedListResponse:

    # deconstruct main payload
    filter_by = general_list_request.filter_by
    sort_by = general_list_request.sort_by
    pagination_key = general_list_request.pagination_key
    page_size = general_list_request.page_size

    items, returned_pagination_key = list_items_paginated_and_filter(
        config=config,
        sort_by=sort_by,
        filter_by=filter_by,
        pagination_key=pagination_key,
        page_size=page_size,
        protected_roles=protected_roles
    )

    # return unparsed items
    return PaginatedListResponse(
        status=Status(
            success=True,
            details="Searched database and returned items matching query."
        ),
        items=items,
        total_item_count=len(items),
        pagination_key=returned_pagination_key,
    )


@router.get("/fetch", response_model=UntypedFetchResponse, operation_id="fetch")
async def fetch_item(
    id: str,
    config: Config = Depends(get_settings),
    protected_roles: ProtectedRole = Depends(
        read_user_protected_role_dependency)
) -> UntypedFetchResponse:

    # Try an untyped lookup into dynamodb
    try:
        item = get_entry_raw(
            id=id,
            config=config
        )
    except KeyError as ke:
        # item can't be found
        return UntypedFetchResponse(
            status=Status(
                success=False,
                details=f'The id you specified was not available in the registry, error: {ke}.'
            )
        )

    # now make sure the user is allowed to read the contents of the item metadata
    roles = describe_access_helper(
        id=id,
        config=config,
        user=protected_roles.user,
        # only need this limited set of roles
        available_roles=FETCH_ACTION_ACCEPTED_ROLES,
        # don't look it up again - we already know it's present
        already_checked_existence=True
    ).roles

    # the user can fetch the record iff they have at least one of the acceptable roles
    access = evaluate_user_access(
        user_roles=roles, acceptable_roles=FETCH_ACTION_ACCEPTED_ROLES)

    if not access:
        raise HTTPException(
            status_code=401,
            detail=f"You are not authorised to fetch this item."
        )

    # Return item raw - don't parse
    return UntypedFetchResponse(
        status=Status(
            success=True,
            details="Successfully retrieved item from the registry."
        ),
        item=item
    )


@router.get("/proxy/fetch", response_model=UntypedFetchResponse, operation_id="proxy_fetch", include_in_schema=False)
async def proxy_fetch_item(
    id: str,
    username: str,
    config: Config = Depends(get_settings),
    protected_roles: ProtectedRole = Depends(
        read_user_protected_role_dependency)
) -> UntypedFetchResponse:
    # must have a role which matches the service accounts
    special_roles = [PROV_SERVICE_ROLE_NAME, DATA_STORE_SERVICE_ROLE_NAME]
    authorised = special_permission_check(
        user=protected_roles.user, special_roles=special_roles)

    if not authorised:
        raise HTTPException(
            status_code=401,
            detail=f"You are not authorised to take this action."
        )

    # update the user username
    user = protected_roles.user
    user.username = username

    # Try an untyped lookup into dynamodb
    try:
        item = get_entry_raw(
            id=id,
            config=config
        )
    except KeyError as ke:
        # item can't be found
        return UntypedFetchResponse(
            status=Status(
                success=False,
                details=f'The id you specified was not available in the registry, error: {ke}.'
            )
        )

    # now make sure the user is allowed to read the contents of the item metadata
    special_roles = describe_access_helper(
        id=id,
        config=config,
        user=user,
        # only need this limited set of roles
        available_roles=FETCH_ACTION_ACCEPTED_ROLES,
        # don't look it up again - we already know it's present
        already_checked_existence=True,
        # use service proxy style lookups
        service_proxy=True
    ).roles

    # the user can fetch the record iff they have at least one of the acceptable roles
    access = evaluate_user_access(
        user_roles=special_roles, acceptable_roles=FETCH_ACTION_ACCEPTED_ROLES)

    if not access:
        raise HTTPException(
            status_code=401,
            detail=f"You are not authorised to fetch this item."
        )

    # Return item raw - don't parse
    return UntypedFetchResponse(
        status=Status(
            success=True,
            details="Successfully retrieved item from the registry."
        ),
        item=item
    )


@router.delete(path="/delete",
               response_model=StatusResponse,
               operation_id='delete',
               include_in_schema=False
               )
async def delete_item(
    id: str,
    config: Config = Depends(get_settings),
    protected_roles: ProtectedRole = Depends(
        admin_user_protected_role_dependency)
) -> StatusResponse:
    """    delete_item
        Admin only endpoint which can be used to delete 
        objects from the registry. Delete is by ID. This
        endpoint will return successfully even if the object
        doesn't exist in the first place.

        Arguments
        ----------
        id : str
            The handle ID of the object to delete

        Returns
        -------
         : StatusResponse
            Was the deletion successful - returns true even if the item 
            did not exist.

        See Also (optional)
        --------

        Examples (optional)
        --------
    """
    try:
        locked = get_lock_status(
            id=id,
            config=config
        )
    except HTTPException as he:
        raise HTTPException(
            status_code=he.status_code,
            detail=f"Failed to check if locked. No access provided. Error: {he.detail}."
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error occurred. Failed to check if locked. No access provided. Error: {e}."
        )

    if locked:
        raise HTTPException(
            status_code=401,
            detail="Cannot perform this action as the resource is locked."
        )

    return delete_item_helper(
        id=id,
        config=config
    )


@router.get("/about/version", response_model=VersionDetails, operation_id="version")
async def get_provena_version(
    config: Config = Depends(get_settings),
    protected_roles: ProtectedRole = Depends(
        read_user_protected_role_dependency)
) -> VersionDetails:
    """    get_provena_version
        Returns the version of the registry

        Arguments
        ----------
        None

        Returns
        -------
         : VersionResponse
            The version response of the registry containing a status response and version details
        See Also (optional)
        --------

        Examples (optional)
        --------
    """

    try:
        return config.version_details
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve registry version details. Error: {e}"
        )
