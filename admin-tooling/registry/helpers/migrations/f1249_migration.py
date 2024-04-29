from typing import Dict, Any, Callable, List
from ProvenaInterfaces.RegistryModels import OptionallyRequiredCheck, ItemSubType, RecordInfo, MODEL_TYPE_MAP
from ProvenaInterfaces.RegistryAPI import BundledItem
from helpers.util import py_to_dict


def add_person_ethics_consent(item: Dict[str, Any]) -> Dict[str, Any]:
    # add new fields
    ethics_dict_key = "ethics_approved"

    # do not override existing items that have the value
    if ethics_dict_key not in item:
        # add the new field
        item[ethics_dict_key] = False

    return item


def add_dataset_approvals_obj(item: Dict[str, Any]) -> Dict[str, Any]:
    # pull out dataset info
    collection_format = item['collection_format']

    # add new fields
    dict_key = "approvals"

    # do not override existing items that have the value
    if dict_key not in collection_format:
        collection_format[dict_key] = {}

    return item


def add_dataset_indigenous_knowledge(item: Dict[str, Any]) -> Dict[str, Any]:
    # pull out dataset info
    approvals = item['collection_format']['approvals']

    # add new fields
    dict_key = "indigenous_knowledge"

    # do not override existing items that have the value
    if dict_key not in approvals:
        # add the new field - assumes not relevant
        approvals[dict_key] = py_to_dict(OptionallyRequiredCheck(
            relevant=False, obtained=False))

    return item


def add_dataset_export_controls(item: Dict[str, Any]) -> Dict[str, Any]:
    # pull out dataset info
    approvals = item['collection_format']['approvals']

    # add new fields
    dict_key = "export_controls"

    # do not override existing items that have the value
    if dict_key not in approvals:
        # add the new field - assumes not relevant
        approvals[dict_key] = py_to_dict(OptionallyRequiredCheck(
            relevant=False, obtained=False))

    return item


def add_dataset_ethics_registration(item: Dict[str, Any]) -> Dict[str, Any]:
    # pull out dataset info
    approvals = item['collection_format']['approvals']

    # add new fields
    dict_key = "ethics_registration"

    # do not override existing items that have the value
    if dict_key not in approvals:
        # add the new field - assumes not relevant
        approvals[dict_key] = py_to_dict(OptionallyRequiredCheck(
            relevant=False, obtained=False))

    return item


def add_dataset_ethics_access(item: Dict[str, Any]) -> Dict[str, Any]:
    # pull out dataset info
    approvals = item['collection_format']['approvals']

    # add new fields
    dict_key = "ethics_access"

    # do not override existing items that have the value
    if dict_key not in approvals:
        # add the new field - assumes not relevant
        approvals[dict_key] = py_to_dict(OptionallyRequiredCheck(
            relevant=False, obtained=False))

    return item


modifier_map: Dict[ItemSubType, List[Callable[[Dict[str, Any]], Dict[str, Any]]]] = {
    ItemSubType.DATASET: [
        # ordered migrations

        # add the dataset approvals object
        add_dataset_approvals_obj,
        # add ethics within it (registration)
        add_dataset_ethics_registration,
        # add ethics within it (access)
        add_dataset_ethics_access,
        # add export controls within it
        add_dataset_export_controls,
        # add indigenous knowledge within it
        add_dataset_indigenous_knowledge
    ],
    ItemSubType.PERSON: [
        add_person_ethics_consent
    ]
}


def f1249_migrator_function(old_item: Dict[str, Any], parse: bool = True) -> Dict[str, Any]:
    # Parse the item as a bundle
    reg_item = BundledItem.parse_obj(old_item)

    # pull out the item payload
    item = reg_item.item_payload

    # check the type of the item and apply suitable modifiers if applicable
    record_base = RecordInfo.parse_obj(item)
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
            mod(to_mod)

    # now parse the item to ensure it's valid as the specified type
    if parse:
        item_model.parse_obj(item)

    # now update the bundled item with the updated item
    old_item['item_payload'] = item

    return old_item
