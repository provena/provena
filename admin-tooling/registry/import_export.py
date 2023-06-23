import subprocess
import typer
import json
import requests as rq
from config import *
from ToolingEnvironmentManager.Management import EnvironmentManager, process_params
from SharedInterfaces.DataStoreAPI import *
from SharedInterfaces.RegistryAPI import *
from KeycloakRestUtilities.TokenManager import DeviceFlowManager
from typing import List, Any
from helpers.import_export_helpers import yes_or_no
from datetime import datetime
import modifiers
import os

# Typer CLI typing hint for parameters
ParametersType = List[str]

# Establish env manager
env_manager = EnvironmentManager(environment_file_path="../environments.json")
valid_env_str = env_manager.environment_help_string

# just want this on DEVs and feature branches which will use dev in this command usage
clear_and_init_valid_stages = ["DEV"]

# disabled to prevent entire json input content from being
# output resulting in error messages being lost in terminal.
app = typer.Typer(pretty_exceptions_show_locals=False)


@app.command()
def export_items(
    env_name: str = typer.Argument(
        ...,
        help=f"The tooling environment to target. Options: {valid_env_str}."
    ),
    output: typer.FileTextWrite = typer.Option(
        f"{SAVE_DIRECTORY}/export_" + str(datetime.now()) + ".json",
        help=f"The name of the file to save exported data in.",
        prompt="Provide the name of the output file - include the file extension. \nEnter to use default -->",
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
    Provides functionality to export a stage's registry contents. Allows
    the overriding of stage endpoints to point at local deployments which may in turn point to any table.
    """

    # Process optional environment replacement parameters
    params = process_params(param)
    env = env_manager.get_environment(name=env_name, params=params)

    try:
        # make dumps directory for saving export data that is excluded from git commits
        os.mkdir(SAVE_DIRECTORY)
    except FileExistsError:
        # directory already exists. Pass.
        pass
    except Exception as e:
        raise Exception(e)

    # Run the desired migration process
    print("Performing export")
    json_response = perform_export(
        registry_endpoint=env.registry_api_endpoint,
        keycloak_endpoint=env.keycloak_endpoint,
        stage=env.stage,
        token_refresh=token_refresh,
    )

    print("Writing output")

    output.write(json.dumps(
        list(map(lambda bundle: json.loads(bundle.json()), json_response)), indent=2))


@app.command()
def import_items(
    env_name: str = typer.Argument(
        ...,
        help=f"The tooling environment to target. Options: {valid_env_str}."
    ),
    input: typer.FileText = typer.Argument(
        ...,
        help=f"The location and name of the input file with the extension. e.g. 'dumps/input_file_123.json'",
    ),
    import_mode: ImportMode = typer.Argument(
        ...,
        help="What kind of import should be performed? See documentation for registry import modes.",
    ),
    token_refresh: bool = typer.Option(
        False,
        help="Force a token refresh, invalidating cached tokens. Can be used if you have updated" +
        " your token permissions and don't want to use an out-dated access token."
    ),
    apply: bool = typer.Option(
        False,
        help="By default, will not apply any changes to the registry." +
        " Include this flag to actually write changes to the registry to update it ",
    ),
    validate: bool = typer.Option(
        True,
        help=f"Should the imported models be validated as the correct type and structure " +
        "before being inputted to the table?"
    ),
    allow_deletion: bool = typer.Option(
        False,
        help=f"Special flag to include if you are explicitly allowing deletion in " +
        "SYNC_DELETION_ALLOWED import mode."
    ),
    suppress_warnings: bool = typer.Option(
        False,
        help="""Whether or not to suppress warnings requiring human input.
             Include flag for fully automated processes."""
    ),
    param: ParametersType = typer.Option(
        [], help=f"List of tooling environment parameter replacements in the format 'id:value' e.g. 'feature_num:1234'. Specify multiple times if required.")
) -> None:
    """
    Provides import functionality to stage's data registry table.
    Provides control over allowing new entries and deleting entries from table.
    """

    # Process optional environment replacement parameters
    params = process_params(param)
    env = env_manager.get_environment(name=env_name, params=params)

    # Run the desired migration process
    perform_import(
        registry_endpoint=env.registry_api_endpoint,
        keycloak_endpoint=env.keycloak_endpoint,
        stage=env.stage,
        input_contents=input.read(),
        trial_mode=not apply,
        validate=validate,
        import_mode=import_mode,
        token_refresh=token_refresh,
        allow_deletion=allow_deletion,
        suppress_warnings=suppress_warnings,
    )


@app.command()
def import_items_from_tables(
    env_name: str = typer.Argument(
        ...,
        help=f"The tooling environment to target. Options: {valid_env_str}."
    ),
    import_mode: ImportMode = typer.Argument(
        ...,
        help="What kind of import should be performed? See documentation for registry import modes.",
    ),
    resource_table_name: str = typer.Option(
        ...,
        help="What is the name of the dynamoDB table to trigger an import from which contains the primary resources?"
    ),
    lock_table_name: str = typer.Option(
        ...,
        help="What is the name of the dynamoDB table to trigger an import from which contains the lock configurations?"
    ),
    auth_table_name: str = typer.Option(
        ...,
        help="What is the name of the dynamoDB table to trigger an import from which contains the auth configurations?"
    ),
    token_refresh: bool = typer.Option(
        False,
        help="Force a token refresh, invalidating cached tokens. Can be used if you have updated" +
        " your token permissions and don't want to use an out-dated access token."
    ),
    apply: bool = typer.Option(
        False,
        help="By default, will not apply any changes to the registry." +
        " Include this flag to actually write changes to the registry to update it ",
    ),
    validate: bool = typer.Option(
        True,
        help=f"Should the imported models be validated as the correct type and structure " +
        "before being inputted to the table?"
    ),
    allow_deletion: bool = typer.Option(
        False,
        help=f"Special flag to include if you are explicitly allowing deletion in " +
        "SYNC_DELETION_ALLOWED import mode."
    ),
    suppress_warnings: bool = typer.Option(
        False,
        help="""Whether or not to suppress warnings requiring human input.
             Include flag for fully automated processes."""
    ),
    param: ParametersType = typer.Option(
        [], help=f"List of tooling environment parameter replacements in the format 'id:value' e.g. 'feature_num:1234'. Specify multiple times if required.")
) -> None:
    """
    A basic wrapper of the external table import function of the registry.

    Ensure the table names provided exist and the targeted API has permissions to r/w into them.
    """

    # Process optional environment replacement parameters
    params = process_params(param)
    env = env_manager.get_environment(name=env_name, params=params)

    # Run the desired migration process
    external_table_import(
        registry_endpoint=env.registry_api_endpoint,
        keycloak_endpoint=env.keycloak_endpoint,
        stage=env.stage,
        resource_table_name=resource_table_name,
        auth_table_name=auth_table_name,
        lock_table_name=lock_table_name,
        trial_mode=not apply,
        validate=validate,
        import_mode=import_mode,
        token_refresh=token_refresh,
        allow_deletion=allow_deletion,
        suppress_warnings=suppress_warnings,
    )


def perform_export(
    registry_endpoint: str,
    keycloak_endpoint: str,
    stage: str,
    token_refresh: bool,
) -> List[BundledItem]:
    print(f"Using registry endpoint = {registry_endpoint}.")
    print(f"Using keycloak endpoint = {keycloak_endpoint}.")

    # Login and setup auth manager
    device_auth = DeviceFlowManager(
        stage=stage,
        keycloak_endpoint=keycloak_endpoint,
        local_storage_location=".tokens.json",
        token_refresh=token_refresh
    )
    # Callable to embed into requests auth
    get_auth = device_auth.get_auth

    # Export request

    # make requests for parsed or unparsed registry items
    resp = rq.get(
        registry_endpoint +
        f"/admin/export",
        auth=get_auth()
    )

    # check success of request
    assert resp.status_code != 401, f"Got status code {resp.status_code} -> Insufficient privileges. Registry admin permissions are required."
    assert resp.status_code == 200, f"expected 200 got {resp.status_code}"
    parsed_export = RegistryExportResponse.parse_obj(resp.json())
    assert parsed_export.status
    assert parsed_export.items
    return parsed_export.items


def perform_import(
    registry_endpoint: str,
    keycloak_endpoint: str,
    input_contents: str,
    import_mode: ImportMode,
    validate: bool,
    stage: str,
    trial_mode: bool,
    token_refresh: bool,
    allow_deletion: bool,
    suppress_warnings: bool,
) -> None:
    print(f"Using registry endpoint = {registry_endpoint}.")
    print(f"Using keycloak endpoint = {keycloak_endpoint}.")

    print(f"Trial mode set to: {trial_mode}")

    if trial_mode:
        print("Not applying changes to registry. Use flag --apply to write changes")
    else:
        print("Will write changes to registry. ")
        if not suppress_warnings:
            response = yes_or_no("Are you sure you want to continue?")

            if not response:
                print("Aborting operation. Exclude --apply to do a trial run.")
                exit(1)

    # Login and setup auth manager
    device_auth = DeviceFlowManager(
        stage=stage,
        keycloak_endpoint=keycloak_endpoint,
        local_storage_location=".tokens.json",
        token_refresh=token_refresh
    )
    # Callable to embed into requests auth
    get_auth = device_auth.get_auth

    # read the items from the json
    unparsed_items: List[Dict[str, Any]] = json.loads(input_contents)
    print(f"Import items length: {len(unparsed_items)}")

    assert isinstance(
        unparsed_items, list), "Your input file had an incorrect structure, it should be a list of dictionaries."

    # human warnings
    if not suppress_warnings:
        if not validate:
            response = yes_or_no(
                "Are you sure you want to allow unparsed imports? This could result in unstable operation...")
            if not response:
                print(
                    "Aborting operation. Exclude --no-validate to perform a parsed import.")
                exit(1)
        if allow_deletion:
            response = yes_or_no("Are you sure you want to allow deletion?")
            if not response:
                print("Aborting operation. Exclude --allow_deletion to not delete.")
                exit(1)

    # construct the payload
    import_request = RegistryImportRequest(
        import_mode=import_mode,
        parse_items=validate,
        allow_entry_deletion=allow_deletion,
        trial_mode=trial_mode,
        items=unparsed_items
    )

    resp = rq.post(
        registry_endpoint + "/admin/import",
        json=json.loads(import_request.json()),
        auth=get_auth()
    )

    try:
        assert resp.status_code == 200
    except Exception as e:
        details = "Cannot parse error message."
        try:
            details = resp.json()['detail']
        except:
            try:
                details = resp.text
            except:
                None
        raise Exception(
            f"import parse failed: Status code {resp.status_code}. Details: {details}.")

    import_response = RegistryImportResponse.parse_obj(resp.json())

    if not import_response.status.success:

        failure_list = import_response.failure_list
        assert failure_list

        for handle, obj in failure_list:
            print(f"Failed for handle {handle}. Registry Item {obj}")

        raise Exception(f"Aborting due to listed failures.")

    assert import_response.statistics
    print("--- IMPORT STATISTICS ---")
    print(import_response.statistics)
    print()

    if trial_mode:
        print(
            "No entries written. Run again with --apply flag to write updates to registry.")
    else:
        print("Successfully imported updated registry items. Changes were applied.")

    return


def external_table_import(
    registry_endpoint: str,
    keycloak_endpoint: str,
    resource_table_name: str,
    lock_table_name: str,
    auth_table_name: str,
    import_mode: ImportMode,
    validate: bool,
    stage: str,
    trial_mode: bool,
    token_refresh: bool,
    allow_deletion: bool,
    suppress_warnings: bool,
) -> None:
    print(f"Trial mode set to: {trial_mode}")

    if trial_mode:
        print("Not applying changes to registry. Use flag --apply to write changes")
    else:
        print("Will write changes to registry. ")
        if not suppress_warnings:
            response = yes_or_no("Are you sure you want to continue?")

            if not response:
                print("Aborting operation. Exclude --apply to do a trial run.")
                exit(1)

    # Login and setup auth manager
    device_auth = DeviceFlowManager(
        stage=stage,
        keycloak_endpoint=keycloak_endpoint,
        local_storage_location=".tokens.json",
        token_refresh=token_refresh
    )
    # Callable to embed into requests auth
    get_auth = device_auth.get_auth

    # human warnings
    if not suppress_warnings:
        if not validate:
            response = yes_or_no(
                "Are you sure you want to allow unparsed imports? This could result in unstable operation...")
            if not response:
                print(
                    "Aborting operation. Exclude --no-validate to perform a parsed import.")
                exit(1)
        if allow_deletion:
            response = yes_or_no("Are you sure you want to allow deletion?")
            if not response:
                print("Aborting operation. Exclude --allow_deletion to not delete.")
                exit(1)

    # construct the payload
    restore_request = RegistryRestoreRequest(
        import_mode=import_mode,
        parse_items=validate,
        allow_entry_deletion=allow_deletion,
        trial_mode=trial_mode,
        table_names=TableNames(
            resource_table_name=resource_table_name,
            auth_table_name=auth_table_name,
            lock_table_name=lock_table_name
        )
    )

    resp = rq.post(
        registry_endpoint + "/admin/restore_from_table",
        json=json.loads(restore_request.json()),
        auth=get_auth()
    )

    try:
        assert resp.status_code == 200
    except Exception as e:
        details = "Cannot parse as JSON."
        try:
            details = resp.json()['detail']
        except:
            None
        raise Exception(
            f"Restore operation failed: Status code {resp.status_code}. Details: {details}.")

    import_response = RegistryImportResponse.parse_obj(resp.json())

    if not import_response.status.success:

        failure_list = import_response.failure_list
        assert failure_list

        for handle, obj in failure_list:
            print(f"Failed for handle {handle}. Registry Item {obj}")

        raise Exception(f"Aborting due to listed failures.")

    assert import_response.statistics
    print("--- IMPORT STATISTICS ---")
    print(import_response.statistics)
    print()

    if trial_mode:
        print(
            "No entries written. Run again with --apply flag to write updates to registry.")
    else:
        print("Successfully imported updated registry items. Changes were applied.")

    return


@app.command()
def clear_items(
    env_name: str = typer.Argument(
        ...,
        help=f"The tooling environment to target. Options: {valid_env_str}."
    ),
    token_refresh: bool = typer.Option(
        False,
        help="Force a token refresh, invalidating cached tokens. Can be used if you have updated" +
        " your token permissions and don't want to use an out-dated access token."
    ),
    apply: bool = typer.Option(
        False,
        help="By default, will not apply any changes to the registry." +
        " Include this flag to actually write changes to the registry to update it ",
    ),
    validate: bool = typer.Option(
        True,
        help=f"Should the imported models be validated as the correct type and structure " +
        "before being inputted to the table?"
    ),
    suppress_warnings: bool = typer.Option(
        False,
        help="""Whether or not to suppress warnings requiring human input.
             Include flag for fully automated processes."""
    ),
    param: ParametersType = typer.Option(
        [], help=f"List of tooling environment parameter replacements in the format 'id:value' e.g. 'feature_num:1234'. Specify multiple times if required.")
) -> None:
    """
    Same as import items but defaults to an empty list and allows deletion. 

    WARNING clears all items from the registry...
    """

    # Process optional environment replacement parameters
    params = process_params(param)
    env = env_manager.get_environment(name=env_name, params=params)

    # Run the desired migration process
    perform_import(
        registry_endpoint=env.registry_api_endpoint,
        keycloak_endpoint=env.keycloak_endpoint,
        stage=env.stage,
        input_contents="[]",
        trial_mode=not apply,
        validate=validate,
        import_mode=ImportMode.SYNC_DELETION_ALLOWED,
        token_refresh=token_refresh,
        allow_deletion=True,
        suppress_warnings=suppress_warnings,
    )


@app.command()
def clear_and_init(
    env_name: str = typer.Argument(
        ...,
        help=f"The tooling environment to target for clear and initialisation. If targeting a feature deployment, then this is used for the keycloak instance. One of: {valid_env_str}.",
    ),
    token_refresh: bool = typer.Option(
        False,
        help="Force a token refresh, invalidating cached tokens. Can be used if you have updated" +
        " your token permissions and don't want to use an out-dated access token."
    ),
    apply: bool = typer.Option(
        False,
        help="By default, will not apply any changes to the registry." +
        " Include this flag to actually write changes to the registry to update it ",
    ),
    suppress_warnings: bool = typer.Option(
        False,
        help="""Whether or not to suppress warnings requiring human input.
             Include flag for fully automated processes."""
    ),
    param: ParametersType = typer.Option(
        [], help=f"List of tooling environment parameter replacements in the format 'id:value' e.g. 'feature_num:1234'. Specify multiple times if required.")
) -> None:
    """
    Same as import items but defaults to an empty list and allows deletion. 

    WARNING clears all items from the registry...
    """

    # Process optional environment replacement parameters
    params = process_params(param)
    env = env_manager.get_environment(name=env_name, params=params)

    # Clear the items
    perform_import(
        registry_endpoint=env.registry_api_endpoint,
        keycloak_endpoint=env.keycloak_endpoint,
        stage=env.stage,
        input_contents="[]",
        trial_mode=not apply,
        # default to validate imported items - we aren't importing anyway.
        validate=True,
        import_mode=ImportMode.SYNC_DELETION_ALLOWED,
        token_refresh=token_refresh,
        allow_deletion=True,
        suppress_warnings=suppress_warnings,
    )

    if not apply:
        return  # dont continue with intialisation if the clear was not applied

    print("Performing initialisation of items by running integration work flow test without clean up...")

    # Initialise the items by running the integration workflow test which requires some env building
    # move to integration test directory
    os.chdir(os.path.join(os.path.dirname(__file__),
             "..", "..", "tests", "integration"))

    # create a .venv if one does not exist
    if not os.path.exists(".venv"):
        subprocess.run(["python3.10", "-m", "venv", ".venv"])

    subprocess.Popen(['source .venv/bin/activate && echo "Sourced virtual environment"'],
                     shell=True, executable="/bin/bash")
    # install requirement
    subprocess.run(["pip", "install", "-r", "requirements.txt"])
    endpoints = env.get_endpoint_map()
    endpoints["LEAVE_ITEMS_FOR_INITIALISATION"] = "True"

    for k, v in endpoints.items():
        os.environ[k] = v

    # run the integration test
    subprocess.run(
        ["pytest", "tests/workflows/test_workflows.py::test_provenance_workflow"])


# add the modifier sub app
app.add_typer(modifiers.app, name="modifiers",
              help="A set of migrations performable between input/output dumps.")


if __name__ == "__main__":
    app()
