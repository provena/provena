from functools import lru_cache
from pydantic import BaseSettings
from typing import List, Union, Callable, Dict

HDL_PREFIX = "https://hdl.handle.net/"

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
    S3_STORAGE_BUCKET_NAME: str
    HANDLE_API_ENDPOINT: str
    REGISTRY_API_ENDPOINT: str
    job_api_endpoint: str
    AUTH_API_ENDPOINT: str
    REVIEWERS_TABLE_NAME: str

    SERVICE_ACCOUNT_SECRET_ARN: str
    KEYCLOAK_ISSUER: str

    OIDC_SERVICE_ACCOUNT_SECRET_ARN: str
    OIDC_SERVICE_ROLE_ARN: str
    BUCKET_ROLE_ARN: str

    SCHEMA_PATH: str = 'resources/schema.json'
    DATASET_PATH: str = "datasets"
    METADATA_FILE_NAME: str = "metadata.json"

    # Validation turned on - this is an external dependency - only leave off for
    # testing
    REMOTE_PRE_VALIDATION: bool = True

    # 3 hour session durations (seconds)
    # maximum role chained duration is one hour!
    SESSION_DURATION_SECONDS: int = 60 * 60 * 1
    SERVICE_SESSION_DURATION_SECONDS: int = 60 * 60 * 8
    # 6 hours
    CONSOLE_SESSION_DURATION_SECONDS: int = 60 * 60 * 12
    KEYCLOAK_TOKEN_POSTFIX: str = "/protocol/openid-connect/token"

    # for use in writing temp files
    TEMP_FILE_LOCATION: str = "/tmp"

    # Server side caching
    SERVER_CACHING_ENABLED: bool = True

    @property
    def KEYCLOAK_TOKEN_ENDPOINT(self) -> str:
        return self.keycloak_endpoint + self.KEYCLOAK_TOKEN_POSTFIX

    class Config:
        env_file = ".env"
        frozen = True


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
        f"{prefix}{base_domain}",
        f"{prefix}www.{base_domain}",
        f"{prefix}data.{base_domain}",
        f"{prefix}prov.{base_domain}",
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


base_config = BaseConfig()

# Setup settings dependency


@lru_cache
def get_settings() -> Config:
    return Config()
