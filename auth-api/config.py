from functools import lru_cache
from pydantic import BaseSettings
from typing import List, Union, Callable, Dict


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

    # Admin console - derived dynamically from keycloak endpoint
    @property
    def admin_console_endpoint(self) -> str:
        # remove /realms/* and add appropriate end point
        realm_name = self.keycloak_endpoint.split("/realms/")[1].split("/")[0]
        return self.keycloak_endpoint.split("/realms/")[0] + f"/admin/{realm_name}/console"

    # Domain base e.g. demo.provena.io - used to generate CORS information -
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

    # Registry API endpoint (used for link service id validation)
    registry_api_endpoint: str

    # Where are the email server creds?
    email_secret_arn: str

    # Dynamo db table name for access requests
    access_request_table_name: str

    # Dynamo db table name for user groups
    user_groups_table_name: str

    # Dynamo db table name for the username <-> registry person link table
    username_person_link_table_name: str

    # Name of the GSI on the link table which allows reverse lookup from person
    # ID -> username
    username_person_link_table_person_index_name: str

    # How long should the requests last in the table
    # before being killed
    request_expiry_days: int = 30

    # Wait at least 5 days on pending request before allowing another
    minimum_request_waiting_time_days: int = 5

    # validate person in registry when performing link updates
    # DEBUG ONLY
    link_update_registry_connection: bool = True

    # for use in writing temp files
    TEMP_FILE_LOCATION: str = "/tmp"

    # use .env file
    class Config:
        env_file = ".env"


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


# Instantiate instance of base config.
base_config = BaseConfig()


@lru_cache()
def get_settings() -> Config:
    # Dependency injection for Config
    return Config()
