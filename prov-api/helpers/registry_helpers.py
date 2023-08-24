from SharedInterfaces.RegistryAPI import *
from helpers.async_requests import *
from config import Config, get_settings
from helpers.keycloak_helpers import get_service_token
from dependencies.dependencies import secret_cache
from fastapi import HTTPException, Depends
import json


async def seed_model_run(proxy_username: str, config: Config) -> SeededItem:
    """    seed_model_run
        Performs a seed operation against the /registry/activity/model_run/seed
        endpoint which will produce an empty model run which can then be later 
        updated to include the provenance document and other details. Returns 
        the SeededItem object.

        Returns
        -------
         : SeededItem
            The response seed item.

        Raises
        ------
        HTTPException
            Non 200 response
        HTTPException
            Unparsable response
        HTTPException
            Status.success == false
        HTTPException
            Item is None

        See Also (optional)
        --------

        Examples (optional)
        --------
    """
    # Setup request
    assert config.registry_api_endpoint
    # ! Uses proxy endpoint so needs to pass through username of user
    endpoint = config.registry_api_endpoint + \
        '/registry/activity/model_run/proxy/seed'
    params: Dict[str, str] = {
        "proxy_username": proxy_username
    }
    token = get_service_token(secret_cache, config)

    # make request
    response = await async_post_request(
        endpoint=endpoint,
        token=token,
        params=params,
        # No body for this post
        json_body=None
    )

    # check status code
    if response.status_code != 200:
        raise HTTPException(
            status_code=500,
            detail=f"Got status code {response.status_code} when trying to seed model run identity!"
        )

    # get JSON content
    json_content = response.json()

    # parse as seed response
    try:
        seed_response = ModelRunSeedResponse.parse_obj(json_content)
    except:
        raise HTTPException(
            status_code=500,
            detail="Response from registry API model run seed was unparsable!"
        )

    # check status of response
    if not seed_response.status.success:
        raise HTTPException(
            status_code=500,
            detail=f"Response from registry API model run was parsed but had success==False with details: {seed_response.status.details}"
        )

    # everything appears ok, check item is present
    if not seed_response.seeded_item:
        raise HTTPException(
            status_code=500,
            detail="Seed response from registry API for model run was successful but had None as the item!"
        )

    # everything is A-okay
    assert seed_response.seeded_item
    return seed_response.seeded_item


async def update_model_run_in_registry(
    proxy_username: str,
    model_run_id: str,
    model_run_domain_info: ModelRunDomainInfo,
    config: Config,
    reason: Optional[str] = None,
) -> ItemModelRun:
    """    update_model_run_in_registry
        Given the model run id and the new domain info object
        will use the registry API /update endpoint to update 
        the information held in the model run record.

        Arguments
        ----------
        model_run_id : str
            The handle ID for the model run record
        model_run_domain_info : ModelRunDomainInfo
            The new domain info to inject to the /update endpoint

        Returns
        -------
         : ItemModelRun
            The returned model run record

        Raises
        ------
        HTTPException
            If an error occurs in any of the API interactions

        See Also (optional)
        --------

        Examples (optional)
        --------
    """
    # Setup request
    assert config.registry_api_endpoint
    # use proxy update endpoint
    endpoint = config.registry_api_endpoint + \
        '/registry/activity/model_run/proxy/update'
    params: Dict[str, str] = {
        'id': model_run_id,
        'proxy_username': proxy_username
    }

    # supply a reason if provided - this annotates the update history of the item
    if reason:
        params['reason'] = reason

    token = get_service_token(secret_cache, config)
    json_body = json.loads(model_run_domain_info.json(exclude_none=True))

    # make request
    response = await async_put_request(
        endpoint=endpoint,
        token=token,
        params=params,
        json_body=json_body
    )

    # check status code
    if response.status_code != 200:
        raise HTTPException(
            status_code=500,
            detail=f"Got status code {response.status_code} when trying to update model run with completed document! Details: {response.text}"
        )

    # get JSON content
    json_content = response.json()

    # parse as status response
    try:
        status_response = StatusResponse.parse_obj(json_content)
    except:
        raise HTTPException(
            status_code=500,
            detail="Response from registry API model run update was unparsable!"
        )

    # check status of response
    if not status_response.status.success:
        raise HTTPException(
            status_code=500,
            detail=f"Response from registry API model run was parsed but had success==False with details: {status_response.status.details}"
        )

    # update was successful - provide the object back
    endpoint = config.registry_api_endpoint + '/registry/activity/model_run/fetch'
    params: Dict[str, str] = {
        'id': model_run_id,
    }

    response = await async_get_request(
        endpoint=endpoint,
        token=token,
        params=params
    )

    # check status code
    if response.status_code != 200:
        raise HTTPException(
            status_code=500,
            detail=f"Got status code {response.status_code} when trying to fetch updated model run!"
        )

    # get JSON content
    json_content = response.json()

    # parse as fetch response
    try:
        fetch_response = ModelRunFetchResponse.parse_obj(json_content)
    except:
        raise HTTPException(
            status_code=500,
            detail="Response from registry API model run fetch was unparsable!"
        )

    # check status of response
    if not fetch_response.status.success:
        raise HTTPException(
            status_code=500,
            detail=f"Response from registry API model run fetch was parsed but had success==False with details: {fetch_response.status.details}"
        )

    # check that item is not a seed
    if fetch_response.item_is_seed:
        raise HTTPException(
            status_code=500,
            detail="Response from registry API model run fetch included seed object despite allow seed being false."
        )

    # check item is present
    if not fetch_response.item:
        raise HTTPException(
            status_code=500,
            detail=f"Despite registry model run fetch API returning successfully, there was no item included."
        )

    # check instance type
    if not isinstance(fetch_response.item, ItemModelRun):
        raise HTTPException(
            status_code=500,
            detail=f"Despite registry model run fetch API returning successfully, the item was not a valid ItemModelRun instance."
        )

    return fetch_response.item
