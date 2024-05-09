from dependencies.dependencies import read_user_protected_role_dependency, read_write_user_protected_role_dependency
from KeycloakFastAPI.Dependencies import User
from ProvenaInterfaces.HandleAPI import *
from fastapi import APIRouter, Depends
from helpers.handle_helpers import *
import logging
from config import get_settings

router = APIRouter()

# setup logger
logging.config.fileConfig('logging.conf', disable_existing_loggers=False)

# get logger for this module
logger_key = "handle_service"
logger = logging.getLogger(logger_key)


# remove value by index

@router.post("/mint", operation_id="mint")
async def mint(
    mint_request: MintRequest,
    _: User = Depends(read_write_user_protected_role_dependency),
    config: Config = Depends(get_settings)
) -> MintResponse:
    """
    mint 
    
    Creates a new handle with the given value and value type at index 1.

    Parameters
    ----------
    mint_request : MintRequest
        The request including the value and type

    Returns
    -------
    MintResponse
        Handle object
    """
    logging.info("Starting mint handle operation.")

    return await mint_handle(
        value=mint_request.value,
        value_type=mint_request.value_type,
        config=config
    )


@router.post("/add_value", operation_id="add_value")
async def add_handle_value(
    add_value_request: AddValueRequest,
    _: User = Depends(read_write_user_protected_role_dependency),
    config: Config = Depends(get_settings)
) -> AddValueResponse:
    """
    add_handle_value 
    
    Adds a value at the next available index

    Parameters
    ----------
    add_value_request : AddValueRequest
        The id of the handle, value and type

    Returns
    -------
    AddValueResponse
        The Handle object
    """
    logging.info("Starting add value handle operation.")

    return await add_value(
        id=add_value_request.id,
        value=add_value_request.value,
        value_type=add_value_request.value_type,
        config=config
    )


@router.post("/add_value_by_index", operation_id="add_value_by_index")
async def add_handle_value_by_index(
    add_value_request: AddValueIndexRequest,
    _: User = Depends(read_write_user_protected_role_dependency),
    config: Config = Depends(get_settings)
) -> AddValueIndexResponse:
    """
    add_handle_value_by_index 
    
    Adds a value on the existing handle at the specified index.

    Parameters
    ----------
    add_value_request : AddValueIndexRequest
        The id, value, value type and index

    Returns
    -------
    AddValueIndexResponse
        The handle object
    """
    logging.info("Starting add value by index handle operation.")

    return await add_value_by_index(
        id=add_value_request.id,
        index=add_value_request.index,
        value=add_value_request.value,
        value_type=add_value_request.value_type,
        config=config
    )


@router.get("/get", operation_id="get")
async def get_handle(
    id: str,
    _: User = Depends(read_user_protected_role_dependency),
    config: Config = Depends(get_settings)
) -> GetResponse:
    """
    get_handle 
    
    Fetches the information about an existing handle.

    Parameters
    ----------
    id : str
        The handle ID

    Returns
    -------
    GetResponse
        Handle object
    """
    logging.info(f"Fetching handle with ID {id}.")
    return await fetch_handle(
        id=id,
        config=config
    )


@router.get("/list", operation_id="list")
async def list_handles_handler(
    _: User = Depends(read_user_protected_role_dependency),
    config: Config = Depends(get_settings)
) -> ListResponse:
    """
    list_handles_handler 
    
    Lists the existing handles on a domain

    Parameters
    ----------

    Returns
    -------
    ListResponse
        List of IDs
    """
    logging.info(f"Listing handles")
    return ListResponse(
        ids=list_handles(config=config)
    )


@router.put("/modify_by_index", operation_id="modify_by_index")
async def modify_by_index_handler(
    modify_request: ModifyRequest,
    _: User = Depends(read_write_user_protected_role_dependency),
    config: Config = Depends(get_settings)
) -> ModifyResponse:
    """
    modify_by_index_handler 
    
    Changes the value at a given location - must match the type and exist.

    Parameters
    ----------
    modify_request : ModifyRequest
        The id, value and index

    Returns
    -------
    ModifyResponse
        Handle object
    """
    logging.info(f"Modifying by index")
    return await modify_value_by_index(
        id=modify_request.id,
        value=modify_request.value,
        index=modify_request.index,
        config=config
    )


@router.post("/remove_by_index", operation_id="remove_by_index")
async def remove_by_index_handler(
    remove_request: RemoveRequest,
    _: User = Depends(read_write_user_protected_role_dependency),
    config: Config = Depends(get_settings)
) -> RemoveResponse:
    """
    remove_by_index_handler 
    
    Deletes the value at the given index on an existing handle, if possible

    Parameters
    ----------
    remove_request : RemoveRequest
        The id and index

    Returns
    -------
    RemoveResponse
        The handle object
    """
    logging.info(f"Removing by index")
    return await remove_value_by_index(
        id=remove_request.id,
        index=remove_request.index,
        config=config
    )
