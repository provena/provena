from dependencies.dependencies import read_write_user_protected_role_dependency, admin_user_protected_role_dependency, get_user_cipher
from KeycloakFastAPI.Dependencies import ProtectedRole
from fastapi import APIRouter, Depends, HTTPException
from ProvenaInterfaces.ProvenanceAPI import *
from helpers.registry_helpers import update_model_run_in_registry
from helpers.workflows import register_and_lodge_provenance
from helpers.entity_validators import RequestStyle, validate_model_run_study_linking, UserCipherProxy
from ProvenaInterfaces.SharedTypes import Status
from ProvenaInterfaces.RegistryModels import ItemModelRun
from helpers.validate_model_run_record import validate_model_run_record
from helpers.auth_helpers import *
from ProvenaSharedFunctionality.Helpers.encryption_helpers import encrypt_user_info
from helpers.job_api_helpers import submit_model_run_lodge_job, submit_batch_lodge_job, submit_model_run_lodge_only_job, submit_model_run_update_job
from ProvenaInterfaces.AsyncJobModels import ProvLodgeModelRunPayload, ProvLodgeBatchSubmitPayload, ProvLodgeModelRunLodgeOnlyPayload, ProvLodgeUpdatePayload
from config import get_settings, Config

router = APIRouter()

EDIT_ROOT_PREFIX = "/edit"


@router.post("/register", response_model=RegisterModelRunResponse, operation_id="register_model_run")
async def register_model_run_complete(
    record: ModelRunRecord,
    roles: ProtectedRole = Depends(read_write_user_protected_role_dependency),
    config: Config = Depends(get_settings),
    user_cipher : str = Depends(get_user_cipher)
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
                revalidate=False,
                user_info=user_cipher
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
    config: Config = Depends(get_settings),
    user_cipher : str = Depends(get_user_cipher)
) -> RegisterBatchModelRunResponse:
    # TODO should we validate items first? No - validate at batch time?
    # Then produce job using Job API and return session ID
    try:
        # Here we encode the required model run record + username and launch a job
        session_id = await submit_batch_lodge_job(
            username=roles.user.username,
            payload=ProvLodgeBatchSubmitPayload(
                records=request.records,
                # encrypted user info
                user_info=user_cipher
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
    config: Config = Depends(get_settings),
    user_cipher : str = Depends(get_user_cipher)
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
        request_style=request_style,
        proxy=UserCipherProxy(user_cipher=user_cipher)
    )

    return SyncRegisterModelRunResponse(
        status=Status(
            success=True, details=f"Provenance record lodged successfully."),
        record_info=result
    )


@router.post(f"{EDIT_ROOT_PREFIX}/link_to_study", response_model=AddStudyLinkResponse, operation_id="add_study_link")
async def link_to_study(
    model_run_id: str,
    study_id: str,
    roles: ProtectedRole = Depends(read_write_user_protected_role_dependency),
    config: Config = Depends(get_settings),
    user_cipher : str = Depends(get_user_cipher)
) -> AddStudyLinkResponse:

    # validate model_run_id and study_id to be linked.
    request_style = RequestStyle(
        user_direct=roles.user, service_account=None)

    model_run, study = await validate_model_run_study_linking(
        model_run_id=model_run_id,
        study_id=study_id,
        request_style=request_style,
        config=config
    )
    model_run: ItemModelRun

    # all valid, make the link in the registry and then in the provenance graph
    try:
        model_run.record.study_id = study_id
        model_run_item: ItemModelRun = await update_model_run_in_registry(
            model_run_id=model_run_id,
            model_run_domain_info=model_run,
            config=config,
            reason="Linking model run to study.",
            user_cipher=user_cipher
        )
    except HTTPException as e:
        raise HTTPException(
            status_code=e.status_code,
            detail=f"Error occurred while updating model run in registry: {e.detail}"
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error occurred while updating model run in registry: {e}"
        ) from e

    # now update to the provenance graph by lodging a model run lodge only job (wont create a new registry record)
    try:
        session_id = await submit_model_run_lodge_only_job(
            username=roles.user.username,
            payload=ProvLodgeModelRunLodgeOnlyPayload(
                model_run_record_id=model_run_id,
                record=model_run.record,
                revalidate=False,
                user_info=user_cipher
            ),
            config=config
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error while dispatching job. Error: {e}."
        ) from e

    # done
    return AddStudyLinkResponse(
        status=Status(
            success=True, details=f"Succesfully linked model run and study together in the registry and lodged a job for the provenance graph update with given session ID."),
        model_run_id=model_run_id,
        study_id=study_id,
        session_id=session_id
    )


@router.post("/update", response_model=PostUpdateModelRunResponse, operation_id="update_model_run", include_in_schema=True)
async def update_model_run(
    payload: PostUpdateModelRunInput,
    roles: ProtectedRole = Depends(read_write_user_protected_role_dependency),
    config: Config = Depends(get_settings),
    user_cipher : str = Depends(get_user_cipher)
) -> PostUpdateModelRunResponse:
    # no proxy - user direct
    request_style = RequestStyle(
        service_account=None, user_direct=roles.user)

    # validate first
    valid, error_message = await validate_model_run_record(
        record=payload.record,
        request_style=request_style,
        config=config,
    )
    if not valid:
        assert error_message
        raise HTTPException(
            status_code=400,
            detail=f"Failed to validate an entity's ID in the record, error: {error_message}."
        )

    try:
        res = await submit_model_run_update_job(
            username=roles.user.username,
            payload=ProvLodgeUpdatePayload(
                model_run_record_id=payload.model_run_id,
                updated_record=payload.record,
                reason=payload.reason,
                revalidate=True,
                # encrypted user info
                user_info=user_cipher
            ),
            config=config
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error while dispatching job. Error: {e}."
        )

    return PostUpdateModelRunResponse(session_id=res)


#
#
# class DeleteGraph(BaseModel):
#    record_id: str
#
#
# @router.post("/delete_graph", operation_id="delete_graph", include_in_schema=False)
# async def delete_graph(
#    delete: DeleteGraph,
#    # admin only for this endpoint
#    roles: ProtectedRole = Depends(admin_user_protected_role_dependency),
#    config: Config = Depends(get_settings)
# ) -> Any:
#    # no proxy - user direct
#    request_style = RequestStyle(
#        service_account=None, user_direct=roles.user)
#
#    # dummy delete graph
#    delete_dummy_graph = NodeGraph(record_id=delete.record_id, links=[])
#
#    print("Setting up neo4j client")
#    neo4j_manager = Neo4jGraphManager(config=config)
#    print("Done")
#
#    # Getting old graph
#    print("Retrieving graph")
#    old_graph = neo4j_manager.get_graph_by_record_id(delete.record_id)
#    print("Done")
#
#    # get the graph diff
#    print("Building diff and applying...")
#    diff_generator = GraphDiffApplier(neo4j_manager=neo4j_manager)
#    diff_generator.apply_diff(
#        old_graph=old_graph, new_graph=delete_dummy_graph)
#    print("Done")
#
#    # get the updated graph
#    print("Retrieving updated graph")
#    updated_graph = neo4j_manager.get_graph_by_record_id(delete.record_id)
#    print("Done")
#
#    return {"old_graph": old_graph.to_json_pretty(), "updated": updated_graph.to_json_pretty()}
#
