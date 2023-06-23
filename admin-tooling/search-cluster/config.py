from pydantic import BaseSettings
from enum import Enum

LINEARISED_FIELD = "body"

class Indexes(str, Enum):
    DATA_STORE = "DATA_STORE"
    REGISTRY = "REGISTRY"
    GLOBAL = "GLOBAL"


INDEX_MAP = {
    Indexes.DATA_STORE: "data_store_index",
    Indexes.REGISTRY: "registry_index",
    Indexes.GLOBAL: "global_index"
}


class SearchableObject(str, Enum):
    DATA_STORE_ITEM = "DATA_STORE_ITEM"
    REGISTRY_ITEM = "REGISTRY_ITEM"