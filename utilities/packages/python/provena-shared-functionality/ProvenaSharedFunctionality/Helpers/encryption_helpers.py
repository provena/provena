from typing import Dict, Any
from ProvenaInterfaces.SharedTypes import UserInfo

# have to do this stupid import due to how the package import works differently
# for relative pip install vs from git install of package
try:
    from Services.encryption import EncryptionService, EncryptionError
    from utils import py_to_dict
except:
    from ..Services.encryption import EncryptionService, EncryptionError
    from ..utils import py_to_dict


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
        raise Exception("Unexpected error occurred during encryption.")


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
        return json.loads(await encryption_service.decrypt(ciphertext=cipher_text))
    except EncryptionError as e:
        raise e
    except Exception as e:
        raise Exception("Unexpected error occurred during encryption.")


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
        raise Exception(
            "Invalid payload for user info context. Decryption succeeded but payload was not parse-able.")
