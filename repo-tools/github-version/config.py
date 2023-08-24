from pydantic import BaseSettings

class BaseConfig(BaseSettings):

    # should be present in the environment that runs this tool
    github_oauth_token: str

    # use .env file
    class Config:
        env_file = ".env"


class Config(BaseConfig):
    class Config:
        env_file = ".env"


base_config = BaseConfig()