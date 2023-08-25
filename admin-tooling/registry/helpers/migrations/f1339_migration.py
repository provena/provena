from typing import Any, Dict
from SharedInterfaces.RegistryAPI import BundledItem
from SharedInterfaces.RegistryModels import ItemSubType, RecordType


def f1339_migration(old_item: Dict[str, Any]) -> Dict[str, Any]:
    # Parse the item as a bundle
    reg_item = BundledItem.parse_obj(old_item)

    # pull out the item payload
    item = reg_item.item_payload

    if item['item_subtype']==ItemSubType.MODEL_RUN and item['record_type']==RecordType.COMPLETE_ITEM:
        curr_name = item['record'].get('display_name')
        if curr_name is not None and curr_name != '':
            # skip items that already have a display name inside their record info 
            # (should be none unless a user has made one in between changes
            # being deployed and this script being run on that deployment.)
            print(f"Skipping item model run item disp name: '{item['display_name']}' with existing display name")
            return old_item

        
        # else, need to give it a display name.
        # pass down the previous default display name into the record.
        old_item['item_payload']['record']['display_name'] = item['display_name']

        history = old_item['item_payload']['history']

        for history_entry in history:
            curr_hist_disp_name = history_entry['item']['record'].get('display_name')
            if curr_hist_disp_name is not None and curr_hist_disp_name != '':
                pass

            # else, pass down its display name.
            history_entry['item']['record']['display_name'] = history_entry['item']['display_name']

    # return the 'modified' item
    return old_item
