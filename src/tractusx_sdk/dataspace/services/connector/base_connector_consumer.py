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

from ..service import BaseService
from ...adapters.connector.adapter_factory import AdapterFactory
from ...controllers.connector.base_dma_controller import BaseDmaController
from ...controllers.connector.controller_factory import ControllerFactory, ControllerType
from requests import Response
from .base_connector_service import BaseConnectorService
from ...managers.connection.base_connection_manager import BaseConnectionManager
from ...managers.connection.memory import MemoryConnectionManager

class BaseConnectorConsumerService(BaseService):
    _catalog_controller: BaseDmaController
    _edr_controller: BaseDmaController
    _contract_negotiation_controller: BaseDmaController
    _transfer_process_controller: BaseDmaController
    connection_manager: BaseConnectionManager
    
    def __init__(self, controllers: dict, connection_manager:BaseConnectionManager = None):
        if connection_manager is None:
            connection_manager = MemoryConnectionManager()
        self._catalog_controller = controllers.get(ControllerType.CATALOG)
        self._edr_controller = controllers.get(ControllerType.EDR)
        self._contract_negotiation_controller = controllers.get(ControllerType.CONTRACT_NEGOTIATION)
        self._transfer_process_controller = controllers.get(ControllerType.TRANSFER_PROCESS)
    
    @property
    def catalogs(self):
        return self._catalog_controller
    
    @property
    def edrs(self):
        return self._edr_controller
    
    @property
    def contract_negotiations(self):
        return self._contract_negotiation_controller
    
    @property
    def transfer_processes(self):
        return self._transfer_process_controller
    
    def get_edr(self, transfer_id: str) -> dict | None:
        """
        Gets and EDR Token.

        This function sends a GET request to the EDC to retrieve the EDR (Endpoint Data Reference) 
        token for the given transfer ID. The EDR token is used to access the data behind the EDC.

        Parameters:
        transfer_id (str): The unique identifier for the transfer process.

        Returns:
        dict | None: The response content from the GET request, or None if the request fails.

        Raises:
        Exception: If the EDC response is not successful (status code is not 200).
        """
        ## Build edr transfer url
        response:Response = self.edrs.get_data_address_with_token_refresh(oid=transfer_id)
        if (response is None or response.status_code != 200):
            raise Exception(
                "[EDC Service] It was not possible to get the edr because the EDC response was not successful!")
        return response.json()
    
    def get_endpoint_with_token(self, transfer_id: str) -> tuple[str, str]:
        """
        @returns: tuple[dataplane_endpoint:str, authorization:str]
        """
        ## Get authorization key from the edr
        edr: dict = self.get_edr(transfer_id=transfer_id)
        if (edr is None):
            raise Exception("[EDC Service] It was not possible to retrieve the edr token and the dataplane endpoint!")

        return edr["endpoint"], edr["authorization"]
    
    def get_transfer_id(self, counter_party_id: str, counter_party_address: str, dct_type: str,
                        policies: list = None) -> str:

        """
        Checks if the transfer is already available at the location or not...

        Parameters:
        counter_party_id (str): The identifier of the counterparty (Business Partner Number [BPN]).
        counter_party_address (str): The URL of the EDC provider.
        policies (list, optional): The policies to be used for the transfer. Defaults to None.
        dct_type (str, optional): The DCT type to be used for the transfer

        Returns:
        str: The transfer ID.

        Raises:
        Exception: If the EDR entry is not found or the transfer ID is not available.
        """

        ## Hash the policies to get checksum. 
        curent_policies_checksum = hashlib.sha3_256(str(policies).encode('utf-8')).hexdigest()

        self.connection_manager.get_connection(counter_party_id=counter_party_id,
                                                   counter_party_address=counter_party_address,
                                                   oid=dct_type, policy_checksum=curent_policies_checksum)
        
        if(self.connection_manager.get_connection(counter_party_id=counter_party_id,
                                                   counter_party_address=counter_party_address,
                                                   oid=dct_type, policy_checksum=curent_policies_checksum) is not None):
            
        ## If the countrer party id is already available and also the dct type is in the counter_party_id and the transfer key is also present
        counterparty_data: dict = self.cached_edrs.get(counter_party_id, {})
        edc_data: dict = counterparty_data.get(counter_party_address, {})
        dct_data: dict = edc_data.get(dct_type, {})

        ## Get policies checksum
        cached_entry: dict = dct_data.get(curent_policies_checksum, {})

        ## Get the edr
        transfer_id: str | None = cached_entry.get(self.TRANSFER_ID_KEY, None)

        ## If is there return the cached one, if the selection is the same the transfer id can be reused!
        if (transfer_id is not None):
            logger.info(
                "[EDC Service] [%s]: EDR transfer_id=[%s] found in the cache for counter_party_id=[%s], dct_type=[%s] and selected policies",
                counter_party_address, transfer_id, counter_party_id, dct_type)
            return transfer_id

        logger.info(
            "[EDC Service] The EDR was not found in the cache for counter_party_address=[%s], counter_party_id=[%s], dct_type=[%s] and selected policies, starting new contract negotiation!",
            counter_party_address, counter_party_id, dct_type)

        ## If not the contract negotiation MUST be done!
        edr_entry: dict = self.negotiate_and_transfer(counter_party_id=counter_party_id,
                                                      counter_party_address=counter_party_address, policies=policies,
                                                      dct_type=dct_type)

        ## Check if the edr entry is not none
        if (edr_entry is None):
            raise Exception("[EDC Service] Failed to get edr entry! Response was none!")

        ## Check if the transfer id is available
        transfer_process_id: str = edr_entry.get(self.TRANSFER_ID_KEY, None)
        if transfer_process_id is None or transfer_process_id == "":
            raise Exception(
                "[EDC Service] The transfer id key was not found or is empty! Not able to do the contract negotiation!")

        logger.info(f"[EDC Service] The EDR Entry was found! Transfer Process ID: [{transfer_process_id}]")

        ## Check if the contract negotiation was alredy specified
        if counter_party_id not in self.cached_edrs:
            self.cached_edrs[counter_party_id] = {}

        ## Using pointers update the memory cache
        cached_edcs = self.cached_edrs[counter_party_id]

        ## Check if the dct type is already available
        if counter_party_address not in cached_edcs:
            cached_edcs[counter_party_address] = {}

        cached_dct_types = cached_edcs[counter_party_address]

        ## Check if the dct type is already available in the EDC
        if dct_type not in cached_dct_types:
            cached_dct_types[dct_type] = {}

        cached_details = cached_dct_types[dct_type]

        ## Store the edr entry!
        if curent_policies_checksum not in cached_details:
            cached_details[curent_policies_checksum] = {}

        ## Prepare edr to be stored in cache
        saved_edr = copy.deepcopy(edr_entry)
        del saved_edr["@type"], saved_edr["providerId"], saved_edr["@context"]

        ## Store edr in cache
        cached_details[curent_policies_checksum] = saved_edr

        if "edrs" not in self.cached_edrs:
            self.cached_edrs["edrs"] = 0

        self.cached_edrs["edrs"] += 1

        logger.info(
            f"[EDC Service] A new EDR entry was saved in the memory cache! [{self.cached_edrs['edrs']}] EDRs Available")

        return transfer_process_id  ## Return transfer_process_id!
    
    def do_dsp(self, counter_party_id: str, counter_party_address: str, dct_type: str, policies: list = None) -> tuple[
        str, str]:
        """
        Does all the dsp necessary operations until getting the edr.
        Giving you all the necessary data to request data to the edc dataplane.

        @param counter_party_id: The identifier of the counterparty (Business Partner Number [BPN]).
        @param counter_party_address: The URL of the EDC provider.
        @param policies: The policies to be used for the transfer. Defaults to None.
        @param dct_type: The DCT type to be used for the transfer. Defaults to "IndustryFlagService".
        @returns: tuple[dataplane_endpoint:str, edr_access_token:str] or if fail Exception
        """

        ## If policies are empty use default policies
        if policies is None:
            policies = self.default_policies

        ## Get the transfer id 
        transfer_id = self.get_transfer_id(counter_party_id=counter_party_id,
                                           counter_party_address=counter_party_address, policies=policies,
                                           dct_type=dct_type)
        ## Get the endpoint and the token
        return self.get_endpoint_with_token(transfer_id=transfer_id)
    
