from typing import Dict, Any, List, Type, Optional
from SharedInterfaces.RegistryModels import AccessInfo, ItemDataset, HistoryEntry, HistoryBase, RecordInfo, AuthTableEntry, MODEL_DOMAIN_INFO_TYPE_MAP, DomainInfoBase, RecordType
from SharedInterfaces.RegistryAPI import BundledItem
from pydantic import BaseModel
import json
from helpers.util import py_to_dict


def generate_item_history(item: Dict[str, Any], username: str) -> List[HistoryEntry]:
    rec_info = RecordInfo.parse_obj(item)

    category = rec_info.item_category
    subtype = rec_info.item_subtype
    record_type = rec_info.record_type
    assert record_type == RecordType.COMPLETE_ITEM

    # pull out just the domain info component so we can parse and dump it to filter full item contents
    domain_info_type: Optional[Type[DomainInfoBase]
                               ] = MODEL_DOMAIN_INFO_TYPE_MAP.get((category, subtype))
    
    if domain_info_type is None:
        raise ValueError(
            f"ID: {rec_info.id} had invalid category/subtype combination : {(category, subtype)}... Aborting")
        
    domain_part_of_item = py_to_dict(domain_info_type.parse_obj(item))

    # to avoid complex generic typing issues here -just use a dict
    history_entry = HistoryEntry[domain_info_type](  # type: ignore
        id=0,
        timestamp=rec_info.updated_timestamp,
        reason='(Auto) Initial generation of item history.',
        username=username,
        item=domain_part_of_item
    )

    return [history_entry]


def add_starting_history(old_item: Dict[str, Any]) -> Dict[str, Any]:
    # Parse the item as a bundle
    reg_item = BundledItem.parse_obj(old_item)
    

    # pull out the item payload
    item = reg_item.item_payload

    rec_info = RecordInfo.parse_obj(item)
    record_type = rec_info.record_type
    if record_type == RecordType.SEED_ITEM:
        # no change required
        return old_item
    
    existing_history = item.get('history')
    
    if existing_history is not None:
        raise ValueError(
            f"The item that is being migrated {reg_item.id} already has a history field! Aborting.")

    # find the username from the auth payload
    auth_info = AuthTableEntry.parse_obj(reg_item.auth_payload)
    username = auth_info.access_settings.owner

    # generate history
    history = generate_item_history(item=item, username=username)

    old_item['item_payload']['history'] = list(map(py_to_dict, history))
    return old_item
