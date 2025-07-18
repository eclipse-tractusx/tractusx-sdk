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

import hashlib
import threading
import logging

from requests import Response

from ..service import BaseService
from ...adapters.connector.adapter_factory import AdapterFactory
from ...controllers.connector.base_dma_controller import BaseDmaController
from ...controllers.connector.controller_factory import ControllerType, ControllerFactory
from ...managers.connection.base_connection_manager import BaseConnectionManager
from ...managers.connection.memory import MemoryConnectionManager
from ...models.connector.model_factory import ModelFactory
from ...models.connector.base_catalog_model import BaseCatalogModel
from ...models.connector.base_contract_negotiation_model import BaseContractNegotiationModel
from ...models.connector.base_queryspec_model import BaseQuerySpecModel
from ...tools import HttpTools, DspTools, op
from ...constants import JSONLDKeys, ODRLTypes

class BaseConnectorConsumerService(BaseService):
    _catalog_controller: BaseDmaController
    _edr_controller: BaseDmaController
    _contract_negotiation_controller: BaseDmaController
    _transfer_process_controller: BaseDmaController

    connection_manager: BaseConnectionManager
    dataspace_version: str

    NEGOTIATION_ID_KEY = "contractNegotiationId"

    def __init__(self, dataspace_version: str, base_url: str, dma_path: str, headers: dict = None,
                 connection_manager: BaseConnectionManager = None, verbose: bool = True, logger: logging.Logger = None):
        self.dataspace_version = dataspace_version
        self.verbose = verbose
        self.logger = logger
        # Backwards compatibility: if verbose is True and no logger provided, use default logger
        if self.verbose and self.logger is None:
            self.logger = logging.getLogger(__name__)

        dma_adapter = AdapterFactory.get_dma_adapter(
            dataspace_version=dataspace_version,
            base_url=base_url,
            dma_path=dma_path,
            headers=headers
        )

        controllers = ControllerFactory.get_dma_controllers_for_version(
            dataspace_version=dataspace_version,
            adapter=dma_adapter,
            controller_types=[
                ControllerType.CATALOG,
                ControllerType.EDR,
                ControllerType.CONTRACT_NEGOTIATION,
                ControllerType.TRANSFER_PROCESS
            ]
        )

        self._catalog_controller = controllers.get(ControllerType.CATALOG)
        self._edr_controller = controllers.get(ControllerType.EDR)
        self._contract_negotiation_controller = controllers.get(ControllerType.CONTRACT_NEGOTIATION)
        self._transfer_process_controller = controllers.get(ControllerType.TRANSFER_PROCESS)

        self.connection_manager = connection_manager if connection_manager is not None else MemoryConnectionManager()

    class _Builder(BaseService._Builder):
        def dma_path(self, dma_path: str):
            self._data["dma_path"] = dma_path
            return self

        def connector_manager(self, connection_manager: BaseConnectionManager):
            self._data["connection_manager"] = connection_manager
            return self

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

    def get_data_plane_headers(self, access_token, content_type=None):
        ## Build the headers needed for the edc the app to communicate with the edc data plane
        headers = {
            "Accept": "*/*",
            "Authorization": access_token
        }

        if content_type is not None:
            headers["Content-Type"] = content_type

        return headers

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
        response: Response = self.edrs.get_data_address(oid=transfer_id, params={"auto_refresh": True})
        if (response is None or response.status_code != 200):
            raise ConnectionError(
                "[EDC Service] It was not possible to get the edr because the EDC response was not successful!")
        return response.json()

    def get_endpoint_with_token(self, transfer_id: str) -> tuple[str, str]:
        """
        @returns: tuple[dataplane_endpoint:str, authorization:str]
        """
        ## Get authorization key from the edr
        edr: dict = self.get_edr(transfer_id=transfer_id)
        if (edr is None):
            raise RuntimeError("[EDC Service] It was not possible to retrieve the edr token and the dataplane endpoint!")

        return edr["endpoint"], edr["authorization"]

    def get_catalog(self, counter_party_id: str = None, counter_party_address: str = None,
                    request: BaseCatalogModel = None, timeout=60) -> dict | None:
        """
        Retrieves the EDC DCAT catalog. Allows to get the catalog without specifying the request, which can be overridden
        
        Parameters:
        counter_party_address (str): The URL of the EDC provider.
        request (BaseCatalogModel, optional): The request payload for the catalog API. If not provided, a default request will be used.

        Returns:
        dict | None: The EDC catalog as a dictionary, or None if the request fails.
        """
        ## Get EDC DCAT catalog
        if request is None:
            if counter_party_id is None or counter_party_address is None:
                raise ValueError(
                    "[EDC Service] Either request or counter_party_id and counter_party_address are required to build a catalog request")
            request = self.get_catalog_request(counter_party_id=counter_party_id,
                                               counter_party_address=counter_party_address)
        ## Get catalog with configurable timeout
        response: Response = self.catalogs.get_catalog(obj=request, timeout=timeout)
        ## In case the response code is not successfull or the response is null
        if response is None or response.status_code != 200:
            raise ConnectionError(
                f"[EDC Service] It was not possible to get the catalog from the EDC provider! Response code: [{response.status_code}]")
        return response.json()

    ## Simple catalog request with filter

    def get_filter_expression(self, key: str, value: str, operator: str = "=") -> dict:
        """
        Prepares a filter expression for querying the catalog.

        Parameters:
        key (str): The key for the filter condition.
        value (str): The value for the filter condition.
        operator (str): The operator for the filter condition. Default is "=" (equal).

        Returns:
        dict: A dictionary representing the filter expression.
        """
        return {
            "operandLeft": key,
            "operator": operator,
            "operandRight": value
        }

    def get_query_spec(self, filter_expression: list[dict]) -> dict:
        return {
            JSONLDKeys.AT_CONTEXT: {
                "@vocab": "https://w3id.org/edc/v0.0.1/ns/"
            },
            JSONLDKeys.AT_TYPE: "QuerySpec",
            "filterExpression": filter_expression
        }

    def get_catalog_request_with_filter(self, counter_party_id: str, counter_party_address: str,
                                        filter_expression: list[dict]) -> BaseCatalogModel:
        """
        Prepares a catalog request with a filter for a specific key-value pair.

        Parameters:
        counter_party_id (str): The identifier of the counterparty (Business Partner Number [BPN]).
        counter_party_address (str): The URL of the EDC provider.
        key (str): The key for the filter condition.
        value (str): The value for the filter condition.
        operator (str): The operator for the filter condition. Default is "=" (equal).

        Returns:
        dict: A catalog request with the filter condition included.
        """
        catalog_request: BaseCatalogModel = self.get_catalog_request(counter_party_id=counter_party_id,
                                                                     counter_party_address=counter_party_address)

        catalog_request.queryspec = self.get_query_spec(filter_expression=filter_expression)

        return catalog_request

    def get_edr_negotiation_request(self, counter_party_id: str, counter_party_address: str, target: str,
                                    policy: dict) -> BaseContractNegotiationModel:
        """
        Builds the EDR Negotiation Request.

        Parameters:
        counter_party_id (str): The identifier of the counterparty (Business Partner Number [BPN]).
        counter_party_address (str): The URL of the EDC provider.
        target (str): The target asset identifier.
        policy (dict): The policy to be negotiated.

        Returns:
        dict: The EDR negotiation request in the form of a dictionary.
        """
        offer_id = policy.get(JSONLDKeys.AT_ID, None)
        if (offer_id is None):
            raise ValueError("[EDC Service] Policy offer id is not available!")

        return ModelFactory.get_contract_negotiation_model(
            dataspace_version=self.dataspace_version,  # version is to be included in the BaseService class  
            context=[
                "https://w3id.org/tractusx/policy/v1.0.0",
                "http://www.w3.org/ns/odrl.jsonld",
                {
                    "@vocab": "https://w3id.org/edc/v0.0.1/ns/"
                }
            ],
            counter_party_address=counter_party_address,
            offer_id=offer_id,
            asset_id=target,
            provider_id=counter_party_id,
            offer_policy=policy
        )

        ## Simple catalog request without filter

    def get_catalog_request(self, counter_party_id: str, counter_party_address: str) -> BaseCatalogModel:
        return ModelFactory.get_catalog_model(
            dataspace_version=self.dataspace_version,
            context={
                "edc": "https://w3id.org/edc/v0.0.1/ns/",
                "odrl": "http://www.w3.org/ns/odrl/2/",
                "dct": "https://purl.org/dc/terms/"
            },
            counter_party_id=counter_party_id,  ## bpn of the provider
            counter_party_address=counter_party_address,  ## dsp url from the provider
        )

    def start_edr_negotiation(self, counter_party_id: str, counter_party_address: str, target: str,
                              policy: dict) -> str | None:
        """
        Starts the edr negotiation and gives the negotation id

        @param counter_party_id: The identifier of the counterparty (Business Partner Number [BPN]).
        @param counter_party_address: The URL of the EDC provider.
        @param target: The target asset for the negotiation.
        @param policy: The policy to be used for the negotiation.
        @returns: negotiation_id:str or if Fail -> None
        """

        ## Prepare the request
        request: BaseContractNegotiationModel = self.get_edr_negotiation_request(counter_party_id=counter_party_id,
                                                                                 counter_party_address=counter_party_address,
                                                                                 target=target,
                                                                                 policy=policy)

        ## Build catalog api url
        response: Response = self.edrs.create(request)
        ## In case the response code is not successfull or the response is null
        if (response is None or response.status_code != 200):
            return None

        content: dict = response.json()
        ## Check if the id was returned in the response
        if (JSONLDKeys.AT_ID not in content):
            return None

        return content.get(JSONLDKeys.AT_ID, None)

    def get_edr_negotiation_filter(self, negotiation_id: str) -> BaseQuerySpecModel:

        return ModelFactory.get_queryspec_model(
            dataspace_version=self.dataspace_version,
            filter_expression=[
                self.get_filter_expression(key=self.NEGOTIATION_ID_KEY, operator="=", value=negotiation_id)]
        )

    def get_catalogs_by_dct_type(self, counter_party_id: str, edcs: list, dct_type: str,
                                 dct_type_key: str = f"'http://purl.org/dc/terms/type'.'{JSONLDKeys.AT_ID}'", timeout: int = None):
        return self.get_catalogs_with_filter(counter_party_id=counter_party_id, edcs=edcs, key=dct_type_key,
                                             value=dct_type, operator=ODRLTypes.EQUALS, timeout=timeout)

    def get_catalogs_with_filter(self, counter_party_id: str, edcs: list, key: str, value: str, operator: str = ODRLTypes.EQUALS,
                                 timeout: int = None):

        ## Where the catalogs get stored
        catalogs: dict = {}
        threads: list[threading.Thread] = []

        for edc_url in edcs:
            thread = threading.Thread(target=self.get_catalog_with_filter_parallel, kwargs=
            {
                'counter_party_id': counter_party_id,
                'counter_party_address': edc_url,
                'key': key,
                'operator': operator,
                'value': value,
                'timeout': timeout,
                'catalogs': catalogs
            }
                                      )
            thread.start()  ## Start thread
            threads.append(thread)

        ## Allow the threads to process
        for thread in threads:
            thread.join()  ## Waiting until they process

        return catalogs

    def get_catalog_by_dct_type(self, counter_party_id: str, counter_party_address: str, dct_type: str,
                                dct_type_key=f"'http://purl.org/dc/terms/type'.'{JSONLDKeys.AT_ID}'", operator=ODRLTypes.EQUALS, timeout=None):
        return self.get_catalog_with_filter(counter_party_id=counter_party_id,
                                            counter_party_address=counter_party_address, filter_expression=[
                self.get_filter_expression(key=dct_type_key, value=dct_type, operator=operator)],
                                            timeout=timeout)

    def get_catalog_with_filter_parallel(self, counter_party_id: str, counter_party_address: str,
                                         filter_expression: list[dict], catalogs: dict = None,
                                         timeout: int = None) -> None:
        catalogs[counter_party_address] = self.get_catalog_with_filter(counter_party_id=counter_party_id,
                                                                       counter_party_address=counter_party_address,
                                                                       filter_expression=filter_expression,
                                                                       timeout=timeout)

    ## Get catalog request with filter
    def get_catalog_with_filter(self, counter_party_id: str, counter_party_address: str, filter_expression: list[dict],
                                timeout: int = None) -> dict:
        """
        Retrieves a catalog from the EDC provider based on a specified filter.

        Parameters:
        counter_party_id (str): The identifier of the counterparty (Business Partner Number [BPN]).
        counter_party_address (str): The URL of the EDC provider.
        key (str): The key to filter the catalog entries by.
        value (str): The value to filter the catalog entries by.
        operator (str, optional): The comparison operator to use for filtering. Defaults to "=".

        Returns:
        dict: The catalog entries that match the specified filter.
        """
        return self.get_catalog(request=self.get_catalog_request_with_filter(counter_party_id=counter_party_id,
                                                                             counter_party_address=counter_party_address,
                                                                             filter_expression=filter_expression),
                                timeout=timeout)

    def get_edr_entry(self, negotiation_id: str) -> dict | None:
        """
        Gets the edr negotiation details for a given negotiation id

        @param negotiation_id: The unique identifier for the negotiation process.
        
        @returns: EndpointDataReferenceEntry:dict or if Fail -> None

        EndpointDataReferenceEntry Example: 
        ```
            {
                "@id": "04e9ec58-a053-4e40-85d8-35efb4a3a343",
                "@type": "EndpointDataReferenceEntry",
                "providerId": "BPNL000000000T4X",
                "assetId": "urn:uuid:0c3d2db0-e5c6-27f9-5875-15a9a00e7a27",
                "agreementId": "a6816e69-a6ea-491c-b842-3532aafb75dd",
                "transferProcessId": "04e9ec58-a053-4e40-85d8-35efb4a3a343",
                "createdAt": 1729683943014,
                "contractNegotiationId": "d9a0d5a4-1f4d-49a7-9270-2ea5163a2a10",
                "@context": {
                    "@vocab": "https://w3id.org/edc/v0.0.1/ns/",
                    "edc": "https://w3id.org/edc/v0.0.1/ns/",
                    "tx": "https://w3id.org/tractusx/v0.0.1/ns/",
                    "tx-auth": "https://w3id.org/tractusx/auth/",
                    "cx-policy": "https://w3id.org/catenax/policy/",
                    "odrl": "http://www.w3.org/ns/odrl/2/"
                }
            }
        ```
        """

        request: BaseQuerySpecModel = self.get_edr_negotiation_filter(negotiation_id=negotiation_id)

        ## Build catalog api url
        response: Response = self.edrs.query(request)
        ## In case the response code is not successfull or the response is null
        if (response is None or response.status_code != 200):
            raise ConnectionError(f"[EDC Service] EDR Entry not found for the negotiation_id=[{negotiation_id}]!")

        ## The response is a list
        data = response.json()

        if (len(data) == 0):
            return None

        return data.pop()  ## Return last entry of the list (should be just one entry because of the filter)

    def negotiate_and_transfer(self, counter_party_id: str, counter_party_address: str, filter_expression: list[dict],
                               policies: list = None, max_retries: int = 6, timeout: int = 10) -> dict:
        """
        This method checks if there is a transfer process ID available, or if it needs to be negotiated.

        @param counter_party_id: The identifier of the counterparty (Business Partner Number [BPN]).
        @param counter_party_address: The URL of the EDC provider.
        @param policies: The policies to be used for the transfer. Defaults to None.
        @param dct_type: The DCT type to be used for the transfer. Defaults to "IndustryFlagService".
        @returns: edr_entry:dict, if fails Exception
        """
        ##### 1. Get Catalog

        catalog_response = self.get_catalog_with_filter(counter_party_id=counter_party_id,
                                                        counter_party_address=counter_party_address,
                                                        filter_expression=filter_expression)
        if (catalog_response is None):
            raise RuntimeError(
                f"[EDC Service] [{counter_party_address}] It was not possible to retrieve the catalog from the edc provider! Catalog response is empty!")

        ## Select Policy and Assetid
        try:
            valid_assets_policies = DspTools.filter_assets_and_policies(catalog=catalog_response,
                                                                        allowed_policies=policies)
        except Exception as e:
            raise RuntimeError(
                f"[EDC Service] [{counter_party_address}] It was not possible to find a valid policy in the catalog! Reason: [{str(e)}]")

        if (len(valid_assets_policies) == 0):
            raise RuntimeError(
                f"[EDC Service] [{counter_party_address}] It was not possible to find a valid policy in the catalog! Asset ID and the Policy are empty!")

        negotiation_id: str | None = None

        for valid_asset_policy in valid_assets_policies:
            ## Unwrap asset id and policy tuple
            asset_id = valid_asset_policy[0]
            policy = valid_asset_policy[1]

            ##### 2. EDR Negotiation Start

            negotiation_id = self.start_edr_negotiation(counter_party_id=counter_party_id,
                                                        counter_party_address=counter_party_address, target=asset_id,
                                                        policy=policy)
            if (negotiation_id is not None):
                break

        if (negotiation_id is None):
            raise RuntimeError(
                f"[EDC Service] [{counter_party_address}] It was not possible to start the EDR Negotiation! The negotiation id is empty!")

        ##### 3. Get EDC Entry (details)

        retries: int = 0
        edr_entry: dict | None = None
        while edr_entry is None and retries < max_retries:
            edr_entry = self.get_edr_entry(negotiation_id=negotiation_id)
            if edr_entry is not None:  ## If edr is found skip retry
                break
            ## Wait until the timeout has reached to retry again
            if self.logger:
                self.logger.info(
                    f"[EDC Service] Attempt [{retries + 1}]/[{max_retries}]: [{counter_party_address}] The EDR Negotiation [{negotiation_id}] entry was not found! Waiting {timeout} seconds and retrying...")
            op.wait(seconds=timeout)
            retries += 1

        if edr_entry is None:
            raise TimeoutError(
                f"[EDC Service] [{counter_party_address}] The EDR Negotiation [{negotiation_id}] has failed! The EDR entry was not found!")

        return edr_entry

    def get_transfer_id(self, counter_party_id: str, counter_party_address: str, filter_expression: list[dict],
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
        current_policies_checksum = hashlib.sha3_256(str(policies).encode('utf-8')).hexdigest()
        filter_expression_checksum = hashlib.sha3_256(str(filter_expression).encode('utf-8')).hexdigest()
        ## If the countrer party id is already available and also the dct type is in the counter_party_id and the transfer key is also present
        transfer_process_id: str = self.connection_manager.get_connection_transfer_id(counter_party_id=counter_party_id,
                                                                                      counter_party_address=counter_party_address,
                                                                                      query_checksum=filter_expression_checksum,
                                                                                      policy_checksum=current_policies_checksum)
        ## If is there return the cached one, if the selection is the same the transfer id can be reused!
        if (transfer_process_id is not None):
            if self.logger:
                self.logger.info(
                    "[EDC Service] [%s]: EDR transfer_id=[%s] found in the cache for counter_party_id=[%s], filter=[%s] and selected policies",
                    counter_party_address, transfer_process_id, counter_party_id, filter_expression)
            return transfer_process_id

        if self.logger:
            self.logger.info(
                "[EDC Service] The EDR was not found in the cache for counter_party_address=[%s], counter_party_id=[%s], filter=[%s] and selected policies, starting new contract negotiation!",
                counter_party_address, counter_party_id, filter_expression)

        ## If not the contract negotiation MUST be done!
        edr_entry: dict = self.negotiate_and_transfer(counter_party_id=counter_party_id,
                                                      counter_party_address=counter_party_address, policies=policies,
                                                      filter_expression=filter_expression)

        ## Check if the edr entry is not none
        if (edr_entry is None):
            raise RuntimeError("[EDC Service] Failed to get edr entry! Response was none!")

        if self.logger:
            self.logger.info(f"[EDC Service] The EDR Entry was found! Transfer Process ID: [{transfer_process_id}]")

        ## Check if the transfer id is available and return the transfer process id
        return self.connection_manager.add_connection(counter_party_id=counter_party_id,
                                                      counter_party_address=counter_party_address,
                                                      query_checksum=filter_expression_checksum,
                                                      policy_checksum=current_policies_checksum,
                                                      connection_entry=edr_entry)

    def do_dsp_by_dct_type(
        self,
        counter_party_id: str,
        counter_party_address: str,
        dct_type: str,
        policies: list = None,
        dct_type_key=f"'http://purl.org/dc/terms/type'.'{JSONLDKeys.AT_ID}'",
        operator="="
    ) -> tuple[str, str]:
        return self.do_dsp(
            counter_party_id=counter_party_id,
            counter_party_address=counter_party_address,
            filter_expression=[
                self.get_filter_expression(key=dct_type_key, value=dct_type, operator=operator)
            ],
            policies=policies
        )

    def do_dsp_by_asset_id(
        self,
        counter_party_id: str,
        counter_party_address: str,
        asset_id: str,
        policies: list = None,
        asset_id_key="https://w3id.org/edc/v0.0.1/ns/id",
        operator="="
    ) -> tuple[str, str]:
        return self.do_dsp(
            counter_party_id=counter_party_id,
            counter_party_address=counter_party_address,
            filter_expression=[
                self.get_filter_expression(key=asset_id_key, value=asset_id, operator=operator)
            ],
            policies=policies,
        )

    def do_get_by_dct_type(
        self,
        counter_party_id: str,
        counter_party_address: str,
        dct_type: str,
        policies: list = None,
        dct_type_key=f"'http://purl.org/dc/terms/type'.'{JSONLDKeys.AT_ID}'",
        operator="=",
        session=None,
        **kwargs,
    ):
        return self.do_get(
            counter_party_id=counter_party_id,
            counter_party_address=counter_party_address,
            filter_expression=[
                self.get_filter_expression(key=dct_type_key, value=dct_type, operator=operator)
            ],
            policies=policies,
            session=session,
            **kwargs,
        )

    def do_get_by_asset_id(
        self,
        counter_party_id: str,
        counter_party_address: str,
        asset_id: str,
        policies: list = None,
        asset_id_key="https://w3id.org/edc/v0.0.1/ns/id",
        operator="=",
        session=None,
        **kwargs,
    ):
        return self.do_get(
            counter_party_id=counter_party_id,
            counter_party_address=counter_party_address,
            filter_expression=[
                self.get_filter_expression(key=asset_id_key, value=asset_id, operator=operator)
            ],
            policies=policies,
            session=session,
            **kwargs,
        )

    def do_post_by_dct_type(
        self,
        counter_party_id: str,
        counter_party_address: str,
        body,
        dct_type: str,
        policies: list = None,
        dct_type_key=f"'http://purl.org/dc/terms/type'.'{JSONLDKeys.AT_ID}'",
        operator="=",
        session=None,
        **kwargs,
    ) -> tuple[str, str]:
        return self.do_post(
            counter_party_id=counter_party_id,
            counter_party_address=counter_party_address,
            body=body,
            filter_expression=[
                self.get_filter_expression(key=dct_type_key, value=dct_type, operator=operator)
            ],
            policies=policies,
            session=session,
            **kwargs,
        )

    def do_post_by_asset_id(
        self,
        counter_party_id: str,
        counter_party_address: str,
        body,
        asset_id: str,
        policies: list = None,
        asset_id_key="https://w3id.org/edc/v0.0.1/ns/id",
        operator="=",
        session=None,
        **kwargs
    ) -> tuple[str, str]:
        return self.do_post(
            counter_party_id=counter_party_id,
            counter_party_address=counter_party_address,
            body=body,
            filter_expression=[
                self.get_filter_expression(key=asset_id_key, value=asset_id, operator=operator)
            ],
            policies=policies,
            session=session,
            **kwargs,
        )

    def do_dsp(
        self,
        counter_party_id: str,
        counter_party_address: str,
        filter_expression: list[dict],
        policies: list
    ) -> tuple[str, str]:
        """
        Does all the dsp necessary operations until getting the edr.
        Giving you all the necessary data to request data to the edc dataplane.

        @param counter_party_id: The identifier of the counterparty (Business Partner Number [BPN]).
        @param counter_party_address: The URL of the EDC provider.
        @param policies: The policies to be used for the transfer.
        @param dct_type: The DCT type to be used for the transfer. Defaults to "IndustryFlagService".
        @returns: tuple[dataplane_endpoint:str, edr_access_token:str] or if fail Exception
        """

        ## Get the transfer id 
        transfer_id = self.get_transfer_id(
            counter_party_id=counter_party_id,
            counter_party_address=counter_party_address,
            policies=policies,
            filter_expression=filter_expression,
        )
        ## Get the endpoint and the token
        return self.get_endpoint_with_token(transfer_id=transfer_id)

    def assets_exists(self, counter_party_id: str, counter_party_address: str, filter_expression: list[dict],
                      timeout=10) -> bool:

        try:
            catalog = self.get_catalog_with_filter(counter_party_id=counter_party_id,
                                                   counter_party_address=counter_party_address,
                                                   filter_expression=filter_expression, timeout=timeout)
        except Exception as e:
            raise ConnectionError(
                f"[EDC Service] Failed to get catalog for counter_party_id=[{counter_party_id}], counter_party_address=[{counter_party_address}], filter_expression=[{filter_expression}]")

        if catalog is None:
            return False

        return not DspTools.is_catalog_empty(catalog=catalog)

    def do_get(
        self,
        counter_party_id: str,
        counter_party_address: str,
        filter_expression: list[dict],
        path: str = "/",
        policies: list = None,
        verify: bool = False,
        headers: dict = {},
        timeout: int = None,
        params: dict = None,
        allow_redirects: bool = False,
        session=None,
    ) -> Response:
        """
        Executes a HTTP GET request to a asset behind an EDC!
        Abstracts everything for you doing the dsp exchange.

        Parameters:
        counter_party_id (str): The identifier of the counterparty (Business Partner Number [BPN]).
        counter_party_address (str): The URL of the EDC provider.
        path (str, optional): The path to be appended to the dataplane URL. Defaults to "/".
        policies (list, optional): The policies to be used for the transfer. Defaults to None.
        dct_type (str, optional): The DCT type to be used for the transfer. Defaults to "IndustryFlagService".

        Returns:
        Response: The HTTP response from the GET request. If the request fails, an Exception is raised.
        """
        ## If policies are empty use default policies

        dataplane_url, access_token = self.do_dsp(
            counter_party_id=counter_party_id,
            counter_party_address=counter_party_address,
            policies=policies,
            filter_expression=filter_expression
        )

        if dataplane_url is None or access_token is None:
            raise RuntimeError("[EDC Service] No dataplane URL or access_token was able to be retrieved!")

        ## Build edr transfer url
        url: str = dataplane_url + path

        dataplane_headers: dict = self.get_data_plane_headers(access_token=access_token)
        merged_headers: dict = (headers | dataplane_headers)
        
        if(session):
            return HttpTools.do_get_with_session(
                url=url,
                headers=merged_headers,
                verify=verify,
                timeout=timeout,
                allow_redirects=allow_redirects,
                session=session,
            )
            
        ## Do get request to get a response!
        return HttpTools.do_get(
            url=url,
            headers=merged_headers,
            verify=verify,
            timeout=timeout,
            params=params,
            allow_redirects=allow_redirects
        )

    def do_post(
        self,
        counter_party_id: str,
        counter_party_address: str,
        body,
        filter_expression: list[dict],
        path: str = "/",
        content_type: str = "application/json",
        policies: list = None,
        verify: bool = False,
        headers: dict = None,
        timeout: int = None,
        allow_redirects: bool = False,
        session=None,
    ) -> Response:
        """
        Performs a HTTP POST request to a specific asset behind an EDC.

        This function abstracts the entire process of exchanging data with the EDC. It first negotiates the EDR (Endpoint Data Reference)
        using the provided counterparty ID, EDC provider URL, policies, and DCT type. Then, it constructs the dataplane URL and access token
        using the negotiated EDR. Finally, it sends a POST request to the dataplane URL with the provided body, headers, and content type.

        Parameters:
        counter_party_id (str): The identifier of the counterparty (Business Partner Number [BPN]).
        counter_party_address (str): The URL of the EDC provider.
        body (dict): The data to be sent in the POST request.
        path (str, optional): The path to be appended to the dataplane URL. Defaults to "/".
        content_type (str, optional): The content type of the POST request. Defaults to "application/json".
        policies (list, optional): The policies to be used for the transfer. Defaults to None.
        dct_type (str, optional): The DCT type to be used for the transfer. Defaults to "IndustryFlagService".

        Returns:
        Response: The HTTP response from the POST request. If the request fails, an Exception is raised.
        """
        ## If policies are empty use default policies

        dataplane_url, access_token = self.do_dsp(
            counter_party_id=counter_party_id,
            counter_party_address=counter_party_address,
            policies=policies,
            filter_expression=filter_expression
        )

        if dataplane_url is None or access_token is None:
            raise RuntimeError("[EDC Service] No dataplane URL or access_token was able to be retrieved!")

        ## Build edr transfer url
        url: str = dataplane_url + path

        dataplane_headers: dict = self.get_data_plane_headers(access_token=access_token, content_type=content_type)
        merged_headers: dict = (headers | dataplane_headers)
        ## Do get request to get a response!
        
        if(session):
            return HttpTools.do_post_with_session(
                url=url,
                json=body,
                headers=merged_headers,
                verify=verify,
                timeout=timeout,
                allow_redirects=allow_redirects,
                session=session,
            )

        return HttpTools.do_post(
            url=url,
            json=body,
            headers=merged_headers,
            verify=verify,
            timeout=timeout,
            allow_redirects=allow_redirects
        )
