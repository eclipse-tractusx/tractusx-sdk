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

import unittest

from tractusx_sdk.dataspace.controllers.connector.base_dma_controller import BaseDmaController
from tractusx_sdk.dataspace.services.connector.base_connector_services import BaseConnectorService


class TestBaseConnectorService(unittest.TestCase):
    def setUp(self):
        self.version = "v0_9_0"
        self.base_url = "https://example.com"
        self.dma_path = "/dma"
        self.headers = {"Authorization": "Bearer token"}

        self.service = BaseConnectorService(
            version=self.version,
            base_url=self.base_url,
            dma_path=self.dma_path,
            headers=self.headers,
        )

    def test_initialization_creates_controllers(self):
        self.assertIsInstance(self.service._asset_controller, BaseDmaController)
        self.assertIsNotNone(self.service._asset_controller)

        self.assertIsInstance(self.service._catalog_controller, BaseDmaController)
        self.assertIsNotNone(self.service._catalog_controller)

        self.assertIsInstance(self.service._contract_agreement_controller, BaseDmaController)
        self.assertIsNotNone(self.service._contract_agreement_controller)

        self.assertIsInstance(self.service._contract_definition_controller, BaseDmaController)
        self.assertIsNotNone(self.service._contract_definition_controller)

        self.assertIsInstance(self.service._contract_negotiation_controller, BaseDmaController)
        self.assertIsNotNone(self.service._contract_negotiation_controller)

        self.assertIsInstance(self.service._edr_controller, BaseDmaController)
        self.assertIsNotNone(self.service._edr_controller)

        self.assertIsInstance(self.service._policy_controller, BaseDmaController)
        self.assertIsNotNone(self.service._policy_controller)

        self.assertIsInstance(self.service._transfer_process_controller, BaseDmaController)
        self.assertIsNotNone(self.service._transfer_process_controller)

    def test_builder_sets_dma_path(self):
        builder = BaseConnectorService.builder()
        builder.dma_path(self.dma_path)
        self.assertEqual(builder._data["dma_path"], self.dma_path)

    def test_assets_property(self):
        self.assertEqual(self.service._asset_controller, self.service.assets)

    def test_catalogs_property(self):
        self.assertEqual(self.service._catalog_controller, self.service.catalogs)

    def test_contract_agreements_property(self):
        self.assertEqual(self.service._contract_agreement_controller, self.service.contract_agreements)

    def test_contract_definitions_property(self):
        self.assertEqual(self.service._contract_definition_controller, self.service.contract_definitions)

    def test_contract_negotiations_property(self):
        self.assertEqual(self.service._contract_negotiation_controller, self.service.contract_negotiations)

    def test_edrs_property(self):
        self.assertEqual(self.service._edr_controller, self.service.edrs)

    def test_policies_property(self):
        self.assertEqual(self.service._policy_controller, self.service.policies)

    def test_transfer_processes_property(self):
        self.assertEqual(self.service._transfer_process_controller, self.service.transfer_processes)
