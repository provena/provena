from typing import Dict, Any, Dict
from ProvenaInterfaces.RegistryModels import RecordInfo, MODEL_TYPE_MAP, VersioningInfo
from ProvenaInterfaces.RegistryAPI import BundledItem, AuthTableEntry, RecordType, ItemCategory


def f1442_migrator_function(old_item: Dict[str, Any], parse: bool = True) -> Dict[str, Any]:
    # Parse the item as a bundle
    reg_item = BundledItem.parse_obj(old_item)

    # pull out the item payload
    item = reg_item.item_payload

    # check the type of the item and apply suitable modifiers if applicable
    record_base = RecordInfo.parse_obj(item)

    # Seeded items all good
    record_type = record_base.record_type
    if record_type == RecordType.SEED_ITEM:
        # no change required
        print(
            f"Skipping seed item - no changes here: type: {record_base.item_subtype}, id: {record_base.id}.")
        return old_item

    subtype = record_base.item_subtype
    category = record_base.item_category

    # Currently versioning enabled on Category == Entity
    if category != ItemCategory.ENTITY:
        print(
            f"Skipping non ENTITY category: subtype {record_base.item_subtype}, id: {record_base.id}.")
        return old_item

    # check cat/sub validity
    item_model = MODEL_TYPE_MAP.get((category, subtype))
    if item_model is None:
        raise ValueError(f"inappropriate cat/sub type: {(category, subtype)}")

    # We need to add versioning for these types
    item['versioning_info'] = VersioningInfo(version=1).dict(exclude_none=True)

    # now parse the item to ensure it's valid as the specified type
    if parse:
        item_model.parse_obj(item)

    # now update the bundled item with the updated item
    old_item['item_payload'] = item

    return old_item
