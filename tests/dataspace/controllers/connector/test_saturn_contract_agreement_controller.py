#################################################################################
# Eclipse Tractus-X - Software Development KIT
#
# Copyright (c) 2026 LKS Next
# Copyright (c) 2026 Contributors to the Eclipse Foundation
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


from unittest import TestCase
from unittest.mock import Mock

from tractusx_sdk.dataspace.adapters.adapter import Adapter
from tractusx_sdk.dataspace.constants import V4_ALPHA
from tractusx_sdk.dataspace.controllers.connector.saturn import ContractAgreementController


class TestSaturnContractAgreementController(TestCase):
    def setUp(self):
        self.adapter = Adapter("https://example.com")
        self.adapter.request = Mock()
        self.controller = ContractAgreementController(self.adapter)

    def test_get_all_v4alpha_uses_versioned_request_url(self):
        self.controller.get_all_v4alpha()

        self.adapter.request.assert_called_once_with(
            "post", f"{V4_ALPHA}/contractagreements/request"
        )

    def test_get_by_id_v4alpha_uses_versioned_resource_url(self):
        self.controller.get_by_id_v4alpha("agreement-1")

        self.adapter.request.assert_called_once_with(
            "get", f"{V4_ALPHA}/contractagreements/agreement-1"
        )