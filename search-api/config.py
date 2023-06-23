from pydantic import BaseSettings
from typing import List, Union, Callable, Dict, Optional
from functools import lru_cache


class BaseConfig(BaseSettings):
    """BaseConfig defines a set of minimum required 
    configuration settings for start up of the app. 

    These are a special case vs the Config object 
    defined below - as they are not configurable
    on a per route level and are needed for startup
    processes of the app. 

    They need to be defined through a .env file 
    or environment variables. For info about how
    Pydantic BaseSettings works, see 
    https://pydantic-docs.helpmanual.io/usage/settings/
    """
    # Keycloak auth endpoint including /auth/realms/xxx
    keycloak_endpoint: str

    # Domain base e.g. your.domain.io, used to generate CORS information -
    # this is NOT specific to this API
    domain_base: str

    # Used to determine proper cors headers
    # TEST, DEV, STAGE, PROD, OPSPROD
    stage: str

    # Is this a test mode? override in unit tests - turns off signature
    # enforcement in keycloak token validation
    test_mode: bool = False

    # use .env file
    class Config:
        env_file = ".env"


class Config(BaseConfig):
    # search service (must not have https:// at the start)
    search_domain: str

    # search indexes
    registry_index: str
    global_index: str

    # linearised field name
    linearised_field: str

    # max query size
    default_query_size: int = 10
    max_query_size: int = 50

    aws_region: str = "ap-southeast-2"

    TEMP_FILE_LOCATION: str = "/tmp"

    class Config:
        env_file = ".env"


base_config = BaseConfig()

# can return either a regex string or list of standard strings
CorsGeneratorReturnType = Union[str, List[str]]
CorsGeneratorFunc = Callable[[str], Union[str, List[str]]]


def dev_cors_generator(base_domain: str) -> CorsGeneratorReturnType:
    # generates regex format
    https_prefix = "https:\/\/"
    http_prefix = "http:\/\/"
    safe_base = base_domain.replace(".", "\.")
    # https://*.base.com OR https://base.com OR http(s)://localhost:port
    return f"({https_prefix}.*\.{safe_base}|{https_prefix}{safe_base}|{https_prefix}localhost:\d*|{http_prefix}localhost:\d*)"


def stage_cors_generator(base_domain: str) -> CorsGeneratorReturnType:
    # generates regex format -> same as DEV but doesn't include localhost
    prefix = "https:\/\/"
    safe_base = base_domain.replace(".", "\.")
    return f"({prefix}.*\.{safe_base}|{prefix}{safe_base})"


def prod_cors_generator(base_domain: str) -> CorsGeneratorReturnType:
    # generates regex format -> same as DEV but doesn't include localhost
    prefix = "https://"
    options: List[str] = [
        f"{prefix}www.{base_domain}",
        f"{prefix}{base_domain}",
        f"{prefix}data.{base_domain}",
        f"{prefix}prov.{base_domain}",
        f"{prefix}registry.{base_domain}"
    ]
    return options


CORS_GENERATOR_MAP: Dict[str, CorsGeneratorFunc] = {
    "DEV": dev_cors_generator,
    "STAGE": stage_cors_generator,
    "PROD": prod_cors_generator,
}


def dispatch_cors(stage: str, base_domain: str) -> CorsGeneratorReturnType:
    generator_func = CORS_GENERATOR_MAP.get(stage)
    if generator_func is None:
        raise ValueError(
            "There is no CORS generator for the given stage. Aborting.")
    return generator_func(base_domain)

# Setup settings dependency


@lru_cache()
def get_settings() -> Config:
    return Config()
