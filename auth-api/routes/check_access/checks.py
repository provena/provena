from fastapi import APIRouter, Depends

from KeycloakFastAPI.Dependencies import User
from dependencies.dependencies import *
from ProvenaInterfaces.AuthAPI import *

router = APIRouter()

@router.get("/public", response_model=Status, operation_id="check_public_access")
async def check_public_access(
) -> Status:
    """
    Function Description
    --------------------
    
    Checks if public access is possible.


    Arguments
    ----------

    Returns
    -------
    Status
        Success



    See Also (optional)
    --------

    Examples (optional)
    --------

    """
    return Status(success=True, details="Public access successful.")

@router.get("/general", response_model=User, operation_id="check_general_access")
async def check_general_access(
    user: User = Depends(user_general_dependency)
) -> User:
    """
    Function Description
    --------------------

    Function used to determine if user has basic authentication
    into the system - does not test any roles or permissions.   


    Arguments
    ----------
    user : User, optional
        The authenticated user - may or may not have the correct roles. 

    Returns
    -------
    User
        Returns user information



    See Also (optional)
    --------

    Examples (optional)
    --------

    """
    return user

