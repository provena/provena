from fastapi import APIRouter, Depends
from KeycloakFastAPI.Dependencies import *
from dependencies.dependencies import *
from SharedInterfaces.AuthAPI import *
from config import Config, get_settings
from helpers.username_person_link_service_helpers import *
from helpers.registry_api_helpers import user_fetch_person_auth_config_from_registry

router = APIRouter(
    prefix="/user"
)


@router.get("/lookup", response_model=UserLinkUserLookupResponse, operation_id="user_link_user_lookup")
async def lookup(
    username: Optional[str] = None,
    config: Config = Depends(get_settings),
    user: User = Depends(user_general_dependency)
) -> UserLinkUserLookupResponse:
    """

    Looks up the specified username in the username person link service. 

    If no username is provided then the user token is used to determine the
    username.

    Args:
        username (Optional[str]): The username to lookup defaults to requesting
        user.

    Returns:
        UserLinkUserLookupResponse: 200OK means no internal error/request error.
        Success = true and value if found. No value and success = False
        otherwise.
    """

    # determine username
    username = username or user.username
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
        return UserLinkUserLookupResponse(person_id=None, success=False)
    else:
        valid = id_appears_valid(entry.person_id)
        if not valid:
            return UserLinkUserLookupResponse(person_id=None, success=False)
        else:
            return UserLinkUserLookupResponse(person_id=entry.person_id, success=True)


@router.post("/assign", response_model=UserLinkUserAssignResponse, operation_id="user_link_user_assign")
async def assign(
    request: UserLinkUserAssignRequest,
    config: Config = Depends(get_settings),
    user: User = Depends(user_general_dependency)
) -> UserLinkUserAssignResponse:
    """

    Attempts to assign the current user to the specified person_id. 

    The person must:
     - be registered in the Registry
     - be owned by the token Username

    The username person link service must not contain any valid record with this user as the username.

    If a user needs to update their link, they should contact an admin.

    Args:
        request (UserLinkUserAssignRequest): Contains the person ID to link to.

    Returns:
        UserLinkUserAssignResponse: The response - 200OK or 400 with errors.
    """

    # determine username
    username = user.username
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
        raise HTTPException(
            status_code=400,
            detail=f"The username {username} already has a person ID assigned, ID {entry.person_id}. You cannot deassign a Person ID without contacting an admin."
        )

    if config.link_update_registry_connection:
        # there is no existing entry - now validate the person id and ensure the
        # user owns it

        # make a request using the users token into the registry - fetch the auth
        # configuration and check the owner
        try:
            access_settings = user_fetch_person_auth_config_from_registry(
                id=request.person_id,
                config=config,
                user=user
            )
        except HTTPException as he:
            raise he
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Unhandled internal server exception when trying to fetch auth configuration for existing item. Error: {e}."
            )

        # is the requesting user the owner?
        is_owner = check_is_owner(username=username, settings=access_settings)

        if not is_owner:
            raise HTTPException(
                status_code=401,
                detail=f"You are not authorised to assign your identity to a Person in the Registry which you do not own. Username: {username}. Person ID: {request.person_id}."
            )

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

    return UserLinkUserAssignResponse()


@router.post("/validate", response_model=UserLinkUserValidateResponse, operation_id="user_link_user_validate")
async def validate(
    request: UserLinkUserValidateRequest,
    config: Config = Depends(get_settings),
    user: User = Depends(user_general_dependency)
) -> UserLinkUserValidateResponse:
    """

    Attempts to assign the current user to the specified person_id. 

    This does not apply any changes- just validates

    The person must:
     - be registered in the Registry
     - be owned by the token Username

    The link service must not contain any valid record with this user as the
    username.

    If a user needs to update their link, they should contact an admin.

    Args:
        request (UserLinkUserAssignRequest): Contains the person ID to link to.

    Returns:
        UserLinkUserValidateResponse: Usually 200OK unless internal errors -
        status shows result.
    """

    # determine username
    username = user.username
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
        return UserLinkUserValidateResponse(
            status=Status(
                success=False,
                details=f"The username {username} already has a person ID assigned, ID {entry.person_id}. You cannot deassign a Person ID without contacting an admin."
            )
        )

    if config.link_update_registry_connection:
        # there is no existing entry - now validate the person id and ensure the
        # user owns it

        # make a request using the users token into the registry - fetch the auth
        # configuration and check the owner
        try:
            access_settings = user_fetch_person_auth_config_from_registry(
                id=request.person_id,
                config=config,
                user=user
            )
        except HTTPException as he:
            raise he
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Unhandled internal server exception when trying to fetch auth configuration for existing item. Error: {e}."
            )

        # is the requesting user the owner?
        is_owner = check_is_owner(username=username, settings=access_settings)

        if not is_owner:
            return UserLinkUserValidateResponse(
                status=Status(
                    success=False,
                    details=f"You are not authorised to assign your identity to a Person in the Registry which you do not own. Username: {username}. Person ID: {request.person_id}."
                )
            )

    return UserLinkUserValidateResponse(
        status=Status(
            success=True,
            details=f"This person ID could be linked to the specified username. Validation successful."
        )
    )
