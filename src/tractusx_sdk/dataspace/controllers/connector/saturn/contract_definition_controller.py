#################################################################################
# Eclipse Tractus-X - Software Development KIT
#
# Copyright (c) 2025,2026 LKS Next
# Copyright (c) 2025,2026 Contributors to the Eclipse Foundation
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

from typing import Any

import requests

from .dma_controller import DmaController
from tractusx_sdk.dataspace.controllers.connector.utils.mixins import CrudDmaController
from tractusx_sdk.dataspace.models.connector.saturn import ContractDefinitionModel


class ContractDefinitionController(CrudDmaController[ContractDefinitionModel], DmaController):
    """
    Concrete implementation of the ContractDefinitionController for the Connector saturn Data Management API.

    This class overrides the create and update methods in order to ensure the correct class types are used, instead of the generic ones.
    """

    endpoint_url = "/v3/contractdefinitions"

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

    def create(self, obj: ContractDefinitionModel, **kwargs: Any) -> requests.Response:
        return super().create(obj, **kwargs)

    def update(self, obj: ContractDefinitionModel, **kwargs: Any) -> requests.Response:
        return super().update(obj, **kwargs)
