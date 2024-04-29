from dependencies.dependencies import read_write_user_protected_role_dependency, admin_user_protected_role_dependency
from KeycloakFastAPI.Dependencies import ProtectedRole
from fastapi import APIRouter, Depends, HTTPException
from ProvenaInterfaces.ProvenanceAPI import *
from helpers.workflows import register_and_lodge_provenance
from helpers.entity_validators import RequestStyle
from ProvenaInterfaces.SharedTypes import Status
from helpers.validate_model_run_record import validate_model_run_record
from helpers.auth_helpers import *
from helpers.job_api_helpers import submit_model_run_lodge_job, submit_batch_lodge_job
from ProvenaInterfaces.AsyncJobModels import ProvLodgeModelRunPayload, ProvLodgeBatchSubmitPayload
from config import get_settings, Config

router = APIRouter()


@router.post("/register", response_model=RegisterModelRunResponse, operation_id="register_model_run")
async def register_model_run_complete(
    record: ModelRunRecord,
    roles: ProtectedRole = Depends(read_write_user_protected_role_dependency),
    config: Config = Depends(get_settings)
) -> RegisterModelRunResponse:
    """    register_model_run_complete
        Given the model run record object (schema/model) will:
        - validate the ids provided in the model 
            - Validate and retrieve the workflow definition
            - Validate the templates for the input and output datasets 
            - Validate that the provided datasets satisfy all templates
            - Validate that datasets provided through data store exist
        - mint a model run record in the registry (acting as prov-api proxy on proxy endpoints)
            - This uses the user's username so that the user correctly owns the record
        - produce a prov-o document reflecting the input model run record
        - update the model run record in the registry with the prov serialisation
          and other information 
        - lodge the model run record into the graph database store
        - update the record to lodged status 
        - return information including the handle id from the model run record

        Arguments
        ----------
        record : ModelRunRecord
            The model run record to lodge into the graph store and registry

        Returns
        -------
         : RegisterModelRunResponse
            The response including the handle id and record information

        Raises
        ------
        HTTPException
            If something goes wrong when validating the IDs returns a 400 error.

        See Also (optional)
        --------

        Examples (optional)
        --------
    """
    # no proxy - user direct
    request_style = RequestStyle(
        service_account=None, user_direct=roles.user)

    valid, error_message = await validate_model_run_record(
        record=record,
        request_style=request_style,
        config=config,
    )

    if not valid:
        assert error_message
        raise HTTPException(
            status_code=400,
            detail=f"Failed to validate an entity's ID in the record, error: {error_message}."
        )

    # Then produce job using Job API and return session ID
    try:
        # Here we encode the required model run record + username and launch a job
        session_id = await submit_model_run_lodge_job(
            username=roles.user.username,
            payload=ProvLodgeModelRunPayload(
                record=record,
                revalidate=False
            ),
            config=config
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error while dispatching job. Error: {e}."
        )

    return RegisterModelRunResponse(
        status=Status(
            success=True, details=f"Job dispatched, monitor session ID using the job API to see progress."),
        session_id=session_id
    )


@router.post("/register_batch", operation_id="register_batch")
async def register_batch(
    request: RegisterBatchModelRunRequest,
    roles: ProtectedRole = Depends(read_write_user_protected_role_dependency),
    config: Config = Depends(get_settings)
) -> RegisterBatchModelRunResponse:
    # TODO should we validate items first? No - validate at batch time?
    # Then produce job using Job API and return session ID
    try:
        # Here we encode the required model run record + username and launch a job
        session_id = await submit_batch_lodge_job(
            username=roles.user.username,
            payload=ProvLodgeBatchSubmitPayload(
                records=request.records
            ),
            config=config
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error while dispatching job. Error: {e}."
        )

    return RegisterBatchModelRunResponse(
        status=Status(
            success=True, details=f"Job dispatched, monitor session ID using the job API to see progress."),
        session_id=session_id
    )


@router.post("/register_sync", response_model=SyncRegisterModelRunResponse, operation_id="register_model_run_sync", include_in_schema=False)
async def register_model_run_sync(
    record: ModelRunRecord,
    # admin only for this endpoint
    roles: ProtectedRole = Depends(admin_user_protected_role_dependency),
    config: Config = Depends(get_settings)
) -> SyncRegisterModelRunResponse:
    # no proxy - user direct
    request_style = RequestStyle(
        service_account=None, user_direct=roles.user)

    valid, error_message = await validate_model_run_record(
        record=record,
        request_style=request_style,
        config=config,
    )

    if not valid:
        assert error_message
        raise HTTPException(
            status_code=400,
            detail=f"Failed to validate an entity's ID in the record, error: {error_message}."
        )

    # lodge the provenance in sync mode
    result = await register_and_lodge_provenance(
        record=record,
        config=config,
        request_style=request_style
    )

    return SyncRegisterModelRunResponse(
        status=Status(
            success=True, details=f"Provenance record lodged successfully."),
        record_info=result
    )
