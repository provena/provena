from fastapi import HTTPException
from ProvenaInterfaces.RegistryModels import *
from ProvenaInterfaces.AsyncJobModels import *
from ProvenaInterfaces.RegistryAPI import VersionRequest
from helpers.util import py_to_dict
from helpers.registry.job_api_helpers import *
from config import Config
from helpers.registry.dynamo_helpers import write_registry_dynamo_db_entry_raw


async def spinoff_creation_job(linked_person_id: str, created_item: ItemBase, username: str, config: Config) -> str:
    """
    Runs the creation spin off tasks using the async job infra.

    This involves submitting a registry job which creates a Create
    activity, then in a chained job, lodges the provenance.

    Returns the session ID from the job api.

    Parameters
    ----------
    linked_person_id : str
        The linked person ID already fetched

    created_item : ItemBase
        The created item to be registered/handled

    username : str
        The job username

    config : Config
        API config

    Returns
    -------
    str
        Session ID

    Raises
    ------
    HTTPException
        Managed HTTP exception
    """
    session_id = await submit_register_create_activity(
        username=username,
        payload=RegistryRegisterCreateActivityPayload(
            created_item_id=created_item.id,
            created_item_subtype=created_item.item_subtype,
            linked_person_id=linked_person_id
        ),
        config=config
    )

    created_item.workflow_links = WorkflowLinks(
        create_activity_workflow_id=session_id)

    # write the object to the registry
    friendly_format = py_to_dict(created_item)
    try:
        write_registry_dynamo_db_entry_raw(
            registry_item=friendly_format,
            config=config
        )
    # Raise 500 if something goes wrong
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to write updated item including workflow session id to registry. Aborting. Contact administrator. Error {e}."
        )
    # return the session id
    return session_id


async def spinoff_version_job(
        username: str,
        version_request: VersionRequest,
        new_item: ItemBase,
        version_number: int,
        from_id: str,
        to_id: str,
        linked_person_id: str,
        item_subtype: ItemSubType,
        config: Config
) -> str:
    """

    Spins off a version job. 

    This uses the async job infra as the registry API service account.

    This creates a Version activity in the registry, and lodges the provenance data.

    Parameters
    ----------
    username : str
        The job username
    version_request : VersionRequest
        The version request which includes info needed for the job
    new_item : ItemBase
        The new item which was generated
    version_number : int
        The version number for the new item
    from_id : str
        Where did it come from?
    to_id : str
        Where did it go (cotton eyed joe)
    linked_person_id : str
        The ID of the Person linked to the username
    item_subtype : ItemSubType
        The item subtype - used for provenance in job payload
    config : Config
        The config

    Returns
    -------
    str
        The session ID of the version create activity

    Raises
    ------
    HTTPException
        Managed HTTP exceptions
    """
    session_id = await submit_register_version_activity(
        username=username,
        payload=RegistryRegisterVersionActivityPayload(
            reason=version_request.reason,
            version_number=version_number,
            from_version_id=from_id,
            to_version_id=to_id,
            linked_person_id=linked_person_id,
            item_subtype=item_subtype
        ),
        config=config
    )

    # update session ID in response

    # track session info against new item
    new_item.workflow_links = WorkflowLinks(
        version_activity_workflow_id=session_id
    )

    # write the object to the registry
    friendly_format = py_to_dict(new_item)
    try:
        write_registry_dynamo_db_entry_raw(
            registry_item=friendly_format,
            config=config
        )
    # Raise 500 if something goes wrong
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to write updated item including workflow session id to registry. Aborting. Contact administrator. Error {e}."
        )

    # return the session id
    return session_id
