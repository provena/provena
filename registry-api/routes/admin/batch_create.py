from dependencies.dependencies import admin_user_protected_role_dependency
from config import get_settings, Config
from KeycloakFastAPI.Dependencies import User
from SharedInterfaces.RegistryAPI import *
from fastapi import APIRouter, Depends
from helpers.admin_helpers import *
"""
# Setup fastAPI router for this sub route
router = APIRouter()

@router.post("/batch_create_junk", response_model=StatusResponse, operation_id="registry_admin_batch_create_junk", include_in_schema=False)
async def batch_create(
    num_per_type: int,
    user: User = Depends(admin_user_protected_role_dependency),
    config: Config = Depends(get_settings),
) -> StatusResponse:
"""

"""
    Facilitates the creation of num_per_type of each item type. Will crate examples junk items. 
    This endpoint exists to fill a test dbb with junk items. Not to facilitate creation of meaningful items.

    Parameters
    ----------
    num_per_type: int
        the number of each item type to create.
    user : User, optional
        _description_, by default Depends(admin_user_protected_role_dependency)
    config : Config, optional
        _description_, by default Depends(get_settings)
    
    Returns
    -------
    StatusResponse
        Status response of whether the batch crate was successful or not.
"""
"""
    try: 
        batch_create_junk_items(num_per_item_type=num_per_type, config=config)
    except Exception as e:
        return StatusResponse(
            status= Status(
                success = False,
                details= f"Failed to batch create items. Error: {e}"
            ), 
        )

    return StatusResponse(
            status= Status(
                success = True,
                details= f"Successfully created {num_per_type} of each item type in the registry."
            ), 
        )
"""