import subprocess
import typer
import json
import requests as rq
from config import *
from ToolingEnvironmentManager.Management import EnvironmentManager, process_params, PopulatedToolingEnvironment, PopulatedToolingEnvironment
from ProvenaInterfaces.DataStoreAPI import *
from ProvenaInterfaces.RegistryAPI import *
from ProvenaInterfaces.AsyncJobAPI import *
from KeycloakRestUtilities.TokenManager import DeviceFlowManager
from typing import List, Any, Callable, Awaitable
from helpers.import_export_helpers import yes_or_no
from datetime import datetime
import modifiers
import misc_scripts
import os
from helpers.api_helpers import fetch_item, GetAuthFunction, resolve_linked_person, JobListManager
import asyncio
from tqdm.asyncio import tqdm_asyncio as tqdm

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
        [], help=f"List of tooling environment parameter replacements in the format 'id:value' e.g. 'feature_number:1234'. Specify multiple times if required.")
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
    restore_graph: bool = typer.Option(
        False,
        help="Include this flag to also spin off lodge tasks for prov enabled nodes during importing. This will do so for all nodes included in the import file - not those already existing in the target destination AND will not take into account the results of the import mode."
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
        [], help=f"List of tooling environment parameter replacements in the format 'id:value' e.g. 'feature_number:1234'. Specify multiple times if required.")
) -> None:
    """
    Provides import functionality to stage's data registry table.
    Provides control over allowing new entries and deleting entries from table.
    """

    # Process optional environment replacement parameters
    params = process_params(param)
    env = env_manager.get_environment(name=env_name, params=params)

    # setup auth
    auth = setup_auth(env=env, token_refresh=token_refresh)

    raw_contents = input.read()

    # Run the desired migration process
    perform_import(
        env=env,
        auth=auth,
        input_contents=raw_contents,
        trial_mode=not apply,
        validate=validate,
        import_mode=import_mode,
        allow_deletion=allow_deletion,
        suppress_warnings=suppress_warnings,
    )

    # restore graph if requested
    if restore_graph:
        asyncio.run(
            perform_graph_restore(
                env=env,
                input_contents=raw_contents,
                auth=auth
            )
        )


@app.command()
def restore_graph(
    env_name: str = typer.Argument(
        ...,
        help=f"The tooling environment to target. Options: {valid_env_str}."
    ),
    input: typer.FileText = typer.Argument(
        ...,
        help=f"The location and name of the input file with the extension. e.g. 'dumps/input_file_123.json'",
    ),
    token_refresh: bool = typer.Option(
        False,
        help="Force a token refresh, invalidating cached tokens. Can be used if you have updated" +
        " your token permissions and don't want to use an out-dated access token."
    ),
    apply: bool = typer.Option(
        False,
        help="By default, will fetch all information to build jobs, but not actually submit jobs. Use --apply to deploy jobs.",
    ),
    param: ParametersType = typer.Option(
        [], help=f"List of tooling environment parameter replacements in the format 'id:value' e.g. 'feature_number:1234'. Specify multiple times if required.")
) -> None:
    """
    Restores the provenance entities in the specified input file (in standard
    dump format) using the lodge job types in the job system.

    NOTE: you will need to ensure that users referenced as owners in the
    specified entities have linked Person's which match the import data.

    NOTE: 
    """

    # Process optional environment replacement parameters
    params = process_params(param)
    env = env_manager.get_environment(name=env_name, params=params)

    # setup auth
    auth = setup_auth(env=env, token_refresh=token_refresh)

    raw_contents = input.read()

    asyncio.run(perform_graph_restore(
        env=env,
        input_contents=raw_contents,
        auth=auth,
        apply=apply
    ))


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
        [], help=f"List of tooling environment parameter replacements in the format 'id:value' e.g. 'feature_number:1234'. Specify multiple times if required.")
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


def setup_auth(env: PopulatedToolingEnvironment, token_refresh: bool) -> GetAuthFunction:
    # Login and setup auth manager
    device_auth = DeviceFlowManager(
        stage=env.stage,
        keycloak_endpoint=env.keycloak_endpoint,
        local_storage_location=".tokens.json",
        token_refresh=token_refresh
    )

    # Callable to embed into requests auth
    return device_auth.get_auth


def perform_import(
    env: PopulatedToolingEnvironment,
    auth: GetAuthFunction,
    input_contents: str,
    import_mode: ImportMode,
    validate: bool,
    trial_mode: bool,
    allow_deletion: bool,
    suppress_warnings: bool,
) -> None:
    registry_endpoint = env.registry_api_endpoint
    keycloak_endpoint = env.keycloak_endpoint

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
        auth=auth()
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


async def perform_graph_restore(
    env: PopulatedToolingEnvironment,
    input_contents: str,
    auth: GetAuthFunction,
    apply: bool
) -> None:
    print("Graph restore operation was specified and is being performed...")
    unparsed_items: List[Dict[str, Any]] = json.loads(input_contents)

    # pull out just the item payloads
    payload_list = [item['item_payload'] for item in unparsed_items]

    err_nodes = await helper_restore_graph(
        node_list=payload_list,
        auth=auth,
        apply=apply,
        env=env
    )

    if len(err_nodes) > 0:
        print("Writing error output file of just nodes which failed. Use overwrite only with apply = false and restore = true to just retry lodging for these effected nodes.")
        to_include = []
        for node in unparsed_items:
            if node['id'] in err_nodes:
                to_include.append(node)
        with open('restore-errors.json', 'w') as f:
            f.write(json.dumps(to_include))


# Restore lodge handlers take the item payload and return a job to launch
Payload = Dict[str, Any]
# set of async functions
RestoreLodgeHandlerFuncType = Callable[
    [ItemSubType, Payload, GetAuthFunction, PopulatedToolingEnvironment],
    Awaitable[Optional[AdminLaunchJobRequest]]
]

# We map the item subtype to appropriate handler function
RestoreHandlers = Dict[ItemSubType, RestoreLodgeHandlerFuncType]


# Define handlers here for each subtype
async def null_handler(subtype: ItemSubType, payload: Payload, auth: GetAuthFunction, env: PopulatedToolingEnvironment) -> Optional[AdminLaunchJobRequest]:
    return None


async def version_lodge_handler(subtype: ItemSubType, payload: Payload, auth: Any, env: PopulatedToolingEnvironment) -> Optional[AdminLaunchJobRequest]:
    # Determine the job type and sub type
    job_type = JobType.PROV_LODGE
    job_sub_type = JobSubType.LODGE_VERSION_ACTIVITY

    # Now determine the job payload by parsing info from the create node
    parsed_node = ItemVersion.parse_obj(payload)

    # get the owner username
    username = parsed_node.owner_username

    # look up connected created node to determine created node subtype
    target_id = parsed_node.from_item_id

    try:
        result: Dict[str, Any] = await fetch_item(id=target_id, auth=auth,
                                                  registry_endpoint=env.registry_api_endpoint)
    except Exception as e:
        print(
            f"Error while trying to fetch connected node for version activity with ID {parsed_node.id}.")
        raise

    # get the connected item subtype
    conn_subtype = RecordInfo.parse_obj(result).item_subtype

    # get the linked person id from the username

    # TODO if this is not linked fail gracefully! (This should be contained in the payload)
    owner_username = parsed_node.owner_username
    linked_person_id = await resolve_linked_person(
        username=owner_username,
        auth=auth,
        auth_api_endpoint=env.auth_api_endpoint
    )

    # construct job payload
    job_payload = ProvLodgeVersionPayload(
        from_version_id=parsed_node.from_item_id,
        to_version_id=parsed_node.to_item_id,
        version_activity_id=parsed_node.id,
        linked_person_id=linked_person_id,
        item_subtype=conn_subtype,
    )

    return AdminLaunchJobRequest(
        username=username,
        job_type=job_type,
        job_sub_type=job_sub_type,
        job_payload=job_payload
    )


async def create_lodge_handler(subtype: ItemSubType, payload: Payload, auth: Any, env: PopulatedToolingEnvironment) -> Optional[AdminLaunchJobRequest]:
    # Determine the job type and sub type
    job_type = JobType.PROV_LODGE
    job_sub_type = JobSubType.LODGE_CREATE_ACTIVITY

    # Now determine the job payload by parsing info from the create node
    parsed_node = ItemCreate.parse_obj(payload)

    # get the owner username
    username = parsed_node.owner_username

    # look up connected created node to determine created node subtype
    target_id = parsed_node.created_item_id
    try:
        result: Dict[str, Any] = await fetch_item(id=target_id, auth=auth,
                                                  registry_endpoint=env.registry_api_endpoint)
    except Exception as e:
        print(
            f"Error while trying to fetch connected node for create activity with ID {parsed_node.id}.")
        raise

    # get the connected item subtype
    conn_subtype = RecordInfo.parse_obj(result).item_subtype

    linked_person_id = await resolve_linked_person(
        username=username,
        auth=auth,
        auth_api_endpoint=env.auth_api_endpoint
    )

    # construct job payload
    job_payload = ProvLodgeCreationPayload(
        created_item_id=parsed_node.created_item_id,
        creation_activity_id=parsed_node.id,
        linked_person_id=linked_person_id,
        created_item_subtype=conn_subtype
    )

    return AdminLaunchJobRequest(
        username=username,
        job_type=job_type,
        job_sub_type=job_sub_type,
        job_payload=job_payload
    )


async def model_run_lodge_handler(subtype: ItemSubType, payload: Payload, auth: Any, env: PopulatedToolingEnvironment) -> Optional[AdminLaunchJobRequest]:
    # Determine the job type and sub type
    job_type = JobType.PROV_LODGE
    job_sub_type = JobSubType.MODEL_RUN_LODGE_ONLY

    # Now determine the job payload by parsing info from the create node
    parsed_node = ItemModelRun.parse_obj(payload)

    # get the owner username
    username = parsed_node.owner_username

    # construct job payload
    job_payload = ProvLodgeModelRunLodgeOnlyPayload(
        model_run_record_id=parsed_node.id,
        record=parsed_node.record,
        revalidate=False
    )

    return AdminLaunchJobRequest(
        username=username,
        job_type=job_type,
        job_sub_type=job_sub_type,
        job_payload=job_payload
    )


RESTORE_LODGE_HANDLER_MAP: RestoreHandlers = {
    # All of these types have no inherent provenance - described in other resources
    ItemSubType.PERSON: null_handler,
    ItemSubType.ORGANISATION: null_handler,
    ItemSubType.STUDY: null_handler,
    ItemSubType.MODEL: null_handler,
    ItemSubType.MODEL_RUN_WORKFLOW_TEMPLATE: null_handler,
    ItemSubType.DATASET: null_handler,
    ItemSubType.DATASET_TEMPLATE: null_handler,
    ItemSubType.STUDY: null_handler,

    # PROV associated - spin off lodge tasks
    ItemSubType.CREATE: create_lodge_handler,
    ItemSubType.VERSION: version_lodge_handler,
    ItemSubType.MODEL_RUN: model_run_lodge_handler,
}


async def helper_restore_graph(
    node_list: List[Dict[str, Any]],
    auth: GetAuthFunction,
    env: PopulatedToolingEnvironment,
    apply: bool
) -> List[str]:
    """

    Looks through all nodes provided and uses the async job system to manage relodging all provenance.

    This is achieved by mapping the nodes by subtype into their respective admin launch job request, then lodging and monitoring this collection of jobs.

    Some notes

    - ensure that all linked entities are present - in some cases this is relied on

    Args:
        node_list (List[Dict[str, Any]]): The list of nodes - this is the payload only not the full bundle item from export
        auth (GetAuthFunction): The auth function
        env (PopulatedToolingEnvironment): Env manager

    Raises:
        Exception: Exceptions depending on error encountered

    Returns:
        List[str]: The list of nodes which experienced an error, if any
    """
    print("--- RESTORING PROV GRAPH ---")
    print()
    print("Note that graph restoration utilises the job system and is therefore an asynchronous operation.")

    # For each node, parse the item subtype - filter out seeds
    subtype_to_node_list_map: Dict[ItemSubType, List[Dict[str, Any]]] = {
    }

    for node in node_list:
        # parse as record info base item
        record_base = RecordInfo.parse_obj(node)

        # check its complete item
        if record_base.record_type != RecordType.COMPLETE_ITEM:
            print(f"Ignoring seed item {record_base.id}...")
            continue

        # update subtype list
        sub = record_base.item_subtype
        current = subtype_to_node_list_map.get(sub, [])
        current.append(node)
        subtype_to_node_list_map[sub] = current

    # use the dispatcher to get list of jobs to submit
    id_to_job: Dict[str, AdminLaunchJobRequest] = {}

    for subtype, node_list in subtype_to_node_list_map.items():
        dispatcher = RESTORE_LODGE_HANDLER_MAP.get(subtype)
        if dispatcher is None:
            raise Exception(f"No handler for restoring type {subtype}")

        # generate pool of tasks
        print(f"Gathering job pool for {subtype} nodes.")
        to_dispatch = [dispatcher(subtype, node, auth, env)
                       for node in node_list]
        print(f"Running {len(to_dispatch)} tasks...")
        results = await tqdm.gather(*to_dispatch)
        print("Done.")
        print()

        # record results
        for node, res in zip(node_list, results):
            if res:
                id_to_job[node['id']] = res

    # dispatch all jobs and keep track of their status until all finished
    # list failures as they occur

    print(
        f"After dispatching, there were {len(id_to_job)} lodges to complete!")

    if not apply:
        print(
            f"Returning early as --apply flag was not supplied. {len(id_to_job)} jobs were prepared for lodge successfully.")
        return []
    else:
        print(f"--apply flag was supplied, applying changes.")

    to_continue = yes_or_no(f"Do you want to lodge {len(id_to_job)} jobs?")

    if not to_continue:
        print("Aborting...")
        exit(1)

    # now spin up a job for each and track using the manager class
    manager = JobListManager(
        item_id_to_job=id_to_job,
        auth=auth,
        env=env
    )

    # deploy jobs
    await manager.deploy_jobs()

    # monitor until completion
    try:
        await manager.run_until_complete()
    except Exception as e:
        print(
            f"An unhandled exception occurred during job monitoring. Error: {e}.")
        print(f"Displaying error report:")
        manager.error_report()
        raise

    # show error report
    return manager.error_report()


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
        [], help=f"List of tooling environment parameter replacements in the format 'id:value' e.g. 'feature_number:1234'. Specify multiple times if required.")
) -> None:
    """
    Same as import items but defaults to an empty list and allows deletion. 

    WARNING clears all items from the registry...
    """

    # Process optional environment replacement parameters
    params = process_params(param)
    env = env_manager.get_environment(name=env_name, params=params)

    # setup auth
    auth = setup_auth(env=env, token_refresh=token_refresh)

    # Run the desired migration process
    perform_import(
        env=env,
        auth=auth,
        input_contents="[]",
        trial_mode=not apply,
        validate=validate,
        import_mode=ImportMode.SYNC_DELETION_ALLOWED,
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
        [], help=f"List of tooling environment parameter replacements in the format 'id:value' e.g. 'feature_number:1234'. Specify multiple times if required.")
) -> None:
    """
    Same as import items but defaults to an empty list and allows deletion. 

    WARNING clears all items from the registry...
    """

    # Process optional environment replacement parameters
    params = process_params(param)
    env = env_manager.get_environment(name=env_name, params=params)

    # setup auth
    auth = setup_auth(env=env, token_refresh=token_refresh)

    # Clear the items
    perform_import(
        env=env,
        auth=auth,
        input_contents="[]",
        trial_mode=not apply,
        # default to validate imported items - we aren't importing anyway.
        validate=True,
        import_mode=ImportMode.SYNC_DELETION_ALLOWED,
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

# add the misc scripts sub app
app.add_typer(misc_scripts.app, name="scripts",
              help="Miscellaneous scripts such as statistic summaries.")


if __name__ == "__main__":
    app()
