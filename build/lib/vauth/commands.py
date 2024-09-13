import base64
import datetime
import getpass

import pyotp
from qrcode.main import QRCode
from vauth.database import Database as db
from vauth.encryption import Encryption as enc
from vauth.handlers import ErrorHandler


class Commands:
    """
    vAUTH Commands Class.
    - Handles all the commands for vAUTH.

    Attributes:
        db (Database): Database Object.
        enc (Encryption): Encryption Object.
        error_handler (ErrorHandler): Error Handler Object.
        login_state (str): Login State.
    """

    def __init__(self):
        self.db = db()
        self.enc = enc()
        self.error_handler = ErrorHandler()
        if self.db.is_registered():
            self.login_state = "login"
        else:
            self.login_state = "register"

    @ErrorHandler()
    def login(self, user_id: str) -> str:
        """
        Initiate login to vAUTH.

        Args:
            user_id (str): User ID

        Returns:
            str: Password

        Raises:
            Exception: 100 - Invalid Password
        """
        key = getpass.getpass("vAUTH> Enter Password: ")
        auth_data = self.db.find_auth(user_id, self.enc.hash_key(key.encode()))
        if auth_data:
            return key
        raise Exception(100)

    @ErrorHandler()
    def register(self, user_id: str) -> tuple:
        """
        Register a new user to vAUTH.
        - Create a new password.
        - Store the password hash.
        - Generate recovery codes.

        Args:
            user_id (str): User ID to register.

        Returns:
            tuple: Recovery Codes

        Raises:
            Exception: 108 - Passwords do not match
        """
        key_1 = getpass.getpass("vAUTH> Create a Password: ")
        key_2 = getpass.getpass("vAUTH> Confirm Password: ")
        if key_1 != key_2:
            raise Exception(108)
        recovery_codes = self.enc.generate_recovery_codes()
        self.db.insert_one(
            {
                "user_id": user_id,
                "key": self.enc.hash_key(key_1.encode()),
                "recovery_codes": [
                    self.enc.hash_key(code.encode()) for code in recovery_codes
                ],
            },
            self.db.auth_table,
        )
        return recovery_codes

    @ErrorHandler()
    def recover(self, user_id: str) -> str:
        """
        Recover a user's password.
        - Check if the recovery code is valid.
        - Update the password hash.

        Args:
            user_id (str): User ID of the account to recover.

        Returns:
            str: New Password

        Raises:
            Exception: 101 - Invalid Recovery Code
            Exception: 108 - Passwords do not match
        """
        recovery_code = getpass.getpass("vAUTH> Enter Recovery Code: ")
        if self.db.find_recovery_code(user_id, recovery_code):
            key_1 = getpass.getpass("vAUTH> Create a New Password: ")
            key_2 = getpass.getpass("vAUTH> Confirm New Password: ")
            if key_1 != key_2:
                raise Exception(108)
            self.db.update_key(user_id, self.enc.hash_key(key_1.encode()))
            return key_1
        raise Exception(101)

    @ErrorHandler()
    def remove_user(self, user_id: str) -> None:
        """
        Remove a user from vAUTH.
        - Check if the user is authenticated.
        - Delete the user's data.

        Args:
            user_id (str): User ID
            key (str): Password

        Returns:
            None: None

        Raises:
            Exception: 102 - Invalid Password
        """
        key = getpass.getpass("vAUTH> Enter Password: ")
        if self.db.find_auth(user_id, self.enc.hash_key(key.encode())):
            self.db.delete_auth(user_id)
            print(f">>USER {user_id} REMOVED")
            return None
        raise Exception(102)

    @ErrorHandler()
    def add_service(
        self, user_id: str, key: str, username: str, service: str, seed: str
    ) -> None:
        """
        Add a new service to the user's account.
        - Check if the service already exists.
        - Check if the seed is valid.
        - Encrypt and store the service data.

        Args:
            user_id (str): User ID
            key (str): Password
            username (str): Username for the service
            service (str): Service name
            seed (str): Seed for the service

        Returns:
            None: None

        Raises:
            Exception: 107 - Service already exists
            Exception: 105 - Invalid Seed
        """
        if self.db.find_service(user_id, username, service):
            raise Exception(107)
        try:
            base64.b32decode(seed, casefold=True)
        except Exception:
            raise Exception(105)
        data = {
            "user_id": user_id,
            "username": username,
            "service": service,
            "seed": seed,
        }
        self.db.insert_one(
            self.enc.encrypt_data(data, key),
            self.db.service_table,
        )
        print(">>SERVICE ADDED")

    @ErrorHandler()
    def find_seed(self, user_id: str, key: str, username: str, service: str) -> str:
        """
        Find the seed for a service.
        - Check if service exists.
        - Decrypt and return the seed.

        Args:
            user_id (str): User ID
            key (str): Password
            username (str): Username for the service
            service (str): Service name

        Returns:
            str: Seed

        Raises:
            Exception: 103 - Service not found.
        """
        service_data = self.db.find_service(user_id, username, service)
        if service_data:
            service_data = self.enc.decrypt_data(service_data, key)
            return service_data["seed"]
        raise Exception(103)

    @ErrorHandler()
    def show_service(self, seed: str, user_id: str, service: str) -> tuple:
        """
        Show the TOTP for a service.
        - Generate the TOTP.
        - Calculate the time remaining for the TOTP.

        Args:
            seed (str): Seed for the service
            user_id (str): User ID
            service (str): Service name

        Returns:
            tuple: TOTP, Time remaining

        Raises:
            Exception: 104 - Invalid Seed > Deleted Service
        """
        try:
            totp = pyotp.TOTP(seed)
        except Exception:
            self.db.delete_service(user_id, service)
            raise Exception(104)
        return (
            totp.now(),
            totp.interval - datetime.datetime.now().timestamp() % totp.interval,
        )

    @ErrorHandler()
    def modify_service(
        self,
        user_id: str,
        key: str,
        username: str,
        service: str,
        type: str,
        new_value: str,
    ) -> None:
        """
        Modify the service data.
        - Check if the service exists.
        - Update the service data.
        - Encrypt and store the updated data.

        Args:
            user_id (str): User ID
            key (str): Password
            username (str): Username for the service
            service (str): Service name
            type (str): Type of data : enum('username', 'seed')
            new_value (str): New value for the data.

        Returns:
            None : None

        Raises:
            Exception: 103 - Service not found.
            Exception: 105 - Invalid Seed.
            Exception: 106 - Invalid Type.
        """
        service_data = self.db.find_service(user_id, username, service)
        if not service_data:
            raise Exception(103)
        if type == "username":
            self.db.update_service(
                user_id,
                service,
                {
                    "username": new_value,
                    "seed": service_data["seed"],
                },
            )
        elif type == "seed":
            try:
                base64.b32decode(new_value, casefold=True)
            except Exception:
                raise Exception(105)
            data = {
                "seed": new_value,
                "username": service_data["username"],
            }
            self.db.update_service(
                user_id,
                service,
                self.enc.encrypt_data(data, key),
            )
        else:
            raise Exception(106)
        print(">>SERVICE MODIFIED")
        return

    @ErrorHandler()
    def remove_service(self, user_id: str, username: str, service: str) -> None:
        """
        Remove a service from the user's account.
        - Check if the service exists.
        - Delete the service data.

        Args:
            user_id (str): User ID
            key (str): Password
            username (str): Username for the service
            service (str): Service name

            Returns:
            None: None

        Raises:
            Exception: 103 - Service not found.
        """
        service_data = self.db.find_service(user_id, username, service)
        if not service_data:
            raise Exception(103)
        self.db.delete_service(user_id, service)
        print(">>SERVICE REMOVED")

    @ErrorHandler()
    def show_qr(self, user_id: str, key: str, username: str, service: str) -> QRCode:
        """
        Show the QR code for a service.
        - Check if the service exists.
        - Decrypt the service data.
        - Generate the provisioning URI.
        - Generate the QR code.

        Args:
            user_id (str): User ID.
            key (str): Password.
            username (str): Username for the service.
            service (str): Service name.

        Returns:
            QRCode: QR Code Object.

        Raises:
            Exception: 103 - Service not found.
        """
        if not self.db.find_auth(user_id, self.enc.hash_key(key.encode())):
            raise Exception(100)
        service_data = self.db.find_service(user_id, username, service)
        if not service_data:
            raise Exception(103)
        service_data = self.enc.decrypt_data(service_data, key)
        totp = pyotp.TOTP(service_data["seed"])
        qr = QRCode()
        qr.add_data(totp.provisioning_uri(username, issuer_name=service))
        return qr
