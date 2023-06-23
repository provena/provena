from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
import requests
from jose import JWTError, jwt
from jose.constants import ALGORITHMS
from typing import Dict, Any, List, Optional


class TokenData(BaseModel):
    # The raw (access) token data which is a json
    # structured dictionary
    token_data: Dict[Any, Any]

    # Raw token
    access_token: str

    # is test mode? This is a fail safe to ensure the API does not recognise a
    # test validated token
    test_mode: bool


class User(BaseModel):
    # The user's username as defined by the
    # preferred username field
    username: str

    # The email of the user if present
    email: Optional[str]

    # The list of authorised user roles
    roles: List[str]

    # The token information
    access_token: str


class ProtectedRole(BaseModel):
    # A list of roles which granted
    # access to this resource
    access_roles: List[str]
    user: User


def retrieve_keycloak_public_key(auth_endpoint: str):
    """
    Function Description
    --------------------

    Returns the public key used to sign JWT's from keycloak endpoint


    Arguments
    ----------
    auth_endpoint : str
        The endpoint to hit when trying to retrieve key

    Returns
    -------
    str
        The public key used to sign JWT assertions



    See Also (optional)
    --------

    Examples (optional)
    --------

    """
    # based on https://github.com/nurgasemetey/fastapi-keycloak-oidc/blob/main/main.py
    error_message = f"Error finding public key from keycloak endpoint {auth_endpoint}."
    try:
        r = requests.get(auth_endpoint,
                         timeout=3)
        r.raise_for_status()
        response_json = r.json()
        return f"-----BEGIN PUBLIC KEY-----\r\n{response_json['public_key']}\r\n-----END PUBLIC KEY-----"
    except requests.exceptions.HTTPError as errh:
        print(error_message)
        print("Http Error:", errh)
        raise errh
    except requests.exceptions.ConnectionError as errc:
        print(error_message)
        print("Error Connecting:", errc)
        raise errc
    except requests.exceptions.Timeout as errt:
        print(error_message)
        print("Timeout Error:", errt)
        raise errt
    except requests.exceptions.RequestException as err:
        print(error_message)
        print("An unknown error occured:", err)
        raise err


class KeycloakAuth():

    def __init__(self, keycloak_endpoint: Optional[str] = None, test_mode: bool = False):
        # Establish the kc endpoint
        self.keycloak_endpoint = keycloak_endpoint

        # are we in test mode?
        self._test_mode = test_mode

        # Get public key from keycloak endpoint
        if not test_mode:
            assert keycloak_endpoint, "In non test mode, must supply keycloak endpoint so that the public key can be identified"
            self.public_key = retrieve_keycloak_public_key(
                self.keycloak_endpoint)
        else:
            self.public_key = ""

        # Setup the authorisation scheme
        self.token_scheme = OAuth2PasswordBearer(tokenUrl="token")

    def get_token_dependency(self):
        async def get_token(raw_token: str = Depends(self.token_scheme)):
            """
            Function Description
            --------------------

            Provides a token data object based on the raw token string. Decodes the 
            string and validates using the JWT library then populates token 
            data object.


            Arguments
            ----------
            raw_token : str, optional
                The raw unprocessed and unvalidated token 
                stripped out of the auth headers, by default Depends(oauth2_scheme)

            Returns
            -------
            TokenData
                The TokenData object filled in with the token data from the access token


            Raises
            ------
            credentials_exception
                If the token was not processed properly or could not be validated with certificate

            See Also (optional)
            --------

            Examples (optional)
            --------

            """
            # based on https://github.com/nurgasemetey/fastapi-keycloak-oidc/blob/main/main.py

            # Setup the error response for no authorisation
            credentials_exception = HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

            try:
                # this is currently locally validating the token
                # It is our responsibility to choose whether to honour the expiration date
                # etc
                jwt_payload = jwt.decode(
                    raw_token,
                    self.public_key,
                    algorithms=[ALGORITHMS.RS256],
                    options={
                        # only verify signature if not in test mode
                        "verify_signature": not self._test_mode,
                        "verify_aud": False,
                        # always validate expiry
                        "exp": True
                    }
                )
                token_data = TokenData(
                    token_data=jwt_payload,
                    access_token=raw_token,
                    test_mode=self._test_mode
                )
            except JWTError as e:
                print(f"JWT failed to decode due to error: {e}")
                raise credentials_exception
            return token_data
        return get_token

    def get_user_dependency(self):
        async def get_user(token_data: TokenData = Depends(self.get_token_dependency())):
            """
            Function Description
            --------------------

            Given the processed and validated token data, processes into a user object
            which contains the desired and extracted user information along with the 
            list of roles.


            Arguments
            ----------
            token_data : str, optional
                The processed token data , by default Depends(get_token)

            Returns
            -------
            User
                The user object created from data


            Raises
            ------
            credentials_exception
                If the token is missing the required fields this is raised

            See Also (optional)
            --------

            Examples (optional)
            --------

            """

            # Setup the error response for no authorisation
            credentials_exception = HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token had incorrect structure.",
                headers={"WWW-Authenticate": "Bearer"},
            )

            try:
                # Pull out username
                username: str = token_data.token_data.get("preferred_username")
                # Pull out keycloak role list
                roles: List[str] = token_data.token_data.get(
                    "realm_access").get("roles")
                # pull out email
                email: str = token_data.token_data.get("email")
            except Exception as e:
                print(f"Failed to decode token contents with error: {e}.")
                raise credentials_exception

            return User(username=username, roles=roles, access_token=token_data.access_token, email=email)
        return get_user

    def get_any_protected_role_dependency(self, allowed_roles: List[str]):
        async def get_protected_role(user: User = Depends(self.get_user_dependency())) -> ProtectedRole:
            """
            Function Description
            --------------------

            Used as a dependency for functions which require one of the protected roles listed
            below in the allowed_roles function. Returns the list of roles which granted 
            access to this resource.

            Grants access if ANY role from the allowed roles is present for the user.


            Arguments
            ----------
            user : User, optional
                The user object containing the role list, by default Depends(get_current_user)

            Returns
            -------
            ProtectedRole
                Protected role object which contains list of access roles which granted access
                to this resource.


            Raises
            ------
            credentials_exception
                If the user is missing this role they will have this error raised.

            See Also (optional)
            --------

            Examples (optional)
            --------

            """
            # Setup the error response for no authorisation
            credentials_exception = HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="You are not authorised to access this resource as you don't have the correct role.",
                headers={"WWW-Authenticate": "Bearer"},
            )

            # check to see if the user has any of the required roles
            access_roles = list(
                filter(lambda role: role in user.roles, allowed_roles))
            if len(access_roles) > 0:
                return ProtectedRole(access_roles=access_roles, user=user)
            else:
                print(f"Token suggests that user has insufficient role privilege.")
                raise credentials_exception
        return get_protected_role

    def get_all_protected_role_dependency(self, required_roles: List[str]):
        async def get_protected_role(user: User = Depends(self.get_user_dependency())) -> ProtectedRole:
            """
            Function Description
            --------------------

            Used as a dependency for functions which require one of the protected roles listed
            below in the allowed_roles function. Returns the list of roles which granted 
            access to this resource.

            Only allows access if ALL roles are present for the user.


            Arguments
            ----------
            user : User, optional
                The user object containing the role list, by default Depends(get_current_user)

            Returns
            -------
            ProtectedRole
                Protected role object which contains list of access roles which granted access
                to this resource.


            Raises
            ------
            credentials_exception
                If the user is missing this role they will have this error raised.

            See Also (optional)
            --------

            Examples (optional)
            --------

            """
            # Setup the error response for no authorisation
            credentials_exception = HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="You are not authorised to access this resource as you don't have the correct role.",
                headers={"WWW-Authenticate": "Bearer"},
            )

            # check to see if the user has any of the required roles
            matching_roles = list(
                filter(lambda role: role in user.roles, required_roles))

            # all roles matching
            if len(matching_roles) == len(required_roles):
                return ProtectedRole(access_roles=matching_roles, user=user)
            else:
                print(f"Token suggests that user has insufficient role privilege.")
                raise credentials_exception
        return get_protected_role


def build_keycloak_auth(keycloak_endpoint: str) -> KeycloakAuth:
    return KeycloakAuth(keycloak_endpoint=keycloak_endpoint, test_mode=False)


def build_test_keycloak_auth() -> KeycloakAuth:
    return KeycloakAuth(keycloak_endpoint="", test_mode=True)
