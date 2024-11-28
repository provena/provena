from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, Union, Dict
import base64
import boto3  # type: ignore
from botocore.config import Config  # type: ignore

# Typed boto3 kms client
from mypy_boto3_kms.client import KMSClient


@dataclass
class EncryptionConfig:
    """Base configuration for encryption services."""
    pass


@dataclass
class KMSConfig(EncryptionConfig):
    """Configuration for KMS-based encryption service."""
    key_id: str
    region: str
    connect_timeout: int = 5
    read_timeout: int = 10
    max_retries: int = 3


class EncryptionError(Exception):
    """Base exception for encryption service errors."""
    pass


class EncryptionService(ABC):
    """
    Abstract base class for encryption services.

    This service provides a consistent interface for encrypting and decrypting data,
    regardless of the underlying encryption implementation.
    """

    @abstractmethod
    async def encrypt(
        self,
        plaintext: Union[str, bytes],
    ) -> str:
        """
        Encrypt the provided plaintext data.

        Args:
            plaintext: The data to encrypt. Can be either string or bytes.

        Returns:
            str: Base64-encoded encrypted data.

        Raises:
            EncryptionError: If encryption fails.
        """
        pass

    @abstractmethod
    async def decrypt(
        self,
        ciphertext: str,
    ) -> str:
        """
        Decrypt the provided ciphertext.

        Args:
            ciphertext: Base64-encoded encrypted data.
            context: Optional encryption context that must match the one used for encryption.

        Returns:
            str: Decrypted plaintext as string.

        Raises:
            EncryptionError: If decryption fails.
        """
        pass


class KMSEncryptionService(EncryptionService):
    """
    AWS KMS implementation of the encryption service.

    This service uses AWS KMS for encryption and decryption operations, handling
    the specifics of working with KMS including encryption context and error handling.
    """

    def __init__(self, config: KMSConfig):
        """
        Initialize the KMS encryption service.

        Args:
            config: KMS-specific configuration including key ID and AWS settings.
        """
        self.config = config
        self.client: KMSClient = boto3.client(
            'kms',
            region_name=config.region,
            config=Config(
                connect_timeout=config.connect_timeout,
                read_timeout=config.read_timeout,
                retries={'max_attempts': config.max_retries}
            )
        )

    async def encrypt(
        self,
        plaintext: Union[str, bytes],
    ) -> str:
        """
        Encrypt data using KMS.

        Args:
            plaintext: Data to encrypt.

        Returns:
            str: Base64-encoded encrypted data.

        Raises:
            EncryptionError: If KMS encryption fails.
        """
        try:
            # Convert string to bytes if necessary
            if isinstance(plaintext, str):
                plaintext = plaintext.encode('utf-8')

            # Encrypt using KMS
            response = self.client.encrypt(
                KeyId=self.config.key_id,
                Plaintext=plaintext,
            )

            # Return base64 encoded ciphertext
            return base64.b64encode(response['CiphertextBlob']).decode('utf-8')

        except Exception as e:
            raise EncryptionError(f"Encryption failed: {str(e)}") from e

    async def decrypt(
        self,
        ciphertext: str,
        context: Optional[Dict[str, str]] = None
    ) -> str:
        """
        Decrypt data using KMS.

        Args:
            ciphertext: Base64-encoded encrypted data.

        Returns:
            str: Decrypted plaintext as string.

        Raises:
            EncryptionError: If KMS decryption fails.
        """
        try:
            # Decode base64 ciphertext
            decoded_ciphertext = base64.b64decode(ciphertext)

            # Decrypt using KMS
            response = self.client.decrypt(
                CiphertextBlob=decoded_ciphertext,
            )

            # Return decoded plaintext
            return response['Plaintext'].decode('utf-8')

        except Exception as e:
            raise EncryptionError(f"Decryption failed: {str(e)}") from e