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
import requests_mock
from json import loads as jloads

from src.tractusx_sdk.dataspace.adapters.adapter import Adapter


class TestAdapter(unittest.TestCase):
    def setUp(self):
        self.base_url = "https://example.com"
        self.headers = {"Authorization": "Bearer token"}
        self.adapter = Adapter(base_url=self.base_url)

    def test_builder_creates_adapter_instance(self):
        builder = Adapter.builder()
        builder.base_url(self.base_url)
        builder.headers(self.headers)
        adapter = builder.build()

        self.assertIsInstance(adapter, Adapter)
        self.assertEqual(adapter.base_url, self.base_url)
        self.assertEqual(adapter.session.headers["Authorization"], self.headers["Authorization"])

    def test_builder_fails_without_base_url(self):
        builder = Adapter.builder()
        with self.assertRaises(TypeError):
            builder.build()

    def test_concat_into_url(self):
        base_url = "https://example.com"
        path = "api/v1/resource"
        expected_url = "https://example.com/api/v1/resource"

        result = Adapter.concat_into_url(base_url, path)
        self.assertEqual(expected_url, result)

    def test_concat_into_url_with_slashes(self):
        base_url = "https://example.com/"
        path = "/api/v1/resource/"
        expected_url = "https://example.com/api/v1/resource"

        result = Adapter.concat_into_url(base_url, path)
        self.assertEqual(expected_url, result)

    def test_concat_into_url_with_empty_path(self):
        base_url = "https://example.com"
        path = ""
        expected_url = "https://example.com/"

        result = Adapter.concat_into_url(base_url, path)
        self.assertEqual(expected_url, result)

    @requests_mock.Mocker()
    def test_request_method(self, mock_request):
        mock_url = f"{self.base_url}/test-endpoint"
        mock_response_data = {"key": "value"}
        mock_request.get(mock_url, json=mock_response_data, status_code=200)

        response = self.adapter.request("get", "test-endpoint")

        self.assertEqual(200, response.status_code)
        self.assertEqual(mock_response_data, jloads(response.body.decode("utf-8")))
        self.assertEqual("application/json", response.headers["Content-Type"])

    def tearDown(self):
        self.adapter.close()
