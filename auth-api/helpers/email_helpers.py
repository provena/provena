
from KeycloakFastAPI.Dependencies import *
from config import Config
from helpers.request_table_helpers import generate_status_change_email_text
from SharedInterfaces.AuthAPI import *
from models.email import *
import boto3  # type: ignore
import json
import smtplib
import ssl
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


def get_email_connection_profile(config: Config) -> EmailConnectionProfile:
    """    get_email_connection_profile
        Uses the email connection secret ARN from aws sm to 
        pull the username, password, port etc for sending 
        emails.

        Returns
        -------
         : EmailConnectionProfile
            The connection profile

        Raises
        ------
        Exception
            Connection error/secret pull failure raises an exception
        Exception
            Parsing failure from secret -> connection profile raises error

        See Also (optional)
        --------

        Examples (optional)
        --------
    """
    # TODO cache this
    # https://docs.aws.amazon.com/secretsmanager/latest/userguide/retrieving-secrets_cache-python.html
    # For now just retrieving each time as required
    client = boto3.client('secretsmanager')

    # Get secret value
    try:
        response = client.get_secret_value(
            SecretId=config.email_secret_arn
        )
    except Exception as e:
        raise Exception(
            f"Failed to pull email connection profile secret from AWS SM with error: {e}")

    # Parse connection profile
    try:
        connection_profile = EmailConnectionProfile.parse_obj(
            json.loads(response['SecretString']))
    except Exception as e:
        raise Exception(
            f"Failed to parse the email connection profile from the AWS secret.")

    # Everything goes as planned, return the connection profile
    return connection_profile


def send_access_diff_email(
    difference_report: AccessReport,
    user: User,
    request_entry: RequestAccessTableItem,
    config: Config
) -> None:
    """    send_access_diff_email
        Given the difference report and user information, will send an email 
        to the configured from/to email address which describes the required 
        access changes.

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
            Failure to create SSL context
        Exception
            Failure to login to SMTP server 
        Exception
            Failure to send email

        See Also (optional)
        --------

        Examples (optional)
        --------
    """
    # Generate the email text
    email_text = generate_email_text_from_diff(
        difference_report=difference_report,
        user=user,
        request_entry=request_entry,
        config=config
    )

    # Get the email creds
    connection_profile = get_email_connection_profile(
        config=config
    )

    # Setup connection
    context = ssl.create_default_context()

    # Send email
    try:
        server = smtplib.SMTP(
            connection_profile.smtp_server, connection_profile.port)
        server.starttls(context=context)
        server.login(connection_profile.email_from,
                     connection_profile.password.get_secret_value())
        server.sendmail(connection_profile.email_from,
                        connection_profile.email_to, email_text)
    except Exception as e:
        raise Exception(
            f"Failed to send email with SSL connection, port: {connection_profile.port},\
            server: {connection_profile.smtp_server},\
            username: {connection_profile.email_from}.\
            Error {e}.")
    finally:
        server.close()


def send_status_change_email(
    email_address: str,
    username: str,
    original_status: RequestStatus,
    new_status: RequestStatus,
    request_entry: RequestAccessTableItem,
    config: Config
) -> None:
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
    email_text = generate_status_change_email_text(
        username=username,
        original_status=original_status,
        new_status=new_status,
        request_entry=request_entry
    )

    # Get the email creds
    connection_profile = get_email_connection_profile(
        config=config
    )

    # Setup connection
    context = ssl.create_default_context()

    try:
        server = smtplib.SMTP(
            connection_profile.smtp_server, connection_profile.port)
        server.starttls(context=context)
        server.login(connection_profile.email_from,
                     connection_profile.password.get_secret_value())
        server.sendmail(connection_profile.email_from,
                        email_address, email_text)
    except Exception as e:
        raise Exception(
            f"Failed to send email with SSL connection, port: {connection_profile.port},\
            server: {connection_profile.smtp_server},\
            username: {connection_profile.email_from}.\
            Error {e}.")
    finally:
        server.close()
