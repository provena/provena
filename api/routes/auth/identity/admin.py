from fastapi import APIRouter, Depends
from KeycloakFastAPI.Dependencies import *
from dependencies.dependencies import *
from ProvenaInterfaces.AuthAPI import *
from config import Config, get_settings
from helpers.auth.username_person_link_service_helpers import *
from helpers.auth.registry_api_helpers import *

router = APIRouter(
    prefix="/admin"
)


@router.get("/lookup", response_model=AdminLinkUserLookupResponse, operation_id="admin_link_user_lookup")
async def lookup(
    username: str,
    config: Config = Depends(get_settings),
    roles: ProtectedRole = Depends(sys_admin_read_dependency)
) -> AdminLinkUserLookupResponse:
    """

    Looks up the specified username in the username person link service.

    Args:
        username (Optional[str]): The username to lookup defaults to requesting
        user.

    Returns:
        UserLinkUserLookupResponse: 200OK means no internal error/request error.
        Success = true and value if found. No value and success = False
        otherwise.
    """

    print(f"Using username: {username}.")

    # lookup username in the table
    try:
        entry = get_link_entry_by_username(
            username=username,
            config=config
        )
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Unhandled internal server exception when trying to read value from table. Error: {e}."
        )

    # if valid looking value then return - otherwise return failure case
    if entry is None:
        return AdminLinkUserLookupResponse(person_id=None, success=False)
    else:
        valid = id_appears_valid(entry.person_id)
        if not valid:
            return AdminLinkUserLookupResponse(person_id=None, success=False)
        else:
            return AdminLinkUserLookupResponse(person_id=entry.person_id, success=True)


@router.post("/assign", response_model=AdminLinkUserAssignResponse, operation_id="admin_link_user_assign")
async def assign(
    request: AdminLinkUserAssignRequest,
    config: Config = Depends(get_settings),
    roles: ProtectedRole = Depends(sys_admin_write_dependency)
) -> AdminLinkUserAssignResponse:
    """

    Attempts to assign the current user to the specified person_id. 

    The person must:
     - be registered in the Registry (unless disabled by validate)

    The link service must not contain any valid record with this user as the
    username (unless disabled with force).


    Args:
        request (AdminLinkUserAssignRequest): Contains the person ID to link to.

    Returns:
        AdminLinkUserAssignResponse: The response - 200OK or 400 with errors.
    """

    # determine username
    username = request.username
    print(f"Using username: {username}.")

    # lookup username in the table
    try:
        entry = get_link_entry_by_username(
            username=username,
            config=config
        )
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Unhandled internal server exception when trying to read value from table. Error: {e}."
        )

    # if there is a valid entry - then abort as users cannot overwrite
    if entry is not None and id_appears_valid(entry.person_id):
        if not request.force:
            raise HTTPException(
                status_code=400,
                detail=f"The username {username} already has a person ID assigned, ID {entry.person_id}. Use the force parameter to reassign."
            )
        else:
            print(f"Forcefully reassigning existing id: {entry.person_id}.")

    # make a request using the admins token into the registry - just fetch the item - don't validate owner
    if request.validate_item and config.link_update_registry_connection:
        try:
            item = user_fetch_person_from_registry(
                id=request.person_id,
                config=config,
                user=roles.user
            )
        except HTTPException as he:
            raise he
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Unhandled internal server exception when trying to fetch existing item. Error: {e}."
            )

        print(f"Item found, not validating ownership as this is admin override endpoint.")
    else:
        print(f"Item validation disabled - writing person ID.")

    # we are safe to assign this now
    try:
        set_link_entry_by_username(
            entry=UsernamePersonLinkTableEntry(
                username=username,
                person_id=request.person_id
            ),
            config=config
        )
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Unhandled internal server exception when trying to write to username person link service table. Error: {e}."
        )

    return AdminLinkUserAssignResponse()


@router.delete("/clear", response_model=AdminLinkUserClearResponse, operation_id="admin_link_user_clear")
async def clear(
    username: str,
    config: Config = Depends(get_settings),
    roles: ProtectedRole = Depends(sys_admin_write_dependency)
) -> AdminLinkUserClearResponse:
    """

    Clears the specified user. 

    Doesn't matter if user is in DB or not.

    Args:
        request (AdminLinkUserClearRequest): The request which includes username

    Returns:
        AdminLinkUserClearResponse: Empty 200 if OK, else 400/500.
    """
    # determine username
    print(f"Using username: {username}.")

    # delete entry
    del_link_entry_by_username(username=username, config=config)

    # return 200OK
    return AdminLinkUserClearResponse()


@router.get("/reverse_lookup", response_model=UserLinkReverseLookupResponse, operation_id="user_link_reverse_lookup")
async def reverse_lookup(
    person_id: str,
    config: Config = Depends(get_settings),
    user: User = Depends(sys_admin_read_dependency)
) -> UserLinkReverseLookupResponse:
    """
    Looks up the specified person_id in the username person link service. 

    Currently this is admin only - not sure on utility in the system yet.

    Args:
        person_id (str): The registry person ID to lookup

    Returns:
        UserLinkReverseLookupResponse: Contains the username if found, and success T/F
    """
    print(f"Using person_id: {person_id}.")

    # lookup username in the table
    try:
        entries = get_link_entries_by_person_id(
            person_id=person_id,
            config=config
        )
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Unhandled internal server exception when trying to read value from table. Error: {e}."
        )

    return UserLinkReverseLookupResponse(usernames=[entry.username for entry in entries])
