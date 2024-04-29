from ProvenaInterfaces.AsyncJobModels import *
from EcsSqsPythonTools.Types import *
from EcsSqsPythonTools.Settings import JobBaseSettings
from EcsSqsPythonTools.Workflow import parse_job_specific_payload
from helpers.util import py_to_dict
from ProvenaInterfaces.AsyncJobAPI import *
from config import Config
from typing import cast
from helpers.handle_helpers import mint_self_describing_handle
from helpers.auth_helpers import seed_auth_configuration
from helpers.job_api_helpers import submit_lodge_create_activity, submit_lodge_version_activity
from helpers.action_helpers import create_seed_history
from helpers.lock_helpers import seed_lock_configuration
from helpers.time_helpers import get_timestamp
from helpers.dynamo_helpers import *
from ProvenaInterfaces.RegistryModels import METADATA_READ_ROLE, ItemCreate, CreateDomainInfo, RecordType
import json
import asyncio

RegistryJobHandler = CallbackFunc


def generate_failed_job(error: str) -> CallbackResponse:
    return CallbackResponse(
        status=JobStatus.FAILED,
        info=f"Job failed, err: {error}.",
        result=None
    )


def wake_up_handler(payload: JobSnsPayload, settings: JobBaseSettings) -> CallbackResponse:
    """
    Do nothing - wake up the job
    """
    print(f"Woke up successfully.")

    return CallbackResponse(
        status=JobStatus.SUCCEEDED,
        info=None,
        result=py_to_dict(
            WakeUpResult(
            )
        )
    )


def create_activity_handler(payload: JobSnsPayload, settings: JobBaseSettings) -> CallbackResponse:
    """
    Handles the registration of the Create activity.

    Then spins off a job to lodge the provenance for this new activity.

    Parameters
    ----------
    payload : JobSnsPayload
        The job payload, parsable as the mapped subtype model
    settings : JobBaseSettings
        The job settings

    Returns
    -------
    CallbackResponse
        The formatted callback response
    """
    # The purpose of this job is to create a CreateActivity item in the
    # Registry, and lodge it using a prov job

    print(f"Running registry register create activity handler.")

    print("Parsing full API config from environment.")
    try:
        config = Config()
    except Exception as e:
        return CallbackResponse(
            status=JobStatus.FAILED,
            info=f"Failed to parse job configuration from the environment. Error: {e}."
        )
    print("Successfully parsed environment config.")

    print(f"Parsing job specific payload")
    try:
        create_payload = cast(RegistryRegisterCreateActivityPayload, parse_job_specific_payload(
            payload=payload, job_sub_type=JobSubType.REGISTER_CREATE_ACTIVITY))
    except Exception as e:
        return generate_failed_job(error=f"Failed to parse job payload from the event. Error: {e}.")

    print(f"Parsed specific payload: {create_payload}")

    # Now we run the usual mint/update workflow to generate the item

    # Create a handle which points to <registry URL>/item/<handle>
    handle = asyncio.run(mint_self_describing_handle(config=config))

    # write auth object first - this uses default roles
    seed_auth_configuration(
        id=handle,
        username=payload.username,
        config=config,
        default_roles=[METADATA_READ_ROLE]
    )

    # write lock object first
    seed_lock_configuration(
        id=handle,
        config=config,
    )

    item_domain_info = CreateDomainInfo(
        display_name=f"Created item {create_payload.created_item_id}",
        created_item_id=create_payload.created_item_id
    )

    item = ItemCreate(
        id=handle,
        owner_username=payload.username,
        created_timestamp=get_timestamp(),
        updated_timestamp=get_timestamp(),
        history=[
            create_seed_history(
                username=payload.username,
                item_domain_info=item_domain_info
            )
        ],
        ** item_domain_info.dict(),
        record_type=RecordType.COMPLETE_ITEM
    )

    # Then we write to DB

    # write the object to the registry
    friendly_format = json.loads(item.json(exclude_none=True))

    try:
        write_registry_dynamo_db_entry_raw(
            registry_item=friendly_format,
            config=config
        )
    # Raise 500 if something goes wrong
    except Exception as e:
        return generate_failed_job(error=f"Failed to write complete item to registry. Aborting. Contact administrator. Error {e}.")

    # And spinoff lodge job
    lodge_session_id = asyncio.run(submit_lodge_create_activity(
        username=payload.username,
        payload=ProvLodgeCreationPayload(
            created_item_id=create_payload.created_item_id,
            creation_activity_id=item.id,
            created_item_subtype=create_payload.created_item_subtype,
            linked_person_id=create_payload.linked_person_id
        ),
        config=config
    ))

    return CallbackResponse(
        status=JobStatus.SUCCEEDED,
        info=None,
        result=py_to_dict(
            RegistryRegisterCreateActivityResult(
                creation_activity_id=item.id,
                lodge_session_id=lodge_session_id
            )
        )
    )


def version_activity_handler(payload: JobSnsPayload, settings: JobBaseSettings) -> CallbackResponse:
    """
    Handles the registration of the Version activity.

    Then spins off a job to lodge the provenance for this new activity.

    Parameters
    ----------
    payload : JobSnsPayload
        The job payload, parsable as the mapped subtype model
    settings : JobBaseSettings
        The job settings

    Returns
    -------
    CallbackResponse
        The formatted callback response
    """
    # The purpose of this job is to create a CreateActivity item in the
    # Registry, and lodge it using a prov job

    print(f"Running registry register version activity handler.")

    print("Parsing full API config from environment.")
    try:
        config = Config()
    except Exception as e:
        return CallbackResponse(
            status=JobStatus.FAILED,
            info=f"Failed to parse job configuration from the environment. Error: {e}."
        )
    print("Successfully parsed environment config.")

    print(f"Parsing job specific payload")
    try:
        version_payload = cast(RegistryRegisterVersionActivityPayload, parse_job_specific_payload(
            payload=payload, job_sub_type=JobSubType.REGISTER_VERSION_ACTIVITY))
    except Exception as e:
        return generate_failed_job(error=f"Failed to parse job payload from the event. Error: {e}.")

    print(f"Parsed specific payload: {version_payload}")

    # Now we run the usual mint/update workflow to generate the item

    # Create a handle which points to <registry URL>/item/<handle>
    handle = asyncio.run(mint_self_describing_handle(config=config))

    # write auth object first - this uses default roles
    seed_auth_configuration(
        id=handle,
        username=payload.username,
        config=config,
        default_roles=[METADATA_READ_ROLE]
    )

    # write lock object first
    seed_lock_configuration(
        id=handle,
        config=config,
    )

    item_domain_info = VersionDomainInfo(
        display_name=f"(V{version_payload.version_number}) Version from {version_payload.from_version_id} to {version_payload.to_version_id}",
        reason=version_payload.reason,
        from_item_id=version_payload.from_version_id,
        to_item_id=version_payload.to_version_id,
        new_version_number=version_payload.version_number
    )

    item = ItemVersion(
        id=handle,
        owner_username=payload.username,
        created_timestamp=get_timestamp(),
        updated_timestamp=get_timestamp(),
        history=[
            create_seed_history(
                username=payload.username,
                item_domain_info=item_domain_info
            )
        ],
        ** item_domain_info.dict(),
        record_type=RecordType.COMPLETE_ITEM
    )

    # Then we write to DB

    # write the object to the registry
    friendly_format = json.loads(item.json(exclude_none=True))

    try:
        write_registry_dynamo_db_entry_raw(
            registry_item=friendly_format,
            config=config
        )
    # Raise 500 if something goes wrong
    except Exception as e:
        return generate_failed_job(error=f"Failed to write complete item to registry. Aborting. Contact administrator. Error {e}.")

    # And spinoff lodge job
    lodge_session_id = asyncio.run(submit_lodge_version_activity(
        username=payload.username,
        payload=ProvLodgeVersionPayload(
            from_version_id=version_payload.from_version_id,
            to_version_id=version_payload.to_version_id,
            version_activity_id=item.id,
            linked_person_id=version_payload.linked_person_id,
            item_subtype=version_payload.item_subtype
        ),
        config=config
    ))

    return CallbackResponse(
        status=JobStatus.SUCCEEDED,
        info=None,
        result=py_to_dict(
            RegistryRegisterVersionActivityResult(
                lodge_session_id=lodge_session_id,
                version_activity_id=item.id
            )
        )
    )


REGISTRY_HANDLER_MAP: Dict[JobSubType, RegistryJobHandler] = {
    JobSubType.REGISTER_CREATE_ACTIVITY: create_activity_handler,
    JobSubType.REGISTER_VERSION_ACTIVITY: version_activity_handler,
    JobSubType.REGISTRY_WAKE_UP: wake_up_handler,
}


def job_dispatcher(payload: JobSnsPayload, settings: JobBaseSettings) -> CallbackResponse:
    # dispatch into function
    print(f"Dispatching into handler.")
    handler = REGISTRY_HANDLER_MAP[payload.job_sub_type]

    print(f"Running dispatched function")
    return handler(payload, settings)
