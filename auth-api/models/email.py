from pydantic import BaseModel, SecretStr


class EmailConnectionProfile(BaseModel):
    # Connection information
    port: int
    smtp_server: str

    # Username/password
    username: str
    password: SecretStr

    # Email from and to
    email_from: str
    email_to: str
