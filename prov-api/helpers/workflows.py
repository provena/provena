from ProvenaInterfaces.ProvenanceAPI import *
from ProvenaInterfaces.ProvenanceModels import *
from ProvenaInterfaces.SharedTypes import Status
from helpers.entity_validators import *
from helpers.registry_helpers import *
from helpers.prov_helpers import model_run_to_graph
from helpers.model_run_helpers import *
from helpers.prov_connector import Neo4jGraphManager, GraphDiffApplier
from config import Config


async def update_existing_model_run(model_run_record_id: str, reason: str, record: ModelRunRecord, config: Config, request_style: RequestStyle) -> ProvenanceRecordInfo:
    """
    Updates and lodges a provenance record into the Registry and GraphDB.

    Parameters
    ----------
    model_run_record_id : str
        The existing record id
    record : ModelRunRecord
        The model run record to mint, lodge, update.
    reason: str
        The reason for update
    config : Config
        The config
    request_style : RequestStyle
        The type of requests to use when validating info in the model run record.

    Returns
    -------
    ProvenanceRecordInfo
        The completed info
    """

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

    # ==========================
    # Update record in registry
    # ==========================

    # resolve the workflow definition
    workflow_response = await validate_model_run_workflow_template(
        id=record.workflow_template_id,
        request_style=request_style,
        config=config
    )
    assert isinstance(workflow_response, ItemModelRunWorkflowTemplate)

    try:
        graph = model_run_to_graph(
            model_record=record,
            record_id=model_run_record_id,
            workflow_template=workflow_response
        )
    except HTTPException as he:
        raise HTTPException(
            status_code=he.status_code,
            detail=f"Error occurred while producing the graph: {he.detail}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error occurred while producing the graph: {e}"
        )

    try:
        doc = graph.to_prov_document()
        serialisation: str = produce_serialisation(doc)
    except HTTPException as he:
        raise HTTPException(
            status_code=500,
            detail=f"Serialisation of prov record failed - seed item created but not lodged. Failed ID: {model_run_record_id}. Contact administrator. Details: {he.detail}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Serialisation of prov record failed - seed item created but not lodged. Failed ID: {model_run_record_id}. Contact administrator. Exception: {e}."
        )

    updated_model_run_record = ModelRunDomainInfo(
        # produce display name
        display_name=produce_display_name(
            display_name=record.display_name
        ),
        # set status to complete
        # mark as lodged once stored
        record_status=WorkflowRunCompletionStatus.COMPLETE,
        # set record to new input information
        record=record,
        # serialisation by python prov
        prov_serialisation=serialisation
    )
    # update record (from seed -> complete, no reason required)

    # NOTE model run records do not have prov versioning enabled so this is
    # fully synchronous op
    model_run_item: ItemModelRun = await update_model_run_in_registry(
        proxy_username=username,
        model_run_id=model_run_record_id,
        model_run_domain_info=updated_model_run_record,
        config=config,
        reason=reason
    )

    # ==========================================
    # Upload provenance record into graph store
    # ==========================================

    # Get the existing graph object
    manager = Neo4jGraphManager(config=config)

    try:
        existing_graph = manager.get_graph_by_record_id(model_run_record_id)

        # Generate and apply diff
        diff_manager = GraphDiffApplier(manager)
        diff_manager.apply_diff(existing_graph, graph)
    except Exception as e:
        raise Exception(
            f"Failed to fetch existing graph or deploy diff. Error: {e}.") from e

    # =======================================
    # Mark record as being lodged in registry
    # =======================================
    model_run_item.record_status = WorkflowRunCompletionStatus.LODGED
    # update (from complete -> complete, reason required)
    updated_item: ItemModelRun = await update_model_run_in_registry(
        proxy_username=username,
        model_run_id=model_run_record_id,
        model_run_domain_info=updated_model_run_record,
        reason="Updating item to mark completion of provenance lodge.",
        config=config
    )

    # ==============================================================
    # Return prov serialisation, fully identified input format, and
    # model run handle ID
    # ==============================================================
    return ProvenanceRecordInfo(
        id=model_run_record_id,
        prov_json=serialisation,
        record=record
    )

async def update_existing_model_run_lodge_only(model_run_record_id: str, record: ModelRunRecord, config: Config, request_style: RequestStyle) -> None:
    """
    Lodges a provenance record into the Registry and GraphDB - diffs existing graph.

    Parameters
    ----------
    model_run_record_id : str
        The existing record id
    record : ModelRunRecord
        The model run record to mint, lodge, update.
    config : Config
        The config
    request_style : RequestStyle
        The type of requests to use when validating info in the model run record.

    Returns
    -------
    ProvenanceRecordInfo
        The completed info
    """

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

    # ==========================
    # Update record in registry
    # ==========================

    # resolve the workflow definition
    workflow_response = await validate_model_run_workflow_template(
        id=record.workflow_template_id,
        request_style=request_style,
        config=config
    )
    assert isinstance(workflow_response, ItemModelRunWorkflowTemplate)

    try:
        graph = model_run_to_graph(
            model_record=record,
            record_id=model_run_record_id,
            workflow_template=workflow_response
        )
    except HTTPException as he:
        raise HTTPException(
            status_code=he.status_code,
            detail=f"Error occurred while producing the graph: {he.detail}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error occurred while producing the graph: {e}"
        )

    # ==========================================
    # Upload provenance record into graph store
    # ==========================================

    # Get the existing graph object
    manager = Neo4jGraphManager(config=config)

    try:
        existing_graph = manager.get_graph_by_record_id(model_run_record_id)

        # Generate and apply diff
        diff_manager = GraphDiffApplier(manager)
        diff_manager.apply_diff(existing_graph, graph)
    except Exception as e:
        raise Exception(
            f"Failed to fetch existing graph or deploy diff. Error: {e}.") from e

async def register_and_lodge_provenance(record: ModelRunRecord, config: Config, request_style: RequestStyle) -> ProvenanceRecordInfo:
    """

    Registers and lodges a provenance record into the Registry and GraphDB.

    Parameters
    ----------
    record : ModelRunRecord
        The model run record to mint, lodge, update.
    config : Config
        The config
    request_style : RequestStyle
        The type of requests to use when validating info in the model run record.

    Returns
    -------
    ProvenanceRecordInfo
        The completed info
    """
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
        graph = model_run_to_graph(
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
        doc = graph.to_prov_document()
        serialisation: str = produce_serialisation(doc)
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
    #
    # This is an additive merge
    # ==========================================

    manager = Neo4jGraphManager(config=config)
    manager.merge_add_graph_to_db(graph)

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
        graph = model_run_to_graph(
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
    #
    # This is an additive merge
    # ==========================================

    manager = Neo4jGraphManager(config=config)
    manager.merge_add_graph_to_db(graph)

    # ===========================================
    # Produce JSON serialisation of prov document
    # ===========================================

    try:
        doc = graph.to_prov_document()
        serialisation: str = produce_serialisation(doc)
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
