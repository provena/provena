from SharedInterfaces.ProvenanceAPI import *
from SharedInterfaces.ProvenanceModels import *
from SharedInterfaces.SharedTypes import Status
from helpers.entity_validators import *
from helpers.registry_helpers import *
from helpers.prov_helpers import produce_prov_document
from helpers.model_run_helpers import *
from helpers.graph_db_helpers import *
from config import Config


async def register_and_lodge_provenance(record: ModelRunRecord, config: Config, request_style: RequestStyle) -> ProvenanceRecordInfo:
    # ==========================
    # Seed identity in registry
    # ==========================

    # this seeds the item on behalf of the user - based on the request style
    # this could be the proxied username or direct from the token
    username: str
    if request_style.service_account:
        assert request_style.service_account.on_behalf_username
        username = request_style.service_account.on_behalf_username
    elif request_style.user_direct:
        username = request_style.user_direct.username
    else:
        raise ValueError("Invalid validation settings")

    # service account is always used for this request
    seeded_item: SeededItem = await seed_model_run(
        proxy_username=username,
        config=config
    )
    handle_id = seeded_item.id

    # ==========================================================
    # Convert fully identified record into python-prov document
    # Integrate handle IDs into prov document
    # ==========================================================

    # resolve the workflow definition
    workflow_response = await validate_model_run_workflow_template(
        id=record.workflow_template_id,
        request_style=request_style,
        config=config
    )
    assert isinstance(workflow_response, ItemModelRunWorkflowTemplate)

    try:
        prov_document = produce_prov_document(
            model_record=record,
            record_id=seeded_item.id,
            workflow_template=workflow_response
        )
    except HTTPException as he:
        raise HTTPException(
            status_code=he.status_code,
            detail=f"Error occurred while producing the provenance document: {he.detail}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error occurred while producing the provenance document: {e}"
        )

    # ============================================================
    # Serialise document, update minted identity with prov record
    # ============================================================
    try:
        serialisation: str = produce_serialisation(prov_document)
    except HTTPException as he:
        raise HTTPException(
            status_code=500,
            detail=f"Serialisation of prov record failed - seed item created but not lodged. Failed ID: {handle_id}. Contact administrator. Details: {he.detail}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Serialisation of prov record failed - seed item created but not lodged. Failed ID: {handle_id}. Contact administrator. Exception: {e}."
        )

    model_run_record = ModelRunDomainInfo(
        # produce display name
        display_name=produce_display_name(
            display_name=record.display_name
        ),
        # set status to complete
        # mark as lodged once stored
        record_status=WorkflowRunCompletionStatus.COMPLETE,
        # set record to original input information
        record=record,
        # serialisation by python prov
        prov_serialisation=serialisation
    )

    # update record (from seed -> complete, no reason required)

    # NOTE model run records do not have prov versioning enabled so this is
    # fully synchronous op
    model_run_item: ItemModelRun = await update_model_run_in_registry(
        proxy_username=username,
        model_run_id=handle_id,
        model_run_domain_info=model_run_record,
        config=config
    )

    # ==========================================
    # Upload provenance record into graph store
    # ==========================================
    document_id = upload_prov_document(
        id=model_run_item.id,
        prov_document=prov_document,
        config=config
    )

    # =======================================
    # Mark record as being lodged in registry
    # =======================================
    model_run_record.record_status = WorkflowRunCompletionStatus.LODGED
    # update (from complete -> complete, reason required)
    updated_item: ItemModelRun = await update_model_run_in_registry(
        proxy_username=username,
        model_run_id=handle_id,
        model_run_domain_info=model_run_record,
        reason="Updating item to mark completion of provenance lodge.",
        config=config
    )

    # ==============================================================
    # Return prov serialisation, fully identified input format, and
    # model run handle ID
    # ==============================================================
    return ProvenanceRecordInfo(
        id=handle_id,
        prov_json=serialisation,
        record=record
    )


async def lodge_provenance(handle_id: str, record: ModelRunRecord, config: Config, request_style: RequestStyle) -> ProvenanceRecordInfo:
    # ==========================
    # Seed identity in registry
    # ==========================

    # this seeds the item on behalf of the user - based on the request style
    # this could be the proxied username or direct from the token
    username: str
    if request_style.service_account:
        assert request_style.service_account.on_behalf_username
        username = request_style.service_account.on_behalf_username
    elif request_style.user_direct:
        username = request_style.user_direct.username
    else:
        raise ValueError("Invalid validation settings")

    # ==========================================================
    # Convert fully identified record into python-prov document
    # Integrate handle IDs into prov document
    # ==========================================================

    # resolve the workflow definition
    print("Validating model run workflow template")
    workflow_response = await validate_model_run_workflow_template(
        id=record.workflow_template_id,
        request_style=request_style,
        config=config
    )
    assert isinstance(workflow_response, ItemModelRunWorkflowTemplate)

    print("Producing prov document")
    try:
        prov_document = produce_prov_document(
            model_record=record,
            record_id=handle_id,
            workflow_template=workflow_response
        )
    except HTTPException as he:
        raise HTTPException(
            status_code=he.status_code,
            detail=f"Error occurred while producing the provenance document: {he.detail}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error occurred while producing the provenance document: {e}"
        )

    # ==========================================
    # Upload provenance record into graph store
    # ==========================================
    print("Uploading prov document")
    document_id = upload_prov_document(
        id=handle_id,
        prov_document=prov_document,
        config=config
    )
    # ===========================================
    # Produce JSON serialisation of prov document
    # ===========================================

    try:
        serialisation: str = produce_serialisation(prov_document)
    except HTTPException as he:
        raise HTTPException(
            status_code=500,
            detail=f"Serialisation of prov record failed - seed item created but not lodged. Failed ID: {handle_id}. Contact administrator. Details: {he.detail}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Serialisation of prov record failed - seed item created but not lodged. Failed ID: {handle_id}. Contact administrator. Exception: {e}."
        )

    # ==============================================================
    # Return prov serialisation, fully identified input format, and
    # model run handle ID
    # ==============================================================

    return ProvenanceRecordInfo(
        id=handle_id,
        prov_json=serialisation,
        record=record
    )
