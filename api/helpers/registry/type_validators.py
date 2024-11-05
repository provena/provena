from typing import Callable, Dict, List
from ProvenaInterfaces.RegistryModels import *
from config import Config
from pydantic import BaseModel
from helpers.registry.id_fetch_helpers import validate_id_helper
from helpers.registry.custom_exceptions import ItemTypeError, SeedItemError
from dataclasses import dataclass
import pyproj
import re
import shapely  # type: ignore

ValidatorFunc = Callable[[BaseModel, Config], None]


@dataclass
class ValidationTarget():
    # describes a combindation of id/category/subtype to validate the item. must
    # be complete (non seed item) if there is an error, the name is used to
    # customise it
    id: str
    name: str
    category: ItemCategory
    subtype: ItemSubType


def validate_target(target: ValidationTarget, config: Config) -> None:
    """
    validate_target 

    Performs a validation against a specified target. 

    A target is defined above as a combinatino of id/category/subtype

    Validates that the ID exists in the registry, that it is the correct type
    and that it is not a seeded item.

    Parameters
    ----------
    target : ValidationTarget
        The target configuration to validate
    config : Config
        The config

    Raises
    ------
    Exception
        If validation fails, customised exception message
    """
    # get the target model type
    model = MODEL_TYPE_MAP.get((target.category, target.subtype))
    if model is None:
        raise ValueError(
            "Unexpected category/subtype combination during validation!")

    # run the validation helper
    try:
        validate_id_helper(
            id=target.id,
            seed_allowed=False,
            item_model_type=model,
            category=target.category,
            subtype=target.subtype,
            config=config,
        )
    # catch and parse errors appropriately
    except KeyError as e:
        raise Exception(
            f"Could not find {target.name} with ID {target.id} in registry. Please ensure it exists.")
    except SeedItemError as e:
        raise Exception(
            f"Seed items ({target.id}) are not allowed to be used in this type. Use complete items only")
    except ItemTypeError as e:
        raise Exception(
            f"Mismatch between expected item types. Please ensure {target.id} refers to a {target.subtype}.")
    except TypeError as e:
        raise Exception(
            f"Existing item {target.id} could not be parsed as correct item type. Error: {e}")
    except Exception as e:
        raise Exception(
            f"Unexpected error when validating {target.name} with ID {target.id}. Error: {e}")


def validate_workflow_def(item: BaseModel, config: Config) -> None:
    """Custom Validation for the creation of a workflow definition.
    Ensure that references to other entities (software and dataset templates) exist, are
    full items, and are the correct/expected type. E.g. An ID in the associated software field
    in the item_domain_info points to only a completed software entity.

    Parameters
    ----------
    item : BaseModel
        The domain info of the item being created - not yet parsed in this context
    config : Config
        The API config object

    """
    # parse the workflow template
    item_domain_info = WorkflowTemplateDomainInfo.parse_obj(item.dict())

    # create list of targets - includes software id and input/output ds template IDs
    targets: List[ValidationTarget] = [
        # software
        ValidationTarget(
            id=item_domain_info.software_id,
            name="Software ID",
            category=ItemCategory.ENTITY,
            subtype=ItemSubType.MODEL
        ),
    ]
    dataset_template_ids = [item.template_id for item in item_domain_info.input_templates] + [
        item.template_id for item in item_domain_info.output_templates]
    targets.extend([
        ValidationTarget(
            id=id,
            name="Dataset Template",
            category=ItemCategory.ENTITY,
            subtype=ItemSubType.DATASET_TEMPLATE
        )
        for id in dataset_template_ids
    ])

    # validate all targets
    for target in targets:
        validate_target(target=target, config=config)


def parse_ewkt_from_string(ewkt_string: str) -> Tuple[str, str]:
    """Parse an EWKT string into its SRID and geometry components.

    Parameters
    ----------
    ewkt_string : str
        The EWKT string to parse

    Returns
    -------
    Tuple[str, str]
        The SRID and geometry components of the EWKT string

    Raises
    ------
    ValueError
        If the EWKT string is not in the expected format
    """
    # integer SRID ; geometry string regex.
    ewkt_pattern = r'SRID=(?P<srid>\d+);(?P<geometry>.+)'
    match = re.match(ewkt_pattern, ewkt_string)

    if match is None:
        raise ValueError(
            f"Invalid EWKT format recieved. Please use the E-WKT standard of: 'SRID=<SRID>;<WKT Formatted Geometry>'. Where the SRID is an integer number.")

    # should have an srid field of digits, and geometry string now inside
    return match.group('srid'), match.group('geometry')


def validate_dataset_spatial_info(spatial_info: CollectionFormatSpatialInfo) -> None:
    """Validate the spatial info of a dataset. Throws an exception if invalid. 
        Fields to validate are the coverage and extent fields. Resolution is validated by
        the pydantic models, not in the API.

    Parameters
    ----------
    spatial_info : CollectionFormatSpatialInfo
        The spatial information to validate
    """
    e_wkts_to_validate = []
    if spatial_info.coverage is not None:
        e_wkts_to_validate.append(spatial_info.coverage)
    if spatial_info.extent is not None:
        e_wkts_to_validate.append(spatial_info.extent)

    [validate_EWKT_string(e_wkt) for e_wkt in e_wkts_to_validate]


def validate_EWKT_string(v: str) -> str:
    """Validate an EWKT string. Throws an exception if invalid.
    The correct format is 'SRID=XXXX;<WKT Formatted Geometry>'. Note that the SRID is exactly 4 digits
    as well as the use of a semi-colon.

    Parameters
    ----------
    v : str
        The EWKT string to validate

    Returns
    -------
    str
        The EWKT string if valid.

    Raises
    ------
    ValueError
        _description_
    ValueError
        _description_
    Exception
        _description_
    """
    try:
        srid, geom_str = parse_ewkt_from_string(v)
    except Exception as e:
        raise (e)

    # validate the SRID
    try:
        pyproj.Proj(f'epsg:{srid}')
    except Exception as e:
        raise Exception(f"Invalid SRID integer provided. Details: {e}")

    # validate the geometry string.
    try:
        shapely.from_wkt(geom_str)
    except shapely.errors.ShapelyError as e:
        raise ValueError(
            f"Invalid EWKT format. Failed to parse the geometry inside of the EWKT string. Details: {e}")
    except Exception as e:
        raise Exception(
            f"Invalid EWKT format. Failed to parse the geometry inside of the EWKT string. Details: {e}")

    return v


def validate_dataset(item: BaseModel, config: Config) -> None:
    """Custom Validation for the creation of a dataset.
    Ensure that references to other entities exist, are full items, and are the
    correct/expected type. 

    Parameters
    ----------
    item : BaseModel
        The domain info of the item being created - not yet parsed in this context
    config : Config
        The API config object

    """
    item_domain_info = DatasetDomainInfo.parse_obj(item.dict())

    # create list of targets
    targets: List[ValidationTarget] = [
        ValidationTarget(
            id=item_domain_info.collection_format.associations.organisation_id,
            name="Author Organisation ID",
            category=ItemCategory.AGENT,
            subtype=ItemSubType.ORGANISATION
        ),
        ValidationTarget(
            id=item_domain_info.collection_format.dataset_info.publisher_id,
            name="Dataset Publisher Organisation ID",
            category=ItemCategory.AGENT,
            subtype=ItemSubType.ORGANISATION
        ),
    ]

    if item_domain_info.collection_format.associations.data_custodian_id is not None:
        targets.append(ValidationTarget(
            id=item_domain_info.collection_format.associations.data_custodian_id,
            name="Data Custodian ID",
            category=ItemCategory.AGENT,
            subtype=ItemSubType.PERSON
        ))

    # validate all targets
    for target in targets:
        validate_target(target=target, config=config)

    spatial_info = item_domain_info.collection_format.dataset_info.spatial_info
    if spatial_info is not None:
        validate_dataset_spatial_info(spatial_info)


def validate_person(item: BaseModel, config: Config) -> None:
    person_domain_info = PersonDomainInfo.parse_obj(item.dict())
    # only validation for person is to ensure consent is obtained for registration
    if not person_domain_info.ethics_approved:
        raise Exception(
            "Please ensure mandatory ethics consent is obtained before proceeding with registration or updating of person.")


custom_type_validators: Dict[ItemSubType, ValidatorFunc] = {
    ItemSubType.MODEL_RUN_WORKFLOW_TEMPLATE: validate_workflow_def,
    ItemSubType.DATASET: validate_dataset,
    ItemSubType.PERSON: validate_person
}
