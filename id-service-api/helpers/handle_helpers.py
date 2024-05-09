from config import Config
from ProvenaInterfaces.HandleModels import *
from typing import Dict, Optional
from enum import Enum
from helpers.handle_templates import template_handle_request
import httpx
import logging
from fastapi import HTTPException
import xmltodict

# setup logger
logging.config.fileConfig('logging.conf', disable_existing_loggers=False)

# get logger for this module
logger_key = "handle_service"
logger = logging.getLogger(logger_key)

# 20 second timeout (instead of default 5) - this is very generous, test service
# seems to cold start/have very long response times sometimes
async_timeout = 20.0


def get_async_client() -> httpx.AsyncClient:
    """

    Sets up an async http client using httpx.

    Uses timeout from above configuration.

    Returns:
        httpx.AsyncClient: The client ready for async with context
    """
    return httpx.AsyncClient(timeout=async_timeout)


class HandleOperation(str, Enum):
    """
    HandleOperation 

    set of handle operations
    """

    MINT = "MINT"
    GET = "GET"
    LIST = "LIST"
    ADD_VALUE = "ADD_VALUE"
    ADD_VALUE_BY_INDEX = "ADD_VALUE_BY_INDEX"
    MODIFY_VALUE_BY_INDEX = "MODIFY_VALUE_BY_INDEX"
    REMOVE_VALUE_BY_INDEX = "REMOVE_VALUE_BY_INDEX"


# maps the handle operation to the postfix on the handle base endpoint
HANDLE_OP_POSTFIX_MAP: Dict[HandleOperation, str] = {
    HandleOperation.MINT: "mint",
    HandleOperation.GET: "getHandle",
    HandleOperation.LIST: "listHandles",
    HandleOperation.ADD_VALUE: "addValue",
    HandleOperation.ADD_VALUE_BY_INDEX: "addValueByIndex",
    HandleOperation.MODIFY_VALUE_BY_INDEX: "modifyValueByIndex",
    HandleOperation.REMOVE_VALUE_BY_INDEX: "deleteValueByIndex",
}

# check all ops have postfixes
for handle_op in HandleOperation:
    assert handle_op in HANDLE_OP_POSTFIX_MAP.keys()


def parse_error(response: httpx.Response) -> str:
    """
    parse_error 

    Tries to parse a non 200 OK response from the ARDC service to get an error
    message.

    Parameters
    ----------
    response : httpx.Response
        The requests response

    Returns
    -------
    str
        The error message
    """
    # TODO expand if we are having issues with uninformative error messages.
    default = "Cannot parse."
    error = default
    try:
        error = response.text
    except Exception:
        pass

    return error


def parse_xml_list(text: str) -> List[str]:
    """
    parse_xml_list 

    Parses XML text response from ARDC service to find a list of IDs from the
    listHandles endpoint.

    Parameters
    ----------
    text : str
        The XML text

    Returns
    -------
    List[str]
        The list of IDs

    Raises
    ------
    HTTPException
        If anything goes wrong 500 code with error
    """

    logging.debug(
        "Decoding XML response from ARDC listHandles service endpoint.")
    # setup handle fields
    ids: List[str] = []

    try:
        json_result = dict(xmltodict.parse(text))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Could not parse XML response from Handle Service. Exception: {e}."
        )
    try:
        # pull out response component
        response = json_result['response']

        # success if present
        success = response['@type']
        if 'success' in success:
            if 'identifiers' in response.keys():
                response_ids = response['identifiers']['identifier']
                # pull out ids list and add
                for id_obj in response_ids:
                    id = id_obj['@handle']
                    ids.append(id)
        else:
            error_message = response['message']['#text']
            raise HTTPException(
                status_code=500,
                detail=f"Error was reported by ARDC handle service, contents: {error_message}."
            )
        assert id
    except HTTPException as he:
        # handled
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected parsing error when parsing ARDC handle service XML response. Exception {e}."
        )

    return ids


def parse_xml(text: str) -> Handle:
    """
    parse_xml 

    Parses all of the XML style responses that ARDC handle service provides into
    the Handle object which is a simple handle + list of properties.

    Parameters
    ----------
    text : str
        The XML input

    Returns
    -------
    Handle
        The handle object decoded from the XML - iff success occurs

    Raises
    ------
    HTTPException
        If anything goes wrong 
    """
    logging.debug("Decoding XML response from ARDC handle service.")
    # setup handle fields
    id: Optional[str] = None
    properties: List[HandleProperty] = []

    # parse into JSON
    try:
        json_result = dict(xmltodict.parse(text))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Could not parse XML response from Handle Service. Exception: {e}."
        )
    try:
        # pull out response component
        response = json_result['response']

        # success if present
        success = response['@type']
        if 'success' in success:
            # read ID
            id = response['identifier']['@handle']
            # read properties
            if 'property' in response['identifier']:
                if isinstance(response['identifier']['property'], list):
                    for p in response['identifier']['property']:
                        # add multiple properties
                        properties.append(
                            HandleProperty(
                                type=p['@type'],
                                value=p['@value'],
                                index=p['@index']
                            )
                        )
                else:
                    # add property
                    p = response['identifier']['property']
                    properties.append(
                        HandleProperty(
                            type=p['@type'],
                            value=p['@value'],
                            index=p['@index']
                        )
                    )
        else:
            error_message = response['message']['#text']
            raise HTTPException(
                status_code=500,
                detail=f"Error was reported by ARDC handle service, contents: {error_message}."
            )
        assert id
    except HTTPException as he:
        # handled
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected parsing error when parsing ARDC handle service XML response. Exception {e}."
        )

    logging.debug("Decoded successfully")
    return Handle(id=id, properties=properties)


def parse_handle_response(response: httpx.Response) -> Handle:
    """
    parse_handle_response 

    Wrapper function which decodes the response and ensures the status is 200 OK 

    Returns the parsed handle response

    Used for all methods except List

    Parameters
    ----------
    response : httpx.Response
        The httpx response

    Returns
    -------
    Handle
        The handle object parsed

    Raises
    ------
    HTTPException
        Returns 500 error with details if anything wrong
    """
    # check that the response is okay
    status_code = response.status_code
    if status_code != 200:
        details = parse_error(response=response)
        raise HTTPException(
            status_code=500,
            detail=f"Response from handle service had non 200 status code: {response.status_code}. Details: {details}."
        )

    # now get the text contents
    text = response.text
    # parse xml -> Handle object
    return parse_xml(text=text)


def parse_handle_list_response(response: httpx.Response) -> List[str]:
    """
    parse_handle_list_response 

    Wrapper function which decodes the response and ensures the status is 200 OK 

    Returns the parsed list of handle IDs

    Used only for the listHandles endpoint

    Parameters
    ----------
    response : httpx.Response
        The httpx response

    Returns
    -------
    List[str]
        The list of handle Ids

    Raises
    ------
    HTTPException
        Returns 500 error with details if anything wrong
    """
    # check that the response is okay
    status_code = response.status_code
    if status_code != 200:
        details = parse_error(response=response)
        raise HTTPException(
            status_code=500,
            detail=f"Response from handle service had non 200 status code: {response.status_code}. Details: {details}."
        )

    # now get the text contents
    text = response.text
    # parse xml -> Handle object
    return parse_xml_list(text=text)


def get_postfix(handle_op: HandleOperation) -> str:
    """
    get_postfix 

    Reads the handle operation post fix map to find the handle route postfix

    NOTE that the map is interrogated for missing entries prior to running this
    hence no runtime check

    Parameters
    ----------
    handle_op : HandleOperation
        The handle operation to find

    Returns
    -------
    str
        The postfix - doesn't include "/"
    """
    return HANDLE_OP_POSTFIX_MAP[handle_op]


def get_route(op: HandleOperation, config: Config) -> str:
    """
    get_route 

    Formats the base endpoint + operation dependent postfix into a URL

    Used for all methods to simplify managing the endpoints

    Parameters
    ----------
    op : HandleOperation
        The operation to run
    config : Config
        Config which contains the base endpoint

    Returns
    -------
    str
        The combined formatted URL
    """
    return f"{config.handle_service_endpoint}/{get_postfix(handle_op=op)}"


async def post_and_parse(url: str, params: Dict[str, str], request: str) -> Handle:
    """
    post_and_parse 

    Wrapper function which runs a POST at the specified endpoint with specified
    params then parses into the Handle object

    Parameters
    ----------
    url : str
        The complete URL to hit
    params : Dict[str, str]
        Query string args
    request : str
        The creds/config XML template - see helpers/handle_templates

    Returns
    -------
    Handle
        The decoded handle object iff successful
    """
    logger.info(f"Making handle request to {url}.")

    async with get_async_client() as client:
        response = await client.post(url=url, params=params, content=request)

    logger.info(f"Completed making handle request.")

    logger.debug("Parsing response")

    return parse_handle_response(response=response)


async def mint_handle(value: str, value_type: ValueType, config: Config) -> Handle:
    """
    mint_handle 

    Mints a handle using the ARDC handle service

    Parameters
    ----------
    value : str
        The value to include at index 1
    value_type : ValueType
        Value type for this value
    config : Config
        The config

    Returns
    -------
    Handle
        Parsed handle object
    """
    logger.debug("Determining handle route")
    route = get_route(op=HandleOperation.MINT, config=config)

    logger.debug("Determining params")
    params = {
        'type': value_type.value,
        'value': value
    }

    logger.debug("Filling out PID service template")
    request = template_handle_request(config=config)

    return await post_and_parse(url=route, params=params, request=request)


async def add_value(id: str, value: str, value_type: ValueType, config: Config) -> Handle:
    """
    add_value

    Adds a value to existing handle using ARDC handle service

    Parameters
    ----------
    id : str
        The existing handle ID
    value : str
        new value
    value_type : ValueType
        new value type
    config : Config
        config

    Returns
    -------
    Handle
        The parsed handle
    """
    logger.debug("Determining handle route")
    route = get_route(op=HandleOperation.ADD_VALUE, config=config)

    logger.debug("Determining params")
    params = {
        'type': value_type.value,
        'value': value,
        'handle': id,
    }

    logger.debug("Filling out PID service template")
    request = template_handle_request(config=config)

    return await post_and_parse(url=route, params=params, request=request)


async def add_value_by_index(id: str, index: int, value: str, value_type: ValueType, config: Config) -> Handle:
    """
    add_value_by_index

    Adds a new value to existing handle at specified index

    Parameters
    ----------
    id : str
        The existing handle id
    index : int
        The index to add at 
    value : str
        The new value
    value_type : ValueType
        New value type
    config : Config
        Config

    Returns
    -------
    Handle
        The parsed handle
    """
    logger.debug("Determining handle route")
    route = get_route(op=HandleOperation.ADD_VALUE_BY_INDEX, config=config)

    logger.debug("Determining params")
    params = {
        'type': value_type.value,
        'index': str(index),
        'value': value,
        'handle': id,
    }

    logger.debug("Filling out PID service template")
    request = template_handle_request(config=config)

    return await post_and_parse(url=route, params=params, request=request)


async def fetch_handle(id: str, config: Config) -> Handle:
    """
    fetch_handle

    Fetches an existing handle

    Parameters
    ----------
    id : str
        The ID
    config : Config
        Config

    Returns
    -------
    Handle
        The parsed handle if it exists
    """
    logger.debug("Determining handle route")
    route = get_route(op=HandleOperation.GET, config=config)

    logger.debug("Determining params")
    params = {
        'handle': id,
    }

    logger.debug("Filling out PID service template")
    request = template_handle_request(config=config)

    return await post_and_parse(url=route, params=params, request=request)


async def list_handles(config: Config) -> List[str]:
    """
    list_handles 

    Lists all handles on the config specified domain

    Parameters
    ----------
    config : Config
        The config

    Returns
    -------
    List[str]
        The list of Ids
    """
    logger.debug("Determining handle route")
    route = get_route(op=HandleOperation.LIST, config=config)

    logger.debug("Filling out PID service template")
    request = template_handle_request(config=config)

    logger.info(f"Making handle request to {route}.")
    async with get_async_client() as client:
        response = await client.post(url=route, content=request)
    logger.info(f"Completed making handle request.")

    logger.info("Parsing and validating response.")
    return parse_handle_list_response(response=response)


async def modify_value_by_index(id: str, index: int, value: str, config: Config) -> Handle:
    """
    modify_value_by_index 

    Modifies an existing handle's value at the specified index

    Parameters
    ----------
    id : str
        The handle ID
    index : int
        The index to modify
    value : str
        The value, type must match existing
    config : Config
        The config

    Returns
    -------
    Handle
        The parsed handle
    """
    logger.debug("Determining handle route")
    route = get_route(op=HandleOperation.MODIFY_VALUE_BY_INDEX, config=config)

    logger.debug("Determining params")
    params = {
        'index': str(index),
        'value': value,
        'handle': id,
    }

    logger.debug("Filling out PID service template")
    request = template_handle_request(config=config)

    return await post_and_parse(url=route, params=params, request=request)


async def remove_value_by_index(id: str, index: int, config: Config) -> Handle:
    """
    remove_value_by_index

    Removes a value at a given index if it exists

    Parameters
    ----------
    id : str
        The existing handle ID
    index : int
        The index to remove
    config : Config
        The config

    Returns
    -------
    Handle
        Parsed handle
    """
    logger.debug("Determining handle route")
    route = get_route(op=HandleOperation.REMOVE_VALUE_BY_INDEX, config=config)

    logger.debug("Determining params")
    params = {
        'index': str(index),
        'handle': id,
    }

    logger.debug("Filling out PID service template")
    request = template_handle_request(config=config)

    return await post_and_parse(url=route, params=params, request=request)
