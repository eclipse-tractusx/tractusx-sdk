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

from ..base_contract_definition_model import BaseContractDefinitionModel


class ContractDefinitionModel(BaseContractDefinitionModel):
    _TYPE = "ContractDefinition"

    def to_data(self):
        """
        Converts the model to a JSON representing the data that will
        be sent to a v0.9.0 connector when using a contract definition model.

        :return: a JSON representation of the model
        """

        data = {
            "@context": self.context,
            "@type": self._TYPE,
            "@id": self.id,
            "properties": self.properties,
            "privateProperties": self.private_properties,
            "dataAddress": self.data_address
        }

        return jdumps(data)
