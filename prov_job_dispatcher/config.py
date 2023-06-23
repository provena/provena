from pydantic import BaseSettings
from datetime import timedelta

class Config(BaseSettings):
    # required env variables
    JOB_TABLE_NAME: str
    SERVICE_ROLE_SECRET_ARN: str
    KEYCLOAK_ENDPOINT: str
    PROV_API_ENDPOINT: str
    
    
    KEYCLOAK_TOKEN_POSTFIX: str = "/protocol/openid-connect/token"

    @property
    def KEYCLOAK_TOKEN_ENDPOINT(self) -> str:
        return self.KEYCLOAK_ENDPOINT + self.KEYCLOAK_TOKEN_POSTFIX
    
config = Config()