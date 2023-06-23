from fastapi import APIRouter, Depends
from SharedInterfaces.ProvenanceAPI import *
from SharedInterfaces.RegistryModels import *
from SharedInterfaces.SharedTypes import Status
from KeycloakFastAPI.Dependencies import User, ProtectedRole
from dependencies.dependencies import admin_user_protected_role_dependency
from config import Config, get_settings
from helpers.admin_helpers import store_existing_record, list_model_run_records_from_registry

router = APIRouter()


@router.post("/store_record", response_model=StatusResponse, operation_id="store_record")
async def store_record(
    registry_record: ItemModelRun,
    validate_record: bool = True,
    roles: ProtectedRole = Depends(admin_user_protected_role_dependency),
    config: Config = Depends(get_settings)
) -> StatusResponse:
    """
    store_record 

    An admin only endpoint which enables the reupload/storage of an existing
    completed provenance record. 

    Optionally, the record can also be revalidated. 

    It might be wise to start with an empty graph before running this command
    however it should work regardless since the properties will be merged on
    existing nodes.

    Parameters
    ----------
    registry_record : ItemModelRun
        The completed registry record for the model run
    validate_record : bool, optional
        Should the ids in the payload be validated?, by default True

    Returns
    -------
    StatusResponse
        A status response

    Raises
    ------
    HTTPException
        Various HTTP exceptions if errors occur
    """
    # Use the admin helper function for this record
    return await store_existing_record(
        registry_record=registry_record,
        validate_record=validate_record,
        config=config,
        user=roles.user
    )


@router.post("/store_records", response_model=StatusResponse, operation_id="store_records")
async def store_records(
    registry_records: List[ItemModelRun],
    validate_record: bool = True,
    roles: ProtectedRole = Depends(admin_user_protected_role_dependency),
    config: Config = Depends(get_settings)
) -> StatusResponse:
    """
    store_records

    Applies the store record endpoint action across a list of ItemModelRun's

    Parameters
    ----------
    registry_records : List[ItemModelRun]
        List of the completed registry record for the model run
    validate_record : bool, optional
        Should the ids in the payload be validated? Applied for all records, by default True

    Returns
    -------
    StatusResponse
        A status response

    Raises
    ------
    HTTPException
        Various HTTP exceptions if errors occur
    """
    # Use the admin helper function for each record
    for record in registry_records:
        status = await store_existing_record(
            registry_record=record,
            validate_record=validate_record,
            config=config,
            user=roles.user
        )
        if not status.status.success:
            return status

    return StatusResponse(
        status=Status(
            success=True,
            details=f"Successfully re-lodged all of the provenance records."
        )
    )


@router.post("/store_all_registry_records", response_model=StatusResponse, operation_id="store_all_registry_records")
async def store_all_registry_records(
    validate_record: bool = True,
    roles: ProtectedRole = Depends(admin_user_protected_role_dependency),
    config: Config = Depends(get_settings)
) -> StatusResponse:
    """
    store_records

    Applies the store record endpoint action across a list of ItemModelRuns
    which is found by querying the registry model run list endpoint directly.

    Parameters
    ----------
    validate_record : bool, optional
        Should the ids in the payload be validated? Applied for all records, by
        default True

    Returns
    -------
    StatusResponse
        A status response

    Raises
    ------
    HTTPException
        Various HTTP exceptions if errors occur
    """
    
    # uses the users admin token to query paginated endpoint to get all records
    records : List[ItemModelRun] = await list_model_run_records_from_registry(
        config=config,
        user=roles.user
    )
    
    # Use the admin helper function for each record
    for record in records:
        print(f"Processing {record.id=}...")
        status = await store_existing_record(
            registry_record=record,
            validate_record=validate_record,
            config=config,
            user=roles.user
        )
        if not status.status.success:
            return status

    return StatusResponse(
        status=Status(
            success=True,
            details=f"Successfully re-lodged all {len(records)} provenance records from the registry."
        )
    )
