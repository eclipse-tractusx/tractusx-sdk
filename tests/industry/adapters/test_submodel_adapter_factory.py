#################################################################################
# Eclipse Tractus-X - Software Development KIT
#
# Copyright (c) 2026 DRÄXLMAIER Group
# (represented by Lisa Dräxlmaier GmbH)
# Copyright (c) 2026 Contributors to the Eclipse Foundation
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
import tempfile
import os
from types import SimpleNamespace

from tractusx_sdk.industry.adapters.submodel_adapter_factory import (
    SubmodelAdapterFactory,
    SubmodelAdapterType,
)
from tractusx_sdk.industry.adapters.submodel_adapters import FileSystemAdapter, HttpSubmodelAdapter


class TestSubmodelAdapterFactory(unittest.TestCase):

    def tearDown(self):
        SubmodelAdapterFactory.unregister_adapter("external_builder")
        SubmodelAdapterFactory.unregister_adapter("external_class")

    def test_get_file_system_success(self):
        adapter = SubmodelAdapterFactory.get_file_system(root_path="./submodels")

        self.assertIsNotNone(adapter)
        self.assertIsInstance(adapter, FileSystemAdapter)
        self.assertEqual(adapter.root_path, os.path.abspath("./submodels"))

    def test_from_config_success(self):
        adapter = SubmodelAdapterFactory.from_config(
            adapter_type="file_system",
            config={
                "root_path": "./submodels",
            },
        )

        self.assertIsInstance(adapter, FileSystemAdapter)
        self.assertEqual(adapter.root_path, os.path.abspath("./submodels"))

    def test_from_config_enum_type_success(self):
        adapter = SubmodelAdapterFactory.from_config(
            adapter_type=SubmodelAdapterType.FILE_SYSTEM,
            config={
                "root_path": "./custom-submodels",
            },
        )

        self.assertIsInstance(adapter, FileSystemAdapter)
        self.assertEqual(adapter.root_path, os.path.abspath("./custom-submodels"))

    def test_from_config_non_mapping_config_type_error(self):
        with self.assertRaises(TypeError):
            SubmodelAdapterFactory.from_config(
                adapter_type="file_system",
                config=["root_path", "./submodels"],
            )

    def test_from_config_unsupported_type(self):
        with self.assertRaises(ValueError):
            SubmodelAdapterFactory.from_config(
                adapter_type="unsupported",
                config={
                    "root_path": "./submodels",
                },
            )

    def test_from_config_unknown_builder_key(self):
        with self.assertRaises(ValueError):
            SubmodelAdapterFactory.from_config(
                adapter_type="file_system",
                config={
                    "root_path": "./submodels",
                    "unknown": "value",
                },
            )

    def test_from_config_builder_attribute_type_mismatch(self):
        with self.assertRaises(TypeError):
            SubmodelAdapterFactory.from_config(
                adapter_type="file_system",
                config={
                    "root_path": 123,
                },
            )

    def test_adapter_type_listings_before_and_after_external_registration(self):
        self.assertNotIn("file_system", SubmodelAdapterFactory.get_registered_adapter_types())
        self.assertIn("file_system", SubmodelAdapterFactory.get_available_adapter_types())

        class ExternalBuilder:
            def build(self):
                return SimpleNamespace()

        SubmodelAdapterFactory.register_adapter(
            adapter_type="external_builder",
            builder_factory=ExternalBuilder,
        )

        self.assertIn("external_builder", SubmodelAdapterFactory.get_registered_adapter_types())
        self.assertIn("external_builder", SubmodelAdapterFactory.get_available_adapter_types())
        self.assertIn("file_system", SubmodelAdapterFactory.get_available_adapter_types())

    def test_register_external_builder_and_create_from_config(self):
        class ExternalBuilder:
            def __init__(self):
                self._data = {}

            def base_url(self, base_url: str):
                self._data["base_url"] = base_url
                return self

            def api_key(self, api_key: str):
                self._data["api_key"] = api_key
                return self

            def build(self):
                return SimpleNamespace(**self._data)

        SubmodelAdapterFactory.register_adapter(
            adapter_type="external_builder",
            builder_factory=ExternalBuilder,
        )

        adapter = SubmodelAdapterFactory.from_config(
            adapter_type="external_builder",
            config={
                "base_url": "https://example.org",
                "api_key": "token",
            },
        )

        self.assertEqual(adapter.base_url, "https://example.org")
        self.assertEqual(adapter.api_key, "token")

    def test_register_external_adapter_class_and_create_from_config(self):
        class ExternalAdapter:
            @classmethod
            def builder(cls):
                class _Builder:
                    def __init__(self):
                        self._data = {}

                    def root_path(self, root_path: str):
                        self._data["root_path"] = root_path
                        return self

                    def build(self):
                        return SimpleNamespace(source="external_class", **self._data)

                return _Builder()

        SubmodelAdapterFactory.register_adapter(
            adapter_type="external_class",
            adapter_class=ExternalAdapter,
        )

        adapter = SubmodelAdapterFactory.from_config(
            adapter_type="external_class",
            config={
                "root_path": "./outside",
            },
        )

        self.assertEqual(adapter.source, "external_class")
        self.assertEqual(adapter.root_path, "./outside")

    def test_from_config_file_system_with_path_pattern_simple_key(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            adapter = SubmodelAdapterFactory.from_config(
                adapter_type="file_system",
                config={
                    "root_path": temp_dir,
                    "path_pattern": "{asset_path}",
                },
            )

            adapter.write_json({"asset_path": "nested/folder/file.json"}, {"hello": "world"})
            self.assertTrue(adapter.exists({"asset_path": "nested/folder/file.json"}))

    def test_from_config_file_system_with_path_pattern(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            adapter = SubmodelAdapterFactory.from_config(
                adapter_type="file_system",
                config={
                    "root_path": temp_dir,
                    "path_pattern": "{asset}/{name}.json",
                },
            )

            submodel_metadata = {"asset": "a1", "name": "f1"}
            adapter.write_json(submodel_metadata, {"hello": "world"})
            self.assertTrue(adapter.exists(submodel_metadata))

    def test_from_config_http_submodel_success(self):
        adapter = SubmodelAdapterFactory.from_config(
            adapter_type="http_submodel",
            config={
                "base_url": "https://example.org",
                "api_path": "/api/v1",
                "auth_type": "none",
                "url_pattern": "{base_url}{api_path}/{tenant}/{semantic_id}/{submodel_id}",
            },
        )

        self.assertIsInstance(adapter, HttpSubmodelAdapter)
        self.assertEqual(adapter.base_url, "https://example.org")
        self.assertEqual(adapter.api_path, "/api/v1")
