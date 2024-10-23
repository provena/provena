from fastapi import APIRouter, Depends, HTTPException
from ProvenaInterfaces.SharedTypes import StatusResponse, Status
from KeycloakFastAPI.Dependencies import User
from dependencies.dependencies import admin_user_protected_role_dependency
from config import Config, get_settings
from helpers.neo4j_helpers import run_query

router = APIRouter()

CLEAR_QUERY = "MATCH (n) DETACH DELETE n"

# This route is excluded from the schema so that its less visible to sticky beaks


@router.delete("/clear", response_model=StatusResponse, operation_id="clear_graph", include_in_schema=False)
async def clear_graph(
    _: User = Depends(admin_user_protected_role_dependency),
    config: Config = Depends(get_settings)
) -> StatusResponse:
    """
    clear_graph 

    Runs a clear query on the graph DB. 

    WARNING this will delete everything from the neo4j graph that backs the lineage queries. 

    This will incur downtime for lineage queries.

    The admin restore from registry endpoints should be used to return the graph to operation.

    Returns
    -------
    StatusResponse
        Status with success true if things worked

    Raises
    ------
    HTTPException
        500 error if something fails
    """
    try:
        response = run_query(
            query=CLEAR_QUERY,
            config=config
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to run the clear query, unsure of state of graph DB - error details: {e}"
        )

    return StatusResponse(status=Status(
        success=True,
        details="Successfully ran a clear query on the graph DB!"
    ))
