from typing import Any, Dict
from ProvenaInterfaces.RegistryAPI import BundledItem


def example_migration(old_item: Dict[str, Any]) -> Dict[str, Any]:
    # Parse the item as a bundle
    reg_item = BundledItem.parse_obj(old_item)

    # pull out the item payload
    item = reg_item.item_payload

    # fake modification
    # item['field'] = 'new_value'

    # return the 'modified' item
    return old_item
