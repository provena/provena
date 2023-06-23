from config import Config, get_settings
import boto3  # type: ignore
from opensearchpy import OpenSearch, RequestsHttpConnection, AWSV4SignerAuth
from fastapi import Depends


def get_search_client(config: Config = Depends(get_settings)) -> OpenSearch:
    # See
    # https://github.com/opensearch-project/opensearch-py/blob/main/USER_GUIDE.md#using-iam-credentials-for-authentication

    # Setup signed IAM V4 auth
    host = config.search_domain
    region = config.aws_region
    credentials = boto3.Session().get_credentials()
    auth = AWSV4SignerAuth(credentials, region)

    # return the client
    return OpenSearch(
        hosts=[{'host': host, 'port': 443}],
        http_auth=auth,
        use_ssl=True,
        verify_certs=True,
        connection_class=RequestsHttpConnection
    )
