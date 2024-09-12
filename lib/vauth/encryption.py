from cryptography.fernet import Fernet
import hashlib
from typing import TypedDict
import secrets
import base64


class Encryption:
    """
    Class to handle encryption and decryption of data.

    Methods
    -------
    generate_key() -> str:
        Generates a new encryption key

    generate_recovery_codes() -> list[str]:
        Generates a list of 5 recovery codes

    encrypt_data(data: ServiceData, key: str) -> dict:
        Encrypts the data using the key provided

    decrypt_data(data: ServiceData, key: str) -> ServiceData:
        Decrypts the data using the key provided

    hash_key(key: bytes) -> str:
        Hashes the key using sha256
    """

    class ServiceData(TypedDict):
        """
        TypedDict to represent the data of a service
        """

        user_id: str
        username: str
        service: str
        seed: str

    def __init__(self) -> None:
        pass

    def generate_key(self) -> str:
        key = Fernet.generate_key()
        return key.decode()

    def generate_recovery_codes(self) -> list[str]:
        """
        Generates a list of 5 recovery codes

        Returns
        -------
        list[str]:
            List of 5 recovery codes
        """
        return [secrets.token_hex(16) for _ in range(5)]

    def encrypt_data(self, data: ServiceData, key: str) -> dict:
        """
        Encrypts the data using the key provided.
        - The key is hashed using sha256
        - The key is then encoded using base64 and truncated to 32 bytes
        - The data is encrypted using the key
        - The encrypted data is returned

        Parameters
        ----------
        data: ServiceData
            Data to be encrypted
        key: str
            Encryption key

        Returns
        -------
        dict:
            Encrypted data
        """
        key = self.hash_key(key.encode())
        key = base64.urlsafe_b64encode(key[:32].encode())
        f = Fernet(key)
        data["seed"] = f.encrypt(data["seed"].encode()).decode()
        return data

    def decrypt_data(self, data: ServiceData, key: str) -> ServiceData:
        """
        Decrypts the data using the key provided.
        - The key is hashed using sha256
        - The key is then encoded using base64 and truncated to 32 bytes
        - The data is decrypted using the key
        - The decrypted data is returned

        Parameters
        ----------
        data: ServiceData
            Data to be decrypted
        key: str
            Encryption key

        Returns
        -------
        ServiceData:
            Decrypted data
        """
        key = self.hash_key(key.encode())
        key = base64.urlsafe_b64encode(key[:32].encode())
        f = Fernet(key)
        data["seed"] = f.decrypt(data["seed"].encode()).decode()
        return data

    def hash_key(self, key: bytes) -> str:
        return hashlib.sha256(key).hexdigest()
