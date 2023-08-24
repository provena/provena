from pydantic import BaseSettings


class Config(BaseSettings):
    # TODO destub
    pass

    # Use a .env file
    class Config:
        env_file = ".env"
