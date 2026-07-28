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
from unittest.mock import Mock

import httpx

from tractusx_sdk.industry.adapters.submodel_adapters.http_submodel_adapter import HttpSubmodelAdapter


class TestHttpSubmodelAdapter(unittest.TestCase):

    def setUp(self):
        self.adapter = HttpSubmodelAdapter(
            base_url="https://example.org",
            api_path="/api/v1",
            auth_type="none",
        )
        self.adapter.client = Mock()

    @staticmethod
    def _response(status_code: int, json_data=None, text: str = ""):
        response = Mock()
        response.status_code = status_code
        response.text = text
        if json_data is None:
            response.content = b""
            response.json = Mock(side_effect=ValueError("No JSON content"))
        else:
            response.content = b"{}"
            response.json = Mock(return_value=json_data)
        return response

    def test_read_uses_submodel_metadata_and_returns_json(self):
        metadata = {
            "semantic_id": "urn:sample:semantic",
            "submodel_id": "123e4567-e89b-12d3-a456-426614174000",
        }
        self.adapter.client.get.return_value = self._response(200, {"k": "v"})

        result = self.adapter.read(metadata)

        self.assertEqual(result, {"k": "v"})
        self.adapter.client.get.assert_called_once()

    def test_write_posts_content(self):
        metadata = {
            "semantic_id": "urn:sample:semantic",
            "submodel_id": "123e4567-e89b-12d3-a456-426614174000",
        }
        self.adapter.client.post.return_value = self._response(201)

        self.adapter.write(metadata, b"raw-bytes")

        self.adapter.client.post.assert_called_once()
        self.assertEqual(self.adapter.client.post.call_args.kwargs["content"], b"raw-bytes")

    def test_write_json_serializes_and_posts_content(self):
        metadata = {
            "semantic_id": "urn:sample:semantic",
            "submodel_id": "123e4567-e89b-12d3-a456-426614174000",
        }
        self.adapter.client.post.return_value = self._response(201)

        self.adapter.write_json(metadata, {"hello": "world"})

        self.adapter.client.post.assert_called_once()
        self.assertEqual(self.adapter.client.post.call_args.kwargs["json"], {"hello": "world"})

    def test_custom_url_pattern_builds_request_url_from_metadata(self):
        adapter = HttpSubmodelAdapter(
            base_url="https://example.org",
            url_pattern="{base_url}/custom/{tenant}/{semantic_id}/{submodel_id}",
            auth_type="none",
        )
        adapter.client = Mock()
        adapter.client.get.return_value = self._response(200, {"ok": True})

        metadata = {
            "tenant": "tenant-a",
            "semantic_id": "urn:sample:semantic",
            "submodel_id": "123e4567-e89b-12d3-a456-426614174000",
        }

        adapter.read(metadata)

        self.assertEqual(
            adapter.client.get.call_args.args[0],
            "https://example.org/custom/tenant-a/urn%3Asample%3Asemantic/123e4567-e89b-12d3-a456-426614174000",
        )

    def test_delete_404_raises_file_not_found(self):
        metadata = {
            "semantic_id": "urn:sample:semantic",
            "submodel_id": "123e4567-e89b-12d3-a456-426614174000",
        }
        self.adapter.client.delete.return_value = self._response(404, {"message": "missing"})

        with self.assertRaises(FileNotFoundError):
            self.adapter.delete(metadata)

    def test_exists_returns_false_for_404(self):
        metadata = {
            "semantic_id": "urn:sample:semantic",
            "submodel_id": "123e4567-e89b-12d3-a456-426614174000",
        }
        self.adapter.client.head.return_value = self._response(404, {"message": "missing"})

        self.assertFalse(self.adapter.exists(metadata))

    def test_request_error_raises_connection_error(self):
        metadata = {
            "semantic_id": "urn:sample:semantic",
            "submodel_id": "123e4567-e89b-12d3-a456-426614174000",
        }
        request = httpx.Request("GET", "https://example.org")
        self.adapter.client.get.side_effect = httpx.RequestError("network issue", request=request)

        with self.assertRaises(ConnectionError):
            self.adapter.read(metadata)

    def test_read_uses_metadata_directly(self):
        metadata = {
            "semantic_id": "urn:sample:semantic",
            "submodel_id": "123e4567-e89b-12d3-a456-426614174000",
        }
        self.adapter.client.get.return_value = self._response(200, {"ok": True})

        result = self.adapter.read(metadata)

        self.assertEqual(result, {"ok": True})
