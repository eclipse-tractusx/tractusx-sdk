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


class ApplicationObservabilityController(DmaController):
    """
    Concrete implementation of the ApplicationObservabilityController for the Connector saturn Data Management API.

    This class overrides the create method in order to ensure the correct class types are used, instead of the generic ones.
    """

    endpoint_url = "/check"

    def get_health(self, **kwargs):
        return self.adapter.get(url=f"{self.endpoint_url}/health", **kwargs)

    def get_liveness(self, **kwargs):
        return self.adapter.get(url=f"{self.endpoint_url}/liveness", **kwargs)

    def get_readiness(self, **kwargs):
        return self.adapter.get(url=f"{self.endpoint_url}/readiness", **kwargs)

    def get_startup(self, **kwargs):
        return self.adapter.get(url=f"{self.endpoint_url}/startup", **kwargs)
