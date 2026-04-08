"""
Adapter to make DynamoDB and Postgres backends interchangeable.
Wraps boto3 DynamoDB table to accept filter (QueryFilter) in scan(),
and provides filter_dict for Postgres.
"""
from typing import Any, Dict, Optional
from ProvenaInterfaces.RegistryModels import QueryFilter


def query_filter_to_dict(filter: Optional[QueryFilter]) -> Optional[Dict[str, Any]]:
    """Convert QueryFilter to simple dict for Postgres WHERE."""
    if not filter:
        return None
    d = {}
    if filter.item_category:
        d["item_category"] = filter.item_category.value
    if filter.item_subtype:
        d["item_subtype"] = filter.item_subtype.value
    if filter.record_type:
        if filter.record_type.value == "COMPLETE_ONLY":
            d["record_type"] = "COMPLETE_ITEM"
        elif filter.record_type.value == "SEED_ONLY":
            d["record_type"] = "SEED_ITEM"
    return d if d else None


def is_postgres_backend(table: Any) -> bool:
    """Check if table is PostgresBackend (from provena_storage)."""
    return getattr(table, "__class__", None).__name__ == "PostgresBackend"
