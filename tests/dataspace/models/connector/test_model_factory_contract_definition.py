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

from tractusx_sdk.dataspace.models.connector.base_contract_definition_model import BaseContractDefinitionModel
from tractusx_sdk.dataspace.models.connector.model_factory import ModelFactory


class TestModelFactoryContractDefinition(unittest.TestCase):
    def setUp(self):
        self.connector_version = "jupiter"
        self.oid = "test-oid"
        self.access_policy_id = "test-access-policy-id"
        self.contract_policy_id = "test-contract-policy-id"
        self.context = {"key": "value"}
        self.assets_selector = [{"key": "value"}]

    def test_get_contract_definition_model_with_defaults(self):
        model = ModelFactory.get_contract_definition_model(
            connector_version=self.connector_version,
            oid=self.oid,
            access_policy_id=self.access_policy_id,
            contract_policy_id=self.contract_policy_id
        )

        self.assertIsInstance(model, BaseContractDefinitionModel)
        self.assertEqual(self.oid, model.oid)
        self.assertEqual(self.access_policy_id, model.access_policy_id)
        self.assertEqual(self.contract_policy_id, model.contract_policy_id)
        self.assertEqual({
            "@vocab": "https://w3id.org/edc/v0.0.1/ns/"
        }, model.context)
        self.assertEqual([], model.assets_selector)

    def test_get_contract_definition_model_without_defaults(self):
        model = ModelFactory.get_contract_definition_model(
            connector_version=self.connector_version,
            oid=self.oid,
            access_policy_id=self.access_policy_id,
            contract_policy_id=self.contract_policy_id,
            context=self.context,
            assets_selector=self.assets_selector
        )

        self.assertIsInstance(model, BaseContractDefinitionModel)
        self.assertEqual(self.oid, model.oid)
        self.assertEqual(self.access_policy_id, model.access_policy_id)
        self.assertEqual(self.contract_policy_id, model.contract_policy_id)
        self.assertEqual(self.context, model.context)
        self.assertEqual(self.assets_selector, model.assets_selector)
