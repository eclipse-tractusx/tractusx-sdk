#################################################################################
# Eclipse Tractus-X - Software Development KIT
#
# Copyright (c) 2025 Contributors to the Eclipse Foundation
#
# See the NOTICE file(s) distributed with this work for additional
# information regarding copyright ownership.
#
# This program and the accompanying materials are made available under the
# terms of the Apache License, Version 2.0 which is available at
# https://www.apache.org/licenses/LICENSE-2.0.
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND,
# either express or implied. See the
# License for the specific language govern in permissions and limitations
# under the License.
#
# SPDX-License-Identifier: Apache-2.0
#################################################################################
## Code created partially using a LLM (GPT 4o) and reviewed by a human committer

from sqlmodel import Session, select
from ..base_connection_manager import BaseConnectionManager
from ....models.connection.database.edr_base import EDRBase
from sqlalchemy.engine import Engine as E
from sqlalchemy.orm import Session as S
from ....constants import JSONLDKeys
import logging

class PostgresConnectionManager(BaseConnectionManager):
    def __init__(self, engine: E | S, provider_id_key: str = "providerId", table_name: str = "edr_connections", logger:logging.Logger=None, debug: bool = False):
        """
        Initialize the PostgresConnectionManager.

        Args:
            engine (Engine | Session): SQLAlchemy engine or session to interact with the database.
            provider_id_key (str): The key used to identify the provider ID in the connection data.
            table_name (str): The name of the table to store EDR connections.
            logger (logging.Logger, optional): Logger instance for outputting messages.
            debug (bool): Whether to output debug log messages.
        """
        # Store the provided engine and configuration details
        self.engine = engine
        self.provider_id_key = provider_id_key
        self.table_name = table_name
        self.logger = logger
        self.debug = debug

        # Define a dynamic SQLModel class tied to the specified table name for storing EDR connections
        class DynamicEDRConnection(EDRBase, table=True):
            __tablename__ = table_name
            __table_args__ = {"extend_existing": True}

        self.EDRConnection = DynamicEDRConnection
        # Ensure the database table exists based on the dynamic class definition
        DynamicEDRConnection.metadata.create_all(engine)

    def add_connection(self, counter_party_id: str, counter_party_address: str, query_checksum: str, policy_checksum: str, connection_entry: dict) -> str | None:
        """
        Adds a new EDR connection to the database if it doesn't already exist.

        Args:
            counter_party_id (str): The ID of the counter party.
            counter_party_address (str): The address of the counter party.
            query_checksum (str): A checksum identifying the query.
            policy_checksum (str): A checksum identifying the policy.
            connection_entry (dict): The EDR connection data.

        Returns:
            str | None: The transfer process ID of the added connection, or None if not added.
        """
        # Extract transfer process ID from the EDR entry and validate it exists
        transfer_process_id: str = connection_entry.get(JSONLDKeys.AT_ID, None)
        if not transfer_process_id:
            raise Exception("[Postgres Connection Manager] The transfer id key was not found or is empty! Not able to do the contract negotiation!")

        # Remove metadata fields that are not needed for storage
        saved_edr = connection_entry.copy()
        saved_edr.pop(JSONLDKeys.AT_TYPE, None)
        saved_edr.pop(self.provider_id_key, None)
        saved_edr.pop(JSONLDKeys.AT_CONTEXT, None)

        # Prepare the ORM model instance for insertion
        new_entry = self.EDRConnection(
            counter_party_id=counter_party_id,
            counter_party_address=counter_party_address,
            query_checksum=query_checksum,
            policy_checksum=policy_checksum,
            transfer_id=transfer_process_id,
            edr_data=saved_edr
        )

        # Check for existing connection with the same transfer_id to avoid duplicates
        with Session(self.engine) as session:
            if not session.get(self.EDRConnection, transfer_process_id):
                session.add(new_entry)
                session.commit()
                if self.logger and self.debug:
                    self.logger.info("[Postgres Connection Manager] A new EDR entry was saved in the database.")
        return transfer_process_id

    def get_connection(self, counter_party_id, counter_party_address, query_checksum, policy_checksum):
        """
        Retrieves the EDR connection data for the given parameters.

        Args:
            counter_party_id (str): The ID of the counter party.
            counter_party_address (str): The address of the counter party.
            query_checksum (str): A checksum identifying the query.
            policy_checksum (str): A checksum identifying the policy.

        Returns:
            dict: The EDR connection data or an empty dict if not found.
        """
        # Build a query to retrieve the EDR connection based on the provided keys
        stmt = select(self.EDRConnection).where(
            self.EDRConnection.counter_party_id == counter_party_id,
            self.EDRConnection.counter_party_address == counter_party_address,
            self.EDRConnection.query_checksum == query_checksum,
            self.EDRConnection.policy_checksum == policy_checksum
        )
        # Execute the query and return the stored EDR data if found, otherwise return an empty dict
        with Session(self.engine) as session:
            result = session.exec(stmt).first()
        return result.edr_data if result else {}

    def get_connection_transfer_id(self, counter_party_id, counter_party_address, query_checksum, policy_checksum):
        """
        Retrieves the transfer process ID for the given parameters.

        Args:
            counter_party_id (str): The ID of the counter party.
            counter_party_address (str): The address of the counter party.
            query_checksum (str): A checksum identifying the query.
            policy_checksum (str): A checksum identifying the policy.

        Returns:
            str | None: The transfer process ID if found, otherwise None.
        """
        # Build a query to retrieve only the transfer process ID for the provided keys
        stmt = select(self.EDRConnection.transfer_id).where(
            self.EDRConnection.counter_party_id == counter_party_id,
            self.EDRConnection.counter_party_address == counter_party_address,
            self.EDRConnection.query_checksum == query_checksum,
            self.EDRConnection.policy_checksum == policy_checksum
        )
        # Execute the query and return the transfer process ID if found, otherwise None
        with Session(self.engine) as session:
            result = session.exec(stmt).first()
        return result if result else None

    def delete_connection(self, counter_party_id: str, counter_party_address: str, query_checksum: str, policy_checksum: str) -> bool:
        """
        Deletes the EDR connection matching the given parameters from the database.

        Args:
            counter_party_id (str): The ID of the counter party.
            counter_party_address (str): The address of the counter party.
            query_checksum (str): A checksum identifying the query.
            policy_checksum (str): A checksum identifying the policy.

        Returns:
            bool: True if the connection was deleted, False if not found.
        """
        # Build a query to find the specific EDR connection for deletion
        stmt = select(self.EDRConnection).where(
            self.EDRConnection.counter_party_id == counter_party_id,
            self.EDRConnection.counter_party_address == counter_party_address,
            self.EDRConnection.query_checksum == query_checksum,
            self.EDRConnection.policy_checksum == policy_checksum
        )
        # If found, delete the connection and commit the transaction
        # Log the action if debug logging is enabled
        # Return True if deleted, False if not found
        with Session(self.engine) as session:
            result = session.exec(stmt).first()
            if result:
                session.delete(result)
                session.commit()
                if self.logger and self.debug:
                    self.logger.info(f"[Postgres Connection Manager] Deleted EDR entry for policy checksum '{policy_checksum}'.")
                return True
            else:
                if self.logger and self.debug:
                    self.logger.info(f"[Postgres Connection Manager] No EDR found to delete for the provided keys.")
                return False