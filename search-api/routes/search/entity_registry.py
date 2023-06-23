from dependencies.dependencies import search_entity_registry_protected_role_dependency
from dependencies.open_search_client import get_search_client
from config import Config, get_settings
from opensearchpy import OpenSearch
from KeycloakFastAPI.Dependencies import ProtectedRole
from fastapi import APIRouter, Depends, HTTPException
from SharedInterfaces.SearchAPI import *
from SharedInterfaces.SharedTypes import Status
from SharedInterfaces.RegistryModels import ALL_SEARCHABLE_FIELDS, ItemSubType
from helpers.search_helpers import *
from typing import Optional


router = APIRouter()

# search the entity registry


@router.get("/entity-registry", response_model=QueryResults, operation_id="search_entity_registry")
async def search_entity_registry(
    query: str,
    subtype_filter: Optional[ItemSubType] = None,
    record_limit: Optional[int] = None,
    search_client: OpenSearch = Depends(get_search_client),
    config: Config = Depends(get_settings),
    role: ProtectedRole = Depends(
        search_entity_registry_protected_role_dependency),
) -> QueryResults:
    # pull out user for later use
    user = role.user

    # searchable fields
    searchable_fields = ALL_SEARCHABLE_FIELDS

    # item subtype field
    item_subtype_field = "item_subtype"

    # work out appropriate record count - bounded upper by config max
    size = min(
        record_limit, config.max_query_size) if record_limit else config.default_query_size

    if subtype_filter is None:
        try:
            results: Dict[str, Any] = query_linearised_index(
                index=config.registry_index,
                query=query,
                config=config,
                client=search_client,
                size=size
            )

        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to search, error: {e}"
            )
    else:
        try:
            results = query_linearised_index_with_filter(
                index=config.registry_index,
                query=query,
                config=config,
                client=search_client,
                size=size,
                must_match_text=subtype_filter.value,
                must_match_field=item_subtype_field
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
            output_results.append(QueryResult(
                # id field for registry items is just id
                id=hit['_source']['id'],
                score=hit['_score']
            ))
        except Exception as e:
            warnings.append(
                f"Failed to create response - probably invalid index object. {e}")

    return QueryResults(
        status=Status(
            success=True,
            details=f"Returned {len(output_results)} results with {'no' if len(warnings) == 0 else len(warnings)} issues."
        ),
        results=output_results,
        warnings=warnings if len(warnings) > 0 else None
    )
