from aws_secretsmanager_caching import SecretCache  # type: ignore
from fastapi import HTTPException
from config import Config, HDL_PREFIX
import httpx
from random import randint
from helpers.keycloak_helpers import get_service_token
from dependencies.dependencies import secret_cache
from ProvenaInterfaces.HandleModels import *
from ProvenaInterfaces.HandleAPI import MintRequest, MintResponse, ModifyRequest


def process_handle_error(status_code: int, handle_message: str) -> None:
    """    
        Function Description
        --------------------
        Processes errors for Handle Service responses so that we can consistently
        apply this across different procedures/functions. 

        Arguments
        ----------
        status_code : int
            Response status code from the Handle Service.
        handle_message : str
            Response message string from the Handle Service

        Raises
        ------
        HTTPException
            A HTTPException which is either a 401 (Not authorised) or a 500 (catch-all exception)
            with the specific status code and message returned from the Handle Service.

        See Also (optional)
        --------

        Examples (optional)
        --------
    """
    if status_code == 401:
        raise HTTPException(status_code=500, detail='API service account was not authorised to mint identifiers on the Handle service. Code: {}. Handle service message returned: {}'
                            .format(status_code, handle_message))
    else:
        raise HTTPException(status_code=500, detail='Handle service returned with a status code of {}. Handle service message returned: {}'
                            .format(status_code, handle_message))


async def get_empty_handle(secret_cache: SecretCache, config: Config) -> str:
    """
    Function Description
    --------------------

    Given a valid access token will call the handle service on behalf
    of the user and mint a new empty handle. This will be returned.


    Arguments
    ----------
    mock : Optional[bool] = False
        Should the actual handle service be used or a mock (random generator)
        Mocking should only be used if testing on non live infra.

    Returns
    -------
    str
        The handle received



    See Also (optional)
    --------

    Examples (optional)
    --------

    """

    len = 5
    rand_code = ""
    for _ in range(len):
        rand_code += str(randint(0, 9))

    if not config.mock_handle:

        # get the service account token to make
        # request on behalf of user
        token = get_service_token(secret_cache, config=config)

        async with httpx.AsyncClient(timeout=10.0) as client:
            mint_request = MintRequest(
                value_type=ValueType.URL,
                value=f'https://www.empty{rand_code}.com'
            )
            headers = {
                'Authorization': f"Bearer {token}"
            }

            try:
                assert config.handle_api_endpoint
                handle_response = await client.post(
                    config.handle_api_endpoint + "/handle/mint", json=mint_request.dict(), headers=headers
                )
            except Exception as e:
                raise HTTPException(
                    status_code=500, detail=f"Handle service failed to respond - mint unsuccessful. Exception: {e}.")

            try:
                if handle_response.status_code != 200:
                    process_handle_error(
                        handle_response.status_code, handle_response.text)
                try:
                    mint_response = MintResponse.parse_obj(
                        handle_response.json())
                except Exception as e:
                    raise HTTPException(
                        status_code=500, detail=f"Handle service responded with 200 OK but response was not parsable. Parse error: {e}.")

                handle = mint_response.id
            except HTTPException as he:
                raise he
            except Exception as e:
                raise HTTPException(
                    status_code=500, detail=f"Handle service responded but failed to parse the handle response. Exception: {e}.")
    else:
        handle = rand_code

    return handle


async def update_handle(secret_cache: SecretCache, existing_handle: str, new_value: str, config: Config) -> None:
    """
    Function Description
    --------------------

    Updates a handle with the specified value. Uses the 
    handle lambda client API.


    Arguments
    ----------
    token : str
        The authorization token used to access this API 
        which is valid for the handle client as well.
    existing_handle : str
        The existing handle id which was minted as an empty
        value.
    new_value : str
        The desired new value which likely includes the handle
        encoded as a resolvable value




    See Also (optional)
    --------

    Examples (optional)
    --------

    """
    if not config.mock_handle:

        # Generate service account token
        token = get_service_token(secret_cache, config=config)

        async with httpx.AsyncClient(timeout=10.0) as client:
            modify_request = ModifyRequest(
                id=existing_handle,
                index=1,
                value=new_value
            )
            headers = {
                'Authorization': f"Bearer {token}"
            }
            try:
                assert config.handle_api_endpoint
                handle_response = await client.put(
                    config.handle_api_endpoint + "/handle/modify_by_index", json=modify_request.dict(), headers=headers
                )
            except Exception as e:
                raise HTTPException(
                    status_code=500, detail=f"Handle service failed to respond - mint unsuccessful. Exception: {e}.")

            try:
                print(handle_response.text)
                if handle_response.status_code != 200:
                    process_handle_error(
                        handle_response.status_code, handle_response.text)
            except HTTPException as he:
                raise he
            except Exception as e:
                raise HTTPException(
                    status_code=500, detail=f"Handle service responded but failed to parse the handle response. Exception: {e}.")


def construct_handle_path(handle: str, config: Config) -> str:
    assert config.stage

    # Data store registry maintains a mapping between handle -> S3 Path
    return f"{HDL_PREFIX}/{handle}"


async def mint_self_describing_handle(config: Config) -> str:
    # mint empty handle
    empty_handle = await get_empty_handle(secret_cache=secret_cache, config=config)

    # generate proper path
    path = construct_handle_path(empty_handle, config=config)

    # update
    await update_handle(
        secret_cache=secret_cache,
        existing_handle=empty_handle,
        new_value=path,
        config=config
    )

    # return the handle that was updated
    return empty_handle
