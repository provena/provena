import boto3  # type: ignore
from requests_aws4auth import AWS4Auth  # type: ignore
from typing import Any


def get_auth(region: str) -> Any:
    # setup credentials for https requests to the search domain
    service = 'es'  # elastic-search
    credentials = boto3.Session().get_credentials()
    return AWS4Auth(credentials.access_key, credentials.secret_key,
                    region, service, session_token=credentials.token)
