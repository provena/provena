import json
from jsonschema import validate  # type: ignore
from typing import Tuple
from constants import RO_CRATE_URI
from SharedInterfaces.RegistryModels import *
from datetime import datetime
from config import Config
from SharedInterfaces.DataStoreAPI import Schema


def validate_against_schema(json_object: Dict[Any, Any], config: Config) -> Tuple[bool, Optional[Exception]]:
    """
    Function Description
    --------------------

    Will attempt to validate a json object against the dataset schema.


    Arguments
    ----------
    json_object : Dict[Any, Any]
        The json data to validate. Validates against the schema path schema

    Returns
    -------
    Tuple[bool, Exception]
        Tuple where bool = False if invalid, Exception contains exception raised by
        the validation if failed (false) otherwise none.



    See Also (optional)
    --------

    Examples (optional)
    --------

    """
    try:
        validate(instance=json_object, schema=get_schema(config).json_schema)
    except Exception as e:
        return (False, e)
    return (True, None)


def get_schema(config: Config) -> Schema:
    """
    Function Description
    --------------------

    Retrieves json schema at the specified path


    Arguments
    ----------
    path : str
        The file path relative to the api directory = schema_path

    Returns
    -------
    Schema
        The json schema document



    See Also (optional)
    --------

    Examples (optional)
    --------

    """
    path: str = config.SCHEMA_PATH
    with open(path, 'r') as f:
        return Schema(json_schema=json.loads(f.read()))

def validate_optionally_required_check(
    check: OptionallyRequiredCheck,
    need_obtained_err_message: str,
    unnecessary_obtained_err_message: str,
) -> None:
    """
    Performs validation of optionally required checks in forms.

    Args:
        check (OptionallyRequiredCheck): The obj to validate
        need_obtained_err_message (str): The message if missing consent
        unnecessary_obtained_err_message (str): The message if unnecessary consent
    """
    if check.relevant and not check.obtained:
        raise Exception(need_obtained_err_message)
    if not check.relevant and check.obtained:
        raise Exception(unnecessary_obtained_err_message)


def validate_fields(data: CollectionFormat) -> None:
    """Validation for the values inside the dataset registration.
    Currently just validating the create and publish times, ethics approval,
    and Indigenous knowledge consent.

    Parameters
    ----------
    data : CollectionFormat
        The item to validate the fields of.

    Raises
    ------
    Exception
        - If the create date is not before (or same as) the publish date.
        - If ethics approval is not present.
        - If the data contains Indigenous knowledge but consent from Indigenous community isnt obtained.
        - If the data contains export control consent unnecessarily
    """

    # Ensure date is reasonable
    if data.dataset_info.published_date < data.dataset_info.created_date:
        raise Exception(
            "The published date cannot be before the creation date.")

    # Check for ethics and privacy (registration)
    validate_optionally_required_check(
        check=data.approvals.ethics_registration,
        need_obtained_err_message="You cannot register a dataset which contains data subject to ethics and privacy concerns without appropriate permissions and consent for it's registration.",
        unnecessary_obtained_err_message="The dataset was marked as having permissions and consent for ethics and privacy concerns but was not marked as containing ethics and privacy sensitive data. Please update the dataset to clarify."
    )

    # Check for ethics and privacy (access)
    validate_optionally_required_check(
        check=data.approvals.ethics_access,
        need_obtained_err_message="You cannot register a dataset which contains data subject to ethics and privacy concerns without appropriate permissions and consent for it's access in the system.",
        unnecessary_obtained_err_message="The dataset was marked as having permissions and consent for ethics and privacy concerns but was not marked as containing ethics and privacy sensitive data. Please update the dataset to clarify."
    )

    # Check for Indigenous knowledge
    validate_optionally_required_check(
        check=data.approvals.indigenous_knowledge,
        need_obtained_err_message="Please obtain mandatory consent from the relevant Indigenous community for the Indigenous knowledge before registering this dataset.",
        unnecessary_obtained_err_message="The dataset does not contain Indigenous knowledge, but consent has been obtained. Please update the dataset to indicate if it contains Indigenous knowledge."
    )

    # and same process for export controls
    validate_optionally_required_check(
        check=data.approvals.export_controls,
        need_obtained_err_message="You have marked this dataset as being subject to export controls but have not performed the necessary due diligence checks and acquired approvals. The dataset cannot be registered.",
        unnecessary_obtained_err_message="The dataset was marked as not containing sensitive data but has obtained consents. Please update the dataset to indicate whether it is subject to export controls."
    )
