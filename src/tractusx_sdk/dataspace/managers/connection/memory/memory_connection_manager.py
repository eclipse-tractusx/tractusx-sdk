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
import copy
from ..base_connection_manager import BaseConnectionManager
from ....constants import JSONLDKeys

class MemoryConnectionManager(BaseConnectionManager):

    def __init__(self, provider_id_key: str = "providerId", edrs_key: str = "edrs"):
        """
        Initializes the MemoryConnectionManager with the given parameters.
        """
        self.provider_id_key = provider_id_key
        self.edrs_key = edrs_key
        self.open_connections=dict()
        
    def add_connection(self, counter_party_id: str, counter_party_address: str, query_checksum: str, policy_checksum: str, connection_entry:dict) -> str | None:
        transfer_process_id: str = connection_entry.get(self.TRANSFER_ID_KEY, None)
        if transfer_process_id is None or transfer_process_id == "":
            raise Exception(
                "[Memory Connection Manager] The transfer id key was not found or is empty! Not able to do the contract negotiation!")
        
        ## Check if the contract negotiation was alredy specified
        if counter_party_id not in self.open_connections:
            self.open_connections[counter_party_id] = {}

        ## Using pointers update the memory cache
        cached_edcs = self.open_connections[counter_party_id]

        ## Check if the dct type is already available
        if counter_party_address not in cached_edcs:
            cached_edcs[counter_party_address] = {}

        cached_oids = cached_edcs[counter_party_address]

        ## Check if the dct type is already available in the EDC
        if query_checksum not in cached_oids:
            cached_oids[query_checksum] = {}

        cached_details = cached_oids[query_checksum]
        
        if policy_checksum not in cached_details:
            cached_details[policy_checksum] = {}

        saved_edr = copy.deepcopy(connection_entry)
        del saved_edr[JSONLDKeys.AT_TYPE], saved_edr[self.provider_id_key], saved_edr[JSONLDKeys.AT_CONTEXT]

        ## Store edr in cache
        cached_details[policy_checksum] = saved_edr
        
        if self.edrs_key not in self.open_connections:
            self.open_connections[self.edrs_key] = 0

        self.open_connections[self.edrs_key] += 1
        print(
            f"[Memory Connection Manager] A new EDR entry was saved in the memory cache! [{self.open_connections[self.edrs_key]}] EDRs Available")
        return transfer_process_id
    
    def get_connection(self, counter_party_id, counter_party_address, query_checksum, policy_checksum):
        ## If the countrer party id is already available and also the dct type is in the counter_party_id and the transfer key is also present
        counterparty_data: dict = self.open_connections.get(counter_party_id, {})
        edc_data: dict = counterparty_data.get(counter_party_address, {})
        oid_data: dict = edc_data.get(query_checksum, {})
        ## Get policies checksum
        cached_entry: dict = oid_data.get(policy_checksum, {})
        return cached_entry
    
    def get_connection_transfer_id(self, counter_party_id, counter_party_address, query_checksum, policy_checksum):
        cached_entry: dict = self.get_connection(counter_party_id, counter_party_address, query_checksum, policy_checksum)
        transfer_id: str | None = cached_entry.get(self.TRANSFER_ID_KEY, None)
        return transfer_id
    
    
    def delete_connection(self, counter_party_id: str, counter_party_address: str, query_checksum: str, policy_checksum: str) -> bool:
        try:
            cached_details = self.open_connections[counter_party_id][counter_party_address][query_checksum]
            if policy_checksum in cached_details:
                del cached_details[policy_checksum]
                if self.edrs_key in self.open_connections:
                    self.open_connections[self.edrs_key] -= 1
                print(f"[Memory Connection Manager] Deleted EDR entry for policy checksum '{policy_checksum}'.")
                return True
            return False
        except KeyError:
            print(f"[Memory Connection Manager] No EDR found to delete for the provided keys.")
            return False