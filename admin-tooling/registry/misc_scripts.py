from ProvenaInterfaces.RegistryAPI import *
import typer
from ToolingEnvironmentManager.Management import EnvironmentManager, process_params
from KeycloakRestUtilities.TokenManager import DeviceFlowManager
from helpers.summary_helpers import *
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.console import Console
from typing import Any, Optional
# types: ignore
import boto3

console = Console()


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


def delete_items(table: Any) -> None:
    #get the table keys
    tableKeyNames = [key.get("AttributeName") for key in table.key_schema]

    #Only retrieve the keys for each item in the table (minimize data transfer)
    projectionExpression = ", ".join('#' + key for key in tableKeyNames)
    expressionAttrNames = {'#'+key: key for key in tableKeyNames}
    
    counter = 0
    page = table.scan(ProjectionExpression=projectionExpression, ExpressionAttributeNames=expressionAttrNames)
    with table.batch_writer() as batch:
        while page["Count"] > 0:
            counter += page["Count"]
            # Delete items in batches
            for itemKeys in page["Items"]:
                batch.delete_item(Key=itemKeys)
            # Fetch the next page
            if 'LastEvaluatedKey' in page:
                page = table.scan(
                    ProjectionExpression=projectionExpression, ExpressionAttributeNames=expressionAttrNames,
                    ExclusiveStartKey=page['LastEvaluatedKey'])
            else:
                break
    print(f"Deleted {counter}")


@app.command()
def delete_all(
    table_name: str = typer.Argument(..., help="Name of the DynamoDB table"),
    region: str = typer.Option("ap-southeast-2", help="AWS region"),
    confirm: bool = typer.Option(
        True, help="Prompt for confirmation before deleting")
) -> None:
    """
    Delete all items from a DynamoDB table.
    """
    try:
        # Set up AWS session
        session = boto3.Session()
        dynamodb = session.resource('dynamodb', region_name=region)
        table = dynamodb.Table(table_name)

        # Get item count (approximate)
        item_count = table.item_count

        if item_count == 0:
            console.print(
                f"[yellow]Table '{table_name}' is already empty.[/yellow]")
            raise typer.Exit()

        # Confirm deletion
        if confirm:
            typer.confirm(
                f"Are you sure you want to delete approximately {item_count} items from '{table_name}'?",
                abort=True
            )

        delete_items(table)

    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        raise typer.Exit(1)
