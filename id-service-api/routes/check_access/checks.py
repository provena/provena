from dependencies.dependencies import read_user_protected_role_dependency, read_write_user_protected_role_dependency, user_general_dependency, admin_user_protected_role_dependency
from KeycloakFastAPI.Dependencies import ProtectedRole, User
from fastapi import APIRouter,  Depends


router = APIRouter()


@router.get("/check-general-access", response_model=User, operation_id="check_general_access")
async def check_general_access(
    user: User = Depends(user_general_dependency)
) -> User:
    """
    Function Description
    --------------------

    A check point for the data store which responds if any authentication 
    is present and valid. Does not check role authorisation.

    Used to distinguish between 'general' and 'protected' access for this API. 


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

@router.get("/check-admin-access", response_model=User, operation_id="check_admin_access")
async def check_admin_access(
    protected_role: ProtectedRole = Depends(admin_user_protected_role_dependency)
) -> User:
    """
    Function Description
    --------------------

    A check point for the data store which responds if any authentication 
    is present and valid. Checks the the user is an admin.

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
    return protected_role.user

@router.get("/check-read-access", response_model=User, operation_id="check_read_access")
async def check_read_access(
    protected_roles: ProtectedRole = Depends(
        read_user_protected_role_dependency)
) -> User:
    """
    Function Description
    --------------------

    A check point for the data store front end to validate authorisation.

    Only allows read users (or read and write).


    Arguments
    ----------
    protected_roles : ProtectedRole, optional
        The protected role dependency, by default Depends( kc_auth.get_any_protected_role_dependency([usage_role]))

    Returns
    -------
    User
        Returns user information


    See Also (optional)
    --------

    Examples (optional)
    --------

    """
    return protected_roles.user

@router.get("/check-write-access", response_model=User, operation_id="check_write_access")
async def check_write_access(
    protected_roles: ProtectedRole = Depends(
        read_write_user_protected_role_dependency)
) -> User:
    """
    Function Description
    --------------------

    A check point for the data store front end to validate authorisation.

    Only allows read-write users.


    Arguments
    ----------
    protected_roles : ProtectedRole, optional
        The protected role dependency, by default Depends( kc_auth.get_any_protected_role_dependency([usage_role]))

    Returns
    -------
    User
        Returns user information



    See Also (optional)
    --------

    Examples (optional)
    --------

    """
    return protected_roles.user