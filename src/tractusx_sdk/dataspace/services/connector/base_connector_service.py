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

from .base_connector_consumer import BaseConnectorConsumerService
from .base_connector_provider import BaseConnectorProviderService
from ..service import BaseService
from ...adapters.connector.adapter_factory import AdapterFactory
from ...controllers.connector.base_dma_controller import BaseDmaController
from ...controllers.connector.controller_factory import ControllerFactory
from ...managers.auth_manager import AuthManagerInterface


class BaseConnectorService(BaseService):
    _contract_agreement_controller: BaseDmaController
    _consumer_service: BaseConnectorConsumerService
    _provider_service: BaseConnectorProviderService

    def __init__(self, dataspace_version: str, base_url: str, dma_path: str,
                 consumer_service: BaseConnectorConsumerService,
                 provider_service: BaseConnectorProviderService,
                 headers: dict = None,
                 auth_header: AuthManagerInterface | None = None):
        self.dataspace_version = dataspace_version

        merged_headers = headers or {}
        if auth_header is not None:
            merged_headers.update(auth_header.get_auth_headers())

        dma_adapter = AdapterFactory.get_dma_adapter(
            dataspace_version=dataspace_version,
            base_url=base_url,
            dma_path=dma_path,
            headers=merged_headers
        )

        self._contract_agreement_controller = ControllerFactory.get_contract_agreement_controller(
            dataspace_version=dataspace_version,
            adapter=dma_adapter
        )

        self._consumer_service = consumer_service
        self._provider_service = provider_service

    class _Builder(BaseService._Builder):
        def dma_path(self, dma_path: str):
            self._data["dma_path"] = dma_path
            return self

        def provider_service(self, provider_service: BaseConnectorProviderService):
            self._data["provider_service"] = provider_service
            return self

        def consumer_service(self, consumer_service: BaseConnectorConsumerService):
            self._data["consumer_service"] = consumer_service
            return self

    @property
    def contract_agreements(self):
        return self._contract_agreement_controller

    @property
    def consumer(self):
        return self._consumer_service

    @property
    def provider(self):
        return self._provider_service
