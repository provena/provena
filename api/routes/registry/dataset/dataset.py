from fastapi import APIRouter, Depends
from KeycloakFastAPI.Dependencies import ProtectedRole
from dependencies.dependencies import read_user_protected_role_dependency
from ProvenaInterfaces.RegistryAPI import *
from helpers.registry.action_helpers import *
from config import Config, get_settings

router = APIRouter()

@router.post("/user/releases", response_model=PaginatedDatasetListResponse, operation_id="list_releasing_datasets")
async def get_releasing_datasets(
    list_request: ListUserReviewingDatasetsRequest,
    config: Config = Depends(get_settings),
    protected_roles: ProtectedRole = Depends(
        read_user_protected_role_dependency),
) -> PaginatedDatasetListResponse: #ItemDataset
    

    # deconstruct main payload
    filter_by = list_request.filter_by
    sort_by = list_request.sort_by
    pagination_key = list_request.pagination_key
    page_size = list_request.page_size

    # check this here because the list items paginated is generic and allows search without filters.
    # to return other registry items.
    if filter_by.release_reviewer is None:
        raise HTTPException(status_code=400, detail="release reviewer id must be specified inside of filter_by")
    
    # fetch handle for this user's person entity using link service
    user_id = get_user_link(user=protected_roles.user, config=config)
    if user_id is None:
        raise HTTPException(
            status_code=400,
            detail="In order to perform this operation you must link your User account to a Person in the registry."
        )

    if user_id != filter_by.release_reviewer:
        raise HTTPException(
            status_code=403,
            detail="You can only search for your own dataset releases. User requesting is not the same as the release reviewer id." +
                f""" requesting username and ID are "{protected_roles.user.username}"" and "{user_id}". Reviewer ID filter is {filter_by.release_reviewer}."""
        )

    items, returned_pagination_key = list_items_paginated_and_filter(
        config=config,
        sort_by=sort_by,
        filter_by=filter_by,
        pagination_key=pagination_key,
        page_size=page_size,
        protected_roles=protected_roles
    )
    dataset_items: List[ItemDataset]
    try:
        # TODO - make this on a per item basis?
        dataset_items = [ItemDataset.parse_obj(item) for item in items]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to parse item into ItemDataset. {e}")
    
    return PaginatedDatasetListResponse(
        status=Status(
            success=True,
            details="Searched database and returned dataset items matching query."
        ),
        dataset_items=dataset_items,
        total_dataset_count=len(dataset_items),
        pagination_key=returned_pagination_key
    )