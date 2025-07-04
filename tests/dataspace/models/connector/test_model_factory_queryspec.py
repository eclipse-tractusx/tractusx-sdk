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

from tractusx_sdk.dataspace.models.connector.base_queryspec_model import BaseQuerySpecModel
from tractusx_sdk.dataspace.models.connector.model_factory import ModelFactory


class TestModelFactoryQuerySpec(unittest.TestCase):
    def setUp(self):
        self.connector_version = "jupiter"
        self.context = {"key": "value"}
        self.offset = 5
        self.limit = 20
        self.sort_order = "ASC"
        self.sort_field = "name"
        self.filter_expression = [{"key": "value"}]

    def test_get_queryspec_model_with_defaults(self):
        model = ModelFactory.get_queryspec_model(
            connector_version=self.connector_version
        )

        self.assertIsInstance(model, BaseQuerySpecModel)
        self.assertEqual(0, model.offset)
        self.assertEqual(10, model.limit)
        self.assertEqual("DESC", model.sort_order)
        self.assertEqual("createdAt", model.sort_field)
        self.assertEqual([], model.filter_expression)
        self.assertEqual({
            "@vocab": "https://w3id.org/edc/v0.0.1/ns/"
        }, model.context)

    def test_get_queryspec_model_without_defaults(self):
        model = ModelFactory.get_queryspec_model(
            connector_version=self.connector_version,
            context=self.context,
            offset=self.offset,
            limit=self.limit,
            sort_order=self.sort_order,
            sort_field=self.sort_field,
            filter_expression=self.filter_expression
        )

        self.assertEqual(self.offset, model.offset)
        self.assertEqual(self.limit, model.limit)
        self.assertEqual(self.sort_order, model.sort_order)
        self.assertEqual(self.sort_field, model.sort_field)
        self.assertEqual(self.filter_expression, model.filter_expression)
        self.assertEqual(self.context, model.context)
