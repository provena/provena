import json
from typing import List, Any
import boto3  # type: ignore
import botocore.session  # type: ignore
from aws_secretsmanager_caching import SecretCache, SecretCacheConfig  # type: ignore
from .sanitize import *
from config import Config
from SharedInterfaces.RegistryModels import *
from SharedInterfaces.DataStoreAPI import ROCrate

"""    
    Defines helper functions which relate to aws functions such as secret manager,
    s3, sts etc
"""


def setup_secret_cache() -> SecretCache:
    """    setup_secret_cache
        Sets up the aws secret manager LRU cache

        Returns
        -------
         : SecretCache

        See Also (optional)
        --------

        Examples (optional)
        --------
    """
    client = botocore.session.get_session().create_client('secretsmanager')
    cache_config = SecretCacheConfig()
    return SecretCache(config=cache_config, client=client)


def retrieve_secret_value(secret_arn: str, secret_cache: SecretCache) -> str:
    """    retrieve_secret_value
        Given the secret arn and secret cache will provide the 
        secret value for the given secret ARN. Should then be parsed
        as a json if it is json form.

        Arguments
        ----------
        secret_arn : str
            The secret ARN
        secret_cache : SecretCache
            The secret cache from aws secret cache library

        Returns
        -------
         : str
            The secret value

        See Also (optional)
        --------

        Examples (optional)
        --------
    """
    return secret_cache.get_secret_string(secret_arn)


def is_s3_path_in_bucket(path: str, config: Config) -> bool:
    """
    Function Description
    --------------------

    Checks if a file bath from the base of the bucket already exists
    in some form on S3 - this could be one of either
    - file
    - folder with contents
    - empty folder

    If any of the above conditions are true -> returns True
    else returns False


    Arguments
    ----------
    path : str
        The path relative to bucket e.g. datasets/some_dataset_name

    Returns
    -------
    bool
        True if exists, False if not



    See Also (optional)
    --------

    Examples (optional)
    --------

    """
    # Create client
    s3_client = boto3.client('s3')

    # Check that the bucket name is present
    assert config.S3_STORAGE_BUCKET_NAME is not None

    # See if the folder exists
    # Inspired by
    # https://stackoverflow.com/questions/57957585/how-to-check-if
    # -a-particular-directory-exists-in-s3-bucket-using-python-and-boto

    # Clear off the end slash to ensure its referring to folder not subitems
    s3_path = path.rstrip('/')

    # Try and list items and only accept 1 - notice we are looking for folder or direct item with that name
    response = s3_client.list_objects(
        Bucket=config.S3_STORAGE_BUCKET_NAME, Prefix=s3_path, Delimiter='/', MaxKeys=1)

    # If CommonPrefixes present the folder exists, if any contents then at least one item exists
    return 'CommonPrefixes' in response or 'Contents' in response


def find_s3_path(collection_format: CollectionFormat, handle: str, config: Config, use_handle_as_name: bool = True) -> S3Location:
    """    find_s3_path
        Given the metadata collection format, handle and some configuration, will 
        return the complete s3 path that the dataset is stored at.
        This function is used when updating existing metadata to both discover 
        the s3 location and also verify that it is already seeded.

        Arguments
        ----------
        collection_format : CollectionFormat
            The metadata
        handle : str
            The dataset handle id
        use_handle_as_name : bool, optional
            Should the handle be used as the folder name, by default True

        Returns
        -------
         : S3Location
            The ideal S3 location

        Raises
        ------
        Exception
            Path already exists/is not unique 
        Exception
            Dataset name field missing

        See Also (optional)
        --------

        Examples (optional)
        --------
    """
    if use_handle_as_name:
        sanitized_name = sanitize_handle(handle)
        path = config.DATASET_PATH + "/" + sanitized_name + "/"
        on_s3 = is_s3_path_in_bucket(path, config=config)
        if not on_s3:
            raise Exception(
                f'path does exist! Path = {path}')

    if not use_handle_as_name:
        dataset_name = collection_format.dataset_info.name
        if not dataset_name:
            raise Exception(
                "Failed to find 'name' field in metadata - check schema.")

        on_s3 = is_s3_path_in_bucket(path, config)
        sanitized_name = sanitize_name(dataset_name)
        path = config.DATASET_PATH + "/" + sanitized_name + "/"

        if not on_s3:
            raise Exception(
                'path does exist! Path = {path}')

    return S3Location(
        bucket_name=config.S3_STORAGE_BUCKET_NAME,
        path=path,
        s3_uri=f"s3://{config.S3_STORAGE_BUCKET_NAME}/{path}"
    )


def construct_s3_path(collection_format: CollectionFormat, handle: str, config: Config, use_handle_as_name: bool = True) -> S3Location:
    """
    Function Description
    --------------------

    Given the metadata and handle, produce an S3 URI where the data can be
    uploaded.

    Requirements:
    -> unique location
    -> no pre-existing content on S3
    -> follows data structure of S3 bucket

    Expects storage bucket name environment variable.

    Arguments
    ----------
    valid_metadata : Metadata
        Metadata object given by user
    handle : str
        The newly generated handle

    Returns
    -------
    S3Location which includes the bucket name, path and URI

    See Also (optional)
    --------

    Examples (optional)
    --------
    """
    if use_handle_as_name:
        sanitized_name = sanitize_handle(handle)
        path = config.DATASET_PATH + "/" + sanitized_name + "/"
        on_s3 = is_s3_path_in_bucket(path, config)
        if on_s3:
            raise Exception(
                'Handle was not unique as a path name - aborting!')

    if not use_handle_as_name:
        dataset_name = collection_format.dataset_info.name
        on_s3 = is_s3_path_in_bucket(path, config)
        sanitized_name = sanitize_name(dataset_name)
        path = config.DATASET_PATH + "/" + sanitized_name + "/"

        if on_s3:
            # Trying desperately to make this path unique since
            # the user has requested a dataset with the same name
            # Behaviour?
            # TODO refine this behaviour
            path = path + "_" + handle + "/"
            on_s3 = is_s3_path_in_bucket(path, config)
            if on_s3:
                raise Exception(
                    'Failed to find unique name - must be a duplicate dataset.')

    return S3Location(
        bucket_name=config.S3_STORAGE_BUCKET_NAME,
        path=path,
        s3_uri=f"s3://{config.S3_STORAGE_BUCKET_NAME}/{path}"
    )


def seed_s3_location_with_metadata(s3_location: S3Location, metadata: ROCrate, config: Config) -> None:
    """
    Function Description
    --------------------

    Given the s3 location and the metadata, will upload the metadata
    file with the METADATA_FILE_NAME config variable name into the location
    specified, which seeds the file structure.


    Arguments
    ----------
    s3_location : S3Location
        The s3 location object describing where to seed.
    metadata : Metadata
        The metadata (modified)


    See Also (optional)
    --------

    Examples (optional)
    --------

    """
    # Create the bytes of object
    json_body = json.dumps(metadata, indent=2).encode('UTF-8')

    # Get s3 client
    client = boto3.client('s3')

    # Construct full path into s3
    path = s3_location.path.rstrip('/') + '/' + config.METADATA_FILE_NAME

    # upload file
    client.put_object(
        Body=json_body,
        Bucket=config.S3_STORAGE_BUCKET_NAME,
        Key=path
    )


def update_metadata_at_s3(s3_location: S3Location, metadata: Dict[str, Any], config: Config) -> None:
    """
    Function Description
    --------------------

    Given the s3 location and the metadata, will update the metadata
    file in this location

    Note, this is currently a duplicate of seeding metadata at a location 
    but is kept in a separate function in case we want to add extra checks/
    hooks for updating vs writing.


    Arguments
    ----------
    s3_location : S3Location
        The s3 location object describing where to update metadata.
    metadata : Metadata
        The metadata (modified)


    See Also (optional)
    --------

    Examples (optional)
    --------

    """
    # Create the bytes of object
    json_body = json.dumps(metadata, indent=2).encode('UTF-8')

    # Get s3 client
    client = boto3.client('s3')

    # Construct full path into s3
    path = s3_location.path.rstrip('/') + '/' + config.METADATA_FILE_NAME

    # upload file
    client.put_object(
        Body=json_body,
        Bucket=config.S3_STORAGE_BUCKET_NAME,
        Key=path
    )


def create_policy_document(write_resource_uris: List[str], read_resource_uris: List[str], list_resource_uris: List[str]) -> str:
    """    create_policy_document
        Given the required write access URIs and read access URIS
        will produce an inline policy document which give access to this.

        Please note that the reason for including more permissive usage of
        the read permissions is due to s3 sync requiring read permissions seemingly
        against the whole bucket.

        Arguments
        ----------
        write_resource_uris : List[str]
            List of ARN/resource identifiers for bucket locations (read write del)
        read_resource_uris : List[str]
            List of ARN/resource identifiers for bucket locations (read only (get objects))
        list_resource_uris : List[str]
            List of ARN/resource identifiers for bucket locations (read only (list for sync))

        Returns
        -------
         : str
            json dumped policy document

        See Also (optional)
        --------

        Examples (optional)
        --------
    """
    statements = []

    if len(write_resource_uris) > 0:
        statements.append(
            {
                "Action": [
                    "s3:GetObject*",
                    "s3:DeleteObject*",
                    "s3:PutObject",
                    "s3:PutObjectLegalHold",
                    "s3:PutObjectRetention",
                    "s3:PutObjectTagging",
                    "s3:PutObjectVersionTagging",
                    "s3:Abort*"
                ],
                "Resource": write_resource_uris,
                "Effect": "Allow"
            }
        )

    if len(read_resource_uris) > 0:
        statements.append(

            {
                "Action": [
                    "s3:GetObject*"
                ],
                "Resource": read_resource_uris,
                "Effect": "Allow"
            }

        )

    if len(list_resource_uris) > 0:
        statements.append(
            {
                "Action": [
                    "s3:ListMultipartUploads",
                    "s3:ListBucketMultipartUploads",
                    "s3:ListBucketVersions",
                    "s3:ListBucket"

                ],
                "Resource": list_resource_uris,
                "Effect": "Allow"
            }
        )

    policy_document = {
        "Version": "2012-10-17",
        "Statement": statements

    }
    return json.dumps(policy_document)
