"""Factory for creating table backends."""
from typing import Optional

from .backends.dynamodb import DynamoDBBackend
from .backends.postgres import PostgresBackend


def get_backend(
    table_name: str,
    backend_type: str = "dynamodb",
    database_url: Optional[str] = None,
):
    """Get table backend. backend_type: 'dynamodb' or 'postgres'."""
    if backend_type == "postgres":
        if not database_url:
            raise ValueError("database_url required for postgres backend")
        return PostgresBackend(table_name, database_url)
    return DynamoDBBackend(table_name)
