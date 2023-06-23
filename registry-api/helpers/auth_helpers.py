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
    # creates a header for use in requests
    return {
        'Authorization': 'Bearer ' + user.access_token
    }


def get_proxy_user_groups(user: User, config: Config) -> List[UserGroupMetadata]:
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
    return AccessSettings(
        owner=username,
        general=default_roles,
        groups={}
    )


def evaluate_user_access(user_roles: Roles, acceptable_roles: Roles) -> bool:
    for acceptable in acceptable_roles:
        if acceptable in user_roles:
            return True

    return False


def determine_user_access(access_settings: AccessSettings, user_group_ids: Set[str]) -> Roles:
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


def seed_auth_configuration(id: str, username: str, config: Config, default_roles: Roles) -> None:
    # generate the default access settings - starting point
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
    # only grants access if the user has ANY of the special roles OR is an admin
    user_roles = user.roles

    # check admin
    if user_is_admin(user):
        return True

    # check special roles
    for possible_special_role in special_roles:
        if possible_special_role in user_roles:
            return True
    return False


def get_user_link(user: User, config: Config) -> Optional[str]:
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
