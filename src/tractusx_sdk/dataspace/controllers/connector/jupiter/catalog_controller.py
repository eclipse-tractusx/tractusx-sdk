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
from tractusx_sdk.dataspace.models.connector.jupiter import CatalogModel


class CatalogController(DmaController):
    """
    Concrete implementation of the CatalogController for the Connector DMA jupiter.
    """

    endpoint_url = "/v3/catalog"

    def get_catalog(self, obj: CatalogModel, **kwargs):
        kwargs["data"] = obj.to_data()
        return self.adapter.post(url=f"{self.endpoint_url}/request", **kwargs)

