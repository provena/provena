from typing import TypeVar, Type, Union
from fastapi import HTTPException
from SharedInterfaces.RegistryModels import *
from SharedInterfaces.RegistryAPI import *
from dependencies.dependencies import secret_cache, User
from helpers.keycloak_helpers import get_service_token
from helpers.async_requests import async_get_request
from config import Config
from aiocache import cached, Cache  # type: ignore
from dataclasses import dataclass

CACHE_TTL = 60
CACHE_TYPE = Cache.MEMORY

"""
==========================
REGISTRY ENTITY VALIDATION
==========================
"""

FetchResponseBaseType = TypeVar(
    "FetchResponseBaseType", bound=GenericFetchResponse)
ItemBaseType = TypeVar(
    "ItemBaseType", bound=ItemBase)


@dataclass
class ServiceAccountProxy:
    on_behalf_username: Optional[str]
    direct_service: bool


@dataclass
class RequestStyle:
    user_direct: Optional[User]
    service_account: Optional[ServiceAccountProxy]


async def untyped_validate_by_id(
    id: str,
    base_endpoint: str,
    request_style: RequestStyle,
    config: Config
) -> Union[str, Dict[str, Any]]:

    standard_endpoint: str = f"{base_endpoint}/fetch"
    proxy_endpoint: str = f"{base_endpoint}/proxy/fetch"
    using_proxy: bool = False
    endpoint = standard_endpoint
    username: Optional[str] = None

    # proxy mode
    if request_style.service_account is not None:
        # get service token
        token = get_service_token(secret_cache, config)

        # service account - are we using it directly or proxying?
        if request_style.service_account.direct_service:
            # use the token directly, standard fetch endpoint
            endpoint = standard_endpoint
            using_proxy = False
        else:
            username = request_style.service_account.on_behalf_username
            assert username
            # use a service token with proxy endpoint
            endpoint = proxy_endpoint
            using_proxy = True
    else:
        # non proxy mode
        assert request_style.user_direct
        # use user token - just pass through
        token = request_style.user_direct.access_token

        using_proxy = False
        endpoint = standard_endpoint

    # make request
    params = {
        'id': id
    }
    # add username if proxy endpoint and username is being supplied
    if using_proxy:
        assert username is not None
        params['username'] = username

    # Make request
    try:
        fetch_response = await async_get_request(
            endpoint=endpoint, token=token, params=params
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Registry API failed to respond - validation unsuccessful. Exception: {e}.")

    # check the status of the response
    status_code = fetch_response.status_code
    if status_code != 200:
        # try and get details then raise HTTPException
        try:
            detail = fetch_response.json()['detail']
        except:
            detail = "Unknown details - cannot parse."

        # authorisation failure case
        if status_code == 401:
            raise HTTPException(
                status_code=401,
                detail=f"Registry API denied access to resource: {status_code}. Error: {detail}"
            )
        else:
            raise HTTPException(
                status_code=500,
                detail=f"Registry API responded with non 200 code: {status_code}. Error: {detail}"
            )

    # 200 code meaning that parse model will be valid
    try:
        model_response: UntypedFetchResponse = UntypedFetchResponse.parse_obj(
            fetch_response.json())
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Tried to parse successful response from registry API but failed. Parse error {e}."
        )

    # We now have a parsed model response
    if model_response.status.success:
        # success indicates we should have a fetched item
        if not model_response.item:
            raise HTTPException(
                status_code=500,
                detail=f"Registry API fetch responded with success=true but did not provide item in payload!"
            )
        return model_response.item
    else:
        # Something went wrong - return validation issue
        return f"Failed to retrieve item with details: {model_response.status.details}."


async def validate_by_id(
    id: str,
    base_endpoint: str,
    fetch_response_class: Type[FetchResponseBaseType],
    request_style: RequestStyle,
    config: Config
) -> Union[str, ItemBase, SeededItem]:
    """    validate_by_id
        Calls the registry fetch API for the given id 
        at the given registry endpoint. It makes sure 
        no status code errors are indicated and parses
        the response as the provided fetch response 
        pydantic model. The response is a string with 
        error reason if error, the item model type if
        the full item was found, or a seeded item if
        the item is in the registry but is in the seed
        state.

        Arguments
        ----------
        id : str
            The handle ID to fetch
        base_endpoint : str
            The endpoint to fetch at - the base e.g. .../entity/model
        fetch_response_class : Type[FetchResponseBaseType]
            The class for the response

        Returns
        -------
         : Union[str, ItemBase, SeededItem]
            Str = error
            ItemBase = the full item model type
            SeededItem = the seeded item

        Raises
        ------
        HTTPException
            Registry API didn't respond
        HTTPException
            Non 200 response code
        HTTPException
            Parse failure
        HTTPException
            No item in payload

        See Also (optional)
        --------

        Examples (optional)
        --------
    """

    standard_endpoint: str = f"{base_endpoint}/fetch"
    proxy_endpoint: str = f"{base_endpoint}/proxy/fetch"
    using_proxy: bool = False
    endpoint = standard_endpoint
    username: Optional[str] = None

    # proxy mode
    if request_style.service_account is not None:
        # get service token
        token = get_service_token(secret_cache, config)

        # service account - are we using it directly or proxying?
        if request_style.service_account.direct_service:
            # use the token directly, standard fetch endpoint
            endpoint = standard_endpoint
            using_proxy = False
        else:
            username = request_style.service_account.on_behalf_username
            assert username
            # use a service token with proxy endpoint
            endpoint = proxy_endpoint
            using_proxy = True
    else:
        # non proxy mode
        assert request_style.user_direct
        # use user token - just pass through
        token = request_style.user_direct.access_token

        using_proxy = False
        endpoint = standard_endpoint

    # make request
    params = {
        'id': id
    }
    # add username if proxy endpoint and username is being supplied
    if using_proxy:
        assert username is not None
        params['username'] = username

    # Make request
    try:
        fetch_response = await async_get_request(
            endpoint=endpoint, token=token, params=params
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Registry API failed to respond - validation unsuccessful. Exception: {e}.")

    # check the status of the response
    status_code = fetch_response.status_code
    if status_code != 200:
        # try and get details then raise HTTPException
        try:
            detail = fetch_response.json()['detail']
        except:
            detail = "Unknown details - cannot parse."

        # authorisation failure case
        if status_code == 401:
            raise HTTPException(
                status_code=401,
                detail=f"Registry API denied access to resource: {status_code}. Error: {detail}"
            )
        else:
            raise HTTPException(
                status_code=500,
                detail=f"Registry API responded with non 200 code: {status_code}. Error: {detail}"
            )

    # 200 code meaning that parse model will be valid
    try:
        model_response: FetchResponseBaseType = fetch_response_class.parse_obj(
            fetch_response.json())
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Tried to parse successful response from registry API but failed. Parse error {e}."
        )

    # We now have a parsed model response
    if model_response.status.success:
        # success indicates we should have a fetched item
        if not model_response.item:
            raise HTTPException(
                status_code=500,
                detail=f"Registry API fetch responded with success=true but did not provide item in payload!"
            )
        return model_response.item
    else:
        # Something went wrong - return validation issue
        return f"Failed to retrieve item with details: {model_response.status.details}."


@cached(ttl=CACHE_TTL, cache=CACHE_TYPE)
async def validate_dataset_template_id(id: str, request_style: RequestStyle, config: Config) -> Union[ItemDatasetTemplate, SeededItem, str]:
    """    validate_dataset_template_id
        Given a DatasetTemplate ID will fetch from registry and ensure it is valid

        Arguments
        ----------
        id : str
            The handle ID

        Returns
        -------
         : Union[ItemDatasetTemplate, SeededItem, str]
            Returns full item, seeded item or error string.

        See Also (optional)
        --------

        Examples (optional)
        --------
    """
    # endpoint to target
    postfix = "/registry/entity/dataset_template"
    endpoint = f"{config.registry_api_endpoint}{postfix}"

    error_or_value = await validate_by_id(
        id=id,
        base_endpoint=endpoint,
        fetch_response_class=DatasetTemplateFetchResponse,
        request_style=request_style,
        config=config
    )

    if isinstance(error_or_value, str):
        return error_or_value
    if isinstance(error_or_value, SeededItem):
        return error_or_value
    elif isinstance(error_or_value, ItemBase):
        return ItemDatasetTemplate(**error_or_value.dict())


@cached(ttl=CACHE_TTL, cache=CACHE_TYPE)
async def validate_model_id(id: str, request_style: RequestStyle, config: Config) -> Union[ItemModel, SeededItem, str]:
    """    validate_model_id
        Given a model ID will fetch from registry and ensure it is valid

        Arguments
        ----------
        id : str
            The handle ID

        Returns
        -------
         : Union[ItemModel, SeededItem, str]
            Returns full item, seeded item or error string.

        See Also (optional)
        --------

        Examples (optional)
        --------
    """
    # endpoint to target
    postfix = "/registry/entity/model"
    endpoint = f"{config.registry_api_endpoint}{postfix}"

    error_or_value = await validate_by_id(
        id=id,
        base_endpoint=endpoint,
        fetch_response_class=ModelFetchResponse,
        request_style=request_style,
        config=config
    )

    if isinstance(error_or_value, str):
        return error_or_value
    if isinstance(error_or_value, SeededItem):
        return error_or_value
    elif isinstance(error_or_value, ItemBase):
        return ItemModel(**error_or_value.dict())


@cached(ttl=CACHE_TTL, cache=CACHE_TYPE)
async def validate_model_run_workflow_template(id: str, request_style: RequestStyle, config: Config) -> Union[ItemModelRunWorkflowTemplate, SeededItem, str]:
    """    validate_model_run_workflow_template
        Given a model run workflow definition ID will fetch from registry 
        and ensure it is valid

        Arguments
        ----------
        id : str
            The handle ID

        Returns
        -------
         : Union[ItemModelRunWorkflowTemplate, SeededItem, str]
            Returns full item, seeded item or error string.

        See Also (optional)
        --------

        Examples (optional)
        --------
    """
    # endpoint to target
    postfix = "/registry/entity/model_run_workflow"
    endpoint = f"{config.registry_api_endpoint}{postfix}"

    error_or_value = await validate_by_id(
        id=id,
        base_endpoint=endpoint,
        fetch_response_class=ModelRunWorkflowTemplateFetchResponse,
        config=config,
        request_style=request_style
    )

    if isinstance(error_or_value, str):
        return error_or_value
    if isinstance(error_or_value, SeededItem):
        return error_or_value
    elif isinstance(error_or_value, ItemBase):
        return ItemModelRunWorkflowTemplate(**error_or_value.dict())


@cached(ttl=CACHE_TTL, cache=CACHE_TYPE)
async def validate_person_id(id: str, request_style: RequestStyle, config: Config) -> Union[ItemPerson, SeededItem, str]:
    """    validate_person_id
        Validates a person agent by ID.

        Arguments
        ----------
        id : str
            The handle ID.

        Returns
        -------
         : Union[ItemPerson, SeededItem, str]
            ItemPerson if full model, 
            SeededItem if seed, 
            str if error

        See Also (optional)
        --------

        Examples (optional)
        --------
    """
    # endpoint to target
    postfix = "/registry/agent/person"
    endpoint = f"{config.registry_api_endpoint}{postfix}"

    error_or_value = await validate_by_id(
        id=id,
        base_endpoint=endpoint,
        fetch_response_class=PersonFetchResponse,
        config=config,
        request_style=request_style
    )

    if isinstance(error_or_value, str):
        return error_or_value
    if isinstance(error_or_value, SeededItem):
        return error_or_value
    elif isinstance(error_or_value, ItemBase):
        return ItemPerson(**error_or_value.dict())


@cached(ttl=CACHE_TTL, cache=CACHE_TYPE)
async def validate_organisation_id(id: str, request_style: RequestStyle, config: Config) -> Union[ItemOrganisation, SeededItem, str]:
    """    validate_organisation_id
        Validates an organisation agent by ID

        Arguments
        ----------
        id : str
            The handle ID

        Returns
        -------
         : Union[ItemOrganisation, SeededItem, str]
            ItemOrganisation if full record
            SeededItem if seed
            Str if error

        See Also (optional)
        --------

        Examples (optional)
        --------
    """
    # endpoint to target
    postfix = "/registry/agent/organisation"
    endpoint = f"{config.registry_api_endpoint}{postfix}"

    error_or_value = await validate_by_id(
        id=id,
        base_endpoint=endpoint,
        fetch_response_class=OrganisationFetchResponse,
        config=config,
        request_style=request_style
    )

    if isinstance(error_or_value, str):
        return error_or_value
    if isinstance(error_or_value, SeededItem):
        return error_or_value
    elif isinstance(error_or_value, ItemBase):
        return ItemOrganisation(**error_or_value.dict())


@cached(ttl=CACHE_TTL, cache=CACHE_TYPE)
async def validate_datastore_id(id: str, request_style: RequestStyle, config: Config) -> Union[str, SeededItem, ItemDataset]:
    """    validate_dateset_id
        Validates a dataset by handle ID.

        This method uses the data store API to fetch the dataset
        metadata as validation. 

        Arguments
        ----------
        id : str
            The handle ID for the dataset

        Returns
        -------
         : Union[str, RegistryItem]
            str if error occurred with message why
            RegistryItem if the item was found 

        Raises
        ------
        HTTPException
            Data store API failed to respond
        HTTPException
            Non 200 code
        HTTPException
            Parsing failure
        HTTPException
            No item in payload

        See Also (optional)
        --------

        Examples (optional)
        --------
    """
    # endpoint to target
    postfix = "/registry/entity/dataset"
    endpoint = f"{config.registry_api_endpoint}{postfix}"

    error_or_value = await validate_by_id(
        id=id,
        base_endpoint=endpoint,
        fetch_response_class=DatasetFetchResponse,
        config=config,
        request_style=request_style
    )

    if isinstance(error_or_value, str):
        return error_or_value
    if isinstance(error_or_value, SeededItem):
        return error_or_value
    elif isinstance(error_or_value, ItemBase):
        return ItemDataset(**error_or_value.dict())


@cached(ttl=CACHE_TTL, cache=CACHE_TYPE)
async def validate_registry_generic_id(id: str, request_style: RequestStyle, config: Config) -> Union[Dict[str, Any], str]:
    # endpoint to target
    postfix = "/registry/general"
    endpoint = f"{config.registry_api_endpoint}{postfix}"

    error_or_value = await untyped_validate_by_id(
        id=id,
        base_endpoint=endpoint,
        config=config,
        request_style=request_style
    )

    if isinstance(error_or_value, str):
        return error_or_value
    if isinstance(error_or_value, Dict):
        return error_or_value


@cached(ttl=CACHE_TTL, cache=CACHE_TYPE)
async def unknown_validator(id: str, config: Config, request_style: RequestStyle) -> None:
    """    unknown_validator
        Given an id, will check the registry generic fetch 
        endpoint and the data store API to see if this item
        exists *somewhere*. If not, it will throw a HTTP 400
        exception with the errors from both APIs. 

        If it succeeds without exception then the item exists.

        This can be used to pre-validate a starting point in a 
        graph lineage query.

        Arguments
        ----------
        id : str
            The id to lookup

        Returns
        -------

        See Also (optional)
        --------

        Examples (optional)
        --------
    """
    # validate starting ID using registry fetch API or data store fetch
    registry_err = ""
    general_item: Union[Dict[str, Any], str] = await validate_registry_generic_id(
        id=id,
        config=config,
        request_style=request_style
    )
    valid = isinstance(general_item, Dict)

    if not valid:
        raise HTTPException(
            status_code=500,
            detail=f"The provided id {id} was not a valid registry\
                item. Error from registry lookup: {registry_err}."
        )
