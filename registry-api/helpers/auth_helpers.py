from SharedInterfaces.RegistryAPI import *
from SharedInterfaces.AuthAPI import *
from KeycloakFastAPI.Dependencies import User
from dependencies.dependencies import user_is_admin
from config import Config
import requests
from fastapi import HTTPException
from helpers.dynamo_helpers import get_auth_entry, write_auth_table_entry
from helpers.keycloak_helpers import get_service_token
from dependencies.dependencies import secret_cache


def get_item_from_auth_table(id: str, config: Config) -> AuthTableEntry:
    """

    Fetches the specified item from the auth table.

    Parses into the AuthTableEntry model.

    Parameters
    ----------
    id : str
        The id of the record
    config : Config
        The API config

    Returns
    -------
    AuthTableEntry
        The parsed entry

    Raises
    ------
    HTTPException
        Managed HTTP exception for known errors
    """
    # get the entry
    try:
        entry_raw = get_auth_entry(id=id, config=config)
    except KeyError as e:
        raise HTTPException(
            status_code=500,
            detail=f"The specified item ({id=}) is missing an authorisation configuration. No access granted."
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An error occured while accessing the auth database, error: {e}."
        )

    # parse the entry
    try:
        parsed = AuthTableEntry.parse_obj(entry_raw)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"The auth entry was not a valid authorisation object, parse failure. Error: {e}."
        )

    return parsed


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


def get_proxy_user_groups(user: User, config: Config) -> List[UserGroupMetadata]:
    """

    Uses the registry API service account to make an admin request fetching the users groups from the Auth API.

    This is required because we may not have an active token for the user in proxy context so need to get the relevant group info as service account instead.

    Parameters
    ----------
    user : User
        The user which includes the proxy username
    config : Config
        API Config

    Returns
    -------
    List[UserGroupMetadata]
        List of groups the user is a part of 

    Raises
    ------
    HTTPException
        managed http exception
    """
    # get the service account token to make
    # request on behalf of user
    token = get_service_token(secret_cache, config=config)

    # service token
    headers = {
        'Authorization': f'Bearer {token}'
    }

    # username from the user (proxy username)
    params = {
        'username': user.username
    }

    # make a call to the admin version of list user membership auth api endpoint
    endpoint = config.auth_api_endpoint + "/groups/admin/list_user_membership"

    response = requests.get(
        url=endpoint,
        params=params,
        headers=headers
    )

    # check the response succeeds
    if response.status_code != 200:
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected non 200 ({response.status_code}) response code from proxied user group auth API request!"
        )
    try:
        parsed_response = ListUserMembershipResponse.parse_obj(response.json())
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to parse the response from the Auth API. Cannot grant access."
        )

    if not parsed_response.status.success:
        raise HTTPException(
            status_code=500,
            detail=f"Auth API responded but noted success False. No access granted. Details: {parsed_response.status.details}."
        )

    if parsed_response.groups is None:
        raise HTTPException(
            status_code=500,
            detail=f"Auth API responded with success but didn't include the groups payload. No access granted."
        )

    # Successful
    return parsed_response.groups


def get_user_groups(user: User, config: Config) -> List[UserGroupMetadata]:
    """

    Uses the users token to make an auth api request listing the user group's.

    Parameters
    ----------
    user : User
        The user incl token
    config : Config
        The API config

    Returns
    -------
    List[UserGroupMetadata]
        List of user's groups

    Raises
    ------
    HTTPException
        Managed http exception 
    """
    # get the auth headers using the users token
    auth_headers = proxied_request(user)

    # make a call to the list user membership auth api endpoint
    endpoint = config.auth_api_endpoint + "/groups/user/list_user_membership"

    response = requests.get(
        url=endpoint,
        headers=auth_headers
    )

    # check the response succeeds
    if response.status_code != 200:
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected non 200 ({response.status_code}) response code from user group auth API request!"
        )
    try:
        parsed_response = ListUserMembershipResponse.parse_obj(response.json())
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to parse the response from the Auth API. Cannot grant access."
        )

    if not parsed_response.status.success:
        raise HTTPException(
            status_code=500,
            detail=f"Auth API responded but noted success False. No access granted. Details: {parsed_response.status.details}."
        )

    if parsed_response.groups is None:
        raise HTTPException(
            status_code=500,
            detail=f"Auth API responded with success but didn't include the groups payload. No access granted."
        )

    # Successful
    return parsed_response.groups


def default_access_settings(username: str, default_roles: Roles) -> AccessSettings:
    """

    Generates default access settings for owner based on default roles provided.

    Parameters
    ----------
    username : str
        The username
    default_roles : Roles
        List of default roles

    Returns
    -------
    AccessSettings
        The complete access settings
    """
    return AccessSettings(
        owner=username,
        general=default_roles,
        groups={}
    )


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


def determine_user_access(access_settings: AccessSettings, user_group_ids: Set[str]) -> Roles:
    """

    Combines the general access provided in the resource access settings +
    merges any groups the user is in with the associated group permissions to
    create a set of roles the user can take against the resource.

    Parameters
    ----------
    access_settings : AccessSettings
        The access settings for the resource
    user_group_ids : Set[str]
        List of groups the user is in

    Returns
    -------
    Roles
        The list of roles the user can take
    """
    user_roles: Set[str] = set([])

    # grant all general roles
    user_roles.update(access_settings.general)

    # iterate through group assigned roles
    for group_id, roles in access_settings.groups.items():
        # if user is a part of the group
        if group_id in user_group_ids:
            # merge the access roles with this group's allocation
            user_roles.update(roles)

    return list(user_roles)


def seed_auth_configuration(id: str, username: str, config: Config, default_roles: Roles, base_settings: Optional[AccessSettings] = None) -> None:
    """

    Creates a default auth configuration table entry, then places it into the
    auth table.

    Can also use an existing settings object (potentially from a different
    resource/owner), and update it to fit this item. This is used in the
    version workflow to generate the revised item based on access of the
    previous.

    Parameters
    ----------
    id : str
        The id of the item to seed

    username : str
        Owner username

    config : Config
        API config

    default_roles : Roles
        Default set of roles

    base_settings : Optional[AccessSettings], optional
        The existing settings, by default None

    Raises
    ------
    HTTPException
        Managed HTTP exception
    """
    # generate the default access settings - starting point
    settings: AccessSettings

    if base_settings is not None:
        settings = base_settings
        # overwrite the owner - versioning can change this!
        settings.owner = username
    else:
        settings = default_access_settings(
            username=username,
            default_roles=default_roles
        )

    # double check there isn't a record already
    entry_exists = True

    # this should fail
    try:
        entry = get_auth_entry(id=id, config=config)
    except KeyError:
        entry_exists = False

    if entry_exists:
        raise HTTPException(
            status_code=500,
            detail=f"While seeding an item, the auth configuration already existed for that handle. Unexpected state. {id=}. Contact admin."
        )

    # now create the record
    auth_entry = AuthTableEntry(
        id=id,
        access_settings=settings
    )

    # write
    try:
        write_auth_table_entry(
            auth_entry=auth_entry,
            config=config
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to write seed auth configuration, error: {e}. Contact admin."
        )


def special_permission_check(user: User, special_roles: Roles) -> bool:
    """

    Checks if the user contains any of a set of special roles. 

    Also enables access if the user is an admin - as determined by user_is_admin
    function.

    Parameters
    ----------
    user : User
        The user object - includes token with roles parsed
    special_roles : Roles
        The list of acceptable roles

    Returns
    -------
    bool
        True iff access granted
    """
    # only grants access if the user has ANY of the special roles OR is an admin
    user_roles = user.roles

    # check admin
    if user_is_admin(user):
        return True

    return evaluate_user_access(user_roles=user_roles, acceptable_roles=special_roles)


def get_user_link(user: User, config: Config) -> Optional[str]:
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
    params = {'username': user.username}

    # make a call to the admin version of list user membership auth api endpoint
    endpoint = config.auth_api_endpoint + "/link/user/lookup"

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
