from config import *
from ProvenaInterfaces.DataStoreAPI import *
from mdsisclienttools.auth.TokenManager import DeviceFlowManager, Stage, BearerAuth  # type: ignore
from ToolingEnvironmentManager.EnvironmentTypes import PopulatedToolingEnvironment
from ToolingEnvironmentManager.Management import EnvironmentManager, process_params
from typing import Optional, Callable
import os
import requests
import typer
from rich import print, console

# Typer CLI typing hint for parameters
ParametersType = List[str]

# Establish env manager
env_manager = EnvironmentManager(environment_file_path="../environments.json")
valid_env_str = env_manager.environment_help_string

app = typer.Typer()


def yes_or_no(query: str) -> bool:
    """    yes_or_no
        helper function to display y/n confirmation.

        Arguments
        ----------
        query : str
            The question to pose

        Returns
        -------
         : bool
        Returns true iff valid input of y/yes. 
        Returns false iff valid input of n/no. 


        See Also (optional)
        --------

        Examples (optional)
        --------
    """
    valid_response = False
    response: Optional[bool] = None
    valid_responses = ["N", "Y", "YES", "NO"]

    while not valid_response:
        possible_response = input(
            query + " [Y/N]\n")
        filtered_response = possible_response.upper().strip()
        if filtered_response in valid_responses:
            valid_response = True
            if filtered_response in ["YES", "Y"]:
                response = True
            else:
                response = False
        else:
            print(
                f"Invalid response. Please enter one of {valid_responses}")
    assert response is not None
    return response


def make_config_request(
    endpoint: str,
    required_only: bool,
    auth: Callable[[], BearerAuth]
) -> bytes:
    """
    make_config_request

    Makes the config request and returns the bytes content.

    Parameters
    ----------
    endpoint : str
        The full config endpoint
    required_only : bool
        Required only argument
    auth : Callable[[], BearerAuth]
        Auth generator function

    Returns
    -------
    bytes
        The bytes content of the env file
    """
    # make request to endpoint
    print(f"Making config request to {endpoint}.")

    params = {
        REQUIRED_PARAM: required_only
    }
    response = requests.get(endpoint, params=params, auth=auth())

    # check the status code
    assert response.status_code == 200, f"Received response code: {response.status_code}!"

    # check the content type
    expected_content_type = "text/plain; charset=utf-8"
    content_type = response.headers.get('content-type')
    assert content_type == expected_content_type, f"Expected content-type header {expected_content_type} but got {content_type}."
    return response.content


def get_api_endpoint(api: API_NAME, env: PopulatedToolingEnvironment) -> str:
    if api == API_NAME.auth_api:
        return env.auth_api_endpoint

    if api == API_NAME.data_store_api:
        return env.datastore_api_endpoint

    if api == API_NAME.prov_api:
        return env.prov_api_endpoint

    if api == API_NAME.registry_api:
        return env.registry_api_endpoint

    if api == API_NAME.search_api:
        return env.search_api_endpoint

    if api == API_NAME.identity_api:
        return env.handle_service_api_endpoint

    if api == API_NAME.job_api:
        return env.jobs_service_api_endpoint

    raise ValueError(f"No API target for {api}")


def setup_environment(
    env: PopulatedToolingEnvironment,
    api_name: str,
    required_only: bool,
    auth: Callable[[], BearerAuth],
    return_to_base_dir: str,
    desired_file_name: str,
    suppress_warnings: bool,
    added_prefix: str = "",
) -> None:
    """
    setup_environment 

    Runs the config endpoint for a given API - assumes you are starting in the
    top level provena working directory.

    Parameters
    ----------
    stage : str
        The deployment stage
    api_name : str
        The name of the api - see config
    required_only : bool
        The required only query argument to the config endpoint
    auth : Callable[[], BearerAuth]
        Auth manager auth generator
    return_to_base_dir : str
        The directory to return to when complete
    desired_file_name : str
        The desired file name to write to
    suppress_warnings : bool
        Should warnings be suppressed

    Returns
    -------
    None
    """
    working_directory = API_LOCATIONS_MAP[api_name]
    print(f"Setting up api environment for {api_name}, at {working_directory}")

    os.chdir(working_directory)

    # work here
    # get the environment file from the API
    base_endpoint = get_api_endpoint(api=API_NAME_MAP[api_name], env=env)
    endpoint = base_endpoint + CONFIG_ENDPOINT_POSTFIX

    content = make_config_request(
        endpoint=endpoint,
        required_only=required_only,
        auth=auth
    )

    # write the content to file with correct name

    # does the file exist already?

    # only ask if we are not suppressing warnings
    if not suppress_warnings:
        if os.path.exists(desired_file_name):
            overwrite = yes_or_no(
                f"There is already an environment file with name: {desired_file_name}, did you want to overwrite it?")
            if not overwrite:
                move_on = yes_or_no(
                    "Do you want to move on to the next API. Y to move on, N to exit application.")
                if not move_on:
                    print("Aborting!")
                    exit(1)

    # file may or may not exist, but we are ovewriting it anyway
    print(f"Writing to {desired_file_name}.")
    with open(desired_file_name, 'wb') as f:
        f.write(content)
    print(f"Complete for {api_name}.")

    # return back to base
    os.chdir(return_to_base_dir)

    return None


@app.command()
def bootstrap_stage(
    target_env: str = typer.Argument(
        ...,
        help=f"The tooling environment to target. Options: {valid_env_str}."
    ),
    token_refresh: bool = typer.Option(
        False,
        help="Force refresh of tokens, invalidating cached tokens. Can be used if you need to refresh your access permissions."),
    required_only: bool = typer.Option(
        False,
        help="Should only required properties of the config be included?"),
    env_name: str = typer.Option(
        ".env",
        help="Optionally specify the name of the generated environment file."),
    suppress_warnings: bool = typer.Option(
        False,
        help="Optionally suppress all warnings to proceed in a headless environment."),
    param: ParametersType = typer.Option(
        [], help=f"List of tooling environment parameter replacements in the format 'id:value' e.g. 'feature_number:1234'. Specify multiple times if required.")
) -> None:
    """
    bootstrap_stage 

    Pulls and writes .env config files for all APIs for the given stage.
    """
    # Process optional environment replacement parameters
    params = process_params(param)
    env = env_manager.get_environment(name=target_env, params=params)

    # Login and setup auth manager
    device_auth = DeviceFlowManager(
        stage=env.stage,
        keycloak_endpoint=env.keycloak_endpoint,
        local_storage_location=".tokens.json",
        force_token_refresh=token_refresh
    )

    # Callable to embed into requests auth
    get_auth = device_auth.get_auth

    # setup cwd
    starting_cwd = os.getcwd()

    # TODO PROVENA UPDATE
    expected_cwd_postfix = "provena/admin-tooling/environment-bootstrapper"
    assert starting_cwd.endswith(
        expected_cwd_postfix), f"Working directory is unexpected, you may need to edit the script, cwd {starting_cwd}, expected ending in {expected_cwd_postfix}."
    os.chdir(RELATIVE_TO_HOME)
    base_working_dir = os.getcwd()
    # TODO PROVENA UPDATE
    assert base_working_dir.endswith(
        "provena"), f"After changing directories with relative path {RELATIVE_TO_HOME}, failed to end in provena base path as expected..."

    # Setup each environment
    for api_name in API_LOCATIONS_MAP.keys():
        setup_environment(
            env=env,
            api_name=api_name,
            required_only=required_only,
            auth=get_auth,
            return_to_base_dir=base_working_dir,
            desired_file_name=env_name,
            suppress_warnings=suppress_warnings
        )
        print()

        # check we are back to base!
        assert os.getcwd().endswith(
            "provena"), f"After changing directories, failed to end in provena base path as expected..."
    # return back to original wd
    os.chdir(starting_cwd)

# DEPRECATED for now
# @app.command()
# def bootstrap_all(
#    exclude_stage: Optional[List[Stage]] = typer.Option(
#        None,
#        help="A list of stages to exclude from the repo bootstrap. You can specify this argument multiple times."),
#    token_refresh: bool = typer.Option(
#        False,
#        help="Force refresh of tokens, invalidating cached tokens. Can be used if you need to refresh your access permissions."),
#    required_only: bool = typer.Option(
#        False,
#        help="Should only required properties of the config be included?"),
#    suppress_warnings: bool = typer.Option(
#        False,
#        help="Optionally suppress all warnings to proceed in a headless environment."),
# ) -> None:
#    """
#    bootstrap_all
#
#    Pulls and writes config .env files for all stages and all APIs. You can
#    exclude stages using the --exclude-stages option. The environment files will
#    have names env.test, env.dev, env.stage and env.prod.
#    """
#    for stage in Stage:
#        if exclude_stage and stage in exclude_stage:
#            print(f"Skipping stage: {stage}!")
#            print()
#        else:
#            env_file_name = STAGE_ENV_FILE_NAME_MAP[stage.value]
#            bootstrap_stage(
#                stage=stage,
#                token_refresh=token_refresh,
#                required_only=required_only,
#                env_name=env_file_name,
#                suppress_warnings=suppress_warnings
#            )


@app.command()
def fetch_api_config(
    target_env: str = typer.Argument(
        ...,
        help=f"The tooling environment to target. Options: {valid_env_str}."
    ),
    api_name: API_NAME = typer.Argument(
        ...,
        help="Which API to fetch config for."),
    output_file: Optional[str] = typer.Option(
        None,
        help="Write the output to a local file - specify file name."),
    token_refresh: bool = typer.Option(
        False,
        help="Force refresh of tokens, invalidating cached tokens. Can be used if you need to refresh your access permissions."),
    required_only: bool = typer.Option(
        False,
        help="Should only required properties of the config be included?"),
    param: ParametersType = typer.Option(
        [], help=f"List of tooling environment parameter replacements in the format 'id:value' e.g. 'feature_num:1234'. Specify multiple times if required.")
) -> None:
    """
    fetch_api_config

    Fetches the api config for a particular stage and API. Optionally writes it
    to file if output-file is provided.
    """

    # Process optional environment replacement parameters
    params = process_params(param)
    env = env_manager.get_environment(name=target_env, params=params)

    # Login and setup auth manager
    device_auth = DeviceFlowManager(
        stage=env.stage,
        keycloak_endpoint=env.keycloak_endpoint,
        local_storage_location=".tokens.json",
        force_token_refresh=token_refresh
    )

    # Callable to embed into requests auth
    get_auth = device_auth.get_auth

    # get the environment file from the API
    endpoint = get_api_endpoint(api=api_name, env=env) + \
        CONFIG_ENDPOINT_POSTFIX

    content = make_config_request(
        endpoint=endpoint,
        required_only=required_only,
        auth=get_auth
    )

    if output_file:
        print(f"Writing to {output_file}.")
        with open(output_file, 'wb') as f:
            f.write(content)
    else:
        print("Displaying returned config")
        print()
        no_colour_console = console.Console(color_system=None)
        no_colour_console.print(content.decode("utf-8"))


if __name__ == "__main__":
    app()
