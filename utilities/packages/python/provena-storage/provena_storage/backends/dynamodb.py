"""DynamoDB backend - wraps boto3 DynamoDB table."""
import boto3
from typing import Any, Dict, Optional

from .base import TableBackend


class DynamoDBBackend(TableBackend):
    """DynamoDB table backend."""

    def __init__(self, table_name: str):
        self._resource = boto3.resource("dynamodb")
        self._table = self._resource.Table(table_name)

    def get_item(self, Key: Dict[str, Any]) -> Dict[str, Any]:
        return self._table.get_item(Key=Key)

    def put_item(self, Item: Dict[str, Any]) -> None:
        self._table.put_item(Item=Item)

    def delete_item(self, Key: Dict[str, Any]) -> None:
        self._table.delete_item(Key=Key)

    def scan(
        self,
        FilterExpression: Optional[Any] = None,
        ExclusiveStartKey: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        kwargs: Dict[str, Any] = {}
        if FilterExpression is not None:
            kwargs["FilterExpression"] = FilterExpression
        if ExclusiveStartKey is not None:
            kwargs["ExclusiveStartKey"] = ExclusiveStartKey
        return self._table.scan(**kwargs)

    def query(
        self,
        IndexName: str,
        KeyConditionExpression: Any,
        ScanIndexForward: bool = True,
        FilterExpression: Optional[Any] = None,
        Limit: Optional[int] = None,
        ExclusiveStartKey: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        kwargs: Dict[str, Any] = {
            "IndexName": IndexName,
            "KeyConditionExpression": KeyConditionExpression,
            "ScanIndexForward": ScanIndexForward,
        }
        if FilterExpression is not None:
            kwargs["FilterExpression"] = FilterExpression
        if Limit is not None:
            kwargs["Limit"] = Limit
        if ExclusiveStartKey is not None:
            kwargs["ExclusiveStartKey"] = ExclusiveStartKey
        return self._table.query(**kwargs)

    def batch_writer(self):
        return self._table.batch_writer()
