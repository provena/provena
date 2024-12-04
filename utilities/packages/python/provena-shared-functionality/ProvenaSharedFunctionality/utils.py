from typing import Optional, Dict, Any
import json
import re
import os
from pydantic import BaseModel

# This allows users to refer to the value of the resolved variable in conditional statements e.g.
# "${VALUE?'!!_postfix'||null}"
SELF_REFERENCE_MARKER = "!!"


def py_to_dict(item: BaseModel) -> Dict[str, Any]:
    """
    Safely converts a pydantic model into a Python JSON dictionary type

    Parameters
    ----------
    item : BaseModel
        The item which is a pydantic model

    Returns
    -------
    Dict[str, Any]
        The output dictionary
    """
    return json.loads(item.json(exclude_none=True))


def perform_config_substitution(
    input_string: str, replacements: Optional[Dict[str, str]] = None
) -> str:
    """
    Perform case-insensitive, bash-style variable substitution on the input string with extended functionality.

    Note that in all cases, any single quotes ' will be replaced with double quotes in the output ".

    Please also note the special case of a conditional statement immediately surrounded by quotes. 
    In this case the double quotes are stripped. But you can reintroduce by using single quotes. This 
    allows the following style  "${VALUE?'!!'||null}" which remains valid in the JSON document.

    The function supports the following patterns (in order of precedence):
    1. "${VARIABLE_NAME?true_value||false_value}" - Quoted conditional substitution with else value
    2. "${VARIABLE_NAME?true_value}" - Quoted conditional substitution without else value
    3. ${VARIABLE_NAME?true_value||false_value} - Unquoted conditional substitution with else value
    4. ${VARIABLE_NAME?true_value} - Unquoted conditional substitution without else value
    5. ${VARIABLE_NAME:-default_value} - Substitution with default value
    6. ${VARIABLE_NAME} - Basic substitution

    Args:
        input_string (str): The input string of a config file containing variables to be substituted.
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
        """Replace single quotes with double quotes."""
        return s.replace("'", '"')

    def basic_substitution(match: re.Match) -> str:
        var_name = match.group(1)
        value = get_replacement(var_name)
        if value is None:
            print(
                f"Warning: Variable '{var_name}' not found and no default provided.")
            # Return the original ${VARIABLE_NAME} unchanged
            return match.group(0)
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
            SELF_REFERENCE_MARKER, str(
                var_value) if var_value is not None else ""
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
