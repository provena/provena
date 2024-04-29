from ProvenaInterfaces.AuthAPI import *
from ProvenaInterfaces.RegistryModels import IdentifiedResource
from KeycloakFastAPI.Dependencies import User
from config import Config
import requests
from fastapi import HTTPException
from aws_secretsmanager_caching import SecretCache  # type: ignore
from typing import Dict, Optional

from helpers.keycloak_helpers import get_service_token


def proxied_request(user: User) -> Dict[str, str]:
    """

    Formats a header dict using the user's Bearer token

    Parameters
    ----------
    user : User
        The user object

    Returns
    -------
    Dict[str, str]
        headers
    """
    # creates a header for use in requests
    return {
        'Authorization': 'Bearer ' + user.access_token
    }


def get_user_link(user: User,  config: Config, username: Optional[str] = None) -> Optional[str]:
    """

    Fetches the user linked person using the link service.

    Returns optional string based on response.

    Parameters
    ----------
    user : User
        The user to fetch for
    config : Config
        The API config

    Returns
    -------
    Optional[str]
        The person ID if linked

    Raises
    ------
    HTTPException
        Managed http exception
    """
    # pass through user token
    headers = proxied_request(user=user)

    # username from the user (proxy username)
    params = {'username': username or user.username}

    # make a call to the admin version of list user membership auth api endpoint
    endpoint = config.AUTH_API_ENDPOINT + "/link/user/lookup"

    response = requests.get(
        url=endpoint,
        params=params,
        headers=headers
    )

    # check the response succeeds
    if response.status_code != 200:
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected non 200 ({response.status_code}) response code from when querying username Person link service! Error text {response.text}."
        )
    try:
        parsed_response = UserLinkUserLookupResponse.parse_obj(response.json())
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to parse the response from the Auth API user link service."
        )

    # Successfully looked up - return the possible ID
    return parsed_response.person_id


def get_usernames_from_id(
    person_id: IdentifiedResource,
    config: Config,
    secret_cache: SecretCache
) -> List[str]:

    headers = {
        'Authorization': 'Bearer ' + get_service_token(secret_cache=secret_cache, config=config)
    }

    params = {'person_id': person_id}

    # make a call to the admin version of list user membership auth api endpoint
    endpoint = config.AUTH_API_ENDPOINT + "/link/admin/reverse_lookup"

    response = requests.get(
        url=endpoint,
        params=params,
        headers=headers
    )

    # check OK
    if response.status_code != 200:
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected non 200 ({response.status_code}) response code from when querying username Person link service! Error text {response.text}."
        )
    try:
        parsed_response = UserLinkReverseLookupResponse.parse_obj(
            response.json())
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to parse the response from the Auth API user link service."
        )

    # Successfully looked up - return the possible ID
    return parsed_response.usernames


def evaluate_user_access(user_roles: Roles, acceptable_roles: Roles) -> bool:
    """

    Determines if a user has access to some operation by checking if ANY of the
    acceptable roles is present in the user's roles

    Parameters
    ----------
    user_roles : Roles
        The user roles

    acceptable_roles : Roles
        The list of acceptable roles

    Returns
    -------
    bool
        True iff access granted
    """
    for acceptable in acceptable_roles:
        if acceptable in user_roles:
            return True

    return False


def evaluate_user_access_all(user_roles: Roles, required_roles: Roles) -> bool:
    """

    Determines if a user has access to some operation by checking if ALL of the
    required roles are present in the user's roles

    Parameters
    ----------
    user_roles : Roles
        The user roles

    required_roles : Roles
        The list of acceptable roles

    Returns
    -------
    bool
        True iff access granted
    """
    for acceptable in required_roles:
        if acceptable not in user_roles:
            return False

    return True
