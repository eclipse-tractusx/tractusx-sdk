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

from src.tractusx_sdk.dataspace.models.connector.base_asset_model import BaseAssetModel


class ConcreteAssetModel(BaseAssetModel):
    @classmethod
    def to_data(cls):
        return {}


class TestBaseAssetModel(unittest.TestCase):
    def setUp(self):
        self.oid = "test-oid"
        self.context = {"key": "value"}
        self.data_address = {"address": "test-address"}
        self.properties = {"prop": "value"}
        self.private_properties = {"private_prop": "private_value"}

    def test_builder_no_id(self):
        with self.assertRaises(ValidationError):
            builder = ConcreteAssetModel.builder()
            builder.data_address(self.data_address)
            builder.build()

    def test_builder_no_data_address(self):
        with self.assertRaises(ValidationError):
            builder = ConcreteAssetModel.builder()
            builder.id(self.oid)
            builder.build()

    def test_default_values(self):
        builder = ConcreteAssetModel.builder()
        builder.id(self.oid)
        builder.data_address(self.data_address)
        asset = builder.build()

        self.assertEqual(ConcreteAssetModel, type(asset))
        self.assertEqual(self.oid, asset.oid)
        self.assertEqual(self.data_address, asset.data_address)
        self.assertEqual({"@vocab": "https://w3id.org/edc/v0.0.1/ns/"}, asset.context)
        self.assertEqual({}, asset.properties)
        self.assertEqual({}, asset.private_properties)

    def test_builder_using_data(self):
        builder = ConcreteAssetModel.builder()
        builder.data({
            "oid": self.oid,
            "data_address": self.data_address
        })
        asset = builder.build()

        self.assertEqual(ConcreteAssetModel, type(asset))
        self.assertEqual(self.oid, asset.oid)
        self.assertEqual(self.data_address, asset.data_address)

    def test_builder_using_bad_data(self):
        builder = ConcreteAssetModel.builder()
        builder.data({
            "oid": self.oid,
            "data_address": self.data_address,
            "non-existing-key": "value"
        })
        asset = builder.build()

        self.assertEqual(ConcreteAssetModel, type(asset))
        self.assertEqual(self.oid, asset.oid)
        self.assertEqual(self.data_address, asset.data_address)

    def test_complete_builder(self):
        builder = ConcreteAssetModel.builder()
        builder.id(self.oid)
        builder.context(self.context)
        builder.data_address(self.data_address)
        builder.properties(self.properties)
        builder.private_properties(self.private_properties)
        asset = builder.build()

        self.assertEqual(ConcreteAssetModel, type(asset))
        self.assertEqual(self.oid, asset.oid)
        self.assertEqual(self.context, asset.context)
        self.assertEqual(self.data_address, asset.data_address)
        self.assertEqual(self.properties, asset.properties)
        self.assertEqual(self.private_properties, asset.private_properties)
