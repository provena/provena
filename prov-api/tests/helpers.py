import httpx

def check_status_code(response:httpx.Response) -> None:
    """
    check_status_code 
    
    Ensures that the httpx response is status code 200.
    
    Prints out helpful error if not.

    Parameters
    ----------
    response : httpx.Response
        The response to decode
    """
    if response.status_code != 200:
        # try and pull out error message
        error_message = "Unknown" 
        try:
            error_message = response.json()['detail'] 
        except:
            try:
                error_message = response.text
            except:
                None
        assert response.status_code == 200, f"Status code {response.status_code}. Error message: {error_message}."
    