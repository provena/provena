import typer
from ToolingEnvironmentManager.Management import EnvironmentManager, process_params
from ProvenaInterfaces.SharedTypes import StatusResponse
from helpers.utils import yes_or_no
from rich import print
from rich.console import Console
from helpers.auth_helpers import setup_auth
import requests
from typing import List

# Typer CLI typing hint for parameters
ParametersType = List[str]

# Establish env manager
env_manager = EnvironmentManager(environment_file_path="../environments.json")
valid_env_str = env_manager.environment_help_string

# disabled to prevent entire json input content from being
# output resulting in error messages being lost in terminal.
app = typer.Typer(pretty_exceptions_show_locals=False)


@app.command()
def clear_graph(
    env_name: str = typer.Argument(
        ...,
        help=f"The tooling environment to target. Options: {valid_env_str}."
    ),
    token_refresh: bool = typer.Option(
        False,
        help="Force a token refresh, invalidating cached tokens. Can be used if you have updated" +
        " your token permissions and don't want to use an out-dated access token."
    ),
    force: bool = typer.Option(
        False,
        help=f"Dismiss all warnings and run graph clear - used for headless operation. Caution..."
    ),
    param: ParametersType = typer.Option(
        [], help=f"List of tooling environment parameter replacements in the format 'id:value' e.g. 'feature_num:1234'. Specify multiple times if required.")
) -> None:
    """
    Given the stage, will run the graph admin only clear graph command which
    wipes the neo4j db backing the prov API lineage capabilities. WARNING: this
    will delete everything from the neo4j graph for the given provenance
    endpoint! Proceed with caution...
    """

    # Process optional environment replacement parameters
    params = process_params(param)
    env = env_manager.get_environment(name=env_name, params=params)

    # Warning
    if not force:
        console = Console()
        console.print(
            f"WARNING running this operation will delete all items from the neo4j graph DB backing the provenance API! Proceed with caution. API being targeted: {env.prov_api_endpoint}.",
            style="red on white"
        )
        y_n_response = yes_or_no("Are you sure you want to proceed?")

        if not y_n_response:
            print("Aborting!")
            exit(1)

    # Setup auth
    auth = setup_auth(
        stage=env.stage,
        keycloak_endpoint=env.keycloak_endpoint,
        token_refresh=token_refresh
    )

    # make API call
    postfix = "/graph/admin/clear"
    endpoint = env.prov_api_endpoint + postfix
    response = requests.delete(endpoint, auth=auth())

    if response.status_code != 200:
        try:
            details = response.json()['detail']
        except:
            details = "Could not unpack payload."

        print(
            f"Non 200 status code! Code: {response.status_code}. Details: {details}.")
    else:
        try:
            status_response = StatusResponse.parse_obj(response.json())
        except Exception as e:
            print(
                f"200 OK but failed to parse StatusResponse, unsure of outcome of clear operation... Exception: {e}.")

        if not status_response.status.success:
            print(
                f"200 OK but status failure, details: {status_response.status.details}.")

        print(
            f"Successfully cleared graph DB. Details: {status_response.status.details}")


if __name__ == "__main__":
    app()
