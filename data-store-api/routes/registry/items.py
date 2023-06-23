from SharedInterfaces.DataStoreAPI import *
from SharedInterfaces.RegistryAPI import *
from KeycloakFastAPI.Dependencies import ProtectedRole
from fastapi import APIRouter, Depends, HTTPException
from config import get_settings, Config
from dependencies.dependencies import read_user_protected_role_dependency
from helpers.registry_api_helpers import *

router = APIRouter()


@router.post("/list", response_model=DatasetListResponse, operation_id="list")
async def list(
    list_request: NoFilterSubtypeListRequest,
    protected_roles: ProtectedRole = Depends(
        read_user_protected_role_dependency),
    config: Config = Depends(get_settings)
) -> DatasetListResponse:
    """    list_all_datasets
        Lists all data in the data registry. Returns a DatasetListResponse.

        Optionally returns a pagination key if there are more items. 

        A pagination key should be included in the request payload if continuing
        from previous request. 

        Only returns datasets for which the user has metadata read permissions
        based on their dataset ownership and/or group access.

        Arguments
        ---------
        list_request : NoFilterSubtypeListRequest
            A JSON payload which includes filter/sort options and optionally the
            pagination key.

        Returns
        -------
         : ListRegistryResponse
            An object containing the responses status and a registry_items
            python list containing a RegistryItem for each item in the the
            database.

        See Also (optional)
        --------

        Examples (optional)
        --------
    """

    # caching disabled for now
    # To filter out rest of exception catching which happens in lower level func.
    try:
        dataset_list_response = user_list_datasets_from_registry(
            config=config,
            user=protected_roles.user,
            list_request=list_request
        )
    except HTTPException as e:  # will catch http exceptions that are raised inside of get_all_registry_items
        raise e
    except Exception as e:
        raise Exception(f"Failed reading registry. Error: {e}")

    # filter based on access - already done by registry
    return dataset_list_response


@router.get("/fetch-dataset", response_model=RegistryFetchResponse, operation_id="fetch_dataset")
async def fetch_dataset(
    handle_id: str,
    protected_roles: ProtectedRole = Depends(
        read_user_protected_role_dependency),
    config: Config = Depends(get_settings)
) -> RegistryFetchResponse:
    """    fetch_dataset
        Given a unique Handle ID, this function searches the data registry for 
        the data associated with this handle and will return a RegistryFetchResponse 
        containing as RegistryItem as an attribute for the queried 
        dataset.

        Returns a 401 if the user is not able to access the dataset.

        Arguments
        ----------
        handle_id : str
            The unique handle ID for searching the data-registry with.

        Returns
        -------
         : RegistryFetchResponse
            Containing the response status and registry_item.

        Raises
        ------
        HTTPException
            If fails to source item from the registry.

        See Also (optional)
        --------

        Examples (optional)
        --------
    """

    # Fetches all columns of the registry for a particular handle_id ("row")
    if handle_id == "":
        raise HTTPException(
            status_code=400,
            detail="Empty string received for query handle_id"
        )

    # fetch the dataset from reg api - this will respect auth and raise
    # appropriate error - it also checks that the item exists in the payload and that
    # success was true - it includes roles as well
    try:
        registry_item = user_fetch_dataset_from_registry(
            id=handle_id,
            config=config,
            user=protected_roles.user
        )
    except HTTPException as e:
        # something has handled this responsibly in fast API format so just
        # raise the error
        raise e
    except Exception as e:  # all other errors.
        raise Exception(
            f"Something unexpected went wrong during data retrieval. Error: {e}")

    return RegistryFetchResponse(
        status=Status(
            success=True,
            details=f"Successfully fetched data for handle '{handle_id}'"
        ),
        item=registry_item.item,
        roles=registry_item.roles,
        locked=registry_item.locked
    )
