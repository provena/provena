from ProvenaInterfaces.AsyncJobModels import *
from EcsSqsPythonTools.Types import *
from EcsSqsPythonTools.Settings import JobBaseSettings
from EcsSqsPythonTools.Workflow import parse_job_specific_payload
from ProvenaInterfaces.AsyncJobAPI import *
from typing import cast
from config import Config
from helpers.util import py_to_dict
from helpers.email_helpers import *

JobHandler = CallbackFunc


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


def send_email_handler(payload: JobSnsPayload, settings: JobBaseSettings) -> CallbackResponse:
    print(f"Running send email job")

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
        job_specific_payload = cast(EmailSendEmailPayload, parse_job_specific_payload(
            payload=payload, job_sub_type=JobSubType.SEND_EMAIL))
    except Exception as e:
        return generate_failed_job(error=f"Failed to parse job payload from the event. Error: {e}.")

    print(f"Parsed specific payload: {job_specific_payload}")

    # Validating email address
    print(f"Validating email address: {job_specific_payload.email_to}.")
    valid = validate_email(email=job_specific_payload.email_to)

    if not valid:
        print(f"Validation failed.")
        return generate_failed_job(
            error=f"Email failed validation against regex: {email_regex}. No email sent."
        )

    # Sending email
    print(f"Attempting to send email to {job_specific_payload.email_to}.")
    try:
        send_email(
            to_address=job_specific_payload.email_to,
            email_subject=job_specific_payload.subject,
            email_body=job_specific_payload.body,
            config=config
        )
    except Exception as e:
        return generate_failed_job(
            error=f"An exception occurred while trying to send the email, exception: {e}."
        )

    print("Finished sending email")
    return CallbackResponse(
        status=JobStatus.SUCCEEDED,
        info=None,
        result=py_to_dict(
            EmailSendEmailResult(
            )
        )
    )


HANDLER_MAP: Dict[JobSubType, JobHandler] = {
    JobSubType.EMAIL_WAKE_UP: wake_up_handler,
    JobSubType.SEND_EMAIL: send_email_handler
}


def job_dispatcher(payload: JobSnsPayload, settings: JobBaseSettings) -> CallbackResponse:
    # dispatch into function
    print(f"Dispatching into handler.")
    handler = HANDLER_MAP[payload.job_sub_type]

    print(f"Running dispatched function")
    return handler(payload, settings)
