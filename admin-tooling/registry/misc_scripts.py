from SharedInterfaces.RegistryAPI import *
import typer
from ToolingEnvironmentManager.Management import EnvironmentManager, process_params
from KeycloakRestUtilities.TokenManager import DeviceFlowManager
from helpers.summary_helpers import *

# Typer CLI typing hint for parameters
ParametersType = List[str]

# Establish env manager
env_manager = EnvironmentManager(environment_file_path="../environments.json")
valid_env_str = env_manager.environment_help_string

app = typer.Typer(pretty_exceptions_show_locals=False)
SAVE_DIRECTORY = "dumps"

@app.command()
def dataset_link_audit(
    env_name: str = typer.Argument(
        ...,
        help=f"The tooling environment to target for clear and initialisation. If targeting a feature deployment, then this is used for the keycloak instance. One of: {valid_env_str}.",
    ),
    output: typer.FileTextWrite = typer.Option(
        f"{SAVE_DIRECTORY}/stats_" + str(datetime.now()) + ".txt",
        help=f"The name of the file to save summary statistics to.",
        prompt="Provide the name of the summary statistics file - include the file extension .txt . \nEnter to use default -->",
    ),
    token_refresh: bool = typer.Option(
        False,
        help="Force a token refresh, invalidating cached tokens. Can be used if you have updated" +
        " your token permissions and don't want to use an out-dated access token."
    ),
    param: ParametersType = typer.Option(
        [], help=f"List of tooling environment parameter replacements in the format 'id:value' e.g. 'feature_num:1234'. Specify multiple times if required.")
) -> None:
    """
    Lists all datasets, and then checks if the registered owner username is linked. 

    Produces an output audit with this information as well as other summary statistics.

    Uses the admin link user service so authorised user must have auth api admin permission.
    """

    # Process optional environment replacement parameters
    params = process_params(param)
    env = env_manager.get_environment(name=env_name, params=params)

    # Login and setup auth manager
    device_auth = DeviceFlowManager(
        stage=env.stage,
        keycloak_endpoint=env.keycloak_endpoint,
        local_storage_location=".tokens.json",
        token_refresh=token_refresh
    )

    # Callable to embed into requests auth
    get_auth = device_auth.get_auth

    perform_dataset_link_audit(
        env=env,
        output=output,
        get_auth=get_auth
    )