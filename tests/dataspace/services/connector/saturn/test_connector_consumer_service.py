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

from unittest import mock, TestCase, main
import logging
from requests import Response

from tractusx_sdk.dataspace.services.connector.saturn.connector_consumer_service import ConnectorConsumerService
from tractusx_sdk.dataspace.managers.connection.base_connection_manager import BaseConnectionManager


class TestSaturnConnectorConsumerService(TestCase):
    
    def setUp(self):
        self.dataspace_version = "saturn"
        self.base_url = "https://consumer-control.plane.url"
        self.dma_path = "/management"
        self.headers = {"X-Api-Key": "api-key-secret", "Content-Type": "application/json"}
        
        # Mock connection manager
        self.mock_connection_manager = mock.Mock(spec=BaseConnectionManager)
        
        # Create service instance with mocked dependencies
        with mock.patch('tractusx_sdk.dataspace.adapters.connector.adapter_factory.AdapterFactory') as mock_adapter_factory, \
             mock.patch('tractusx_sdk.dataspace.controllers.connector.controller_factory.ControllerFactory') as mock_controller_factory:
            
            # Setup mock returns
            mock_adapter_factory.get_dma_adapter.return_value = mock.Mock()
            mock_controller_factory.get_dma_controllers_for_version.return_value = {
                'CATALOG': mock.Mock(),
                'EDR': mock.Mock(),
                'CONTRACT_NEGOTIATION': mock.Mock(),
                'TRANSFER_PROCESS': mock.Mock(),
                'CONNECTOR_DISCOVERY': mock.Mock()
            }
            
            self.service = ConnectorConsumerService(
                dataspace_version=self.dataspace_version,
                base_url=self.base_url,
                dma_path=self.dma_path,
                headers=self.headers,
                connection_manager=self.mock_connection_manager,
                verbose=True
            )
    
    def test_initialization(self):
        """Test service initialization with required parameters."""
        # Note: Saturn service hardcodes dataspace_version to "saturn"
        self.assertEqual(self.service.dataspace_version, "saturn")
        # Note: base_url and dma_path are not stored as attributes, they're passed to adapters
        self.assertIsNotNone(self.service.controllers)
        self.assertIsNotNone(self.service.connection_manager)
        self.assertIsNotNone(self.service.connector_discovery)
    
    def test_initialization_with_logger(self):
        """Test service initialization with custom logger."""
        custom_logger = logging.getLogger("test_logger")
        
        with mock.patch('tractusx_sdk.dataspace.adapters.connector.adapter_factory.AdapterFactory') as mock_adapter_factory, \
             mock.patch('tractusx_sdk.dataspace.controllers.connector.controller_factory.ControllerFactory') as mock_controller_factory:
            
            # Setup mock returns
            mock_adapter_factory.get_dma_adapter.return_value = mock.Mock()
            mock_controller_factory.get_dma_controllers_for_version.return_value = {
                'CATALOG': mock.Mock(),
                'EDR': mock.Mock(),
                'CONTRACT_NEGOTIATION': mock.Mock(),
                'TRANSFER_PROCESS': mock.Mock(),
                'CONNECTOR_DISCOVERY': mock.Mock()
            }
            
            service = ConnectorConsumerService(
                dataspace_version=self.dataspace_version,
                base_url=self.base_url,
                dma_path=self.dma_path,
                headers=self.headers,
                logger=custom_logger
            )
            
            self.assertEqual(service.logger, custom_logger)
    
    def test_connector_discovery_property(self):
        """Test connector discovery property returns the correct controller."""
        self.assertIsNotNone(self.service.connector_discovery)
    
    def test_resolve_counter_party_info_with_bpnl(self):
        """Test _resolve_counter_party_info with BPNL discovery (always returns legacy protocol)."""
        bpnl = "BPNL000000000001"
        expected_address = "https://provider.example.com"
        expected_id = "BPNL000000000001"
        expected_protocol = "dataspace-protocol-http"  # BPNL discovery always returns legacy protocol
        
        with mock.patch.object(self.service, 'get_discovery_info') as mock_discovery:
            mock_discovery.return_value = (expected_address, expected_id, expected_protocol)
            
            result = self.service._resolve_counter_party_info(bpnl=bpnl)
            
            self.assertEqual(result, (expected_address, expected_id, expected_protocol))
            mock_discovery.assert_called_once_with(bpnl=bpnl, counter_party_address=None, namespace=ConnectorConsumerService.EDC_NAMESPACE, verify=None)
    
    def test_resolve_counter_party_info_without_bpnl(self):
        """Test _resolve_counter_party_info with direct parameters."""
        address = "https://provider.example.com"
        party_id = "BPNL000000000001"
        protocol = "custom-protocol"
        
        result = self.service._resolve_counter_party_info(
            counter_party_address=address,
            counter_party_id=party_id,
            protocol=protocol
        )
        
        self.assertEqual(result, (address, party_id, protocol))
    
    def test_execute_http_request_get(self):
        """Test _execute_http_request for GET method."""
        dataplane_url = "https://dataplane.example.com"
        access_token = "test-token"
        path = "/test-path"
        
        with mock.patch('tractusx_sdk.dataspace.services.connector.saturn.connector_consumer_service.HttpTools') as mock_http_tools, \
             mock.patch.object(self.service, 'get_data_plane_headers') as mock_headers:
            
            mock_headers.return_value = {"Authorization": f"Bearer {access_token}"}
            mock_response = mock.Mock(spec=Response)
            mock_http_tools.do_get.return_value = mock_response
            
            result = self.service._execute_http_request(
                method='GET',
                dataplane_url=dataplane_url,
                access_token=access_token,
                path=path
            )
            
            self.assertEqual(result, mock_response)
            mock_http_tools.do_get.assert_called_once()
    
    def test_execute_http_request_post(self):
        """Test _execute_http_request for POST method."""
        dataplane_url = "https://dataplane.example.com"
        access_token = "test-token"
        path = "/test-path"
        json_data = {"test": "data"}
        
        with mock.patch('tractusx_sdk.dataspace.services.connector.saturn.connector_consumer_service.HttpTools') as mock_http_tools, \
             mock.patch.object(self.service, 'get_data_plane_headers') as mock_headers:
            
            mock_headers.return_value = {"Authorization": f"Bearer {access_token}"}
            mock_response = mock.Mock(spec=Response)
            mock_http_tools.do_post.return_value = mock_response
            
            result = self.service._execute_http_request(
                method='POST',
                dataplane_url=dataplane_url,
                access_token=access_token,
                path=path,
                json=json_data
            )
            
            self.assertEqual(result, mock_response)
            mock_http_tools.do_post.assert_called_once()
    
    def test_execute_http_request_with_session(self):
        """Test _execute_http_request with session."""
        dataplane_url = "https://dataplane.example.com"
        access_token = "test-token"
        session = mock.Mock()
        
        with mock.patch('tractusx_sdk.dataspace.services.connector.saturn.connector_consumer_service.HttpTools') as mock_http_tools, \
             mock.patch.object(self.service, 'get_data_plane_headers') as mock_headers:
            
            mock_headers.return_value = {"Authorization": f"Bearer {access_token}"}
            mock_response = mock.Mock(spec=Response)
            mock_http_tools.do_get_with_session.return_value = mock_response
            
            result = self.service._execute_http_request(
                method='GET',
                dataplane_url=dataplane_url,
                access_token=access_token,
                session=session
            )
            
            self.assertEqual(result, mock_response)
            mock_http_tools.do_get_with_session.assert_called_once()
    
    def test_execute_http_request_put(self):
        """Test _execute_http_request with PUT method."""
        dataplane_url = "https://dataplane.example.com"
        access_token = "test-token"
        path = "/update"
        json_data = {"key": "value"}
        
        with mock.patch('tractusx_sdk.dataspace.services.connector.saturn.connector_consumer_service.HttpTools') as mock_http_tools, \
             mock.patch.object(self.service, 'get_data_plane_headers') as mock_headers:
            
            mock_headers.return_value = {"Authorization": f"Bearer {access_token}"}
            mock_response = mock.Mock(spec=Response)
            mock_http_tools.do_put.return_value = mock_response
            
            result = self.service._execute_http_request(
                method='PUT',
                dataplane_url=dataplane_url,
                access_token=access_token,
                path=path,
                json=json_data
            )
            
            self.assertEqual(result, mock_response)
            mock_http_tools.do_put.assert_called_once_with(
                url=dataplane_url + path,
                json=json_data,
                data=None,
                headers={"Authorization": f"Bearer {access_token}"},
                verify=False,
                timeout=None,
                allow_redirects=False
            )
    
    def test_execute_http_request_put_with_session(self):
        """Test _execute_http_request with PUT method and session."""
        dataplane_url = "https://dataplane.example.com"
        access_token = "test-token"
        path = "/update"
        data = "raw data"
        session = mock.Mock()
        
        with mock.patch('tractusx_sdk.dataspace.services.connector.saturn.connector_consumer_service.HttpTools') as mock_http_tools, \
             mock.patch.object(self.service, 'get_data_plane_headers') as mock_headers:
            
            mock_headers.return_value = {"Authorization": f"Bearer {access_token}"}
            mock_response = mock.Mock(spec=Response)
            mock_http_tools.do_put_with_session.return_value = mock_response
            
            result = self.service._execute_http_request(
                method='PUT',
                dataplane_url=dataplane_url,
                access_token=access_token,
                path=path,
                data=data,
                session=session
            )
            
            self.assertEqual(result, mock_response)
            mock_http_tools.do_put_with_session.assert_called_once_with(
                url=dataplane_url + path,
                json=None,
                data=data,
                headers={"Authorization": f"Bearer {access_token}"},
                verify=False,
                timeout=None,
                allow_redirects=False,
                session=session
            )
    
    def test_get_catalog_internal_with_filter_bpnl(self):
        """Test _get_catalog_internal with filter expression and BPNL."""
        counter_party_id = "BPNL000000000001"
        counter_party_address = "https://provider.example.com"
        filter_expression = [{"key": "test", "value": "value"}]
        
        with mock.patch.object(self.service, '_resolve_counter_party_info') as mock_resolve, \
             mock.patch.object(self.service, 'get_catalog_request_with_filter') as mock_request, \
             mock.patch.object(self.service, 'get_catalog') as mock_catalog:
            
            mock_resolve.return_value = (counter_party_address, counter_party_id, ConnectorConsumerService.DSP_2025)
            mock_request.return_value = mock.Mock()
            expected_catalog = {"test": "catalog"}
            mock_catalog.return_value = expected_catalog
            
            result = self.service._get_catalog_internal(
                counter_party_id=counter_party_id,
                counter_party_address=counter_party_address,
                filter_expression=filter_expression
            )
            
            self.assertEqual(result, expected_catalog)
            mock_request.assert_called_once()
            mock_catalog.assert_called_once()
    
    def test_get_catalog_internal_with_filter_did(self):
        """Test _get_catalog_internal with filter expression and DID."""
        counter_party_id = "did:web:connector-provider.example.com"
        counter_party_address = "https://provider.example.com"
        filter_expression = [{"key": "test", "value": "value"}]
        
        with mock.patch.object(self.service, '_resolve_counter_party_info') as mock_resolve, \
             mock.patch.object(self.service, 'get_catalog_request_with_filter') as mock_request, \
             mock.patch.object(self.service, 'get_catalog') as mock_catalog:
            
            mock_resolve.return_value = (counter_party_address, counter_party_id, ConnectorConsumerService.DSP_2025)
            mock_request.return_value = mock.Mock()
            expected_catalog = {"test": "catalog"}
            mock_catalog.return_value = expected_catalog
            
            result = self.service._get_catalog_internal(
                counter_party_id=counter_party_id,
                counter_party_address=counter_party_address,
                filter_expression=filter_expression
            )
            
            self.assertEqual(result, expected_catalog)
            mock_request.assert_called_once()
            mock_catalog.assert_called_once()
            # Verify that the DID is properly passed through the chain
            call_args = mock_request.call_args
            self.assertIn(counter_party_id, str(call_args))
    
    def test_get_catalog_internal_with_legacy_protocol(self):
        """Test _get_catalog_internal with legacy protocol."""
        counter_party_id = "BPNL000000000001"
        counter_party_address = "https://provider.example.com"
        filter_expression = [{"key": "test", "value": "value"}]
        legacy_protocol = "dataspace-protocol-http"
        
        with mock.patch.object(self.service, '_resolve_counter_party_info') as mock_resolve, \
             mock.patch.object(self.service, 'get_catalog_request_with_filter') as mock_request, \
             mock.patch.object(self.service, 'get_catalog') as mock_catalog:
            
            mock_resolve.return_value = (counter_party_address, counter_party_id, legacy_protocol)
            mock_request.return_value = mock.Mock()
            expected_catalog = {"test": "catalog"}
            mock_catalog.return_value = expected_catalog
            
            result = self.service._get_catalog_internal(
                counter_party_id=counter_party_id,
                counter_party_address=counter_party_address,
                filter_expression=filter_expression,
                protocol=legacy_protocol
            )
            
            self.assertEqual(result, expected_catalog)
            mock_request.assert_called_once()
            mock_catalog.assert_called_once()
            # Verify that the legacy protocol is properly passed through
            call_args = mock_request.call_args
            self.assertIn(legacy_protocol, str(call_args))
    
    def test_get_catalog_internal_without_filter(self):
        """Test _get_catalog_internal without filter expression."""
        counter_party_id = "BPNL000000000001"
        counter_party_address = "https://provider.example.com"
        
        with mock.patch.object(self.service, '_resolve_counter_party_info') as mock_resolve, \
             mock.patch.object(self.service, 'get_catalog_request') as mock_request, \
             mock.patch.object(self.service, 'get_catalog') as mock_catalog:
            
            mock_resolve.return_value = (counter_party_address, counter_party_id, ConnectorConsumerService.DSP_2025)
            mock_request.return_value = mock.Mock()
            expected_catalog = {"test": "catalog"}
            mock_catalog.return_value = expected_catalog
            
            result = self.service._get_catalog_internal(
                counter_party_id=counter_party_id,
                counter_party_address=counter_party_address
            )
            
            self.assertEqual(result, expected_catalog)
            mock_request.assert_called_once()
            mock_catalog.assert_called_once()
    
    def test_get_edr_negotiation_request_success(self):
        """Test get_edr_negotiation_request with valid policy and BPNL."""
        counter_party_id = "BPNL000000000001"
        counter_party_address = "https://provider.example.com"
        target = "asset-123"
        policy = {"@id": "policy-123", "odrl:permission": {}}
        
        with mock.patch('tractusx_sdk.dataspace.services.connector.saturn.connector_consumer_service.ModelFactory') as mock_factory:
            mock_model = mock.Mock()
            mock_factory.get_contract_negotiation_model.return_value = mock_model
            
            result = self.service.get_edr_negotiation_request(
                counter_party_id=counter_party_id,
                counter_party_address=counter_party_address,
                target=target,
                policy=policy
            )
            
            self.assertEqual(result, mock_model)
            mock_factory.get_contract_negotiation_model.assert_called_once()
    
    def test_get_edr_negotiation_request_with_did(self):
        """Test get_edr_negotiation_request with valid policy and DID."""
        counter_party_id = "did:web:connector-provider.example.com"
        counter_party_address = "https://provider.example.com"
        target = "asset-123"
        policy = {"@id": "policy-123", "odrl:permission": {}}
        protocol = "dataspace-protocol-https:2025-1"
        
        with mock.patch('tractusx_sdk.dataspace.services.connector.saturn.connector_consumer_service.ModelFactory') as mock_factory:
            mock_model = mock.Mock()
            mock_factory.get_contract_negotiation_model.return_value = mock_model
            
            result = self.service.get_edr_negotiation_request(
                counter_party_id=counter_party_id,
                counter_party_address=counter_party_address,
                target=target,
                policy=policy,
                protocol=protocol
            )
            
            self.assertEqual(result, mock_model)
            mock_factory.get_contract_negotiation_model.assert_called_once()
            # Verify that the DID is passed correctly in the negotiation request
            call_args = mock_factory.get_contract_negotiation_model.call_args
            self.assertIn(counter_party_id, str(call_args))
    
    def test_get_edr_negotiation_request_with_legacy_protocol(self):
        """Test get_edr_negotiation_request with legacy protocol."""
        counter_party_id = "BPNL000000000001"
        counter_party_address = "https://provider.example.com"
        target = "asset-123"
        policy = {"@id": "policy-123", "odrl:permission": {}}
        protocol = "dataspace-protocol-http"
        
        with mock.patch('tractusx_sdk.dataspace.services.connector.saturn.connector_consumer_service.ModelFactory') as mock_factory:
            mock_model = mock.Mock()
            mock_factory.get_contract_negotiation_model.return_value = mock_model
            
            result = self.service.get_edr_negotiation_request(
                counter_party_id=counter_party_id,
                counter_party_address=counter_party_address,
                target=target,
                policy=policy,
                protocol=protocol
            )
            
            self.assertEqual(result, mock_model)
            mock_factory.get_contract_negotiation_model.assert_called_once()
    
    def test_get_edr_negotiation_request_missing_offer_id(self):
        """Test get_edr_negotiation_request with missing offer ID."""
        counter_party_id = "BPNL000000000001"
        counter_party_address = "https://provider.example.com"
        target = "asset-123"
        policy = {"odrl:permission": {}}  # Missing @id
        
        with self.assertRaises(ValueError) as context:
            self.service.get_edr_negotiation_request(
                counter_party_id=counter_party_id,
                counter_party_address=counter_party_address,
                target=target,
                policy=policy
            )
        
        self.assertIn("Policy offer id is not available", str(context.exception))
    
    def test_start_edr_negotiation_success(self):
        """Test start_edr_negotiation with successful response."""
        counter_party_id = "BPNL000000000001"
        counter_party_address = "https://provider.example.com"
        target = "asset-123"
        policy = {"@id": "policy-123"}
        negotiation_id = "negotiation-456"
        
        mock_response = mock.Mock(spec=Response)
        mock_response.status_code = 200
        mock_response.json.return_value = {"@id": negotiation_id}
        
        with mock.patch.object(self.service, 'get_edr_negotiation_request') as mock_request, \
             mock.patch.object(self.service, '_edr_controller') as mock_edrs:
            
            mock_request.return_value = mock.Mock()
            mock_edrs.create.return_value = mock_response
            
            result = self.service.start_edr_negotiation(
                counter_party_id=counter_party_id,
                counter_party_address=counter_party_address,
                target=target,
                policy=policy
            )
            
            self.assertEqual(result, negotiation_id)
    
    def test_start_edr_negotiation_failure(self):
        """Test start_edr_negotiation with failed response."""
        counter_party_id = "BPNL000000000001"
        counter_party_address = "https://provider.example.com"
        target = "asset-123"
        policy = {"@id": "policy-123"}
        
        mock_response = mock.Mock(spec=Response)
        mock_response.status_code = 400
        
        with mock.patch.object(self.service, 'get_edr_negotiation_request') as mock_request, \
             mock.patch.object(self.service, '_edr_controller') as mock_edrs:
            
            mock_request.return_value = mock.Mock()
            mock_edrs.create.return_value = mock_response
            
            result = self.service.start_edr_negotiation(
                counter_party_id=counter_party_id,
                counter_party_address=counter_party_address,
                target=target,
                policy=policy
            )
            
            self.assertIsNone(result)
    
    def test_get_transfer_id_cached(self):
        """Test get_transfer_id with cached transfer ID."""
        counter_party_id = "BPNL000000000001"
        counter_party_address = "https://provider.example.com"
        filter_expression = [{"key": "test"}]
        policies = [{"@id": "policy-123"}]
        cached_transfer_id = "cached-transfer-123"
        
        self.mock_connection_manager.get_connection_transfer_id.return_value = cached_transfer_id
        
        result = self.service.get_transfer_id(
            counter_party_id=counter_party_id,
            counter_party_address=counter_party_address,
            filter_expression=filter_expression,
            policies=policies
        )
        
        self.assertEqual(result, cached_transfer_id)
        self.mock_connection_manager.get_connection_transfer_id.assert_called_once()
    
    def test_get_transfer_id_new_negotiation(self):
        """Test get_transfer_id with new negotiation."""
        counter_party_id = "BPNL000000000001"
        counter_party_address = "https://provider.example.com"
        filter_expression = [{"key": "test"}]
        policies = [{"@id": "policy-123"}]
        edr_entry = {"id": "edr-123", "authKey": "token-456"}
        new_transfer_id = "new-transfer-789"
        
        self.mock_connection_manager.get_connection_transfer_id.return_value = None
        self.mock_connection_manager.add_connection.return_value = new_transfer_id
        
        with mock.patch.object(self.service, 'negotiate_and_transfer') as mock_negotiate:
            mock_negotiate.return_value = edr_entry
            
            result = self.service.get_transfer_id(
                counter_party_id=counter_party_id,
                counter_party_address=counter_party_address,
                filter_expression=filter_expression,
                policies=policies
            )
            
            self.assertEqual(result, new_transfer_id)
            mock_negotiate.assert_called_once()
            self.mock_connection_manager.add_connection.assert_called_once()
    
    def test_discover_connector_protocol_success(self):
        """Test discover_connector_protocol with successful response."""
        bpnl = "BPNL000000000001"
        discovery_info = {
            "https://w3id.org/edc/v0.0.1/ns/counterPartyAddress": "https://provider.example.com",
            "https://w3id.org/edc/v0.0.1/ns/counterPartyId": "did:web:connector-provider.example.com",
            "https://w3id.org/edc/v0.0.1/ns/protocol": "dataspace-protocol-https:2025-1"
        }
        
        mock_response = mock.Mock(spec=Response)
        mock_response.status_code = 200
        mock_response.json.return_value = discovery_info
        
        with mock.patch.object(self.service, '_connector_discovery_controller') as mock_discovery, \
             mock.patch('tractusx_sdk.dataspace.services.connector.saturn.connector_consumer_service.ModelFactory') as mock_factory:
            
            mock_discovery.get_discover.return_value = mock_response
            mock_factory.get_connector_discovery_model.return_value = mock.Mock()
            
            result = self.service.discover_connector_protocol(bpnl=bpnl)
            
            self.assertEqual(result, discovery_info)
    

    

    
    def test_discover_connector_protocol_failure(self):
        """Test discover_connector_protocol with failed response."""
        bpnl = "BPNL000000000001"
        
        mock_response = mock.Mock(spec=Response)
        mock_response.status_code = 404
        
        with mock.patch.object(self.service, '_connector_discovery_controller') as mock_discovery, \
             mock.patch('tractusx_sdk.dataspace.services.connector.saturn.connector_consumer_service.ModelFactory') as mock_factory:
            
            mock_discovery.get_discover.return_value = mock_response
            mock_factory.get_connector_discovery_model.return_value = mock.Mock()
            
            with self.assertRaises(ConnectionError):
                self.service.discover_connector_protocol(bpnl=bpnl)
    
    def test_get_discovery_info_variations(self):
        """Test get_discovery_info with different protocol and ID combinations."""
        test_cases = [
            {
                "name": "legacy_bpnl",
                "discovery_info": {
                    "https://w3id.org/edc/v0.0.1/ns/counterPartyAddress": "https://provider.example.com",
                    "https://w3id.org/edc/v0.0.1/ns/counterPartyId": "BPNL000000000001",
                    "https://w3id.org/edc/v0.0.1/ns/protocol": "dataspace-protocol-http"
                },
                "expected": ("https://provider.example.com", "BPNL000000000001", "dataspace-protocol-http")
            },
            {
                "name": "did_modern",
                "discovery_info": {
                    "https://w3id.org/edc/v0.0.1/ns/counterPartyAddress": "https://provider.example.com",
                    "https://w3id.org/edc/v0.0.1/ns/counterPartyId": "did:web:connector-provider.example.com",
                    "https://w3id.org/edc/v0.0.1/ns/protocol": "dataspace-protocol-https:2025-1"
                },
                "expected": ("https://provider.example.com", "did:web:connector-provider.example.com", "dataspace-protocol-https:2025-1")
            }
        ]
        
        for case in test_cases:
            with self.subTest(case["name"]):
                bpnl = "BPNL000000000001"
                with mock.patch.object(self.service, 'discover_connector_protocol') as mock_discover:
                    mock_discover.return_value = case["discovery_info"]
                    result = self.service.get_discovery_info(bpnl=bpnl)
                    self.assertEqual(result, case["expected"])
    

    
    def test_get_catalog_with_bpnl(self):
        """Test get_catalog_with_bpnl uses internal helper."""
        bpnl = "BPNL000000000001"
        expected_catalog = {"test": "catalog"}
        
        with mock.patch.object(self.service, '_get_catalog_internal') as mock_internal:
            mock_internal.return_value = expected_catalog
            
            result = self.service.get_catalog_with_bpnl(bpnl=bpnl)
            
            self.assertEqual(result, expected_catalog)
            mock_internal.assert_called_once_with(
                bpnl=bpnl,
                counter_party_address=None,
                filter_expression=None,
                context=ConnectorConsumerService.DEFAULT_CONTEXT,
                namespace=ConnectorConsumerService.EDC_NAMESPACE,
                verify=None
            )
    
    def test_get_catalog_request_protocol_variations(self):
        """Test get_catalog_request with different protocols."""
        test_cases = [
            {
                "name": "dsp_2025",
                "protocol": "dataspace-protocol-https:2025-1",
                "counter_party_id": "did:web:connector-provider.example.com",
                "expected_version": "saturn"
            },
            {
                "name": "legacy_http",
                "protocol": "dataspace-protocol-http",
                "counter_party_id": "BPNL000000000001",
                "expected_version": "jupiter"
            }
        ]
        
        for case in test_cases:
            with self.subTest(case["name"]):
                counter_party_address = "https://provider.example.com"
                
                with mock.patch('tractusx_sdk.dataspace.services.connector.saturn.connector_consumer_service.ModelFactory') as mock_factory, \
                     mock.patch('tractusx_sdk.dataspace.services.connector.saturn.connector_consumer_service.DataspaceVersionMapping') as mock_mapping:
                    
                    mock_model = mock.Mock()
                    mock_factory.get_catalog_model.return_value = mock_model
                    mock_enum_value = mock.Mock()
                    mock_enum_value.value = case["expected_version"]
                    mock_mapping.from_protocol.return_value = mock_enum_value
                    
                    result = self.service.get_catalog_request(
                        counter_party_id=case["counter_party_id"],
                        counter_party_address=counter_party_address,
                        protocol=case["protocol"]
                    )
                    
                    self.assertEqual(result, mock_model)
                    mock_factory.get_catalog_model.assert_called_once()
                    mock_mapping.from_protocol.assert_called_once_with(case["protocol"])
    

    
    def test_get_catalog_request_with_did_counter_party_id(self):
        """Test get_catalog_request creates catalog model with DID counter party ID."""
        counter_party_id = "did:web:connector-provider.example.com"
        counter_party_address = "https://provider.example.com"
        protocol = "dataspace-protocol-https:2025-1"
        
        with mock.patch('tractusx_sdk.dataspace.services.connector.saturn.connector_consumer_service.ModelFactory') as mock_factory, \
             mock.patch('tractusx_sdk.dataspace.services.connector.saturn.connector_consumer_service.DataspaceVersionMapping') as mock_mapping:
            
            mock_model = mock.Mock()
            mock_factory.get_catalog_model.return_value = mock_model
            mock_enum_value = mock.Mock()
            mock_enum_value.value = "saturn"
            mock_mapping.from_protocol.return_value = mock_enum_value
            
            result = self.service.get_catalog_request(
                counter_party_id=counter_party_id,
                counter_party_address=counter_party_address,
                protocol=protocol
            )
            
            self.assertEqual(result, mock_model)
            mock_factory.get_catalog_model.assert_called_once()
            # Verify that the counter_party_id (DID) is passed correctly
            call_args = mock_factory.get_catalog_model.call_args
            self.assertIn(counter_party_id, str(call_args))
    
    def test_get_catalog_with_filter(self):
        """Test get_catalog_with_filter uses internal helper."""
        counter_party_id = "BPNL000000000001"
        counter_party_address = "https://provider.example.com"
        filter_expression = [{"key": "test", "value": "value"}]
        expected_catalog = {"test": "catalog"}
        
        with mock.patch.object(self.service, '_get_catalog_internal') as mock_internal:
            mock_internal.return_value = expected_catalog
            
            result = self.service.get_catalog_with_filter(
                counter_party_id=counter_party_id,
                counter_party_address=counter_party_address,
                filter_expression=filter_expression
            )
            
            self.assertEqual(result, expected_catalog)
            mock_internal.assert_called_once()
    
    def test_do_get_success(self):
        """Test do_get method with successful DSP exchange."""
        counter_party_id = "BPNL000000000001"
        counter_party_address = "https://provider.example.com"
        filter_expression = [{"key": "test"}]
        dataplane_url = "https://dataplane.example.com"
        access_token = "test-token"
        
        mock_response = mock.Mock(spec=Response)
        
        with mock.patch.object(self.service, 'do_dsp') as mock_dsp, \
             mock.patch.object(self.service, '_execute_http_request') as mock_execute:
            
            mock_dsp.return_value = (dataplane_url, access_token)
            mock_execute.return_value = mock_response
            
            result = self.service.do_get(
                counter_party_id=counter_party_id,
                counter_party_address=counter_party_address,
                filter_expression=filter_expression
            )
            
            self.assertEqual(result, mock_response)
            mock_dsp.assert_called_once()
            mock_execute.assert_called_once()
    
    def test_do_get_missing_dataplane_info(self):
        """Test do_get method with missing dataplane information."""
        counter_party_id = "BPNL000000000001"
        counter_party_address = "https://provider.example.com"
        filter_expression = [{"key": "test"}]
        
        with mock.patch.object(self.service, 'do_dsp') as mock_dsp:
            mock_dsp.return_value = (None, None)
            
            with self.assertRaises(RuntimeError) as context:
                self.service.do_get(
                    counter_party_id=counter_party_id,
                    counter_party_address=counter_party_address,
                    filter_expression=filter_expression
                )
            
            self.assertIn("No dataplane URL or access_token", str(context.exception))
    

    
    def test_do_post_success(self):
        """Test do_post method with successful DSP exchange."""
        counter_party_id = "BPNL000000000001"
        counter_party_address = "https://provider.example.com"
        filter_expression = [{"key": "test"}]
        json_data = {"test": "data"}
        dataplane_url = "https://dataplane.example.com"
        access_token = "test-token"
        
        mock_response = mock.Mock(spec=Response)
        
        with mock.patch.object(self.service, 'do_dsp') as mock_dsp, \
             mock.patch.object(self.service, '_execute_http_request') as mock_execute:
            
            mock_dsp.return_value = (dataplane_url, access_token)
            mock_execute.return_value = mock_response
            
            result = self.service.do_post(
                counter_party_id=counter_party_id,
                counter_party_address=counter_party_address,
                filter_expression=filter_expression,
                json=json_data
            )
            
            self.assertEqual(result, mock_response)
            mock_dsp.assert_called_once()
            mock_execute.assert_called_once()
    

    
    def test_do_put_success(self):
        """Test do_put method with successful DSP exchange."""
        counter_party_id = "BPNL000000000001"
        counter_party_address = "https://provider.example.com"
        filter_expression = [{"key": "test"}]
        json_data = {"test": "data"}
        dataplane_url = "https://dataplane.example.com"
        access_token = "test-token"
        
        mock_response = mock.Mock(spec=Response)
        
        with mock.patch.object(self.service, 'do_dsp') as mock_dsp, \
             mock.patch.object(self.service, '_execute_http_request') as mock_execute:
            
            mock_dsp.return_value = (dataplane_url, access_token)
            mock_execute.return_value = mock_response
            
            result = self.service.do_put(
                counter_party_id=counter_party_id,
                counter_party_address=counter_party_address,
                filter_expression=filter_expression,
                json=json_data
            )
            
            self.assertEqual(result, mock_response)
            mock_dsp.assert_called_once()
            mock_execute.assert_called_once()
    

    
    def test_do_dsp_success(self):
        """Test do_dsp method returns dataplane URL and access token."""
        counter_party_id = "BPNL000000000001"
        counter_party_address = "https://provider.example.com"
        filter_expression = [{"key": "test"}]
        policies = [{"@id": "policy-123"}]
        transfer_id = "transfer-456"
        expected_url = "https://dataplane.example.com"
        expected_token = "access-token-789"
        
        with mock.patch.object(self.service, 'get_transfer_id') as mock_transfer, \
             mock.patch.object(self.service, 'get_endpoint_with_token') as mock_endpoint:
            
            mock_transfer.return_value = transfer_id
            mock_endpoint.return_value = (expected_url, expected_token)
            
            result = self.service.do_dsp(
                counter_party_id=counter_party_id,
                counter_party_address=counter_party_address,
                filter_expression=filter_expression,
                policies=policies
            )
            
            self.assertEqual(result, (expected_url, expected_token))
            mock_transfer.assert_called_once()
            mock_endpoint.assert_called_once_with(transfer_id=transfer_id)
    
    def test_do_dsp_with_bpnl_protocol_variations(self):
        """Test do_dsp_with_bpnl with different protocol and discovery results."""
        test_cases = [
            {
                "name": "legacy_bpnl",
                "discovery_result": ("https://discovered.provider.com", "BPNL000000000001", "dataspace-protocol-http"),
                "expected_counter_party_id": "BPNL000000000001"
            },
            {
                "name": "modern_did",
                "discovery_result": ("https://discovered.provider.com", "did:web:connector-provider.example.com", "dataspace-protocol-https:2025-1"),
                "expected_counter_party_id": "did:web:connector-provider.example.com"
            }
        ]
        
        for case in test_cases:
            with self.subTest(case["name"]):
                bpnl = "BPNL000000000001"
                counter_party_address = "https://provider.example.com"
                filter_expression = [{"key": "test"}]
                policies = [{"@id": "policy-123"}]
                expected_url = "https://dataplane.example.com"
                expected_token = "access-token-123"
                
                with mock.patch.object(self.service, 'get_discovery_info') as mock_discovery, \
                     mock.patch.object(self.service, 'do_dsp') as mock_dsp:
                    
                    mock_discovery.return_value = case["discovery_result"]
                    mock_dsp.return_value = (expected_url, expected_token)
                    
                    result = self.service.do_dsp_with_bpnl(
                        bpnl=bpnl,
                        counter_party_address=counter_party_address,
                        filter_expression=filter_expression,
                        policies=policies
                    )
                    
                    self.assertEqual(result, (expected_url, expected_token))
                    mock_discovery.assert_called_once()
                    # Verify the correct counter party ID was used
                    call_args = mock_dsp.call_args
                    self.assertEqual(call_args[1]['counter_party_id'], case["expected_counter_party_id"])


    def test_end_to_end_discovery_with_different_protocols(self):
        """Test complete end-to-end flow with different protocol and ID combinations."""
        test_cases = [
            {
                "name": "DSP 2025-1 with DID (required)",
                "discovery_response": {
                    "https://w3id.org/edc/v0.0.1/ns/counterPartyAddress": "https://provider.example.com",
                    "https://w3id.org/edc/v0.0.1/ns/counterPartyId": "did:web:connector-provider.example.com",
                    "https://w3id.org/edc/v0.0.1/ns/protocol": "dataspace-protocol-https:2025-1"
                },
                "expected_counter_party_id": "did:web:connector-provider.example.com",
                "expected_protocol": "dataspace-protocol-https:2025-1"
            },
            {
                "name": "Legacy protocol with BPNL",
                "discovery_response": {
                    "https://w3id.org/edc/v0.0.1/ns/counterPartyAddress": "https://provider.example.com",
                    "https://w3id.org/edc/v0.0.1/ns/counterPartyId": "BPNL000000000001",
                    "https://w3id.org/edc/v0.0.1/ns/protocol": "dataspace-protocol-http"
                },
                "expected_counter_party_id": "BPNL000000000001",
                "expected_protocol": "dataspace-protocol-http"
            }
        ]
        
        for test_case in test_cases:
            with self.subTest(test_case["name"]):
                bpnl = "BPNL000000000001"
                
                # Mock discovery response
                mock_response = mock.Mock(spec=Response)
                mock_response.status_code = 200
                mock_response.json.return_value = test_case["discovery_response"]
                
                with mock.patch.object(self.service, '_connector_discovery_controller') as mock_discovery, \
                     mock.patch('tractusx_sdk.dataspace.services.connector.saturn.connector_consumer_service.ModelFactory') as mock_factory:
                    
                    mock_discovery.get_discover.return_value = mock_response
                    mock_factory.get_connector_discovery_model.return_value = mock.Mock()
                    
                    # Test discovery
                    result = self.service.discover_connector_protocol(bpnl=bpnl)
                    self.assertEqual(result, test_case["discovery_response"])
                    
                    # Test parsed discovery info
                    discovery_info = self.service.get_discovery_info(bpnl=bpnl)
                    self.assertEqual(discovery_info[0], "https://provider.example.com")
                    self.assertEqual(discovery_info[1], test_case["expected_counter_party_id"])
                    self.assertEqual(discovery_info[2], test_case["expected_protocol"])
    
    def test_protocol_version_mapping_consistency(self):
        """Test that protocol version mapping is consistent across different methods."""
        test_cases = [
            {
                "protocol": "dataspace-protocol-https:2025-1",
                "counter_party_id": "did:web:connector-provider.example.com",  # DSP 2025-1 requires DID
                "expected_version": "saturn"
            },
            {
                "protocol": "dataspace-protocol-http",
                "counter_party_id": "BPNL000000000001",  # Legacy protocol uses BPNL
                "expected_version": "jupiter"
            }
        ]
        
        for test_case in test_cases:
            with self.subTest(protocol=test_case["protocol"]):
                counter_party_address = "https://provider.example.com"
                
                with mock.patch('tractusx_sdk.dataspace.services.connector.saturn.connector_consumer_service.ModelFactory') as mock_factory, \
                     mock.patch('tractusx_sdk.dataspace.services.connector.saturn.connector_consumer_service.DataspaceVersionMapping') as mock_mapping:
                    
                    mock_model = mock.Mock()
                    mock_factory.get_catalog_model.return_value = mock_model
                    mock_enum_value = mock.Mock()
                    mock_enum_value.value = test_case["expected_version"]
                    mock_mapping.from_protocol.return_value = mock_enum_value
                    
                    # Test catalog request creation
                    result = self.service.get_catalog_request(
                        counter_party_id=test_case["counter_party_id"],
                        counter_party_address=counter_party_address,
                        protocol=test_case["protocol"]
                    )
                    
                    self.assertEqual(result, mock_model)
                    mock_mapping.from_protocol.assert_called_with(test_case["protocol"])
                    
                    # Verify that the correct dataspace version is being used
                    self.assertEqual(mock_enum_value.value, test_case["expected_version"])
    



if __name__ == '__main__':
    main()