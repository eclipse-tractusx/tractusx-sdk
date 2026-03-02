#################################################################################
# Eclipse Tractus-X - Software Development KIT
#
# Copyright (c) 2026 Catena-X Automotive Network e.V.
# Copyright (c) 2025 CGI Deutschland B.V. & Co. KG
# Copyright (c) 2026 Contributors to the Eclipse Foundation
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

EDC_NAMESPACE: str = "https://w3id.org/edc/v0.0.1/ns/"
DSP_0_8: str = "dataspace-protocol-http"
# Jupiter / legacy DSP uses Tractus-X v1.0.0 and W3C ODRL JSON-LD context URLs.
# (Saturn replaces these with Catena-X 2025-9 URLs.)
DEFAULT_NEGOTIATION_CONTEXT: list = [
    "https://w3id.org/tractusx/policy/v1.0.0",
    "http://www.w3.org/ns/odrl.jsonld",
    {"@vocab": EDC_NAMESPACE},
]
DEFAULT_CONTEXT: dict = {
    "edc": EDC_NAMESPACE,
    "odrl": "http://www.w3.org/ns/odrl/2/",
    "dct": "https://purl.org/dc/terms/",
}
DEFAULT_DCT_TYPE_KEY: str = "'http://purl.org/dc/terms/type'.'@id'"
DEFAULT_ID_KEY: str = "https://w3id.org/edc/v0.0.1/ns/id"


class BaseConnectorConsumerService(BaseService):
    _catalog_controller: BaseDmaController
    _edr_controller: BaseDmaController
    _contract_negotiation_controller: BaseDmaController
    _transfer_process_controller: BaseDmaController

    connection_manager: BaseConnectionManager
    dataspace_version: str

    NEGOTIATION_ID_KEY = "contractNegotiationId"

    def __init__(self, dataspace_version: str, base_url: str, dma_path: str, headers: dict = None,
                 connection_manager: BaseConnectionManager = None, verbose: bool = True, debug: bool = False, logger: logging.Logger = None, verify_ssl: bool = True):
        self.dataspace_version = dataspace_version
        self.verbose = verbose
        self.debug = debug
        self.logger = logger
        self.verify_ssl = verify_ssl
        # Backwards compatibility: if verbose is True and no logger provided, use default logger
        if self.verbose and self.logger is None:
            self.logger = logging.getLogger(__name__)

        self.dma_adapter = AdapterFactory.get_dma_adapter(
            dataspace_version=dataspace_version,
            base_url=base_url,
            dma_path=dma_path,
            headers=headers
        )

        self.controllers = ControllerFactory.get_dma_controllers_for_version(
            dataspace_version=dataspace_version,
            adapter=self.dma_adapter,
            controller_types=[
                ControllerType.CATALOG,
                ControllerType.EDR,
                ControllerType.CONTRACT_NEGOTIATION,
                ControllerType.TRANSFER_PROCESS
            ]
        )

        self._catalog_controller = self.controllers.get(ControllerType.CATALOG)
        self._edr_controller = self.controllers.get(ControllerType.EDR)
        self._contract_negotiation_controller = self.controllers.get(ControllerType.CONTRACT_NEGOTIATION)
        self._transfer_process_controller = self.controllers.get(ControllerType.TRANSFER_PROCESS)

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

    def get_edr(self, transfer_id: str, verify: bool = None) -> dict | None:
        """
        Gets and EDR Token.

        This function sends a GET request to the EDC to retrieve the EDR (Endpoint Data Reference) 
        token for the given transfer ID. The EDR token is used to access the data behind the EDC.

        Parameters:
        transfer_id (str): The unique identifier for the transfer process.
        verify (bool, optional): Whether to verify SSL certificates. If None, uses service default.

        Returns:
        dict | None: The response content from the GET request, or None if the request fails.

        Raises:
        Exception: If the EDC response is not successful (status code is not 200).
        """
        ## Build edr transfer url
        # Use service-level verify_ssl if verify not explicitly provided
        if verify is None:
            verify = getattr(self, 'verify_ssl', True)
        response: Response = self.edrs.get_data_address(oid=transfer_id, params={"auto_refresh": True}, verify=verify)
        if (response is None or response.status_code != 200):
            raise ConnectionError(
                "[Connector Service]: It was not possible to get the edr because the EDC response was not successful!")
        return response.json()

    def get_endpoint_with_token(self, transfer_id: str) -> tuple[str, str]:
        """
        @returns: tuple[dataplane_endpoint:str, authorization:str]
        """
        ## Get authorization key from the edr
        edr: dict = self.get_edr(transfer_id=transfer_id)
        if (edr is None):
            raise RuntimeError("[Connector Service]: It was not possible to retrieve the edr token and the dataplane endpoint!")

        return edr["endpoint"], edr["authorization"]

    def get_catalog(self, counter_party_id: str = None, counter_party_address: str = None,
                    request: BaseCatalogModel = None, timeout=60, verify: bool = None, context:dict=DEFAULT_CONTEXT) -> dict | None:
        """
        Retrieves the EDC DCAT catalog. Allows to get the catalog without specifying the request, which can be overridden
        
        Parameters:
        counter_party_address (str): The URL of the EDC provider.
        request (BaseCatalogModel, optional): The request payload for the catalog API. If not provided, a default request will be used.
        verify (bool, optional): Whether to verify SSL certificates. If None, uses service default.

        Returns:
        dict | None: The EDC catalog as a dictionary, or None if the request fails.
        """
        ## Get EDC DCAT catalog
        if request is None:
            if counter_party_id is None or counter_party_address is None:
                raise ValueError(
                    "[Connector Service]: Either request or counter_party_id and counter_party_address are required to build a catalog request")
            request = self.get_catalog_request(counter_party_id=counter_party_id,
                                               counter_party_address=counter_party_address, context=context)
        
        if self.debug:
            self.logger.info(f"[Connector Service] [CATALOG REQUEST]: {request.to_data()}")
        
        ## Get catalog with configurable timeout
        # Use service-level verify_ssl if verify not explicitly provided
        if verify is None:
            verify = getattr(self, 'verify_ssl', True)
        response: Response = self.catalogs.get_catalog(obj=request, timeout=timeout, verify=verify)
        ## In case the response code is not successfull or the response is null
        if response is None or response.status_code != 200:
            status_code = response.status_code if response is not None else 'None'
            error_msg = f"[Connector Service]: It was not possible to get the catalog from the EDC provider! Response code: [{status_code}]"
            if getattr(self, 'verbose', False) and response is not None:
                error_msg += f"\nResponse headers: {dict(response.headers)}"
                error_msg += f"\nResponse body: {response.text}"
            elif getattr(self, 'logger', None) and response is not None:
                self.logger.debug("[get_catalog] Error response body: %s", response.text)
            raise ConnectionError(error_msg)
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
            "@context": {
                "@vocab": "https://w3id.org/edc/v0.0.1/ns/"
            },
            "@type": "QuerySpec",
            "filterExpression": filter_expression
        }

    def get_catalog_request_with_filter(self, counter_party_id: str, counter_party_address: str,
                                        filter_expression: list[dict], context: dict=DEFAULT_CONTEXT) -> BaseCatalogModel:
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
                                                                     counter_party_address=counter_party_address, context=context)

        catalog_request.queryspec = self.get_query_spec(filter_expression=filter_expression)

        return catalog_request

    def get_edr_negotiation_request(self, counter_party_id: str, counter_party_address: str, target: str,
                                    policy: dict, protocol: str = DSP_0_8, context: dict = ["https://w3id.org/tractusx/policy/v1.0.0","http://www.w3.org/ns/odrl.jsonld",{"@vocab": "https://w3id.org/edc/v0.0.1/ns/"}]) -> BaseContractNegotiationModel:
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
            raise ValueError("[Connector Service]: Policy offer id is not available!")

        return ModelFactory.get_contract_negotiation_model(
            dataspace_version=self.dataspace_version,  # version is to be included in the BaseService class  
            context=context,
            counter_party_address=counter_party_address,
            offer_id=offer_id,
            asset_id=target,
            provider_id=counter_party_id,
            offer_policy=policy,
            protocol=protocol
        )

        ## Simple catalog request without filter

    def get_catalog_request(self, counter_party_id: str, counter_party_address: str, context={"edc": "https://w3id.org/edc/v0.0.1/ns/","odrl": "http://www.w3.org/ns/odrl/2/","dct": "https://purl.org/dc/terms/"}) -> BaseCatalogModel:
        return ModelFactory.get_catalog_model(
            dataspace_version=self.dataspace_version,
            context=context,
            counter_party_id=counter_party_id,  ## bpn of the provider
            counter_party_address=counter_party_address,  ## dsp url from the provider
        )

    def start_edr_negotiation(self, counter_party_id: str, counter_party_address: str, target: str,
                              policy: dict, verify: bool = None, protocol: str = DSP_0_8, context: dict = None) -> str | None:
        """
        Starts the edr negotiation and gives the negotation id

        @param counter_party_id: The identifier of the counterparty (Business Partner Number [BPN]).
        @param counter_party_address: The URL of the EDC provider.
        @param target: The target asset for the negotiation.
        @param policy: The policy to be used for the negotiation.
        @param verify: Whether to verify SSL certificates. If None, uses service default.
        @param protocol: DSP protocol version. Pass None to use defaults. Defaults to None.
        @param context: JSON-LD context for negotiation request. Pass None to use defaults. Defaults to None.
        @returns: negotiation_id:str or if Fail -> None
        """

        ## Prepare the request
        request: BaseContractNegotiationModel = self.get_edr_negotiation_request(counter_party_id=counter_party_id,
                                                                                 counter_party_address=counter_party_address,
                                                                                 target=target,
                                                                                 policy=policy,
                                                                                 protocol=protocol,
                                                                                 context=context)

        # Debug logging: log negotiation request
        if self.debug:
            self.logger.info(f"[Connector Service] [NEGOTIATION REQUEST]: {request.to_data()}")

        ## Build catalog api url
        # Use service-level verify_ssl if verify not explicitly provided
        if verify is None:
            verify = getattr(self, 'verify_ssl', True)
        response: Response = self.edrs.create(request, verify=verify)
        ## In case the response code is not successfull or the response is null
        if (response is None or response.status_code != 200):
            return None

        content: dict = response.json()
        ## Check if the id was returned in the response
        if ("@id" not in content):
            return None

        return content.get("@id", None)

    def get_edr_negotiation_filter(self, negotiation_id: str) -> BaseQuerySpecModel:

        return ModelFactory.get_queryspec_model(
            dataspace_version=self.dataspace_version,
            filter_expression=[
                self.get_filter_expression(key=self.NEGOTIATION_ID_KEY, operator="=", value=negotiation_id)]
        )

    def get_catalogs_by_dct_type(self, counter_party_id: str, edcs: list, dct_type: str,
                                 dct_type_key: str = "'http://purl.org/dc/terms/type'.'@id'", timeout: int = None, **kwargs):
        return self.get_catalogs_with_filter(counter_party_id=counter_party_id, edcs=edcs, 
                                             filter_expression=[self.get_filter_expression(key=dct_type_key, value=dct_type, operator="=")],
                                             timeout=timeout, **kwargs)

    def get_catalogs_with_filter(self, counter_party_id: str, edcs: list, filter_expression: list[dict],
                                 timeout: int = None, context: dict = DEFAULT_CONTEXT, **kwargs):

        ## Where the catalogs get stored
        catalogs: dict = {}
        threads: list[threading.Thread] = []

        for edc_url in edcs:
            thread_kwargs = {
                'counter_party_id': counter_party_id,
                'counter_party_address': edc_url,
                'filter_expression': filter_expression,
                'timeout': timeout,
                'catalogs': catalogs,
                'context': context,
                **kwargs
            }
            thread = threading.Thread(target=self.get_catalog_with_filter_parallel, kwargs=thread_kwargs)
            thread.start()  ## Start thread
            threads.append(thread)

        ## Allow the threads to process
        for thread in threads:
            thread.join()  ## Waiting until they process

        return catalogs

    def get_catalog_by_dct_type(self, counter_party_id: str, counter_party_address: str, dct_type: str,
                                dct_type_key="'http://purl.org/dc/terms/type'.'@id'", operator="=", timeout=None, context=DEFAULT_CONTEXT, **kwargs):
        return self.get_catalog_with_filter(counter_party_id=counter_party_id,
                                            counter_party_address=counter_party_address, filter_expression=[
                self.get_filter_expression(key=dct_type_key, value=dct_type, operator=operator)],
                                            timeout=timeout, context=context, **kwargs)

    def get_catalog_by_asset_id(self, counter_party_id: str, counter_party_address: str, asset_id: str,
                                id_key: str = "https://w3id.org/edc/v0.0.1/ns/id", operator: str = "=", 
                                timeout: int = None, verify: bool = None, context=DEFAULT_CONTEXT, **kwargs) -> dict:
        """
        Retrieves a catalog filtered by a specific asset ID.

        Parameters:
        counter_party_id (str): The identifier of the counterparty (Business Partner Number [BPN]).
        counter_party_address (str): The URL of the EDC provider.
        asset_id (str): The asset ID to filter by.
        id_key (str): The operand key used to match the asset ID. Defaults to the EDC id namespace key.
        operator (str): The filter operator. Defaults to "=".
        timeout (int, optional): Request timeout in seconds.
        verify (bool, optional): Whether to verify SSL certificates. If None, uses service default.
        context (dict, optional): The context for the request. Defaults to DEFAULT_CONTEXT.
        **kwargs: Additional subclass-specific parameters (e.g., protocol for Saturn).
        Returns:
        dict: The filtered EDC catalog.
        """
        return self.get_catalog_with_filter(
            counter_party_id=counter_party_id,
            counter_party_address=counter_party_address,
            filter_expression=[self.get_filter_expression(key=id_key, value=asset_id, operator=operator)],
            timeout=timeout,
            verify=verify,
            context=context,
            **kwargs
        )

    def get_catalog_with_filter_parallel(self, counter_party_id: str, counter_party_address: str,
                                         filter_expression: list[dict], catalogs: dict = None,
                                         timeout: int = None, context: dict = DEFAULT_CONTEXT, **kwargs) -> None:
        catalogs[counter_party_address] = self.get_catalog_with_filter(counter_party_id=counter_party_id,
                                                                       counter_party_address=counter_party_address,
                                                                       filter_expression=filter_expression,
                                                                       timeout=timeout, context=context, **kwargs)

    ## Get catalog request with filter
    def get_catalog_with_filter(self, counter_party_id: str, counter_party_address: str, filter_expression: list[dict],
                                timeout: int = None, verify: bool = None, context: dict = DEFAULT_CONTEXT, **kwargs) -> dict:
        """
        Retrieves a catalog from the EDC provider based on a specified filter.

        Parameters:
        counter_party_id (str): The identifier of the counterparty (Business Partner Number [BPN]).
        counter_party_address (str): The URL of the EDC provider.
        filter_expression (list[dict]): A list of filter conditions.
        timeout (int, optional): Request timeout in seconds.
        verify (bool, optional): Whether to verify SSL certificates. If None, uses service default.
        context (dict, optional): JSON-LD context for the request. Defaults to DEFAULT_CONTEXT.
        **kwargs: Additional subclass-specific parameters (e.g., protocol for Saturn).

        Returns:
        dict: The catalog entries that match the specified filter.
        """
        # Note: **kwargs allows subclasses to pass additional parameters (e.g., protocol in Saturn)
        # Base implementation ignores them, but subclass overrides can use them
        return self.get_catalog(request=self.get_catalog_request_with_filter(counter_party_id=counter_party_id,
                                                                             counter_party_address=counter_party_address,
                                                                             filter_expression=filter_expression),
                                timeout=timeout, verify=verify, context=context)

    def get_edr_entry(self, negotiation_id: str, verify: bool = None) -> dict | None:
        """
        Gets the edr negotiation details for a given negotiation id

        @param negotiation_id: The unique identifier for the negotiation process.
        @param verify: Whether to verify SSL certificates. If None, uses service default.
        
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
        # Use service-level verify_ssl if verify not explicitly provided
        if verify is None:
            verify = getattr(self, 'verify_ssl', True)
        response: Response = self.edrs.query(request, verify=verify)
        ## In case the response code is not successfull or the response is null
        if (response is None or response.status_code != 200):
            raise ConnectionError(f"[Connector Service]: EDR Entry not found for the negotiation_id=[{negotiation_id}]!")

        ## The response is a list
        data = response.json()

        if (len(data) == 0):
            return None

        return data.pop()  ## Return last entry of the list (should be just one entry because of the filter)

    def _build_optional_kwargs(self, protocol: str = None, context: dict = None, 
                                protocol_key: str = 'protocol', context_key: str = 'context') -> dict:
        """
        Build optional keyword arguments dictionary, skipping None values.
        
        @param protocol: DSP protocol version (optional).
        @param context: JSON-LD context (optional).
        @param protocol_key: Key name for protocol in kwargs. Defaults to 'protocol'.
        @param context_key: Key name for context in kwargs. Defaults to 'context'.
        @returns: Dictionary containing only non-None parameters.
        """
        kwargs: dict = {}
        if protocol is not None:
            kwargs[protocol_key] = protocol
        if context is not None:
            kwargs[context_key] = context
        return kwargs

    def _fetch_and_validate_catalog(self, counter_party_id: str, counter_party_address: str,
                                     filter_expression: list[dict], policies: list = None,
                                     **catalog_kwargs) -> list:
        """
        Fetch catalog and validate that matching assets with acceptable policies exist.
        
        @param counter_party_id: The identifier of the counterparty.
        @param counter_party_address: The URL of the EDC provider.
        @param filter_expression: Catalog filter conditions.
        @param policies: Allow-list of accepted usage policies.
        @param catalog_kwargs: Additional arguments for catalog request.
        @returns: List of (asset_id, policy) tuples.
        @raises RuntimeError: If catalog retrieval or policy validation fails.
        """
        catalog_response = self.get_catalog_with_filter(
            counter_party_id=counter_party_id,
            counter_party_address=counter_party_address,
            filter_expression=filter_expression,
            **catalog_kwargs
        )
        
        if catalog_response is None:
            raise RuntimeError(
                f"[Connector Service]: [{counter_party_address}] It was not possible to retrieve the catalog from the edc provider! Catalog response is empty!")

        try:
            valid_assets_policies = DspTools.filter_assets_and_policies(
                catalog=catalog_response,
                allowed_policies=policies
            )
        except Exception as e:
            raise RuntimeError(
                f"[Connector Service]: [{counter_party_address}] It was not possible to find a valid policy in the catalog! Reason: [{str(e)}]")

        if len(valid_assets_policies) == 0:
            raise RuntimeError(
                f"[Connector Service]: [{counter_party_address}] It was not possible to find a valid policy in the catalog! Asset ID and the Policy are empty!")

        return valid_assets_policies

    def _start_negotiation_for_assets(self, counter_party_id: str, counter_party_address: str,
                                       valid_assets_policies: list, **negotiation_kwargs) -> str:
        """
        Attempt to start negotiation for the first valid asset/policy pair.
        
        @param counter_party_id: The identifier of the counterparty.
        @param counter_party_address: The URL of the EDC provider.
        @param valid_assets_policies: List of (asset_id, policy) tuples.
        @param negotiation_kwargs: Additional arguments for negotiation request.
        @returns: Negotiation ID.
        @raises RuntimeError: If no negotiation could be started.
        """
        for asset_id, policy in valid_assets_policies:
            negotiation_id = self.start_edr_negotiation(
                counter_party_id=counter_party_id,
                counter_party_address=counter_party_address,
                target=asset_id,
                policy=policy,
                **negotiation_kwargs
            )
            if negotiation_id is not None:
                return negotiation_id

        raise RuntimeError(
            f"[Connector Service]: [{counter_party_address}] It was not possible to start the EDR Negotiation! The negotiation id is empty!")

    def _check_single_negotiation_state(self, negotiation_id: str, counter_party_address: str, 
                                        last_logged_state: str | None) -> tuple[str | None, str | None]:
        """
        Check negotiation state for a single poll attempt.
        
        @param negotiation_id: The unique identifier for the negotiation process.
        @param counter_party_address: The URL of the EDC provider (for logging).
        @param last_logged_state: The last state that was logged.
        @returns: Tuple of (negotiation_state, updated_last_logged_state).
        @raises RuntimeError: If negotiation is TERMINATED.
        """
        state_response = self.contract_negotiations.get_by_id(negotiation_id)
        if state_response is None or state_response.status_code != 200:
            return None, last_logged_state
            
        state_data = state_response.json()
        negotiation_state = state_data.get("state", state_data.get("edc:state"))
        
        # Log state change if logger is available and state changed
        if self.logger and negotiation_state != last_logged_state:
            self.logger.info(
                "[Connector Service]: [%s] Negotiation [%s] state: %s",
                counter_party_address, negotiation_id, negotiation_state)
            last_logged_state = negotiation_state
        
        # Check terminal states
        if negotiation_state == "TERMINATED":
            raise RuntimeError(
                f"[Connector Service]: [{counter_party_address}] The EDR Negotiation [{negotiation_id}] was TERMINATED by the provider!")
        
        return negotiation_state, last_logged_state

    def _poll_negotiation_state(self, negotiation_id: str, counter_party_address: str,
                                 max_wait: int, poll_interval: int) -> None:
        """
        Poll negotiation status until it reaches FINALIZED state.
        
        @param negotiation_id: The unique identifier for the negotiation process.
        @param counter_party_address: The URL of the EDC provider (for logging).
        @param max_wait: Maximum seconds to wait.
        @param poll_interval: Seconds to wait between poll attempts.
        @raises TimeoutError: If negotiation doesn't reach FINALIZED within max_wait.
        @raises RuntimeError: If negotiation is TERMINATED.
        """
        elapsed: float = 0.0
        negotiation_state: str | None = None
        last_logged_state: str | None = None
        
        while elapsed < max_wait:
            try:
                negotiation_state, last_logged_state = self._check_single_negotiation_state(
                    negotiation_id, counter_party_address, last_logged_state)
                
                if negotiation_state == "FINALIZED":
                    return
            except RuntimeError:
                raise
            except Exception as e:
                if self.logger:
                    self.logger.warning(
                        "[Connector Service]: [%s] Failed to check negotiation state: %s",
                        counter_party_address, e)
            
            op.wait(seconds=poll_interval)
            elapsed += poll_interval

        raise TimeoutError(
            f"[Connector Service]: [{counter_party_address}] The EDR Negotiation [{negotiation_id}] did not reach FINALIZED state after {max_wait}s (last state: {negotiation_state})!")

    def _wait_for_edr_entry(self, negotiation_id: str, counter_party_address: str,
                            max_wait: int, poll_interval: int) -> dict:
        """
        Poll for EDR entry until it becomes available.
        
        @param negotiation_id: The unique identifier for the negotiation process.
        @param counter_party_address: The URL of the EDC provider (for logging).
        @param max_wait: Maximum seconds to wait.
        @param poll_interval: Seconds to wait between poll attempts.
        @returns: EDR entry dictionary.
        @raises TimeoutError: If EDR entry is not found within max_wait.
        """
        elapsed: float = 0.0
        
        while elapsed < max_wait:
            edr_entry = self.get_edr_entry(negotiation_id=negotiation_id)
            if edr_entry is not None:
                return edr_entry
            
            if self.logger:
                self.logger.info(
                    "[Connector Service]: [%s] EDR entry for negotiation [%s] not yet available, waiting %ss...",
                    counter_party_address, negotiation_id, poll_interval)
            
            op.wait(seconds=poll_interval)
            elapsed += poll_interval

        raise TimeoutError(
            f"[Connector Service]: [{counter_party_address}] The EDR Negotiation [{negotiation_id}] has failed! The EDR entry was not found after {max_wait}s!")

    def negotiate_and_transfer(self, counter_party_id: str, counter_party_address: str, filter_expression: list[dict],
                               policies: list = None, max_wait: int = 60, poll_interval: int = 1,
                               protocol: str = None, catalog_context: dict = None, negotiation_context: dict = None) -> dict:
        """
        Performs the full DSP exchange: catalog lookup → contract negotiation → EDR entry retrieval.

        Internally calls ``self.get_catalog_with_filter`` and ``self.start_edr_negotiation`` via
        virtual dispatch, so subclass overrides (e.g. saturn protocol/context defaults) are respected
        automatically.

        @param counter_party_id: The identifier of the counterparty (Business Partner Number [BPN]).
        @param counter_party_address: The URL of the EDC provider.
        @param filter_expression: Catalog filter conditions.
        @param policies: Allow-list of accepted usage policies. Pass ``None`` to accept any policy
            offered by the provider (test-only; avoid in production). Defaults to None.
        @param max_wait: Maximum seconds to wait for negotiation FINALIZED state and EDR entry. Defaults to 60.
        @param poll_interval: Seconds to wait between poll attempts. Defaults to 1.
        @param protocol: DSP protocol version to use. Pass ``None`` to use the subclass default. Defaults to None.
        @param catalog_context: JSON-LD context for catalog requests. Pass ``None`` to use the subclass default. Defaults to None.
        @param negotiation_context: JSON-LD context for negotiation requests. Pass ``None`` to use the subclass default. Defaults to None.
        @returns: edr_entry:dict, if fails Exception
        """
        # Phase 1: Fetch catalog and validate policies
        catalog_kwargs = self._build_optional_kwargs(protocol=protocol, context=catalog_context)
        valid_assets_policies = self._fetch_and_validate_catalog(
            counter_party_id=counter_party_id,
            counter_party_address=counter_party_address,
            filter_expression=filter_expression,
            policies=policies,
            **catalog_kwargs
        )

        # Phase 2: Start negotiation for the first valid asset
        negotiation_kwargs = self._build_optional_kwargs(protocol=protocol, context=negotiation_context)
        negotiation_id = self._start_negotiation_for_assets(
            counter_party_id=counter_party_id,
            counter_party_address=counter_party_address,
            valid_assets_policies=valid_assets_policies,
            **negotiation_kwargs
        )

        # Phase 3: Poll negotiation state until FINALIZED
        self._poll_negotiation_state(
            negotiation_id=negotiation_id,
            counter_party_address=counter_party_address,
            max_wait=max_wait,
            poll_interval=poll_interval
        )

        # Phase 4: Wait for EDR entry to become available
        edr_entry = self._wait_for_edr_entry(
            negotiation_id=negotiation_id,
            counter_party_address=counter_party_address,
            max_wait=max_wait,
            poll_interval=poll_interval
        )

        return edr_entry

    def get_transfer_id(self, counter_party_id: str, counter_party_address: str, filter_expression: list[dict],
                        policies: list = None, max_wait: int = 60, poll_interval: int = 1,
                        protocol: str = None, catalog_context: dict = None, negotiation_context: dict = None) -> str:

        """
        Returns a cached EDR transfer ID if available, otherwise performs a full contract negotiation.

        Parameters:
        counter_party_id (str): The identifier of the counterparty (Business Partner Number [BPN]).
        counter_party_address (str): The URL of the EDC provider.
        policies (list | None, optional): Allow-list of accepted usage policies. Pass ``None`` to
            accept any policy offered by the provider (test-only; avoid in production). Defaults to None.
        max_wait (int): Maximum seconds to wait for negotiation FINALIZED state and EDR entry. Defaults to 60.
        poll_interval (int): Seconds to wait between poll attempts. Defaults to 1.
        protocol (str, optional): DSP protocol version. Pass ``None`` to use the subclass default. Defaults to None.
        catalog_context (dict, optional): JSON-LD context for catalog requests. Pass ``None`` to use the subclass default. Defaults to None.
        negotiation_context (dict, optional): JSON-LD context for negotiation requests. Pass ``None`` to use the subclass default. Defaults to None.

        Returns:
        str: The transfer ID.

        Raises:
        Exception: If the EDR entry is not found or the transfer ID is not available.
        """

        if policies is None and self.logger:
            self.logger.warning(
                "\n%s\n"
                "  ATTENTION! — policies=None DETECTED\n"
                "%s\n"
                "  [Connector Service]: [%s]\n"
                "  ANY policy offered by the provider will be accepted automatically.\n"
                "  This bypasses all usage-policy enforcement.\n"
                "\n"
                "  \u25b6  RECOMMENDED FOR TESTING / DEVELOPMENT ONLY.\n"
                "  \u25b6  DO NOT USE IN PRODUCTION.\n"
                "     Always pass an explicit allow-list of accepted policies.\n"
                "%s",
                "=" * 72, "=" * 72, counter_party_address, "=" * 72)

        ## Hash the policies to get checksum.
        current_policies_checksum = hashlib.sha3_256(str(policies).encode('utf-8')).hexdigest()
        filter_expression_checksum = hashlib.sha3_256(str(filter_expression).encode('utf-8')).hexdigest()
        ## If the counter party id is already available and the transfer key is also present
        transfer_process_id: str = self.connection_manager.get_connection_transfer_id(counter_party_id=counter_party_id,
                                                                                      counter_party_address=counter_party_address,
                                                                                      query_checksum=filter_expression_checksum,
                                                                                      policy_checksum=current_policies_checksum)
        ## If is there return the cached one, if the selection is the same the transfer id can be reused!
        if transfer_process_id is not None and self.logger:
            self.logger.debug(
                "[Connector Service]: [%s]: EDR transfer_id=[%s] found in the cache for counter_party_id=[%s], filter=[%s] and selected policies",
                counter_party_address, transfer_process_id, counter_party_id, filter_expression)
        if transfer_process_id is not None:
            return transfer_process_id

        if self.logger:
            self.logger.info(
                "[Connector Service]: The EDR was not found in the cache for counter_party_address=[%s], counter_party_id=[%s], filter=[%s] and selected policies, starting new contract negotiation!",
                counter_party_address, counter_party_id, filter_expression)

        ## If not the contract negotiation MUST be done!
        edr_entry: dict = self.negotiate_and_transfer(counter_party_id=counter_party_id,
                                                      counter_party_address=counter_party_address, policies=policies,
                                                      filter_expression=filter_expression,
                                                      max_wait=max_wait,
                                                      poll_interval=poll_interval,
                                                      protocol=protocol,
                                                      catalog_context=catalog_context,
                                                      negotiation_context=negotiation_context)

        ## Check if the edr entry is not none
        if (edr_entry is None):
            raise RuntimeError("[Connector Service]: Failed to get edr entry! Response was none!")

        transfer_process_id = self.connection_manager.add_connection(counter_party_id=counter_party_id,
                                                                      counter_party_address=counter_party_address,
                                                                      query_checksum=filter_expression_checksum,
                                                                      policy_checksum=current_policies_checksum,
                                                                      connection_entry=edr_entry)
        if self.logger:
            self.logger.info("[Connector Service]: The EDR Entry was found! Transfer Process ID: [%s]", transfer_process_id)

        return transfer_process_id

    def do_dsp_by_dct_type(
        self,
        counter_party_id: str,
        counter_party_address: str,
        dct_type: str,
        policies: list = None,
        dct_type_key="'http://purl.org/dc/terms/type'.'@id'",
        operator="="
    ) -> tuple[str, str]:
        """
        Performs DSP (Dataspace Protocol) exchange filtered by DCT (Dublin Core Terms) type from the DCMI Metadata Terms.
        
        This method establishes an EDC connection by filtering the catalog based on a specific DCT type,
        negotiates the contract, and returns the dataplane endpoint and access token for data access.

        Parameters:
        counter_party_id (str): The identifier of the counterparty (Business Partner Number [BPN]).
        counter_party_address (str): The URL of the EDC provider's DSP endpoint.
        dct_type (str): The DCT type to filter assets by (e.g., "IndustryFlagService").
        policies (list, optional): List of allowed policies for contract negotiation. Defaults to None.
        dct_type_key (str, optional): The JSON path key for DCT type filtering. 
            Defaults to "'http://purl.org/dc/terms/type'.'@id'".
        operator (str, optional): The comparison operator for filtering. Defaults to "=".

        Returns:
        tuple[str, str]: A tuple containing (dataplane_endpoint, access_token) for data access.

        Raises:
        RuntimeError: If EDR negotiation fails or dataplane details cannot be retrieved.
        ConnectionError: If catalog retrieval fails.
        
        Example:
        ```python
        endpoint, token = connector.do_dsp_by_dct_type(
            counter_party_id="BPNL000000000001",
            counter_party_address="https://provider-edc.example.com/api/v1/dsp",
            dct_type="IndustryFlagService"
        )
        ```
        """
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
        """
        Performs DSP (Dataspace Protocol) exchange filtered by specific asset ID.
        
        This method establishes an EDC connection by filtering the catalog for a specific asset,
        negotiates the contract, and returns the dataplane endpoint and access token for data access.

        Parameters:
        counter_party_id (str): The identifier of the counterparty (Business Partner Number [BPN]).
        counter_party_address (str): The URL of the EDC provider's DSP endpoint.
        asset_id (str): The unique identifier of the asset to access.
        policies (list, optional): List of allowed policies for contract negotiation. Defaults to None.
        asset_id_key (str, optional): The JSON path key for asset ID filtering. 
            Defaults to "https://w3id.org/edc/v0.0.1/ns/id".
        operator (str, optional): The comparison operator for filtering. Defaults to "=".

        Returns:
        tuple[str, str]: A tuple containing (dataplane_endpoint, access_token) for data access.

        Raises:
        RuntimeError: If EDR negotiation fails or dataplane details cannot be retrieved.
        ConnectionError: If catalog retrieval fails.
        
        Example:
        ```python
        endpoint, token = connector.do_dsp_by_asset_id(
            counter_party_id="BPNL000000000001",
            counter_party_address="https://provider-edc.example.com/api/v1/dsp",
            asset_id="urn:uuid:12345678-1234-1234-1234-123456789abc"
        )
        ```
        """
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
        dct_type_key="'http://purl.org/dc/terms/type'.'@id'",
        operator="=",
        session=None,
        **kwargs,
    ):
        """
        Executes an HTTP GET request to an asset behind an EDC, filtered by DCT type.
        
        This method performs the complete DSP exchange (catalog retrieval, contract negotiation,
        and EDR token acquisition) and then executes a GET request to the resulting dataplane endpoint.

        Parameters:
        counter_party_id (str): The identifier of the counterparty (Business Partner Number [BPN]).
        counter_party_address (str): The URL of the EDC provider's DSP endpoint.
        dct_type (str): The DCT type to filter assets by (e.g., "IndustryFlagService").
        policies (list, optional): List of allowed policies for contract negotiation. Defaults to None.
        dct_type_key (str, optional): The JSON path key for DCT type filtering. 
            Defaults to "'http://purl.org/dc/terms/type'.'@id'".
        operator (str, optional): The comparison operator for filtering. Defaults to "=".
        session (requests.Session, optional): HTTP session for connection reuse. Defaults to None.
        **kwargs: Additional keyword arguments passed to the underlying do_get method 
            (e.g., path, headers, timeout, verify, params, allow_redirects).

        Returns:
        requests.Response: The HTTP response from the GET request to the dataplane.

        Raises:
        RuntimeError: If EDR negotiation fails or dataplane details cannot be retrieved.
        ConnectionError: If catalog retrieval or HTTP request fails.
        
        Example:
        ```python
        response = connector.do_get_by_dct_type(
            counter_party_id="BPNL000000000001",
            counter_party_address="https://provider-edc.example.com/api/v1/dsp",
            dct_type="IndustryFlagService",
            path="/data/latest",
            timeout=30
        )
        data = response.json()
        ```
        """
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
        """
        Executes an HTTP GET request to a specific asset behind an EDC.
        
        This method performs the complete DSP exchange (catalog retrieval, contract negotiation,
        and EDR token acquisition) for a specific asset and then executes a GET request to the 
        resulting dataplane endpoint.

        Parameters:
        counter_party_id (str): The identifier of the counterparty (Business Partner Number [BPN]).
        counter_party_address (str): The URL of the EDC provider's DSP endpoint.
        asset_id (str): The unique identifier of the asset to access.
        policies (list, optional): List of allowed policies for contract negotiation. Defaults to None.
        asset_id_key (str, optional): The JSON path key for asset ID filtering. 
            Defaults to "https://w3id.org/edc/v0.0.1/ns/id".
        operator (str, optional): The comparison operator for filtering. Defaults to "=".
        session (requests.Session, optional): HTTP session for connection reuse. Defaults to None.
        **kwargs: Additional keyword arguments passed to the underlying do_get method 
            (e.g., path, headers, timeout, verify, params, allow_redirects).

        Returns:
        requests.Response: The HTTP response from the GET request to the dataplane.

        Raises:
        RuntimeError: If EDR negotiation fails or dataplane details cannot be retrieved.
        ConnectionError: If catalog retrieval or HTTP request fails.
        
        Example:
        ```python
        response = connector.do_get_by_asset_id(
            counter_party_id="BPNL000000000001",
            counter_party_address="https://provider-edc.example.com/api/v1/dsp",
            asset_id="urn:uuid:12345678-1234-1234-1234-123456789abc",
            path="/data/latest",
            headers={"Accept": "application/json"}
        )
        data = response.json()
        ```
        """
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
        dct_type: str,
        json=None,
        data=None,
        policies: list = None,
        dct_type_key="'http://purl.org/dc/terms/type'.'@id'",
        operator="=",
        session=None,
        **kwargs,
    ) -> tuple[str, str]:
        """
        Executes an HTTP POST request to an asset behind an EDC, filtered by DCT type.
        
        This method performs the complete DSP exchange (catalog retrieval, contract negotiation,
        and EDR token acquisition) and then executes a POST request with the provided data to 
        the resulting dataplane endpoint.

        Parameters:
        counter_party_id (str): The identifier of the counterparty (Business Partner Number [BPN]).
        counter_party_address (str): The URL of the EDC provider's DSP endpoint.
        json (dict, optional): The JSON data to be sent in the POST request.
        data (dict, optional): The data to be sent in the POST request.
        dct_type (str): The DCT type to filter assets by (e.g., "IndustryFlagService").
        policies (list, optional): List of allowed policies for contract negotiation. Defaults to None.
        dct_type_key (str, optional): The JSON path key for DCT type filtering. 
            Defaults to "'http://purl.org/dc/terms/type'.'@id'".
        operator (str, optional): The comparison operator for filtering. Defaults to "=".
        session (requests.Session, optional): HTTP session for connection reuse. Defaults to None.
        **kwargs: Additional keyword arguments passed to the underlying do_post method 
            (e.g., path, content_type, headers, timeout, verify, allow_redirects).

        Returns:
        tuple[str, str]: A tuple containing (dataplane_endpoint, access_token) for the completed request.

        Raises:
        RuntimeError: If EDR negotiation fails or dataplane details cannot be retrieved.
        ConnectionError: If catalog retrieval or HTTP request fails.
        
        Example:
        ```python
        request_data = {"query": "SELECT * FROM data", "limit": 100}
        endpoint, token = connector.do_post_by_dct_type(
            counter_party_id="BPNL000000000001",
            counter_party_address="https://provider-edc.example.com/api/v1/dsp",
            json=request_data,
            dct_type="QueryService",
            path="/query",
            content_type="application/json"
        )
        ```
        """
        return self.do_post(
            counter_party_id=counter_party_id,
            counter_party_address=counter_party_address,
            json=json,
            data=data,
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
        asset_id: str,
        json=None,
        data=None,
        policies: list = None,
        asset_id_key="https://w3id.org/edc/v0.0.1/ns/id",
        operator="=",
        session=None,
        **kwargs
    ) -> tuple[str, str]:
        """
        Executes an HTTP POST request to a specific asset behind an EDC.
        
        This method performs the complete DSP exchange (catalog retrieval, contract negotiation,
        and EDR token acquisition) for a specific asset and then executes a POST request with 
        the provided data to the resulting dataplane endpoint.

        Parameters:
        counter_party_id (str): The identifier of the counterparty (Business Partner Number [BPN]).
        counter_party_address (str): The URL of the EDC provider's DSP endpoint.
        json (dict, optional): The JSON data to be sent in the POST request.
        data (dict, optional): The data to be sent in the POST request.
        asset_id (str): The unique identifier of the asset to access.
        policies (list, optional): List of allowed policies for contract negotiation. Defaults to None.
        asset_id_key (str, optional): The JSON path key for asset ID filtering. 
            Defaults to "https://w3id.org/edc/v0.0.1/ns/id".
        operator (str, optional): The comparison operator for filtering. Defaults to "=".
        session (requests.Session, optional): HTTP session for connection reuse. Defaults to None.
        **kwargs: Additional keyword arguments passed to the underlying do_post method 
            (e.g., path, content_type, headers, timeout, verify, allow_redirects).

        Returns:
        tuple[str, str]: A tuple containing (dataplane_endpoint, access_token) for the completed request.

        Raises:
        RuntimeError: If EDR negotiation fails or dataplane details cannot be retrieved.
        ConnectionError: If catalog retrieval or HTTP request fails.
        
        Example:
        ```python
        update_data = {"status": "processed", "timestamp": "2025-08-07T10:30:00Z"}
        endpoint, token = connector.do_post_by_asset_id(
            counter_party_id="BPNL000000000001",
            counter_party_address="https://provider-edc.example.com/api/v1/dsp",
            json=update_data,
            asset_id="urn:uuid:12345678-1234-1234-1234-123456789abc",
            path="/update",
            content_type="application/json"
        )
        ```
        """
        return self.do_post(
            counter_party_id=counter_party_id,
            counter_party_address=counter_party_address,
            json=json,
            data=data,
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
        policies: list,
        max_wait: int = 60,
        poll_interval: int = 1,
        catalog_context: dict = None,
        negotiation_context: dict = None,
        protocol: str = DSP_0_8
    ) -> tuple[str, str]:
        """
        Does all the dsp necessary operations until getting the edr.
        Giving you all the necessary data to request data to the edc dataplane.

        @param counter_party_id: The identifier of the counterparty (Business Partner Number [BPN]).
        @param counter_party_address: The URL of the EDC provider.
        @param policies: The policies to be used for the transfer.
        @param max_wait: Maximum seconds to wait for negotiation and EDR. Defaults to 60.
        @param poll_interval: Seconds between status poll attempts. Defaults to 1.
        @param catalog_context: JSON-LD context for catalog requests. Defaults to None (uses subclass default).
        @param negotiation_context: JSON-LD context for negotiation requests. Defaults to None (uses subclass default).
        @returns: tuple[dataplane_endpoint:str, edr_access_token:str] or if fail Exception
        """

        ## Get the transfer id 
        transfer_id = self.get_transfer_id(
            counter_party_id=counter_party_id,
            counter_party_address=counter_party_address,
            policies=policies,
            filter_expression=filter_expression,
            protocol=protocol,
            max_wait=max_wait,
            poll_interval=poll_interval,
            catalog_context=catalog_context,
            negotiation_context=negotiation_context
        )
        ## Get the endpoint and the token
        return self.get_endpoint_with_token(transfer_id=transfer_id)

    def assets_exists(self, counter_party_id: str, counter_party_address: str, filter_expression: list[dict],
                      timeout=10) -> bool:

        try:
            catalog = self.get_catalog_with_filter(counter_party_id=counter_party_id,
                                                   counter_party_address=counter_party_address,
                                                   filter_expression=filter_expression, timeout=timeout)
        except Exception:
            raise ConnectionError(
                f"[Connector Service]: Failed to get catalog for counter_party_id=[{counter_party_id}], counter_party_address=[{counter_party_address}], filter_expression=[{filter_expression}]")

        if catalog is None:
            return False

        return not DspTools.is_catalog_empty(catalog=catalog)

    def do_get(  # NOSONAR pylint: disable=too-many-arguments
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
        max_wait: int = 60,
        poll_interval: int = 1,
        catalog_context: dict = DEFAULT_CONTEXT,
        negotiation_context: dict = DEFAULT_NEGOTIATION_CONTEXT,
        protocol: str = DSP_0_8
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
            protocol=protocol,
            filter_expression=filter_expression,
            max_wait=max_wait,
            poll_interval=poll_interval,
            catalog_context=catalog_context,
            negotiation_context=negotiation_context
        )

        if dataplane_url is None or access_token is None:
            raise RuntimeError("[Connector Service]: No dataplane URL or access_token was able to be retrieved!")

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
                session=session
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

    def do_post(  # NOSONAR pylint: disable=too-many-arguments
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
        max_wait: int = 60,
        poll_interval: int = 1,
        catalog_context: dict = DEFAULT_CONTEXT,
        negotiation_context: dict = DEFAULT_NEGOTIATION_CONTEXT,
        protocol: str = DSP_0_8
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
        ## If policies are empty use default policies

        dataplane_url, access_token = self.do_dsp(
            counter_party_id=counter_party_id,
            counter_party_address=counter_party_address,
            policies=policies,
            protocol=protocol,
            filter_expression=filter_expression,
            max_wait=max_wait,
            poll_interval=poll_interval,
            catalog_context=catalog_context,
            negotiation_context=negotiation_context
        )

        if dataplane_url is None or access_token is None:
            raise RuntimeError("[Connector Service]: No dataplane URL or access_token was able to be retrieved!")

        ## Build edr transfer url
        url: str = dataplane_url + path

        dataplane_headers: dict = self.get_data_plane_headers(access_token=access_token, content_type=content_type)
        merged_headers: dict = (headers | dataplane_headers)
        ## Do get request to get a response!
        
        if(session):
            return HttpTools.do_post_with_session(
                url=url,
                json=json,
                data=data,
                headers=merged_headers,
                verify=verify,
                timeout=timeout,
                allow_redirects=allow_redirects,
                session=session
            )

        return HttpTools.do_post(
            url=url,
            json=json,
            data=data,
            headers=merged_headers,
            verify=verify,
            timeout=timeout,
            allow_redirects=allow_redirects
        )
    def do_put(  # NOSONAR pylint: disable=too-many-arguments
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
        max_wait: int = 60,
        poll_interval: int = 1,
        catalog_context: dict = DEFAULT_CONTEXT,
        negotiation_context: dict = DEFAULT_NEGOTIATION_CONTEXT,
        protocol: str = DSP_0_8
    ) -> Response:
        """
        Performs a HTTP PUT request to a specific asset behind an EDC.

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
        ## If policies are empty use default policies

        dataplane_url, access_token = self.do_dsp(
            counter_party_id=counter_party_id,
            counter_party_address=counter_party_address,
            policies=policies,
            protocol=protocol,
            filter_expression=filter_expression,
            max_wait=max_wait,
            poll_interval=poll_interval,
            catalog_context=catalog_context,
            negotiation_context=negotiation_context
        )

        if dataplane_url is None or access_token is None:
            raise RuntimeError("[Connector Service]: No dataplane URL or access_token was able to be retrieved!")

        ## Build edr transfer url
        url: str = dataplane_url + path

        dataplane_headers: dict = self.get_data_plane_headers(access_token=access_token, content_type=content_type)
        merged_headers: dict = (headers | dataplane_headers)
        ## Do get request to get a response!
        
        if(session):
            return HttpTools.do_put_with_session(
                url=url,
                json=json,
                data=data,
                headers=merged_headers,
                verify=verify,
                timeout=timeout,
                allow_redirects=allow_redirects,
                session=session
            )

        return HttpTools.do_put(
            url=url,
            json=json,
            data=data,
            headers=merged_headers,
            verify=verify,
            timeout=timeout,
            allow_redirects=allow_redirects
        )
