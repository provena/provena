from provena.config.config_class import ProvenaConfig, ProvenaUIOnlyConfig, GithubBootstrapConfig
import re
import os
from typing import Callable

CONFIGS_FILE_PREFIX = "configs"

AppConfigType = Callable[[], ProvenaConfig]
UIConfigType = Callable[[], ProvenaUIOnlyConfig]
BootstrapConfigType = Callable[[], GithubBootstrapConfig]

def load_provena_config_from_file(path: str) -> ProvenaConfig:
    return ProvenaConfig.parse_file(path)

def substitute_env_vars(input_string: str) -> str:
    """
    Perform bash-style variable substitution on the input string.

    The function replaces patterns like ${VARIABLE_NAME} with the corresponding
    environment variable value. It also supports default values using the syntax
    ${VARIABLE_NAME:-default_value}.

    Args:
        input_string (str): The input string containing variables to be substituted.

    Returns:
        str: The input string with all variables substituted.

    Example:
        >>> os.environ['NAME'] = 'John'
        >>> substitute_env_vars('Hello, ${NAME}!')
        'Hello, John!'
        >>> substitute_env_vars('Age: ${AGE:-30}')
        'Age: 30'
    """
    def replace_var(match: re.Match[str]) -> str:
        var_name, default_value = match.group(1), None
        if ':-' in var_name:
            var_name, default_value = var_name.split(':-', 1)
        
        value = os.environ.get(var_name) or os.environ.get(var_name.upper())
        
        if value is None:
            if default_value is not None:
                return default_value
            else:
                print(f"Warning: Environment variable '{var_name}' not found and no default provided.")
                return match.group(0)  # Return the original ${VARIABLE_NAME} unchanged
        
        return value

    pattern = r'\$\{([^}]+)\}'
    return re.sub(pattern, replace_var, input_string)


def get_app_config(config_id: str) -> AppConfigType:
    def func() -> ProvenaConfig:
        # load config file
        file_name = f"{CONFIGS_FILE_PREFIX}/{config_id}.json"
        try:
            with open(file_name, 'r') as f:
                content = f.read()
        except Exception:
            prev = file_name
            file_name = f"{CONFIGS_FILE_PREFIX}/{config_id.upper()}.json"
            print(f"Couldn't find {prev} trying {file_name}")
            with open(file_name, 'r') as f:
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
            with open(file_name, 'r') as f:
                content = f.read()
        except Exception:
            prev = file_name
            file_name = f"{CONFIGS_FILE_PREFIX}/{config_id.upper()}-ui.json"
            print(f"Couldn't find {prev} trying {file_name}")
            with open(file_name, 'r') as f:
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
            with open(file_name, 'r') as f:
                content = f.read()
        except Exception:
            prev = file_name
            file_name = f"{CONFIGS_FILE_PREFIX}/{config_id.upper()}-github.json"
            print(f"Couldn't find {prev} trying {file_name}")
            with open(file_name, 'r') as f:
                content = f.read()
    
        # perform variable replacement
        replaced = substitute_env_vars(content)
        # parse as model
        return GithubBootstrapConfig.parse_raw(replaced)
    return func