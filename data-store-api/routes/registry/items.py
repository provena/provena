from ProvenaInterfaces.DataStoreAPI import *
from ProvenaInterfaces.RegistryAPI import *
from KeycloakFastAPI.Dependencies import ProtectedRole
from fastapi import APIRouter, Depends, HTTPException
from config import get_settings, Config
from dependencies.dependencies import read_user_protected_role_dependency
from helpers.auth_helpers import evaluate_user_access
from helpers.s3_helpers import check_file_exists, generate_presigned_url_for_download
from helpers.registry_api_helpers import *
from helpers.sanitize import sanitize_handle
import re

router = APIRouter()

ILLEGAL_PATH_SUBSTRINGS = ["../", "/../", "..", "//", "\\", "\\\\"]

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

    return fetch_dataset_helper(handle_id, protected_roles.user, config)


@router.post('/generate-presigned-url', response_model=PresignedURLResponse, operation_id="generate_presigned_url")
async def generate_presigned_url(
    presigned_url_req: PresignedURLRequest,
    protected_roles: ProtectedRole = Depends(
        read_user_protected_role_dependency),
    config: Config = Depends(get_settings)
) -> PresignedURLResponse:

    dataset_id = presigned_url_req.dataset_id
    # relative path to file inside bucket/dataset_id.
    file_path = presigned_url_req.file_path

    # validate dataset id exists, and user has read access to it
    try:
        dataset_item = ensure_user_roles_access_to_dataset(
            dataset_id=dataset_id, user=protected_roles.user, roles=[DATASET_READ_ROLE], config=config)
    except HTTPException as e:
        raise HTTPException(
            status_code=e.status_code,
            detail=f"Failed to generate presigned url. Error: {e.detail}"
        )

    # validate file path does not do anything shifty or dodgy like ../
    for illegal_string in ILLEGAL_PATH_SUBSTRINGS:
        if illegal_string in file_path:
            raise HTTPException(
                status_code=400,
                detail=f"File path '{file_path}' contains '{illegal_string}' which is not allowed."
            )

    # create full path to compare with other full paths to items inside dataset_id
    full_file_path = config.DATASET_PATH + '/' + sanitize_handle(dataset_id) + '/' + file_path

    # validate file path exists in dataset    
    if not check_file_exists(config.S3_STORAGE_BUCKET_NAME, full_file_path):
        raise HTTPException(
            status_code=400,
            detail=f"File path '{file_path}' does not exist in dataset with id {dataset_id}"
        )

    # generate presigned url using scoped credentials to the s3 location of the dataset
    url = generate_presigned_url_for_download(
        path=full_file_path,
        expires_in=presigned_url_req.expires_in,
        s3_loc=dataset_item.s3,
        config=config
    )

    return PresignedURLResponse(
        dataset_id=dataset_id,
        file_path=file_path,
        presigned_url=url
    )
