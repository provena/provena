from provena.config.config_class import (
    ProvenaConfig,
    ProvenaUIOnlyConfig,
    GithubBootstrapConfig,
)
import re
import os
from typing import Callable, Optional

CONFIGS_FILE_PREFIX = "configs"

AppConfigType = Callable[[], ProvenaConfig]
UIConfigType = Callable[[], ProvenaUIOnlyConfig]
BootstrapConfigType = Callable[[], GithubBootstrapConfig]

def substitute_env_vars(input_string: str) -> str:
    """
    Perform case-insensitive, bash-style variable substitution on the input string with extended functionality.

    The function supports the following patterns:
    1. ${VARIABLE_NAME} - Basic substitution
    2. ${VARIABLE_NAME:-default_value} - Substitution with default value
    3. ${VARIABLE_NAME?true_value||false_value} - Conditional substitution with else value
    4. ${VARIABLE_NAME?true_value} - Conditional substitution without else value (returns empty string if falsey)

    Variable names are case-insensitive. For conditional substitution, a value is considered
    truthy if it exists and is not explicitly set to "false" (case-insensitive).

    Args:
        input_string (str): The input string containing variables to be substituted.

    Returns:
        str: The input string with all variables substituted.

    Example:
        >>> os.environ['NAME'] = 'John'
        >>> os.environ['DEBUG'] = '0'
        >>> substitute_env_vars('Hello, ${name}!')
        'Hello, John!'
        >>> substitute_env_vars('Mode: ${DEBUG?Debug}')
        'Mode: Debug'
        >>> substitute_env_vars('Admin: ${IS_ADMIN?Administrator}')
        'Admin: '
    """
    def get_env_var(var_name: str) -> Optional[str]:
        """Get environment variable value case-insensitively."""
        for key, value in os.environ.items():
            if key.lower() == var_name.lower():
                return value
        return None

    def is_truthy(value: Optional[str]) -> bool:
        """Determine if a value is truthy."""
        return value is not None and value.lower() != "false"

    def replace_var(match: re.Match[str]) -> str:
        full_match = match.group(0)
        var_content = match.group(1)

        # Check for conditional pattern
        if '?' in var_content:
            var_name, rest = var_content.split('?', 1)
            if '||' in rest:
                true_value, false_value = rest.split('||', 1)
                return true_value if is_truthy(get_env_var(var_name)) else false_value
            else:
                true_value = rest
                return true_value if is_truthy(get_env_var(var_name)) else ''

        # Check for default value pattern
        if ':-' in var_content:
            var_name, default_value = var_content.split(':-', 1)
            return get_env_var(var_name) or default_value

        # Basic substitution
        var_name = var_content
        value = get_env_var(var_name)
        
        if value is None:
            print(f"Warning: Environment variable '{var_name}' not found and no default provided.")
            return full_match  # Return the original ${VARIABLE_NAME} unchanged
        
        return value

    pattern = r'\$\{([^}]+)\}'
    return re.sub(pattern, replace_var, input_string)

def get_app_config(config_id: str) -> AppConfigType:
    def func() -> ProvenaConfig:
        # load config file
        file_name = f"{CONFIGS_FILE_PREFIX}/{config_id}.json"
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
        replaced = substitute_env_vars(content)
        # parse as model
        return ProvenaConfig.parse_raw(replaced)

    return func


def get_ui_only_config(config_id: str) -> UIConfigType:
    def func() -> ProvenaUIOnlyConfig:
        # load config file
        file_name = f"{CONFIGS_FILE_PREFIX}/{config_id}-ui.json"
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
        replaced = substitute_env_vars(content)
        # parse as model
        return ProvenaUIOnlyConfig.parse_raw(replaced)

    return func


def get_bootstrap_config(config_id: str) -> BootstrapConfigType:
    def func() -> GithubBootstrapConfig:
        # load config file
        file_name = f"{CONFIGS_FILE_PREFIX}/{config_id}-github.json"
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
        replaced = substitute_env_vars(content)
        # parse as model
        return GithubBootstrapConfig.parse_raw(replaced)

    return func
