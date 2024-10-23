import os
from dependencies.dependencies import read_user_protected_role_dependency, read_write_user_protected_role_dependency, user_general_dependency, admin_user_protected_role_dependency
from KeycloakFastAPI.Dependencies import User, ProtectedRole
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from ProvenaInterfaces.ProvenanceAPI import *
from ProvenaInterfaces.ProvenanceModels import *
from ProvenaInterfaces.SharedTypes import Status
from helpers.entity_validators import unknown_validator, RequestStyle, ServiceAccountProxy
import helpers.prov_connector as prov_connector
from typing import Dict, Any
from config import Config, get_settings


from ProvenaInterfaces.RegistryAPI import ItemSubType, ItemBase, Node
from helpers.generate_report_helpers import parse_nodes, validate_node_id, generate_report_helper, generate_word_file, remove_file

router = APIRouter()


@router.get("/upstream", response_model=LineageResponse, operation_id="explore_upstream")
async def explore_upstream(
    starting_id: str,
    depth: Optional[int] = None,
    config: Config = Depends(get_settings),
    _: User = Depends(read_user_protected_role_dependency)
) -> LineageResponse:
    """    explore_upstream
        Explores in the upstream direction (inputs/associations)
        starting at the specified node handle ID. The search 
        depth is bounded by the depth parameter which has a default
        maximum of 100.

        Arguments
        ----------
        starting_id : str
            The handle ID to start at.
        depth : int, optional
            The maximum depth to traverse in this direction, by default depth_upper_limit

        Returns
        -------
         : LineageResponse
            A status, node count, and networkx serialised graph response.

        See Also (optional)
        --------

        Examples (optional)
        --------
    """
    if not depth:
        depth = config.depth_default_limit

    if depth > config.depth_upper_limit:
        raise HTTPException(
            status_code=400,
            detail=f"Depth provided is in excess of depth maximum: {config.depth_upper_limit}."
        )

    # we want to make a proxied request directly using the service account
    request_style = RequestStyle(user_direct=None, service_account=ServiceAccountProxy(
        direct_service=True, on_behalf_username=None))

    # validate starting point
    await unknown_validator(id=starting_id, config=config, request_style=request_style)

    # make lineage query
    json_serialisation: Dict[str, Any] = prov_connector.upstream_query(
        starting_id=starting_id,
        depth=depth,
        config=config
    )

    # record count := length of the nodes list in response
    node_count = len(json_serialisation['nodes'])

    return LineageResponse(
        status=Status(
            success=True,
            details=f"Made lineage query (with depth {depth}) to neo4j backend."
        ),
        record_count=node_count,
        graph=json_serialisation
    )


@router.get("/downstream", response_model=LineageResponse, operation_id="explore_downstream")
async def explore_downstream(
    starting_id: str,
    depth: Optional[int] = None,
    config: Config = Depends(get_settings),
    _: User = Depends(read_user_protected_role_dependency)
) -> LineageResponse:
    """    explore_downstream
        Explores in the downstream direction (outputs/results)
        starting at the specified node handle ID. The search 
        depth is bounded by the depth parameter which has a default
        maximum of 100.

        Arguments
        ----------
        starting_id : str
            The handle ID to start at.
        depth : int, optional
            The maximum depth to traverse in this direction, by default depth_upper_limit

        Returns
        -------
         : LineageResponse
            A status, node count, and networkx serialised graph response.

        See Also (optional)
        --------

        Examples (optional)
        --------
    """
    if not depth:
        depth = config.depth_default_limit

    if depth > config.depth_upper_limit:
        raise HTTPException(
            status_code=400,
            detail=f"Depth provided is in excess of depth maximum: {config.depth_upper_limit}."
        )

    # we want to make a proxied request directly using the service account
    request_style = RequestStyle(user_direct=None, service_account=ServiceAccountProxy(
        direct_service=True, on_behalf_username=None))

    # validate starting point
    await unknown_validator(id=starting_id, config=config, request_style=request_style)

    # make lineage query
    json_serialisation: Dict[str, Any] = prov_connector.downstream_query(
        starting_id=starting_id,
        depth=depth,
        config=config
    )

    # record count := length of the nodes list in response
    node_count = len(json_serialisation['nodes'])

    return LineageResponse(
        status=Status(
            success=True,
            details=f"Made downstream query (with depth {depth}) to neo4j backend."
        ),
        record_count=node_count,
        graph=json_serialisation
    )


@router.get("/special/contributing_datasets", response_model=LineageResponse, operation_id="special_contributing_datasets")
async def contributing_datasets(
    starting_id: str,
    depth: Optional[int] = None,
    config: Config = Depends(get_settings),
    _: User = Depends(read_user_protected_role_dependency)
) -> LineageResponse:
    if not depth:
        depth = config.depth_specialised_default_limit

    if depth > config.depth_upper_limit:
        raise HTTPException(
            status_code=400,
            detail=f"Depth provided is in excess of depth maximum: {config.depth_upper_limit}."
        )

    # we want to make a proxied request directly using the service account
    request_style = RequestStyle(user_direct=None, service_account=ServiceAccountProxy(
        direct_service=True, on_behalf_username=None))

    # validate starting point
    await unknown_validator(id=starting_id, config=config, request_style=request_style)

    # make lineage query
    json_serialisation: Dict[str, Any] = prov_connector.special_contributing_dataset_query(
        starting_id=starting_id,
        depth=depth,
        config=config
    )

    # record count := length of the nodes list in response
    node_count = len(json_serialisation['nodes'])

    return LineageResponse(
        status=Status(
            success=True,
            details=f"Made upstream contribution query (with depth {depth}) to neo4j backend."
        ),
        record_count=node_count,
        graph=json_serialisation
    )


@router.get("/special/effected_datasets", response_model=LineageResponse, operation_id="special_effected_datasets")
async def effected_datasets(
    starting_id: str,
    depth: Optional[int] = None,
    config: Config = Depends(get_settings),
    _: User = Depends(read_user_protected_role_dependency)
) -> LineageResponse:
    if not depth:
        depth = config.depth_specialised_default_limit

    if depth > config.depth_upper_limit:
        raise HTTPException(
            status_code=400,
            detail=f"Depth provided is in excess of depth maximum: {config.depth_upper_limit}."
        )

    # we want to make a proxied request directly using the service account
    request_style = RequestStyle(user_direct=None, service_account=ServiceAccountProxy(
        direct_service=True, on_behalf_username=None))

    # validate starting point
    await unknown_validator(id=starting_id, config=config, request_style=request_style)

    # make lineage query
    json_serialisation: Dict[str, Any] = prov_connector.special_effected_dataset_query(
        starting_id=starting_id,
        depth=depth,
        config=config
    )

    # record count := length of the nodes list in response
    node_count = len(json_serialisation['nodes'])

    return LineageResponse(
        status=Status(
            success=True,
            details=f"Made downstream effect query (with depth {depth}) to neo4j backend."
        ),
        record_count=node_count,
        graph=json_serialisation
    )


@router.get("/special/contributing_agents", response_model=LineageResponse, operation_id="special_contributing_agents")
async def contributing_agents(
    starting_id: str,
    depth: Optional[int] = None,
    config: Config = Depends(get_settings),
    _: User = Depends(read_user_protected_role_dependency)
) -> LineageResponse:
    if not depth:
        depth = config.depth_specialised_default_limit

    if depth > config.depth_upper_limit:
        raise HTTPException(
            status_code=400,
            detail=f"Depth provided is in excess of depth maximum: {config.depth_upper_limit}."
        )

    # we want to make a proxied request directly using the service account
    request_style = RequestStyle(user_direct=None, service_account=ServiceAccountProxy(
        direct_service=True, on_behalf_username=None))

    # validate starting point
    await unknown_validator(id=starting_id, config=config, request_style=request_style)

    # make lineage query
    json_serialisation: Dict[str, Any] = prov_connector.special_contributing_agent_query(
        starting_id=starting_id,
        depth=depth,
        config=config
    )

    # record count := length of the nodes list in response
    node_count = len(json_serialisation['nodes'])

    return LineageResponse(
        status=Status(
            success=True,
            details=f"Made upstream contribution query (with depth {depth}) to neo4j backend."
        ),
        record_count=node_count,
        graph=json_serialisation
    )


@router.get("/special/effected_agents", response_model=LineageResponse, operation_id="special_effected_agents")
async def effected_agents(
    starting_id: str,
    depth: Optional[int] = None,
    config: Config = Depends(get_settings),
    _: User = Depends(read_user_protected_role_dependency)
) -> LineageResponse:
    if not depth:
        depth = config.depth_specialised_default_limit

    if depth > config.depth_upper_limit:
        raise HTTPException(
            status_code=400,
            detail=f"Depth provided is in excess of depth maximum: {config.depth_upper_limit}."
        )

    # we want to make a proxied request directly using the service account
    request_style = RequestStyle(user_direct=None, service_account=ServiceAccountProxy(
        direct_service=True, on_behalf_username=None))

    # validate starting point
    await unknown_validator(id=starting_id, config=config, request_style=request_style)

    # make lineage query
    json_serialisation: Dict[str, Any] = prov_connector.special_effected_agent_query(
        starting_id=starting_id,
        depth=depth,
        config=config
    )

    # record count := length of the nodes list in response
    node_count = len(json_serialisation['nodes'])

    return LineageResponse(
        status=Status(
            success=True,
            details=f"Made downstream effect query (with depth {depth}) to neo4j backend."
        ),
        record_count=node_count,
        graph=json_serialisation
    )


@router.get("/generate/report", response_class = FileResponse, operation_id="export_prov_graph")
# Setup the endpoint inputs.
async def export_graph(
    node_id: str,
    depth: int, 
    item_subtype: ItemSubType,
    background_tasks: BackgroundTasks,
    roles: ProtectedRole = Depends(read_user_protected_role_dependency),
    config: Config = Depends(get_settings),  
) -> FileResponse:
    
    """Exports the provenance graph upto a certain upstream depth and fixed downstream depth (1) for Study and Model Run based entities.  
    This generates a Word Document (.docx) and contains the input, outputs and model runs involved within the Study or within the Model Run. 

    Parameters
    ----------
    node_id : str
        The ID of the starting node for which the report will be generated (Study or Model Run). 
    depth : int
        The depth for the upstream direction traversal.
    item_subtype : ItemSubType
        The type of the node, which can be either MODEL_RUN or STUDY, determining which report generation path is followed.
    background_tasks : BackgroundTasks
        FastAPI background task handler which manage tasks such as cleaning up temporary files. 

    Returns
    -------
    FileResponse
        A FileResponse object that contains the generated word-document and is sent to the front-end. 

    Raises
    ------
    HTTPException
        Raised if the input depth is invalid (not within the range of 1 to 3).
    HTTPException
        Raised if an unsupported item subtype is provided.
    HTTPException
        Raised if there is an error in generating the word document.

    """
         
    # Create the request style, here we assert where the HTTP request came from. 
    request_style: RequestStyle = RequestStyle(
        user_direct=roles.user, service_account=None
    )

    # Validate the depth.
    if depth < 1 or depth > 3: 
        raise HTTPException(status_code=400, detail="Invalid input depth provided. Input depth is only from 1 to 3")
    
    # do checks accordingly. 
    await validate_node_id(node_id=node_id, item_subtype=item_subtype, request_style=request_style, config=config)

    # This acting as a shared dictionary across both edge cases and in the helper function in the edge cases.
    # Could be converted into a dataclass maybe??
    all_filtered_responses: Dict[str, List[Node]] = {"inputs": [], "outputs": [], "model_runs": []}

    if item_subtype == ItemSubType.MODEL_RUN: 
        await generate_report_helper(starting_id=node_id, upstream_depth=depth, shared_responses=all_filtered_responses, config=config)

    elif item_subtype == ItemSubType.STUDY: 

        """
        Upstream (Outputs):
        Example: From a study, it will fetch all model runs associated with the study and their inputs, up to 3 layers upstream.

        Downstream (Outputs): 
        Example: From a study, it will fetch all relevant datasets (outputs) from the model runs linked to the study, up to 1 layer downstream.
        """
    
        # Query upstream to get all linked model runs at depth 1. 
        # This may contain more than one model run.
        upstream_model_run_response = await explore_downstream(starting_id=node_id, depth=1, config=config)
        assert upstream_model_run_response.graph, "Node collections not found!"

        model_run_nodes: List[Node]= parse_nodes(upstream_model_run_response.graph.get('nodes', []))

        # Now branch out with the model runs in here and explore them as above (depth 1-3 upstream and depth 1 downstream)
        # The model run will be the new updated starting id.

        for model_run_node in model_run_nodes:
            if model_run_node.item_subtype == ItemSubType.MODEL_RUN:
                model_run_id = model_run_node.id
                # Extract the upstream and downstream entities from this node. 
                await generate_report_helper(starting_id=model_run_id, upstream_depth=depth, shared_responses=all_filtered_responses, config=config)                

    else: 
        raise HTTPException(status_code=400, detail="Unsupported node requested.")
    

    # All the nodes involved in the model run/study have been populated. 
    generated_doc_path = generate_word_file()

    if os.path.exists(generated_doc_path): 
        background_tasks.add_task(remove_file, file_path=generated_doc_path)

        return FileResponse(
            path = generated_doc_path, 
            filename= "generated-doc.docx"
        )
    
    else:
        raise HTTPException(status_code=400, detail="Error generating your study-closeout document.")
        






