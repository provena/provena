from KeycloakRestUtilities.TokenManager import DeviceFlowManager
from helpers.type_aliases import GetAuthFunction


def setup_auth(stage: str, keycloak_endpoint: str, token_refresh: bool) -> GetAuthFunction:
    # Login and setup auth manager
    device_auth = DeviceFlowManager(
        stage=stage,
        keycloak_endpoint=keycloak_endpoint,
        local_storage_location=".tokens.json",
        token_refresh=token_refresh
    )

    # Callable to embed into requests auth
    return device_auth.get_auth
