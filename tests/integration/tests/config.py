from KeycloakRestUtilities.Token import get_token
from pydantic import BaseSettings
from functools import lru_cache
from typing import Callable, Optional
import jwt
from dataclasses import dataclass


class Config(BaseSettings):
    # use .env file
    class Config:
        env_file = ".env"

    REGISTRY_API_ENDPOINT: str
    DATA_STORE_API_ENDPOINT: str
    PROV_API_ENDPOINT: str
    JOB_API_ENDPOINT: str
    AUTH_API_ENDPOINT: str
    SYSTEM_WRITE_USERNAME: str
    SYSTEM_WRITE_PASSWORD: str
    SYSTEM_WRITE_USERNAME_2: str
    SYSTEM_WRITE_PASSWORD_2: str
    SYSTEM_WRITE_USERNAME_3: str
    SYSTEM_WRITE_PASSWORD_3: str
    ADMIN_USERNAME: str
    ADMIN_PASSWORD: str
    KEYCLOAK_ENDPOINT: str
    # keycloak_token_endpoint: str
    KEYCLOAK_CLIENT_ID: str
    INVALID_HANDLE: str
    LEAVE_ITEMS_FOR_INITIALISATION: bool = False

    # Postfix to add to keycloak endpoint to reach token endpoint
    keycloak_token_postfix: str = "/protocol/openid-connect/token"

    @property
    def keycloak_token_endpoint(self) -> str:
        return self.KEYCLOAK_ENDPOINT + self.keycloak_token_postfix


config = Config()


@lru_cache()
def get_settings() -> Config:
    # define dep injection for proper config
    return Config()


def check_expiry(token: str) -> bool:
    try:
        decoded = jwt.decode(
            jwt=token,
            # Don't bother verifying the signature, API  does that, just check
            # expiry
            options={'verify_signature': False, 'verify_exp': True}
        )
        return True
    except jwt.ExpiredSignatureError:
        return False


def fetch_token(username: str, password: str) -> str:
    return get_token(keycloak_endpoint=config.keycloak_token_endpoint, client_id=config.KEYCLOAK_CLIENT_ID, username=username, password=password)


def refresh_user1() -> str:
    print("Refreshing user1 token")
    return fetch_token(
        username=config.SYSTEM_WRITE_USERNAME,
        password=config.SYSTEM_WRITE_PASSWORD
    )


def refresh_user2() -> str:
    print("Refreshing user2 token")
    return fetch_token(
        username=config.SYSTEM_WRITE_USERNAME_2,
        password=config.SYSTEM_WRITE_PASSWORD_2
    )

def refresh_user3() -> str:
    print("Refreshing user3 token")
    return fetch_token(
        username=config.SYSTEM_WRITE_USERNAME_3,
        password=config.SYSTEM_WRITE_PASSWORD_3
    )


def refresh_admin() -> str:
    print("Refreshing admin token")
    return fetch_token(
        username=config.ADMIN_USERNAME,
        password=config.ADMIN_PASSWORD
    )


TokenGenerator = Callable[[], str]
TokenSetter = Callable[[str], None]


def check_and_update(token: Optional[str], refresh_method: TokenGenerator, set_method: TokenSetter) -> str:
    if token is None:
        new_token = refresh_method()
        set_method(new_token)
        return new_token
    else:
        if check_expiry(token):
            return token
        else:
            new_token = refresh_method()
            set_method(new_token)
            return new_token


@dataclass
class CurrentTokens:
    user1: Optional[str] = refresh_user1()
    user2: Optional[str] = refresh_user2()
    user3: Optional[str] = refresh_user3()
    admin: Optional[str] = refresh_admin()

    def get_refresh_user1(self) -> str:
        def update(t: str) -> None:
            self.user1 = t
        return check_and_update(
            token=self.user1,
            refresh_method=refresh_user1,
            set_method=update
        )

    def get_refresh_user2(self) -> str:
        def update(t: str) -> None:
            self.user2 = t
        return check_and_update(
            token=self.user2,
            refresh_method=refresh_user2,
            set_method=update
        )
    
    def get_refresh_user3(self) -> str:
        def update(t: str) -> None:
            self.user3 = t
        return check_and_update(
            token=self.user3,
            refresh_method=refresh_user3,
            set_method=update
        )

    def get_refresh_admin(self) -> str:
        def update(t: str) -> None:
            self.admin = t
        return check_and_update(
            token=self.admin,
            refresh_method=refresh_admin,
            set_method=update
        )


class Tokens:
    # initialises token state for user1,2 and admin
    token_state: CurrentTokens = CurrentTokens()

    # system write and read access users
    user1: TokenGenerator = token_state.get_refresh_user1
    user2: TokenGenerator = token_state.get_refresh_user2
    user3: TokenGenerator = token_state.get_refresh_user3

    # static usernames
    user1_username: str = config.SYSTEM_WRITE_USERNAME
    user2_username: str = config.SYSTEM_WRITE_USERNAME_2
    user3_username: str = config.SYSTEM_WRITE_USERNAME_3
    admin_username: str = config.ADMIN_USERNAME

    # system admin access for clean up + admin only endpoints (such as auth/group management)
    admin: TokenGenerator = token_state.get_refresh_admin


# endpoint setup for link service
link_prefix = "link"
user_prefix = "user"
admin_prefix = "admin"

lookup_action = "lookup"
assign_action = "assign"
clear_action = "clear"
reverse_action = "reverse_lookup"

user_lookup = f"{config.AUTH_API_ENDPOINT}/{link_prefix}/{user_prefix}/{lookup_action}"
user_assign = f"{config.AUTH_API_ENDPOINT}/{link_prefix}/{user_prefix}/{assign_action}"

admin_lookup = f"{config.AUTH_API_ENDPOINT}/{link_prefix}/{admin_prefix}/{lookup_action}"
admin_assign = f"{config.AUTH_API_ENDPOINT}/{link_prefix}/{admin_prefix}/{assign_action}"
admin_clear = f"{config.AUTH_API_ENDPOINT}/{link_prefix}/{admin_prefix}/{clear_action}"
admin_reverse_lookup = f"{config.AUTH_API_ENDPOINT}/{link_prefix}/{admin_prefix}/{reverse_action}"
