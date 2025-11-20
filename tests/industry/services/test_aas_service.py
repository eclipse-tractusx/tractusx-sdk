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
# Comments and refactors made using an LLM AI Agent
# Revised by an human committer

import unittest
import yaml
from unittest.mock import patch, MagicMock
from pydantic import ValidationError 
from tractusx_sdk.dataspace.tools.encoding_tools import encode_as_base64_url_safe
from tractusx_sdk.industry.services.aas_service import AasService
from tractusx_sdk.industry.models.v3.aas import AssetKind, GetAllShellDescriptorsResponse

class TestAasService(unittest.TestCase):
    @patch("tractusx_sdk.dataspace.tools.HttpTools.do_get")
    def test_getallassetadministrationshelldescriptors_noparameters_correct(self, mock_do_get):
        # Load mock response from YAML
        with open("tests/industry/services/yaml_mocks/mock_full_response_data.json", "r") as file:
            mock_response_data = yaml.safe_load(file)

        mock_do_get.return_value = MagicMock(
            json=MagicMock(return_value=mock_response_data),
            raise_for_status=MagicMock()
        )

        # Initialize the service
        service = AasService(
            base_url="https://example.com",
            base_lookup_url="https://lookup.example.com",
            api_path="/api/v3",
            auth_service=None,
            verify_ssl=True
        )

        # Call the method
        response = service.get_all_asset_administration_shell_descriptors()

        # Assertions
        self.assertIsInstance(response, GetAllShellDescriptorsResponse)
        self.assertEqual(response, GetAllShellDescriptorsResponse(**mock_response_data))
        self.assertEqual(len(response.result), 2)
        self.assertEqual(response.result[0].id, "urn:uuid:3d050cd8-cdc7-4d65-9f37-70a65d5f53f5")
        self.assertEqual(response.paging_metadata.cursor, "wJlCDLIl6KTWypN7T6vc6nWEmEYe99Hjf1XY1xmqV-M=#")

        # Verify the mock was called with correct parameters
        mock_do_get.assert_called_once_with(
            url="https://example.com/api/v3/shell-descriptors",
            params={},
            headers={"Accept": "application/json"},
            verify=True
        )
        

    @patch("tractusx_sdk.dataspace.tools.HttpTools.do_get")
    def test_getallassetadministrationshelldescriptors_allparameters_correct(self, mock_do_get):
        # Load mock response from YAML
        with open("tests/industry/services/yaml_mocks/mock_full_response_data.json", "r") as file:
            mock_response_data = yaml.safe_load(file)

        mock_do_get.return_value = MagicMock(
            json=MagicMock(return_value=mock_response_data),
            raise_for_status=MagicMock()
        )

        # Initialize the service
        service = AasService(
            base_url="https://example.com",
            base_lookup_url="https://lookup.example.com",
            api_path="/api/v3",
            auth_service=None,
            verify_ssl=True
        )

        # Define parameters
        params = {
            "limit": 10,
            "cursor": "wJlCDLIl6KTWypN7T6vc6nWEmEYe99Hjf1XY1xmqV-M=#",
            "asset_kind": AssetKind.INSTANCE,
            "asset_type": "test_asset_type",
            "bpn": "BPNL000000000000"
        }

        # Call the method
        response = service.get_all_asset_administration_shell_descriptors(**params)

        # Assertions
        self.assertIsInstance(response, GetAllShellDescriptorsResponse)
        self.assertEqual(response, GetAllShellDescriptorsResponse(**mock_response_data))
        self.assertEqual(len(response.result), 2)
        self.assertEqual(response.result[0].id, "urn:uuid:3d050cd8-cdc7-4d65-9f37-70a65d5f53f5")
        self.assertEqual(response.paging_metadata.cursor, "wJlCDLIl6KTWypN7T6vc6nWEmEYe99Hjf1XY1xmqV-M=#")

        # Verify the mock was called with correct parameters
        mock_do_get.assert_called_once_with(
            url="https://example.com/api/v3/shell-descriptors",
            params={
                "limit": 10,
                "cursor": "wJlCDLIl6KTWypN7T6vc6nWEmEYe99Hjf1XY1xmqV-M=#",
                "assetKind": AssetKind.INSTANCE,  # Use AssetKind.INSTANCE.value
                "assetType": encode_as_base64_url_safe("test_asset_type"),  # Base64-encoded asset_type
            },
            headers={
                "Accept": "application/json",
                "Edc-Bpn": "BPNL000000000000"  # Include BPN in headers
            },
            verify=True
        )
        
    @patch("tractusx_sdk.dataspace.tools.HttpTools.do_get")
    def test_getallassetadministrationshelldescriptors_noid_error(self, mock_do_get):
        # Load mock response from YAML
        with open("tests/industry/services/yaml_mocks/mock_noid_response_data.json", "r") as file:
            mock_response_data = yaml.safe_load(file)

        mock_do_get.return_value = MagicMock(
            json=MagicMock(return_value=mock_response_data),
            raise_for_status=MagicMock()
        )

        # Initialize the service
        service = AasService(
            base_url="https://example.com",
            base_lookup_url="https://lookup.example.com",
            api_path="/api/v3",
            auth_service=None,
            verify_ssl=True
        )

        # Assert that the expected exception is raised
        with self.assertRaises(ValidationError) as context:
            service.get_all_asset_administration_shell_descriptors()

        # Optionally, verify the exception message or details
        self.assertIn("Field required", str(context.exception))

        # Verify the mock was called with correct parameters
        mock_do_get.assert_called_once_with(
            url="https://example.com/api/v3/shell-descriptors",
            params={},
            headers={"Accept": "application/json"},
            verify=True
        )

if __name__ == "__main__":
    unittest.main()
