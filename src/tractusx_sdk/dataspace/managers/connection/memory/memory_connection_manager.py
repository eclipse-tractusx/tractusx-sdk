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

"""
Memory-based connection manager for storing EDR connections in an in-memory cache.
Provides thread-safe methods for adding, retrieving, and deleting EDR connections.
"""

import copy
from tractusx_sdk.dataspace.managers.connection.base_connection_manager import BaseConnectionManager
from tractusx_sdk.dataspace.constants import JSONLDKeys
import threading
import logging

class MemoryConnectionManager(BaseConnectionManager):
    """
    Manages EDR connections in an in-memory cache with thread-safe operations.
    """

    def __init__(self, provider_id_key: str = "providerId", edrs_key: str = "edrs", logger:logging.Logger=None, verbose: bool = False):
        """
        Initializes the MemoryConnectionManager with specified keys for provider ID and EDR count.

        Args:
            provider_id_key (str): Key used to identify the provider ID in the connection data.
            edrs_key (str): Key used to store the EDR count within the open_connections dictionary.
        """
        # Initialize the connection cache and thread lock for concurrency.
        self.provider_id_key = provider_id_key
        self.edrs_key = edrs_key
        self.open_connections=dict()
        self._lock = threading.RLock()
        self.logger = logger
        self.verbose = verbose
        
    def add_connection(self, counter_party_id: str, counter_party_address: str, query_checksum: str, policy_checksum: str, connection_entry:dict) -> str | None:
        """
        Adds a new EDR connection to the in-memory cache.

        Args:
            counter_party_id (str): The ID of the counter party.
            counter_party_address (str): The address of the counter party.
            query_checksum (str): Checksum identifying the query.
            policy_checksum (str): Checksum identifying the policy.
            connection_entry (dict): The EDR connection data.

        Returns:
            str | None: The transfer process ID of the added connection.
        """
        # Verify the transfer process ID exists.
        with self._lock:
            transfer_process_id: str = connection_entry.get(self.TRANSFER_ID_KEY, None)
            if transfer_process_id is None or transfer_process_id == "":
                raise Exception(
                    "[Memory Connection Manager] The transfer id key was not found or is empty! Not able to do the contract negotiation!")
            
            # Initialize nested dictionaries as needed.
            if counter_party_id not in self.open_connections:
                self.open_connections[counter_party_id] = {}

            cached_edcs = self.open_connections[counter_party_id]

            if counter_party_address not in cached_edcs:
                cached_edcs[counter_party_address] = {}

            cached_oids = cached_edcs[counter_party_address]

            if query_checksum not in cached_oids:
                cached_oids[query_checksum] = {}

            cached_details = cached_oids[query_checksum]
            
            if policy_checksum not in cached_details:
                cached_details[policy_checksum] = {}

            # Remove metadata fields and store the cleaned EDR.
            saved_edr = copy.deepcopy(connection_entry)
            del saved_edr[JSONLDKeys.AT_TYPE], saved_edr[self.provider_id_key], saved_edr[JSONLDKeys.AT_CONTEXT]

            # Store edr in cache
            cached_details[policy_checksum] = saved_edr
            
            # Increment the count of stored EDRs.
            if self.edrs_key not in self.open_connections:
                self.open_connections[self.edrs_key] = 0

            self.open_connections[self.edrs_key] += 1
            if self.logger and self.verbose:
                self.logger.info(
                    f"[Memory Connection Manager] A new EDR entry was saved in the memory cache! [{self.open_connections[self.edrs_key]}] EDRs Available")
            return transfer_process_id
    
    def get_connection(self, counter_party_id, counter_party_address, query_checksum, policy_checksum):
        """
        Retrieves a specific EDR connection from the cache.

        Args:
            counter_party_id (str): The ID of the counter party.
            counter_party_address (str): The address of the counter party.
            query_checksum (str): Checksum identifying the query.
            policy_checksum (str): Checksum identifying the policy.

        Returns:
            dict: The EDR connection data, or an empty dict if not found.
        """
        # Safely navigate the nested dictionaries to retrieve the stored connection.
        with self._lock:
            counterparty_data: dict = self.open_connections.get(counter_party_id, {})
            edc_data: dict = counterparty_data.get(counter_party_address, {})
            oid_data: dict = edc_data.get(query_checksum, {})
            cached_entry: dict = oid_data.get(policy_checksum, {})
        
        return cached_entry
    
    def get_connection_transfer_id(self, counter_party_id, counter_party_address, query_checksum, policy_checksum):
        """
        Retrieves the transfer process ID for a given EDR connection.

        Args:
            counter_party_id (str): The ID of the counter party.
            counter_party_address (str): The address of the counter party.
            query_checksum (str): Checksum identifying the query.
            policy_checksum (str): Checksum identifying the policy.

        Returns:
            str | None: The transfer process ID if found, else None.
        """
        with self._lock:
            cached_entry: dict = self.get_connection(counter_party_id, counter_party_address, query_checksum, policy_checksum)
            transfer_id: str | None = cached_entry.get(self.TRANSFER_ID_KEY, None)
        
        return transfer_id
    
    
    def delete_connection(self, counter_party_id: str, counter_party_address: str, query_checksum: str, policy_checksum: str) -> bool:
        """
        Deletes an EDR connection from the cache.

        Args:
            counter_party_id (str): The ID of the counter party.
            counter_party_address (str): The address of the counter party.
            query_checksum (str): Checksum identifying the query.
            policy_checksum (str): Checksum identifying the policy.

        Returns:
            bool: True if the connection was deleted, False otherwise.
        """
        # Safely attempt to remove the specified connection.
        # Decrement the EDR count if successful.
        with self._lock:
            try:
                cached_details = self.open_connections[counter_party_id][counter_party_address][query_checksum]
                if policy_checksum in cached_details:
                    del cached_details[policy_checksum]
                    if self.edrs_key in self.open_connections:
                        self.open_connections[self.edrs_key] -= 1
                    if self.logger and self.verbose:
                        self.logger.info(f"[Memory Connection Manager] Deleted EDR entry for policy checksum '{policy_checksum}'.")
                    return True
                return False
            except KeyError:
                if self.logger and self.verbose:
                    self.logger.error("[Memory Connection Manager] No EDR found to delete for the provided keys.")
                return False
