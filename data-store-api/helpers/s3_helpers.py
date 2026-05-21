
from typing import List
import boto3  # type: ignore
from botocore.exceptions import ClientError  # type: ignore
from fastapi import HTTPException
from helpers.sts_helpers import call_sts_oidc_service
from helpers.s3_client import get_s3_client
from ProvenaInterfaces.DataStoreAPI import Credentials
from .sanitize import *
from config import Config
from ProvenaInterfaces.RegistryModels import *


def check_file_exists(bucket_name: str, file_path: str, config: Config = None) -> bool:
    """Checks if a file exists inside an s3 bucket

    Parameters
    ----------
    bucket_name : str
        The s3 bucket name to check for the file in.
    file_path : str
        The path to the file inside the bucket to check for existance.

    Returns
    -------
    bool
        True if the file exists, False if it does not.

    Raises
    ------
    e
        Unexpected error occurred during s3 head operation.
    Exception
        Unexpected error occurred during s3 head operation.
    """
    from config import get_settings
    cfg = config or get_settings()
    s3 = get_s3_client(cfg)

    try:
        s3.head_object(Bucket=bucket_name, Key=file_path)
        return True
    except ClientError as e:
        # If the exception is due to the file not existing, return False
        if e.response['Error']['Code'] == '404':
            return False
        else:
            raise e
    except Exception as e:
        raise Exception(f"Unexpected error occurred during s3 head operation. Error: {e}")


def generate_presigned_url_for_download(path: str, expires_in: int, s3_loc: S3Location, config: Config) -> str:
    """    generate_presigned_url_for_download
        Given a path to an object in an S3 bucket, will return a presigned url (generated
        with scoped credentials to that dataset only) which can be used to download the object.

        Arguments
        ----------
        path : str
            The path to the object in the bucket. This is the full path that comes after the bucket name.
            E.g. datasets/dataset_id/file_path..."
        expires_in : int
            The number of seconds until the presigned url expires.
        s3_loc : S3Location
            s3 location for scoping credentials to.
        config : Config
            The configuration object.

        Returns
        -------
         : str
            The presigned url.

        Raises
        ------
        Exception
            Failed to generate presigned url. Error: {e}

        See Also (optional)
        --------

        Examples (optional)
        --------
    """
    # On-prem MinIO: use static creds, no STS
    if config.storage_backend == "minio" and config.s3_access_key and config.s3_secret_key:
        s3 = get_s3_client(config)
    else:
        # AWS: credentials scoped to this dataset s3 location only
        creds: Credentials = call_sts_oidc_service(
            session_name="Generate-presigned-url-for-dataset-download",
            s3_location=s3_loc,
            write=False,
            config=config,
        )
        s3 = boto3.client(
            "s3",
            aws_access_key_id=creds.aws_access_key_id,
            aws_secret_access_key=creds.aws_secret_access_key,
            aws_session_token=creds.aws_session_token,
        )

    try:
        url = s3.generate_presigned_url(
            ClientMethod='get_object',  # get_object for download rights only.
            Params=get_presigned_url_method_params(path, config),
            ExpiresIn=expires_in,
        )

    except Exception as e:
        raise Exception(f"Failed to generate presigned url. Error: {e}")
    return url


def get_presigned_url_method_params(path: str, config: Config) -> Dict[str, str]:
    """    get_presigned_url_method_params
        Given a path to an object in an S3 bucket, will return a dictionary of 
        parameters to be passed to the generate_presigned_url function. 

        If being used for get_object methods, path should be the path
        to the object for download. 

        If being used for uplaod, path should be the file name that will be uploaded.

        Arguments
        ----------
        path : str
            The path to the object in the bucket.
        config : Config
            The configuration object.

        Returns
        -------
         : dict
            The dictionary of parameters to be passed to the generate_presigned_url function.

        See Also (optional)
        --------

        Examples (optional)
        --------
    """
    return {
        'Bucket': config.S3_STORAGE_BUCKET_NAME,
        'Key': path,
        # This makes the server indicate that the browser can download as an
        # attachment
        'ResponseContentDisposition': f"attachment; filename={path}"
    }
