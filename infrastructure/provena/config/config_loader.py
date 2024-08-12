from provena.config.config_class import (
    ProvenaConfig,
    ProvenaUIOnlyConfig,
    GithubBootstrapConfig,
)
import re
import os
from typing import Callable, Optional, Dict

# This is a critical function for CDK config but is used in other parts of the
# project hence inclusion in the shared utilities
from ProvenaSharedFunctionality.utils import perform_config_substitution

CONFIGS_FILE_PREFIX = "configs"

AppConfigType = Callable[[], ProvenaConfig]
UIConfigType = Callable[[], ProvenaUIOnlyConfig]
BootstrapConfigType = Callable[[], GithubBootstrapConfig]

def get_app_config(config_id: str) -> AppConfigType:
    def func() -> ProvenaConfig:
        # load config file
        file_name = f"{CONFIGS_FILE_PREFIX}/{config_id.lower()}.json"
        try:
            with open(file_name, "r") as f:
                content = f.read()
        except Exception:
            prev = file_name
            file_name = f"{CONFIGS_FILE_PREFIX}/{config_id.upper()}.json"
            print(f"Couldn't find {prev} trying {file_name}")
            with open(file_name, "r") as f:
                content = f.read()

        # perform variable replacement
        replaced = perform_config_substitution(content)
        # parse as model
        config = ProvenaConfig.parse_raw(replaced)
        f = open('feat.json', 'w')
        f.write(config.json(indent=2, exclude_defaults=True))
        f.close()
        return config 

    return func


def get_ui_only_config(config_id: str) -> UIConfigType:
    def func() -> ProvenaUIOnlyConfig:
        # load config file
        file_name = f"{CONFIGS_FILE_PREFIX}/{config_id.lower()}-ui.json"
        try:
            with open(file_name, "r") as f:
                content = f.read()
        except Exception:
            prev = file_name
            file_name = f"{CONFIGS_FILE_PREFIX}/{config_id.upper()}-ui.json"
            print(f"Couldn't find {prev} trying {file_name}")
            with open(file_name, "r") as f:
                content = f.read()

        # perform variable replacement
        replaced = perform_config_substitution(content)
        # parse as model
        output = ProvenaUIOnlyConfig.parse_raw(replaced)
        return output

    return func


def get_bootstrap_config(config_id: str) -> BootstrapConfigType:
    def func() -> GithubBootstrapConfig:
        # load config file
        file_name = f"{CONFIGS_FILE_PREFIX}/{config_id.lower()}-github.json"
        try:
            with open(file_name, "r") as f:
                content = f.read()
        except Exception:
            prev = file_name
            file_name = f"{CONFIGS_FILE_PREFIX}/{config_id.upper()}-github.json"
            print(f"Couldn't find {prev} trying {file_name}")
            with open(file_name, "r") as f:
                content = f.read()

        # perform variable replacement
        replaced = perform_config_substitution(content)
        # parse as model
        return GithubBootstrapConfig.parse_raw(replaced)

    return func
