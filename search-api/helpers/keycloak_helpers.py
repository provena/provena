import requests
from requests.auth import HTTPBasicAuth
from fastapi.exceptions import HTTPException
from config import Config
from aws_secretsmanager_caching import SecretCache, SecretCacheConfig  # type: ignore
import json
import botocore  # type: ignore
from cachetools.func import ttl_cache


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


def get_service_token(secret_cache: SecretCache, config : Config) -> None:
    """    get_service_token
        Given the secret cache object, will get the 
        secret ARN for the service account, expand it 
        and make a keycloak token request, then return
        the access token.

        Arguments
        ----------
        secret_cache : SecretCache
            The secret cache for AWS SM

        Returns
        -------
         : str
            The token

        See Also (optional)
        --------

        Examples (optional)
        --------
    """
    # TODO implement if service account required
    # sample below

    """
    # Get the secret details (potentially cached)
    assert config.SERVICE_ACCOUNT_SECRET_ARN
    secret_json = json.loads(
        retrieve_secret_value(
            secret_arn=config.SERVICE_ACCOUNT_SECRET_ARN,
            secret_cache=secret_cache
        )
    )

    # Get the token from keycloak using the secret
    return get_client_credential_token(
        client_id=secret_json['client_id'],
        client_secret=secret_json['client_secret'],
        grant_type=secret_json['grant_type'],
        token_endpoint=config.KEYCLOAK_TOKEN_ENDPOINT
    )
    """
    # should return string
    return None


@ttl_cache(ttl=60)
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
