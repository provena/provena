from ProvenaInterfaces.AsyncJobModels import *
from EcsSqsPythonTools.Types import *
from EcsSqsPythonTools.Settings import JobBaseSettings
from EcsSqsPythonTools.Workflow import parse_job_specific_payload
from ProvenaInterfaces.AsyncJobAPI import *
from typing import cast
from config import Config
from helpers.util import py_to_dict

JobHandler = CallbackFunc


def generate_failed_job(error: str) -> CallbackResponse:
    return CallbackResponse(
        status=JobStatus.FAILED,
        info=f"Job failed, err: {error}.",
        result=None
    )


# def example_handler(payload: JobSnsPayload, settings: JobBaseSettings) -> CallbackResponse:
#    # TODO Destub
#    print(f"Running JOB NAME HERE job")
#
#    print("Parsing full API config from environment.")
#    try:
#        config = Config()
#    except Exception as e:
#        return CallbackResponse(
#            status=JobStatus.FAILED,
#            info=f"Failed to parse job configuration from the environment. Error: {e}."
#        )
#    print("Successfully parsed environment config.")
#
#    print(f"Parsing job specific payload")
#    try:
#        job_specific_payload = cast(PAYLOAD_MODEL_HERE, parse_job_specific_payload(
#            payload=payload, job_sub_type=JobSubType.JOB_SUB_TYPE_HERE))
#    except Exception as e:
#        return generate_failed_job(error=f"Failed to parse job payload from the event. Error: {e}.")
#
#    print(f"Parsed specific payload: {job_specific_payload}")
#
#    # DO WORK HERE
#
#    return CallbackResponse(
#        status=JobStatus.SUCCEEDED,
#        info=None,
#        result=py_to_dict(
#            RESULT_MODEL_HERE(
#            )
#        )
#    )


HANDLER_MAP: Dict[JobSubType, JobHandler] = {
    # JobSubType.JOB_SUB_TYPE_HERE: example_handler
}


def job_dispatcher(payload: JobSnsPayload, settings: JobBaseSettings) -> CallbackResponse:
    # dispatch into function
    print(f"Dispatching into handler.")
    handler = HANDLER_MAP[payload.job_sub_type]

    print(f"Running dispatched function")
    return handler(payload, settings)
