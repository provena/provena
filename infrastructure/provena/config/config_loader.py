from provena.config.config_class import (
    ProvenaConfig,
    ProvenaUIOnlyConfig,
    ConfigBase,
    DeploymentType
)
from typing import Callable, Union

# This is a critical function for CDK config but is used in other parts of the
# project hence inclusion in the shared utilities
from ProvenaSharedFunctionality.utils import perform_config_substitution

CONFIGS_FILE_PREFIX = "configs"

ConfigTypes = Union[ProvenaConfig, ProvenaUIOnlyConfig]
ConfigDispatch = Callable[[], ConfigTypes]

def get_config(config_id: str) -> ConfigDispatch:
    def func() -> ConfigTypes:
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

        # parse as base model
        config = ConfigBase.parse_raw(replaced)

        # identify type
        if config.type == DeploymentType.FULL_APP:
            return ProvenaConfig.parse_raw(replaced)
        elif config.type == DeploymentType.UI_ONLY:
            return ProvenaUIOnlyConfig.parse_raw(replaced)
        else: 
            raise ValueError(f"Unexpected DeploymentType in base config: {config.type}. Report to system administrator.")
    return func