from typing import Dict, Any, Callable, List, Optional, Dict, Tuple
from ProvenaInterfaces.RegistryModels import OptionallyRequiredCheck, ItemSubType, RecordInfo, MODEL_TYPE_MAP
from ProvenaInterfaces.RegistryAPI import BundledItem, AuthTableEntry, CollectionFormatAssociations, RecordType
from helpers.util import py_to_dict


# map from (name, optional ror) -> ID for prod datasets
PROD_INFO_ORG_LOOKUP: Dict[Tuple[str, Optional[str]], str] = {
    # ADD LINKS AS REQUIRED - (Org name, org ror) -> ID to link to
}

STAGE_INFO_ORG_LOOKUP: Dict[Tuple[str, Optional[str]], str] = {
    # ADD LINKS AS REQUIRED - (Org name, org ror) -> ID to link to
}

STAGE_FALLTHROUGH = "TODO - add a fallthrough ID if required"


def determine_new_org_id_from_old_info(name: str, ror: Optional[str], stage: str) -> str:
    if (stage == "PROD"):
        org_id = PROD_INFO_ORG_LOOKUP.get((name, ror))

        if org_id is None:
            raise Exception(
                f"Cannot find an organisation from the PROD org lookup for name: {name}, ror: {ror}.")

        return org_id

    if (stage == "STAGE"):
        org_id = STAGE_INFO_ORG_LOOKUP.get((name, ror))

        if org_id is None:
            print(f"Using stage fallthrough for organisation link: {name = } {ror = } fallthrough = {STAGE_FALLTHROUGH}.")
            return STAGE_FALLTHROUGH

        return org_id
    
    else:
        raise Exception(
            "Cannot proceed with this migration for non PROD/STAGE stages. No mapping defined for other stages.")


def change_dataset_references(stage: str, item: Dict[str, Any]) -> Dict[str, Any]:
    # pull out dataset info
    collection_format = item['collection_format']

    # pull out all old info
    author_info = collection_format['author']

    old_org = author_info['organisation']
    old_org_name = old_org['name']
    optional_org_ror = old_org.get('ror')

    ds_info = collection_format['dataset_info']
    old_publisher = ds_info['publisher']
    old_publisher_name = old_publisher['name']
    optional_publisher_ror = old_publisher.get('ror')

    # put into new format

    # need to determine IDs for old author org and publisher org
    new_org_id = determine_new_org_id_from_old_info(
        name=old_org_name,
        ror=optional_org_ror,
        stage=stage
    )

    new_publisher_id = determine_new_org_id_from_old_info(
        name=old_publisher_name,
        ror=optional_publisher_ror,
        stage=stage
    )

    # now clean up into new format
    del collection_format['author']
    del collection_format['dataset_info']['publisher']

    collection_format['associations'] = py_to_dict(
        CollectionFormatAssociations(organisation_id=new_org_id))
    collection_format['dataset_info']['publisher_id'] = new_publisher_id

    return item


def remove_ro_crate(stage: str, old_item: Dict[str, Any]) -> Dict[str, Any]:
    del old_item['rocrate_metadata']
    return old_item


DataType = Dict[str, Any]
Stage = str
ModifierFunc = Callable[[Stage, DataType], DataType]
modifier_map: Dict[ItemSubType, List[ModifierFunc]] = {
    ItemSubType.DATASET: [
        remove_ro_crate,
        change_dataset_references
    ],
}


def add_owner_username(old_item: Dict[str, Any], username: str) -> Dict[str, Any]:
    old_item['owner_username'] = username
    return old_item


def f1176_migrator_function(stage: str, old_item: Dict[str, Any], parse: bool = True) -> Dict[str, Any]:
    # Parse the item as a bundle
    reg_item = BundledItem.parse_obj(old_item)

    # pull out the item payload
    item = reg_item.item_payload
    raw_auth = reg_item.auth_payload

    # parse the auth info
    auth = AuthTableEntry.parse_obj(raw_auth)

    # username
    username = auth.access_settings.owner

    # add username to the main record
    item = add_owner_username(old_item=item, username=username)

    # check the type of the item and apply suitable modifiers if applicable
    record_base = RecordInfo.parse_obj(item)

    record_type = record_base.record_type
    if record_type == RecordType.SEED_ITEM:
        # no change required
        print(
            f"Skipping seed item: type: {record_base.item_subtype}, id: {record_base.id}.")
        # now update the bundled item with the updated item
        old_item['item_payload'] = item
        return old_item

    subtype = record_base.item_subtype
    category = record_base.item_category

    # check cat/sub validity
    item_model = MODEL_TYPE_MAP.get((category, subtype))
    if item_model is None:
        raise ValueError(f"inappropriate cat/sub type: {(category, subtype)}")

    # get modifiers
    modifiers = modifier_map.get(subtype)

    # create a list of modification targets including all historical entries
    to_modify = [item]
    to_modify.extend(
        map(lambda history_entry: history_entry['item'], item.get('history') or []))

    # apply where modifiers exist
    for mod in modifiers or []:
        for to_mod in to_modify:
            mod(stage, to_mod)

    # now parse the item to ensure it's valid as the specified type
    if parse:
        item_model.parse_obj(item)

    # now update the bundled item with the updated item
    old_item['item_payload'] = item

    return old_item
