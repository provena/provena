import typer
from config import AWSConfig
from KeycloakRestUtilities.TokenManager import DeviceFlowManager, BearerAuth
from helpers.type_aliases import GetAuthFunction
from rich import print
from typing import Optional
from helpers.report_helpers import *
from helpers.registry_helpers import *
from helpers.auth_helpers import *
from helpers.time_helpers import RECOMMENDED_TIMEZONES, validate_timezone
from ToolingEnvironmentManager.Management import EnvironmentManager, process_params

# Typer CLI typing hint for parameters
ParametersType = List[str]

# Establish env manager
env_manager = EnvironmentManager(environment_file_path="../environments.json")
valid_env_str = env_manager.environment_help_string

# disabled to prevent entire json input content from being
# output resulting in error messages being lost in terminal.
app = typer.Typer(pretty_exceptions_show_locals=False)


def setup_auth(stage: str, keycloak_endpoint: str, token_refresh: bool) -> GetAuthFunction:
    # Login and setup auth manager
    device_auth = DeviceFlowManager(
        stage=stage,
        keycloak_endpoint=keycloak_endpoint,
        local_storage_location=".tokens.json",
        token_refresh=token_refresh
    )

    # Callable to embed into requests auth
    return device_auth.get_auth


@app.command()
def generate_export_local(
    report_type: ReportType = typer.Argument(
        ...,
        help=f"The report type to generate."
    ),
    output_path: typer.FileTextWrite = typer.Argument(
        ...,
        help=f"The filename to write the CSV to."
    ),
    env_name: str = typer.Argument(
        ...,
        help=f"The tooling environment to target. Options: {valid_env_str}."
    ),
    token_refresh: bool = typer.Option(
        False,
        help="Force a token refresh, invalidating cached tokens. Can be used if you have updated" +
        " your token permissions and don't want to use an out-dated access token."
    ),
    timezone: str = typer.Option(
        'Australia/Sydney',
        help=f"The timezone to use formatted as Country/City. I.e. [{', '.join(RECOMMENDED_TIMEZONES)}].",
        show_default=True,
    ),
    param: ParametersType = typer.Option(
        [], help=f"List of tooling environment parameter replacements in the format 'id:value' e.g. 'feature_num:1234'. Specify multiple times if required.")
) -> None:
    """
    Generates a CSV report of the specified type by listing all model runs and
    transforming according to report format.

    Local run mode.
    """

    # Process optional environment replacement parameters
    params = process_params(param)
    env = env_manager.get_environment(name=env_name, params=params)

    validate_timezone(timezone)

    auth: GetAuthFunction = setup_auth(
        stage=env.stage,
        keycloak_endpoint=env.keycloak_endpoint,
        token_refresh=token_refresh
    )

    # basic workflow

    # list all the model run records
    print("Retrieving all model run records from the registry.")
    all_model_run_records = list_model_run_records_from_registry(
        auth=auth,
        registry_endpoint=env.registry_api_endpoint
    )
    print("Completed retrieving list.")
    print()

    # generate report based on report type
    print(f"Generating CSV report from entries - type: {report_type}.")
    endpoint = env.registry_api_endpoint
    endpoint_context = EndpointContext(endpoint=endpoint, auth=auth)
    csv_result = dispatch_report_generator(
        model_runs=all_model_run_records, report_type=report_type, endpoint_context=endpoint_context, timezone=timezone)
    print("Done.")
    print()

    # write to a CSV
    print(f"Writing report to {output_path.name}.")
    write_csv_report(csv_report=csv_result, output_file=output_path)
    print("Finished.")


@app.command()
def generate_export_aws(
    report_type: ReportType = typer.Argument(
        ...,
        help=f"The report type to generate."
    ),
    output_path: typer.FileTextWrite = typer.Argument(
        ...,
        help=f"The filename to write the CSV to."
    ),
    timezone: str = typer.Option(
        'Australia/Sydney',
        help=f"The timezone to use formatted as Country/City. I.e. [{', '.join(RECOMMENDED_TIMEZONES)}].",
        show_default=True
    )
) -> None:
    """
    Generates a CSV report of the specified type by listing all model runs and
    transforming according to report format.

    This is used by the AWS scheduled job - it requires usage of a service
    account.
    """
    validate_timezone(timezone)

    # parse the config object (from env)
    config = AWSConfig()

    # Process optional environment replacement parameters
    env = env_manager.get_environment(name=config.stage, params={})

    # get service account token
    token = get_client_credential_token(
        client_id=config.service_account_client_id,
        client_secret=config.service_account_client_secret,
        token_endpoint=env.keycloak_endpoint +
        "/protocol/openid-connect/token",
        grant_type="client_credentials"
    )

    # wrap in auth function
    def auth() -> BearerAuth: return BearerAuth(token)

    # pull out stage
    stage = config.stage

    # basic workflow

    # list all the model run records
    print("Retrieving all model run records from the registry.")
    all_model_run_records = list_model_run_records_from_registry(
        auth=auth,
        registry_endpoint=env.registry_api_endpoint
    )
    print("Completed retrieving list.")
    print()

    # generate report based on report type
    print(f"Generating CSV report from entries - type: {report_type}.")
    endpoint = env.registry_api_endpoint
    endpoint_context = EndpointContext(endpoint=endpoint, auth=auth)
    csv_result = dispatch_report_generator(
        model_runs=all_model_run_records, report_type=report_type, endpoint_context=endpoint_context, timezone=timezone)
    print("Done.")
    print()

    # write to a CSV
    print(f"Writing report to {output_path.name}.")
    write_csv_report(csv_report=csv_result, output_file=output_path)
    print("Finished.")


if __name__ == "__main__":
    app()
