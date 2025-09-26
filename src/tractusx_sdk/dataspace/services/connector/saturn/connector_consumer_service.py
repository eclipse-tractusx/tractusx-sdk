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

from ..base_connector_consumer import BaseConnectorConsumerService
from ....models.connector.base_catalog_model import BaseCatalogModel
from typing_extensions import override
class ConnectorConsumerService(BaseConnectorConsumerService):
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
        
        
    @override
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
    
    

