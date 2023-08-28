from typing import Dict, Any, Dict
from SharedInterfaces.RegistryModels import RecordInfo
from SharedInterfaces.RegistryAPI import BundledItem, RecordType, ItemDataset, ReleasedStatus, ItemSubType


def f1458_migrator_function(old_item: Dict[str, Any], parse: bool = True) -> Dict[str, Any]:
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

    if subtype != ItemSubType.DATASET:
        print(
            f"Skipping non DATASET subtype: subtype {record_base.item_subtype}, id: {record_base.id}.")
        return old_item

    # Add default release status of not released
    item['release_status'] = ReleasedStatus.NOT_RELEASED

    history = item['history']

    for history_entry in history:
        # else, pass down its display name.
        history_entry['item']['release_status'] = ReleasedStatus.NOT_RELEASED

    # now parse the item to ensure it's valid as the specified type
    if parse:
        ItemDataset.parse_obj(item)

    # now update the bundled item with the updated item
    old_item['item_payload'] = item

    return old_item
