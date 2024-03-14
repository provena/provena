from helpers.keycloak_helpers import get_oidc_service_token
import json
from dependencies.secret_cache import secret_cache
from SharedInterfaces.DataStoreAPI import *
import boto3  # type: ignore
from helpers.aws_helpers import create_policy_document, S3CredentialPaths
import urllib
import requests
from config import Config


def generate_read_write_paths(s3_location: S3Location, write: bool) -> S3CredentialPaths:
    """
    
    Generates a set of resource paths at different access levels suitable for inclusion in an IAM S3 policy.
    
    Requires knowing the base location of the dataset and the bucket name (in the S3Location object).
    
    If write is True, additional actions are allowed in the resource list to allow writing bucket files.
     
    read/write access to be granted.
    
    Returns a collection of 
    
    - read
    - write 
    - list
    
    Resource URI paths suitable for direct inclusion in a IAM policy document as
    s3 resource paths.
    
    NOTE noting that list access is provided for the whole bucket - this is so
    that the sync operation works in the AWS CLI.

    Args:
        s3_location (S3Location): The dataset location in bucket
        write (bool): Write access? else read only

    Returns:
        S3CredentialPaths: Collection of resource URIs at read/write/list level
    """
    # Generate the resource URIs required for read and write
    base_dataset_path = f"arn:aws:s3:::{s3_location.bucket_name}/{s3_location.path}".rstrip(
        '/')

    # This enables downloading of specific bucket files
    read_resource_uris = [
        base_dataset_path,
        base_dataset_path + "/",
        base_dataset_path + "/*"
    ]

    # Which resources to grant read/write to
    write_resource_uris = []

    if write:
        write_resource_uris.extend(
            [
                base_dataset_path,
                base_dataset_path + "/",
                base_dataset_path + "/*"
            ])

    # and bucket wide list operations for syncing note this means that someone
    # can list all files but they can't download them

    # NOTE this is required because using the S3 CLI will fail if the user
    # cannot list files across the whole bucket during SYNC operation
    bucket_path = f"arn:aws:s3:::{s3_location.bucket_name}"
    list_resource_uris = [
        bucket_path,
        bucket_path + "/*"
    ]

    return S3CredentialPaths(
        read_uris=read_resource_uris,
        write_uris=write_resource_uris,
        list_uris=list_resource_uris
    )


def call_sts_oidc_service(session_name: str, s3_location: S3Location, write: bool, config: Config) -> Credentials:
    """    call_sts_oidc_service
        Uses the oidc service keycloak account to act on behalf of the user 
        to generate federated identities with dynamic policies based on the s3
        bucket that is being accessed. 

        Arguments
        ----------
        session_name : str
            The name of the console session 
        s3_location : S3Location
            The bucket location to generate tailored access against
        write : bool
            Is this write level - true = r/w, false = r

        Returns
        -------
         : Credentials
            The credentials object from sts assume role with web identity.

        Raises
        ------
        Exception
            If STS call fails
        Exception
            If STS response is empty

        See Also (optional)
        --------

        Examples (optional)
        --------
    """

    resource_paths = generate_read_write_paths(
        s3_location=s3_location, write=write)

    policy_document = create_policy_document(
        s3_paths=resource_paths
    )

    # Get OIDC compatible token from keycloak
    token = get_oidc_service_token(
        secret_cache=secret_cache,
        config=config
    )

    # Create AWS client
    client = boto3.client('sts')

    # Try to call assume role
    # This relies on the role ARN trusting web
    # identities with the right aud
    try:
        response = client.assume_role_with_web_identity(
            RoleArn=config.OIDC_SERVICE_ROLE_ARN,
            RoleSessionName=session_name,
            WebIdentityToken=token,
            Policy=policy_document,
            DurationSeconds=config.SERVICE_SESSION_DURATION_SECONDS
        )
    except Exception as e:
        raise Exception(f"AWS STS call failed - error: {e}")

    try:
        assert response['Credentials']['SecretAccessKey']
    except:
        raise Exception(
            f"STS call succeeded but no credentials were present. Response: {response}")

    # assuming everything went well, unpack and return the credentials
    creds = response['Credentials']
    return Credentials(
        aws_access_key_id=creds['AccessKeyId'],
        aws_secret_access_key=creds['SecretAccessKey'],
        aws_session_token=creds['SessionToken'],
        expiry=creds['Expiration']
    )


def create_console_session(aws_credentials: Credentials, session_duration: int, aws_issuer: str, destination_url: str) -> str:
    """    create_console_session

        The AWS sample code at the URL below to hit the 
        federation endpoint with a carefully crafted 
        query string which embeds the credentials. This endpoint
        responds with a sign in token which can be embedded into 
        a URL and opened in the browser.

        Arguments
        ----------
        aws_credentials : Credentials
            The active AWS credentials
        session_duration : int
            The duration of access required - up to 12 hours max
        aws_issuer : str
            The auth issuer e.g. auth.your.domain
        destination_url : str
            Where should the link, once clicked, direct the user?

        Returns
        -------
         : str
            Fully signed URL

        See Also (optional)
        --------

        Examples (optional)
        --------
    """
    # from https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_providers_enable-console-custom-url.html#STSConsoleLink_programPython

    # Construct url components
    url_credentials = {}
    url_credentials['sessionId'] = aws_credentials.aws_access_key_id
    url_credentials['sessionKey'] = aws_credentials.aws_secret_access_key
    url_credentials['sessionToken'] = aws_credentials.aws_session_token
    json_string_with_temp_credentials = json.dumps(url_credentials)

    # Step 4. Make request to AWS federation endpoint to get sign-in token. Construct the parameter string with
    # the sign-in action request, a 12-hour session duration, and the JSON document with temporary credentials
    # as parameters.
    request_parameters = "?Action=getSigninToken"
    request_parameters += f"&SessionDuration={session_duration}"

    def quote_plus_function(s: str) -> str:
        return urllib.parse.quote_plus(s)

    request_parameters += "&Session=" + \
        quote_plus_function(json_string_with_temp_credentials)
    request_url = "https://signin.aws.amazon.com/federation" + request_parameters

    r = requests.get(request_url)

    # Returns a JSON document with a single element named SigninToken.
    signin_token = json.loads(r.text)

    # Step 5: Create URL where users can use the sign-in token to sign in to
    # the console. This URL must be used within 15 minutes after the
    # sign-in token was issued.
    request_parameters = "?Action=login"
    request_parameters += f"&Issuer={aws_issuer}"
    request_parameters += "&Destination=" + \
        quote_plus_function(destination_url)
    request_parameters += "&SigninToken=" + signin_token["SigninToken"]
    request_url = "https://signin.aws.amazon.com/federation" + request_parameters

    # Return sign in token URL
    return request_url
