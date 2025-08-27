from fastapi import APIRouter, Depends, HTTPException
from helpers.config_response import generate_config_route
from config import base_config, get_settings, Config
from typing import Optional, Dict
from KeycloakFastAPI.Dependencies import User, ProtectedRole
from dependencies.dependencies import admin_user_protected_role_dependency
from ProvenaInterfaces.ProvenanceAPI import PostDeleteGraphRequest, PostDeleteGraphResponse
from helpers.registry_helpers import fetch_item_from_registry_with_subtype, fetch_item_from_registry
from ProvenaInterfaces.RegistryModels import ItemSubType
from helpers.prov_connector import NodeGraph, Neo4jGraphManager, GraphDiffApplier, diff_graphs
from helpers.util import py_to_dict
from typing import List

router = APIRouter()

# Add the config route
generate_config_route(
    router=router,
    # has admin prefix
    route_path="/config"
)

# Admin only sentry debug endpoint to ensure it is reporting events


@router.get("/sentry-debug", operation_id="test_sentry_reporting")
async def trigger_error(
    user: User = Depends(admin_user_protected_role_dependency)
) -> Optional[Dict[str, str]]:

    if base_config.monitoring_enabled and base_config.sentry_dsn:
        division_by_zero = 1 / 0
    else:
        return {
            "message": f"Monitoring is disabled by configuration. Not going to trigger fake error. " +
            f"Monitoring enabled: {base_config.monitoring_enabled}, and required DSN: {base_config.sentry_dsn}."
        }
    return None

# We can expand this list in future if we want to allow deletion of other types
ALLOWED_DELETION_TYPES: List[ItemSubType] = [
    ItemSubType.MODEL_RUN,
    ItemSubType.STUDY
]


@router.post("/delete-provenance-record", operation_id="delete_provenance_record", include_in_schema=True)
async def delete_model_run(
    delete: PostDeleteGraphRequest,
    # admin only for this endpoint
    roles: ProtectedRole = Depends(admin_user_protected_role_dependency),
    config: Config = Depends(get_settings)
) -> PostDeleteGraphResponse:
    """

    Delete a provenance record and all associated provenance information from the graph database.

    Parameters
    ----------
    delete : PostDeleteGraphRequest
        The delete payload containing the record ID to delete and trial mode flag.

    Returns
    -------
    PostDeleteGraphResponse
        Diff - applied or not applied depending on trial mode flag.
    """
    # Get the item generically
    item = await fetch_item_from_registry(id=delete.record_id, config=config)

    # Ensure it is of an allowed type
    if item.item_subtype not in ALLOWED_DELETION_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Item with id {delete.record_id} is of type {item.item_subtype} which is not allowed to be deleted. Allowed types are: {ALLOWED_DELETION_TYPES}"
        )

    # dummy delete graph which is just an empty graph with the record id to delete
    delete_dummy_graph = NodeGraph(record_id=delete.record_id, links=[])

    print("Setting up neo4j client")
    neo4j_manager = Neo4jGraphManager(config=config)
    print("Done")

    # Getting old graph
    print("Retrieving existing graph")
    old_graph = neo4j_manager.get_graph_by_record_id(delete.record_id)
    print("Done")

    if (delete.trial_mode):
        print("Trial mode, not applying delete")
        print("Building diff")
        try:
            diff_list = diff_graphs(
                old_graph=old_graph, new_graph=delete_dummy_graph)
            print(f"Diff list generated with {len(diff_list)} entries")
            return PostDeleteGraphResponse(
                diff=list(map(lambda diff: py_to_dict(diff), diff_list))
            )
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Exception: could not produce graph diff: {e}"
            ) from e

    else:
        try:
            # get the graph diff
            print("Building diff (empty) and applying...")
            diff_list = diff_graphs(
                old_graph=old_graph, new_graph=delete_dummy_graph)
            diff_generator = GraphDiffApplier(neo4j_manager=neo4j_manager)
            diff_generator.apply_diff(
                old_graph=old_graph, new_graph=delete_dummy_graph)
            return PostDeleteGraphResponse(
                diff=list(map(lambda diff: py_to_dict(diff), diff_list))
            )
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Exception: could not apply graph diff: {e}"
            ) from e
