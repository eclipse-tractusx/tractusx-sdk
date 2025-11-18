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

from ....models.connector.saturn import ContractNegotiationModel
from ....tools import op, HttpTools, DspTools
from ..base_connector_consumer import BaseConnectorConsumerService
from ....managers.connection.base_connection_manager import BaseConnectionManager
import logging
from ....models.connector.model_factory import ModelFactory, DataspaceVersionMapping
from ....adapters.connector.adapter_factory import AdapterFactory
from ....controllers.connector.base_dma_controller import BaseDmaController
from ....controllers.connector.controller_factory import ControllerType, ControllerFactory
from ....models.connector.saturn.catalog_model import CatalogModel
import hashlib
from requests import Response
class ConnectorConsumerService(BaseConnectorConsumerService):
    
    EDC_NAMESPACE= "https://w3id.org/edc/v0.0.1/ns/"
    DSP_2025="dataspace-protocol-http:2025-1"
    DEFAULT_NEGOTIATION_CONTEXT:list=["https://w3id.org/tractusx/policy/v1.0.0","http://www.w3.org/ns/odrl.jsonld",{"@vocab": EDC_NAMESPACE, "edc": EDC_NAMESPACE}]
    DEFAULT_CONTEXT:dict = {"edc": EDC_NAMESPACE,"odrl": "http://www.w3.org/ns/odrl/2/","dct": "https://purl.org/dc/terms/"}
    _connector_discovery_controller: BaseDmaController
    DEFAULT_DCT_TYPE_KEY: str = "'http://purl.org/dc/terms/type'.'@id'"
    def __init__(self, dataspace_version: str, base_url: str, dma_path: str, headers: dict = None,
                 connection_manager: BaseConnectionManager = None, verbose: bool = True, logger: logging.Logger = None):
        # Set attributes before accessing them
        self.verbose = verbose
        self.logger = logger
        
        # Validate dataspace_version is saturn
        if dataspace_version != "saturn":
            raise ValueError(f"Saturn ConnectorConsumerService only supports dataspace_version='saturn', got '{dataspace_version}'")
        
        self.dataspace_version = dataspace_version
        # Backwards compatibility: if verbose is True and no logger provided, use default logger
        if self.verbose and self.logger is None:
            self.logger = logging.getLogger(__name__)

        self.dma_adapter = AdapterFactory.get_dma_adapter(
            dataspace_version=self.dataspace_version,
            base_url=base_url,
            dma_path=dma_path,
            headers=headers
        )

        self.controllers = ControllerFactory.get_dma_controllers_for_version(
            dataspace_version=self.dataspace_version,
            adapter=self.dma_adapter,
            controller_types=[
                ControllerType.CATALOG,
                ControllerType.EDR,
                ControllerType.CONTRACT_NEGOTIATION,
                ControllerType.TRANSFER_PROCESS,
                ControllerType.CONNECTOR_DISCOVERY
            ]
        )
        self._connector_discovery_controller = self.controllers.get(ControllerType.CONNECTOR_DISCOVERY)
        super().__init__(
            dataspace_version=self.dataspace_version,
            base_url=base_url,
            dma_path=dma_path,
            headers=headers,
            connection_manager=connection_manager,
            verbose=verbose,
            logger=logger
        )
        
    @property
    def connector_discovery(self):
        return self._connector_discovery_controller
    
    def _resolve_counter_party_info(self, counter_party_id: str = None, counter_party_address: str = None, 
                                   bpnl: str = None, protocol: str = DSP_2025, namespace: str = EDC_NAMESPACE) -> tuple[str, str, str]:
        """
        Internal helper to resolve counter party information from either direct parameters or BPNL discovery.
        
        Returns:
        tuple[str, str, str]: counter_party_address, counter_party_id, protocol
        """
        if bpnl is not None:
            return self.get_discovery_info(bpnl=bpnl, counter_party_address=counter_party_address, namespace=namespace)
        else:
            # Use provided values and protocol
            return counter_party_address, counter_party_id, protocol
    
    def _execute_http_request(self, method: str, dataplane_url: str, access_token: str, path: str = "/",
                            content_type: str = "application/json", json=None, data=None, 
                            verify: bool = False, headers: dict = None, timeout: int = None,
                            params: dict = None, allow_redirects: bool = False, session=None) -> Response:
        """
        Internal helper to execute HTTP requests with common logic.
        
        Supports only GET, POST, and PUT methods with optional session support.
        """
        # Validate that only allowed HTTP methods are used
        allowed_methods = {'GET', 'POST', 'PUT'}
        if method.upper() not in allowed_methods:
            raise ValueError(f"HTTP method '{method}' is not supported. Only {', '.join(allowed_methods)} are allowed.")
        
        if headers is None:
            headers = {}
        
        url = dataplane_url + path
        dataplane_headers = self.get_data_plane_headers(access_token=access_token, content_type=content_type if method == 'POST' else None)
        merged_headers = headers | dataplane_headers

        if session:
            if method == 'GET':
                return HttpTools.do_get_with_session(
                    url=url, headers=merged_headers, verify=verify, timeout=timeout,
                    allow_redirects=allow_redirects, session=session
                )
            elif method == 'POST':
                return HttpTools.do_post_with_session(
                    url=url, json=json, data=data, headers=merged_headers, verify=verify,
                    timeout=timeout, allow_redirects=allow_redirects, session=session
                )
            elif method == 'PUT':
                return HttpTools.do_put_with_session(
                    url=url, json=json, data=data, headers=merged_headers, verify=verify,
                    timeout=timeout, allow_redirects=allow_redirects, session=session
                )

        if method == 'GET':
            return HttpTools.do_get(
                url=url, headers=merged_headers, verify=verify, timeout=timeout,
                params=params, allow_redirects=allow_redirects
            )
        elif method == 'POST':
            return HttpTools.do_post(
                url=url, json=json, data=data, headers=merged_headers, verify=verify,
                timeout=timeout, allow_redirects=allow_redirects
            )
        elif method == 'PUT':
            return HttpTools.do_put(
                url=url, json=json, data=data, headers=merged_headers, verify=verify,
                timeout=timeout, allow_redirects=allow_redirects
            )

    def _get_catalog_internal(self, counter_party_id: str = None, counter_party_address: str = None,
                            bpnl: str = None, filter_expression: list[dict] = None, timeout: int = None,
                            protocol: str = DSP_2025, context: dict = DEFAULT_CONTEXT, 
                            namespace: str = EDC_NAMESPACE) -> dict:
        """
        Internal method to get catalog with optional BPNL resolution and filtering.
        """
        resolved_address, resolved_id, resolved_protocol = self._resolve_counter_party_info(
            counter_party_id=counter_party_id, counter_party_address=counter_party_address,
            bpnl=bpnl, protocol=protocol, namespace=namespace
        )
        
        if filter_expression:
            catalog_request = self.get_catalog_request_with_filter(
                counter_party_id=resolved_id, counter_party_address=resolved_address,
                filter_expression=filter_expression, protocol=resolved_protocol, context=context
            )
        else:
            catalog_request = self.get_catalog_request(
                counter_party_id=resolved_id, counter_party_address=resolved_address,
                protocol=resolved_protocol, context=context
            )
        
        return self.get_catalog(request=catalog_request, timeout=timeout)
    
    def get_edr_negotiation_request(self, counter_party_id: str, counter_party_address: str, target: str,
                                    policy: dict, protocol: str = DSP_2025, context: dict = DEFAULT_NEGOTIATION_CONTEXT) -> ContractNegotiationModel:
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
        offer_id = policy.get("@id", None)
        if (offer_id is None):
            raise ValueError("Connector Service Policy offer id is not available!")

        return ModelFactory.get_contract_negotiation_model(
            dataspace_version=DataspaceVersionMapping.from_protocol(protocol).value,  # version is to be included in the BaseService class
            context=context,
            counter_party_address=counter_party_address,
            offer_id=offer_id,
            asset_id=target,
            provider_id=counter_party_id,
            offer_policy=policy,
            protocol=protocol
        )
    
    def start_edr_negotiation(self, counter_party_id: str, counter_party_address: str, target: str,
                              policy: dict, protocol: str = DSP_2025, context: dict = DEFAULT_NEGOTIATION_CONTEXT) -> str | None:
        """
        Starts the edr negotiation and gives the negotation id

        @param counter_party_id: The identifier of the counterparty (Business Partner Number [BPN]).
        @param counter_party_address: The URL of the EDC provider.
        @param target: The target asset for the negotiation.
        @param policy: The policy to be used for the negotiation.
        @returns: negotiation_id:str or if Fail -> None
        """

        ## Prepare the request
        request: ContractNegotiationModel = self.get_edr_negotiation_request(counter_party_id=counter_party_id,
                                                                                 counter_party_address=counter_party_address,
                                                                                 target=target,
                                                                                 policy=policy,
                                                                                 protocol=protocol,
                                                                                 context=context)

        ## Build catalog api url
        response: Response = self.edrs.create(request)
        ## In case the response code is not successfull or the response is null
        if (response is None or response.status_code != 200):
            return None

        content: dict = response.json()
        ## Check if the id was returned in the response
        if ("@id" not in content):
            return None

        return content.get("@id", None)
    
    def negotiate_and_transfer(self, counter_party_id: str, counter_party_address: str, filter_expression: list[dict],
                               policies: list = None, max_retries: int = 6, timeout: int = 10, protocol: str = DSP_2025, catalog_context: dict = DEFAULT_CONTEXT, negotiation_context: dict = DEFAULT_NEGOTIATION_CONTEXT) -> dict:
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
                                                        protocol=protocol,
                                                        context=catalog_context,
                                                        filter_expression=filter_expression)
        if (catalog_response is None):
            raise RuntimeError(
                f"Connector Service [{counter_party_address}] It was not possible to retrieve the catalog from the edc provider! Catalog response is empty!")

        ## Select Policy and Assetid
        try:
            valid_assets_policies = DspTools.filter_assets_and_policies(catalog=catalog_response,
                                                                        allowed_policies=policies)
        except Exception as e:
            raise RuntimeError(
                f"Connector Service [{counter_party_address}] It was not possible to find a valid policy in the catalog! Reason: [{str(e)}]")

        if (len(valid_assets_policies) == 0):
            raise RuntimeError(
                f"Connector Service [{counter_party_address}] It was not possible to find a valid policy in the catalog! Asset ID and the Policy are empty!")

        negotiation_id: str | None = None

        for valid_asset_policy in valid_assets_policies:
            ## Unwrap asset id and policy tuple
            asset_id = valid_asset_policy[0]
            policy = valid_asset_policy[1]

            ##### 2. EDR Negotiation Start

            negotiation_id = self.start_edr_negotiation(counter_party_id=counter_party_id,
                                                        counter_party_address=counter_party_address, target=asset_id,
                                                        policy=policy, protocol=protocol, context=negotiation_context)
            if (negotiation_id is not None):
                break

        if (negotiation_id is None):
            raise RuntimeError(
                f"Connector Service [{counter_party_address}] It was not possible to start the EDR Negotiation! The negotiation id is empty!")

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
                    f"Connector Service Attempt [{retries + 1}]/[{max_retries}]: [{counter_party_address}] The EDR Negotiation [{negotiation_id}] entry was not found! Waiting {timeout} seconds and retrying...")
            op.wait(seconds=timeout)
            retries += 1

        if edr_entry is None:
            raise TimeoutError(
                f"Connector Service [{counter_party_address}] The EDR Negotiation [{negotiation_id}] has failed! The EDR entry was not found!")

        return edr_entry

    def get_transfer_id(self, counter_party_id: str, counter_party_address: str, filter_expression: list[dict],
                        policies: list = None, protocol: str = DSP_2025, catalog_context: dict = DEFAULT_CONTEXT, negotiation_context: dict = DEFAULT_NEGOTIATION_CONTEXT) -> str:

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
                self.logger.debug(
                    "Connector Service [%s]: EDR transfer_id=[%s] found in the cache for counter_party_id=[%s], filter=[%s] and selected policies",
                    counter_party_address, transfer_process_id, counter_party_id, filter_expression)
            return transfer_process_id

        if self.logger:
            self.logger.info(
                "Connector Service The EDR was not found in the cache for counter_party_address=[%s], counter_party_id=[%s], filter=[%s] and selected policies, starting new contract negotiation!",
                counter_party_address, counter_party_id, filter_expression)

        ## If not the contract negotiation MUST be done!
        edr_entry: dict = self.negotiate_and_transfer(counter_party_id=counter_party_id,
                                                      counter_party_address=counter_party_address, policies=policies,
                                                      filter_expression=filter_expression,
                                                      protocol=protocol,
                                                      catalog_context=catalog_context,
                                                      negotiation_context=negotiation_context)

        ## Check if the edr entry is not none
        if (edr_entry is None):
            raise RuntimeError("Connector Service Failed to get edr entry! Response was none!")

        if self.logger:
            self.logger.info(f"Connector Service The EDR Entry was found! Transfer Process ID: [{transfer_process_id}]")

        ## Check if the transfer id is available and return the transfer process id
        return self.connection_manager.add_connection(counter_party_id=counter_party_id,
                                                      counter_party_address=counter_party_address,
                                                      query_checksum=filter_expression_checksum,
                                                      policy_checksum=current_policies_checksum,
                                                      connection_entry=edr_entry)
        
    def discover_connector_protocol(self, bpnl: str, counter_party_address: str = None) -> dict | None:

        response: Response = self.connector_discovery.get_discover(
            ModelFactory.get_connector_discovery_model(dataspace_version=self.dataspace_version,
                                                       bpnl=bpnl,
                                                       counter_party_address=counter_party_address)
        )
        if response is None or response.status_code != 200:
            raise ConnectionError(
                f"Connector Service It was not possible to get the catalog from the EDC provider! Response code: [{response.status_code}]")
        return response.json()


    def get_discovery_info(self, bpnl: str, counter_party_address: str = None, namespace: str = EDC_NAMESPACE) -> tuple[str, str, str]:
        """
        Retrieves the discovery information for the specified connector protocol.
        
        Parameters:
        bpnl (str): The Business Partner Number (BPN) of the counterparty.
        counter_party_address (str, optional): The URL of the EDC provider. If not
            provided, it will be discovered using the BPNL.
        namespace (str): The namespace for the returned keys. Default is "https://w3id.org/edc/v0.0.1/ns/".
        
        Returns:
        tuple[str, str, str]: A tuple containing the counter party address, counter party ID, and protocol.
        """
        discovery_info = self.discover_connector_protocol(bpnl=bpnl, counter_party_address=counter_party_address)
        counter_party_address = discovery_info[f"{namespace}counterPartyAddress"]
        counter_party_id = discovery_info[f"{namespace}counterPartyId"]
        protocol = discovery_info[f"{namespace}protocol"]
        return counter_party_address, counter_party_id, protocol

    def get_catalog_with_bpnl(self, bpnl: str, counter_party_address: str = None, namespace: str = EDC_NAMESPACE, context=DEFAULT_CONTEXT) -> dict | None:
        """
        Retrieves the Connector DCAT catalog using the BPNL to discover the connector protocol and address.

        Parameters:
        bpnl (str): The Business Partner Number (BPN) of the counterparty.
        counter_party_address (str, optional): The URL of the EDC provider. If not provided, it will be discovered using the BPNL.
        namespace (str): The namespace for the returned keys. Default is "https://w3id.org/edc/v0.0.1/ns/".
        context (dict, optional): The JSON-LD context to use in the catalog request.
        
        Returns:
        dict | None: The EDC catalog as a dictionary, or None if the request fails.
        """
        return self._get_catalog_internal(bpnl=bpnl, counter_party_address=counter_party_address, 
                                        context=context, namespace=namespace)

    def get_catalog_request(self, counter_party_id: str, counter_party_address: str, protocol: str = DSP_2025, context=DEFAULT_CONTEXT) -> CatalogModel:
        ## Here it will autoselect the dataspace version based on the protocol
        return ModelFactory.get_catalog_model(
            dataspace_version=DataspaceVersionMapping.from_protocol(protocol).value,
            context=context,
            counter_party_id=counter_party_id,  ## bpn of the provider
            counter_party_address=counter_party_address,  ## dsp url from the provider,
            protocol=protocol
        )
        
    ## Get catalog request with filter
    def get_catalog_with_filter(self, counter_party_id: str, counter_party_address: str, filter_expression: list[dict],
                                timeout: int = None, protocol: str = DSP_2025, context=DEFAULT_CONTEXT) -> dict:
        """
        Retrieves a catalog from the EDC provider based on a specified filter.

        Parameters:
        counter_party_id (str): The identifier of the counterparty (Business Partner Number [BPN]).
        counter_party_address (str): The URL of the EDC provider.
        filter_expression (list[dict]): A list of filter conditions, each represented as a dictionary.

        Returns:
        dict | None: The EDC catalog as a dictionary, or None if the request fails.
        """
        return self._get_catalog_internal(counter_party_id=counter_party_id, counter_party_address=counter_party_address,
                                        filter_expression=filter_expression, timeout=timeout, protocol=protocol, context=context)
        
    def get_catalog_request_with_filter(self, counter_party_id: str, counter_party_address: str,
                                        filter_expression: list[dict], protocol: str = DSP_2025, context=DEFAULT_CONTEXT) -> CatalogModel:
        """
        Prepares a catalog request with a filter for a specific key-value pair.

        Parameters:
        counter_party_id (str): The identifier of the counterparty (Business Partner Number [BPN]).
        counter_party_address (str): The URL of the EDC provider.
        filter_expression (list[dict]): A list of filter conditions, each represented as a dictionary.

        Returns:
        dict: A catalog request with the filter condition included.
        """
        catalog_request: CatalogModel = self.get_catalog_request(counter_party_id=counter_party_id,
                                    counter_party_address=counter_party_address, protocol=protocol, context=context)
        catalog_request.queryspec = self.get_query_spec(filter_expression=filter_expression)

        return catalog_request
    

    def get_catalogs_by_dct_type(self, counter_party_id: str, edcs: list, dct_type: str,
                                 dct_type_key: str = DEFAULT_DCT_TYPE_KEY, timeout: int = None,
                                 protocol: str = DSP_2025, context=DEFAULT_CONTEXT):
        filter_expr = [self.get_filter_expression(key=dct_type_key, value=dct_type, operator="=")]
        return self.get_catalogs_with_filter(counter_party_id=counter_party_id, edcs=edcs, filter_expression=filter_expr, timeout=timeout, protocol=protocol, context=context)

    def get_catalogs_by_dct_type_with_bpnl(self, bpnl: str, edcs: list, dct_type: str,
                                           dct_type_key: str = DEFAULT_DCT_TYPE_KEY, timeout: int = None,
                                           namespace: str = EDC_NAMESPACE, context=DEFAULT_CONTEXT):
        filter_expr = [self.get_filter_expression(key=dct_type_key, value=dct_type, operator="=")]
        return self.get_catalogs_with_filter_with_bpnl(bpnl=bpnl, edcs=edcs, filter_expression=filter_expr, 
                                                      timeout=timeout, namespace=namespace, context=context)

    def get_catalogs_with_filter(self, counter_party_id: str, edcs: list, filter_expression: list[dict],
                                 timeout: int = None, protocol: str = DSP_2025, context=DEFAULT_CONTEXT):
        import threading
        catalogs: dict = {}
        threads: list[threading.Thread] = []

        def fetch_catalog(counter_party_id, counter_party_address, filter_expression, timeout, catalogs, protocol, context):
            catalog_request = self.get_catalog_request_with_filter(
                counter_party_id=counter_party_id,
                counter_party_address=counter_party_address,
                filter_expression=filter_expression,
                protocol=protocol,
                context=context
            )
            catalogs[counter_party_address] = self.get_catalog(request=catalog_request, timeout=timeout)

        for edc_url in edcs:
            thread = threading.Thread(target=fetch_catalog, kwargs={
                'counter_party_id': counter_party_id,
                'counter_party_address': edc_url,
                'filter_expression': filter_expression,
                'timeout': timeout,
                'catalogs': catalogs,
                'protocol': protocol,
                'context': context
            })
            thread.start()
            threads.append(thread)

        for thread in threads:
            thread.join()

        return catalogs

    def get_catalogs_with_filter_with_bpnl(self, bpnl: str, edcs: list, filter_expression: list[dict],
                                           timeout: int = None, namespace: str = EDC_NAMESPACE, context=DEFAULT_CONTEXT):
        catalogs = {}
        for edc_url in edcs:
            catalogs[edc_url] = self._get_catalog_internal(bpnl=bpnl, counter_party_address=edc_url,
                                                         filter_expression=filter_expression, timeout=timeout,
                                                         context=context, namespace=namespace)
        return catalogs

    def get_catalog_by_dct_type(self, counter_party_id: str, counter_party_address: str, dct_type: str,
                                dct_type_key=DEFAULT_DCT_TYPE_KEY, operator="=", timeout=None,
                                protocol: str = DSP_2025, context=DEFAULT_CONTEXT):
        filter_expr = [self.get_filter_expression(key=dct_type_key, value=dct_type, operator=operator)]
        catalog_request = self.get_catalog_request_with_filter(
            counter_party_id=counter_party_id,
            counter_party_address=counter_party_address,
            filter_expression=filter_expr,
            protocol=protocol,
            context=context
        )
        return self.get_catalog(request=catalog_request, timeout=timeout)

    def get_catalog_by_dct_type_with_bpnl(self, bpnl: str, counter_party_address: str, dct_type: str,
                                          dct_type_key=DEFAULT_DCT_TYPE_KEY, operator="=", timeout=None,
                                          namespace: str = EDC_NAMESPACE, context=DEFAULT_CONTEXT):
        filter_expr = [self.get_filter_expression(key=dct_type_key, value=dct_type, operator=operator)]
        return self._get_catalog_internal(bpnl=bpnl, counter_party_address=counter_party_address,
                                        filter_expression=filter_expr, timeout=timeout, 
                                        context=context, namespace=namespace)

    def get_catalog_with_filter_parallel(self, counter_party_id: str, counter_party_address: str,
                                         filter_expression: list[dict], catalogs: dict = None,
                                         timeout: int = None, protocol: str = DSP_2025, context=DEFAULT_CONTEXT) -> None:
        catalog_request = self.get_catalog_request_with_filter(
            counter_party_id=counter_party_id,
            counter_party_address=counter_party_address,
            filter_expression=filter_expression,
            protocol=protocol,
            context=context
        )
        catalogs[counter_party_address] = self.get_catalog(request=catalog_request, timeout=timeout)

    def get_catalog_with_filter_parallel_with_bpnl(self, bpnl: str, counter_party_address: str,
                                                  filter_expression: list[dict], catalogs: dict = None,
                                                  timeout: int = None, namespace: str = EDC_NAMESPACE, context=DEFAULT_CONTEXT) -> None:
        if catalogs is None:
            catalogs = {}
        catalogs[counter_party_address] = self._get_catalog_internal(bpnl=bpnl, counter_party_address=counter_party_address,
                                                                   filter_expression=filter_expression, timeout=timeout,
                                                                   context=context, namespace=namespace)
    
    def get_catalogs_by_dct_type_with_bpnl_parallel(self, bpnl: str, edcs: list, dct_type: str,
                                                    dct_type_key: str = DEFAULT_DCT_TYPE_KEY, timeout: int = None,
                                                    namespace: str = EDC_NAMESPACE, context=DEFAULT_CONTEXT):
        filter_expr = [self.get_filter_expression(key=dct_type_key, value=dct_type, operator="=")]
        return self.get_catalogs_with_filter_with_bpnl_parallel(bpnl=bpnl, edcs=edcs, filter_expression=filter_expr,
                                                               timeout=timeout, namespace=namespace, context=context)

    def get_catalogs_with_filter_with_bpnl_parallel(self, bpnl: str, edcs: list, filter_expression: list[dict],
                                                   timeout: int = None, namespace: str = EDC_NAMESPACE, context=DEFAULT_CONTEXT):
        import threading
        catalogs = {}
        threads = []

        def fetch_catalog(edc_url):
            catalogs[edc_url] = self._get_catalog_internal(bpnl=bpnl, counter_party_address=edc_url,
                                                         filter_expression=filter_expression, timeout=timeout,
                                                         context=context, namespace=namespace)

        for edc_url in edcs:
            thread = threading.Thread(target=fetch_catalog, args=(edc_url,))
            thread.start()
            threads.append(thread)

        for thread in threads:
            thread.join()

        return catalogs
    
    def do_dsp_with_bpnl(self, bpnl: str, counter_party_address: str = None, filter_expression: list[dict] = None,
                        policies: list = None,
                        namespace: str = EDC_NAMESPACE,
                        catalog_context: dict = DEFAULT_CONTEXT,
                        negotiation_context: dict = DEFAULT_NEGOTIATION_CONTEXT) -> tuple[str, str]:
        """
        Does all the dsp necessary operations until getting the edr.
        Giving you all the necessary data to request data to the edc dataplane.

        @param bpnl: The Business Partner Number (BPN) of the counterparty.
        @param counter_party_address: The URL of the EDC provider. If not provided, it will be discovered using the BPNL.
        @param policies: The policies to be used for the transfer.
        @param dct_type: The DCT type to be used for the transfer. Defaults to "IndustryFlagService".
        @returns: tuple[dataplane_endpoint:str, edr_access_token:str] or if fail Exception
        """
        counter_party_address, counter_party_id, protocol = self.get_discovery_info(bpnl=bpnl, counter_party_address=counter_party_address, namespace=namespace)
        return self.do_dsp(
            counter_party_id=counter_party_id,
            counter_party_address=counter_party_address,
            filter_expression=filter_expression,
            policies=policies,
            protocol=protocol,
            catalog_context=catalog_context,
            negotiation_context=negotiation_context
        )
    
    
    def do_dsp(
        self,
        counter_party_id: str,
        counter_party_address: str,
        filter_expression: list[dict],
        policies: list,
        protocol: str = DSP_2025,
        catalog_context: dict = DEFAULT_CONTEXT,
        negotiation_context: dict = DEFAULT_NEGOTIATION_CONTEXT
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
            protocol=protocol,
            catalog_context=catalog_context,
            negotiation_context=negotiation_context
        )
        ## Get the endpoint and the token
        return self.get_endpoint_with_token(transfer_id=transfer_id)

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
        protocol: str = DSP_2025,
        catalog_context: dict = DEFAULT_CONTEXT,
        negotiation_context: dict = DEFAULT_NEGOTIATION_CONTEXT
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
        dataplane_url, access_token = self.do_dsp(
            counter_party_id=counter_party_id,
            counter_party_address=counter_party_address,
            policies=policies,
            filter_expression=filter_expression,
            protocol=protocol,
            catalog_context=catalog_context,
            negotiation_context=negotiation_context
        )

        if dataplane_url is None or access_token is None:
            raise RuntimeError("Connector Service No dataplane URL or access_token was able to be retrieved!")

        return self._execute_http_request(
            method='GET', dataplane_url=dataplane_url, access_token=access_token, path=path,
            verify=verify, headers=headers, timeout=timeout, params=params,
            allow_redirects=allow_redirects, session=session
        )
    
    def do_get_with_bpnl(
        self, 
        bpnl: str,
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
        catalog_context: dict = DEFAULT_CONTEXT,
        negotiation_context: dict = DEFAULT_NEGOTIATION_CONTEXT
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
        dataplane_url, access_token = self.do_dsp_with_bpnl(
            bpnl=bpnl,
            counter_party_address=counter_party_address,
            policies=policies,
            filter_expression=filter_expression,
            catalog_context=catalog_context,
            negotiation_context=negotiation_context
        )

        if dataplane_url is None or access_token is None:
            raise RuntimeError("Connector Service No dataplane URL or access_token was able to be retrieved!")

        return self._execute_http_request(
            method='GET', dataplane_url=dataplane_url, access_token=access_token, path=path,
            verify=verify, headers=headers, timeout=timeout, params=params,
            allow_redirects=allow_redirects, session=session
        )
        
    def do_post_with_bpnl(
        self,
        bpnl: str,
        counter_party_address: str,
        filter_expression: list[dict],
        path: str = "/",
        content_type: str = "application/json",
        json=None,
        data=None,
        policies: list = None,
        verify: bool = False,
        headers: dict = None,
        timeout: int = None,
        allow_redirects: bool = False,
        session=None,
        catalog_context: dict = DEFAULT_CONTEXT,
        negotiation_context: dict = DEFAULT_NEGOTIATION_CONTEXT
    ) -> Response:
        """
        Performs a HTTP POST request to a specific asset behind an EDC.

        This function abstracts the entire process of exchanging data with the EDC. It first negotiates the EDR (Endpoint Data Reference)
        using the provided counterparty ID, EDC provider URL, policies, and DCT type. Then, it constructs the dataplane URL and access token
        using the negotiated EDR. Finally, it sends a POST request to the dataplane URL with the provided data, headers, and content type.

        Parameters:
        counter_party_id (str): The identifier of the counterparty (Business Partner Number [BPN]).
        counter_party_address (str): The URL of the EDC provider.
        json (dict, optional): The JSON data to be sent in the POST request.
        data (dict, optional): The data to be sent in the POST request.
        path (str, optional): The path to be appended to the dataplane URL. Defaults to "/".
        content_type (str, optional): The content type of the POST request. Defaults to "application/json".
        policies (list, optional): The policies to be used for the transfer. Defaults to None.
        dct_type (str, optional): The DCT type to be used for the transfer. Defaults to "IndustryFlagService".

        Returns:
        Response: The HTTP response from the POST request. If the request fails, an Exception is raised.
        """
        dataplane_url, access_token = self.do_dsp_with_bpnl(
            bpnl=bpnl,
            counter_party_address=counter_party_address,
            policies=policies,
            filter_expression=filter_expression,
            catalog_context=catalog_context,
            negotiation_context=negotiation_context
        )

        if dataplane_url is None or access_token is None:
            raise RuntimeError("Connector Service No dataplane URL or access_token was able to be retrieved!")

        return self._execute_http_request(
            method='POST', dataplane_url=dataplane_url, access_token=access_token, path=path,
            content_type=content_type, json=json, data=data, verify=verify, headers=headers,
            timeout=timeout, allow_redirects=allow_redirects, session=session
        )
        
    def do_post(
        self,
        counter_party_id: str,
        counter_party_address: str,
        filter_expression: list[dict],
        path: str = "/",
        content_type: str = "application/json",
        json=None,
        data=None,
        policies: list = None,
        verify: bool = False,
        headers: dict = None,
        timeout: int = None,
        allow_redirects: bool = False,
        session=None,
        protocol: str = DSP_2025,
        catalog_context: dict = DEFAULT_CONTEXT,
        negotiation_context: dict = DEFAULT_NEGOTIATION_CONTEXT
    ) -> Response:
        """
        Performs a HTTP POST request to a specific asset behind an EDC.

        This function abstracts the entire process of exchanging data with the EDC. It first negotiates the EDR (Endpoint Data Reference)
        using the provided counterparty ID, EDC provider URL, policies, and DCT type. Then, it constructs the dataplane URL and access token
        using the negotiated EDR. Finally, it sends a POST request to the dataplane URL with the provided data, headers, and content type.

        Parameters:
        counter_party_id (str): The identifier of the counterparty (Business Partner Number [BPN]).
        counter_party_address (str): The URL of the EDC provider.
        json (dict, optional): The JSON data to be sent in the POST request.
        data (dict, optional): The data to be sent in the POST request.
        path (str, optional): The path to be appended to the dataplane URL. Defaults to "/".
        content_type (str, optional): The content type of the POST request. Defaults to "application/json".
        policies (list, optional): The policies to be used for the transfer. Defaults to None.
        dct_type (str, optional): The DCT type to be used for the transfer. Defaults to "IndustryFlagService".

        Returns:
        Response: The HTTP response from the POST request. If the request fails, an Exception is raised.
        """
        dataplane_url, access_token = self.do_dsp(
            counter_party_id=counter_party_id,
            counter_party_address=counter_party_address,
            policies=policies,
            filter_expression=filter_expression,
            protocol=protocol,
            catalog_context=catalog_context,
            negotiation_context=negotiation_context
        )

        if dataplane_url is None or access_token is None:
            raise RuntimeError("Connector Service No dataplane URL or access_token was able to be retrieved!")

        return self._execute_http_request(
            method='POST', dataplane_url=dataplane_url, access_token=access_token, path=path,
            content_type=content_type, json=json, data=data, verify=verify, headers=headers,
            timeout=timeout, allow_redirects=allow_redirects, session=session
        )
    
    def do_put_with_bpnl(
        self,
        bpnl: str,
        counter_party_address: str,
        filter_expression: list[dict],
        path: str = "/",
        content_type: str = "application/json",
        json=None,
        data=None,
        policies: list = None,
        verify: bool = False,
        headers: dict = None,
        timeout: int = None,
        allow_redirects: bool = False,
        session=None,
        catalog_context: dict = DEFAULT_CONTEXT,
        negotiation_context: dict = DEFAULT_NEGOTIATION_CONTEXT
    ) -> Response:
        """
        Performs a HTTP PUT request to a specific asset behind an EDC.

        This function abstracts the entire process of exchanging data with the EDC. It first negotiates the EDR (Endpoint Data Reference)
        using the provided counterparty ID, EDC provider URL, policies, and DCT type. Then, it constructs the dataplane URL and access token
        using the negotiated EDR. Finally, it sends a PUT request to the dataplane URL with the provided data, headers, and content type.

        Parameters:
        bpnl (str): The Business Partner Number (BPN) of the counterparty.
        counter_party_address (str): The URL of the EDC provider.
        filter_expression (list[dict]): A list of filter conditions for the catalog request.
        json (dict, optional): The JSON data to be sent in the PUT request.
        data (dict, optional): The data to be sent in the PUT request.
        path (str, optional): The path to be appended to the dataplane URL. Defaults to "/".
        content_type (str, optional): The content type of the PUT request. Defaults to "application/json".
        policies (list, optional): The policies to be used for the transfer. Defaults to None.
        verify (bool, optional): Whether to verify SSL certificates. Defaults to False.
        headers (dict, optional): Additional headers to include in the request. Defaults to None.
        timeout (int, optional): Request timeout in seconds. Defaults to None.
        allow_redirects (bool, optional): Whether to allow redirects. Defaults to False.
        session (optional): Session object for connection pooling. Defaults to None.
        catalog_context (dict, optional): Context for catalog requests. Defaults to DEFAULT_CONTEXT.
        negotiation_context (dict, optional): Context for negotiation requests. Defaults to DEFAULT_NEGOTIATION_CONTEXT.

        Returns:
        Response: The HTTP response from the PUT request. If the request fails, an Exception is raised.
        """
        dataplane_url, access_token = self.do_dsp_with_bpnl(
            bpnl=bpnl,
            counter_party_address=counter_party_address,
            policies=policies,
            filter_expression=filter_expression,
            catalog_context=catalog_context,
            negotiation_context=negotiation_context
        )

        if dataplane_url is None or access_token is None:
            raise RuntimeError("Connector Service No dataplane URL or access_token was able to be retrieved!")

        return self._execute_http_request(
            method='PUT', dataplane_url=dataplane_url, access_token=access_token, path=path,
            content_type=content_type, json=json, data=data, verify=verify, headers=headers,
            timeout=timeout, allow_redirects=allow_redirects, session=session
        )
        
    def do_put(
        self,
        counter_party_id: str,
        counter_party_address: str,
        filter_expression: list[dict],
        path: str = "/",
        content_type: str = "application/json",
        json=None,
        data=None,
        policies: list = None,
        verify: bool = False,
        headers: dict = None,
        timeout: int = None,
        allow_redirects: bool = False,
        session=None,
        protocol: str = DSP_2025,
        catalog_context: dict = DEFAULT_CONTEXT,
        negotiation_context: dict = DEFAULT_NEGOTIATION_CONTEXT
    ) -> Response:
        """
        Performs a HTTP PUT request to a specific asset behind an EDC.

        This function abstracts the entire process of exchanging data with the EDC. It first negotiates the EDR (Endpoint Data Reference)
        using the provided counterparty ID, EDC provider URL, policies, and DCT type. Then, it constructs the dataplane URL and access token
        using the negotiated EDR. Finally, it sends a PUT request to the dataplane URL with the provided data, headers, and content type.

        Parameters:
        counter_party_id (str): The identifier of the counterparty (Business Partner Number [BPN]).
        counter_party_address (str): The URL of the EDC provider.
        filter_expression (list[dict]): A list of filter conditions for the catalog request.
        json (dict, optional): The JSON data to be sent in the PUT request.
        data (dict, optional): The data to be sent in the PUT request.
        path (str, optional): The path to be appended to the dataplane URL. Defaults to "/".
        content_type (str, optional): The content type of the PUT request. Defaults to "application/json".
        policies (list, optional): The policies to be used for the transfer. Defaults to None.
        verify (bool, optional): Whether to verify SSL certificates. Defaults to False.
        headers (dict, optional): Additional headers to include in the request. Defaults to None.
        timeout (int, optional): Request timeout in seconds. Defaults to None.
        allow_redirects (bool, optional): Whether to allow redirects. Defaults to False.
        session (optional): Session object for connection pooling. Defaults to None.
        protocol (str, optional): The DSP protocol version to use. Defaults to DSP_2025.
        catalog_context (dict, optional): Context for catalog requests. Defaults to DEFAULT_CONTEXT.
        negotiation_context (dict, optional): Context for negotiation requests. Defaults to DEFAULT_NEGOTIATION_CONTEXT.

        Returns:
        Response: The HTTP response from the PUT request. If the request fails, an Exception is raised.
        """
        dataplane_url, access_token = self.do_dsp(
            counter_party_id=counter_party_id,
            counter_party_address=counter_party_address,
            policies=policies,
            filter_expression=filter_expression,
            protocol=protocol,
            catalog_context=catalog_context,
            negotiation_context=negotiation_context
        )

        if dataplane_url is None or access_token is None:
            raise RuntimeError("Connector Service No dataplane URL or access_token was able to be retrieved!")

        return self._execute_http_request(
            method='PUT', dataplane_url=dataplane_url, access_token=access_token, path=path,
            content_type=content_type, json=json, data=data, verify=verify, headers=headers,
            timeout=timeout, allow_redirects=allow_redirects, session=session
        )