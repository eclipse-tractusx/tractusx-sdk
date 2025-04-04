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

from ..base_policy_model import BasePolicyModel


class PolicyModel(BasePolicyModel):
    _TYPE = "PolicyDefinition"
    _ODRL_TYPE = "odrl:Set"
    _ODRL_CONTEXT = "http://www.w3.org/ns/odrl.jsonld"

    def to_data(self):
        """
        Converts the model to a JSON representing the data that
        will be sent to the connector when using a policy model.

        :return: a JSON representation of the model
        """

        data = {
            "@context": self._context,
            "@type": self._TYPE,
            "@id": self._id,
            "policy": {
                "@context": self._ODRL_CONTEXT,
                "@type": self._ODRL_TYPE,
                "permission": self._permissions,
                "prohibition": self._prohibitions,
                "obligation": self._obligations
            }
        }

        return jdumps(data)
