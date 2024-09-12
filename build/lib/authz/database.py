import sqlite3
from typing import TypedDict
import os
import json


class Database:
    """
    Database class to handle the database operations.

    Methods
    -------
    insert_one(data: dict, table_name: str) -> None:
        Inserts a record into the table
    find_service(user_id: str, username: str, service: str) -> ServiceData | None:
        Finds a service record
    find_auth(user_id: str, key: str, mode="key") -> AuthData | None:
        Finds an auth record
    find_recovery_code(user_id: str, recovery_code: str) -> bool:
        Finds a recovery code
    delete_service(user_id: str, service: str) -> None:
        Deletes a service record
    delete_auth(user_id: str) -> None:
        Deletes an auth record
    remove_user(user_id: str) -> None:
        Removes a user
    update_service(user_id: str, service: str, data: ServiceData) -> None:
        Updates a service record
    is_registered() -> bool:
        Checks if the database is registered
    close():
        Closes the database connection
    """

    class ServiceData(TypedDict):
        """
        TypedDict to represent the data of a service
        """

        user_id: str
        username: str
        service: str
        seed: str

    class AuthData(TypedDict):
        """
        TypedDict to represent the data of an auth record
        """

        user_id: str
        key: str
        recovery_codes: list

    def __init__(self, path=os.path.join(os.path.expanduser("~"), ".authz")) -> None:
        os.makedirs(path, exist_ok=True)
        self.connection = sqlite3.connect(os.path.join(path, "authz.db"))
        self.cursor = self.connection.cursor()
        self.service_table = "services"
        self.auth_table = "auth"

    def insert_one(self, data, table_name: str) -> None:
        """
        Inserts a record into the table
        ----------
        data : dict
            Data to be inserted
        table_name : str
            Name of the table

        Returns
        -------
        None
        """
        if table_name == self.service_table:
            self.cursor.execute(
                f"CREATE TABLE IF NOT EXISTS {self.service_table}(user_id TEXT, username TEXT, service TEXT, seed TEXT)",
            )
            self.cursor.execute(
                f"INSERT INTO {self.service_table} (user_id, username, service, seed) VALUES (?, ?, ?, ?)",
                (
                    data["user_id"],
                    data["username"],
                    data["service"],
                    data["seed"],
                ),
            )
        elif table_name == self.auth_table:

            self.cursor.execute(
                f"CREATE TABLE IF NOT EXISTS {self.auth_table}(user_id TEXT, key TEXT, recovery_codes TEXT)",
            )
            self.cursor.execute(
                f"INSERT INTO {table_name} (user_id, key, recovery_codes) VALUES (?, ?, ?)",
                (
                    data["user_id"],
                    data["key"],
                    json.dumps(data["recovery_codes"]),
                ),
            )
        self.connection.commit()

    def find_service(
        self,
        user_id: str,
        username: str,
        service: str,
    ) -> ServiceData | None:
        """
        Finds a service record
        ----------
        user_id : str
            User ID
        username : str
            Username
        service : str
            Service

        Returns
        -------
        ServiceData | None
            Service record
        """
        self.cursor.execute(
            f"CREATE TABLE IF NOT EXISTS {self.service_table}(user_id TEXT, username TEXT, service TEXT, seed TEXT)",
        )
        self.cursor.execute(
            f"SELECT * FROM {self.service_table} WHERE user_id = ? AND username = ? AND service = ?",
            (user_id, username, service),
        )
        output = self.cursor.fetchone()
        return (
            {
                "user_id": output[0],
                "username": output[1],
                "service": output[2],
                "seed": output[3],
            }
            if output
            else None
        )

    def find_auth(self, user_id: str, key: str, mode="key") -> AuthData | None:
        """
        Finds an auth record

        Parameters
        ----------
        user_id : str
            User ID
            key : str
            Key
            mode : str
            Mode

        Returns
        -------
            AuthData | None
            Auth record
        """
        if mode == "key":
            self.cursor.execute(
                f"SELECT * FROM {self.auth_table} WHERE user_id = ? AND key = ?",
                (user_id, key),
            )
            output = self.cursor.fetchone()
        elif mode == "recovery":
            self.cursor.execute(
                f"SELECT * FROM {self.auth_table} WHERE user_id = ?",
                (user_id,),
            )
            output = self.cursor.fetchone()
        return (
            {
                "user_id": output[0],
                "key": output[1],
                "recovery_codes": output[2],
            }
            if output
            else None
        )

    def find_recovery_code(self, user_id: str, recovery_code: str) -> bool:
        """
        Validates the recovery code.

        Parameters
        ----------
        user_id : str
            User ID
        recovery_code : str
            Recovery code

        Returns
        -------
        bool
            True if the recovery code exists, False otherwise
        """
        auth_data = self.find_auth(user_id, "", mode="recovery")
        if auth_data:
            recovery_codes = json.loads(auth_data["recovery_codes"])
            if recovery_code in recovery_codes:
                return True
        return False

    def delete_service(self, user_id: str, service: str) -> None:
        """
        Deletes a service record

        Parameters
        ----------
        user_id : str
            User ID
        service : str
            Service

        Returns
        -------
        None
        """
        self.cursor.execute(
            f"DELETE FROM {self.service_table} WHERE user_id = ? AND service = ?",  # Fixed: Correct table name
            (user_id, service),
        )
        self.connection.commit()

    def delete_auth(self, user_id: str) -> None:
        """
        Deletes an auth record

        Parameters
        ----------
        user_id : str
            User ID

        Returns
        -------
        None
        """
        self.cursor.execute(
            f"DELETE FROM {self.auth_table} WHERE user_id = ?",
            (user_id,),
        )
        self.connection.commit()

    def update_service(
        self,
        user_id: str,
        service: str,
        data: ServiceData,
    ) -> None:
        """
        Updates a service record

        Parameters
        ----------
        user_id : str
            User ID
            service : str
            Service
            data : ServiceData
            Data

        Returns
            -------
            None
        """
        self.cursor.execute(
            f"UPDATE {self.service_table} SET username = ?, seed = ? WHERE user_id = ? AND service = ?",
            (data["username"], data["seed"], user_id, service),
        )
        self.connection.commit()

    def is_registered(self) -> bool:
        """
        Checks if any user is registered

        Returns
        -------
        bool
            True if the database is registered, False otherwise
        """
        self.cursor.execute(
            f"SELECT name FROM sqlite_master WHERE type='table' AND name='{self.auth_table}'",
        )
        return self.cursor.fetchone() is not None

    def close(self):
        """
        Closes the database connection
        """
        self.cursor.close()
        self.connection.close()
