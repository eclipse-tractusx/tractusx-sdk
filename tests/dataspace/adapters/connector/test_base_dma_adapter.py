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
from src.tractusx_sdk.dataspace.adapters.connector.base_dma_adapter import BaseDmaAdapter


class TestBaseDmaAdapter(unittest.TestCase):
    def setUp(self):
        self.base_url = "https://example.com"
        self.dma_path = "/dma"
        self.headers = {"Authorization": "Bearer token"}

    def test_initializer(self):
        adapter = BaseDmaAdapter(base_url=self.base_url, dma_path=self.dma_path, headers=self.headers)

        self.assertEqual(self.dma_path, adapter.dma_path)
        self.assertEqual(f"{self.base_url}{self.dma_path}", adapter.base_url)
        self.assertEqual(self.headers["Authorization"], adapter.session.headers["Authorization"])

    def test_builder(self):
        builder = BaseDmaAdapter.builder()
        builder.base_url(self.base_url)
        builder.headers(self.headers)
        builder.dma_path(self.dma_path)
        adapter = builder.build()

        self.assertIsInstance(adapter, BaseDmaAdapter)
        self.assertEqual(adapter.dma_path, self.dma_path)
        self.assertEqual(adapter.base_url, f"{self.base_url}{self.dma_path}")
        self.assertEqual(adapter.session.headers["Authorization"], self.headers["Authorization"])

    def test_builder_fails_without_dma_path(self):
        builder = BaseDmaAdapter.builder()
        builder.base_url(self.base_url)
        with self.assertRaises(TypeError):
            builder.build()
