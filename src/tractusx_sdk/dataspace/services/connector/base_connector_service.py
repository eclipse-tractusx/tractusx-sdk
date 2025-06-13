
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
from .base_connector_consumer import BaseConnectorConsumerService
from .base_connector_provider import BaseConnectorProviderService
from fastapi.responses import Response

class BaseConnectorService(BaseService):
    _contract_agreement_controller: BaseDmaController
    _consumer: BaseConnectorConsumerService
    _provider: BaseConnectorProviderService
    base_url: str
    dma_path: str
    version: str
    
    
    def __init__(self, version: str, base_url: str, dma_path: str, headers: dict = None):
        self.base_url = base_url
        self.dma_path = dma_path
        self.version = version
        dma_adapter = AdapterFactory.get_dma_adapter(
            connector_version=version,
            base_url=base_url,
            dma_path=dma_path,
            headers=headers
        )

        controllers = ControllerFactory.get_dma_controllers_for_version(
            connector_version=version,
            adapter=dma_adapter
        )

        self._contract_agreement_controller = controllers.get(ControllerType.CONTRACT_AGREEMENT)
        
        self._consumer = BaseConnectorConsumerService(controllers)
        self._provider = BaseConnectorProviderService(controllers)
    
    class _Builder(BaseService._Builder):
        def dma_path(self, dma_path: str):
            self._data["dma_path"] = dma_path
            return self

    @property
    def contract_agreements(self):
        return self._contract_agreement_controller
    
    @property
    def consumer(self):
        return self._consumer

    @property
    def provider(self):
        return self._provider