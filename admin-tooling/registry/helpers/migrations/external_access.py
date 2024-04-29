from typing import Dict, Any
from ProvenaInterfaces.RegistryModels import AccessInfo, ItemDataset
from ProvenaInterfaces.RegistryAPI import BundledItem
import json

default_info = json.loads(AccessInfo(
    reposited=True
).json(exclude_none=True))


def external_access(old_item: Dict[str, Any]) -> Dict[str, Any]:
    # Parse the item as a registry item and dataset
    reg_item = BundledItem.parse_obj(old_item)
    resource = reg_item.item_payload

    if resource.get("item_subtype") != "DATASET":
        return old_item

    print("Dataset found - migrating:")
    old_item["item_payload"]["collection_format"]["dataset_info"]["access_info"] = default_info

    # validate that new item is parsable
    ItemDataset.parse_obj(old_item["item_payload"])

    return old_item
