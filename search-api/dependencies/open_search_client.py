from config import Config, get_settings
import boto3  # type: ignore
from opensearchpy import OpenSearch, RequestsHttpConnection, AWSV4SignerAuth
from fastapi import Depends


def get_search_client(config: Config = Depends(get_settings)) -> OpenSearch:
    host = config.search_domain
    port = getattr(config, "opensearch_port", 443)
    use_ssl = getattr(config, "opensearch_use_ssl", True)
    verify_certs = getattr(config, "opensearch_verify_certs", True)

    # On-prem: use basic auth when search_auth_type='basic'
    if getattr(config, "search_auth_type", "iam") == "basic" and getattr(config, "opensearch_user", None) and getattr(config, "opensearch_password", None):
        return OpenSearch(
            hosts=[{"host": host, "port": port}],
            http_auth=(config.opensearch_user, config.opensearch_password),
            use_ssl=use_ssl,
            verify_certs=verify_certs,
            connection_class=RequestsHttpConnection,
        )

    # AWS: IAM SigV4 auth
    # https://github.com/opensearch-project/opensearch-py/blob/main/USER_GUIDE.md#using-iam-credentials-for-authentication
    region = config.aws_region
    credentials = boto3.Session().get_credentials()
    auth = AWSV4SignerAuth(credentials, region)

    return OpenSearch(
        hosts=[{"host": host, "port": port}],
        http_auth=auth,
        use_ssl=use_ssl,
        verify_certs=verify_certs,
        connection_class=RequestsHttpConnection,
    )
