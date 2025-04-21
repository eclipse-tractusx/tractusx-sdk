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
from src.tractusx_sdk.dataspace.adapters.connector.adapter_factory import AdapterFactory, AdapterType


class TestAdapterFactory(unittest.TestCase):

    def setUp(self):
        self.base_url = "https://example.com"
        self.headers = {"Authorization": "Bearer token"}
        self.dma_path = "/dma"

    def test_get_dma_adapter_success(self):
        adapter = AdapterFactory.get_dma_adapter(
            connector_version="v0_9_0",
            base_url=self.base_url,
            dma_path=self.dma_path,
            headers=self.headers
        )
        self.assertIsNotNone(adapter)
        self.assertEqual(adapter.base_url, f"{self.base_url}{self.dma_path}")
        self.assertIsNotNone(adapter.session)

    def test_get_adapter_unsupported_version(self):
        with self.assertRaises(ValueError):
            AdapterFactory.get_dma_adapter(
                connector_version="NonExistentVersion",
                base_url=self.base_url,
                dma_path=self.dma_path,
                headers=self.headers
            )

    def test_get_adapter_unsupported_type(self):
        with self.assertRaises(AttributeError):
            adapter_type = Enum('AdapterType', { 'foo': 'bar' })
            AdapterFactory._get_adapter_builder(
                adapter_type=adapter_type.foo,
                connector_version="v0_9_0"
            )

    def test_get_adapter_import_error(self):
        with patch.object(AdapterFactory, "SUPPORTED_VERSIONS", new=["v0_0_0"]):
            with self.assertRaises(ImportError):
                AdapterFactory._get_adapter_builder(
                    adapter_type=AdapterType.DMA_ADAPTER,
                    connector_version="v0_0_0"
                )

    def test_get_dataplane_adapter_failure(self):
        # TODO: There is no dataplane adapter yet. Adjust this test when it is implemented.
        with self.assertRaises(AttributeError):
            AdapterFactory.get_dataplane_adapter(
                connector_version="v0_9_0",
                base_url=self.base_url,
                headers=self.headers
            )
