from ProvenaInterfaces.RegistryAPI import *
import typer
from ToolingEnvironmentManager.Management import EnvironmentManager, process_params
from KeycloakRestUtilities.TokenManager import DeviceFlowManager
from helpers.summary_helpers import *
import json
from typing import Any, List

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
    
@app.command()
def valid_prov_records(
    file_name: str = typer.Argument(
        ...,
        help="The name of the file to process. This should be a json file containing a registry export."
    ),
    output: str = typer.Option(
        f"{SAVE_DIRECTORY}/valid_prov_" + str(datetime.now()) + ".json",
        help=f"The name of the file to save valid provenance items to.",
    ),
    save_invalids: str = typer.Option(
        f"{SAVE_DIRECTORY}/invalid_prov_" + str(datetime.now()) + ".json",
        help=f"For inspection, the name of the file to save invalid provenance items to.",
    )
) -> None:
    """
    Given a registry export, this command removes entities with invalid
    provenance that will result in failures if supplied to the admin/restore-prov-graph.
    Will not remove failures because of a missing or broken user-person link, but will remove items that
    1) are owned by the integration-test-read-write-bot.
    2) are create activities that have no created item existing in the payload.
    3) are version activities that have no versioned item existing in the payload.
    Invalid creates and versions can occur from integration tests that fail to clean up after themselves.
    Always check the invalid_prov.json to make sure what is being removed is indeed junk.
    The valid_prov.json can be used to restore the provenance graph as is.
    
    """
    with open(file_name, "r") as f:
        data = json.load(f)
        
    all_ids = set([item["id"] for item in data])
    final_data: List[Any] = []
    deleting: List[Any] = []

    for item in data:
        keep=True
        if item['item_payload']["item_subtype"] == "CREATE":
            # is a create activity... 
            # make sure its created thing exists (hasn't been deleted) otherwise, provenance recreation will fail
            created_id = item['item_payload']["created_item_id"]
            if created_id not in all_ids:
                keep=False
            
        if item['item_payload']["item_subtype"] == "VERSION":
            # is a version activity... 
            # make sure its versioned thing exists (hasn't been deleted) otherwise, provenance recreation will fail
            to_item_id = item['item_payload']["to_item_id"]
            if to_item_id not in all_ids:
                keep=False
        
        if item['item_payload']["owner_username"] == "integration-test-read-write-bot":
            # skip the bot user's items 
            # because the bot is not linked to an entity, and so provenance re-creation for its items will fail
            # they exist because the integration tests currently fail to clean up create/versions items 100%.
            keep=False
        
        if keep:
            final_data.append(item)
        else:
            deleting.append(item)
    
    with open(output, "w") as f:
        json.dump(final_data, f, indent=2)
        
    with open(save_invalids, "w") as f:
        json.dump(deleting, f, indent=2)


if __name__ == "__main__":
    app()
