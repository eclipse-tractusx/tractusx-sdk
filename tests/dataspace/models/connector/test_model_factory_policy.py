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

from src.tractusx_sdk.dataspace.models.connector.base_policy_model import BasePolicyModel
from src.tractusx_sdk.dataspace.models.connector.model_factory import ModelFactory


class TestModelFactoryPolicy(unittest.TestCase):
    def setUp(self):
        self.connector_version = "v0_9_0"
        self.oid = "test-oid"
        self.context = {"key": "value"}
        self.permissions = [{"action": "permission"}]
        self.prohibitions = [{"action": "prohibitions"}]
        self.obligations = [{"action": "obligations"}]

    def test_get_policy_model_with_defaults(self):
        model = ModelFactory.get_policy_model(
            connector_version=self.connector_version,
            oid=self.oid
        )

        self.assertIsInstance(model, BasePolicyModel)
        self.assertEqual(self.oid, model.oid)
        self.assertEqual({
            "@vocab": "https://w3id.org/edc/v0.0.1/ns/"
        }, model.context)
        self.assertEqual([], model.permissions)
        self.assertEqual([], model.prohibitions)
        self.assertEqual([], model.obligations)

    def test_get_policy_model_without_defaults(self):
        model = ModelFactory.get_policy_model(
            connector_version=self.connector_version,
            oid=self.oid,
            context=self.context,
            permissions=self.permissions,
            prohibitions=self.prohibitions,
            obligations=self.obligations
        )

        self.assertIsInstance(model, BasePolicyModel)
        self.assertEqual(self.oid, model.oid)
        self.assertEqual(self.context, model.context)
        self.assertEqual(self.permissions, model.permissions)
        self.assertEqual(self.prohibitions, model.prohibitions)
        self.assertEqual(self.obligations, model.obligations)
