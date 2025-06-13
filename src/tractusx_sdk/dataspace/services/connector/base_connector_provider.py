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
from fastapi.responses import Response
from .base_connector_service import BaseConnectorService

class BaseConnectorProviderService(BaseService):
    _asset_controller: BaseDmaController
    _contract_definition_controller: BaseDmaController
    _policy_controller: BaseDmaController
    
    def __init__(self, controllers: dict):
        self._asset_controller = controllers.get(ControllerType.ASSET)
        self._contract_definition_controller = controllers.get(ControllerType.CONTRACT_DEFINITION)
        self._policy_controller = controllers.get(ControllerType.POLICY)

    @property
    def assets(self):
        return self._asset_controller

    @property
    def contract_definitions(self):
        return self._contract_definition_controller

    @property
    def policies(self):
        return self._policy_controller



    
