from config import Config
import requests
from fastapi import HTTPException
from ProvenaInterfaces.RegistryAPI import *
from typing import Dict
from KeycloakFastAPI.Dependencies import User


def proxied_request(user: User) -> Dict[str, str]:
    # creates a header for use in requests
    return {
        'Authorization': 'Bearer ' + user.access_token
    }


def user_fetch_person_auth_config_from_registry(id: str, config: Config, user: User) -> AccessSettings:
    # endpoint
    postfix = "/registry/agent/person/auth/configuration"
    auth_config_endpoint = config.registry_api_endpoint + postfix

    # make the seed request
    headers = proxied_request(user)
    params = {"id": id}

    try:
        response = requests.get(
            url=auth_config_endpoint,
            headers=headers,
            params=params,
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Fetching person auth config from registry failed, request error: {e}."
        )

    # check the response code
    if response.status_code != 200:
        # try to get more details
        details = "Unknown"

        try:
            details = response.json()['detail']
        except Exception:
            None

        # unauthorised
        if response.status_code == 401:
            raise HTTPException(
                status_code=401,
                detail=f"Registry did not grant access to the auth configuration for this person. Details: {details}."
            )

        raise HTTPException(
            status_code=500,
            detail=f"Unexpected non 200 status code in Registry person auth configuration fetch. Status code: {response.status_code}. Details: {details}."
        )

    # 200 response code - parse as the list response
    try:
        auth_config_response = AccessSettings.parse_obj(response.json())
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to parse the auth configuration fetch response from the registry, error: {e}."
        )

    # parsed succesfully
    return auth_config_response


def user_fetch_person_from_registry(id: str, config: Config, user: User) -> Union[ItemPerson, SeededItem]:
    # endpoint
    postfix = "/registry/agent/person/fetch"
    fetch_endpoint = config.registry_api_endpoint + postfix

    # make the seed request
    headers = proxied_request(user)
    params = {"id": id}

    try:
        response = requests.get(
            url=fetch_endpoint,
            headers=headers,
            params=params,
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Fetching person auth config from registry failed, request error: {e}."
        )

    # check the response code
    if response.status_code != 200:
        # try to get more details
        details = "Unknown"

        try:
            details = response.json()['detail']
        except Exception:
            None

        # unauthorised
        if response.status_code == 401:
            raise HTTPException(
                status_code=401,
                detail=f"Registry did not grant access to the person with id {id}. Details: {details}."
            )

        raise HTTPException(
            status_code=500,
            detail=f"Unexpected non 200 status code in Registry person {id=} fetch. Status code: {response.status_code}. Details: {details}."
        )

    # 200 response code - parse as the list response
    try:
        fetch_response = PersonFetchResponse.parse_obj(response.json())
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to parse the auth configuration fetch response from the registry, error: {e}."
        )

    # check status
    if not fetch_response.status.success:
        raise HTTPException(
            status_code=500,
            detail=f"Registry fetch response {id=} indicated status failure - details: {fetch_response.status.details}."
        )

    # check item is present
    if fetch_response.item is None:
        raise HTTPException(
            status_code=500,
            detail=f"Registry fetch response {id=} was missing the item."
        )

    return fetch_response.item
