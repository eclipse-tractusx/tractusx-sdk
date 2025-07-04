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
from unittest.mock import patch
from tractusx_sdk.dataspace.models.connector.model_factory import ModelFactory, ModelType


class TestModelFactory(unittest.TestCase):
    def setUp(self):
        self.connector_version = "jupiter"
        self.oid = "test-oid"
        self.data_address = {"type": "test_type", "value": "test_value"}

    def test_get_model_unsupported_version(self):
        with self.assertRaises(ValueError):
            ModelFactory._get_model_builder(
                model_type=ModelType.ASSET,
                connector_version="NonExistentVersion"
            )

    def test_get_model_unsupported_type(self):
        with self.assertRaises(AttributeError):
            model_type = Enum('ModelType', { 'foo': 'bar' })
            ModelFactory._get_model_builder(
                model_type=model_type.foo,
                connector_version="jupiter"
            )

    def test_get_model_import_error(self):
        with patch.object(ModelFactory, "SUPPORTED_VERSIONS", new=["v0_0_0"]):
            with self.assertRaises(ImportError):
                ModelFactory._get_model_builder(
                    model_type=ModelType.ASSET,
                    connector_version="v0_0_0"
                )