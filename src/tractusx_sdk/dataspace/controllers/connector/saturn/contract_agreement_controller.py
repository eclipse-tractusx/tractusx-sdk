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
from tractusx_sdk.dataspace.controllers.connector.utils.mixins import GetControllerMixin, GetAllControllerMixin
from tractusx_sdk.dataspace.models.connector.saturn import ContractAgreementRetirementModel
from tractusx_sdk.dataspace.constants import V3, V4_ALPHA


class ContractAgreementController(GetControllerMixin, GetAllControllerMixin, DmaController):
    """
    Concrete implementation of the ContractAgreementController for the Connector saturn Data Management API.
    """

    endpoint_url = "/contractagreements"

    def get_negotiation_by_id(self, oid: str, **kwargs):
        return self.adapter.get(url=f"{V3}/{self.endpoint_url}/{oid}/negotiation", **kwargs)

    def agreement_retirement(self, obj: ContractAgreementRetirementModel, **kwargs):
        kwargs["data"] = obj.to_data()
        return self.adapter.post(url=f"{V3}/{self.endpoint_url}/retirements", **kwargs)
    
    def get_all_retired_agreements(self, **kwargs):
        return self.adapter.post(url=f"{V3}/{self.endpoint_url}/retirements/request", **kwargs)

    def delete_retired_agreement_by_id(self, oid: str, **kwargs):
        return self.adapter.delete(url=f"{V3}/{self.endpoint_url}/retirements/{oid}", **kwargs)
    
    def get_all_v4alpha(self, **kwargs):
        return super().get_all(url=f"{V4_ALPHA}/{self.endpoint_url}", **kwargs)
    
    def get_by_id_v4alpha(self, oid: str, **kwargs):
        return super().get_by_id(oid, url=f"{V4_ALPHA}/{self.endpoint_url}", **kwargs)
    
    def get_negotiation_by_id_v4alpha(self, oid: str, **kwargs):
        return self.adapter.get(url=f"{V4_ALPHA}/{self.endpoint_url}/{oid}/negotiation", **kwargs)
