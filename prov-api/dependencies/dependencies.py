from ProvenaInterfaces.AuthAPI import ENTITY_REGISTRY_COMPONENT, AccessLevel
from ProvenaInterfaces.SharedTypes import UserInfo
from KeycloakFastAPI.Dependencies import User, build_keycloak_auth, build_test_keycloak_auth
from config import base_config, get_settings, Config
from fastapi import Depends
from helpers.keycloak_helpers import setup_secret_cache
from ProvenaSharedFunctionality.Services.encryption import EncryptionService, KMSEncryptionService, KMSConfig
from ProvenaSharedFunctionality.Helpers.encryption_helpers import encrypt_user_info
from typing import Dict


# Setup auth -> test mode means no sig enforcement on validation
kc_auth = build_keycloak_auth(
    keycloak_endpoint=base_config.keycloak_endpoint) if not base_config.test_mode else build_test_keycloak_auth()

PROV_JOB_DISPATCHER_SERVICE_ROLE_NAME = "prov-job-dispatcher"

auth_component = ENTITY_REGISTRY_COMPONENT

# Create dependencies
# This is from the shared authorisation model
read_usage_role = auth_component.get_role_at_level(
    AccessLevel.READ).role_name
write_usage_role = auth_component.get_role_at_level(
    AccessLevel.WRITE).role_name
admin_usage_role = auth_component.get_role_at_level(
    AccessLevel.ADMIN).role_name

user_general_dependency = kc_auth.get_user_dependency()
read_user_protected_role_dependency = kc_auth.get_all_protected_role_dependency(
    [read_usage_role]
)
read_write_user_protected_role_dependency = kc_auth.get_all_protected_role_dependency(
    [read_usage_role, write_usage_role]
)
admin_user_protected_role_dependency = kc_auth.get_all_protected_role_dependency(
    [read_usage_role, write_usage_role, admin_usage_role]
)

secret_cache = setup_secret_cache()


def user_is_admin(user: User) -> bool:
    return admin_usage_role in user.roles


def build_kms_service_from_config(config: Config) -> KMSEncryptionService:
    """

    Builds the AWS Key Management service encryption service from the config object.

    Parameters
    ----------
    config : Config
        Config to build from

    Returns
    -------
    KMSEncryptionService
        The encryption service
    """
    return KMSEncryptionService(KMSConfig(
        key_id=config.user_key_id,
        region=config.user_key_region
    ))


def get_encryption_service(config: Config = Depends(get_settings)) -> EncryptionService:
    """
    FastAPI dependency injection to get encryption service. This exposes
    abstract base class implementation so we can swap out to other encryption
    service implementations as needed.

    Parameters
    ----------
    config : Config, optional
        The config - this is injected prior to the encryption service, by default Depends(get_settings)

    Returns
    -------
    EncryptionService
        The resulting service as an EncryptionService type
    """
    return build_kms_service_from_config(config)


def get_user_context_header(user_cipher: str, config: Config) -> Dict[str, str]:
    """

    Returns a dictionary intended to be merged with other headers which includes
    the user cipher at the configured user context header field.

    Parameters
    ----------
    user_cipher : str
        The encrypted user context
    config : Config
        The config

    Returns
    -------
    Dict[str, str]
        The headers
    """
    return {config.user_context_header: user_cipher}


async def get_user_cipher(
    encryption_service: EncryptionService = Depends(get_encryption_service),
    # check user is defined through dependency
    user: User = Depends(user_general_dependency)
) -> str:
    # use the encryption service to build the cipher
    return await encrypt_user_info(
        payload=UserInfo(
            email=user.email,
            roles=user.roles,
            username=user.username
        ),
        encryption_service=encryption_service)
