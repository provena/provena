
from KeycloakFastAPI.Dependencies import *
from config import Config
from helpers.request_table_helpers import generate_status_change_email_text
from ProvenaInterfaces.AuthAPI import *
from ProvenaInterfaces.AsyncJobModels import EmailSendEmailPayload
from helpers.job_api_helpers import submit_send_email_job
import re

from helpers.access_report_helpers import *

# From https://www.geeksforgeeks.org/check-if-email-address-valid-or-not-in-python/
email_regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'


def validate_email(email: str) -> bool:
    """    validate_email
        Ensure that an email appears valid before sending an 
        email to the address.

        Arguments
        ----------
        email : str
            The email address to validate

        Returns
        -------
         : bool
            true iff valid 

        See Also (optional)
        --------

        Examples (optional)
        --------
    """
    # Check that email matches regex
    return (re.fullmatch(email_regex, email) != None)


async def send_access_diff_email(
    email_to: str,
    difference_report: AccessReport,
    user: User,
    request_entry: RequestAccessTableItem,
    config: Config
) -> str:
    """    send_access_diff_email
        Given the difference report and user information, will send an email 
        to the configured from/to email address which describes the required 
        access changes.
        
        Uses the email job system to send this email.

        Arguments
        ----------
        difference_report : AccessReport
            The difference access report
        user : User
            The user 
        request_entry : RequestAccessTableItem
            The request access item added to the table 
            so we can link to the request username/id

        Raises
        ------
        Exception
            Failure to lodge send email job

        See Also (optional)
        --------

        Examples (optional)
        --------
    """
    # Generate the email text
    email_content = generate_email_text_from_diff(
        difference_report=difference_report,
        user=user,
        request_entry=request_entry,
        config=config
    )
    try:
        session_id = await submit_send_email_job(
            # Use service account username here
            username=None,
            config=config,
            payload=EmailSendEmailPayload(
                email_to=email_to,
                subject=email_content.subject,
                body=email_content.body,
                reason="Alerting sys admins of access request."
            )
        )
        return session_id
    except Exception as e:
        raise HTTPException(status_code=500,
                            detail=f"Failed to dispatch email job. Error: {e}.")


async def send_status_change_email(
    email_address: str,
    username: str,
    original_status: RequestStatus,
    new_status: RequestStatus,
    request_entry: RequestAccessTableItem,
    config: Config
) -> str:
    """    send_status_change_email
        Sends an email address containing status and role request information to the 
        user that has requested changes.

        Arguments
        ----------
        email_address : str
            Recipient's email adress
        username : str
            Username of user to send status change to.
        original_status : RequestStatus
            The original status
        new_status : RequestStatus
            The new status
        request_entry : RequestAccessTableItem
            Current request entry for the table containing roles

        Raises
        ------
        Exception
            If fails to send email with SSL connection

        See Also (optional)
        --------

        Examples (optional)
        --------
    """
    # Generate the email text
    email_content = generate_status_change_email_text(
        username=username,
        original_status=original_status,
        new_status=new_status,
        request_entry=request_entry
    )

    try:
        session_id = await submit_send_email_job(
            # Use the user's username here - they can see their address/contents
            username=username,
            config=config,
            payload=EmailSendEmailPayload(
                email_to=email_address,
                subject=email_content.subject,
                body=email_content.body,
                reason="Updating user of change in access request status."
            )
        )
        return session_id
    except Exception as e:
        raise HTTPException(status_code=500,
                            detail=f"Failed to dispatch email job. Error: {e}.")
