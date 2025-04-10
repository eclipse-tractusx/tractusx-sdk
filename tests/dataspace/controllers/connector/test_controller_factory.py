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
from enum import Enum
from unittest.mock import patch, Mock

from src.tractusx_sdk.dataspace.adapters.connector.base_dma_adapter import BaseDmaAdapter
from src.tractusx_sdk.dataspace.controllers.connector.controller_factory import ControllerFactory, ControllerType
from src.tractusx_sdk.dataspace.controllers.connector.v0_9_0 import (
    AssetController,
    CatalogController,
    ContractAgreementController,
    ContractDefinitionController,
    ContractNegotiationController,
    EdrController,
    PolicyController,
    TransferProcessController
)


class TestControllerFactory(unittest.TestCase):
    def setUp(self):
        self.connector_version = "v0_9_0"
        self.adapter = Mock(BaseDmaAdapter)

    def test_get_controller_unsupported_version(self):
        with self.assertRaises(ValueError):
            ControllerFactory._get_controller_builder(
                controller_type=ControllerType.ASSET,
                connector_version="NonExistentVersion"
            )

    def test_get_controller_unsupported_type(self):
        with self.assertRaises(AttributeError):
            controller_type = Enum('ControllerType', {'foo': 'bar'})
            ControllerFactory._get_controller_builder(
                controller_type=controller_type.foo,
                connector_version="v0_9_0"
            )

    def test_get_controller_import_error(self):
        with patch.object(ControllerFactory, "SUPPORTED_VERSIONS", new=["v0_0_0"]):
            with self.assertRaises(ImportError):
                ControllerFactory._get_controller_builder(
                    controller_type=ControllerType.ASSET,
                    connector_version="v0_0_0"
                )

    def test_get_asset_controller(self):
        controller = ControllerFactory.get_asset_controller(
            connector_version=self.connector_version,
            adapter=self.adapter
        )

        self.assertIsNotNone(controller)
        self.assertIsInstance(controller, AssetController)

    def test_get_catalog_controller(self):
        controller = ControllerFactory.get_catalog_controller(
            connector_version=self.connector_version,
            adapter=self.adapter
        )

        self.assertIsNotNone(controller)
        self.assertIsInstance(controller, CatalogController)

    def test_get_contract_agreement_controller(self):
        controller = ControllerFactory.get_contract_agreement_controller(
            connector_version=self.connector_version,
            adapter=self.adapter
        )

        self.assertIsNotNone(controller)
        self.assertIsInstance(controller, ContractAgreementController)

    def test_get_contract_definition_controller(self):
        controller = ControllerFactory.get_contract_definition_controller(
            connector_version=self.connector_version,
            adapter=self.adapter
        )

        self.assertIsNotNone(controller)
        self.assertIsInstance(controller, ContractDefinitionController)

    def test_get_contract_negotiation_controller(self):
        controller = ControllerFactory.get_contract_negotiation_controller(
            connector_version=self.connector_version,
            adapter=self.adapter
        )

        self.assertIsNotNone(controller)
        self.assertIsInstance(controller, ContractNegotiationController)

    def test_get_edr_controller(self):
        controller = ControllerFactory.get_edr_controller(
            connector_version=self.connector_version,
            adapter=self.adapter
        )

        self.assertIsNotNone(controller)
        self.assertIsInstance(controller, EdrController)

    def test_get_policy_controller(self):
        controller = ControllerFactory.get_policy_controller(
            connector_version=self.connector_version,
            adapter=self.adapter
        )

        self.assertIsNotNone(controller)
        self.assertIsInstance(controller, PolicyController)

    def test_get_transfer_process_controller(self):
        controller = ControllerFactory.get_transfer_process_controller(
            connector_version=self.connector_version,
            adapter=self.adapter
        )

        self.assertIsNotNone(controller)
        self.assertIsInstance(controller, TransferProcessController)
