from aws_secretsmanager_caching import SecretCache, SecretCacheConfig  # type: ignore
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

@ttl_cache()
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