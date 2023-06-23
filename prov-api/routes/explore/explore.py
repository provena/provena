from dependencies.dependencies import read_user_protected_role_dependency, read_write_user_protected_role_dependency, user_general_dependency, admin_user_protected_role_dependency
from KeycloakFastAPI.Dependencies import User
from fastapi import APIRouter, Depends, HTTPException
from SharedInterfaces.ProvenanceAPI import *
from SharedInterfaces.ProvenanceModels import *
from SharedInterfaces.SharedTypes import Status
from helpers.entity_validators import unknown_validator, RequestStyle, ServiceAccountProxy
import helpers.neo4j_helpers as neo4j_helpers
from typing import Dict, Any
from config import Config, get_settings

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
            The maximum depth to traverse in this direction, by default DEPTH_UPPER_LIMIT

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
        depth = config.DEPTH_DEFAULT_LIMIT

    if depth > config.DEPTH_UPPER_LIMIT:
        raise HTTPException(
            status_code=400,
            detail=f"Depth provided is in excess of depth maximum: {config.DEPTH_UPPER_LIMIT}."
        )

    # we want to make a proxied request directly using the service account
    request_style = RequestStyle(user_direct=None, service_account=ServiceAccountProxy(
        direct_service=True, on_behalf_username=None))

    # validate starting point
    await unknown_validator(id=starting_id, config=config, request_style=request_style)

    # make lineage query
    json_serialisation: Dict[str, Any] = neo4j_helpers.upstream_query(
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
            The maximum depth to traverse in this direction, by default DEPTH_UPPER_LIMIT

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
        depth = config.DEPTH_DEFAULT_LIMIT

    if depth > config.DEPTH_UPPER_LIMIT:
        raise HTTPException(
            status_code=400,
            detail=f"Depth provided is in excess of depth maximum: {config.DEPTH_UPPER_LIMIT}."
        )

    # we want to make a proxied request directly using the service account
    request_style = RequestStyle(user_direct=None, service_account=ServiceAccountProxy(
        direct_service=True, on_behalf_username=None))

    # validate starting point
    await unknown_validator(id=starting_id, config=config, request_style=request_style)

    # make lineage query
    json_serialisation: Dict[str, Any] = neo4j_helpers.downstream_query(
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
