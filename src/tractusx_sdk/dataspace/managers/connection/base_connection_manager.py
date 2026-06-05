#################################################################################
# Eclipse Tractus-X - Software Development KIT
#
# Copyright (c) 2026 LKS Next
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

from abc import ABC, abstractmethod

class BaseConnectionManager(ABC):
    TRANSFER_ID_KEY = "transferProcessId"
    
    @abstractmethod
    def __init__(self):
        raise NotImplementedError
    
    @abstractmethod
    def add_connection(self, counter_party_id: str, counter_party_address: str, query_checksum: str, policy_checksum: str, connection_entry:dict) -> str | None:
        """
        Adds a connection to the open connections dictionary.

        :param counter_party_id: The ID of the counter party.
        :param counter_party_address: The address of the counter party.
        :param query_checksum: The checksum of the filter expression query.
        :param policy_checksum: The checksum of the policy.
        :param transfer_id: The ID of the transfer.
        """
        raise NotImplementedError("This method should be implemented by subclasses.")
        
    @abstractmethod
    def get_connection(self, counter_party_id: str, counter_party_address: str, query_checksum: str, policy_checksum: str) -> dict | None:
        """
        Gets a connection to the open connections dictionary.

        :param counter_party_id: The ID of the counter party.
        :param counter_party_address: The address of the counter party.
        :param query_checksum: The checksum of the filter expression query.
        :param policy_checksum: The checksum of the policy.
        :param transfer_id: The ID of the transfer.
        """
        raise NotImplementedError("This method should be implemented by subclasses.")

    @abstractmethod
    def get_connection_transfer_id(self, counter_party_id: str, counter_party_address: str, query_checksum: str, policy_checksum: str) -> str | None:
        """
        Gets a connection transfer ID from the open connections dictionary.

        :param counter_party_id: The ID of the counter party.
        :param counter_party_address: The address of the counter party.
        :param query_checksum: The checksum of the filter expression query.
        :param policy_checksum: The checksum of the policy.
        :param transfer_id: The ID of the transfer.
        """
        raise NotImplementedError("This method should be implemented by subclasses.")
    
    @abstractmethod
    def delete_connection(self, counter_party_id: str, counter_party_address: str, query_checksum: str, policy_checksum: str) -> bool:
        """
        Gets a connection to the open connections dictionary.

        :param counter_party_id: The ID of the counter party.
        :param counter_party_address: The address of the counter party.
        :param query_checksum: The checksum of the filter expression query.
        :param policy_checksum: The checksum of the policy.
        :param transfer_id: The ID of the transfer.
        """
        raise NotImplementedError("This method should be implemented by subclasses.")

    @abstractmethod
    def clear_connections_by_party(self, counter_party_id_substring: str) -> int:
        """
        Removes all cached EDR connections whose ``counter_party_id`` key contains
        ``counter_party_id_substring``.

        This is necessary because the connection cache stores entries keyed by the
        full counterparty DID (e.g. ``did:web:wallet.example.com:BPNL000000000065``)
        while callers often only know the short BPN form.  A substring match covers
        both the plain-BPN and the DID-wrapped form without requiring the caller to
        resolve the DID first.

        :param counter_party_id_substring: A string that must appear inside the
            ``counter_party_id`` key (e.g. ``"BPNL000000000065"``).
        :returns: The number of top-level party entries that were removed.
        """
        raise NotImplementedError("This method should be implemented by subclasses.")