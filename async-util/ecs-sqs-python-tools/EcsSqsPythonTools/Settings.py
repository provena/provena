from pydantic import BaseSettings
from ProvenaInterfaces.AsyncJobModels import JobType


class JobBaseSettings(BaseSettings):
    # These are env variables required for running a job
    idle_timeout: int
    
    # The SQS queue URL
    queue_url: str
    
    # Job status table ARN
    status_table_name: str
    
    # The SNS topic arn
    sns_topic_arn: str
    
    # job type
    job_type: JobType
    
    # job API endpoint
    job_api_endpoint: str

    # use .env file
    class Config:
        env_file = ".env"
