import logging
from typing import Dict
import boto3
from botocore.exceptions import ClientError
from config import Config

log = logging.getLogger(__name__)


def upload_file_to_s3(path: str, bucket: str, key: str) -> None:
    """Upload local file `path` to S3 `bucket` at `key`.

    Raises ClientError on failure.
    """
    s3 = boto3.client("s3")
    try:
        s3.upload_file(Filename=path, Bucket=bucket, Key=key)
    except ClientError:
        log.exception("Failed to upload %s to s3://%s/%s", path, bucket, key)
        raise


def get_presigned_url_method_params(key: str, config: Config) -> Dict[str, str]:
    filename = key.split('/')[-1]
    return {
        'Bucket': config.REPORT_BUCKET_NAME,
        'Key': key,
        'ResponseContentDisposition': f"attachment; filename={filename}"
    }


def generate_presigned_url_for_report(key: str, expires_in: int, config: Config) -> str:
    """Generate presigned GET URL for a report object using settings from `config`.

    This uses the current task/instance role credentials (no STS/OIDC).
    """
    if not config.REPORT_BUCKET_NAME:
        raise ValueError("REPORT_BUCKET_NAME not configured in Config")

    try:
        s3 = boto3.client('s3')
        url = s3.generate_presigned_url(
            ClientMethod='get_object',
            Params=get_presigned_url_method_params(key, config),
            ExpiresIn=int(expires_in),
        )
        return url
    except Exception as e:
        log.exception("Failed to generate presigned url for report %s", key)
        raise