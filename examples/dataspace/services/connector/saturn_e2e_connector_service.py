#################################################################################
# Eclipse Tractus-X - Software Development KIT
#
# Copyright (c) 2026 Catena-X Automotive Network e.V.
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
import argparse
import time
import json
import logging
import os
import sys
import uuid
from datetime import datetime

# Configure logging to both console and timestamped log file
_run_timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
_log_dir = os.path.dirname(os.path.abspath(__file__))
_log_file = os.path.join(_log_dir, f"saturn_e2e_run_{_run_timestamp}.log")
_log_format = "%(asctime)s %(levelname)s [%(name)s] %(message)s"
_file_handler = logging.FileHandler(_log_file, mode="w", encoding="utf-8")
_file_handler.setLevel(logging.INFO)
_file_handler.setFormatter(logging.Formatter(_log_format))
_console_handler = logging.StreamHandler(sys.stdout)
_console_handler.setLevel(logging.INFO)
_console_handler.setFormatter(logging.Formatter(_log_format))
logging.basicConfig(level=logging.INFO, handlers=[_console_handler, _file_handler], force=True)
# Module-level logger for this example script
logger = logging.getLogger("saturn_e2e")
logger.info("Logging to file: %s", _log_file)

def _finalize_log(result: str):
    """Flush and close log handlers, then rename log file with PASS or FAIL result."""
    global _log_file
    for handler in logging.root.handlers[:]:
        handler.flush()
        handler.close()
    final_log = _log_file.replace(".log", f"_{result}.log")
    os.rename(_log_file, final_log)
    sys.stdout.write(f"Log saved as: {final_log}\n")
    sys.stdout.flush()


PROVIDER_CONNECTOR_CONFIG = {
    "base_url": "https://edc-provider-ichub-control.test.io",  # PLACEHOLDER: Provider EDC Control Plane URL
    "dma_path": "/management",  # Management API path
    "api_key_header": "X-Api-Key",  # API key header name
    "api_key": "",  # PLACEHOLDER: Provider API key
    "dataspace_version": "saturn",  # "jupiter" or "saturn"
    "bpn": "BPNL0000000093Q7",  # PLACEHOLDER: Provider BPN
    "dsp_url": "https://edc-provider-ichub-control.test.io/api/v1/dsp"  # PLACEHOLDER: Provider DSP base URL — do NOT include the protocol version suffix (e.g. /2025-01), the consumer EDC appends it internally
}

# Consumer Connector Configuration
CONSUMER_CONNECTOR_CONFIG = {
    "base_url": "https://edc-consumer-ichub-control.test.io",  # PLACEHOLDER: Consumer EDC Control Plane URL
    "dma_path": "/management",  # Management API path
    "api_key_header": "X-Api-Key",  # API key header name
    "api_key": "",  # PLACEHOLDER: Consumer API key
    "dataspace_version": "saturn",  # "jupiter" or "saturn"
    "bpn": "BPNL00000003CRHK"  # PLACEHOLDER: Consumer BPN
}

# Backend Data Source Configuration (for Provider Asset)
BACKEND_CONFIG = {
    "base_url": f"https://storage-ichub.test.io/urn:uuid:{uuid.uuid4()}",  # UUID generated fresh per test run
}

# Sample BusinessPartnerCertificate aspect model data to upload to the backend
SAMPLE_ASPECT_MODEL_DATA = {
    "businessPartnerNumber": "BPNL00000003AYRE",
    "enclosedSites": [
        {
            "areaOfApplication": "Development, Marketing und Sales and also Procurement for interior components",
            "enclosedSiteBpn": "BPNS00000003AYRE"
        }
    ],
    "registrationNumber": "12 198 54182 TMS",
    "uploader": "BPNL00000003AYRE",
    "document": {
        "documentID": "UUID--123456789",
        "creationDate": "2024-08-23T13:19:00.280+02:00",
        "contentType": "application/pdf",
        "contentBase64": "iVBORw0KGgoAAdsfwerTETEfdgd"
    },
    "validator": {
        "validatorName": "Data service provider X",
        "validatorBpn": "BPNL00000007YREZ"
    },
    "validUntil": "2026-01-24",
    "validFrom": "2023-01-25",
    "trustLevel": "none",
    "type": {
        "certificateVersion": "2015",
        "certificateType": "ISO9001"
    },
    "areaOfApplication": "Development, Marketing und Sales and also Procurement for interior components",
    "issuer": {
        "issuerName": "TÜV",
        "issuerBpn": "BPNL133631123120"
    }
}


def print_header(title: str):
    """Helper to log section headers"""
    logger.info("\n%s\n  %s\n%s", "=" * 80, title, "=" * 80)


def upload_sample_data_to_backend():
    """
    Phase 0: Upload sample aspect model data to the backend storage before provisioning.
    This ensures the backend has data for the provider asset to serve.
    """
    import requests

    print_header("PHASE 0: Uploading Sample Data to Backend Storage")

    headers = {
        "Content-Type": "application/json"
    }
    payload = json.dumps(SAMPLE_ASPECT_MODEL_DATA, indent=2)

    logger.info("Uploading BusinessPartnerCertificate aspect model to: %s", BACKEND_CONFIG['base_url'])
    logger.info("[UPLOAD REQUEST]:\n%s", payload)

    try:
        response = requests.post(
            BACKEND_CONFIG["base_url"],
            data=payload,
            headers=headers,
            verify=False,
            timeout=30
        )
        logger.info("[UPLOAD RESPONSE] Status: %s", response.status_code)
        logger.info("[UPLOAD RESPONSE] Body:\n%s", response.text)

        if response.status_code not in (200, 201, 204):
            raise Exception(f"Backend upload failed with status {response.status_code}: {response.text}")

        logger.info("✓ Sample data uploaded successfully to backend storage")
    except Exception as e:
        logger.exception("✗ Failed to upload sample data: %s", e)
        raise


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
        verify_ssl=False,  # Disable SSL verification for INT environment with self-signed certificates
        logger=logger,
    )
    
    logger.info("✓ Provider service initialized")
    logger.info("  - Base URL: %s", PROVIDER_CONNECTOR_CONFIG['base_url'])
    logger.info("  - Dataspace Version: %s", PROVIDER_CONNECTOR_CONFIG['dataspace_version'])
    logger.info("  - BPN: %s", PROVIDER_CONNECTOR_CONFIG['bpn'])
    
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
        verify_ssl=False,  # Disable SSL verification for INT environment with self-signed certificates
        logger=logger,
    )
    
    logger.info("✓ Consumer service initialized")
    logger.info("  - Base URL: %s", CONSUMER_CONNECTOR_CONFIG['base_url'])
    logger.info("  - Dataspace Version: %s", CONSUMER_CONNECTOR_CONFIG['dataspace_version'])
    logger.info("  - BPN: %s", CONSUMER_CONNECTOR_CONFIG['bpn'])
    
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
    
    logger.info("Step 1.1: Creating Access Policy (BPN-based)")
    logger.info("%s", "-" * 80)
    
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
        logger.info("✓ Access Policy created: %s", access_policy_id)
        logger.info("  - Restricts catalog visibility to BPN: %s", CONSUMER_CONNECTOR_CONFIG['bpn'])
        logger.info("  - Response: %s", json.dumps(access_policy_response, indent=2))
    except Exception as e:
        logger.exception("✗ Failed to create access policy: %s", e)
        raise
    
    logger.info("\nStep 1.2: Creating Usage Policy (Framework Agreement)")
    logger.info("%s", "-" * 80)
    
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
                            "rightOperand": "cx.core.industrycore:1",
                        },
                    ]
                }
            }]
        )
        logger.info("✓ Usage Policy created: %s", usage_policy_id)
        logger.info("  - Requires: Active Membership")
        logger.info("  - Requires: Framework Agreement DataExchangeGovernance:1.0")
        logger.info("  - Response: %s", json.dumps(usage_policy_response, indent=2))
    except Exception as e:
        logger.exception("✗ Failed to create usage policy: %s", e)
        raise
    
    logger.info("\nStep 1.3: Creating Asset (Backend Data Source)")
    logger.info("%s", "-" * 80)
    
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
        logger.info("✓ Asset created: %s", asset_id)
        logger.info("  - Backend URL: %s", BACKEND_CONFIG['base_url'])
        logger.info("  - Type: Submodel")
        logger.info("  - Version: 1.0")
        logger.info("  - Response: %s", json.dumps(asset_response, indent=2))
    except Exception as e:
        logger.exception("✗ Failed to create asset: %s", e)
        raise
    
    logger.info("\nStep 1.4: Creating Contract Definition")
    logger.info("%s", "-" * 80)
    
    # Create Contract Definition - Links Asset with Policies
    try:
        contract_def_response = provider_service.create_contract(
            contract_id=contract_def_id,
            usage_policy_id=usage_policy_id,
            access_policy_id=access_policy_id,
            asset_id=asset_id
        )
        logger.info("✓ Contract Definition created: %s", contract_def_id)
        logger.info("  - Asset: %s", asset_id)
        logger.info("  - Access Policy: %s", access_policy_id)
        logger.info("  - Usage Policy: %s", usage_policy_id)
        logger.info("  - Response: %s", json.dumps(contract_def_response, indent=2))
    except Exception as e:
        logger.exception("✗ Failed to create contract definition: %s", e)
        raise
    
    logger.info("\n%s", "=" * 80)
    logger.info("✓ Data Provision Complete!")
    logger.info("%s", "=" * 80)
    logger.info("Provider has made the data available in the dataspace:")
    logger.info("  - Asset ID: %s", asset_id)
    logger.info("  - Visible to: %s", CONSUMER_CONNECTOR_CONFIG['bpn'])
    logger.info("  - Contract Terms: Active Membership + Framework Agreement")
    
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
    
    logger.info("Step 2.0: Discovering Connector Info via BPNL")
    logger.info("%s", "-" * 80)

    try:
        discovered_address, discovered_id, discovered_protocol = consumer_service.get_discovery_info(
            bpnl=PROVIDER_CONNECTOR_CONFIG["bpn"],
            counter_party_address=PROVIDER_CONNECTOR_CONFIG["dsp_url"]
        )
        logger.info("✓ Connector discovery successful:")
        logger.info("  - Counter Party Address : %s", discovered_address)
        logger.info("  - Counter Party ID      : %s", discovered_id)
        logger.info("  - Protocol              : %s", discovered_protocol)
    except Exception as e:
        logger.exception("✗ Connector discovery failed: %s", e)
        raise

    logger.info("\nStep 2.1: Discovering Provider Catalog")
    logger.info("%s", "-" * 80)
    
    # Request Catalog from Provider
    try:
        catalog_data = consumer_service.get_catalog_by_asset_id_with_bpnl(
            bpnl=PROVIDER_CONNECTOR_CONFIG["bpn"],
            counter_party_address=PROVIDER_CONNECTOR_CONFIG["dsp_url"],
            asset_id=asset_id
        )
        
        datasets = catalog_data.get("dataset", [])
        if isinstance(datasets, dict):
            datasets = [datasets]
        logger.info("[CATALOG RESPONSE]:\n%s", json.dumps(catalog_data, indent=2))
        
        # Extract participantId from catalog response
        participant_id = catalog_data.get("participantId", catalog_data.get("participantId", PROVIDER_CONNECTOR_CONFIG["bpn"]))
        logger.info("  - Participant ID from catalog: %s", participant_id)

        # Extract DSP endpoint URL from catalog service
        dsp_endpoint = PROVIDER_CONNECTOR_CONFIG["dsp_url"]  # fallback
        services = catalog_data.get("service", [])
        if isinstance(services, dict):
            services = [services]
        for service in services:
            if service.get("@type") == "DataService" and service.get("endpointURL"):
                dsp_endpoint = service["endpointURL"]
                break
        logger.info("  - DSP endpoint from catalog: %s", dsp_endpoint)
        
        logger.info("✓ Catalog received from Provider")
        logger.info("  - Provider BPN: %s", PROVIDER_CONNECTOR_CONFIG['bpn'])
        logger.info("  - Total datasets: %s", len(datasets))
        
        # Find our target asset
        target_dataset = None
        for dataset in datasets:
            if dataset.get("@id") == asset_id:
                target_dataset = dataset
                break
        
        if target_dataset is None:
            raise Exception(f"Asset {asset_id} not found in catalog")
        
        # Extract offer details
        offer_policy = target_dataset["hasPolicy"][0]
        offer_id = offer_policy["@id"]
        
        logger.info("  - Found asset: %s", asset_id)
        logger.info("  - Offer ID: %s", offer_id)
        
    except Exception as e:
        logger.exception("✗ Failed to get catalog: %s", e)
        raise
    
    logger.info("\nStep 2.2: Negotiating Contract")
    logger.info("%s", "-" * 80)
    
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
            "permission": offer_policy.get("permission", []),
            "prohibition": offer_policy.get("prohibition", []),
            "obligation": offer_policy.get("obligation", [])
        }
        
        # Create contract negotiation request
        contract_negotiation = ModelFactory.get_contract_negotiation_model(
            dataspace_version=CONSUMER_CONNECTOR_CONFIG["dataspace_version"],
            counter_party_address=dsp_endpoint,
            offer_id=offer_id,
            asset_id=asset_id,
            provider_id=participant_id,
            offer_policy=offer_policy_data,
            context=negotiation_context,
            protocol="dataspace-protocol-http:2025-1"
        )
        
        logger.info("[NEGOTIATION REQUEST]:\n%s", contract_negotiation.to_data())

        # Submit negotiation
        negotiation_response = consumer_service.contract_negotiations.create(obj=contract_negotiation)

        logger.info("[NEGOTIATION RESPONSE] Status: %s", negotiation_response.status_code)
        logger.info("[NEGOTIATION RESPONSE] Body:\n%s", json.dumps(negotiation_response.json(), indent=2))

        if negotiation_response.status_code != 200:
            raise Exception(f"Contract negotiation failed with status {negotiation_response.status_code}")
        
        negotiation_data = negotiation_response.json()
        negotiation_id = negotiation_data.get("@id")
        
        logger.info("✓ Contract negotiation initiated: %s", negotiation_id)
        logger.info("  - Asset: %s", asset_id)
        logger.info("  - Provider: %s", participant_id)
        
    except Exception as e:
        logger.exception("✗ Failed to negotiate contract: %s", e)
        raise
    
    logger.info("\nStep 2.3: Waiting for Contract Agreement")
    logger.info("%s", "-" * 80)
    
    # Poll negotiation status until FINALIZED
    max_wait = 60  # seconds
    poll_interval = 2  # seconds
    elapsed = 0
    contract_agreement_id = None
    
    try:
        logger.info("Polling negotiation state...")
        
        while elapsed < max_wait:
            time.sleep(poll_interval)
            elapsed += poll_interval
            
            status_response = consumer_service.contract_negotiations.get_by_id(negotiation_id)
            if status_response.status_code == 200:
                status_data = status_response.json()
                state = status_data.get("state", status_data.get("edc:state"))
                
                logger.info("  Negotiation state: %s", state)
                
                if state == "FINALIZED":
                    logger.info("[NEGOTIATION STATE RESPONSE]:\n%s", json.dumps(status_data, indent=2))
                    contract_agreement_id = status_data.get("contractAgreementId",
                                                            status_data.get("edc:contractAgreementId"))
                    logger.info("✓ Contract Agreement finalized: %s", contract_agreement_id)
                    break
                elif state == "TERMINATED":
                    logger.info("[NEGOTIATION STATE RESPONSE]:\n%s", json.dumps(status_data, indent=2))
                    raise Exception(f"Contract negotiation was TERMINATED")
            
            if elapsed >= max_wait:
                raise Exception("Contract negotiation timeout")
        
        if contract_agreement_id is None:
            raise Exception("Contract agreement ID not received")
            
    except Exception as e:
        logger.exception("\n✗ Contract negotiation failed: %s", e)
        raise
    
    logger.info("\nStep 2.4: Initiating Transfer Process")
    logger.info("%s", "-" * 80)
    
    # Start transfer process
    try:
        transfer_request = ModelFactory.get_transfer_process_model(
            dataspace_version=CONSUMER_CONNECTOR_CONFIG["dataspace_version"],
            counter_party_address=dsp_endpoint,
            contract_id=contract_agreement_id,
            transfer_type="HttpData-PULL",
            protocol="dataspace-protocol-http:2025-1",
            data_destination={
                "type": "HttpProxy"
            }
        )
        
        logger.info("[TRANSFER REQUEST]:\n%s", transfer_request.to_data())

        transfer_response = consumer_service.transfer_processes.create(obj=transfer_request)

        logger.info("[TRANSFER RESPONSE] Status: %s", transfer_response.status_code)
        logger.info("[TRANSFER RESPONSE] Body:\n%s", json.dumps(transfer_response.json(), indent=2))

        if transfer_response.status_code != 200:
            raise Exception(f"Transfer process failed with status {transfer_response.status_code}")
        
        transfer_data = transfer_response.json()
        transfer_id = transfer_data.get("@id")
        
        logger.info("✓ Transfer process initiated: %s", transfer_id)
        logger.info("  - Type: HttpData-PULL")
        logger.info("  - Contract: %s", contract_agreement_id)
        
    except Exception as e:
        logger.exception("✗ Failed to start transfer: %s", e)
        raise
    
    logger.info("\nStep 2.5: Waiting for EDR (Endpoint Data Reference)")
    logger.info("%s", "-" * 80)
    
    # Poll for EDR availability
    elapsed = 0
    edr_data = None
    
    try:
        logger.info("Waiting for EDR...")
        
        while elapsed < max_wait:
            time.sleep(poll_interval)
            elapsed += poll_interval
            
            # Check transfer state
            transfer_status = consumer_service.transfer_processes.get_by_id(transfer_id)
            if transfer_status.status_code == 200:
                transfer_state_data = transfer_status.json()
                state = transfer_state_data.get("state", transfer_state_data.get("edc:state"))
                
                logger.info("  Transfer state: %s", state)
                
                if state in ["STARTED", "COMPLETED"]:
                    # Try to get EDR data address by transfer process ID
                    edr_response = consumer_service.edrs.get_data_address(transfer_id)
                    logger.info("[EDR RESPONSE] Status: %s", edr_response.status_code)
                    logger.info("[EDR RESPONSE] Body:\n%s", json.dumps(edr_response.json(), indent=2))
                    if edr_response.status_code == 200:
                        edr_data = edr_response.json()
                        logger.info("✓ EDR received!")
                        break
                elif state == "TERMINATED":
                    raise Exception(f"Transfer process was TERMINATED")
            
            if elapsed >= max_wait:
                raise Exception("EDR retrieval timeout")
        
        if edr_data is None:
            raise Exception("EDR not available")
        
        # Extract EDR details
        dataplane_url = edr_data.get("endpoint", edr_data.get("edc:endpoint"))
        access_token = edr_data.get("authorization", edr_data.get("edc:authorization"))
        
        logger.info("  - Endpoint: %s", dataplane_url)
        logger.info("  - Token: %s...", access_token[:30] if access_token else None)
        
    except Exception as e:
        logger.exception("\n✗ Failed to get EDR: %s", e)
        raise
    
    logger.info("\n%s", "=" * 80)
    logger.info("✓ Data Consumption Complete!")
    logger.info("%s", "=" * 80)
    logger.info("Consumer can now access Provider's data:")
    logger.info("  - Endpoint: %s", dataplane_url)
    logger.info("  - Authorization header required with token")
    logger.info("  - Make HTTP requests to access the data")
    
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
        logger.info("Making request to: %s%s", dataplane_url, path)

        response = requests.get(
            f"{dataplane_url}{path}",
            headers={
                "Authorization": access_token
            },
            verify=False,  # Disable SSL verification for INT environment with self-signed certificates
            timeout=30
        )
        
        logger.info("✓ Response received: HTTP %s", response.status_code)
        
        if response.status_code == 200:
            logger.info("  - Content-Type: %s", response.headers.get('Content-Type', 'unknown'))
            logger.info("  - Content-Length: %s bytes", len(response.content))
            
            # Try to parse as JSON
            try:
                data = response.json()
                full_data = json.dumps(data, indent=2)
                logger.info("[DATA RESPONSE]:\n%s", full_data)
            except Exception:
                logger.info("[DATA RESPONSE (raw)]:\n%s", response.text)
        else:
            logger.error("✗ Request failed: %s", response.text)
        
        return response
        
    except Exception as e:
        logger.exception("✗ Failed to access data: %s", e)
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
            logger.info("✓ Deleted %s: %s", resource_type, resource_id)
        except Exception as e:
            logger.error("✗ Failed to delete %s %s: %s", resource_type, resource_id, e)


def _print_summary(steps: list[dict], overall_result: str, total_elapsed: float,
                   provision_ids: dict = None, consumption_result: dict = None):
    W = 80
    passed  = sum(1 for s in steps if s["result"] == "PASS")
    failed  = sum(1 for s in steps if s["result"] == "FAIL")
    skipped = sum(1 for s in steps if s["result"] == "SKIP")

    verdict_line = f"  RESULT: {overall_result}  |  {passed} passed  {failed} failed  {skipped} skipped  |  Total: {total_elapsed:.1f}s"

    col_name   = 45
    col_result =  6
    col_dur    =  8

    lines = [
        "",
        "╔" + "=" * (W - 2) + "╗",
        "║" + "  E2E TEST RUN SUMMARY".center(W - 2) + "║",
        "╠" + "=" * (W - 2) + "╣",
        "║" + f"  {'STEP':<{col_name}} {'RESULT':>{col_result}}  {'TIME':>{col_dur}}".ljust(W - 2) + "║",
        "║" + "  " + "-" * (W - 4) + "  ║"[:-2] + "║",
    ]
    for s in steps:
        icon   = "✓" if s["result"] == "PASS" else ("✗" if s["result"] == "FAIL" else "-")
        dur    = f"{s['duration_s']:.1f}s" if s["duration_s"] is not None else "  -"
        line   = f"  {icon} {s['name']:<{col_name - 2}} {s['result']:>{col_result}}  {dur:>{col_dur}}"
        lines.append("║" + line.ljust(W - 2) + "║")
    lines += [
        "╠" + "=" * (W - 2) + "╣",
        "║" + verdict_line.ljust(W - 2) + "║",
        "╚" + "=" * (W - 2) + "╝",
    ]
    if provision_ids or consumption_result:
        lines += ["", "  Resource IDs", "  " + "-" * 60]
    if provision_ids:
        lines += [
            f"  Asset ID          : {provision_ids.get('asset_id', '-')}",
            f"  Access Policy     : {provision_ids.get('access_policy_id', '-')}",
            f"  Usage Policy      : {provision_ids.get('usage_policy_id', '-')}",
            f"  Contract Def      : {provision_ids.get('contract_def_id', '-')}",
        ]
    if consumption_result:
        lines += [
            f"  Contract Agreement: {consumption_result.get('contract_agreement_id', '-')}",
            f"  Transfer ID       : {consumption_result.get('transfer_id', '-')}",
            f"  Dataplane URL     : {consumption_result.get('dataplane_url', '-')}",
        ]
    lines.append("")
    logger.info("\n".join(lines))


def main():
    """
    Main execution flow: Provider provisions data, Consumer consumes it.
    """
    logger.info(
        "\n\n%s\n%s\n%s\n%s\n%s\n%s",
        "╔" + "=" * 78 + "╗",
        "║" + " " * 78 + "║",
        "║" + "  Saturn Connector Services - E2E Data Exchange Example".center(78) + "║",
        "║" + "  Provider Data Provision → Consumer Data Consumption".center(78) + "║",
        "║" + " " * 78 + "║",
        "╚" + "=" * 78 + "╝",
    )

    provision_ids      = None
    consumption_result = None
    overall_result     = "FAIL"
    run_start          = time.time()

    # Track each step: {name, result, duration_s}
    steps: list[dict] = []

    def _run_step(name: str, fn):
        """Execute fn(), record timing and PASS/FAIL, return result or re-raise."""
        t0 = time.time()
        try:
            result = fn()
            steps.append({"name": name, "result": "PASS", "duration_s": time.time() - t0})
            return result
        except Exception as exc:
            steps.append({"name": name, "result": "FAIL", "duration_s": time.time() - t0})
            raise

    try:
        # Initialise services (not counted as test steps)
        provider_service = initialize_provider_service()
        consumer_service = initialize_consumer_service()

        # Phase 0
        _run_step("Phase 0 · Upload sample data to backend",
                  upload_sample_data_to_backend)

        # Phase 1
        provision_ids = _run_step("Phase 1 · Provider data provision",
                                  lambda: provision_data_on_provider(provider_service))

        logger.info("Waiting 3 seconds for Provider EDC to process...")
        time.sleep(3)

        # Phase 2
        consumption_result = _run_step(
            "Phase 2 · Consumer data consumption (catalog→negotiate→transfer→EDR)",
            lambda: consume_data_as_consumer(consumer_service, asset_id=provision_ids["asset_id"])
        )

        # Phase 3
        _run_step("Phase 3 · Access data with EDR",
                  lambda: access_data_with_edr(
                      dataplane_url=consumption_result["dataplane_url"],
                      access_token=consumption_result["access_token"]
                  ))

        overall_result = "PASS"

    except Exception as e:
        logger.exception("\n✗ E2E flow failed: %s", e)
        # Mark remaining phases as SKIP
        completed_phases = {s["name"] for s in steps}
        all_phases = [
            "Phase 0 · Upload sample data to backend",
            "Phase 1 · Provider data provision",
            "Phase 2 · Consumer data consumption (catalog→negotiate→transfer→EDR)",
            "Phase 3 · Access data with EDR",
        ]
        for phase in all_phases:
            if phase not in completed_phases:
                steps.append({"name": phase, "result": "SKIP", "duration_s": None})

    finally:
        total_elapsed = time.time() - run_start
        _print_summary(
            steps=steps,
            overall_result=overall_result,
            total_elapsed=total_elapsed,
            provision_ids=provision_ids,
            consumption_result=consumption_result,
        )
        # Flush the _Tee so the summary lands in the file before we close it
        sys.stdout.flush()
        # Cleanup (optional - uncomment to clean up resources)
        # if provision_ids:
        #     cleanup_provider_resources(provider_service, provision_ids)
        _finalize_log(overall_result)


if __name__ == "__main__":
    _parser = argparse.ArgumentParser(description="Saturn E2E connector service example")
    _parser.add_argument("--debug", action="store_true", help="Enable DEBUG-level logging (very verbose)")
    _args = _parser.parse_args()
    if _args.debug:
        logging.root.setLevel(logging.DEBUG)
        for _h in logging.root.handlers:
            _h.setLevel(logging.DEBUG)
        logger.info("DEBUG logging enabled")

    logger.warning(
        "\n⚠️  IMPORTANT: Update the PLACEHOLDER values before running!\n"
        "%s\n"
        "Required configuration:\n"
        "  1. Provider connector URL, API key, BPN, DSP URL\n"
        "  2. Consumer connector URL, API key, BPN\n"
        "  3. Backend data source URL and OAuth2 credentials\n"
        "\nSee configuration section at the top of this file.\n"
        "%s",
        "=" * 80,
        "=" * 80,
    )

    main()

    logger.info("\n✓ Example script loaded successfully!")
