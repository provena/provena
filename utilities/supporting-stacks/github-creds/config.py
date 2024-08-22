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


class GithubBootstrapConfig(BaseModel):
    # AWS Region/Account to bootstrap with credentials
    env: AWSTarget
    # The ARN of the AWS Secret manager secret containing the OAuth github token
    # as a simple string
    github_token_arn: str


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


def load_and_validate_config(path: str) -> Optional[GithubBootstrapConfig]:
    """
    Load and validate a config file.

    Args:
        path (str): The path to the config file.

    Returns:
        Optional[GithubBootstrapConfig]: A validated GithubBootstrapConfig object, or None if any error occurs.
    """
    try:
        with open(path, "r") as file:
            raw_config = file.read()

        # Perform config substitution
        substituted_config = perform_config_substitution(raw_config)

        # Parse and validate using Pydantic model
        return GithubBootstrapConfig.model_validate_json(substituted_config)
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON in {path}: {e}")
    except Exception as e:
        print(f"Error processing config file {path}: {e}")
    return None


def retrieve_config() -> GithubBootstrapConfig:
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
