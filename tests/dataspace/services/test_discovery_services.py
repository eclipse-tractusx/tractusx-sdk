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

import pytest
from unittest import mock
from tractusx_sdk.dataspace.services.discovery.discovery_finder_service import DiscoveryFinderService
from tractusx_sdk.exceptions import AuthServiceUnavailableError
from tractusx_sdk.dataspace.services.discovery.connector_discovery_service import ConnectorDiscoveryService

@pytest.fixture
def mock_oauth():
    mock_oauth = mock.Mock()
    mock_oauth.connected = True
    mock_oauth.add_auth_header.side_effect = lambda headers: {**headers, "Authorization": "Bearer token"}
    return mock_oauth

@pytest.fixture
def mock_discovery_finder(mock_oauth):
    return DiscoveryFinderService(
        url="https://discovery.example.com",
        oauth=mock_oauth
    )

@pytest.fixture
def connector_service(mock_oauth, mock_discovery_finder):
    with mock.patch.object(ConnectorDiscoveryService, '_get_or_update_discovery_url') as mock_update:
        mock_update.return_value = "https://connector-discovery.example.com"
        service = ConnectorDiscoveryService(
            oauth=mock_oauth,
            discovery_finder_service=mock_discovery_finder,
            connector_discovery_key="bpn",
            cache_timeout_seconds=10
        )
        return service

class TestDiscoveryFinderService:
    
    @mock.patch("tractusx_sdk.dataspace.services.discovery.discovery_finder_service.HttpTools")
    def test_find_discovery_urls_success(self, mock_http, mock_oauth):
        """Test successful discovery URL finding."""
        mock_response = mock.Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "endpoints": [
                {"type": "bpn", "endpointAddress": "https://bpn-discovery.example.com"},
                {"type": "manufacturerPartId", "endpointAddress": "https://part-discovery.example.com"}
            ]
        }
        mock_http.do_post.return_value = mock_response
        
        discovery_finder = DiscoveryFinderService(
            url="https://discovery.example.com",
            oauth=mock_oauth
        )
        
        result = discovery_finder.find_discovery_urls(
            keys=["bpn", "manufacturerPartId"]
        )
        
        expected_body = {
            "types": ["bpn", "manufacturerPartId"]
        }
        
        mock_http.do_post.assert_called_once_with(
            url="https://discovery.example.com",
            headers={'Content-Type': 'application/json', "Authorization": "Bearer token"},
            json=expected_body
        )
        
        assert result == {
            "bpn": "https://bpn-discovery.example.com",
            "manufacturerPartId": "https://part-discovery.example.com"
        }

    def test_find_discovery_urls_auth_service_unreachable(self, mock_oauth):
        """Test discovery URL finding when the OAuth manager cannot reach the IAM on first use."""
        mock_oauth.connected = False
        mock_oauth.add_auth_header.side_effect = AuthServiceUnavailableError("Unable to access the Keycloak instance")
        
        discovery_finder = DiscoveryFinderService(
            url="https://discovery.example.com",
            oauth=mock_oauth
        )
        
        with pytest.raises(AuthServiceUnavailableError, match="Unable to access the Keycloak instance"):
            discovery_finder.find_discovery_urls(keys=["bpn"])

    @mock.patch("tractusx_sdk.dataspace.services.discovery.discovery_finder_service.HttpTools")
    def test_find_discovery_urls_http_error(self, mock_http, mock_oauth):
        """Test discovery URL finding with HTTP error."""
        mock_response = mock.Mock()
        mock_response.status_code = 500
        mock_http.do_post.return_value = mock_response
        
        discovery_finder = DiscoveryFinderService(
            url="https://discovery.example.com",
            oauth=mock_oauth
        )
        
        with pytest.raises(Exception, match="response was not successful"):
            discovery_finder.find_discovery_urls(keys=["bpn"])

    @mock.patch("tractusx_sdk.dataspace.services.discovery.discovery_finder_service.HttpTools")
    def test_find_discovery_urls_no_endpoints(self, mock_http, mock_oauth):
        """Test discovery URL finding when no endpoints are found."""
        mock_response = mock.Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"endpoints": []}
        mock_http.do_post.return_value = mock_response
        
        discovery_finder = DiscoveryFinderService(
            url="https://discovery.example.com",
            oauth=mock_oauth
        )
        
        with pytest.raises(Exception, match="No endpoints were found"):
            discovery_finder.find_discovery_urls(keys=["bpn"])

class TestConnectorDiscoveryService:

    @mock.patch("tractusx_sdk.dataspace.services.discovery.discovery_finder_service.HttpTools")
    def test_get_connector_discovery_url_success(self, mock_http, connector_service):
        """Test successful connector discovery URL retrieval using legacy method."""
        # Mock the HTTP response
        mock_response = mock.Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "endpoints": [
                {
                    "type": "bpn",
                    "description": "Discovery Endpoint",
                    "endpointAddress": "https://connector-discovery.example.com",
                    "documentation": "https://example.com/docs",
                    "resourceId": "bpn"
                }
            ]
        }
        mock_http.do_post.return_value = mock_response
        
        # Test the legacy method that should call the new interface
        url = connector_service.get_connector_discovery_url(connector_discovery_key="bpn")
        
        # Should return the endpoint from the mocked response
        assert url == "https://connector-discovery.example.com"

    @mock.patch("tractusx_sdk.dataspace.services.discovery.discovery_finder_service.HttpTools")
    def test_get_discovery_url_success(self, mock_http, connector_service, mock_discovery_finder):
        """Test successful discovery URL retrieval."""
        # Mock the HTTP response
        mock_response = mock.Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "endpoints": [
                {
                    "type": "bpn",
                    "description": "Discovery Endpoint",
                    "endpointAddress": "https://connector-discovery.example.com",
                    "documentation": "https://example.com/docs",
                    "resourceId": "bpn"
                }
            ]
        }
        mock_http.do_post.return_value = mock_response
        
        url = connector_service.get_discovery_url(mock_discovery_finder, "bpn")
        
        assert url == "https://connector-discovery.example.com"

    @mock.patch("tractusx_sdk.dataspace.services.discovery.discovery_finder_service.HttpTools")
    def test_get_discovery_url_not_found(self, mock_http, connector_service, mock_discovery_finder):
        """Test discovery URL retrieval when endpoint not found."""
        # Mock the HTTP response with empty endpoints
        mock_response = mock.Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"endpoints": []}
        mock_http.do_post.return_value = mock_response
        
        with pytest.raises(Exception, match="No endpoints were found"):
            connector_service.get_discovery_url(mock_discovery_finder, "bpn")

    @mock.patch("tractusx_sdk.dataspace.services.discovery.discovery_finder_service.HttpTools")
    @mock.patch("tractusx_sdk.dataspace.services.discovery.connector_discovery_service.HttpTools")
    def test_find_connector_by_bpn_success(self, mock_connector_http, mock_finder_http, connector_service):
        """Test successful connector finding by BPN."""
        # Mock discovery finder response
        mock_finder_response = mock.Mock()
        mock_finder_response.status_code = 200
        mock_finder_response.json.return_value = {
            "endpoints": [
                {
                    "type": "bpn",
                    "description": "Discovery Endpoint",
                    "endpointAddress": "https://connector-discovery.example.com",
                    "documentation": "https://example.com/docs",
                    "resourceId": "bpn"
                }
            ]
        }
        mock_finder_http.do_post.return_value = mock_finder_response
        
        # Mock connector discovery HTTP response
        mock_connector_response = mock.Mock()
        mock_connector_response.status_code = 200
        mock_connector_response.json.return_value = [
            {
                "bpn": "BPNL000000000001",
                "connectorEndpoint": [
                    "https://edc1.example.com/api/v1/dsp",
                    "https://edc2.example.com/api/v1/dsp"
                ]
            },
            {
                "bpn": "BPNL000000000002",
                "connectorEndpoint": [
                    "https://edc3.example.com/api/v1/dsp"
                ]
            }
        ]
        mock_connector_http.do_post.return_value = mock_connector_response
        
        result = connector_service.find_connector_by_bpn("BPNL000000000001")
        
        mock_connector_http.do_post.assert_called_once_with(
            url="https://connector-discovery.example.com",
            headers={'Content-Type': 'application/json', "Authorization": "Bearer token"},
            json=["BPNL000000000001"]
        )
        
        assert result == [
            "https://edc1.example.com/api/v1/dsp",
            "https://edc2.example.com/api/v1/dsp"
        ]

    @mock.patch("tractusx_sdk.dataspace.services.discovery.discovery_finder_service.HttpTools")
    @mock.patch("tractusx_sdk.dataspace.services.discovery.connector_discovery_service.HttpTools")
    def test_find_connector_by_bpn_not_found(self, mock_connector_http, mock_finder_http, connector_service):
        """Test connector finding when BPN is not found."""
        # Mock discovery finder response
        mock_finder_response = mock.Mock()
        mock_finder_response.status_code = 200
        mock_finder_response.json.return_value = {
            "endpoints": [
                {
                    "type": "bpn",
                    "description": "Discovery Endpoint",
                    "endpointAddress": "https://connector-discovery.example.com",
                    "documentation": "https://example.com/docs",
                    "resourceId": "bpn"
                }
            ]
        }
        mock_finder_http.do_post.return_value = mock_finder_response
        
        mock_connector_response = mock.Mock()
        mock_connector_response.status_code = 200
        mock_connector_response.json.return_value = [
            {
                "bpn": "BPNL000000000002",
                "connectorEndpoint": ["https://edc3.example.com/api/v1/dsp"]
            }
        ]
        mock_connector_http.do_post.return_value = mock_connector_response
        
        result = connector_service.find_connector_by_bpn("BPNL000000000001")
        
        assert result is None

    @mock.patch("tractusx_sdk.dataspace.services.discovery.discovery_finder_service.HttpTools")
    @mock.patch("tractusx_sdk.dataspace.services.discovery.connector_discovery_service.HttpTools")
    def test_find_connector_by_bpn_http_error(self, mock_connector_http, mock_finder_http, connector_service):
        """Test connector finding with HTTP error."""
        # Mock discovery finder response
        mock_finder_response = mock.Mock()
        mock_finder_response.status_code = 200
        mock_finder_response.json.return_value = {
            "endpoints": [
                {
                    "type": "bpn",
                    "description": "Discovery Endpoint",
                    "endpointAddress": "https://connector-discovery.example.com",
                    "documentation": "https://example.com/docs",
                    "resourceId": "bpn"
                }
            ]
        }
        mock_finder_http.do_post.return_value = mock_finder_response
        
        mock_connector_response = mock.Mock()
        mock_connector_response.status_code = 500
        mock_connector_http.do_post.return_value = mock_connector_response
        
        with pytest.raises(Exception, match="response was not successful"):
            connector_service.find_connector_by_bpn("BPNL000000000001")

    def test_initialization_with_custom_parameters(self, mock_oauth):
        """Test service initialization with custom parameters."""
        mock_discovery_finder = DiscoveryFinderService(
            url="https://custom-discovery-finder.example.com",
            oauth=mock_oauth
        )
        
        with mock.patch.object(ConnectorDiscoveryService, '_get_or_update_discovery_url') as mock_update:
            mock_update.return_value = "https://custom-discovery.example.com"
            
            service = ConnectorDiscoveryService(
                oauth=mock_oauth,
                discovery_finder_service=mock_discovery_finder,
                connector_discovery_key="customKey",
                cache_timeout_seconds=3600  # 1 hour
            )
            
            assert service.connector_discovery_key == "customKey"
            assert service.cache_timeout_seconds == 3600
