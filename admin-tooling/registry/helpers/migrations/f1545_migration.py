from typing import Dict, Any, Dict
from ProvenaInterfaces.RegistryModels import RecordInfo
from ProvenaInterfaces.RegistryAPI import BundledItem, RecordType, ItemDataset, ReleasedStatus, ItemSubType


def f1545_migrator_function(old_item: Dict[str, Any], parse: bool = True) -> Dict[str, Any]:
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

    access_info = item['collection_format']['dataset_info']['access_info']
    if access_info['reposited']:
        pass 
    else: # there will be a field for the access info uri
        item['access_info_uri'] = access_info['uri']

    # now for each history item if it is non reposited.
    for hist_entry in item["history"]:
        access_info = hist_entry['item']['collection_format']['dataset_info']['access_info']
        if access_info['reposited']:
            pass
        else:  # there will be a field for the access info uri
            hist_entry['item']['access_info_uri'] = access_info['uri']

    # now parse the item to ensure it's valid as the specified type
    # this will validate that both uri's match.
    if parse:
        ItemDataset.parse_obj(item)

    # now update the bundled item with the updated item
    old_item['item_payload'] = item

    return old_item
