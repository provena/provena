from pydantic import BaseSettings, SecretStr

class Config(BaseSettings):
    # Connection information
    port: int
    smtp_server: str

    # Username/password
    username: str
    password: SecretStr

    # Email from address
    email_from: str

    # Use a .env file
    class Config:
        env_file = ".env"
