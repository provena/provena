from pydantic import BaseSettings, root_validator
from typing import List, Union, Callable, Dict, Optional, Any
from functools import lru_cache

# these settings are essential from start to finish
# and its not worth sorting out dep injection
# for them


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

    # commit hash
    git_commit_id: Optional[str]
    feature_number: Optional[str]

    # monitoring via sentry
    monitoring_enabled: Optional[bool] = False
    sentry_dsn: Optional[str] = None

    @property
    def sentry_environment(self) -> str:
        return f"{self.stage}:{self.feature_number}" if self.feature_number else self.stage

    # validate sentry dsn is provided if monitoring is enabled
    @root_validator
    def valide_sentry_config(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        if values.get("monitoring_enabled") == True and values.get("sentry_dsn") is None:
            raise ValueError(
                "Sentry DSN is required if monitoring is enabled.")
        return values

    # use .env file
    class Config:
        env_file = ".env"


class Config(BaseConfig):
    # General API settings
    service_account_secret_arn: str
    registry_api_endpoint: str
    mock_graph_db: bool = False
    neo4j_host: str
    neo4j_port: int

    # Job API endpoint
    job_api_endpoint: str

    # default depth upper limit
    depth_upper_limit: int = 10
    depth_default_limit: int = 2
    depth_specialised_default_limit: int = 4

    # potential overrides of user/pass for testing neo4j
    neo4j_auth_arn: Optional[str] = None
    neo4j_test_username: Optional[str] = None
    neo4j_test_password: Optional[str] = None

    # default settings
    keycloak_token_postfix: str = "/protocol/openid-connect/token"

    @property
    def keycloak_token_endpoint(self) -> str:
        return self.keycloak_endpoint + self.keycloak_token_postfix

    neo4j_encrypted: bool = False

    # for use in writing temp files
    TEMP_FILE_LOCATION: str = "/tmp"

    # config options for csv templates
    INPUT_DATASET_TEMPLATE_PREFIX: str = "Input dataset id for template: "
    OUTPUT_DATASET_TEMPLATE_PREFIX: str = "Output dataset id for template: "
    INPUT_TEMPLATE_RESOURCE_PREFIX: str = "Input resource: "
    OUTPUT_TEMPLATE_RESOURCE_PREFIX: str = "Output resource: "
    WORKFLOW_TEMPLATE_MARKER_PREFIX: str = "workflow template id"
    TEMPLATE_DISPLAY_NAME_HEADER: str = "display name"
    TEMPLATE_MODEL_VERSION_HEADER: str = "model version (optional)"
    TEMPLATE_DESCRIPTION_HEADER: str = "description"
    TEMPLATE_AGENT_HEADER: str = "agent id"
    STUDY_HEADER: str = "study id"
    TEMPLATE_ORGANISATION_HEADER: str = "requesting organisation id"
    TEMPLATE_START_TIME_HEADER: str = "execution start time (YYYY-MM-DD HH:MM:SS+HH:MM)"
    TEMPLATE_END_TIME_HEADER: str = "execution end time (YYYY-MM-DD HH:MM:SS+HH:MM)"

    class Config:
        env_file = ".env"
        frozen = True


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
    return ".*"


def stage_cors_generator(base_domain: str) -> CorsGeneratorReturnType:
    # generates regex format -> same as DEV but doesn't include localhost
    prefix = "https:\/\/"
    safe_base = base_domain.replace(".", "\.")
    return f"({prefix}.*\.{safe_base}|{prefix}{safe_base})"


def prod_cors_generator(base_domain: str) -> CorsGeneratorReturnType:
    # generates regex format -> prov and data front ends currently supported
    prefix = "https://"
    options: List[str] = [
        f"{prefix}prov.{base_domain}",
        f"{prefix}data.{base_domain}"
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
