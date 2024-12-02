import os
import json
import aws_cdk as cdk
from ProvenaSharedFunctionality.utils import perform_config_substitution
from pydantic import BaseModel
from typing import List, Optional

CONFIG_PATH = "./configs"


# define config class
class AWSTarget(BaseModel):
    # AWS Account to send credentials to
    account: str
    # AWS Region to send credentials to
    region: str

    @property
    def env(self) -> cdk.Environment:
        return cdk.Environment(account=self.account, region=self.region)


class FeatureBranchManagerConfig(BaseModel):
    # Target for deployment
    env: AWSTarget

    # token to use when authenticating to github API - requires repo access
    github_api_token_arn: str

    # repo owner e.g. provena
    repo_owner: str

    # repo name to target e.g. provena
    repo_name: str

    # combined repo name to target e.g. provena/provena
    repo_string: str

    # what branch to checkout to get this script
    branch_name: str

    # path to script
    script_path: str = "scripts/delete_stale_fb.sh"

    # regex pattern to look at in PR titles to identify ticket number
    # e.g. r"JIRA-(\d+)"
    ticket_pattern: str

    # regex pattern to determine if a cfn stack is a feature deployment
    # e.g. r"deploy-[f]?(\d+)-my-project"
    deploy_stack_pattern: str

    # pipeline stack name regex pattern to look for
    pipeline_stack_pattern: str = r"f(\d+)Pipeline"

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


# Define method to load configs
def find_suitable_configs(path: str) -> List[str]:
    """
    Scan the specified folder and find all *.json file paths which don't start with 'sample'.

    Args:
        path (str): The directory path to scan for config files.

    Returns:
        List[str]: A list of suitable config file paths.
    """
    suitable_configs = []
    try:
        for file in os.listdir(path):
            if file.endswith(".json") and not file.lower().startswith("sample"):
                suitable_configs.append(os.path.join(path, file))
    except OSError as e:
        print(f"Error reading directory {path}: {e}")
    return suitable_configs


def load_and_validate_config(path: str) -> Optional[FeatureBranchManagerConfig]:
    """
    Load and validate a config file.

    Args:
        path (str): The path to the config file.

    Returns:
        Optional[FeatureBranchManagerStackConfig]: A validated GithubBootstrapConfig object, or None if any error occurs.
    """
    try:
        with open(path, "r") as file:
            raw_config = file.read()

        # Perform config substitution
        substituted_config = perform_config_substitution(raw_config)

        # Parse and validate using Pydantic model
        return FeatureBranchManagerConfig.parse_raw(substituted_config)
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON in {path}: {e}")
    except Exception as e:
        print(f"Error processing config file {path}: {e}")
    return None


def retrieve_config() -> FeatureBranchManagerConfig:
    """
    Select config with CONFIG_ID env variable from available configs in /configs

    Returns:
        GithubBootstrapConfig: The selected and validated configuration.
    """
    # Check for CONFIG_ID environment variable
    config_id = os.environ.get("CONFIG_ID")

    configs = find_suitable_configs(CONFIG_PATH)

    if not config_id:
        raise ValueError("Missing CONFIG_ID environment variable.")

    config_name = f"{config_id.lower()}.json"
    matching_configs = [c for c in configs if os.path.basename(c) == config_name]
    if matching_configs:
        config = load_and_validate_config(matching_configs[0])
        if config:
            return config
        else:
            raise Exception(
                f"Error: Unable to load or validate the specified config: {config_name}"
            )
    else:
        print(f"Could not find config with name {config_name}. Available configs:")
        for c in configs:
            print(f"Path: {c}")
        raise Exception(f"Error: Specified config not found: {config_name}")
