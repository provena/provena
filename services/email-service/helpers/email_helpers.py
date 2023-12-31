import smtplib
import ssl
import re
from config import Config
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def generate_email_text(subject: str, body: str) -> str:
    msg = MIMEMultipart()
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain', 'utf-16'))
    return msg.as_string()


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


def send_email(to_address: str, email_subject: str, email_body: str, config: Config) -> None:
    # Generate email msg text containg body and subject info.
    email_text = generate_email_text(email_subject, email_body)

    # Setup connection
    context = ssl.create_default_context()

    # Send email
    try:
        server = smtplib.SMTP(
            config.smtp_server, config.port)
        server.starttls(context=context)
        server.login(config.email_from,
                     config.password.get_secret_value())
        server.sendmail(config.email_from,
                        to_address, email_text)
    except Exception as e:
        raise Exception(
            f"Failed to send email with SSL connection, port: {config.port},\
            server: {config.smtp_server},\
            username: {config.email_from}.\
            Error {e}.")
    finally:
        server.close()
