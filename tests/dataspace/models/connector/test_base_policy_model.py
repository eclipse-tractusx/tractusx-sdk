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

from src.tractusx_sdk.dataspace.models.connector.base_policy_model import BasePolicyModel


class ConcretePolicyModel(BasePolicyModel):
    @classmethod
    def to_data(cls):
        return {}


class TestBasePolicyModel(unittest.TestCase):

    def setUp(self):
        self.oid = "test-oid"
        self.context = {"key": "value"}
        self.use_action = [{"action": "odrl:use"}]

    def test_builder_no_id(self):
        with self.assertRaises(ValidationError):
            builder = ConcretePolicyModel.builder()
            builder.build()

    def test_default_values(self):
        builder = ConcretePolicyModel.builder()
        builder.id(self.oid)
        policy = builder.build()

        self.assertEqual(ConcretePolicyModel, type(policy))
        self.assertEqual(self.oid, policy.oid)
        self.assertEqual({"@vocab": "https://w3id.org/edc/v0.0.1/ns/"}, policy.context)
        self.assertEqual([], policy.permissions)
        self.assertEqual([], policy.prohibitions)
        self.assertEqual([], policy.obligations)

    def test_builder_with_permissions_only(self):
        builder = ConcretePolicyModel.builder()
        builder.id(self.oid)
        builder.permissions(self.use_action)
        policy = builder.build()

        self.assertEqual(ConcretePolicyModel, type(policy))
        self.assertEqual(self.oid, policy.oid)
        self.assertEqual(self.use_action, policy.permissions)

    def test_builder_with_prohibitions_only(self):
        builder = ConcretePolicyModel.builder()
        builder.id(self.oid)
        builder.prohibitions(self.use_action)
        policy = builder.build()

        self.assertEqual(ConcretePolicyModel, type(policy))
        self.assertEqual(self.oid, policy.oid)
        self.assertEqual(self.use_action, policy.prohibitions)

    def test_builder_with_obligations_only(self):
        builder = ConcretePolicyModel.builder()
        builder.id(self.oid)
        builder.obligations(self.use_action)
        policy = builder.build()

        self.assertEqual(ConcretePolicyModel, type(policy))
        self.assertEqual(self.oid, policy.oid)
        self.assertEqual(self.use_action, policy.obligations)

    def test_complete_builder(self):
        builder = ConcretePolicyModel.builder()
        builder.id(self.oid)
        builder.context(self.context)
        builder.permissions(self.use_action)
        builder.prohibitions(self.use_action)
        builder.obligations(self.use_action)
        policy = builder.build()

        self.assertEqual(ConcretePolicyModel, type(policy))
        self.assertEqual(self.oid, policy.oid)
        self.assertEqual(self.context, policy.context)
        self.assertEqual(self.use_action, policy.permissions)
        self.assertEqual(self.use_action, policy.prohibitions)
        self.assertEqual(self.use_action, policy.obligations)
