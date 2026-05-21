"""Base interface for table backends."""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class TableBackend(ABC):
    """Abstract base for DynamoDB-like table operations."""

    @abstractmethod
    def get_item(self, Key: Dict[str, Any]) -> Dict[str, Any]:
        """Get item by key. Returns {'Item': {...}} or {}."""
        pass

    @abstractmethod
    def put_item(self, Item: Dict[str, Any]) -> None:
        """Put item."""
        pass

    @abstractmethod
    def delete_item(self, Key: Dict[str, Any]) -> None:
        """Delete item by key."""
        pass

    @abstractmethod
    def scan(
        self,
        FilterExpression: Optional[Any] = None,
        ExclusiveStartKey: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Scan table. Returns {'Items': [...], 'LastEvaluatedKey': ...}."""
        pass

    @abstractmethod
    def query(
        self,
        IndexName: str,
        KeyConditionExpression: Any,
        ScanIndexForward: bool = True,
        FilterExpression: Optional[Any] = None,
        Limit: Optional[int] = None,
        ExclusiveStartKey: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Query table. Returns {'Items': [...], 'LastEvaluatedKey': ...}."""
        pass

    def batch_writer(self) -> "BatchWriterContext":
        """Return batch writer context manager."""
        return BatchWriterContext(self)


class BatchWriterContext:
    """Context manager for batch writes."""

    def __init__(self, backend: TableBackend):
        self.backend = backend
        self._puts: List[Dict[str, Any]] = []
        self._deletes: List[Dict[str, Any]] = []

    def put_item(self, Item: Dict[str, Any]) -> None:
        self._puts.append(Item)

    def delete_item(self, Key: Dict[str, Any]) -> None:
        self._deletes.append(Key)

    def __enter__(self) -> "BatchWriterContext":
        return self

    def __exit__(self, *args: Any) -> None:
        for item in self._puts:
            self.backend.put_item(Item=item)
        for key in self._deletes:
            self.backend.delete_item(Key=key)
