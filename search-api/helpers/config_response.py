from fastapi.responses import FileResponse
from fastapi import APIRouter, Depends
from starlette.background import BackgroundTask
from typing import Any, Tuple, Dict, Type, List
import random
import os
from config import Config, get_settings
import json
from dependencies.dependencies import sys_admin_admin_user_protected_role_dependency
from KeycloakFastAPI.Dependencies import User


def delete_file(filename: str) -> None:
    """
    delete_file

    Given a file name, will delete it from the current working
    directory. Used to cleanup after API file delivery.

    Parameters
    ----------
    filename : str
        The name of the file including file extension
    """
    os.remove(filename)


def generate_random_file(config : Config) -> Tuple[str, Any]:
    """
    generate_random_file 

    Generates a temp file to be used for file delivery. Tempfile library seemed
    buggy so we are implementing basic version. This is not mission critical
    functionality.

    Returns
    -------
    Tuple[str, Any]
        The name of the file, and the file itself
    """
    random_name = f"{config.TEMP_FILE_LOCATION}/config_temp{str(random.randint(1,100000))}.txt"
    f = open(random_name, 'w')
    return random_name, f


def generate_safe_json_payload(config: Config, required_only: bool) -> Dict[str, Any]:
    unfiltered = json.loads(config.json(exclude_none=True, indent=2))
    if required_only:
        req_fields = find_required_fields(Config)
        filtered: Dict[str, Any] = {}
        for k, v in unfiltered.items():
            if k in req_fields:
                filtered[k] = v
        return filtered
    else:
        return unfiltered


def find_required_fields(config_model: Type[Config]) -> List[str]:
    """
    find_required_fields
    
    Filters the config model to supply only keys which are required.

    Parameters
    ----------
    config_model : Type[Config]
        The config Type (not an instance)

    Returns
    -------
    List[str]
        The list of keys
    """
    key_list: List[str] = []
    for name, field in config_model.__fields__.items():
        if field.required:
            key_list.append(name)
    return key_list


def convert_json_to_env(safe_json: Dict[str, Any]) -> str:
    """
    convert_json_to_env 
    
    Returns the env formatted version of the simple k,v safe json object

    Parameters
    ----------
    safe_json : Dict[str, Any]
        The safe json object produced by the generate config route method.  

    Returns
    -------
    str
        The string ready to produce the config env file
    """
    return '\n'.join([f"{key}={value}" for key, value in safe_json.items()])


def generate_config_route(router: APIRouter, route_path: str) -> None:
    """
    generate_config_route
    
    Adds a config generator route which returns a config.txt file as an
    attachment at the specified route path.

    Parameters
    ----------
    router : APIRouter
        The fast API router to attach method to
    route_path : str
        The route path to use

    Returns
    -------
    """
    @router.get(route_path, operation_id="generate_config_file")
    async def generate_config_file(
        required_only: bool = True,
        config: Config = Depends(get_settings),
        user: User = Depends(sys_admin_admin_user_protected_role_dependency)
    ) -> FileResponse:
        """
        generate_config_file 

        Generates a nicely formatted .env file of the current required/non
        supplied properties of the Config pydantic model. Used to quickly
        bootstrap a local environment or to understand currently deployed API.

        Parameters
        ----------
        config : Config, optional
            The configuration injected by dep, by default Depends(get_settings)

        Returns
        -------
        FileResponse
            Returns a .env file
        """
        # Create temporary config file
        name, file = generate_random_file(config)

        # Write content to the temp file
        file.write(convert_json_to_env(generate_safe_json_payload(
            config = config, 
            required_only = required_only
            )))
        file.close()

        return FileResponse(
            path=file.name,
            filename="config.txt",
            background=BackgroundTask(delete_file, name)
        )
