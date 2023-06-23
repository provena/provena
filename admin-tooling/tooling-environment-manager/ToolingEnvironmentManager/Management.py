from typing import List, Dict
from ToolingEnvironmentManager.EnvironmentTypes import *


def process_params(param_list: List[str]) -> Dict[str, str]:
    """

    Takes a list of key:value formatted parameters from the typer CLI context
    and splits them into a {key: value} dictionary

    Args:
        param_list (List[str]): The list of formatted parameters

    Raises:
        ValueError: Inappropriate format detected

    Returns:
        Dict[str, str]: The key value dict
    """
    kvs = {}
    for param in param_list:
        splits = param.split(':')
        if len(splits) != 2:
            raise ValueError(
                f"Invalid parameter {param}. Must be in format k:v.")
        kvs[splits[0]] = splits[1]
    return kvs


class EnvironmentManager():
    """
    Manages a file submitted environment. 

    Exposes a environments list and get environment method. 

    The get environment requires a set of params to perform optional
    replacement.
    """

    def __init__(self, environment_file_path: str) -> None:
        """

        Reads from the specified file to generate the env list. Must satisfy the
        ToolingEnvironmentsFile Pydantic schema.

        Args:
            environment_file_path (str): The file path relative to script location.
        """
        self._environments: Dict[str, ToolingEnvironment] = {
            env.name: env for env in
            ToolingEnvironmentsFile.parse_file(environment_file_path).envs
        }

    def get_environment(self, name: str, params: ReplacementDict) -> PopulatedToolingEnvironment:
        """
        Fetches the environment based on the ToolingEnvironment name and the set
        of parameter replacements.

        Args:
            name (str): The tooling environment "name" field
            params (ReplacementDict): The replacement dictionary - use
            process_params to generate this from CLI args

        Raises:
            ValueError: Throws an error if environment doesn't exist

        Returns:
            PopulatedToolingEnvironment: A populated and validated version of
            the environment ready to use.
        """        
        unpopulated = self._environments.get(name)
        if unpopulated is None:
            raise ValueError(
                f"Specified environment name does not exist: {name = }.")
        populated = PopulatedToolingEnvironment(
            parameters=params, **unpopulated.dict())
        populated.validate_parameters()
        return populated

    @property
    def environments(self) -> List[str]:
        return list(self._environments.keys())

    @property
    def environment_help_string(self) -> List[str]:
        envs = self.environments
        return '"' + '" "'.join(envs) + '"'
