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
from unittest.mock import Mock, MagicMock

from tractusx_sdk.dataspace.models.connector.base_catalog_model import BaseCatalogModel
from tractusx_sdk.dataspace.models.connector.base_queryspec_model import BaseQuerySpecModel
from tractusx_sdk.dataspace.models.connector.model_factory import ModelFactory


class TestModelFactoryCatalog(unittest.TestCase):
    def setUp(self):
        self.connector_version = "jupiter"
        self.counter_party_address = "https://counterparty.com"
        self.counter_party_id = "counterparty-id"
        self.context = {"key": "value"}
        self.additional_scopes = ["scope-1", "scope-2"]
        self.queryspec_data = {"key": "value"}
        self.queryspec_model_to_data = {"queryspec_key": "queryspec_value"}

    def test_get_catalog_model_with_defaults(self):
        model = ModelFactory.get_catalog_model(
            connector_version=self.connector_version,
            counter_party_address=self.counter_party_address,
            counter_party_id=self.counter_party_id
        )

        self.assertIsInstance(model, BaseCatalogModel)
        self.assertEqual(self.counter_party_address, model.counter_party_address)
        self.assertEqual(self.counter_party_id, model.counter_party_id)
        self.assertEqual({
            "@vocab": "https://w3id.org/edc/v0.0.1/ns/"
        }, model.context)
        self.assertEqual([], model.additional_scopes)
        self.assertEqual({}, model.queryspec)

    def test_get_catalog_model_with_queryspec_data_only(self):
        model = ModelFactory.get_catalog_model(
            connector_version=self.connector_version,
            counter_party_address=self.counter_party_address,
            counter_party_id=self.counter_party_id,
            queryspec=self.queryspec_data
        )

        self.assertEqual(self.queryspec_data, model.queryspec)

    def test_get_catalog_model_with_queryspec_model_only(self):
        queryspec_model = Mock(BaseQuerySpecModel)
        queryspec_model.to_data = MagicMock(return_value=self.queryspec_model_to_data)

        model = ModelFactory.get_catalog_model(
            connector_version=self.connector_version,
            counter_party_address=self.counter_party_address,
            counter_party_id=self.counter_party_id,
            queryspec_model=queryspec_model
        )

        self.assertEqual(self.queryspec_model_to_data, model.queryspec)

    def test_get_catalog_model_with_queryspec_model_overwrite(self):
        queryspec_model = Mock(BaseQuerySpecModel)
        queryspec_model.to_data = MagicMock(return_value=self.queryspec_model_to_data)

        model = ModelFactory.get_catalog_model(
            connector_version=self.connector_version,
            counter_party_address=self.counter_party_address,
            counter_party_id=self.counter_party_id,
            queryspec_model=queryspec_model,
            queryspec=self.queryspec_data
        )

        self.assertEqual(self.queryspec_model_to_data, model.queryspec)

    def test_get_catalog_model_without_defaults(self):
        model = ModelFactory.get_catalog_model(
            connector_version=self.connector_version,
            counter_party_address=self.counter_party_address,
            counter_party_id=self.counter_party_id,
            context=self.context,
            additional_scopes=self.additional_scopes,
            queryspec=self.queryspec_data
        )

        self.assertIsInstance(model, BaseCatalogModel)
        self.assertEqual(self.counter_party_address, model.counter_party_address)
        self.assertEqual(self.counter_party_id, model.counter_party_id)
        self.assertEqual(self.context, model.context)
        self.assertEqual(self.additional_scopes, model.additional_scopes)
        self.assertEqual(self.queryspec_data, model.queryspec)
