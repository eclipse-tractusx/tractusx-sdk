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

from src.tractusx_sdk.dataspace.models.connector.model_factory import ModelFactory


class TestModelFactoryAsset(unittest.TestCase):
    def setUp(self):
        self.connector_version = "v0_9_0"
        self.oid = "test-oid"
        self.data_address = {"type": "test_type", "value": "test_value"}
        self.context = {"key": "value"}
        self.properties = {"prop_key": "prop_value"}
        self.private_properties = {"private_key": "private_value"}

    def test_get_asset_model_with_defaults(self):
        model = ModelFactory.get_asset_model(
            connector_version=self.connector_version,
            oid=self.oid,
            data_address=self.data_address
        )

        self.assertEqual(self.oid, model.oid)
        self.assertEqual(self.data_address, model.data_address)
        self.assertEqual({
            "@vocab": "https://w3id.org/edc/v0.0.1/ns/"
        }, model.context)
        self.assertEqual({}, model.properties)
        self.assertEqual({}, model.private_properties)

    def test_get_asset_model_without_defaults(self):
        model = ModelFactory.get_asset_model(
            connector_version=self.connector_version,
            oid=self.oid,
            data_address=self.data_address,
            context=self.context,
            properties=self.properties,
            private_properties=self.private_properties
        )

        self.assertEqual(self.oid, model.oid)
        self.assertEqual(self.data_address, model.data_address)
        self.assertEqual(self.context, model.context)
        self.assertEqual(self.properties, model.properties)
        self.assertEqual(self.private_properties, model.private_properties)
