from pydantic import BaseSettings, root_validator
from typing import Optional, Dict, Union, List, Any
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
        if values.get("monitoring_enabled")==True and values.get("sentry_dsn") is None:
            raise ValueError(
                "Sentry DSN is required if monitoring is enabled.")
        return values

    # use .env file
    class Config:
        env_file = ".env"



class Config(BaseConfig):
    # ARDC service endpoint
    handle_service_endpoint: str

    # Handle creds ARN
    handle_service_creds_arn: str

    TEMP_FILE_LOCATION: str = "/tmp"

    class Config:
        env_file = ".env"


base_config = BaseConfig()


# Setup settings dependency
@lru_cache()
def get_settings() -> Config:
    return Config()
