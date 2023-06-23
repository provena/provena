from fastapi import APIRouter, Depends, HTTPException
from KeycloakFastAPI.Dependencies import ProtectedRole
from SharedInterfaces.RegistryModels import *
from SharedInterfaces.DataStoreAPI import Schema
from SharedInterfaces.SharedTypes import Status
from dependencies.dependencies import read_user_protected_role_dependency
from helpers.metadata_helpers import validate_against_schema, get_schema, validate_fields
from helpers.registry_api_helpers import validate_dataset_in_registry
import json
from config import Config, get_settings

router = APIRouter()


@router.post("/validate-metadata", response_model=Status, operation_id="validate_metadata")
async def validate_metadata(
    metadata: CollectionFormat,
    protected_roles: ProtectedRole = Depends(
        read_user_protected_role_dependency),
    config: Config = Depends(get_settings)
) -> Status:
    """    validate_metadata
        Allows for validation checks without any interaction with external resources.
        Used for testing and potentially as an ongoing validation checker on the front end.

        Arguments
        ----------
        metadata : CollectionFormat
            The metadata to validate - this validation occurs both in terms of 
            parsing the collection format object at the API level and also by 
            validating the schema against the json schema file.

        Returns
        -------
         : Status
            The status object - true/false

        Raises
        ------
        HTTPException 422
            If the parsing fails at API level then 422 is returned with the 
            shared interface validation exception type.

        See Also (optional)
        --------

        Examples (optional)
        --------
    """
    # Validate metadata
    collection_model = metadata
    valid, failure_exception = validate_against_schema(
        json.loads(collection_model.json(exclude_none=True)),
        config=config
    )

    # If the validation against schema fails, return invalid Status
    if not valid:
        return Status(
            success=False,
            details=f'Exception when validating against schema: {failure_exception}'
        )

    try:
        validate_fields(metadata)
    except Exception as e:
        return Status(
            success=False,
            details=f"Failed field value validation. Error: {e}"
        )

    # Call the validate endpoint which also checks the IDs
    if config.REMOTE_PRE_VALIDATION:
        possible_error = validate_dataset_in_registry(
            collection_format=metadata,
            user=protected_roles.user,
            config=config
        )

        if possible_error is not None:
            return Status(
                success=False,
                details=f"Registry API responded with an error during validation, error: {possible_error}."
            )

    # Everything seems okay
    return Status(
        success=True,
        details="Validation successful."
    )


@router.get("/dataset-schema", response_model=Schema, operation_id="get_dataset_schema")
async def get_dataset_schema(
    protected_roles: ProtectedRole = Depends(
        read_user_protected_role_dependency),
    config: Config = Depends(get_settings)
) -> Schema:
    """
    Function Description
    --------------------

    Returns the json schema Schema object which defines the required dataset metadata. 
    Metadata which is uploaded via the mint-dataset endpoint will be validated against this 
    schema before being accepted.


    Arguments
    ----------
    protected_roles : ProtectedRole, optional
        by default Depends( kc_auth.get_any_protected_role_dependency([usage_role]))

    Returns
    -------
    Schema
        The json schema object


    Raises
    ------
    HTTPException
        Raises a 500 internal error if something goes wrong.

    See Also (optional)
    --------

    Examples (optional)
    --------

    """
    # Read the schema from file
    try:
        return get_schema(config=config)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve the json schema with error: {e}.")
