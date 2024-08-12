from provena.config.config_class import (
    ProvenaConfig,
    ProvenaUIOnlyConfig,
    GithubBootstrapConfig,
)
import re
import os
from typing import Callable, Optional, Dict

CONFIGS_FILE_PREFIX = "configs"

AppConfigType = Callable[[], ProvenaConfig]
UIConfigType = Callable[[], ProvenaUIOnlyConfig]
BootstrapConfigType = Callable[[], GithubBootstrapConfig]

# Global variable for the self-reference marker
SELF_REFERENCE_MARKER = "!!"


def substitute_env_vars(
    input_string: str, replacements: Optional[Dict[str, str]] = None
) -> str:
    """
    Perform case-insensitive, bash-style variable substitution on the input string with extended functionality.

    The function supports the following patterns (in order of precedence):
    1. "${VARIABLE_NAME?true_value||false_value}" - Quoted conditional substitution with else value
    2. "${VARIABLE_NAME?true_value}" - Quoted conditional substitution without else value
    3. ${VARIABLE_NAME?true_value||false_value} - Unquoted conditional substitution with else value
    4. ${VARIABLE_NAME?true_value} - Unquoted conditional substitution without else value
    5. ${VARIABLE_NAME:-default_value} - Substitution with default value
    6. ${VARIABLE_NAME} - Basic substitution

    Args:
        input_string (str): The input string containing variables to be substituted.
        replacements (Optional[Dict[str, str]]): An optional dictionary of replacement keys -> values
            to be used if the environment variable isn't available.

    Returns:
        str: The input string with all variables substituted.
    """

    def get_replacement(var_name: str) -> Optional[str]:
        """Get environment variable value case-insensitively."""
        for key, value in os.environ.items():
            if key.lower() == var_name.lower():
                return value
        if replacements:
            for key, value in replacements.items():
                if key.lower() == var_name.lower():
                    return value
        return None

    def is_truthy(value: Optional[str]) -> bool:
        """Determine if a value is truthy."""
        return value is not None and value.lower() != "false"

    def replace_quotes(s: str) -> str:
        """Replace single quotes with double quotes, except for 'null'."""
        return "null" if s.strip() == "null" else s.replace("'", '"')

    def basic_substitution(match: re.Match) -> str:
        var_name = match.group(1)
        value = get_replacement(var_name)
        if value is None:
            print(f"Warning: Variable '{var_name}' not found and no default provided.")
            return match.group(0)  # Return the original ${VARIABLE_NAME} unchanged
        return replace_quotes(value)

    def default_value_substitution(match: re.Match) -> str:
        var_name, default_value = match.group(1, 2)
        value = get_replacement(var_name) or default_value
        return replace_quotes(value)

    def conditional_substitution(match: re.Match) -> str:
        var_name, true_value = match.group(1, 2)
        false_value = match.group(3) if match.lastindex == 3 else ""
        var_value = get_replacement(var_name)
        result = true_value if is_truthy(var_value) else false_value
        result = result.replace(
            SELF_REFERENCE_MARKER, str(var_value) if var_value is not None else ""
        )
        return replace_quotes(result)

    # Define regex patterns for each substitution type

    # e.g. "${VAR?'!!'||null}"
    quoted_conditional_pattern = r'"\$\{([^:?}]+)\?([^}|]+)(?:\|\|([^}]+))?\}"'
    # e.g. ${VAR?!!||null}
    unquoted_conditional_pattern = r"\$\{([^:?}]+)\?([^}|]+)(?:\|\|([^}]+))?\}"
    # e.g. ${VAR:-default value}
    default_value_pattern = r"\$\{([^:?}]+):-([^}]+)\}"
    # e.g. ${VAR}
    basic_pattern = r"\$\{([^:?}]+)\}"

    # Apply substitutions in order of complexity
    input_string = re.sub(
        quoted_conditional_pattern, conditional_substitution, input_string
    )
    input_string = re.sub(
        unquoted_conditional_pattern, conditional_substitution, input_string
    )
    input_string = re.sub(
        default_value_pattern, default_value_substitution, input_string
    )
    input_string = re.sub(basic_pattern, basic_substitution, input_string)

    return input_string


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
        replaced = substitute_env_vars(content)
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
        replaced = substitute_env_vars(content)
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
        replaced = substitute_env_vars(content)
        # parse as model
        return GithubBootstrapConfig.parse_raw(replaced)

    return func
