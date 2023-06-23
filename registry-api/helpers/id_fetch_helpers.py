from typing import Type, Dict, TypeVar, Any, Tuple, Union
from SharedInterfaces.RegistryModels import ItemCategory, ItemSubType, ItemBase, RecordType, SeededItem, RecordInfo
from fastapi import HTTPException
from config import Config
from helpers.dynamo_helpers import get_entry_raw
from helpers.custom_exceptions import SeedItemError, ItemTypeError

item_base_type = TypeVar('item_base_type', bound=ItemBase)


def validate_item_type(
    item: Union[SeededItem, ItemBase],
    category: ItemCategory,
    subtype: ItemSubType
) -> None:
    if (item.item_category != category) or \
            (item.item_subtype != subtype):
        raise HTTPException(
            status_code=400,
            detail=f"Item with id {item.id} did not have the correct category or subtype for the specified item type."
        )


def parse_unknown_record_type(
    raw_item: Dict[str, Any],
    item_model_type: Type[item_base_type]
) -> Tuple[RecordType, Union[SeededItem, ItemBase]]:
    """
    Given a raw item, will attempt to validate it as either a seeded item or
    complete item of the specified item_model_type. If the object record info
    type is not parsable, or the expected type cannot be parsed, then a
    ValueError is raised.
    Parameters
    ----------
    raw_item : Dict[str, Any]
        The record to parse and validate
    item_model_type : Type[item_base_type]
        The type for the full model - used to parse (pydantic)
    Returns
    -------
    Tuple[RecordType, Union[SeededItem, ItemBase]]
        (The record type, the corresponding parsed item)
    Raises
    ------
    ValueError
        If the record cannot be parsed as a RecordInfo
    ValueError
        If the record is a Seed Item and cannot be parsed as SeededItem
    ValueError
        If the record is a Complete Item and cannot be parsed as item_model_type model
    """
    # Item retrieved, now try to parse
    # Either a complete item or a seed item
    parsed_obj: Union[ItemBase, SeededItem]

    # Check if it has a record_type field by parsing as the base
    # RecordInfo class
    try:
        record_info: RecordInfo = RecordInfo.parse_obj(raw_item)
    except Exception as e:
        raise ValueError(
            f"The record could not be parsed in the current RecordInfo data model. Error: {e}.")

    # Pull out the record type
    record_type = record_info.record_type

    # Seed record
    if (record_type == RecordType.SEED_ITEM):
        # Should be a Seed Item and therefore
        # the parse should be successful
        try:
            parsed_obj = SeededItem.parse_obj(raw_item)
        except Exception as e:
            raise ValueError(
                f"The record was marked as a SEED_ITEM but could not be parsed as a SeededItem. Error: {e}.")
    # Complete record
    if (record_type == RecordType.COMPLETE_ITEM):
        # Should be an item_model_type and therefore
        # the parse should be successful
        try:
            parsed_obj = item_model_type.parse_obj(raw_item)
        except Exception as e:
            raise ValueError(
                f"The record was marked as a COMPLETE_ITEM but could not be parsed as the correct model. Error: {e}."
            )

    # Return the record type and parsed object
    return (record_type, parsed_obj)


def validate_id_helper(
    id: str,
    seed_allowed: bool,
    item_model_type: Type[item_base_type],
    category: ItemCategory,
    subtype: ItemSubType,
    config: Config
) -> None:
    """Implements validation of a particular ID supposedly in the registry.
    Parameters
    ----------
    id : str
        ID of the item to validate
    seed_allowed : bool
        whether or not to throw an error if the item is a seed.
    item_model_type : Type[item_base_type]
        _description_
    category : ItemCategory
        The expected category
    subtype : ItemSubType
        The expected item subtype
    config : Config
        _description_
    Returns
    -------
    None
    Raises
    ------
    KeyError
        An item with associated ID did not exist
    HTTPException
        OTher unexpected behaviour when accessing registry resources
    TypeError
        If the item could not be parsed using the expected model define in RegistryModels
    SeedItemError
        The item was a seed and seed items are not allowed
    ItemTypeError
        The retrieved item did not match the expected type.
    """
    # Try to read the raw item with given key from registry
    try:
        raw_item: Dict[str, Any] = get_entry_raw(id=id, config=config)
    # The item wasn't present
    except KeyError as e:
        raise KeyError(f"Could not find item for id {id} in the registry.")

    # Error occurred which was caught and handled in fastAPI format
    except HTTPException as e:
        raise e
    # Unknown error occurred
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"An unexpected error occurred while reading from the registry: {e}.")

    # Parse the type and record
    try:
        record_type, parsed_obj = parse_unknown_record_type(
            raw_item=raw_item,
            item_model_type=item_model_type
        )
    except Exception as e:
        raise TypeError(
            "The entity was found, but could not be parsed as the appropriate type")

    # If seed item and seed not allowed, throw an error
    if record_type == RecordType.SEED_ITEM and not seed_allowed:
        raise SeedItemError(
            "Seed items not allowed. Please use complete items only")
    try:
        # Check types
        validate_item_type(
            item=parsed_obj,
            category=category,
            subtype=subtype
        )
    except Exception as e:
        raise ItemTypeError(
            "Parsed Item type does not match expected item type.")
