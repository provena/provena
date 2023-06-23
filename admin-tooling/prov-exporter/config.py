from pydantic import BaseSettings

LOCAL_STORAGE_TOKEN_LOCATION = ".tokens.json"


class AWSConfig(BaseSettings):
    # Service account creds
    service_account_client_id: str
    service_account_client_secret: str

    # The application stage to target
    stage: str
