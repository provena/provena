import httpx
from typing import Dict, Any, Optional
from fastapi import HTTPException


async def async_get_request(
        endpoint: str,
        token: str,
        params: Dict[str, str],
        request_headers: Optional[Dict[str, str]] = None,
        timeout: float = 10.0
) -> httpx.Response:
    """    async_get_request
        Makes a httpx async get request.

        Arguments
        ----------
        endpoint : str
        The URL to hit
        token : str
        The token to include as Authorization header
        params : Dict[str, str]
        The query string parameters ({} for none)
        request_headers: Optional[Dict[str, str]] = None
            Any headers to merge into the request
        timeout : float, optional
        Optionally specify timeout (in seconds), by default 10.0

        Returns
        -------
         : httpx.Response
        The httpx response object

        Raises
        ------
        HTTPException
        If an exception occurs during request

        See Also (optional)
        --------

        Examples (optional)
        --------
    """
    # setup async request
    async with httpx.AsyncClient(timeout=timeout) as client:
        headers = {
            'Authorization': 'Bearer ' + token  # token
        }
        headers.update(request_headers or {})

        try:
            # Make request
            return await client.get(
                endpoint, params=params, headers=headers
            )
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Registry API failed to respond - validation unsuccessful. Exception: {e}.")


async def async_post_request(
        endpoint: str,
        token: str,
        params: Dict[str, str],
        json_body: Optional[Dict[str, Any]],
        request_headers: Optional[Dict[str, str]] = None,
        timeout: float = 10.0
) -> httpx.Response:
    """    async_post_request
        Makes an async httpx post request

        Arguments
        ----------
        endpoint : str
            The URL to hit
        token : str
            The token for authorization header
        params : Dict[str, str]
            The query string params ({} for none)
        json_body : Optional[Dict[str, Any]]
            The optional json body 
        request_headers: Optional[Dict[str, str]] = None
            Any headers to merge into the request
        timeout : float, optional
            Optionally specify timeout (in seconds), by default 10.0

        Returns
        -------
         : httpx.Response
            Response object

        Raises
        ------
        HTTPException
            500 if something goes wrong in request

        See Also (optional)
        --------

        Examples (optional)
        --------
    """
    # setup async request
    async with httpx.AsyncClient(timeout=timeout) as client:
        headers = {
            'Authorization': 'Bearer ' + token  # token
        }
        headers.update(request_headers or {})
        try:
            # Make POST request
            if json_body:
                return await client.post(
                    endpoint, params=params, headers=headers, json=json_body
                )
            else:
                return await client.post(
                    endpoint, params=params, headers=headers
                )
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Registry API failed to respond - validation unsuccessful. Exception: {e}.")


async def async_put_request(
        endpoint: str,
        token: str,
        params: Dict[str, str],
        json_body: Optional[Dict[str, Any]],
        request_headers: Optional[Dict[str, str]] = None,
        timeout: float = 10.0
) -> httpx.Response:
    """    async_put_request
        Makes an async httpx put request

        Arguments
        ----------
        endpoint : str
            The URL to hit
        token : str
            The token for authorization header
        params : Dict[str, str]
            The query string params ({} for none)
        json_body : Optional[Dict[str, Any]]
            The optional json body 
        request_headers: Optional[Dict[str, str]] = None
            Any headers to merge into the request
        timeout : float, optional
            Optionally specify timeout (in seconds), by default 10.0

        Returns
        -------
         : httpx.Response
            Response object

        Raises
        ------
        HTTPException
            500 if something goes wrong in request

        See Also (optional)
        --------

        Examples (optional)
        --------
    """
    # setup async request
    async with httpx.AsyncClient(timeout=timeout) as client:
        headers = {
            'Authorization': 'Bearer ' + token  # token
        }
        headers.update(request_headers or {})
        try:
            # Make PUT request
            if json_body:
                return await client.put(
                    endpoint, params=params, headers=headers, json=json_body
                )
            else:
                return await client.put(
                    endpoint, params=params, headers=headers
                )
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Registry API failed to respond - validation unsuccessful. Exception: {e}.")
