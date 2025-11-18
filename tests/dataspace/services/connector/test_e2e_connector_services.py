"""
End-to-End Integration Test: Provider and Consumer Connector Services

This test demonstrates the complete data exchange flow using the actual
ConnectorProviderService and ConnectorConsumerService from the SDK.

Flow:
1. Provider creates Asset, Policies, and Contract Definition
2. Consumer discovers the offer via Catalog
3. Consumer negotiates a Contract
4. Consumer initiates Transfer Process
5. Consumer accesses data using EDR

NOTE: This test requires actual running EDC connectors and uses placeholders
for real endpoints. Replace placeholders with actual values for integration testing.
"""

import pytest
import json
import time
from unittest.mock import Mock, patch, MagicMock
from tractusx_sdk.dataspace.services.connector.service_factory import ServiceFactory


# ============================================================================
# PLACEHOLDERS - Replace these with actual values for integration testing
# ============================================================================

# Provider Connector Configuration
PROVIDER_CONNECTOR_URL = "PLACEHOLDER_PROVIDER_EDC_URL"  # e.g., "https://provider-edc.example.com"
PROVIDER_DMA_PATH = "/management"
PROVIDER_API_KEY = "PLACEHOLDER_PROVIDER_API_KEY"
PROVIDER_BPN = "PLACEHOLDER_PROVIDER_BPN"  # e.g., "BPNL000000000001"
PROVIDER_DSP_URL = "PLACEHOLDER_PROVIDER_DSP_URL"  # e.g., "https://provider-edc.example.com/api/v1/dsp"

# Consumer Connector Configuration
CONSUMER_CONNECTOR_URL = "PLACEHOLDER_CONSUMER_EDC_URL"  # e.g., "https://consumer-edc.example.com"
CONSUMER_DMA_PATH = "/management"
CONSUMER_API_KEY = "PLACEHOLDER_CONSUMER_API_KEY"
CONSUMER_BPN = "PLACEHOLDER_CONSUMER_BPN"  # e.g., "BPNL000000000002"

# Backend Data Source Configuration
BACKEND_DATA_URL = "PLACEHOLDER_BACKEND_API_URL"  # e.g., "https://backend.example.com/api/data"
BACKEND_AUTH_TOKEN_URL = "PLACEHOLDER_OAUTH_TOKEN_URL"  # e.g., "https://auth.example.com/token"
BACKEND_CLIENT_ID = "PLACEHOLDER_CLIENT_ID"
BACKEND_CLIENT_SECRET_KEY = "PLACEHOLDER_SECRET_KEY"  # Key in vault, not actual secret

# Test Configuration
USE_MOCK = True  # Set to False to run against real EDC connectors
DATASPACE_VERSION = "saturn"  # "jupiter" or "saturn"


@pytest.mark.skipif(USE_MOCK, reason="Mocked test - set USE_MOCK=False for real integration")
class TestE2EConnectorServicesIntegration:
    """
    End-to-End integration tests using real connector services.
    
    These tests require actual running EDC connectors.
    Set USE_MOCK=False and provide real credentials to run.
    """
    
    def test_complete_e2e_flow_real_connectors(self):
        """
        Complete E2E flow from Provider asset creation to Consumer data access
        using real EDC connector services.
        """
        # Initialize Provider Service
        provider_service = ServiceFactory.get_connector_provider_service(
            dataspace_version=DATASPACE_VERSION,
            base_url=PROVIDER_CONNECTOR_URL,
            dma_path=PROVIDER_DMA_PATH,
            headers={
                "X-Api-Key": PROVIDER_API_KEY,
                "Content-Type": "application/json"
            },
            verbose=True
        )
        
        # Initialize Consumer Service
        consumer_service = ServiceFactory.get_connector_consumer_service(
            dataspace_version=DATASPACE_VERSION,
            base_url=CONSUMER_CONNECTOR_URL,
            dma_path=CONSUMER_DMA_PATH,
            headers={
                "X-Api-Key": CONSUMER_API_KEY,
                "Content-Type": "application/json"
            },
            verbose=True
        )
        
        # Test IDs
        asset_id = f"test-asset-{int(time.time())}"
        access_policy_id = f"access-policy-{int(time.time())}"
        usage_policy_id = f"usage-policy-{int(time.time())}"
        contract_def_id = f"contract-def-{int(time.time())}"
        
        try:
            # ================================================================
            # STEP 1: Provider creates Access Policy
            # ================================================================
            print("\n=== STEP 1: Creating Access Policy ===")
            
            access_policy_response = provider_service.create_policy(
                policy_id=access_policy_id,
                permissions=[{
                    "action": "access",
                    "constraint": {
                        "leftOperand": "BusinessPartnerNumber",
                        "operator": "eq",
                        "rightOperand": CONSUMER_BPN
                    }
                }]
            )
            
            print(f"Access Policy created: {access_policy_id}")
            assert access_policy_response is not None
            
            # ================================================================
            # STEP 2: Provider creates Usage Policy
            # ================================================================
            print("\n=== STEP 2: Creating Usage Policy ===")
            
            usage_policy_response = provider_service.create_policy(
                policy_id=usage_policy_id,
                permissions=[{
                    "action": "use",
                    "constraint": {
                        "and": [
                            {
                                "leftOperand": "Membership",
                                "operator": "eq",
                                "rightOperand": "active"
                            },
                            {
                                "leftOperand": "FrameworkAgreement",
                                "operator": "eq",
                                "rightOperand": "DataExchangeGovernance:1.0"
                            }
                        ]
                    }
                }]
            )
            
            print(f"Usage Policy created: {usage_policy_id}")
            assert usage_policy_response is not None
            
            # ================================================================
            # STEP 3: Provider creates Asset
            # ================================================================
            print("\n=== STEP 3: Creating Asset ===")
            
            asset_response = provider_service.create_asset(
                asset_id=asset_id,
                base_url=BACKEND_DATA_URL,
                dct_type="https://w3id.org/catenax/taxonomy#VehicleProductionData",
                version="1.0",
                headers={
                    "oauth2:tokenUrl": BACKEND_AUTH_TOKEN_URL,
                    "oauth2:clientId": BACKEND_CLIENT_ID,
                    "oauth2:clientSecretKey": BACKEND_CLIENT_SECRET_KEY
                },
                proxy_params={
                    "proxyQueryParams": "true",
                    "proxyPath": "true",
                    "proxyMethod": "true",
                    "proxyBody": "false"
                }
            )
            
            print(f"Asset created: {asset_id}")
            assert asset_response is not None
            
            # ================================================================
            # STEP 4: Provider creates Contract Definition
            # ================================================================
            print("\n=== STEP 4: Creating Contract Definition ===")
            
            contract_def_response = provider_service.create_contract(
                contract_id=contract_def_id,
                usage_policy_id=usage_policy_id,
                access_policy_id=access_policy_id,
                asset_id=asset_id
            )
            
            print(f"Contract Definition created: {contract_def_id}")
            assert contract_def_response is not None
            
            # Give provider EDC time to process
            time.sleep(2)
            
            # ================================================================
            # STEP 5: Consumer requests Catalog
            # ================================================================
            print("\n=== STEP 5: Consumer Requesting Catalog ===")
            
            catalog_response = consumer_service.catalogs.get_from_provider(
                counter_party_id=PROVIDER_BPN,
                counter_party_address=PROVIDER_DSP_URL,
                protocol="dataspace-protocol-http:2025-1"
            )
            
            print(f"Catalog received from Provider")
            assert catalog_response.status_code == 200
            
            catalog_data = catalog_response.json()
            print(f"Catalog datasets: {len(catalog_data.get('dcat:dataset', []))}")
            
            # Find our asset in the catalog
            datasets = catalog_data.get("dcat:dataset", [])
            target_dataset = None
            for dataset in datasets:
                if dataset.get("@id") == asset_id:
                    target_dataset = dataset
                    break
            
            assert target_dataset is not None, f"Asset {asset_id} not found in catalog"
            
            # Extract offer details
            offer_policy = target_dataset["odrl:hasPolicy"]
            offer_id = offer_policy["@id"]
            
            print(f"Found offer: {offer_id} for asset: {asset_id}")
            
            # ================================================================
            # STEP 6: Consumer negotiates Contract
            # ================================================================
            print("\n=== STEP 6: Consumer Negotiating Contract ===")
            
            # Prepare negotiation context with ODRL
            negotiation_context = [
                "https://w3id.org/catenax/2025/9/policy/odrl.jsonld",
                "https://w3id.org/catenax/2025/9/policy/context.jsonld",
                {
                    "@vocab": "https://w3id.org/edc/v0.0.1/ns/"
                }
            ]
            
            # Prepare offer policy for negotiation
            offer_policy_data = {
                "permission": offer_policy.get("odrl:permission", []),
                "prohibition": offer_policy.get("odrl:prohibition", []),
                "obligation": offer_policy.get("odrl:obligation", [])
            }
            
            from tractusx_sdk.dataspace.models.connector.model_factory import ModelFactory
            
            contract_negotiation = ModelFactory.get_contract_negotiation_model(
                dataspace_version=DATASPACE_VERSION,
                counter_party_address=PROVIDER_DSP_URL,
                offer_id=offer_id,
                asset_id=asset_id,
                provider_id=PROVIDER_BPN,
                offer_policy=offer_policy_data,
                context=negotiation_context,
                protocol="dataspace-protocol-http:2025-1"
            )
            
            negotiation_response = consumer_service.contract_negotiations.create(
                obj=contract_negotiation
            )
            
            assert negotiation_response.status_code == 200
            negotiation_data = negotiation_response.json()
            negotiation_id = negotiation_data.get("@id")
            
            print(f"Contract negotiation initiated: {negotiation_id}")
            
            # Poll negotiation status until FINALIZED
            max_wait = 30  # seconds
            poll_interval = 2  # seconds
            elapsed = 0
            contract_agreement_id = None
            
            while elapsed < max_wait:
                time.sleep(poll_interval)
                elapsed += poll_interval
                
                status_response = consumer_service.contract_negotiations.get(negotiation_id)
                if status_response.status_code == 200:
                    status_data = status_response.json()
                    state = status_data.get("state", status_data.get("edc:state"))
                    
                    print(f"Negotiation state: {state}")
                    
                    if state == "FINALIZED":
                        contract_agreement_id = status_data.get("contractAgreementId", 
                                                                status_data.get("edc:contractAgreementId"))
                        print(f"Contract Agreement ID: {contract_agreement_id}")
                        break
            
            assert contract_agreement_id is not None, "Contract negotiation did not finalize"
            
            # ================================================================
            # STEP 7: Consumer starts Transfer Process
            # ================================================================
            print("\n=== STEP 7: Consumer Starting Transfer Process ===")
            
            transfer_request = ModelFactory.get_transfer_process_model(
                dataspace_version=DATASPACE_VERSION,
                counter_party_address=PROVIDER_DSP_URL,
                contract_id=contract_agreement_id,
                transfer_type="HttpData-PULL",
                protocol="dataspace-protocol-http:2025-1",
                data_destination={
                    "type": "HttpProxy"
                }
            )
            
            transfer_response = consumer_service.transfer_processes.create(obj=transfer_request)
            
            assert transfer_response.status_code == 200
            transfer_data = transfer_response.json()
            transfer_id = transfer_data.get("@id")
            
            print(f"Transfer process initiated: {transfer_id}")
            
            # Poll transfer status until STARTED and EDR available
            elapsed = 0
            edr_available = False
            
            while elapsed < max_wait:
                time.sleep(poll_interval)
                elapsed += poll_interval
                
                transfer_status = consumer_service.transfer_processes.get(transfer_id)
                if transfer_status.status_code == 200:
                    transfer_state_data = transfer_status.json()
                    state = transfer_state_data.get("state", transfer_state_data.get("edc:state"))
                    
                    print(f"Transfer state: {state}")
                    
                    if state in ["STARTED", "COMPLETED"]:
                        # Check if EDR is available
                        edr_response = consumer_service.edrs.get_for_transfer(transfer_id)
                        if edr_response.status_code == 200:
                            edr_available = True
                            break
            
            assert edr_available, "EDR not available after transfer started"
            
            # ================================================================
            # STEP 8: Consumer accesses data using EDR
            # ================================================================
            print("\n=== STEP 8: Consumer Accessing Data via EDR ===")
            
            edr_data = edr_response.json()
            dataplane_url = edr_data.get("endpoint", edr_data.get("edc:endpoint"))
            access_token = edr_data.get("authorization", edr_data.get("edc:authorization"))
            
            print(f"EDR received:")
            print(f"  - Endpoint: {dataplane_url}")
            print(f"  - Token: {access_token[:20]}..." if access_token else "  - Token: None")
            
            assert dataplane_url is not None
            assert access_token is not None
            
            # Make actual data request using EDR
            import requests
            
            data_response = requests.get(
                dataplane_url,
                headers={
                    "Authorization": access_token
                },
                verify=True  # Set to False for self-signed certs in dev
            )
            
            print(f"Data access response status: {data_response.status_code}")
            assert data_response.status_code == 200
            
            print("\n✓ Complete E2E flow successful!")
            print("  - Provider created Asset, Policies, and Contract Definition")
            print("  - Consumer discovered offer via Catalog")
            print("  - Consumer negotiated Contract Agreement")
            print("  - Consumer initiated Transfer Process")
            print("  - Consumer accessed data using EDR")
            
        finally:
            # ================================================================
            # CLEANUP: Delete created resources
            # ================================================================
            print("\n=== CLEANUP: Deleting Test Resources ===")
            
            try:
                provider_service.contract_definitions.delete(contract_def_id)
                print(f"Deleted contract definition: {contract_def_id}")
            except Exception as e:
                print(f"Failed to delete contract definition: {e}")
            
            try:
                provider_service.assets.delete(asset_id)
                print(f"Deleted asset: {asset_id}")
            except Exception as e:
                print(f"Failed to delete asset: {e}")
            
            try:
                provider_service.policies.delete(usage_policy_id)
                print(f"Deleted usage policy: {usage_policy_id}")
            except Exception as e:
                print(f"Failed to delete usage policy: {e}")
            
            try:
                provider_service.policies.delete(access_policy_id)
                print(f"Deleted access policy: {access_policy_id}")
            except Exception as e:
                print(f"Failed to delete access policy: {e}")


@pytest.mark.skipif(not USE_MOCK, reason="Real integration test - set USE_MOCK=True for mocked tests")
class TestE2EConnectorServicesMocked:
    """
    Mocked E2E tests that verify the service interactions without real connectors.
    
    These tests validate the correct usage of the SDK APIs and model structures.
    """
    
    @patch('tractusx_sdk.dataspace.services.connector.base_connector_provider.AdapterFactory')
    @patch('tractusx_sdk.dataspace.services.connector.base_connector_provider.ControllerFactory')
    def test_provider_creates_asset_policy_contract(self, mock_controller_factory, mock_adapter_factory):
        """Test Provider service creates Asset, Policies, and Contract Definition"""
        
        # Setup mocks
        mock_adapter = MagicMock()
        mock_adapter_factory.get_dma_adapter.return_value = mock_adapter
        
        mock_asset_controller = MagicMock()
        mock_policy_controller = MagicMock()
        mock_contract_controller = MagicMock()
        
        mock_controller_factory.get_dma_controllers_for_version.return_value = {
            "ASSET": mock_asset_controller,
            "POLICY": mock_policy_controller,
            "CONTRACT_DEFINITION": mock_contract_controller
        }
        
        # Mock successful responses
        mock_asset_response = Mock()
        mock_asset_response.status_code = 200
        mock_asset_response.json.return_value = {"@id": "test-asset"}
        mock_asset_controller.create.return_value = mock_asset_response
        
        mock_policy_response = Mock()
        mock_policy_response.status_code = 200
        mock_policy_response.json.return_value = {"@id": "test-policy"}
        mock_policy_controller.create.return_value = mock_policy_response
        
        mock_contract_response = Mock()
        mock_contract_response.status_code = 200
        mock_contract_response.json.return_value = {"@id": "test-contract"}
        mock_contract_controller.create.return_value = mock_contract_response
        
        # Initialize Provider Service
        provider_service = ServiceFactory.get_connector_provider_service(
            dataspace_version=DATASPACE_VERSION,
            base_url="https://mock-provider.example.com",
            dma_path="/management",
            headers={"X-Api-Key": "mock-key"},
            verbose=False
        )
        
        # Test asset creation
        asset_response = provider_service.create_asset(
            asset_id="test-asset",
            base_url="https://backend.example.com/api",
            dct_type="https://w3id.org/catenax/taxonomy#TestData",
            version="1.0"
        )
        
        assert asset_response["@id"] == "test-asset"
        assert mock_asset_controller.create.called
        
        # Test policy creation
        policy_response = provider_service.create_policy(
            policy_id="test-policy",
            permissions=[{"action": "use"}]
        )
        
        assert policy_response["@id"] == "test-policy"
        assert mock_policy_controller.create.called
        
        # Test contract definition creation
        contract_response = provider_service.create_contract(
            contract_id="test-contract",
            usage_policy_id="test-policy",
            access_policy_id="test-policy",
            asset_id="test-asset"
        )
        
        assert contract_response["@id"] == "test-contract"
        assert mock_contract_controller.create.called
    
    @patch('tractusx_sdk.dataspace.services.connector.base_connector_consumer.AdapterFactory')
    @patch('tractusx_sdk.dataspace.services.connector.base_connector_consumer.ControllerFactory')
    def test_consumer_catalog_negotiation_transfer_flow(self, mock_controller_factory, mock_adapter_factory):
        """Test Consumer service performs Catalog → Negotiation → Transfer flow"""
        
        # Setup mocks
        mock_adapter = MagicMock()
        mock_adapter_factory.get_dma_adapter.return_value = mock_adapter
        
        mock_catalog_controller = MagicMock()
        mock_edr_controller = MagicMock()
        mock_negotiation_controller = MagicMock()
        mock_transfer_controller = MagicMock()
        
        mock_controller_factory.get_dma_controllers_for_version.return_value = {
            "CATALOG": mock_catalog_controller,
            "EDR": mock_edr_controller,
            "CONTRACT_NEGOTIATION": mock_negotiation_controller,
            "TRANSFER_PROCESS": mock_transfer_controller
        }
        
        # Mock catalog response
        mock_catalog_response = Mock()
        mock_catalog_response.status_code = 200
        mock_catalog_response.json.return_value = {
            "@type": "dcat:Catalog",
            "dcat:dataset": [{
                "@id": "test-asset",
                "odrl:hasPolicy": {
                    "@id": "test-offer",
                    "@type": "odrl:Offer",
                    "odrl:permission": [{"action": "use"}],
                    "odrl:prohibition": [],
                    "odrl:obligation": []
                }
            }]
        }
        mock_catalog_controller.get_from_provider.return_value = mock_catalog_response
        
        # Mock negotiation response
        mock_negotiation_response = Mock()
        mock_negotiation_response.status_code = 200
        mock_negotiation_response.json.return_value = {"@id": "negotiation-123"}
        mock_negotiation_controller.create.return_value = mock_negotiation_response
        
        mock_negotiation_status = Mock()
        mock_negotiation_status.status_code = 200
        mock_negotiation_status.json.return_value = {
            "@id": "negotiation-123",
            "state": "FINALIZED",
            "contractAgreementId": "agreement-456"
        }
        mock_negotiation_controller.get.return_value = mock_negotiation_status
        
        # Mock transfer response
        mock_transfer_response = Mock()
        mock_transfer_response.status_code = 200
        mock_transfer_response.json.return_value = {"@id": "transfer-789"}
        mock_transfer_controller.create.return_value = mock_transfer_response
        
        # Mock EDR response
        mock_edr_response = Mock()
        mock_edr_response.status_code = 200
        mock_edr_response.json.return_value = {
            "endpoint": "https://provider-dataplane.example.com",
            "authorization": "Bearer test-token"
        }
        mock_edr_controller.get_for_transfer.return_value = mock_edr_response
        
        # Initialize Consumer Service
        consumer_service = ServiceFactory.get_connector_consumer_service(
            dataspace_version=DATASPACE_VERSION,
            base_url="https://mock-consumer.example.com",
            dma_path="/management",
            headers={"X-Api-Key": "mock-key"},
            verbose=False
        )
        
        # Test catalog request
        catalog_response = consumer_service.catalogs.get_from_provider(
            counter_party_id="BPNL000000000001",
            counter_party_address="https://provider.example.com/dsp",
            protocol="dataspace-protocol-http:2025-1"
        )
        
        assert catalog_response.status_code == 200
        catalog_data = catalog_response.json()
        assert len(catalog_data["dcat:dataset"]) == 1
        
        # Verify catalog controller was called
        assert mock_catalog_controller.get_from_provider.called
        
        # Test contract negotiation
        from tractusx_sdk.dataspace.models.connector.model_factory import ModelFactory
        
        offer_policy = catalog_data["dcat:dataset"][0]["odrl:hasPolicy"]
        
        negotiation_model = ModelFactory.get_contract_negotiation_model(
            dataspace_version=DATASPACE_VERSION,
            counter_party_address="https://provider.example.com/dsp",
            offer_id="test-offer",
            asset_id="test-asset",
            provider_id="BPNL000000000001",
            offer_policy={
                "permission": offer_policy["odrl:permission"],
                "prohibition": offer_policy["odrl:prohibition"],
                "obligation": offer_policy["odrl:obligation"]
            },
            context=[
                "https://w3id.org/catenax/2025/9/policy/odrl.jsonld",
                "https://w3id.org/catenax/2025/9/policy/context.jsonld",
                {"@vocab": "https://w3id.org/edc/v0.0.1/ns/"}
            ],
            protocol="dataspace-protocol-http:2025-1"
        )
        
        negotiation_response = consumer_service.contract_negotiations.create(obj=negotiation_model)
        assert negotiation_response.status_code == 200
        
        # Verify negotiation controller was called
        assert mock_negotiation_controller.create.called
        
        # Get negotiation status
        negotiation_id = negotiation_response.json()["@id"]
        status_response = consumer_service.contract_negotiations.get(negotiation_id)
        assert status_response.json()["state"] == "FINALIZED"
        
        # Test transfer process
        transfer_model = ModelFactory.get_transfer_process_model(
            dataspace_version=DATASPACE_VERSION,
            counter_party_address="https://provider.example.com/dsp",
            contract_id="agreement-456",
            transfer_type="HttpData-PULL",
            protocol="dataspace-protocol-http:2025-1",
            data_destination={"type": "HttpProxy"}
        )
        
        transfer_response = consumer_service.transfer_processes.create(obj=transfer_model)
        assert transfer_response.status_code == 200
        
        # Verify transfer controller was called
        assert mock_transfer_controller.create.called
        
        # Get EDR
        transfer_id = transfer_response.json()["@id"]
        edr_response = consumer_service.edrs.get_for_transfer(transfer_id)
        assert edr_response.status_code == 200
        
        edr_data = edr_response.json()
        assert "endpoint" in edr_data
        assert "authorization" in edr_data
    
    def test_model_serialization_for_connector_services(self):
        """Test that models serialize correctly for connector service usage"""
        from tractusx_sdk.dataspace.models.connector.model_factory import ModelFactory
        import json
        
        # Test PolicyModel serialization
        policy = ModelFactory.get_policy_model(
            dataspace_version=DATASPACE_VERSION,
            oid="test-policy",
            permissions=[{
                "action": "use",
                "constraint": {
                    "leftOperand": "BusinessPartnerNumber",
                    "operator": "eq",
                    "rightOperand": "BPNL000000000002"
                }
            }]
        )
        
        policy_data = json.loads(policy.to_data())
        
        # Verify ODRL context compliance
        assert "@context" in policy_data
        assert isinstance(policy_data["@context"], list)
        assert "https://w3id.org/catenax/2025/9/policy/odrl.jsonld" in policy_data["@context"]
        assert policy_data["@type"] == "PolicyDefinition"
        assert policy_data["policy"]["@type"] == "Set"
        
        # Test AssetModel serialization
        asset = ModelFactory.get_asset_model(
            dataspace_version=DATASPACE_VERSION,
            oid="test-asset",
            properties={
                "dct:type": {"@id": "https://w3id.org/catenax/taxonomy#TestData"}
            },
            data_address={
                "type": "HttpData",
                "baseUrl": "https://backend.example.com/api"
            }
        )
        
        asset_data = json.loads(asset.to_data())
        assert asset_data["@type"] == "Asset"
        assert asset_data["@id"] == "test-asset"
        
        # Test ContractNegotiationModel serialization
        negotiation = ModelFactory.get_contract_negotiation_model(
            dataspace_version=DATASPACE_VERSION,
            counter_party_address="https://provider.example.com/dsp",
            offer_id="offer-1",
            asset_id="asset-1",
            provider_id="BPNL000000000001",
            offer_policy={
                "permission": [{"action": "use"}],
                "prohibition": [],
                "obligation": []
            },
            context=[
                "https://w3id.org/catenax/2025/9/policy/odrl.jsonld",
                "https://w3id.org/catenax/2025/9/policy/context.jsonld",
                {"@vocab": "https://w3id.org/edc/v0.0.1/ns/"}
            ],
            protocol="dataspace-protocol-http:2025-1"
        )
        
        negotiation_data = json.loads(negotiation.to_data())
        assert negotiation_data["@type"] == "ContractRequest"
        assert "https://w3id.org/catenax/2025/9/policy/odrl.jsonld" in negotiation_data["@context"]
        assert negotiation_data["policy"]["@type"] == "odrl:Offer"


# ============================================================================
# Instructions for Running Integration Tests
# ============================================================================

"""
TO RUN MOCKED TESTS (Default):
    pytest tests/dataspace/services/connector/test_e2e_connector_services.py -v

TO RUN REAL INTEGRATION TESTS:
    1. Set up Provider and Consumer EDC connectors
    2. Update the PLACEHOLDER values at the top of this file:
       - PROVIDER_CONNECTOR_URL
       - PROVIDER_DMA_PATH
       - PROVIDER_API_KEY
       - PROVIDER_BPN
       - PROVIDER_DSP_URL
       - CONSUMER_CONNECTOR_URL
       - CONSUMER_DMA_PATH
       - CONSUMER_API_KEY
       - CONSUMER_BPN
       - BACKEND_DATA_URL
       - BACKEND_AUTH_TOKEN_URL
       - BACKEND_CLIENT_ID
       - BACKEND_CLIENT_SECRET_KEY
    
    3. Set USE_MOCK = False
    
    4. Run the tests:
       pytest tests/dataspace/services/connector/test_e2e_connector_services.py::TestE2EConnectorServicesIntegration -v -s

EXAMPLE PLACEHOLDER VALUES:

Provider Configuration:
    PROVIDER_CONNECTOR_URL = "https://provider-edc.tractus-x.example.com"
    PROVIDER_DMA_PATH = "/management"
    PROVIDER_API_KEY = "your-provider-api-key-here"
    PROVIDER_BPN = "BPNL000000000001"
    PROVIDER_DSP_URL = "https://provider-edc.tractus-x.example.com/api/v1/dsp"

Consumer Configuration:
    CONSUMER_CONNECTOR_URL = "https://consumer-edc.tractus-x.example.com"
    CONSUMER_DMA_PATH = "/management"
    CONSUMER_API_KEY = "your-consumer-api-key-here"
    CONSUMER_BPN = "BPNL000000000002"

Backend Configuration:
    BACKEND_DATA_URL = "https://backend-api.example.com/api/production-data"
    BACKEND_AUTH_TOKEN_URL = "https://auth.example.com/oauth/token"
    BACKEND_CLIENT_ID = "backend-service-client"
    BACKEND_CLIENT_SECRET_KEY = "vault-secret-key-reference"

NOTES:
- The test will automatically clean up created resources
- Ensure both EDC connectors are running and accessible
- The Consumer BPN must be allowed in the Provider's access policy
- Backend API must support OAuth2 authentication
- For development, you may need to set verify=False for self-signed certificates
"""
