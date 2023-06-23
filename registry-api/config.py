from SharedInterfaces.RegistryModels import *
from pydantic import BaseSettings
from functools import lru_cache
from typing import List, Union, Callable, Dict
import os


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
    """This config object uses Pydantic BaseSettings (through 
    the parent class BaseConfig defined above) to define 
    possibly route specific settings. 

    These can be configured with defaults as in some cases below, 
    instantiated through a direct constructor, env variables, 
    or with a .env file.
    """

    # Dynamo DB table name where reg items are persisted
    registry_table_name: str

    # Dynamo DB table name where reg items auth info are persisted
    auth_table_name: str

    # Dynamo DB table name where reg items lock information is persisted
    lock_table_name: str

    # Auth api endpoint
    auth_api_endpoint: str

    # The endpoint of the handle service API
    handle_api_endpoint: str

    # Creds for the keycloak service account used to make
    # requests on behalf of user
    service_account_secret_arn: str

    # Should the handle ids be mocked?
    mock_handle: bool = False

    # Postfix to add to keycloak endpoint to reach token endpoint
    keycloak_token_postfix: str = "/protocol/openid-connect/token"

    # for use in writing temp files
    TEMP_FILE_LOCATION: str = "/tmp"

    # Entity specific run-time validation.
    perform_validation: bool = True

    # enforce special proxy roles for dataset/model run
    enforce_special_proxy_roles: bool = True

    # enforce user auth only disable for unit testing to avoid auth api dependency
    enforce_user_auth: bool = True

    # should user links be enforced (disable for testing only!)
    enforce_user_links: bool = True

    # Derived property of token endpoint
    @property
    def keycloak_token_endpoint(self) -> str:
        return self.keycloak_endpoint + self.keycloak_token_postfix

    # Use a .env file
    class Config:
        env_file = ".env"


# instantiate base config object
base_config = BaseConfig()

HDL_PREFIX = f"https://registry.{base_config.domain_base}/item"

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


@lru_cache()
def get_settings() -> Config:
    # define dep injection for proper config
    return Config()
