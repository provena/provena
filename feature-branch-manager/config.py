from pydantic import BaseSettings
from github import Github
from typing import List


class Config(BaseSettings):
    # token to use when authenticating to github API - requires repo access
    github_token: str

    # combined repo name to target e.g. provena/provena
    repo_string: str

    # regex pattern to look at in PR titles to identify ticket number
    # e.g. r"JIRA-(\d+)"
    ticket_pattern: str

    # regex pattern to determine if a cfn stack is a feature deployment
    # e.g. r"deploy-[f]?(\d+)-my-project"
    deploy_stack_pattern: str

    # pipeline stack name regex pattern to look for
    pipeline_stack_pattern : str = r"f(\d+)Pipeline"

    # regex pattern to search for in PR description as backup to title match
    feat_md_pattern: str = r"feat-(\d+)"

    # prefixes and postfixes around ticket numbers for various stacks
    pipeline_stack_prefix: str = "f"
    pipeline_stack_postfix: str = "Pipeline"

    def build_pipeline_stack_name(self, id: str) -> str:
        return f"{self.pipeline_stack_prefix}{id}{self.pipeline_stack_postfix}"

    # e.g. deploy-f
    deploy_stack_prefix: str
    # e.g. -my-app-name
    deploy_stack_postfix: str

    def build_app_stack_name(self, id: str) -> str:
        return f"{self.deploy_stack_prefix}{id}{self.deploy_stack_postfix}"

    # read from env file
    class Config:
        env_file = ".env"


config = Config()

# setup github instance
g = Github(config.github_token)
