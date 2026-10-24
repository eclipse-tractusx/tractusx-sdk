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
import time
from unittest import mock
from tractusx_sdk.industry.services.discovery.bpn_discovery_service import BpnDiscoveryService
from tractusx_sdk.dataspace.services.discovery.discovery_finder_service import DiscoveryFinderService

@pytest.fixture
def mock_oauth():
    mock_oauth = mock.Mock()
    mock_oauth.add_auth_header.side_effect = lambda headers: {**headers, "Authorization": "Bearer token"}
    return mock_oauth

@pytest.fixture
def mock_discovery_finder(mock_oauth):
    return DiscoveryFinderService(
        url="https://discovery.example.com",
        oauth=mock_oauth
    )

@pytest.fixture
def service(mock_oauth, mock_discovery_finder):
    return BpnDiscoveryService(
        oauth=mock_oauth,
        discovery_finder_service=mock_discovery_finder,
        cache_timeout_seconds=10
    )

def test_get_bpn_discovery_url_success(service, mock_discovery_finder):
    """Test successful BPN discovery URL retrieval using legacy method."""
    # Mock the discovery finder to return a URL
    with mock.patch.object(mock_discovery_finder, 'find_discovery_urls') as mock_find:
        mock_find.return_value = {"manufacturerPartId": "https://bpn.example.com/api/v1.0/administration/connectors/bpnDiscovery"}
        
        url = service.get_bpn_discovery_url("manufacturerPartId")
        
        assert url == "https://bpn.example.com/api/v1.0/administration/connectors/bpnDiscovery"

def test_get_bpn_discovery_url_not_found(service, mock_discovery_finder):
    """Test BPN discovery URL retrieval when endpoint not found."""
    # Mock the discovery finder to return empty dict
    with mock.patch.object(mock_discovery_finder, 'find_discovery_urls') as mock_find:
        mock_find.return_value = {}
        
        with pytest.raises(Exception, match="BPN Discovery endpoint not found"):
            service.get_bpn_discovery_url("manufacturerPartId")

@pytest.mark.parametrize("discovery_url", [None, ""])
def test_get_or_update_discovery_url_rejects_falsy_url(service, mock_discovery_finder, discovery_url):
    """A falsy discovery URL without a cache entry raises a meaningful error."""
    with mock.patch.object(service, "get_discovery_url", return_value=discovery_url):
        with pytest.raises(ValueError, match="Discovery finder returned no URL"):
            service._get_or_update_discovery_url("manufacturerPartId")

@mock.patch("tractusx_sdk.dataspace.services.discovery.discovery_finder_service.HttpTools")
@mock.patch("tractusx_sdk.industry.services.discovery.bpn_discovery_service.HttpTools")
def test_search_bpns_success(mock_bpn_http, mock_finder_http, service):
    """Test successful BPN search."""
    # Mock discovery finder response
    mock_finder_response = mock.Mock()
    mock_finder_response.status_code = 200
    mock_finder_response.json.return_value = {
        "endpoints": [
            {
                "type": "manufacturerPartId",
                "description": "BPN Discovery Endpoint",
                "endpointAddress": "https://bpn.example.com",
                "documentation": "https://example.com/docs",
                "resourceId": "manufacturerPartId"
            }
        ]
    }
    mock_finder_http.do_post.return_value = mock_finder_response
    
    # Mock BPN discovery HTTP response
    mock_bpn_response = mock.Mock()
    mock_bpn_response.status_code = 200
    mock_bpn_response.json.return_value = {
        "bpns": [
            {"value": "BPNL000000000001"},
            {"value": "BPNL000000000002"}
        ]
    }
    mock_bpn_http.do_post_with_session.return_value = mock_bpn_response
    
    result = service.search_bpns(keys=["part123", "part456"])
    
    expected_body = {
        "searchFilter": [
            {
                "type": "manufacturerPartId",
                "keys": ["part123", "part456"]
            }
        ]
    }
    
    mock_bpn_http.do_post_with_session.assert_called_once_with(
        url="https://bpn.example.com/api/v1.0/administration/connectors/bpnDiscovery/search",
        headers={'Content-Type': 'application/json', "Authorization": "Bearer token"},
        json=expected_body,
        session=service.session
    )
    
    assert result == {
        "bpns": [
            {"value": "BPNL000000000001"},
            {"value": "BPNL000000000002"}
        ]
    }

@mock.patch("tractusx_sdk.dataspace.services.discovery.discovery_finder_service.HttpTools")
@mock.patch("tractusx_sdk.industry.services.discovery.bpn_discovery_service.HttpTools")
def test_search_bpns_unauthorized(mock_bpn_http, mock_finder_http, service):
    """Test BPN search with unauthorized response."""
    # Mock discovery finder response
    mock_finder_response = mock.Mock()
    mock_finder_response.status_code = 200
    mock_finder_response.json.return_value = {
        "endpoints": [
            {
                "type": "manufacturerPartId",
                "description": "BPN Discovery Endpoint",
                "endpointAddress": "https://bpn.example.com",
                "documentation": "https://example.com/docs",
                "resourceId": "manufacturerPartId"
            }
        ]
    }
    mock_finder_http.do_post.return_value = mock_finder_response
    
    mock_bpn_response = mock.Mock()
    mock_bpn_response.status_code = 401
    mock_bpn_http.do_post_with_session.return_value = mock_bpn_response
    
    with pytest.raises(Exception, match="Unauthorized access"):
        service.search_bpns(keys=["part123"])

@mock.patch("tractusx_sdk.dataspace.services.discovery.discovery_finder_service.HttpTools")
@mock.patch("tractusx_sdk.industry.services.discovery.bpn_discovery_service.HttpTools")
def test_search_bpns_no_response(mock_bpn_http, mock_finder_http, service):
    """Test BPN search with no response."""
    # Mock discovery finder response
    mock_finder_response = mock.Mock()
    mock_finder_response.status_code = 200
    mock_finder_response.json.return_value = {
        "endpoints": [
            {
                "type": "manufacturerPartId",
                "description": "BPN Discovery Endpoint",
                "endpointAddress": "https://bpn.example.com",
                "documentation": "https://example.com/docs",
                "resourceId": "manufacturerPartId"
            }
        ]
    }
    mock_finder_http.do_post.return_value = mock_finder_response
    
    mock_bpn_http.do_post_with_session.return_value = None
    
    with pytest.raises(Exception, match="No response received"):
        service.search_bpns(keys=["part123"])

@mock.patch("tractusx_sdk.industry.services.discovery.bpn_discovery_service.op")
def test_find_bpns_success(mock_op, service):
    """Test successful BPN finding."""
    # Mock search_bpns method
    service.search_bpns = mock.Mock(return_value={
        "bpns": [
            {"value": "BPNL000000000001"},
            {"value": "BPNL000000000002"},
            {"value": "BPNL000000000001"}  # Duplicate
        ]
    })
    
    mock_op.extract_dict_values.return_value = ["BPNL000000000001", "BPNL000000000002", "BPNL000000000001"]
    
    result = service.find_bpns(keys=["part123", "part456"])
    
    service.search_bpns.assert_called_once_with(keys=["part123", "part456"], identifier_type="manufacturerPartId")
    mock_op.extract_dict_values.assert_called_once_with(
        array=[
            {"value": "BPNL000000000001"},
            {"value": "BPNL000000000002"},
            {"value": "BPNL000000000001"}
        ],
        key="value"
    )
    
    # Should return unique BPNs
    assert set(result) == {"BPNL000000000001", "BPNL000000000002"}

def test_find_bpns_no_results(service):
    """Test BPN finding with no results."""
    service.search_bpns = mock.Mock(return_value={"bpns": []})
    
    result = service.find_bpns(keys=["nonexistent"])
    
    assert result is None

@mock.patch("tractusx_sdk.dataspace.services.discovery.discovery_finder_service.HttpTools")
@mock.patch("tractusx_sdk.industry.services.discovery.bpn_discovery_service.HttpTools")
def test_set_identifier_success(mock_bpn_http, mock_finder_http, service):
    """Test successful identifier setting."""
    # Mock discovery finder response
    mock_finder_response = mock.Mock()
    mock_finder_response.status_code = 200
    mock_finder_response.json.return_value = {
        "endpoints": [
            {
                "type": "manufacturerPartId",
                "description": "BPN Discovery Endpoint",
                "endpointAddress": "https://bpn.example.com",
                "documentation": "https://example.com/docs",
                "resourceId": "manufacturerPartId"
            }
        ]
    }
    mock_finder_http.do_post.return_value = mock_finder_response
    
    mock_bpn_response = mock.Mock()
    mock_bpn_response.status_code = 201
    mock_bpn_response.json.return_value = {"resourceId": "12345", "key": "part123"}
    mock_bpn_http.do_post_with_session.return_value = mock_bpn_response
    
    result = service.set_identifier("part123")
    
    expected_body = {
        "type": "manufacturerPartId",
        "key": "part123"
    }
    
    mock_bpn_http.do_post_with_session.assert_called_once_with(
        url="https://bpn.example.com/api/v1.0/administration/connectors/bpnDiscovery",
        headers={'Content-Type': 'application/json', "Authorization": "Bearer token"},
        json=expected_body,
        session=service.session
    )
    
    assert result == {"resourceId": "12345", "key": "part123"}

@mock.patch("tractusx_sdk.dataspace.services.discovery.discovery_finder_service.HttpTools")
@mock.patch("tractusx_sdk.industry.services.discovery.bpn_discovery_service.HttpTools")
def test_set_multiple_identifiers_success(mock_bpn_http, mock_finder_http, service):
    """Test successful multiple identifiers setting."""
    # Mock discovery finder response
    mock_finder_response = mock.Mock()
    mock_finder_response.status_code = 200
    mock_finder_response.json.return_value = {
        "endpoints": [
            {
                "type": "manufacturerPartId",
                "description": "BPN Discovery Endpoint",
                "endpointAddress": "https://bpn.example.com",
                "documentation": "https://example.com/docs",
                "resourceId": "manufacturerPartId"
            }
        ]
    }
    mock_finder_http.do_post.return_value = mock_finder_response
    
    mock_bpn_response = mock.Mock()
    mock_bpn_response.status_code = 201
    mock_bpn_response.json.return_value = [
        {"resourceId": "12345", "key": "part123"},
        {"resourceId": "12346", "key": "part456"}
    ]
    mock_bpn_http.do_post_with_session.return_value = mock_bpn_response
    
    result = service.set_multiple_identifiers(["part123", "part456"])
    
    expected_body = [
        {"type": "manufacturerPartId", "key": "part123"},
        {"type": "manufacturerPartId", "key": "part456"}
    ]
    
    mock_bpn_http.do_post_with_session.assert_called_once_with(
        url="https://bpn.example.com/api/v1.0/administration/connectors/bpnDiscovery/batch",
        headers={'Content-Type': 'application/json', "Authorization": "Bearer token"},
        json=expected_body,
        session=service.session
    )
    
    assert len(result) == 2

@mock.patch("tractusx_sdk.dataspace.services.discovery.discovery_finder_service.HttpTools")
@mock.patch("tractusx_sdk.industry.services.discovery.bpn_discovery_service.HttpTools")
def test_delete_bpn_identifier_success(mock_bpn_http, mock_finder_http, service):
    """Test successful BPN identifier deletion."""
    # Mock discovery finder response
    mock_finder_response = mock.Mock()
    mock_finder_response.status_code = 200
    mock_finder_response.json.return_value = {
        "endpoints": [
            {
                "type": "manufacturerPartId",
                "description": "BPN Discovery Endpoint",
                "endpointAddress": "https://bpn.example.com",
                "documentation": "https://example.com/docs",
                "resourceId": "manufacturerPartId"
            }
        ]
    }
    mock_finder_http.do_post.return_value = mock_finder_response
    
    mock_bpn_response = mock.Mock()
    mock_bpn_response.status_code = 204
    mock_bpn_http.do_delete_with_session.return_value = mock_bpn_response
    
    # Should not raise an exception
    service.delete_bpn_identifier_by_id("12345")
    
    mock_bpn_http.do_delete_with_session.assert_called_once_with(
        url="https://bpn.example.com/api/v1.0/administration/connectors/bpnDiscovery/12345",
        headers={'Content-Type': 'application/json', "Authorization": "Bearer token"},
        session=service.session
    )

@mock.patch("tractusx_sdk.dataspace.services.discovery.discovery_finder_service.HttpTools")
def test_cache_functionality(mock_http, service, mock_oauth):
    """Test cache functionality with expired entries."""
    # Mock discovery finder response
    mock_response = mock.Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "endpoints": [
            {
                "type": "manufacturerPartId",
                "description": "BPN Discovery Endpoint",
                "endpointAddress": "https://new-bpn.example.com",
                "documentation": "https://example.com/docs",
                "resourceId": "manufacturerPartId"
            }
        ]
    }
    mock_http.do_post.return_value = mock_response
    
    # Set up initial cache entry that's expired (using discovery_cache)
    old_timestamp = time.time() - 20  # 20 seconds ago, cache timeout is 10 seconds
    service.discovery_cache = {
        "manufacturerPartId": {
            "url": "https://old-bpn.example.com/api/v1.0/administration/connectors/bpnDiscovery",
            "timestamp": old_timestamp
        }
    }
    
    url = service._get_or_update_discovery_url()
    
    # Should call the discovery finder service to get new URL
    assert url == "https://new-bpn.example.com/api/v1.0/administration/connectors/bpnDiscovery"
    # Cache should be updated
    assert service.discovery_cache["manufacturerPartId"]["url"] == "https://new-bpn.example.com/api/v1.0/administration/connectors/bpnDiscovery"

@mock.patch("tractusx_sdk.dataspace.services.discovery.discovery_finder_service.HttpTools")
def test_cache_valid_entry(mock_http, service):
    """Test cache functionality with valid entries."""
    # Mock discovery finder response (should not be called)
    mock_response = mock.Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "endpoints": [
            {
                "type": "manufacturerPartId",
                "description": "BPN Discovery Endpoint",
                "endpointAddress": "https://new-bpn.example.com",
                "documentation": "https://example.com/docs",
                "resourceId": "manufacturerPartId"
            }
        ]
    }
    mock_http.do_post.return_value = mock_response
    
    # Set up valid cache entry (using discovery_cache)
    current_timestamp = time.time()
    service.discovery_cache = {
        "manufacturerPartId": {
            "url": "https://cached-bpn.example.com/api/v1.0/administration/connectors/bpnDiscovery",
            "timestamp": current_timestamp
        }
    }
    
    url = service._get_or_update_discovery_url()
    
    # Should use cached URL without calling discovery finder
    assert url == "https://cached-bpn.example.com/api/v1.0/administration/connectors/bpnDiscovery"
    mock_http.do_post.assert_not_called()

@mock.patch("tractusx_sdk.dataspace.services.discovery.discovery_finder_service.HttpTools")
def test_cache_safety_mechanism_with_existing_cache(mock_http, service, mock_oauth):
    """Test safety mechanism when refresh fails but cached URL exists."""
    # Mock discovery finder to simulate failure
    mock_http.do_post.side_effect = ConnectionError("Connection timeout")
    
    # Set up expired cache entry (using discovery_cache)
    old_timestamp = time.time() - 20  # 20 seconds ago, cache timeout is 10 seconds
    service.discovery_cache = {
        "manufacturerPartId": {
            "url": "https://cached-bpn.example.com/api/v1.0/administration/connectors/bpnDiscovery",
            "timestamp": old_timestamp
        }
    }
    
    # Should return cached URL despite refresh failure
    url = service._get_or_update_discovery_url()
    
    # Should have attempted to refresh
    mock_http.do_post.assert_called_once()
    # Should return the cached URL as fallback
    assert url == "https://cached-bpn.example.com/api/v1.0/administration/connectors/bpnDiscovery"
    # Cache should still contain the old entry (not deleted)
    assert "manufacturerPartId" in service.discovery_cache
    assert service.discovery_cache["manufacturerPartId"]["url"] == "https://cached-bpn.example.com/api/v1.0/administration/connectors/bpnDiscovery"

@mock.patch("tractusx_sdk.dataspace.services.discovery.discovery_finder_service.HttpTools")
def test_cache_safety_mechanism_no_existing_cache(mock_http, service):
    """Test safety mechanism when refresh fails and no cached URL exists."""
    # Mock discovery finder to simulate failure
    mock_http.do_post.side_effect = ConnectionError("Connection timeout")
    
    # No existing cache (using discovery_cache)
    service.discovery_cache = {}
    
    # Should raise the original exception since no fallback exists
    with pytest.raises(ConnectionError, match="Connection timeout"):
        service._get_or_update_discovery_url()
    
    # Should have attempted to get URL
    mock_http.do_post.assert_called_once()
    # Cache should remain empty
    assert "manufacturerPartId" not in service.discovery_cache

@mock.patch("tractusx_sdk.dataspace.services.discovery.discovery_finder_service.HttpTools")
def test_cache_successful_refresh_after_failure(mock_http, service):
    """Test that cache is properly updated when refresh succeeds after previous failure."""
    # Set up expired cache entry (using discovery_cache)
    old_timestamp = time.time() - 20
    service.discovery_cache = {
        "manufacturerPartId": {
            "url": "https://old-cached-bpn.example.com/api/v1.0/administration/connectors/bpnDiscovery",
            "timestamp": old_timestamp
        }
    }
    
    # First call fails, should return cached URL
    mock_http.do_post.side_effect = ConnectionError("Connection timeout")
    url1 = service._get_or_update_discovery_url()
    assert url1 == "https://old-cached-bpn.example.com/api/v1.0/administration/connectors/bpnDiscovery"
    
    # Second call succeeds, should update cache
    mock_response = mock.Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "endpoints": [
            {
                "type": "manufacturerPartId",
                "description": "BPN Discovery Endpoint",
                "endpointAddress": "https://new-refreshed-bpn.example.com",
                "documentation": "https://example.com/docs",
                "resourceId": "manufacturerPartId"
            }
        ]
    }
    mock_http.do_post.side_effect = None
    mock_http.do_post.return_value = mock_response
    
    # Force cache expiration for next call
    service.discovery_cache["manufacturerPartId"]["timestamp"] = time.time() - 30
    
    url2 = service._get_or_update_discovery_url()
    assert url2 == "https://new-refreshed-bpn.example.com/api/v1.0/administration/connectors/bpnDiscovery"
    
    # Cache should be updated with new URL and timestamp
    assert service.discovery_cache["manufacturerPartId"]["url"] == "https://new-refreshed-bpn.example.com/api/v1.0/administration/connectors/bpnDiscovery"
    assert service.discovery_cache["manufacturerPartId"]["timestamp"] > old_timestamp
