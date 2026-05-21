"""PostgreSQL backend - DynamoDB-like interface using JSONB."""
import json
import sqlalchemy
from sqlalchemy import text
from typing import Any, Dict, List, Optional

from .base import TableBackend, BatchWriterContext

class PostgresBackend(TableBackend):
    """PostgreSQL backend with DynamoDB-like interface."""

    def __init__(self, table_name: str, database_url: str):
        self.table_name = table_name
        self.engine = sqlalchemy.create_engine(database_url)

    def _get_connection(self):
        return self.engine.connect()

    def get_item(self, Key: Dict[str, Any]) -> Dict[str, Any]:
        item_id = Key.get("id")
        if not item_id:
            return {}
        with self._get_connection() as conn:
            result = conn.execute(
                text("SELECT data FROM {} WHERE id = :id".format(self.table_name)),
                {"id": item_id},
            )
            row = result.fetchone()
        if not row:
            return {}
        data = row[0]
        if isinstance(data, str):
            data = json.loads(data)
        item = dict(data)
        item["id"] = item_id
        return {"Item": item}

    def put_item(self, Item: Dict[str, Any]) -> None:
        item_id = Item.get("id")
        if not item_id:
            raise ValueError("Item must have 'id' key")
        data = json.dumps({k: v for k, v in Item.items()})
        with self._get_connection() as conn:
            conn.execute(
                text("""
                    INSERT INTO {} (id, data) VALUES (:id, :data::jsonb)
                    ON CONFLICT (id) DO UPDATE SET data = :data::jsonb
                """.format(self.table_name)),
                {"id": item_id, "data": data},
            )
            conn.commit()

    def delete_item(self, Key: Dict[str, Any]) -> None:
        item_id = Key.get("id")
        if not item_id:
            return
        with self._get_connection() as conn:
            conn.execute(
                text("DELETE FROM {} WHERE id = :id".format(self.table_name)),
                {"id": item_id},
            )
            conn.commit()

    def _apply_filter(self, items: List[Dict], filter_dict: Optional[Dict]) -> List[Dict]:
        """Apply simple key=value filter."""
        if not filter_dict:
            return items
        result = []
        for item in items:
            match = True
            for k, v in filter_dict.items():
                if item.get(k) != v:
                    match = False
                    break
            if match:
                result.append(item)
        return result

    def scan(
        self,
        FilterExpression: Optional[Any] = None,
        ExclusiveStartKey: Optional[Dict[str, Any]] = None,
        filter_dict: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Scan table. Uses filter_dict when provided (from QueryFilter)."""
        with self._get_connection() as conn:
            result = conn.execute(
                text("SELECT id, data FROM {}".format(self.table_name))
            )
            rows = result.fetchall()
        items = []
        for row in rows:
            data = row[1]
            if isinstance(data, str):
                data = json.loads(data)
            item = dict(data)
            item["id"] = row[0]
            items.append(item)
        items = self._apply_filter(items, filter_dict)
        return {"Items": items}

    def query(
        self,
        IndexName: str,
        KeyConditionExpression: Any,
        ScanIndexForward: bool = True,
        FilterExpression: Optional[Any] = None,
        Limit: Optional[int] = None,
        ExclusiveStartKey: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Query with index. Maps index name to SQL ORDER BY."""
        # Parse index e.g. "universal_partition_key-updated_timestamp-index"
        parts = IndexName.replace("-index", "").split("-")
        partition_key = parts[0] if parts else "universal_partition_key"
        sort_key = parts[1] if len(parts) > 1 else "updated_timestamp"

        with self._get_connection() as conn:
            order = "ASC" if ScanIndexForward else "DESC"
            sql = """
                SELECT id, data FROM {}
                WHERE data->>'{pk}' = 'OK'
                ORDER BY (data->>'{sk}')::bigint NULLS LAST {ord}
            """.format(
                self.table_name,
                pk=partition_key.replace("'", "''"),
                sk=sort_key.replace("'", "''"),
                ord=order,
            )
            if Limit:
                sql += " LIMIT {}".format(Limit)
            result = conn.execute(text(sql))
            rows = result.fetchall()
        items = []
        for row in rows:
            data = row[1]
            if isinstance(data, str):
                data = json.loads(data)
            item = dict(data)
            item["id"] = row[0]
            items.append(item)
        return {"Items": items}
