from typing import Dict, Any
from services.encryption import EncryptionService, EncryptionError
from KeycloakFastAPI.Dependencies import ProtectedRole, User
from config import Config
from helpers.util import py_to_dict
from ProvenaInterfaces.SharedTypes import UserInfo
from fastapi import HTTPException
import json


async def encrypt_json(payload: Dict[str, Any], encryption_service: EncryptionService) -> str:
    """
    Given a JSON type payload, will stringify it, then encrypt it

    Parameters
    ----------
    payload : Dict[str, Any]
        The payload
    encryption_service: EncryptionService
        The encryption service to use

    Returns
    -------
    str
        The encrypted string
    """
    try:
        return await encryption_service.encrypt(json.dumps(payload))
    except EncryptionError as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=500, detail="Unexpected error occurred during encryption.")


async def decrypt_json(cipher_text: str, encryption_service: EncryptionService) -> Dict[str, Any]:
    """
    Decrypts cipher text and parses as JSON.

    Parameters
    ----------
    cipher_text : str
        The encrypted payload
    encryption_service: EncryptionService
        The encryption service to use

    Returns
    -------
    Dict[str, Any]
        The decrypted JSON object
    """
    try:
        return await json.loads(await encryption_service.decrypt(ciphertext=cipher_text))
    except EncryptionError as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=500, detail="Unexpected error occurred during encryption.")


async def encrypt_user_info(payload: UserInfo, encryption_service: EncryptionService) -> str:
    """

    Takes a user info object, makes json object, then passes to encrypt json

    Parameters
    ----------
    payload : UserInfo
        The user info model
    encryption_service : EncryptionService
        The encryption service

    Returns
    -------
    str
        The ciphertext
    """
    # make into dict safely
    payload = py_to_dict(payload)
    # encrypt
    return await encrypt_json(payload=payload, encryption_service=encryption_service)


async def decrypt_user_info(cipher_text: str, encryption_service: EncryptionService) -> UserInfo:
    """

    Decrypts cipher text into user info

    Parameters
    ----------
    cipher_text : str
        The encrypted payload
    encryption_service : EncryptionService
        The encryption service

    Returns
    -------
    UserInfo
        Decrypted user info
    """
    data = await decrypt_json(cipher_text=cipher_text, encryption_service=encryption_service)
    try:
        return UserInfo.parse_obj(data)
    except Exception as e:
        raise HTTPException(
            status_code=400, detail=f"Invalid payload for user info context. Decryption succeeded but payload was not parse-able.")


async def encrypt_user_dep(user: ProtectedRole, encryption_service: EncryptionService) -> str:
    """

    Takes an injected protected user fast API dependency and encrypts a UserInfo payload

    Parameters
    ----------
    user : ProtectedRole
        The user injected dependency
    encryption_service : EncryptionService
        The encryption service

    Returns
    -------
    str
        The ciphertext
    """
    # build the user info object
    user_info = UserInfo(
        username=user.user.username,
        email=user.user.email,
        roles=user.access_roles
    )
    return await encrypt_user_info(payload=user_info, encryption_service=encryption_service)


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


async def decrypt_user_dep(cipher_text: str, encryption_service: EncryptionService) -> ProtectedRole:
    """

    Decrypts cipher text into user info

    Parameters
    ----------
    cipher_text : str
        The encrypted payload
    encryption_service : EncryptionService
        The encryption service

    Returns
    -------
    ProtectedRole
        Decrypted user info
    """
    user_info = await decrypt_user_info(cipher_text=cipher_text, encryption_service=encryption_service)

    # return user as dependency format, noting that the token is not valid since
    # we don't know the original token
    return ProtectedRole(access_roles=user_info.roles, user=User(email=user_info.email, roles=user_info.roles, access_token="", username=user_info.username))
