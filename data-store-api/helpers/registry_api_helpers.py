from config import Config
import requests
import json
from helpers.keycloak_helpers import get_service_token
from aws_secretsmanager_caching import SecretCache  # type: ignore
from fastapi import HTTPException
from SharedInterfaces.RegistryAPI import *
from typing import Dict
from dependencies.dependencies import User


def generate_service_token_for_registry_api(secret_cache: SecretCache, config: Config) -> str:
    # get service token - this includes special roles which the registry expects
    try:
        token = get_service_token(
            secret_cache=secret_cache,
            config=config
        )
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail="Failed to generate service token - error: {e}. Contact an administrator."
        )

    return token


def validate_dataset_in_registry(collection_format: CollectionFormat, user: User, config: Config) -> Optional[str]:
    """
    validate_dataset_in_registry 
    Parameters
    ----------
    collection_format: CollectionFormat
        The data to validate - need to wrap in DatasetDomainInfo
    config : Config
        API config
    Returns
    -------
    """
    # wrap the payload
    payload = DatasetDomainInfo(
        display_name=collection_format.dataset_info.name,
        collection_format=collection_format,
        s3=S3Location(bucket_name="fake", path="fake", s3_uri="fake")
    )

    # endpoint
    postfix = "/registry/entity/dataset/validate"
    validate_endpoint = config.REGISTRY_API_ENDPOINT + postfix

    # make the seed request - pass through user token
    token = user.access_token
    headers = {
        'Authorization': 'Bearer ' + token
    }

    try:
        response = requests.post(
            url=validate_endpoint,
            json=json.loads(payload.json(exclude_none=True)),
            headers=headers
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to call validation endpoint in registry before seeding. Error: {e}."
        )

    # check the response code
    if response.status_code != 200:
        # try to get more details
        details = "Unknown"

        try:
            details = response.json()['detail']
        except Exception:
            None

        if response.status_code == 401:
            raise HTTPException(
                status_code=401,
                detail=f"Dataset validation failed, received not authorised. Status code: {response.status_code}. Details: {details}."
            )

        raise HTTPException(
            status_code=500,
            detail=f"Unexpected non 200 status code in dataset validation process. Status code: {response.status_code}. Details: {details}."
        )

    # 200 response code - parse as the status response
    try:
        status_response = StatusResponse.parse_obj(response.json())
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to parse the response from registry API as a Status Response, error: {e}."
        )

    # return either the validation issue or None if OK
    if not status_response.status.success:
        return status_response.status.details
    else:
        return None


def seed_dataset_in_registry(proxy_username: str, secret_cache: SecretCache, config: Config) -> str:
    """
    seed_dataset_in_registry 

    Acts in the data-store-api service role to seed a new dataset registry entity.

    Returns the ID of the seeded item.

    Parameters
    ----------
    secret_cache : SecretCache
        The secret cache to use to pull the secret info
    config : Config
        API config

    Returns
    -------
    str
        The handle ID of the seeded item in the registry

    """
    # get service token - this includes special roles which the registry expects
    token = generate_service_token_for_registry_api(
        secret_cache=secret_cache,
        config=config
    )

    # endpoint
    postfix = "/registry/entity/dataset/proxy/seed"
    seed_endpoint = config.REGISTRY_API_ENDPOINT + postfix

    # make the seed request
    headers = {
        'Authorization': 'Bearer ' + token
    }

    # params - add the proxy username
    params = {
        'proxy_username': proxy_username
    }

    try:
        response = requests.post(
            url=seed_endpoint,
            params=params,
            headers=headers
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Minting dataset request failed, request error: {e}."
        )

    # check the response code
    if response.status_code != 200:
        # try to get more details
        details = "Unknown"

        try:
            details = response.json()['detail']
        except Exception:
            None

        if response.status_code == 401:
            raise HTTPException(
                status_code=401,
                detail=f"Dataset minting failed, not authorised. Status code: {response.status_code}. Details: {details}."
            )

        raise HTTPException(
            status_code=500,
            detail=f"Unexpected non 200 status code in dataset minting process. Status code: {response.status_code}. Details: {details}."
        )

    # 200 response code - parse as the mint response
    try:
        seed_response = GenericSeedResponse.parse_obj(response.json())
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to parse the response from registry API as a seed item, error: {e}."
        )

    # parsed succesfully
    if not seed_response.status.success:
        raise HTTPException(
            status_code=500,
            detail=f"The registry API responded with status success False during dataset mint. Details: {seed_response.status.details}."
        )

    # all is well - get the ID
    if seed_response.seeded_item is None:
        raise HTTPException(
            status_code=500,
            detail=f"The registry API responded with status success but didn't include the seeded item. Contact an administrator."
        )

    return seed_response.seeded_item.id


def update_dataset_in_registry(proxy_username: str, domain_info: DatasetDomainInfo, id: str, secret_cache: SecretCache, reason: str, config: Config) -> None:
    # get service token - this includes special roles which the registry expects
    token = generate_service_token_for_registry_api(
        secret_cache=secret_cache,
        config=config
    )

    # endpoint
    postfix = "/registry/entity/dataset/proxy/update"
    update_endpoint = config.REGISTRY_API_ENDPOINT + postfix
    json_payload = json.loads(domain_info.json(exclude_none=True))
    params = {
        'id': id,
        'proxy_username': proxy_username,
        'reason': reason
    }

    # make the seed request
    headers = {
        'Authorization': 'Bearer ' + token
    }

    try:
        response = requests.put(
            url=update_endpoint,
            json=json_payload,
            params=params,
            headers=headers
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Updating dataset failed, request error: {e}."
        )

    # check the response code
    if response.status_code != 200:
        # try to get more details
        details = "Unknown"

        try:
            details = response.json()['detail']
        except Exception:
            None

        if response.status_code == 401:
            raise HTTPException(
                status_code=401,
                detail=f"Dataset metadata update failed, not authorised. Status code: {response.status_code}. Details: {details}."
            )

        raise HTTPException(
            status_code=500,
            detail=f"Unexpected non 200 status code in dataset update process. Status code: {response.status_code}. Details: {details}."
        )

    # 200 response code - parse as the update response
    try:
        update_response = StatusResponse.parse_obj(response.json())
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to parse the response from registry API as a status response, error: {e}."
        )

    # parsed succesfully
    if not update_response.status.success:
        raise HTTPException(
            status_code=500,
            detail=f"The registry API responded with status success False during dataset update. Details: {update_response.status.details}."
        )


def revert_dataset_in_registry(proxy_username: str, revert_request: ItemRevertRequest, secret_cache: SecretCache, config: Config) -> None:
    # get service token - this includes special roles which the registry expects
    token = generate_service_token_for_registry_api(
        secret_cache=secret_cache,
        config=config
    )

    # endpoint
    postfix = "/registry/entity/dataset/proxy/revert"
    revert_endpoint = config.REGISTRY_API_ENDPOINT + postfix
    json_payload = json.loads(revert_request.json(exclude_none=True))
    params = {'proxy_username': proxy_username}

    # make the seed request
    headers = {
        'Authorization': 'Bearer ' + token
    }

    try:
        response = requests.put(
            url=revert_endpoint,
            json=json_payload,
            params=params,
            headers=headers
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Restoring dataset failed, request error: {e}."
        )

    # check the response code
    if response.status_code != 200:
        # try to get more details
        details = "Unknown"

        try:
            details = response.json()['detail']
        except Exception:
            None

        if response.status_code == 401:
            raise HTTPException(
                status_code=401,
                detail=f"Dataset metadata revert failed, not authorised. Status code: {response.status_code}. Details: {details}."
            )

        raise HTTPException(
            status_code=500,
            detail=f"Unexpected non 200 status code in dataset revert process. Status code: {response.status_code}. Details: {details}."
        )

    # 200 response code - parse as the update response
    try:
        revert_response = ItemRevertResponse.parse_obj(response.json())
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to parse the response from registry API as a status response, error: {e}."
        )

    # parsed succesfully
    if not revert_response.status.success:
        raise HTTPException(
            status_code=500,
            detail=f"The registry API responded with status success False during dataset metadata revert. Details: {revert_response.status.details}."
        )


def proxied_request(user: User) -> Dict[str, str]:
    # creates a header for use in requests
    return {
        'Authorization': 'Bearer ' + user.access_token
    }


def user_fetch_dataset_from_registry(id: str, config: Config, user: User) -> DatasetFetchResponse:
    # endpoint
    postfix = "/registry/entity/dataset/fetch"
    fetch_endpoint = config.REGISTRY_API_ENDPOINT + postfix

    # make the seed request
    headers = proxied_request(user)

    params = {
        'id': id
    }

    try:
        response = requests.get(
            url=fetch_endpoint,
            headers=headers,
            params=params
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Fetching dataset failed, request error: {e}."
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
                detail=f"Registry did not grant access to the dataset. Details: {details}."
            )

        raise HTTPException(
            status_code=500,
            detail=f"Unexpected non 200 status code in dataset update process. Status code: {response.status_code}. Details: {details}."
        )

    # 200 response code - parse as the fetch response
    try:
        fetch_response = DatasetFetchResponse.parse_obj(response.json())
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to parse the fetch response from the registry, error: {e}."
        )

    # parsed succesfully
    if not fetch_response.status.success:
        raise HTTPException(
            status_code=400,
            detail=f"The registry API responded with status success False during dataset fetching. Details: {fetch_response.status.details}."
        )

    # check item exists
    if not fetch_response.item:
        raise HTTPException(
            status_code=500,
            detail=f"The registry API responded with success but didn't provide an item."
        )

    if fetch_response.item_is_seed:
        raise HTTPException(
            status_code=400,
            detail=f"The requested dataset is an incomplete item (seed item). It is not a valid dataset."
        )

    assert isinstance(fetch_response.item, ItemDataset)

    # return the item
    return fetch_response


def user_list_datasets_from_registry(config: Config, user: User, list_request: NoFilterSubtypeListRequest) -> DatasetListResponse:
    # endpoint
    postfix = "/registry/entity/dataset/list"
    list_endpoint = config.REGISTRY_API_ENDPOINT + postfix

    # make the seed request
    headers = proxied_request(user)

    # completed request payload
    full_request = SubtypeListRequest(
        filter_by=None,
        sort_by=list_request.sort_by,
        pagination_key=list_request.pagination_key,
        page_size=list_request.page_size
    )

    try:
        response = requests.post(
            url=list_endpoint,
            headers=headers,
            json=json.loads(full_request.json())
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Listing datasets failed, request error: {e}."
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
                detail=f"Registry did not grant access to the list endpoint. Details: {details}."
            )

        raise HTTPException(
            status_code=500,
            detail=f"Unexpected non 200 status code in dataset update process. Status code: {response.status_code}. Details: {details}."
        )

    # 200 response code - parse as the list response
    try:
        list_response = DatasetListResponse.parse_obj(response.json())
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to parse the list response from the registry, error: {e}."
        )

    # parsed succesfully
    if not list_response.status.success:
        raise HTTPException(
            status_code=400,
            detail=f"The registry API responded with status success False during dataset listing. Details: {list_response.status.details}."
        )

    # check item exists
    if list_response.items is None:
        raise HTTPException(
            status_code=500,
            detail=f"The registry API responded with success but didn't provide a list of items."
        )

    return list_response
