from fastapi import APIRouter, Depends, HTTPException
from SharedInterfaces.DataStoreAPI import *
from SharedInterfaces.RegistryModels import *
from dependencies.dependencies import read_user_protected_role_dependency, read_write_user_protected_role_dependency, user_is_admin
from KeycloakFastAPI.Dependencies import ProtectedRole
from helpers.sts_helpers import call_sts_oidc_service, create_console_session
from config import Config, get_settings
from helpers.registry_api_helpers import *

router = APIRouter()


# read, write or admin will grant data read
DATA_READ_ROLES = [
    DATASET_READ_ROLE,
    DATASET_WRITE_ROLE,
    ADMIN_ROLE
]

# write or admin will grant data read
DATA_WRITE_ROLES = [
    DATASET_WRITE_ROLE,
    ADMIN_ROLE
]


def allows_credential_generation(dataset: ItemDataset) -> bool:
    """
    allows_credential_generation 
    
    Ensures that the dataset is reposited before enabling credential generation.

    Parameters
    ----------
    dataset : ItemDataset
        The complete item dataset

    Returns
    -------
    bool
        True iff the dataset should enable credential generation
    """
    return dataset.collection_format.dataset_info.access_info.reposited


@router.post("/generate-read-access-credentials", response_model=CredentialResponse, operation_id="generate_read_access_credentials")
async def generate_read_access_credentials(
    credentials_request: CredentialsRequest,
    protected_roles: ProtectedRole = Depends(
        read_user_protected_role_dependency),
        config: Config = Depends(get_settings)
) -> CredentialResponse:
    """    generate_access_credentials
        Given an S3 location, will attempt to generate programmatic access keys
        for the storage bucket at this particular subdirectory. 

        Note that the permission boundary is restricted by the intersection of 
        the preformed role and the created policy based on the location - which is
        bounded to the storage bucket.

        This produces read level access into the subset of the bucket 
        requested in the S3 location object.

        Arguments
        ----------
        credentials_request: CredentialsRequest 
            Contains the location + console session URL required flag

        Returns
        -------
         : CredentialResponse
            The AWS credentials

        Raises
        ------
        HTTPException
            500 error code if something goes wrong with STS call or otherwise.

        See Also (optional)
        --------

        Examples (optional)
        --------
    """
    # pul the id from the req
    id = credentials_request.dataset_id

    # fetch the dataset metadata based on id - also fetches roles
    # if KeyError  -> 400, if internal error -> 500, auth -> 401
    try:
        registry_item = user_fetch_dataset_from_registry(
            id=id,
            config=config,
            user=protected_roles.user
        )
    except HTTPException as he:
        raise he
    except Exception as e:  # all other errors.
        raise Exception(
            f"Something unexpected went wrong during data retrieval. Error: {e}")

    # check access based on groups and dataset access configuration
    registry_item_roles = registry_item.roles

    # check authorisation
    authorised = False

    # a datastore admin can do everything
    if user_is_admin(protected_roles.user):
        authorised = True

    if registry_item_roles is not None:
        for role in DATA_READ_ROLES:
            if role in registry_item_roles:
                authorised = True
                break

    if not authorised:
        raise HTTPException(
            status_code=401,
            detail=f"You do not have sufficient permissions to read from this dataset!"
        )

    item = registry_item.item

    try:
        assert isinstance(item, ItemDataset)
    except Exception:
        raise HTTPException(status_code=400,
                            detail=f'The item with id {id} is a SeededItem and cannot have credentials generated.')

    # we know the item is a ItemDataset - perform checks to ensure it is reposited
    allowed = allows_credential_generation(dataset=item)

    if not allowed:
        raise HTTPException(
            status_code=400, detail=f"You cannot generate credentials for a non reposited data store item. ID: {id}.")

    # extract s3 location from item
    s3_location = item.s3

    # determine a suitable session name
    session_name = f"{protected_roles.user.username},read-prog-bucket-access"

    # Get creds
    try:
        credentials: Credentials = call_sts_oidc_service(
            session_name=session_name,
            s3_location=s3_location,
            write=False,
            config=config
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Something went wrong when running the AWS STS service command: {e}."
        )

    # keycloak issuer is always present
    assert config.KEYCLOAK_ISSUER

    console_url: Optional[str] = None
    if credentials_request.console_session_required:
        # determine suitable target URL
        target_url = f"https://s3.console.aws.amazon.com/s3/buckets/{config.S3_STORAGE_BUCKET_NAME}?prefix={s3_location.path}&region=ap-southeast-2"
        try:
            console_url = create_console_session(
                aws_credentials=credentials,
                session_duration=config.CONSOLE_SESSION_DURATION_SECONDS,
                aws_issuer=config.KEYCLOAK_ISSUER,
                destination_url=target_url
            )
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Something went wrong when trading credentials for console session: {e}."
            )

    # Return success
    return CredentialResponse(
        status=Status(
            success=True,
            details="STS credentials generated successfully for specified path."),
        credentials=credentials,
        console_session_url=console_url
    )


@router.post("/generate-write-access-credentials", response_model=CredentialResponse, operation_id="generate_write_access_credentials")
async def generate_write_access_credentials(
    credentials_request: CredentialsRequest,
    protected_roles: ProtectedRole = Depends(
        read_write_user_protected_role_dependency),
    config: Config = Depends(get_settings)
) -> CredentialResponse:
    """    generate_access_credentials
        Given an S3 location, will attempt to generate programmatic access keys
        for the storage bucket at this particular subdirectory. 

        Note that the permission boundary is restricted by the intersection of 
        the preformed role and the created policy based on the location - which is
        bounded to the storage bucket.

        This produces write level access into the subset of the bucket 
        requested in the S3 location object.

        Arguments
        ----------
        credentials_request: CredentialsRequest 
            Contains the location + console session URL required flag

        Returns
        -------
         : CredentialResponse
            The AWS credentials

        Raises
        ------
        HTTPException
            500 error code if something goes wrong with STS call or otherwise.

        See Also (optional)
        --------

        Examples (optional)
        --------
    """
    # pul the id from the req
    id = credentials_request.dataset_id

    # fetch the dataset metadata based on id - also fetches roles
    # if KeyError  -> 400, if internal error -> 500, auth -> 401
    try:
        registry_item = user_fetch_dataset_from_registry(
            id=id,
            config=config,
            user=protected_roles.user
        )
    except HTTPException as he:
        raise he
    except Exception as e:  # all other errors.
        raise Exception(
            f"Something unexpected went wrong during data retrieval. Error: {e}")

    # check the dataset is not locked
    if registry_item.locked:
        raise HTTPException(
            status_code=401,
            detail=f"This dataset is locked - you cannot modify the files of a locked dataset. Unlock the dataset first."
        )

    # check access based on groups and dataset access configuration
    registry_item_roles = registry_item.roles

    # check authorisation
    authorised = False

    # a datastore admin can do everything
    if user_is_admin(protected_roles.user):
        authorised = True

    if registry_item_roles is not None:
        for role in DATA_WRITE_ROLES:
            if role in registry_item_roles:
                authorised = True
                break

    if not authorised:
        raise HTTPException(
            status_code=401,
            detail=f"You do not have sufficient permissions to write to this dataset!"
        )

    item = registry_item.item
    try:
        assert isinstance(item, ItemDataset)
    except Exception:
        raise HTTPException(status_code=400,
                            detail=f'The item with id {id} is a SeededItem and cannot have credentials generated.')

    # we know the item is a ItemDataset - perform checks to ensure it is reposited
    allowed = allows_credential_generation(dataset=item)

    if not allowed:
        raise HTTPException(
            status_code=400, detail=f"You cannot generate credentials for a non reposited data store item. ID: {id}.")

    # extract s3 location from item
    s3_location = item.s3

    # determine a suitable session name
    session_name = f"{protected_roles.user.username},write-prog-bucket-access"

    # Get creds
    try:
        credentials: Credentials = call_sts_oidc_service(
            session_name=session_name,
            s3_location=s3_location,
            write=True,
            config=config
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Something went wrong when running the AWS STS service command: {e}.")

    # keycloak issuer is always present
    assert config.KEYCLOAK_ISSUER

    console_url: Optional[str] = None
    if credentials_request.console_session_required:
        # determine suitable target URL
        target_url = f"https://s3.console.aws.amazon.com/s3/buckets/{config.S3_STORAGE_BUCKET_NAME}?prefix={s3_location.path}&region=ap-southeast-2"
        try:
            console_url = create_console_session(
                aws_credentials=credentials,
                session_duration=config.CONSOLE_SESSION_DURATION_SECONDS,
                aws_issuer=config.KEYCLOAK_ISSUER,
                destination_url=target_url
            )
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Something went wrong when trading credentials for console session: {e}."
            )

    # Return success
    return CredentialResponse(
        status=Status(
            success=True,
            details="STS credentials generated successfully for specified path."),
        credentials=credentials,
        console_session_url=console_url
    )
