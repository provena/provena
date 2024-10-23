from ProvenaInterfaces.AsyncJobModels import *
from EcsSqsPythonTools.Types import *
from EcsSqsPythonTools.Settings import JobBaseSettings
from EcsSqsPythonTools.Workflow import parse_job_specific_payload
from helpers.util import py_to_dict
from helpers.workflows import register_and_lodge_provenance, lodge_provenance
from helpers.entity_validators import RequestStyle, ServiceAccountProxy
from helpers.validate_model_run_record import validate_model_run_record
from helpers.prov_helpers import produce_create_prov_document, produce_version_prov_document
from helpers.job_api_helpers import launch_generic_job
from helpers.graph_db_helpers import upload_prov_document
from ProvenaInterfaces.AsyncJobAPI import *
from config import Config
from typing import cast
import asyncio

ProvJobHandler = CallbackFunc


def generate_failed_job(error: str) -> CallbackResponse:
    """

    Generates a formatted callback response with failed state.

    Used to simplify reporting errors.

    Parameters
    ----------
    error : str
        The error message

    Returns
    -------
    CallbackResponse
        Properly formatted callback response.
    """
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


def model_run_lodge_only_handler(payload: JobSnsPayload, settings: JobBaseSettings) -> CallbackResponse:
    """
    Handles lodging the provenance graph data ONLY
    into Neo4j for the specified model run record.

    Optionally validates the record as specified in the job payload.

    This involves creating the prov document and lodging the record.

    Parameters
    ----------
    payload : JobSnsPayload
        The payload which validates against subtype payload from map
    settings : JobBaseSettings
        The job settings

    Returns
    -------
    CallbackResponse
        The response indicating success/failure and reporting result payload
    """
    print(f"Running model run lodge handler.")

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
        model_run_lodge_payload = cast(ProvLodgeModelRunLodgeOnlyPayload, parse_job_specific_payload(
            payload=payload, job_sub_type=JobSubType.MODEL_RUN_LODGE_ONLY))
    except Exception as e:
        return generate_failed_job(error=f"Failed to parse job payload from the event. Error: {e}.")

    print(f"Parsed specific payload: {model_run_lodge_payload}")

    # What request style to use for lodge? We want to use the service account +
    # proxy endpoint on behalf of user
    request_style = RequestStyle(
        user_direct=None,
        service_account=ServiceAccountProxy(
            on_behalf_username=payload.username,
            direct_service=False
        )
    )

    if model_run_lodge_payload.revalidate:
        print("Validating record contents as specified in job payload.")
        # We need to validate here
        try:
            valid, error_message = asyncio.run(validate_model_run_record(
                record=model_run_lodge_payload.record,
                request_style=request_style,
                config=config,
            ))
        except Exception as e:
            return generate_failed_job(
                error=f"Unhandled exception during model run validation. Error: {e}."
            )

        if not valid:
            assert error_message
            return CallbackResponse(
                status=JobStatus.FAILED,
                info=f"Failed to validate an entity's ID in the record, error: {error_message}."
            )

        print("Record validation successful.")
    else:
        print("Validation skipped as specified in job payload.")

    print("Starting lodge of provenance payload.")
    try:
        record_info = asyncio.run(lodge_provenance(
            handle_id=model_run_lodge_payload.model_run_record_id,
            record=model_run_lodge_payload.record,
            config=config,
            request_style=request_style
        ))
    except Exception as e:
        return generate_failed_job(
            error=f"An error occurred while lodging the provenance record. Error: {e}."
        )

    return CallbackResponse(
        status=JobStatus.SUCCEEDED,
        info=None,
        result=py_to_dict(
            ProvLodgeModelRunResult(
                record=record_info
            )
        )
    )


def model_run_lodge_handler(payload: JobSnsPayload, settings: JobBaseSettings) -> CallbackResponse:
    """
    Handles registering in the registry AND lodging the provenance graph data
    into Neo4j for the specified model run record.

    Optionally validates the record as specified in the job payload.

    This involves creating the prov document and lodging the record.

    Parameters
    ----------
    payload : JobSnsPayload
        The payload which validates against subtype payload from map
    settings : JobBaseSettings
        The job settings

    Returns
    -------
    CallbackResponse
        The response indicating success/failure and reporting result payload
    """
    print(f"Running model run lodge handler.")

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
        model_run_lodge_payload = cast(ProvLodgeModelRunPayload, parse_job_specific_payload(
            payload=payload, job_sub_type=JobSubType.MODEL_RUN_PROV_LODGE))
    except Exception as e:
        return generate_failed_job(error=f"Failed to parse job payload from the event. Error: {e}.")

    print(f"Parsed specific payload: {model_run_lodge_payload}")

    # What request style to use for lodge? We want to use the service account +
    # proxy endpoint on behalf of user
    request_style = RequestStyle(
        user_direct=None,
        service_account=ServiceAccountProxy(
            on_behalf_username=payload.username,
            direct_service=False
        )
    )

    if model_run_lodge_payload.revalidate:
        print("Validating record contents as specified in job payload.")
        # We need to validate here
        try:
            valid, error_message = asyncio.run(validate_model_run_record(
                record=model_run_lodge_payload.record,
                request_style=request_style,
                config=config,
            ))
        except Exception as e:
            return generate_failed_job(
                error=f"Unhandled exception during model run validation. Error: {e}."
            )

        if not valid:
            assert error_message
            return CallbackResponse(
                status=JobStatus.FAILED,
                info=f"Failed to validate an entity's ID in the record, error: {error_message}."
            )

        print("Record validation successful.")
    else:
        print("Validation skipped as specified in job payload.")

    print("Starting lodge of provenance payload.")
    try:
        record_info = asyncio.run(register_and_lodge_provenance(
            record=model_run_lodge_payload.record,
            config=config,
            request_style=request_style
        ))
    except Exception as e:
        return generate_failed_job(
            error=f"An error occurred while lodging the provenance record. Error: {e}."
        )

    return CallbackResponse(
        status=JobStatus.SUCCEEDED,
        info=None,
        result=py_to_dict(
            ProvLodgeModelRunResult(
                record=record_info
            )
        )
    )


def creation_lodge_handler(payload: JobSnsPayload, settings: JobBaseSettings) -> CallbackResponse:
    """
    Handles lodging the provenance graph data into Neo4j for the specified
    Create activity.

    This involves creating the prov document and lodging the record.

    The registry item already exists at this stage.

    Parameters
    ----------
    payload : JobSnsPayload
        The payload which validates against subtype payload from map

    settings : JobBaseSettings
        The job settings

    Returns
    -------
    CallbackResponse
        The response indicating success/failure and reporting result payload
    """
    print(f"Running creation lodge handler.")

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
        creation_lodge_payload = cast(ProvLodgeCreationPayload, parse_job_specific_payload(
            payload=payload, job_sub_type=JobSubType.LODGE_CREATE_ACTIVITY))
    except Exception as e:
        return generate_failed_job(error=f"Failed to parse job payload from the event. Error: {e}.")

    print(f"Parsed specific payload: {creation_lodge_payload}")

    # Create prov document
    print("Converting details into prov document.")
    try:
        document = produce_create_prov_document(
            created_item_id=creation_lodge_payload.created_item_id,
            created_item_subtype=creation_lodge_payload.created_item_subtype,
            create_activity_id=creation_lodge_payload.creation_activity_id,
            agent_id=creation_lodge_payload.linked_person_id
        )
    except Exception as e:
        return generate_failed_job(error=f"Failed to convert lodge details into a Provenance document. Error: {e}.")

    # Upload to the DB
    print("Uploading to DB.")
    try:
        upload_prov_document(
            id=creation_lodge_payload.creation_activity_id,
            prov_document=document,
            config=config
        )
    except Exception as e:
        return generate_failed_job(error=f"Failed to lodge generated prov document into the Provenance graph database. Error: {e}.")

    print("Job complete.")
    return CallbackResponse(
        status=JobStatus.SUCCEEDED,
        info=None,
        result=py_to_dict(
            ProvLodgeCreationResult(
            )
        )
    )


def model_run_batch_submit_handler(payload: JobSnsPayload, settings: JobBaseSettings) -> CallbackResponse:
    """
    This is a helper job which takes a list of model run records, and launches a
    job to create and lodge each record.

    Uses the Job API to request the jobs.

    This batch fanout means we can scale to handling a large number of batch
    registered records without any concern for timeouts/synchronous operation
    issues.

    The first launch requests a batch id, subsequent launches use this batch id
    so they are associated in an indexed collection.

    Parameters
    ----------
    payload : JobSnsPayload
        The payload which validates against subtype payload from map

    settings : JobBaseSettings
        The job settings

    Returns
    -------
    CallbackResponse
        The response indicating success/failure and reporting result payload
    """
    print(f"Running model run batch submit handler.")

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
        batch_submit_payload = cast(ProvLodgeBatchSubmitPayload, parse_job_specific_payload(
            payload=payload, job_sub_type=JobSubType.MODEL_RUN_BATCH_SUBMIT))
    except Exception as e:
        return CallbackResponse(
            status=JobStatus.FAILED,
            info=f"Failed to parse job payload from the event. Error: {e}."
        )

    print(f"Parsed specific payload: {batch_submit_payload}")

    # Spinoff new jobs, noting the first gets a batch id, the rest reference it
    first = True
    batch_id: Optional[str] = None
    for record in batch_submit_payload.records:
        launch_payload = AdminLaunchJobRequest(
            username=payload.username,
            job_type=JobType.PROV_LODGE,
            job_sub_type=JobSubType.MODEL_RUN_PROV_LODGE,
            job_payload=py_to_dict(ProvLodgeModelRunPayload(
                record=record,
                revalidate=True
            )),
            request_batch_id=first,
            add_to_batch=batch_id
        )

        response = asyncio.run(launch_generic_job(
            payload=launch_payload,
            config=config
        ))

        # update batch id
        if first:
            batch_id = response.batch_id

            if batch_id is None:
                err = f"Job API should have responded with a batch ID on first launch... Aborting."
                return CallbackResponse(
                    status=JobStatus.FAILED,
                    info=f"An error occurred: {err}"
                )

            # batch ID all good
            first = False

    assert batch_id
    return CallbackResponse(
        status=JobStatus.SUCCEEDED,
        info=f"Successfully distributed batch jobs to queue.",
        result=py_to_dict(
            ProvLodgeBatchSubmitResult(
                batch_id=batch_id
            )
        )
    )


def version_lodge_handler(payload: JobSnsPayload, settings: JobBaseSettings) -> CallbackResponse:
    """
    Handles lodging the provenance document for the Version activity
    into the neo4j prov graph.

    Parameters
    ----------
    payload : JobSnsPayload
        The payload which validates against subtype payload from map

    settings : JobBaseSettings
        The job settings

    Returns
    -------
    CallbackResponse
        The response indicating success/failure and reporting result payload
    """
    print(f"Running version lodge handler.")

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
        version_payload = cast(ProvLodgeVersionPayload, parse_job_specific_payload(
            payload=payload, job_sub_type=JobSubType.LODGE_VERSION_ACTIVITY))
    except Exception as e:
        return generate_failed_job(error=f"Failed to parse job payload from the event. Error: {e}.")

    print(f"Parsed specific payload: {version_payload}")

    # Create prov document
    print("Converting details into prov document.")
    try:
        document = produce_version_prov_document(
            from_version_id=version_payload.from_version_id,
            to_version_id=version_payload.to_version_id,
            version_activity_id=version_payload.version_activity_id,
            item_subtype=version_payload.item_subtype,
            agent_id=version_payload.linked_person_id
        )
    except Exception as e:
        return generate_failed_job(error=f"Failed to convert lodge details into a Provenance document. Error: {e}.")

    # Upload to the DB
    print("Uploading to DB.")
    try:
        upload_prov_document(
            id=version_payload.version_activity_id,
            prov_document=document,
            config=config
        )
    except Exception as e:
        return generate_failed_job(error=f"Failed to lodge generated prov document into the Provenance graph database. Error: {e}.")

    print("Job complete.")
    return CallbackResponse(
        status=JobStatus.SUCCEEDED,
        info=None,
        result=py_to_dict(
            ProvLodgeVersionResult(
            )
        )
    )


# Map from the job sub type to the prov handler
PROV_LODGE_HANDLER_MAP: Dict[JobSubType, ProvJobHandler] = {
    JobSubType.PROV_LODGE_WAKE_UP: wake_up_handler,
    JobSubType.MODEL_RUN_PROV_LODGE: model_run_lodge_handler,
    JobSubType.MODEL_RUN_LODGE_ONLY: model_run_lodge_only_handler,
    JobSubType.MODEL_RUN_BATCH_SUBMIT: model_run_batch_submit_handler,
    JobSubType.LODGE_CREATE_ACTIVITY: creation_lodge_handler,
    JobSubType.LODGE_VERSION_ACTIVITY: version_lodge_handler
}


def job_dispatcher(payload: JobSnsPayload, settings: JobBaseSettings) -> CallbackResponse:
    # dispatch into function
    print(f"Dispatching into handler.")
    handler = PROV_LODGE_HANDLER_MAP[payload.job_sub_type]

    print(f"Running dispatched function")
    return handler(payload, settings)
