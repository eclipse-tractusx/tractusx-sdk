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
from pydantic import ValidationError

from src.tractusx_sdk.dataspace.models.connector.base_contract_definition_model import BaseContractDefinitionModel


class ConcreteContractDefinitionModel(BaseContractDefinitionModel):
    @classmethod
    def to_data(cls):
        return {}


class TestBasePolicyModel(unittest.TestCase):

    def setUp(self):
        self.oid = "test-oid"
        self.access_policy_id = "test-access-policy-id"
        self.contract_policy_id = "test-contract-policy-id"
        self.context = {"key": "value"}
        self.assets_selector = [{"key": "value"}]

    def test_builder_no_id(self):
        with self.assertRaises(ValidationError):
            builder = ConcreteContractDefinitionModel.builder()
            builder.access_policy_id(self.access_policy_id)
            builder.contract_policy_id(self.contract_policy_id)
            builder.build()

    def test_builder_no_access_policy_id(self):
        with self.assertRaises(ValidationError):
            builder = ConcreteContractDefinitionModel.builder()
            builder.id(self.oid)
            builder.contract_policy_id(self.contract_policy_id)
            builder.build()

    def test_builder_no_contract_policy_id(self):
        with self.assertRaises(ValidationError):
            builder = ConcreteContractDefinitionModel.builder()
            builder.id(self.oid)
            builder.access_policy_id(self.access_policy_id)
            builder.build()

    def test_default_values(self):
        builder = ConcreteContractDefinitionModel.builder()
        builder.id(self.oid)
        builder.access_policy_id(self.access_policy_id)
        builder.contract_policy_id(self.contract_policy_id)
        contract_definition = builder.build()

        self.assertEqual(ConcreteContractDefinitionModel, type(contract_definition))
        self.assertEqual(self.oid, contract_definition.oid)
        self.assertEqual(self.access_policy_id, contract_definition.access_policy_id)
        self.assertEqual(self.contract_policy_id, contract_definition.contract_policy_id)
        self.assertEqual({"@vocab": "https://w3id.org/edc/v0.0.1/ns/"}, contract_definition.context)
        self.assertEqual([], contract_definition.assets_selector)

    def test_complete_builder(self):
        builder = ConcreteContractDefinitionModel.builder()
        builder.id(self.oid)
        builder.access_policy_id(self.access_policy_id)
        builder.contract_policy_id(self.contract_policy_id)
        builder.context(self.context)
        builder.assets_selector(self.assets_selector)
        contract_definition = builder.build()

        self.assertEqual(ConcreteContractDefinitionModel, type(contract_definition))
        self.assertEqual(self.oid, contract_definition.oid)
        self.assertEqual(self.access_policy_id, contract_definition.access_policy_id)
        self.assertEqual(self.contract_policy_id, contract_definition.contract_policy_id)
        self.assertEqual(self.context, contract_definition.context)
        self.assertEqual(self.assets_selector, contract_definition.assets_selector)
