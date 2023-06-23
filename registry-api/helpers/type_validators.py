from typing import Callable, Dict, List
from SharedInterfaces.RegistryModels import ItemSubType, WorkflowTemplateDomainInfo, ItemModel, ItemCategory, ItemDatasetTemplate, DatasetDomainInfo, MODEL_TYPE_MAP, PersonDomainInfo
from config import Config
from pydantic import BaseModel
from helpers.id_fetch_helpers import validate_id_helper
from helpers.custom_exceptions import ItemTypeError, SeedItemError
from dataclasses import dataclass

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

    # validate all targets
    for target in targets:
        validate_target(target=target, config=config)


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
