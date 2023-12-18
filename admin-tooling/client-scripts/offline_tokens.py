import typer
import os
from mdsisclienttools.auth.TokenManager import DeviceFlowManager, AuthFlow  # type: ignore
from ToolingEnvironmentManager.Management import EnvironmentManager, process_params
from rich import print
from typing import List

# Typer CLI typing hint for parameters
ParametersType = List[str]

# Establish env manager
env_manager = EnvironmentManager(environment_file_path="../environments.json")
valid_env_str = env_manager.environment_help_string

# try to avoid leaking creds to CLI output - don't show local vars on exception
app = typer.Typer(pretty_exceptions_show_locals=False)


def write_to_file(token: str, file: typer.FileTextWrite) -> None:
    with file as f:
        f.write(token)


@app.command()
def test_offline_token(
    env_name: str = typer.Argument(
        ...,
        help=f"The tooling environment to target. Options: {valid_env_str}."
    ),
    param: ParametersType = typer.Option(
        [], help=f"List of tooling environment parameter replacements in the format 'id:value' e.g. 'feature_num:1234'. Specify multiple times if required.")
) -> None:
    """ 
    Tests that the provided offline token allows login. Must have an environment
    variable called PROVENA_OFFLINE_TOKEN which contains the valid offline access token.
    """
    # Process optional environment replacement parameters
    params = process_params(param)
    env = env_manager.get_environment(name=env_name, params=params)

    # special keycloak client configured for offline access
    client_id = "automated-access"

    # get the token
    token = os.environ.get("PROVENA_OFFLINE_TOKEN")

    if token is None:
        raise ValueError(
            "There was no PROVENA_OFFLINE_TOKEN environment variable.")

    # remove any unwanted whitespace
    token.strip()

    # get the respective keycloak endpoint for the stage
    keycloak_endpoint = env.keycloak_endpoint

    print("Logging into automated-access client using offline authorisation flow.")

    # initiate a device auth flow
    manager = DeviceFlowManager(
        stage=env.stage,
        keycloak_endpoint=keycloak_endpoint,
        client_id=client_id,
        auth_flow=AuthFlow.OFFLINE,
        offline_token=token,
        force_token_refresh=True
    )

    print("Success!")


@app.command()
def generate_offline_token(
    env_name: str = typer.Argument(
        ...,
        help=f"The tooling environment to target. Options: {valid_env_str}."
    ),
    output_file: typer.FileTextWrite = typer.Argument(
        ...,
        help="The name of the file to output plain text token to - ensure it is stored securely."
    ),
    param: ParametersType = typer.Option(
        [], help=f"List of tooling environment parameter replacements in the format 'id:value' e.g. 'feature_num:1234'. Specify multiple times if required.")
) -> None:
    """ 
    Produces an offline token by completing an OAuth device grant against the
    configured keycloak client and requesting the offline access scope.
    """
    # Process optional environment replacement parameters
    params = process_params(param)
    env = env_manager.get_environment(name=env_name, params=params)

    # grant scope
    scopes = ["offline_access"]

    # special keycloak client configured for offline access
    client_id = "automated-access"

    # get the respective keycloak endpoint for the stage
    keycloak_endpoint = env.keycloak_endpoint

    print("Logging into automated-access client using device authorisation flow.")

    # initiate a device auth flow
    manager = DeviceFlowManager(
        stage=env.stage,
        keycloak_endpoint=keycloak_endpoint,
        client_id=client_id,
        auth_flow=AuthFlow.DEVICE,
        scopes=scopes,
        force_token_refresh=True
    )

    print("Login complete - offline token generated.")

    # if successful, pull out the offline access token (refresh token)
    offline_token = manager.tokens.refresh_token
    assert offline_token

    # write to output file
    write_to_file(
        token=offline_token,
        file=output_file
    )


if __name__ == "__main__":
    app()
