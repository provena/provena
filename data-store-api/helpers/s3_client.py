"""S3/MinIO client factory for on-prem support."""
import boto3
from typing import Optional
from config import Config


def get_s3_client(config: Config, use_static_creds: bool = False):
    """
    Get S3 client. For MinIO (storage_backend='minio'), uses endpoint_url and static creds.
    For AWS, uses default boto3 behavior.
    """
    if config.storage_backend == "minio" and config.s3_endpoint_url:
        kwargs = {
            "endpoint_url": config.s3_endpoint_url,
            "use_ssl": config.s3_use_ssl,
        }
        if config.s3_access_key and config.s3_secret_key:
            kwargs["aws_access_key_id"] = config.s3_access_key
            kwargs["aws_secret_access_key"] = config.s3_secret_key
        return boto3.client("s3", **kwargs)
    return boto3.client("s3")
