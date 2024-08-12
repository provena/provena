#!/usr/bin/env python3
import os
import json
import aws_cdk as cdk
from github_creds.github_creds_stack import GithubCredsStack
from ProvenaSharedFunctionality.utils import perform_config_substitution
from pydantic import BaseModel
from typing import List, Optional


# define config class
class AWSTarget(BaseModel):
    account: str
    region: str

    @property
    def env(self) -> cdk.Environment:
        return cdk.Environment(account=self.account, region=self.region)


class GithubBootstrapConfig(BaseModel):
    env: AWSTarget
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
            raw_config = json.load(file)

        # Perform config substitution
        substituted_config = perform_config_substitution(raw_config)

        # Parse and validate using Pydantic model
        return GithubBootstrapConfig.model_validate_json(substituted_config)
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON in {path}: {e}")
    except Exception as e:
        print(f"Error processing config file {path}: {e}")
    return None


def select_config() -> GithubBootstrapConfig:
    """
    Find all configs, parse them, and let the user select interactively.
    Allows an override using the CONFIG_ID environment variable.

    Returns:
        GithubBootstrapConfig: The selected and validated configuration.
    """
    # Check for CONFIG_ID environment variable
    config_id = os.environ.get("CONFIG_ID")
    if config_id:
        config_name = f"{config_id.lower()}.json"
        configs = find_suitable_configs(".")
        matching_configs = [c for c in configs if os.path.basename(c) == config_name]
        if matching_configs:
            config = load_and_validate_config(matching_configs[0])
            if config:
                return config
            else:
                print(
                    f"Error: Unable to load or validate the specified config: {config_name}"
                )
        else:
            print(f"Error: Specified config not found: {config_name}")

    # Find and load all suitable configs
    configs = find_suitable_configs(".")
    valid_configs = []
    for config_path in configs:
        config = load_and_validate_config(config_path)
        if config:
            valid_configs.append((config_path, config))

    if not valid_configs:
        raise ValueError("No valid configurations found.")

    # Interactive selection
    print("Available configurations:")
    for i, (path, config) in enumerate(valid_configs):
        print(
            f"{i + 1}. {os.path.basename(path)} - Account: {config.env.account}, Region: {config.env.region}"
        )

    while True:
        try:
            selection = (
                int(input("Enter the number of the configuration you want to use: "))
                - 1
            )
            if 0 <= selection < len(valid_configs):
                return valid_configs[selection][1]
            else:
                print("Invalid selection. Please try again.")
        except ValueError:
            print("Invalid input. Please enter a number.")


# get user to select a suitable config
config = select_config()

app = cdk.App()

GithubCredsStack(app, "GithubCredsStack", config.github_token_arn, env=config.env.env)

app.synth()
