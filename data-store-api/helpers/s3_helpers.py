
from typing import List
import boto3  # type: ignore
from fastapi import HTTPException
from helpers.sts_helpers import call_sts_oidc_service
from SharedInterfaces.DataStoreAPI import Credentials
from .sanitize import *
from config import Config
from SharedInterfaces.RegistryModels import *


def get_dataset_files(dataset_id: IdentifiedResource, config: Config) -> List[str]:
    """Given a dataset ID will return a list of all the files in the dataset.
    NOTE: that, this includes folders as S3 sees them as items. E.g. dataset/test_folder/ 
    will be returned in the list..
    List entries are formatted as full paths from bucket root. E.g., "datasets/{dataset_id}/{file_path}". This
    helps prevent people form ../{other dataset id}{file path} to access other datasets they should not.

    Parameters
    ----------
    dataset_id : IdentifiedResource
        The dataset ID to source files for.
    config : Config
        config object. Used for bucket name of datastore

    Returns
    -------
    List[str]
        List of files (and folders which s3 sees as files)

    Raises
    ------
    HTTPException
        500 if fails to source objects for dataset with id {dataset_id}
    """

    # The folder path from the bucket root to inside the dataset folder.
    folder_path = config.DATASET_PATH + '/' + sanitize_handle(dataset_id)
    try:
        s3 = boto3.client('s3')
        objects_resp = s3.list_objects_v2(
            Bucket=config.S3_STORAGE_BUCKET_NAME, Prefix=folder_path)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to source objects for dataset with id {dataset_id}. Error: {e}"
        )

    if 'Contents' not in objects_resp:
        raise HTTPException(
            status_code=400,
            detail=f"Dataset {dataset_id} is empty. No content can be downloaded."
        )

    return [obj['Key'] for obj in objects_resp['Contents']]


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

    # credentials scoped to this dataset s3 location only
    creds: Credentials = call_sts_oidc_service(
        session_name=f"Generate-presigned-url-for-dataset-download",
        s3_location=s3_loc,
        write=False,
        config=config
    )

    try:
        # generate presigned url using s3 client with creds scope to the dataset at s3 loc only
        s3 = boto3.client('s3', aws_access_key_id=creds.aws_access_key_id,
                          aws_secret_access_key=creds.aws_secret_access_key, aws_session_token=creds.aws_session_token)

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
