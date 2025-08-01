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

from .dma_controller import DmaController
from tractusx_sdk.dataspace.controllers.connector.utils.mixins import StatefulEntityDmaController
from tractusx_sdk.dataspace.models.connector.jupiter import TransferProcessModel


class TransferProcessController(StatefulEntityDmaController, DmaController):
    """
    Concrete implementation of the TransferProcessController for the Connector jupiter Data Management API.

    This class overrides the create and terminate_by_id methods in order to ensure the correct class types are used, instead of the generic ones.
    """

    endpoint_url = "/v3/transferprocesses"

    def create(self, obj: TransferProcessModel, **kwargs):
        return super().create(obj, **kwargs)

    def terminate_by_id(self, oid: str, obj: TransferProcessModel, **kwargs):
        return super().terminate_by_id(oid, obj, **kwargs)

    def deprovision_by_id(self, oid: str, **kwargs):
        return self.adapter.post(url=f"{self.endpoint_url}/{oid}/deprovision", **kwargs)
