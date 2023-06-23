import requests
from requests.auth import HTTPBasicAuth


def get_client_credential_token(client_id: str, client_secret: str, token_endpoint: str, grant_type: str) -> str:
    """    get_service_access_token
        Given the client id, secret, grant type and endpoint will perform a token 
        request against the keycloak server to retrieve a service account credential.

        Arguments
        ----------
        client_id : str
            The keycloak client id
        client_secret : str
            The keycloak client secret
        token_endpoint : str
            The token endpoint for keycloak auth server
        grant_type : str
            The grant type (probably client_credentials)

        Returns
        -------
         : str
            The access token

        Raises
        ------
        HTTPException
            500 if something goes wrong making request
        HTTPException
            500 if 401 unauthorized response

        See Also (optional)
        --------

        Examples (optional)
        --------
    """
    auth = HTTPBasicAuth(client_id, client_secret)
    payload = {
        'grant_type': grant_type
    }

    # make request
    response = requests.post(token_endpoint, data=payload, auth=auth)

    try:
        assert response.status_code == 200
    except Exception as e:
        if response.status_code == 401:
            raise Exception(
                "API service account creds appear to be incorrect. Contact administrator."
            )
        else:
            raise Exception(
                f"API service creds request failed, code: {response.status_code}."
            )

    return response.json()['access_token']
