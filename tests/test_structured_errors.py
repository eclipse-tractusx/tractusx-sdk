#################################################################################
# Eclipse Tractus-X - Software Development KIT
#
# Copyright (c) 2026 LKS Next
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

"""Failures are reported as SDK errors that callers can catch by type, not as bare ``Exception``s."""

from unittest import mock

import pytest

from tractusx_sdk.dataspace.managers.connection.memory.memory_connection_manager import MemoryConnectionManager
from tractusx_sdk.dataspace.services.discovery.connector_discovery_service import ConnectorDiscoveryService
from tractusx_sdk.dataspace.services.discovery.discovery_finder_service import DiscoveryFinderService
from tractusx_sdk.extensions.semantics.schema_to_context_translator import SammSchemaContextTranslator
from tractusx_sdk.exceptions import (
    ConnectionManagerError,
    DiscoveryEndpointNotFoundError,
    DiscoveryError,
    DiscoveryUnauthorizedError,
    InvalidSemanticIdError,
    SchemaNotFoundError,
    SchemaTranslationError,
    TractusXSDKError,
)
from tractusx_sdk.industry.services.discovery.bpn_discovery_service import BpnDiscoveryService, _ensure_response


def _response(status_code):
    return mock.Mock(status_code=status_code)


class TestBpnDiscoveryResponses:

    def test_the_expected_response_is_returned(self):
        response = _response(201)
        assert _ensure_response(response, 201, "failed") is response

    def test_no_response(self):
        with pytest.raises(DiscoveryError, match="No response received"):
            _ensure_response(None, 200, "failed")

    def test_unauthorized_is_told_apart(self):
        with pytest.raises(DiscoveryUnauthorizedError, match="Unauthorized access"):
            _ensure_response(_response(401), 200, "failed")

    @pytest.mark.parametrize("status", [200, 404, 500])
    def test_any_other_status_carries_the_given_message(self, status):
        with pytest.raises(DiscoveryError, match="could not create") as raised:
            _ensure_response(_response(status), 201, "could not create it")
        assert not isinstance(raised.value, DiscoveryUnauthorizedError)

    def test_missing_endpoint(self):
        finder = mock.Mock()
        finder.find_discovery_urls.return_value = {}
        service = BpnDiscoveryService(oauth=mock.Mock(), discovery_finder_service=finder)
        with pytest.raises(DiscoveryEndpointNotFoundError, match="BPN Discovery endpoint not found") as raised:
            service.get_bpn_discovery_url("manufacturerPartId")
        assert isinstance(raised.value, DiscoveryError)
        assert isinstance(raised.value, TractusXSDKError)


class TestDataspaceDiscovery:

    def test_unsuccessful_finder_response(self):
        oauth = mock.Mock()
        oauth.add_auth_header.side_effect = lambda headers: headers
        finder = DiscoveryFinderService(url="https://discovery.example.com", oauth=oauth)
        with mock.patch("tractusx_sdk.dataspace.services.discovery.discovery_finder_service.HttpTools") as http:
            http.do_post.return_value = _response(500)
            with pytest.raises(DiscoveryError, match="response was not successful"):
                finder.find_discovery_urls(keys=["bpn"])

    def test_finder_without_endpoints(self):
        oauth = mock.Mock()
        oauth.add_auth_header.side_effect = lambda headers: headers
        finder = DiscoveryFinderService(url="https://discovery.example.com", oauth=oauth)
        with mock.patch("tractusx_sdk.dataspace.services.discovery.discovery_finder_service.HttpTools") as http:
            http.do_post.return_value = mock.Mock(status_code=200, json=mock.Mock(return_value={"endpoints": []}))
            with pytest.raises(DiscoveryEndpointNotFoundError, match="No endpoints were found"):
                finder.find_discovery_urls(keys=["bpn"])

    def test_connector_discovery_missing_endpoint(self):
        finder = mock.Mock()
        finder.find_discovery_urls.return_value = {}
        service = ConnectorDiscoveryService(oauth=mock.Mock(), discovery_finder_service=finder)
        with pytest.raises(DiscoveryEndpointNotFoundError, match="Connector Discovery endpoint not found"):
            service.get_connector_discovery_url()


class TestConnectionManagerErrors:

    def test_missing_transfer_id_is_a_connection_manager_error(self):
        manager = MemoryConnectionManager()
        with pytest.raises(ConnectionManagerError, match="transfer id key was not found") as raised:
            manager.add_connection("bpn", "address", "query", "policy", connection_entry={})
        assert isinstance(raised.value, TractusXSDKError)


class TestTranslatorErrors:

    @pytest.fixture
    def translator(self):
        return SammSchemaContextTranslator()

    def test_invalid_semantic_id_keeps_the_cause(self, translator):
        with pytest.raises(SchemaTranslationError, match="create flattened jsonld schema") as raised:
            translator.schema_to_jsonld("invalid_semantic_id", {"type": "string"})
        assert isinstance(raised.value.__cause__, InvalidSemanticIdError)
        assert isinstance(raised.value, TractusXSDKError)

    def test_a_missing_schema_keeps_the_cause_of_the_failed_lookup(self, translator):
        lookup_failure = ConnectionError("no network")
        with mock.patch.object(translator, "_find_schema", side_effect=lookup_failure):
            with pytest.raises(SchemaTranslationError) as raised:
                translator.schema_to_jsonld("urn:samm:io.catenax.pcf:7.0.0#Pcf")
        missing = raised.value.__cause__
        assert isinstance(missing, SchemaNotFoundError)
        assert "urn:samm:io.catenax.pcf:7.0.0#Pcf" in str(missing)
        assert missing.__cause__ is lookup_failure

    def test_the_public_fetch_still_returns_none_on_failure(self, translator):
        with mock.patch.object(translator, "_find_schema", side_effect=ConnectionError("no network")):
            assert translator.fetch_schema_from_semantic_id("urn:samm:io.catenax.pcf:7.0.0#Pcf") is None
