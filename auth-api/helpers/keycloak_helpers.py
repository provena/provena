import json
from typing import Optional

import botocore  # type: ignore
import requests
from aws_secretsmanager_caching import SecretCache, SecretCacheConfig  # type: ignore
from fastapi.exceptions import HTTPException
from requests.auth import HTTPBasicAuth

from config import *
from config import Config


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


def get_service_token(secret_cache: Optional[SecretCache], config: Config) -> str:
    """    get_service_token
        Returns a Keycloak service account (client credentials) token.
        Uses either (1) on-prem env credentials (KEYCLOAK_SERVICE_CLIENT_ID/SECRET)
        or (2) AWS Secrets Manager via secret_cache.

        Arguments
        ----------
        secret_cache : SecretCache or None
            The secret cache for AWS SM (None in test/on-prem when using env creds)
        config : Config
            App config; may contain keycloak_service_client_id / keycloak_service_client_secret

        Returns
        -------
         : str
            The access token

        Raises
        ------
        HTTPException
            503 if neither env credentials nor secret_cache is configured
        See Also (optional)
        --------

        Examples (optional)
        --------
    """
    # On-prem: use Keycloak client credentials from env when set
    if config.keycloak_service_client_id and config.keycloak_service_client_secret:
        return get_client_credential_token(
            client_id=config.keycloak_service_client_id,
            client_secret=config.keycloak_service_client_secret,
            grant_type=config.keycloak_service_grant_type,
            token_endpoint=config.keycloak_token_endpoint,
        )
    # AWS: use Secrets Manager
    if secret_cache is not None and config.service_account_secret_arn:
        secret_json = json.loads(
            retrieve_secret_value(
                secret_arn=config.service_account_secret_arn,
                secret_cache=secret_cache,
            )
        )
        return get_client_credential_token(
            client_id=secret_json["client_id"],
            client_secret=secret_json["client_secret"],
            grant_type=secret_json.get("grant_type", "client_credentials"),
            token_endpoint=config.keycloak_token_endpoint,
        )
    raise HTTPException(
        status_code=503,
        detail="Service account not configured. Set KEYCLOAK_SERVICE_CLIENT_ID and "
        "KEYCLOAK_SERVICE_CLIENT_SECRET (on-prem) or use AWS Secrets Manager.",
    )


def get_client_credential_token(client_id: str, client_secret: str, token_endpoint: str, grant_type: str) -> str:
    """    get_service_access_token
        Given the client id, secret, grant type and endpoint will perform a token 
        request against the keycloak server to retrieve a service account credential.

        Arguments
        ----------
        client_id : str
            The keycloak client id
        client_secret : str
            The keycloak client secret
        token_endpoint : str
            The token endpoint for keycloak auth server
        grant_type : str
            The grant type (probably client_credentials)

        Returns
        -------
         : str
            The access token

        Raises
        ------
        HTTPException
            500 if something goes wrong making request
        HTTPException
            500 if 401 unauthorized response

        See Also (optional)
        --------

        Examples (optional)
        --------
    """
    auth = HTTPBasicAuth(client_id, client_secret)
    payload = {
        'grant_type': grant_type
    }

    # make request
    response = requests.post(token_endpoint, data=payload, auth=auth)

    try:
        assert response.status_code == 200
    except Exception as e:
        if response.status_code == 401:
            raise HTTPException(
                status_code=500,
                detail="API service account creds appear to be incorrect. Contact administrator."
            )
        else:
            raise HTTPException(
                status_code=500,
                detail=f"API service creds request failed, code: {response.status_code}."
            )

    return response.json()['access_token']
