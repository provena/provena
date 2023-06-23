import typer
from config import VALIDATE_BY_DEFAULT
from KeycloakRestUtilities.TokenManager import DeviceFlowManager, Stage
from ToolingEnvironmentManager.Management import EnvironmentManager, process_params
from SharedInterfaces.ProvenanceAPI import *
from SharedInterfaces.RegistryAPI import *
from helpers.prov_helpers import relodge_model_run_record
from helpers.registry_helpers import get_model_run_by_handle, list_model_run_records_from_registry
from helpers.utils import yes_or_no
from helpers.type_aliases import GetAuthFunction
from helpers.auth_helpers import setup_auth
from rich import print
from typing import Set
import json

# Typer CLI typing hint for parameters
ParametersType = List[str]

# Establish env manager
env_manager = EnvironmentManager(environment_file_path="../environments.json")
valid_env_str = env_manager.environment_help_string

# disabled to prevent entire json input content from being
# output resulting in error messages being lost in terminal.
app = typer.Typer(pretty_exceptions_show_locals=False)


@app.command()
def restore_model_run_from_handle(
    handle_id: str = typer.Argument(
        ...,
        help=f"The handle ID of the model run activity record to restore into " +
        "the neo4j graph store using the prov API."
    ),
    env_name: str = typer.Argument(
        ...,
        help=f"The tooling environment to target. Options: {valid_env_str}."
    ),
    validate_record: bool = typer.Option(
        VALIDATE_BY_DEFAULT,
        help="Should the record that is uploaded be validated by the prov store?",
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
    Given a handle ID, will pull the model run record from the stage's registry,
    and run a restore into the neo4j graph db using the prov API admin endpoint.
    Requires registry READ and prov store ADMIN permissions.
    """

    # Process optional environment replacement parameters
    params = process_params(param)
    env = env_manager.get_environment(name=env_name, params=params)

    # Setup auth
    auth: GetAuthFunction = setup_auth(
        stage=env.stage,
        keycloak_endpoint=env.keycloak_endpoint,
        token_refresh=token_refresh
    )

    print(f"Processing record id: {handle_id}...")

    # get the model run from the registry
    model_run = get_model_run_by_handle(
        handle_id=handle_id,
        auth=auth,
        registry_endpoint=env.registry_api_endpoint
    )

    # restore the record
    relodge_model_run_record(
        record=model_run,
        auth=auth,
        validate_record=validate_record,
        prov_endpoint=env.prov_api_endpoint
    )

    print(f"Relodge successful.\n")


@app.command()
def restore_model_run_from_file(
    model_run_file: typer.FileText = typer.Argument(
        ...,
        help="The path to the file which contains a JSON record for the model" +
        " run to relodge. Needs to be a complete ItemModelRun which contains" +
        " a handle - i.e. a valid registry entry."
    ),
    env_name: str = typer.Argument(
        ...,
        help=f"The tooling environment to target. Options: {valid_env_str}."
    ),
    validate_record: bool = typer.Option(
        VALIDATE_BY_DEFAULT,
        help="Should the record that is uploaded be validated by the prov store?",
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
    Given a file which contains a valid model run record, will run a restore
    into the neo4j graph db using the prov API admin endpoint. Requires prov
    store ADMIN permissions.
    """

    # Process optional environment replacement parameters
    params = process_params(param)
    env = env_manager.get_environment(name=env_name, params=params)

    # Setup auth
    auth: GetAuthFunction = setup_auth(
        stage=env.stage,
        keycloak_endpoint=env.keycloak_endpoint,
        token_refresh=token_refresh
    )

    print(f"Reading file contents...")
    file_contents = model_run_file.read()
    try:
        model_run = ItemModelRun.parse_raw(file_contents)
    except Exception as e:
        raise Exception(
            f"Failed to parse the contents of your provided file! Please double check it is valid. Exception: {e}.")
    model_run_file.close()

    print(f"Parsed successfully")
    print(f"Processing record id: {model_run.id}...")

    # restore the record
    relodge_model_run_record(
        record=model_run,
        auth=auth,
        validate_record=validate_record,
        prov_endpoint=env.prov_api_endpoint
    )

    print(f"Relodge successful.\n")


def write_handle_status(
    successful: Set[str],
    failed: Set[str],
    output_success: str,
    output_failed: str
) -> None:
    successful_list = list(successful)
    failed_list = list(failed)
    try:
        with open(output_success, 'w') as f:
            f.write(json.dumps(successful_list, indent=2))
    except Exception as e:
        raise Exception(
            f"Failed to write successful outputs to {output_success}, error {e}.")
    try:
        with open(output_failed, 'w') as f:
            f.write(json.dumps(failed_list, indent=2))
    except Exception as e:
        raise Exception(
            f"Failed to write failed outputs to {output_failed}, error {e}.")


@app.command()
def restore_all_model_runs(
    env_name: str = typer.Argument(
        ...,
        help=f"The tooling environment to target. Options: {valid_env_str}."
    ),
    completed_items: Optional[typer.FileText] = typer.Option(
        None,
        help=f"If a previous restoration was aborted, it will have produced a list of" +
        " successful processed handles - this list can be provided here to avoid" +
        " reprocessing successful or failed entries. It should be a basic list of handles in" +
        " JSON array."
    ),
    successful_output_path: str = typer.Option(
        "temp/successful_records.json",
        help="The path to write the list of successfully re-lodged record handles to." +
        " Warning: this file will be completely overwritten."
    ),
    failed_output_path: str = typer.Option(
        "temp/failed_records.json",
        help="The path to write the list of failed record handles to." +
        " Warning: this file will be completely overwritten."
    ),
    continue_by_default: bool = typer.Option(
        False,
        help="If a failure occurs, by default, the user is prompted whether to continue, " +
        "do you want to continue on all failures by default?"
    ),
    fail_by_default: bool = typer.Option(
        False,
        help="This operates like the -e flag in the bash shell - exit on failure. Progress will be written"
    ),
    validate_record: bool = typer.Option(
        VALIDATE_BY_DEFAULT,
        help="Should the record that is uploaded be validated by the prov store?",
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
    Will pull all complete model run records from the registry, then use these
    records to restore every item into the neo4j graph store using the prov API
    restore admin endpoint. Requires registry READ and prov ADMIN permissions.
    Upon success or handled termination due to an internal error (not Ctrl+C),
    will write the progress into two files, success and failure. These file
    locations can be modified. You can also provide an input completed items
    list which contains a list of handle IDs to consider already restored to
    avoid rewriting. If you are running this operation in a headless
    environment, you should include the --continue-by-default flag. 
    """

    # Process optional environment replacement parameters
    params = process_params(param)
    env = env_manager.get_environment(name=env_name, params=params)

    # Setup auth
    auth: GetAuthFunction = setup_auth(
        stage=env.stage,
        keycloak_endpoint=env.keycloak_endpoint,
        token_refresh=token_refresh
    )

    # keep track of handles processed
    successful_handles: Set[str] = set()
    failed_handles: Set[str] = set()

    # update successful if file provided
    if completed_items:
        try:
            item_list: List[str] = json.loads(completed_items.read())
            for item in item_list:
                successful_handles.add(item)
            print(
                f"A completed items file of length: {len(item_list)} was provided - these items will not be processed again!")
            completed_items.close()
        except Exception as e:
            raise Exception(
                "An error occurred while trying to process the provided completed items list, error: {e}.")

    record_list: List[ItemModelRun] = list_model_run_records_from_registry(
        auth=auth,
        registry_endpoint=env.registry_api_endpoint
    )

    if not continue_by_default:
        response = yes_or_no(
            f"There were {len(record_list)} records found, do you want to continue?")
        if not response:
            print("Aborting.")
            return

    for record in record_list:
        if record.id in successful_handles:
            print(f"Skipping record id {record.id} as it's already complete!")
        else:
            print(f"Processing record id: {record.id}...")

            try:
                # restore the record
                relodge_model_run_record(
                    record=record,
                    auth=auth,
                    validate_record=validate_record,
                    prov_endpoint=env.prov_api_endpoint
                )
                print(f"Relodge successful.")

                # update successful handle list
                successful_handles.add(record.id)
            except Exception as e:
                print(
                    f"Failure on record id {record.id}! Adding to failure list... Exception: {e}.")
                failed_handles.add(record.id)
                if continue_by_default:
                    print("Continuing by default...")
                elif fail_by_default:
                    print("Failing by default!")
                    print("Saving completed and failed.")
                    write_handle_status(
                        successful=successful_handles,
                        failed=failed_handles,
                        output_success=successful_output_path,
                        output_failed=failed_output_path,
                    )
                    print("Aborting.")
                    return
                else:
                    response = yes_or_no("Do you want to continue?")
                    if not response:
                        print("Saving completed and failed.")
                        write_handle_status(
                            successful=successful_handles,
                            failed=failed_handles,
                            output_success=successful_output_path,
                            output_failed=failed_output_path,
                        )
                        print("Aborting.")
                        return

    print("Completed all records.")

    if (len(failed_handles) > 0):
        print(f"There were {len(failed_handles)} failures!")

    print("Saving status...")
    write_handle_status(
        successful=successful_handles,
        failed=failed_handles,
        output_success=successful_output_path,
        output_failed=failed_output_path,
    )
    print(f"Saved. See {successful_output_path} and {failed_output_path}.")


if __name__ == "__main__":
    app()
