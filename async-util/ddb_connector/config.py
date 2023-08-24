from pydantic import BaseSettings


class Settings(BaseSettings):
    # Job status table name
    table_name: str
