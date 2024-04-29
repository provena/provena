from dependencies.dependencies import search_global_protected_role_dependency
from dependencies.open_search_client import get_search_client
from config import Config, get_settings
from opensearchpy import OpenSearch
from KeycloakFastAPI.Dependencies import ProtectedRole
from fastapi import APIRouter, Depends, HTTPException
from ProvenaInterfaces.SearchAPI import *
from ProvenaInterfaces.SharedTypes import Status

from helpers.search_helpers import *


router = APIRouter()

# search the global alias index


@router.get("/global", response_model=MixedQueryResults, operation_id="global_search")
async def search_global(
    query: str,
    record_limit: Optional[int] = None,
    search_client: OpenSearch = Depends(get_search_client),
    config: Config = Depends(get_settings),
    role: ProtectedRole = Depends(search_global_protected_role_dependency),
) -> MixedQueryResults:
    # pull out user for later use
    user = role.user

    # work out appropriate record count - bounded upper by config max
    size = min(
        record_limit, config.max_query_size) if record_limit else config.default_query_size

    # searchable fields TODO optimise this to prioritise ID/handle - merging
    # could cause duplicates
    searchable_fields = ["*"]

    try:
        results: Dict[str, Any] = multi_match_query_index(
            index=config.global_index,
            query=query,
            fields=searchable_fields,
            config=config,
            client=search_client,
            size=size
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to search, error: {e}"
        )

    # filter results based on auth?? Other hooks?
    # TODO
    hits = results.get('hits')

    if hits is None:
        raise HTTPException(
            status_code=500,
            detail=f"Expected to find hits in search response - no hits field."
        )
    hits = hits.get('hits')
    if hits is None:
        raise HTTPException(
            status_code=500,
            detail=f"Expected to find hits in search response - no hits field."
        )

    warnings: List[str] = []
    output_results: List[QueryResult] = []
    for hit in hits:
        try:
            hit_index = hit['_index']
            type: Optional[SearchResultType] = None
            if hit_index == config.registry_index:
                type = SearchResultType.REGISTRY_ITEM
                record_id = hit['_source']['id']
            else:
                raise HTTPException(
                    status_code=400,
                    detail=f"Encountered unexpected aliased index {hit_index}. Aborting."
                )
            output_results.append(MixedQueryResult(
                # id field for registry items is just id
                id=record_id,
                score=hit['_score'],
                type=type
            ))
        except Exception as e:
            warnings.append(
                f"Failed to create response - probably invalid index object. {e}")

    return MixedQueryResults(
        status=Status(
            success=True,
            details=f"Returned {len(output_results)} results with {'no' if len(warnings) == 0 else len(warnings)} issues."
        ),
        results=output_results,
        warnings=warnings if len(warnings) > 0 else None
    )
