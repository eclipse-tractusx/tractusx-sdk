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

from json import dumps as jdumps
from pydantic import Field

from ..base_contract_definition_model import BaseContractDefinitionModel


class ContractDefinitionModel(BaseContractDefinitionModel):
    TYPE: str = Field(default="ContractDefinition", frozen=True)

    def to_data(self):
        """
        Converts the model to a JSON representing the data that will
        be sent to a jupiter connector when using a contract definition model.

        :return: a JSON representation of the model
        """

        data = {
            "@context": self.context,
            "@type": self.TYPE,
            "@id": self.oid,
            "accessPolicyId": self.access_policy_id,
            "contractPolicyId": self.contract_policy_id,
            "assetsSelector": self.assets_selector
        }

        return jdumps(data)
