import webbrowser
from SharedInterfaces.DataStoreAPI import *
import requests as rq
import time
from jose import jwt  # type: ignore
from jose.constants import ALGORITHMS  # type: ignore
from KeycloakRestUtilities.Token import BearerAuth
from pydantic import BaseModel
from enum import Enum


# Model for storing and serialising tokens
class Stage(str, Enum):
    TEST = "TEST"
    DEV = "DEV"
    STAGE = "STAGE"
    PROD = "PROD"


class Tokens(BaseModel):
    access_token: str
    refresh_token: str


class StageTokens(BaseModel):
    stages: Dict[Stage, Optional[Tokens]]


LOCAL_STORAGE_DEFAULT = ".tokens.json"


class DeviceFlowManager:
    def __init__(
        self,
        stage: str,
        keycloak_endpoint: str,
        client_id: str = "admin-tools",
        local_storage_location: str = LOCAL_STORAGE_DEFAULT,
        scopes: List[str] = [],
        token_refresh: bool = False
    ) -> None:
        """    __init__
            Generates a helper class for managing authorisation. 

            This class uses a device auth flow to generate access and refresh tokens. 

            It provides a get_auth() method which will validate, refresh or regenerate tokens
            as required. You can use this in the requests auth argument to enable dynamic token 
            generation as required (even through multiple refreshes).

            Arguments
            ----------
            stage : str
                The application stage e.g. TEST DEV STAGE PROD
            keycloak_endpoint : str 
                The qualified keycloak endpoint for the given stage e.g. 
                https://auth.your.domain/auth/realms/realm_name
            client_id : str, optional
                The client id, by default "admin-tools"
            local_storage_location : str
                The location that the tokens will be written/stored to and pulled
                from. Defaults to .tokens.json 
            scopes : List[str], optional
                The scopes, by default []
            token_refresh: bool 
                Force an invalidation of cached credentials, by default False.

            See Also (optional)
            --------

            Examples (optional)
            --------
        """
        self.keycloak_endpoint = keycloak_endpoint
        self.client_id = client_id

        # initialise empty stage tokens
        self.stage_tokens: Optional[Tokens] = None
        self.public_key: Optional[str] = None
        self.scopes: List[str] = scopes

        # pull out stage
        try:
            self.stage: Stage = Stage[stage]
        except:
            print(f"Stage {stage} is not one of {list(Stage)}.")

        self.token_endpoint = self.keycloak_endpoint + "/protocol/openid-connect/token"
        self.device_endpoint = self.keycloak_endpoint + \
            "/protocol/openid-connect/auth/device"
        self.token_storage_location = local_storage_location

        if token_refresh:
            self.reset_local_storage()

        self.retrieve_keycloak_public_key()
        self.get_tokens()

    def retrieve_local_tokens(self, stage: Stage) -> Optional[Tokens]:
        print("Looking for existing tokens in local storage.")
        print()
        # Try to read file
        try:
            stage_tokens = StageTokens.parse_file(self.token_storage_location)
            tokens = stage_tokens.stages.get(stage)
            assert tokens
        except:
            print(f"No local storage tokens for stage {stage} found.")
            print()
            return None

        # Validate
        print("Validating found tokens")
        print()
        valid = True
        try:
            self.validate_token(tokens=tokens)
        except:
            valid = False

        # Return the tokens found if valid
        if valid:
            print("Found tokens valid, using.")
            print()
            return tokens

        # Tokens found but were invalid, try refreshing
        refresh_succeeded = True
        try:
            print("Trying to use found tokens to refresh the access token.")
            print()
            refreshed = self.perform_refresh(tokens=tokens)

            # unpack response and return access token
            access_token = refreshed.get('access_token')
            refresh_token = refreshed.get('refresh_token')

            # Make sure they are preset
            assert access_token
            assert refresh_token

            tokens = Tokens(
                access_token=access_token,
                refresh_token=refresh_token
            )
            self.validate_token(tokens)
        except:
            refresh_succeeded = False

        # If refresh fails for some reason then return None
        # otherwise return the tokens
        if refresh_succeeded:
            print("Token refresh successful.")
            print()
            return tokens
        else:
            print("Tokens found in storage but they are not valid.")
            print()
            return None

    def reset_local_storage(self) -> None:
        """    reset_local_storage
            Forces a local storage reset if the token_refresh
            parameter is supplied. 

            This is used to invalidate cache.

            See Also (optional)
            --------

            Examples (optional)
            --------
        """
        print("Flushing tokens from local storage.")
        cleared_tokens = StageTokens(
            stages={
                Stage.TEST: None,
                Stage.DEV: None,
                Stage.STAGE: None,
                Stage.PROD: None
            }
        )

        # Dump the cleared file into storage
        with open(self.token_storage_location, 'w') as f:
            f.write(cleared_tokens.json())

    def update_local_storage(self, stage: Stage) -> None:
        """    update_local_storage
            Dumps the current tokens into storage, 
            must have tokens.

            See Also (optional)
            --------

            Examples (optional)
            --------
        """
        # Check current tokens
        assert self.tokens
        existing: Optional[bool] = None
        existing_tokens: Optional[StageTokens] = None
        try:
            existing_tokens = StageTokens.parse_file(
                self.token_storage_location)
            existing = True
        except:
            existing = False

        assert existing is not None
        if existing:
            # We have existing - update current stage
            assert existing_tokens

            existing_tokens.stages[stage] = self.tokens
        else:
            existing_tokens = StageTokens(
                stages={
                    Stage.TEST: None,
                    Stage.DEV: None,
                    Stage.STAGE: None,
                    Stage.PROD: None
                }
            )
            existing_tokens.stages[stage] = self.tokens

        # Dump the file into storage
        with open(self.token_storage_location, 'w') as f:
            f.write(existing_tokens.json())

    def get_tokens(self) -> None:
        """    get_tokens
            The main method for establishing the tokens. 
            This will look first in local storage, then it will 
            do a login and validate.

            Raises
            ------
            Exception
                Failure of device authorisation flow
            Exception
                Failure of device response (not including required fields)

            See Also (optional)
            --------

            Examples (optional)
            --------
        """
        # Try getting from local storage first
        # These are always validated
        print("Attempting to generate authorisation tokens.")
        print()

        retrieved_tokens = self.retrieve_local_tokens(self.stage)
        if retrieved_tokens:
            self.tokens = retrieved_tokens
            self.update_local_storage(self.stage)
            return

        # Otherwise do a normal authorisation flow
        # grant type
        device_grant_type = "urn:ietf:params:oauth:grant-type:device_code"

        print("Initiating device auth flow to setup offline access token.")
        print()
        device_auth_response = self.initiate_device_auth_flow()

        print("Decoding response")
        print()
        device_code = device_auth_response['device_code']
        user_code = device_auth_response['user_code']
        verification_uri = device_auth_response['verification_uri_complete']
        interval = device_auth_response['interval']

        print("Please authorise using the following endpoint.")
        print()
        self.display_device_auth_flow(user_code, verification_uri)
        print()

        print("Awaiting completion")
        print()
        oauth_tokens = self.await_device_auth_flow_completion(
            device_code=device_code,
            interval=interval,
            grant_type=device_grant_type,
        )
        print()

        if oauth_tokens is None:
            raise Exception(
                "Failed to retrieve tokens from device authorisation flow!")

        # pull out the refresh and access token
        # this refresh token is standard (not offline access)
        access_token = oauth_tokens.get('access_token')
        refresh_token = oauth_tokens.get('refresh_token')

        # Check that they are present
        try:
            assert access_token is not None
            assert refresh_token is not None
        except Exception as e:
            raise Exception(
                f"Token payload did not include access or refresh token: Error: {e}")
        # Set tokens
        self.tokens = Tokens(
            access_token=access_token,
            refresh_token=refresh_token
        )
        self.update_local_storage(self.stage)

        print("Token generation complete. Authorisation successful.")
        print()

    def perform_token_refresh(self) -> None:
        """    perform_token_refresh
            Updates the current instances tokens with 
            a new set by using the refresh token.

            See Also (optional)
            --------

            Examples (optional)
            --------
        """
        assert self.tokens is not None

        print("Refreshing using refresh token")
        print()

        refreshed = self.perform_refresh()

        # unpack response and return access token
        access_token = refreshed.get('access_token')
        refresh_token = refreshed.get('refresh_token')

        # Make sure they are preset
        assert access_token
        assert refresh_token

        self.tokens = Tokens(
            access_token=access_token,
            refresh_token=refresh_token
        )
        self.update_local_storage(self.stage)

    def perform_refresh(self, tokens: Optional[Tokens] = None) -> Dict[str, Any]:
        """    perform_offline_refresh
            Exchanges a refresh token for an access token with the specified client id, 
            scopes and endpoint. Used to exchange offline token for access token.

            Arguments
            ----------
            tokens : Optional[Tokens] = None
                if you want to provide a set of tokens instead 
                of using the instances current tokens

            Returns
            -------
            : Dict[str, Any]
                JSON response from API endpoint which includes ['access_token'] field

            See Also (optional)
            --------
            https://developer.okta.com/docs/reference/api/oidc/#token

            Examples (optional)
            --------
        """

        # Perform a refresh grant
        refresh_grant_type = "refresh_token"

        # make sure we have tokens to use
        desired_tokens: Optional[Tokens]
        if tokens:
            desired_tokens = tokens
        else:
            desired_tokens = self.tokens

        assert desired_tokens

        # Required openid connect fields
        data = {
            "grant_type": refresh_grant_type,
            "client_id": self.client_id,
            "refresh_token": desired_tokens.refresh_token,
            "scope": " ".join(self.scopes)
        }

        # Send API request
        response = rq.post(self.token_endpoint, data=data)

        if (not response.status_code == 200):
            raise Exception(
                f"Something went wrong during token refresh. Status code: {response.status_code}.")

        return response.json()

    def initiate_device_auth_flow(self) -> Dict[str, Any]:
        """Initiates an OAuth device authorization flow against
        the keycloak server. The client id and scope are included.

        Args:
            client_id (str): The client id which enables offline 
            access.

        Returns:
            Dict: The JSON response from the keycloak endpoint.
        """
        data = {
            "client_id": self.client_id,
            "scope": ' '.join(self.scopes)
        }
        response = rq.post(self.device_endpoint, data=data).json()
        return response

    def get_auth(self) -> BearerAuth:
        """    get_auth
            A method to generate a requests wrapped auth object.
            Also performs a refresh if the token has expired.
            Will try to sign back in if the refresh fails.  

            Returns
            -------
             : BearerAuth
                The requests bearer auth

            Raises
            ------
            Exception
                The instance has no tokens
            Exception
                If all attempts at refreshing tokens
                fails

            See Also (optional)
            --------

            Examples (optional)
            --------
        """
        # make auth object using access_token
        if (self.tokens is None or self.public_key is None):
            raise Exception(
                "cannot generate bearer auth object without access token or public key")

        assert self.tokens
        assert self.public_key

        try:
            self.validate_token()
        except Exception as e:
            print(f"Token validation failed due to error: {e}")
            try:
                self.perform_token_refresh()
                self.validate_token()
            except Exception as e:
                try:
                    self.get_tokens()
                    self.validate_token()
                except Exception as e:
                    raise Exception(
                        f"Device log in failed, access token expired/invalid, and refresh failed. Error: {e}")
        return BearerAuth(token=self.tokens.access_token)

    def retrieve_keycloak_public_key(self) -> None:
        """
        Function Description
        --------------------

        Returns the public key used to sign JWT's from keycloak endpoint


        Arguments
        ----------

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
        error_message = f"Error finding public key from keycloak endpoint {self.keycloak_endpoint}."
        try:
            r = rq.get(self.keycloak_endpoint,
                       timeout=3)
            r.raise_for_status()
            response_json = r.json()
            self.public_key = f"-----BEGIN PUBLIC KEY-----\r\n{response_json['public_key']}\r\n-----END PUBLIC KEY-----"
        except rq.exceptions.HTTPError as errh:
            print(error_message)
            print("Http Error:", errh)
            raise errh
        except rq.exceptions.ConnectionError as errc:
            print(error_message)
            print("Error Connecting:", errc)
            raise errc
        except rq.exceptions.Timeout as errt:
            print(error_message)
            print("Timeout Error:", errt)
            raise errt
        except rq.exceptions.RequestException as err:
            print(error_message)
            print("An unknown error occured:", err)
            raise err

    def display_device_auth_flow(self, user_code: str, verification_url: str) -> None:
        """Given the user code and verification url from the device 
        auth challenge, will display in the console the URL and also
        open a browser window using the default browser defined in the 
        OS to the specified URL.

        Args:
            user_code (str): The device auth flow user code.
            verification_url (str): The verification URL with the user code embedded
        """
        print(f"Verification URL: {verification_url}")
        print(f"User Code: {user_code}")
        try:
            webbrowser.open(verification_url)
        except Exception:
            print("Tried to open web-browser but failed. Please visit URL above.")

    def await_device_auth_flow_completion(
        self,
        device_code: str,
        interval: int,
        grant_type: str,
    ) -> Optional[Dict[str, Any]]:
        """Given the device code, client id and the poll interval, will 
        repeatedly post against the OAuth token endpoint to try and get
        an access and id token. Will wait until the user verifies at the 
        URL.

        Args:
            device_code (str): The oauth device code
            client_id (str): The keycloak client id
            interval (int): The polling interval returned from the 
            device auth flow endpoint.

        Returns:
            Dict: The response from the token endpoint (tokens)
        """
        # set up request
        data = {
            "grant_type": grant_type,
            "device_code": device_code,
            "client_id": self.client_id,
            "scope": " ".join(self.scopes)
        }

        # Setup success criteria
        succeeded = False
        timed_out = False
        misc_fail = False

        # start time
        response_data: Optional[Dict[str, Any]] = None

        # get requests session for repeated queries
        session = rq.session()

        # Poll for success
        while not succeeded and not timed_out and not misc_fail:
            response = session.post(self.token_endpoint, data=data)
            response_data = response.json()
            assert response_data
            if response_data.get('error'):
                error = response_data['error']
                if error != 'authorization_pending':
                    misc_fail = True
                # Wait appropriate OAuth poll interval
                time.sleep(interval)
            else:
                # Successful as there was no error at the endpoint
                return response_data

        try:
            assert response_data
            print(f"Failed due to {response_data['error']}")
            return None
        except Exception as e:
            print(
                f"Failed with unknown error, failed to find error message. Error {e}")
            return None

    def validate_token(self, tokens: Optional[Tokens] = None) -> None:
        """    validate_token
            Will attempt to validate the current instances token 
            or a separate set of tokens against current instances
            public key endpoint etc.

            Arguments
            ----------
            tokens : Optional[Tokens], optional
                If you want to use a non instance set 
                of tokens rather than instance, by default None

            See Also (optional)
            --------

            Examples (optional)
            --------
        """
        # Validate either self.tokens or supply tokens optionally
        test_tokens: Optional[Tokens]
        if tokens:
            test_tokens = tokens
        else:
            test_tokens = self.tokens

        # Check tokens are present
        assert test_tokens
        assert self.public_key

        # this is currently locally validating the token
        # It is our responsibility to choose whether to honour the expiration date
        # etc
        # this will throw an exception if invalid
        jwt_payload = jwt.decode(
            test_tokens.access_token,
            self.public_key,
            algorithms=[ALGORITHMS.RS256],
            options={
                "verify_signature": True,
                "verify_aud": False,
                "exp": True
            }
        )
