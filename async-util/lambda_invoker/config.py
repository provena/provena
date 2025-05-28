from pydantic import BaseSettings

# These are read from the env at runtime


class Settings(BaseSettings):
    # ECS Cluster ARN
    cluster_arn: str
    # The VPC to run in
    vpc_id: str
    # How long do tasks run before auto-quitting due to inactivity
    idle_timeout: int
    # how many possible tasks can be running before we stop - safety cutoff
    max_task_scaling: int

    # Type = PROV_LODGE
    prov_lodge_task_definition_arn: str

    # Type = REGISTRY
    registry_task_definition_arn: str

    # Type = EMAIL
    email_task_definition_arn: str

    # Type = REPORT
    report_task_definition_arn: str
