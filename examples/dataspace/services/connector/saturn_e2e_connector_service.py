"""
End-to-End Example: Saturn Connector Services - Data Provision and Consumption

This example demonstrates the complete flow from Provider data provision to Consumer
data consumption using the actual ConnectorProviderService and ConnectorConsumerService
from the Tractus-X SDK.

Flow:
1. Provider provisions data (Asset + Policies + Contract Definition)
2. Consumer discovers available offers (Catalog Request)
3. Consumer negotiates contract
4. Consumer initiates transfer
5. Consumer accesses data using EDR

Based on: https://github.com/eclipse-tractusx/industry-core-hub/blob/main/ichub-backend/connector.py
"""

from tractusx_sdk.dataspace.services.connector import ServiceFactory
from tractusx_sdk.dataspace.services.connector.base_connector_provider import BaseConnectorProviderService
import time
import json


# ============================================================================
# CONFIGURATION - Replace with your actual values
# ============================================================================

# Provider Connector Configuration
PROVIDER_CONNECTOR_CONFIG = {
    "base_url": "https://edc-provider-ichub-control.int.catena-x.net",  # PLACEHOLDER: Provider EDC Control Plane URL
    "dma_path": "/management",  # Management API path
    "api_key_header": "X-Api-Key",  # API key header name
    "api_key": "ACA176440A8BDD3954FCEC3552BF8985AFB75608A57B9121EA809791854AAA2BEDBF85333572E8DECE9537D69697D6BA28EA26174085242CB536B7877E219CAC",  # PLACEHOLDER: Provider API key
    "dataspace_version": "saturn",  # "jupiter" or "saturn"
    "bpn": "BPNL0000000093Q7",  # PLACEHOLDER: Provider BPN
    "dsp_url": "https://edc-provider-ichub-control.int.catena-x.net/api/v1/dsp/2025-01"  # PLACEHOLDER: Provider DSP endpoint
}

# Consumer Connector Configuration
CONSUMER_CONNECTOR_CONFIG = {
    "base_url": "https://edc-consumer-saturn-ichub-control.int.catena-x.net",  # PLACEHOLDER: Consumer EDC Control Plane URL
    "dma_path": "/management",  # Management API path
    "api_key_header": "X-Api-Key",  # API key header name
    "api_key": "ACA176440A8BDD3954FCEC3552BF8985AFB75608A57B9121EA809791854AAA2BEDBF85333572E8DECE9537D69697D6BA28EA26174085242CB536B7877E219CAC",  # PLACEHOLDER: Consumer API key
    "dataspace_version": "saturn",  # "jupiter" or "saturn"
    "bpn": "BPNL00000003CRHK"  # PLACEHOLDER: Consumer BPN
}

# Backend Data Source Configuration (for Provider Asset)
BACKEND_CONFIG = {
    "base_url": "https://storage-ichub.int.catena-x.net/urn:uuid:6e4ab8c0-b6a2-42f0-8b02-9e6a2a5a7fae",  # PLACEHOLDER: Backend API URL
}


def print_header(title: str):
    """Helper to print section headers"""
    print(f"\n{'=' * 80}")
    print(f"  {title}")
    print(f"{'=' * 80}\n")


def initialize_provider_service():
    """
    Initialize the Provider Connector Service following the Industry Core Hub pattern.
    
    Returns:
        ConnectorProviderService instance
    """
    print_header("Initializing Provider Connector Service")
    
    provider_headers = {
        PROVIDER_CONNECTOR_CONFIG["api_key_header"]: PROVIDER_CONNECTOR_CONFIG["api_key"],
        "Content-Type": "application/json"
    }
    
    provider_service = ServiceFactory.get_connector_provider_service(
        dataspace_version=PROVIDER_CONNECTOR_CONFIG["dataspace_version"],
        base_url=PROVIDER_CONNECTOR_CONFIG["base_url"],
        dma_path=PROVIDER_CONNECTOR_CONFIG["dma_path"],
        headers=provider_headers,
        verbose=True,
        verify_ssl=False  # Disable SSL verification for INT environment with self-signed certificates
    )
    
    print(f"✓ Provider service initialized")
    print(f"  - Base URL: {PROVIDER_CONNECTOR_CONFIG['base_url']}")
    print(f"  - Dataspace Version: {PROVIDER_CONNECTOR_CONFIG['dataspace_version']}")
    print(f"  - BPN: {PROVIDER_CONNECTOR_CONFIG['bpn']}")
    
    return provider_service


def initialize_consumer_service(connection_manager=None):
    """
    Initialize the Consumer Connector Service following the Industry Core Hub pattern.
    
    Args:
        connection_manager: Optional connection manager for EDR caching
        
    Returns:
        ConnectorConsumerService instance
    """
    print_header("Initializing Consumer Connector Service")
    
    consumer_headers = {
        CONSUMER_CONNECTOR_CONFIG["api_key_header"]: CONSUMER_CONNECTOR_CONFIG["api_key"],
        "Content-Type": "application/json"
    }
    
    consumer_service = ServiceFactory.get_connector_consumer_service(
        dataspace_version=CONSUMER_CONNECTOR_CONFIG["dataspace_version"],
        base_url=CONSUMER_CONNECTOR_CONFIG["base_url"],
        dma_path=CONSUMER_CONNECTOR_CONFIG["dma_path"],
        headers=consumer_headers,
        connection_manager=connection_manager,
        verbose=True,
        verify_ssl=False  # Disable SSL verification for INT environment with self-signed certificates
    )
    
    print(f"✓ Consumer service initialized")
    print(f"  - Base URL: {CONSUMER_CONNECTOR_CONFIG['base_url']}")
    print(f"  - Dataspace Version: {CONSUMER_CONNECTOR_CONFIG['dataspace_version']}")
    print(f"  - BPN: {CONSUMER_CONNECTOR_CONFIG['bpn']}")
    
    return consumer_service


def provision_data_on_provider(provider_service:BaseConnectorProviderService):
    """
    Phase 1: Provider provisions data by creating Asset, Policies, and Contract Definition.
    
    Args:
        provider_service: Initialized ConnectorProviderService
        
    Returns:
        dict: Contains asset_id, access_policy_id, usage_policy_id, contract_def_id
    """
    print_header("PHASE 1: Provider Data Provision")
    
    # Generate unique IDs with timestamp
    timestamp = int(time.time())
    asset_id = f"vehicle-production-data-{timestamp}"
    access_policy_id = f"access-policy-bpn-{timestamp}"
    usage_policy_id = f"usage-policy-framework-{timestamp}"
    contract_def_id = f"contract-def-{timestamp}"
    
    print("Step 1.1: Creating Access Policy (BPN-based)")
    print("-" * 80)
    
    # Create Access Policy - Controls who can see the asset in catalog
    try:
        access_policy_response = provider_service.create_policy(
            policy_id=access_policy_id,
            permissions=[{
                "action": "access",
                "constraint": {
                    "leftOperand": "BusinessPartnerNumber",
                    "operator": "isAnyOf",
                    "rightOperand": CONSUMER_CONNECTOR_CONFIG["bpn"]
                }
            }]
        )
        print(f"✓ Access Policy created: {access_policy_id}")
        print(f"  - Restricts catalog visibility to BPN: {CONSUMER_CONNECTOR_CONFIG['bpn']}")
        print(f"  - Response: {json.dumps(access_policy_response, indent=2)}")
    except Exception as e:
        print(f"✗ Failed to create access policy: {e}")
        import traceback
        traceback.print_exc()
        raise
    
    print("\nStep 1.2: Creating Usage Policy (Framework Agreement)")
    print("-" * 80)
    
    # Create Usage Policy - Controls contract negotiation terms
    try:
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
                        },
                        {
                            "leftOperand": "UsagePurpose",
                            "operator": "isAnyOf",
                            "rightOperand": [
                                "cx.core.industrycore:1",
                                "cx.circular.dpp:1"
                            ]
                        },
                    ]
                }
            }]
        )
        print(f"✓ Usage Policy created: {usage_policy_id}")
        print(f"  - Requires: Active Membership")
        print(f"  - Requires: Framework Agreement DataExchangeGovernance:1.0")
    except Exception as e:
        print(f"✗ Failed to create usage policy: {e}")
        raise
    
    print("\nStep 1.3: Creating Asset (Backend Data Source)")
    print("-" * 80)
    
    # Create Asset with backend data source configuration
    try:
        asset_response = provider_service.create_asset(
            asset_id=asset_id,
            base_url=BACKEND_CONFIG["base_url"],
            dct_type="https://w3id.org/catenax/taxonomy#Submodel",
            semantic_id="urn:samm:io.catenax.business_partner_certificate:3.1.0#BusinessPartnerCertificate",
            version="1.0",
            proxy_params={
                "proxyQueryParams": "true",
                "proxyPath": "true",
                "proxyMethod": "true",
                "proxyBody": "false"
            },
        )
        print(f"✓ Asset created: {asset_id}")
        print(f"  - Backend URL: {BACKEND_CONFIG['base_url']}")
        print(f"  - Type: Submodel")
        print(f"  - Version: 1.0")
    except Exception as e:
        print(f"✗ Failed to create asset: {e}")
        raise
    
    print("\nStep 1.4: Creating Contract Definition")
    print("-" * 80)
    
    # Create Contract Definition - Links Asset with Policies
    try:
        contract_def_response = provider_service.create_contract(
            contract_id=contract_def_id,
            usage_policy_id=usage_policy_id,
            access_policy_id=access_policy_id,
            asset_id=asset_id
        )
        print(f"✓ Contract Definition created: {contract_def_id}")
        print(f"  - Asset: {asset_id}")
        print(f"  - Access Policy: {access_policy_id}")
        print(f"  - Usage Policy: {usage_policy_id}")
    except Exception as e:
        print(f"✗ Failed to create contract definition: {e}")
        raise
    
    print("\n" + "=" * 80)
    print("✓ Data Provision Complete!")
    print("=" * 80)
    print(f"Provider has made the data available in the dataspace:")
    print(f"  - Asset ID: {asset_id}")
    print(f"  - Visible to: {CONSUMER_CONNECTOR_CONFIG['bpn']}")
    print(f"  - Contract Terms: Active Membership + Framework Agreement")
    
    return {
        "asset_id": asset_id,
        "access_policy_id": access_policy_id,
        "usage_policy_id": usage_policy_id,
        "contract_def_id": contract_def_id
    }


def consume_data_as_consumer(consumer_service, asset_id):
    """
    Phase 2: Consumer discovers and consumes data from Provider.
    
    Args:
        consumer_service: Initialized ConnectorConsumerService
        asset_id: The asset ID to consume
        
    Returns:
        dict: Contains edr_data with endpoint and authorization token
    """
    print_header("PHASE 2: Consumer Data Consumption")
    
    print("Step 2.1: Discovering Provider Catalog")
    print("-" * 80)
    
    # Request Catalog from Provider
    try:
        catalog_response = consumer_service.get_catalog_with_bpnl(
            bpnl=PROVIDER_CONNECTOR_CONFIG["bpn"],
            counter_party_address=PROVIDER_CONNECTOR_CONFIG["dsp_url"]
        )
        
        if catalog_response.status_code != 200:
            raise Exception(f"Catalog request failed with status {catalog_response.status_code}")
        
        catalog_data = catalog_response.json()
        datasets = catalog_data.get("dcat:dataset", [])
        
        print(f"✓ Catalog received from Provider")
        print(f"  - Provider BPN: {PROVIDER_CONNECTOR_CONFIG['bpn']}")
        print(f"  - Total datasets: {len(datasets)}")
        
        # Find our target asset
        target_dataset = None
        for dataset in datasets:
            if dataset.get("@id") == asset_id:
                target_dataset = dataset
                break
        
        if target_dataset is None:
            raise Exception(f"Asset {asset_id} not found in catalog")
        
        # Extract offer details
        offer_policy = target_dataset["odrl:hasPolicy"]
        offer_id = offer_policy["@id"]
        
        print(f"  - Found asset: {asset_id}")
        print(f"  - Offer ID: {offer_id}")
        
    except Exception as e:
        print(f"✗ Failed to get catalog: {e}")
        raise
    
    print("\nStep 2.2: Negotiating Contract")
    print("-" * 80)
    
    # Prepare contract negotiation
    try:
        from tractusx_sdk.dataspace.models.connector.model_factory import ModelFactory
        
        # Prepare ODRL context for Saturn
        negotiation_context = [
            "https://w3id.org/catenax/2025/9/policy/odrl.jsonld",
            "https://w3id.org/catenax/2025/9/policy/context.jsonld",
            {
                "@vocab": "https://w3id.org/edc/v0.0.1/ns/"
            }
        ]
        
        # Extract policy from offer
        offer_policy_data = {
            "permission": offer_policy.get("odrl:permission", []),
            "prohibition": offer_policy.get("odrl:prohibition", []),
            "obligation": offer_policy.get("odrl:obligation", [])
        }
        
        # Create contract negotiation request
        contract_negotiation = ModelFactory.get_contract_negotiation_model(
            dataspace_version=CONSUMER_CONNECTOR_CONFIG["dataspace_version"],
            counter_party_address=PROVIDER_CONNECTOR_CONFIG["dsp_url"],
            offer_id=offer_id,
            asset_id=asset_id,
            provider_id=PROVIDER_CONNECTOR_CONFIG["bpn"],
            offer_policy=offer_policy_data,
            context=negotiation_context,
            protocol="dataspace-protocol-http:2025-1"
        )
        
        # Submit negotiation
        negotiation_response = consumer_service.contract_negotiations.create(obj=contract_negotiation)
        
        if negotiation_response.status_code != 200:
            raise Exception(f"Contract negotiation failed with status {negotiation_response.status_code}")
        
        negotiation_data = negotiation_response.json()
        negotiation_id = negotiation_data.get("@id")
        
        print(f"✓ Contract negotiation initiated: {negotiation_id}")
        print(f"  - Asset: {asset_id}")
        print(f"  - Provider: {PROVIDER_CONNECTOR_CONFIG['bpn']}")
        
    except Exception as e:
        print(f"✗ Failed to negotiate contract: {e}")
        raise
    
    print("\nStep 2.3: Waiting for Contract Agreement")
    print("-" * 80)
    
    # Poll negotiation status until FINALIZED
    max_wait = 60  # seconds
    poll_interval = 2  # seconds
    elapsed = 0
    contract_agreement_id = None
    
    try:
        print("Polling negotiation state...", end="", flush=True)
        
        while elapsed < max_wait:
            time.sleep(poll_interval)
            elapsed += poll_interval
            
            status_response = consumer_service.contract_negotiations.get(negotiation_id)
            if status_response.status_code == 200:
                status_data = status_response.json()
                state = status_data.get("state", status_data.get("edc:state"))
                
                print(f" {state}", end="", flush=True)
                
                if state == "FINALIZED":
                    contract_agreement_id = status_data.get("contractAgreementId", 
                                                            status_data.get("edc:contractAgreementId"))
                    print(f"\n✓ Contract Agreement finalized: {contract_agreement_id}")
                    break
            
            if elapsed >= max_wait:
                raise Exception("Contract negotiation timeout")
        
        if contract_agreement_id is None:
            raise Exception("Contract agreement ID not received")
            
    except Exception as e:
        print(f"\n✗ Contract negotiation failed: {e}")
        raise
    
    print("\nStep 2.4: Initiating Transfer Process")
    print("-" * 80)
    
    # Start transfer process
    try:
        transfer_request = ModelFactory.get_transfer_process_model(
            dataspace_version=CONSUMER_CONNECTOR_CONFIG["dataspace_version"],
            counter_party_address=PROVIDER_CONNECTOR_CONFIG["dsp_url"],
            contract_id=contract_agreement_id,
            transfer_type="HttpData-PULL",
            protocol="dataspace-protocol-http:2025-1",
            data_destination={
                "type": "HttpProxy"
            }
        )
        
        transfer_response = consumer_service.transfer_processes.create(obj=transfer_request)
        
        if transfer_response.status_code != 200:
            raise Exception(f"Transfer process failed with status {transfer_response.status_code}")
        
        transfer_data = transfer_response.json()
        transfer_id = transfer_data.get("@id")
        
        print(f"✓ Transfer process initiated: {transfer_id}")
        print(f"  - Type: HttpData-PULL")
        print(f"  - Contract: {contract_agreement_id}")
        
    except Exception as e:
        print(f"✗ Failed to start transfer: {e}")
        raise
    
    print("\nStep 2.5: Waiting for EDR (Endpoint Data Reference)")
    print("-" * 80)
    
    # Poll for EDR availability
    elapsed = 0
    edr_data = None
    
    try:
        print("Waiting for EDR...", end="", flush=True)
        
        while elapsed < max_wait:
            time.sleep(poll_interval)
            elapsed += poll_interval
            
            # Check transfer state
            transfer_status = consumer_service.transfer_processes.get(transfer_id)
            if transfer_status.status_code == 200:
                transfer_state_data = transfer_status.json()
                state = transfer_state_data.get("state", transfer_state_data.get("edc:state"))
                
                print(f" {state}", end="", flush=True)
                
                if state in ["STARTED", "COMPLETED"]:
                    # Try to get EDR
                    edr_response = consumer_service.edrs.get_for_transfer(transfer_id)
                    if edr_response.status_code == 200:
                        edr_data = edr_response.json()
                        print(f"\n✓ EDR received!")
                        break
            
            if elapsed >= max_wait:
                raise Exception("EDR retrieval timeout")
        
        if edr_data is None:
            raise Exception("EDR not available")
        
        # Extract EDR details
        dataplane_url = edr_data.get("endpoint", edr_data.get("edc:endpoint"))
        access_token = edr_data.get("authorization", edr_data.get("edc:authorization"))
        
        print(f"  - Endpoint: {dataplane_url}")
        print(f"  - Token: {access_token[:30]}..." if access_token else "  - Token: None")
        
    except Exception as e:
        print(f"\n✗ Failed to get EDR: {e}")
        raise
    
    print("\n" + "=" * 80)
    print("✓ Data Consumption Complete!")
    print("=" * 80)
    print(f"Consumer can now access Provider's data:")
    print(f"  - Endpoint: {dataplane_url}")
    print(f"  - Authorization header required with token")
    print(f"  - Make HTTP requests to access the data")
    
    return {
        "edr_data": edr_data,
        "dataplane_url": dataplane_url,
        "access_token": access_token,
        "transfer_id": transfer_id,
        "contract_agreement_id": contract_agreement_id
    }


def access_data_with_edr(dataplane_url, access_token, path="/"):
    """
    Phase 3: Access actual data using the EDR.
    
    Args:
        dataplane_url: The data plane endpoint from EDR
        access_token: The authorization token from EDR
        path: Optional path to append to the endpoint
        
    Returns:
        Response from the data plane
    """
    print_header("PHASE 3: Accessing Data with EDR")
    
    import requests
    
    try:
        print(f"Making request to: {dataplane_url}{path}")
        
        response = requests.get(
            f"{dataplane_url}{path}",
            headers={
                "Authorization": access_token
            },
            verify=True,  # Set to False for self-signed certs in dev environments
            timeout=30
        )
        
        print(f"✓ Response received: HTTP {response.status_code}")
        
        if response.status_code == 200:
            print(f"  - Content-Type: {response.headers.get('Content-Type', 'unknown')}")
            print(f"  - Content-Length: {len(response.content)} bytes")
            
            # Try to parse as JSON
            try:
                data = response.json()
                print(f"\nData preview:")
                print(json.dumps(data, indent=2)[:500] + "..." if len(json.dumps(data)) > 500 else json.dumps(data, indent=2))
            except:
                print(f"\nRaw data preview:")
                print(response.text[:500] + "..." if len(response.text) > 500 else response.text)
        else:
            print(f"✗ Request failed: {response.text}")
        
        return response
        
    except Exception as e:
        print(f"✗ Failed to access data: {e}")
        raise


def cleanup_provider_resources(provider_service, provision_ids):
    """
    Cleanup: Delete all created resources from Provider.
    
    Args:
        provider_service: Initialized ConnectorProviderService
        provision_ids: Dict containing resource IDs to delete
    """
    print_header("CLEANUP: Deleting Provider Resources")
    
    # Delete in reverse order of creation
    resources = [
        ("Contract Definition", provision_ids["contract_def_id"], provider_service.contract_definitions),
        ("Asset", provision_ids["asset_id"], provider_service.assets),
        ("Usage Policy", provision_ids["usage_policy_id"], provider_service.policies),
        ("Access Policy", provision_ids["access_policy_id"], provider_service.policies)
    ]
    
    for resource_type, resource_id, controller in resources:
        try:
            controller.delete(resource_id)
            print(f"✓ Deleted {resource_type}: {resource_id}")
        except Exception as e:
            print(f"✗ Failed to delete {resource_type} {resource_id}: {e}")


def main():
    """
    Main execution flow: Provider provisions data, Consumer consumes it.
    """
    print("\n")
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 78 + "║")
    print("║" + "  Saturn Connector Services - E2E Data Exchange Example".center(78) + "║")
    print("║" + "  Provider Data Provision → Consumer Data Consumption".center(78) + "║")
    print("║" + " " * 78 + "║")
    print("╚" + "=" * 78 + "╝")
    
    provision_ids = None
    
    try:
        # Initialize services
        provider_service = initialize_provider_service()
        consumer_service = initialize_consumer_service()
        
        # Phase 1: Provider provisions data
        provision_ids = provision_data_on_provider(provider_service)
        
        # Give provider EDC time to process and propagate changes
        print("\nWaiting 3 seconds for Provider EDC to process...")
        time.sleep(3)
        
        # Phase 2: Consumer discovers and consumes data
        consumption_result = consume_data_as_consumer(
            consumer_service,
            asset_id=provision_ids["asset_id"]
        )
        
        # Phase 3: Access actual data (optional - uncomment to test)
        # access_data_with_edr(
        #     dataplane_url=consumption_result["dataplane_url"],
        #     access_token=consumption_result["access_token"]
        # )
        
        print_header("SUCCESS - Complete E2E Flow Executed")
        print("Provider successfully provisioned data:")
        print(f"  ✓ Asset: {provision_ids['asset_id']}")
        print(f"  ✓ Policies: {provision_ids['access_policy_id']}, {provision_ids['usage_policy_id']}")
        print(f"  ✓ Contract Definition: {provision_ids['contract_def_id']}")
        
        print("\nConsumer successfully consumed data:")
        print(f"  ✓ Catalog discovered")
        print(f"  ✓ Contract negotiated: {consumption_result['contract_agreement_id']}")
        print(f"  ✓ Transfer initiated: {consumption_result['transfer_id']}")
        print(f"  ✓ EDR obtained for data access")
        
    except Exception as e:
        print(f"\n✗ E2E flow failed: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Cleanup (optional - uncomment to clean up resources)
        # if provision_ids:
        #     cleanup_provider_resources(provider_service, provision_ids)
        pass


if __name__ == "__main__":
    print("\n⚠️  IMPORTANT: Update the PLACEHOLDER values before running!")
    print("=" * 80)
    print("Required configuration:")
    print("  1. Provider connector URL, API key, BPN, DSP URL")
    print("  2. Consumer connector URL, API key, BPN")
    print("  3. Backend data source URL and OAuth2 credentials")
    print("\nSee configuration section at the top of this file.")
    print("=" * 80)
    
    # Uncomment to run (after updating placeholders)
    main()
    
    print("\n✓ Example script loaded successfully!")
    print("Update placeholders and uncomment main() call to execute.")
