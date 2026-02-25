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
End-to-End Example: Jupiter Connector Services - Data Provision and Consumption

This example demonstrates the complete flow from Provider data provision to Consumer
data consumption using the legacy DSP protocol ("dataspace-protocol-http", a.k.a.
Jupiter / EDC v0.8.x–0.10.x era).

Key differences from the Saturn equivalent (saturn_e2e_connector_service.py):
  - Protocol string : "dataspace-protocol-http"   (Saturn: "dataspace-protocol-http:2025-1")
  - ODRL context    : Tractus-X v1.0.0 + W3C URLs (Saturn: Catena-X 2025-9 URLs)
  - dataspace_version: "jupiter"                  (Saturn: "saturn")

Flow:
1. Provider provisions data (Asset + Policies + Contract Definition)
2. Consumer discovers available offers (Catalog Request via BPNL)
3. Consumer negotiates contract
4. Consumer initiates transfer
5. Consumer accesses data using EDR

For the simplified one-call version see: jupiter_simple_e2e.py
For the Saturn (DSP 2025-1) equivalent see: saturn_e2e_connector_service.py
"""

import argparse
import time
import json
import logging
import os
import sys
import uuid
from datetime import datetime

from tractusx_sdk.dataspace.services.connector import ServiceFactory
from tractusx_sdk.dataspace.services.connector.base_connector_provider import BaseConnectorProviderService
from tractusx_sdk.dataspace.services.connector.jupiter.connector_consumer_service import ConnectorConsumerService

# Configure logging to both console and timestamped log file
_test_case_name = "tck_e2e_jupiter_0-10-X_detailed"
_now = datetime.now()
_run_date = _now.strftime("%Y-%m-%d")
_run_time = _now.strftime("%H%M%S")
_script_dir = os.path.dirname(os.path.abspath(__file__))
_log_dir = os.path.join(_script_dir, "logs", _test_case_name, _run_date)
os.makedirs(_log_dir, exist_ok=True)
_log_file = os.path.join(_log_dir, f"{_run_time}_{_test_case_name}.log")
_log_format = "%(asctime)s %(levelname)s [%(name)s] %(message)s"
_file_handler = logging.FileHandler(_log_file, mode="w", encoding="utf-8")
_file_handler.setLevel(logging.INFO)
_file_handler.setFormatter(logging.Formatter(_log_format))
_console_handler = logging.StreamHandler(sys.stdout)
_console_handler.setLevel(logging.INFO)
_console_handler.setFormatter(logging.Formatter(_log_format))
logging.basicConfig(level=logging.INFO, handlers=[_console_handler, _file_handler], force=True)

logger = logging.getLogger(_test_case_name)
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


# ============================================================================
# CONFIGURATION — Replace with your actual values
# ============================================================================
# This TCK is designed for Eclipse Tractus-X EDC (https://github.com/eclipse-tractusx/tractusx-edc)
# Compatible EDC versions: 0.8.0 - 0.10.X (Jupiter Protocol)
#
# Backend: Uses simple-data-backend from Tractus-X Umbrella
#          https://github.com/eclipse-tractusx/tractus-x-umbrella/tree/main/simple-data-backend

PROVIDER_CONNECTOR_CONFIG = {
    "base_url": "http://dataprovider-controlplane.tx.test",  # Tractus-X Umbrella reference: tx-data-provider EDC Control Plane
    "dma_path": "/management",  # Management API path
    "api_key_header": "X-Api-Key",  # API key header name
    "api_key": "TEST2",  # Umbrella Provider API key from values.yaml
    "dataspace_version": "jupiter",  # "jupiter" or "saturn"
    "bpn": "BPNL00000003AYRE",  # Umbrella Provider BPN (tx-data-provider)
    "dsp_url": "http://dataprovider-controlplane.tx.test/api/v1/dsp"  # Provider DSP base URL — do NOT include the protocol version suffix (e.g. /2025-01), the consumer EDC appends it internally
}

# Consumer Connector Configuration
CONSUMER_CONNECTOR_CONFIG = {
    "base_url": "http://dataconsumer-1-controlplane.tx.test",  # Tractus-X Umbrella reference: dataconsumerOne EDC Control Plane
    "dma_path": "/management",  # Management API path
    "api_key_header": "X-Api-Key",  # API key header name
    "api_key": "TEST1",  # Umbrella Consumer API key from values.yaml
    "dataspace_version": "jupiter",  # "jupiter" or "saturn"
    "bpn": "BPNL00000003AZQP"  # Umbrella Consumer BPN (dataconsumerOne)
}

# Backend Data Source Configuration (for Provider Asset)
BACKEND_CONFIG = {
    "base_url": f"http://dataprovider-submodelserver.tx.test/urn:uuid:{uuid.uuid4()}",  # Umbrella Submodel Server with UUID generated fresh per test run
    "api_key_header": "X-Api-Key",  # Optional: API key header name (if backend requires authentication)
    "api_key": "",  # Optional: API key (leave empty if not needed)
}

# ============================================================================
# POLICY CONFIGURATION — Customize access and usage constraints
# ============================================================================

# Access Policy Configuration - Controls catalog visibility
# Jupiter uses Tractus-X v1.0.0 + W3C ODRL JSON-LD context
ACCESS_POLICY_CONFIG = {
    "context": [
        "https://w3id.org/tractusx/policy/v1.0.0",
        "http://www.w3.org/ns/odrl.jsonld",
        {
            "tx": "https://w3id.org/tractusx/v0.0.1/ns/",
            "@vocab": "https://w3id.org/edc/v0.0.1/ns/"
        }
    ],
    "permissions": [{
        "action": "use",
        "constraint": {
            "leftOperand": "tx:BusinessPartnerNumber",
            "operator": "eq",
            "rightOperand": None  # Will be set to CONSUMER_CONNECTOR_CONFIG["bpn"] at runtime
        }
    }],
    "profile": "cx-policy:profile2405"
}

# Usage Policy Configuration - Controls contract negotiation terms
# Requires active membership, framework agreement, and usage purpose
USAGE_POLICY_CONFIG = {
    "context": [
        "https://w3id.org/tractusx/policy/v1.0.0",
        "http://www.w3.org/ns/odrl.jsonld",
        {
            "@vocab": "https://w3id.org/edc/v0.0.1/ns/"
        }
    ],
    "permissions": [{
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
                    "operator": "eq",
                    "rightOperand": "cx.core.industrycore:1"
                }
            ]
        }
    }],
    "profile": "cx-policy:profile2405"
}

# ============================================================================
# ASSET CONFIGURATION — Customize asset properties
# ============================================================================

ASSET_CONFIG = {
    "dct_type": "https://w3id.org/catenax/taxonomy#Submodel",
    "semantic_id": "urn:samm:io.catenax.business_partner_certificate:3.1.0#BusinessPartnerCertificate",
    "version": "1.0",
    "proxy_params": {
        "proxyQueryParams": "true",
        "proxyPath": "true",
        "proxyMethod": "true",
        "proxyBody": "false"
    }
}

# ============================================================================
# SAMPLE DATA — Test payload uploaded to backend
# ============================================================================

SAMPLE_ASPECT_MODEL_DATA = {
    "businessPartnerNumber": "BPNL0000000093Q7",
    "enclosedSites": [
        {
            "areaOfApplication": "Development, Marketing und Sales and also Procurement for interior components",
            "enclosedSiteBpn": "BPNL0000000093Q7",
        }
    ],
    "registrationNumber": "12 198 54182 TMS",
    "uploader": "BPNL0000000093Q7",
    "document": {
        "documentID": "UUID--123456789",
        "creationDate": "2024-08-23T13:19:00.280+02:00",
        "contentType": "application/pdf",
        "contentBase64": "iVBORw0KGgoAAdsfwerTETEfdgd",
    },
    "validator": {
        "validatorName": "Data service provider X",
        "validatorBpn": "BPNL00000007YREZ",
    },
    "validUntil": "2026-01-24",
    "validFrom": "2023-01-25",
    "trustLevel": "none",
    "type": {
        "certificateVersion": "2015",
        "certificateType": "ISO9001",
    },
    "areaOfApplication": "Development, Marketing und Sales and also Procurement for interior components",
    "issuer": {
        "issuerName": "TÜV",
        "issuerBpn": "BPNL133631123120",
    },
}


def print_header(title: str):
    logger.info("\n%s\n  %s\n%s", "=" * 80, title, "=" * 80)


# ============================================================================
# PHASE 0 — Upload sample data to backend storage
# ============================================================================

def upload_sample_data_to_backend(backend_config=None):
    import requests
    
    if backend_config is None:
        backend_config = BACKEND_CONFIG

    print_header("PHASE 0: Uploading Sample Data to Backend Storage")

    headers = {"Content-Type": "application/json"}
    
    # Add API key if provided
    if backend_config.get("api_key"):
        headers[backend_config.get("api_key_header", "X-Api-Key")] = backend_config["api_key"]
    
    payload = json.dumps(SAMPLE_ASPECT_MODEL_DATA, indent=2)

    logger.info("Uploading BusinessPartnerCertificate aspect model to: %s", backend_config["base_url"])
    logger.info("[UPLOAD REQUEST]:\n%s", payload)

    try:
        response = requests.post(
            backend_config["base_url"],
            data=payload,
            headers=headers,
            verify=False,
            timeout=30,
        )
        logger.info("[UPLOAD RESPONSE] Status: %s", response.status_code)
        logger.info("[UPLOAD RESPONSE] Body:\n%s", response.text)

        if response.status_code not in (200, 201, 204):
            raise RuntimeError(
                f"Backend upload failed with status {response.status_code}: {response.text}"
            )

        logger.info("✓ Sample data uploaded successfully to backend storage")
    except Exception as e:
        logger.exception("✗ Failed to upload sample data: %s", e)
        raise


# ============================================================================
# Service initialisation
# ============================================================================

def initialize_provider_service(provider_config=None) -> BaseConnectorProviderService:
    """
    Initialize the Provider Connector Service following the Industry Core Hub pattern.
    
    Args:
        provider_config: Optional provider connector configuration. Defaults to PROVIDER_CONNECTOR_CONFIG.
        
    Returns:
        ConnectorProviderService instance
    """
    if provider_config is None:
        provider_config = PROVIDER_CONNECTOR_CONFIG
        
    print_header("Initializing Provider Connector Service")

    provider_service = ServiceFactory.get_connector_provider_service(
        dataspace_version=provider_config["dataspace_version"],
        base_url=provider_config["base_url"],
        dma_path=provider_config["dma_path"],
        headers={
            provider_config["api_key_header"]: provider_config["api_key"],
            "Content-Type": "application/json",
        },
        verbose=True,
        debug=True,
        verify_ssl=False,
        logger=logger,
    )

    logger.info("✓ Provider service initialized")
    logger.info("  - Base URL: %s", provider_config["base_url"])
    logger.info("  - Dataspace Version: %s", provider_config["dataspace_version"])
    logger.info("  - BPN: %s", provider_config["bpn"])
    return provider_service


def initialize_consumer_service(consumer_config=None, connection_manager=None) -> ConnectorConsumerService:
    """
    Initialize the Consumer Connector Service following the Industry Core Hub pattern.
    
    Args:
        consumer_config: Optional consumer connector configuration. Defaults to CONSUMER_CONNECTOR_CONFIG.
        connection_manager: Optional connection manager for EDR caching
        
    Returns:
        ConnectorConsumerService instance
    """
    if consumer_config is None:
        consumer_config = CONSUMER_CONNECTOR_CONFIG
        
    print_header("Initializing Consumer Connector Service")

    consumer_service = ServiceFactory.get_connector_consumer_service(
        dataspace_version=consumer_config["dataspace_version"],
        base_url=consumer_config["base_url"],
        dma_path=consumer_config["dma_path"],
        headers={
            consumer_config["api_key_header"]: consumer_config["api_key"],
            "Content-Type": "application/json",
        },
        connection_manager=connection_manager,
        verbose=True,
        debug=True,
        verify_ssl=False,
        logger=logger,
    )

    logger.info("✓ Consumer service initialized")
    logger.info("  - Base URL: %s", consumer_config["base_url"])
    logger.info("  - Dataspace Version: %s", consumer_config["dataspace_version"])
    logger.info("  - BPN: %s", consumer_config["bpn"])
    return consumer_service


# ============================================================================
# PHASE 1 — Provider: provision asset + policies + contract definition
# ============================================================================

def provision_data_on_provider(
    provider_service: BaseConnectorProviderService,
    access_policy_config=None,
    usage_policy_config=None,
    asset_config=None,
    backend_config=None,
    consumer_config=None
) -> dict:
    """
    Phase 1: Provider provisions data by creating Asset, Policies, and Contract Definition.
    
    Args:
        provider_service: Initialized ConnectorProviderService
        access_policy_config: Optional access policy config. If None, uses ACCESS_POLICY_CONFIG.
        usage_policy_config: Optional usage policy config. If None, uses USAGE_POLICY_CONFIG.
        asset_config: Optional asset config. If None, uses ASSET_CONFIG.
        backend_config: Optional backend config. If None, uses BACKEND_CONFIG.
        consumer_config: Optional consumer config (for BPN). If None, uses CONSUMER_CONNECTOR_CONFIG.
        
    Returns:
        dict: Contains asset_id, access_policy_id, usage_policy_id, contract_def_id
    """
    if access_policy_config is None:
        access_policy_config = ACCESS_POLICY_CONFIG
    if usage_policy_config is None:
        usage_policy_config = USAGE_POLICY_CONFIG
    if asset_config is None:
        asset_config = ASSET_CONFIG
    if backend_config is None:
        backend_config = BACKEND_CONFIG
    if consumer_config is None:
        consumer_config = CONSUMER_CONNECTOR_CONFIG
        
    print_header("PHASE 1: Provider Data Provision")

    timestamp        = int(time.time())
    asset_id         = f"jupiter-e2e-asset-{timestamp}"
    access_policy_id = f"jupiter-e2e-access-{timestamp}"
    usage_policy_id  = f"jupiter-e2e-usage-{timestamp}"
    contract_def_id  = f"jupiter-e2e-contract-{timestamp}"

    # 1.1 Access policy
    logger.info("Step 1.1: Creating Access Policy (BPN-based)")
    logger.info("%s", "-" * 80)
    try:
        # Set consumer BPN in access policy
        access_permissions = [p.copy() for p in access_policy_config["permissions"]]
        access_permissions[0]["constraint"]["rightOperand"] = consumer_config["bpn"]
        
        access_policy_response = provider_service.create_policy(
            policy_id=access_policy_id,
            context=access_policy_config["context"],
            permissions=access_permissions,
            profile=access_policy_config["profile"],
        )
        logger.info("✓ Access Policy created: %s", access_policy_id)
        logger.info("  - Restricts catalog visibility to BPN: %s", consumer_config["bpn"])
        logger.info("  - Response: %s", json.dumps(access_policy_response, indent=2))
    except Exception as e:
        logger.exception("✗ Failed to create access policy: %s", e)
        raise

    # 1.2 Usage policy
    logger.info("\nStep 1.2: Creating Usage Policy (Framework Agreement)")
    logger.info("%s", "-" * 80)
    try:
        usage_policy_response = provider_service.create_policy(
            policy_id=usage_policy_id,
            context=usage_policy_config["context"],
            permissions=usage_policy_config["permissions"],
            profile=usage_policy_config["profile"],
        )
        logger.info("✓ Usage Policy created: %s", usage_policy_id)
        logger.info("  - Requires: Active Membership")
        logger.info("  - Requires: Framework Agreement DataExchangeGovernance:1.0")
        logger.info("  - Response: %s", json.dumps(usage_policy_response, indent=2))
    except Exception as e:
        logger.exception("✗ Failed to create usage policy: %s", e)
        raise

    # 1.3 Asset
    logger.info("\nStep 1.3: Creating Asset (Backend Data Source)")
    logger.info("%s", "-" * 80)
    try:
        asset_response = provider_service.create_asset(
            asset_id=asset_id,
            base_url=backend_config["base_url"],
            dct_type=asset_config["dct_type"],
            semantic_id=asset_config["semantic_id"],
            version=asset_config["version"],
            proxy_params=asset_config["proxy_params"],
        )
        logger.info("✓ Asset created: %s", asset_id)
        logger.info("  - Backend URL: %s", backend_config["base_url"])
        logger.info("  - Type: Submodel")
        logger.info("  - Version: 1.0")
        logger.info("  - Response: %s", json.dumps(asset_response, indent=2))
    except Exception as e:
        logger.exception("✗ Failed to create asset: %s", e)
        raise

    # 1.4 Contract definition
    logger.info("\nStep 1.4: Creating Contract Definition")
    logger.info("%s", "-" * 80)
    try:
        
        contract_def_response = provider_service.create_contract(
            contract_id=contract_def_id,
            usage_policy_id=usage_policy_id,
            access_policy_id=access_policy_id,
            asset_id=asset_id,
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
    logger.info("  - Asset ID:    %s", asset_id)
    logger.info("  - Visible to:  %s", consumer_config["bpn"])

    return {
        "asset_id":         asset_id,
        "access_policy_id": access_policy_id,
        "usage_policy_id":  usage_policy_id,
        "contract_def_id":  contract_def_id,
    }


# ============================================================================
# PHASE 2 — Consumer: step-by-step catalog → negotiate → transfer → EDR
# ============================================================================

def consume_data_as_consumer(
    consumer_service: ConnectorConsumerService,
    asset_id: str,
    provider_config=None,
    consumer_config=None
) -> dict:
    """
    Phase 2: Consumer discovers and consumes data from Provider.
    
    Args:
        consumer_service: Initialized ConnectorConsumerService
        asset_id: The asset ID to consume
        provider_config: Optional provider config (for BPN, DSP URL). If None, uses PROVIDER_CONNECTOR_CONFIG.
        consumer_config: Optional consumer config (for dataspace version). If None, uses CONSUMER_CONNECTOR_CONFIG.
        
    Returns:
        dict: Contains edr_data with endpoint and authorization token
    """
    if provider_config is None:
        provider_config = PROVIDER_CONNECTOR_CONFIG
    if consumer_config is None:
        consumer_config = CONSUMER_CONNECTOR_CONFIG
        
    import requests as _requests

    print_header("PHASE 2: Consumer Data Consumption")

    # ------------------------------------------------------------------
    # Step 2.1 Catalog
    # ------------------------------------------------------------------
    logger.info("\nStep 2.1: Discovering Provider Catalog")
    logger.info("%s", "-" * 80)
    try:
     
        catalog_data = consumer_service.get_catalog_by_asset_id_with_bpnl(
            bpnl=provider_config["bpn"],
            counter_party_address=provider_config["dsp_url"],
            asset_id=asset_id,
            verify=False,
        )

        # Jupiter uses prefixed JSON-LD keys (dcat:dataset, odrl:hasPolicy)
        datasets = catalog_data.get("dcat:dataset", catalog_data.get("dataset", []))
        if isinstance(datasets, dict):
            datasets = [datasets]
        logger.info("[CATALOG RESPONSE]:\n%s", json.dumps(catalog_data, indent=2))

        participant_id = catalog_data.get("dspace:participantId", provider_config["bpn"])
        logger.info("  - Participant ID from catalog: %s", participant_id)

        # Extract DSP endpoint from catalog service entries
        dsp_endpoint = provider_config["dsp_url"]
        services = catalog_data.get("dcat:service", catalog_data.get("service", []))
        if isinstance(services, dict):
            services = [services]
        for service in services:
            if service.get("@type") == "DataService" and service.get("endpointURL"):
                dsp_endpoint = service["endpointURL"]
                break
        logger.info("  - DSP endpoint from catalog: %s", dsp_endpoint)
        logger.info("✓ Catalog received — total datasets: %s", len(datasets))

        # Find our target asset
        target_dataset = next((d for d in datasets if d.get("@id") == asset_id), None)
        if target_dataset is None:
            raise RuntimeError(f"Asset {asset_id} not found in catalog")

        # Jupiter uses odrl:hasPolicy (prefixed)
        has_policy = target_dataset.get("odrl:hasPolicy", None)
        if isinstance(has_policy, dict):
            has_policy = [has_policy]
        offer_policy = has_policy[0]
        offer_id     = offer_policy["@id"]
        logger.info("  - Found asset: %s", asset_id)
        logger.info("  - Offer ID:    %s", offer_id)

    except Exception as e:
        logger.exception("✗ Failed to get catalog: %s", e)
        raise

    # ------------------------------------------------------------------
    # Step 2.2 Contract negotiation
    # Jupiter uses the legacy Tractus-X v1.0.0 + W3C ODRL JSON-LD context
    # ------------------------------------------------------------------
    logger.info("\nStep 2.2: Negotiating Contract")
    logger.info("%s", "-" * 80)
    try:
        from tractusx_sdk.dataspace.models.connector.model_factory import ModelFactory

        # Jupiter / legacy ODRL JSON-LD context
        negotiation_context = ConnectorConsumerService.DEFAULT_NEGOTIATION_CONTEXT

        # Handle both prefixed and non-prefixed policy keys
        offer_policy_data = {
            "odrl:permission":  offer_policy.get("odrl:permission",  offer_policy.get("permission",  [])),
            "odrl:prohibition": offer_policy.get("odrl:prohibition", offer_policy.get("prohibition", [])),
            "odrl:obligation":  offer_policy.get("odrl:obligation",  offer_policy.get("obligation",  [])),
        }

        contract_negotiation = ModelFactory.get_contract_negotiation_model(
            dataspace_version=consumer_config["dataspace_version"],
            counter_party_address=dsp_endpoint,
            offer_id=offer_id,
            asset_id=asset_id,
            provider_id=participant_id,
            offer_policy=offer_policy_data,
            context=negotiation_context,
            protocol=ConnectorConsumerService.DSP_0_8,  # "dataspace-protocol-http"
        )

        logger.info("[NEGOTIATION REQUEST]:\n%s", contract_negotiation.to_data())

        negotiation_response = consumer_service.contract_negotiations.create(obj=contract_negotiation, verify=False)

        logger.info("[NEGOTIATION RESPONSE] Status: %s", negotiation_response.status_code)
        logger.info("[NEGOTIATION RESPONSE] Body:\n%s", json.dumps(negotiation_response.json(), indent=2))

        if negotiation_response.status_code != 200:
            raise RuntimeError(
                f"Contract negotiation failed with status {negotiation_response.status_code}"
            )

        negotiation_id = negotiation_response.json().get("@id")
        logger.info("✓ Contract negotiation initiated: %s", negotiation_id)

    except Exception as e:
        logger.exception("✗ Failed to negotiate contract: %s", e)
        raise

    # ------------------------------------------------------------------
    # Step 2.3 Wait for FINALIZED
    # ------------------------------------------------------------------
    logger.info("\nStep 2.3: Waiting for Contract Agreement")
    logger.info("%s", "-" * 80)

    max_wait      = 60
    poll_interval = 2
    elapsed       = 0
    contract_agreement_id = None

    try:
        logger.info("Polling negotiation state…")
        while elapsed < max_wait:
            time.sleep(poll_interval)
            elapsed += poll_interval

            status_response = consumer_service.contract_negotiations.get_by_id(negotiation_id, verify=False)
            if status_response.status_code == 200:
                status_data = status_response.json()
                state = status_data.get("state", status_data.get("edc:state"))
                logger.info("  Negotiation state: %s", state)

                if state == "FINALIZED":
                    logger.info("[NEGOTIATION STATE RESPONSE]:\n%s", json.dumps(status_data, indent=2))
                    contract_agreement_id = status_data.get(
                        "contractAgreementId", status_data.get("edc:contractAgreementId")
                    )
                    logger.info("✓ Contract Agreement finalized: %s", contract_agreement_id)
                    break
                elif state == "TERMINATED":
                    logger.info("[NEGOTIATION STATE RESPONSE]:\n%s", json.dumps(status_data, indent=2))
                    raise RuntimeError("Contract negotiation was TERMINATED")

            if elapsed >= max_wait:
                raise RuntimeError("Contract negotiation timed out")

        if contract_agreement_id is None:
            raise RuntimeError("Contract agreement ID not received")

    except Exception as e:
        logger.exception("✗ Contract negotiation failed: %s", e)
        raise

    # ------------------------------------------------------------------
    # Step 2.4 Transfer process
    # ------------------------------------------------------------------
    logger.info("\nStep 2.4: Initiating Transfer Process")
    logger.info("%s", "-" * 80)
    try:
        transfer_request = ModelFactory.get_transfer_process_model(
            dataspace_version=consumer_config["dataspace_version"],
            counter_party_address=dsp_endpoint,
            contract_id=contract_agreement_id,
            transfer_type="HttpData-PULL",
            protocol=ConnectorConsumerService.DSP_0_8,  # "dataspace-protocol-http"
            data_destination={"type": "HttpProxy"},
        )

        logger.info("[TRANSFER REQUEST]:\n%s", transfer_request.to_data())

        transfer_response = consumer_service.transfer_processes.create(obj=transfer_request, verify=False)

        logger.info("[TRANSFER RESPONSE] Status: %s", transfer_response.status_code)
        logger.info("[TRANSFER RESPONSE] Body:\n%s", json.dumps(transfer_response.json(), indent=2))

        if transfer_response.status_code != 200:
            raise RuntimeError(
                f"Transfer process failed with status {transfer_response.status_code}"
            )

        transfer_id = transfer_response.json().get("@id")
        logger.info("✓ Transfer process initiated: %s", transfer_id)

    except Exception as e:
        logger.exception("✗ Failed to start transfer: %s", e)
        raise

    # ------------------------------------------------------------------
    # Step 2.5 EDR polling
    # ------------------------------------------------------------------
    logger.info("\nStep 2.5: Waiting for EDR (Endpoint Data Reference)")
    logger.info("%s", "-" * 80)

    elapsed  = 0
    edr_data = None

    try:
        logger.info("Waiting for EDR…")
        while elapsed < max_wait:
            time.sleep(poll_interval)
            elapsed += poll_interval

            transfer_status = consumer_service.transfer_processes.get_by_id(transfer_id, verify=False)
            if transfer_status.status_code == 200:
                transfer_state_data = transfer_status.json()
                state = transfer_state_data.get("state", transfer_state_data.get("edc:state"))
                logger.info("  Transfer state: %s", state)

                if state in ("STARTED", "COMPLETED"):
                    edr_response = consumer_service.edrs.get_data_address(transfer_id, verify=False)
                    logger.info("[EDR RESPONSE] Status: %s", edr_response.status_code)
                    logger.info("[EDR RESPONSE] Body:\n%s", json.dumps(edr_response.json(), indent=2))
                    if edr_response.status_code == 200:
                        edr_data = edr_response.json()
                        logger.info("✓ EDR received!")
                        break
                elif state == "TERMINATED":
                    raise RuntimeError("Transfer process was TERMINATED")

            if elapsed >= max_wait:
                raise RuntimeError("EDR retrieval timed out")

        if edr_data is None:
            raise RuntimeError("EDR not available within timeout")

        dataplane_url = edr_data.get("endpoint",      edr_data.get("edc:endpoint"))
        access_token  = edr_data.get("authorization", edr_data.get("edc:authorization"))

        logger.info("  - Endpoint: %s", dataplane_url)
        logger.info("  - Token: %s…", access_token[:30] if access_token else None)

    except Exception as e:
        logger.exception("✗ Failed to get EDR: %s", e)
        raise

    logger.info("\n%s", "=" * 80)
    logger.info("✓ Data Consumption Complete!")
    logger.info("%s", "=" * 80)
    logger.info("  - Endpoint: %s", dataplane_url)

    return {
        "edr_data":             edr_data,
        "dataplane_url":        dataplane_url,
        "access_token":         access_token,
        "transfer_id":          transfer_id,
        "contract_agreement_id": contract_agreement_id,
    }


# ============================================================================
# PHASE 3 — Access actual data via EDR
# ============================================================================

def access_data_with_edr(dataplane_url: str, access_token: str, path: str = "/"):
    import requests as _requests

    print_header("PHASE 3: Accessing Data with EDR")

    try:
        logger.info("Making request to: %s%s", dataplane_url, path)
        data_request_params = {
            "method": "GET",
            "url": f"{dataplane_url}{path}",
            "headers": {
                "Authorization": access_token[:50] + "..." if access_token and len(access_token) > 50 else access_token
            }
        }
        logger.info("[DATA ACCESS REQUEST]:\n%s", json.dumps(data_request_params, indent=2))
        
        response = _requests.get(
            f"{dataplane_url}{path}",
            headers={"Authorization": access_token},
            verify=False,
            timeout=30,
        )
        logger.info("✓ Response received: HTTP %s", response.status_code)

        if response.status_code == 200:
            logger.info("  - Content-Type: %s", response.headers.get("Content-Type", "unknown"))
            logger.info("  - Content-Length: %s bytes", len(response.content))
            try:
                logger.info("[DATA RESPONSE]:\n%s", json.dumps(response.json(), indent=2))
            except Exception:
                logger.info("[DATA RESPONSE (raw)]:\n%s", response.text)
        else:
            logger.error("✗ Request failed: %s", response.text)

        return response

    except Exception as e:
        logger.exception("✗ Failed to access data: %s", e)
        raise


# ============================================================================
# Cleanup (optional)
# ============================================================================

def cleanup_provider_resources(provider_service: BaseConnectorProviderService, provision_ids: dict):
    print_header("CLEANUP: Deleting Provider Resources")

    resources = [
        ("Contract Definition", provision_ids["contract_def_id"], provider_service.contract_definitions),
        ("Asset",               provision_ids["asset_id"],         provider_service.assets),
        ("Usage Policy",        provision_ids["usage_policy_id"],  provider_service.policies),
        ("Access Policy",       provision_ids["access_policy_id"], provider_service.policies),
    ]

    for resource_type, resource_id, controller in resources:
        try:
            controller.delete(resource_id)
            logger.info("✓ Deleted %s: %s", resource_type, resource_id)
        except Exception as e:
            logger.error("✗ Failed to delete %s %s: %s", resource_type, resource_id, e)


def cleanup_backend_data(backend_config=None):
    """
    Cleanup: Delete test data from backend storage.
    
    Args:
        backend_config: Backend configuration dict (defaults to BACKEND_CONFIG)
    """
    if backend_config is None:
        backend_config = BACKEND_CONFIG
        
    print_header("CLEANUP: Deleting Backend Data")
    import requests
    
    try:
        headers = {}
        
        # Add API key if provided
        if backend_config.get("api_key"):
            headers[backend_config.get("api_key_header", "X-Api-Key")] = backend_config["api_key"]
        
        logger.info("Deleting data from backend: %s", backend_config["base_url"])
        response = requests.delete(
            backend_config["base_url"],
            headers=headers if headers else None,
            verify=False,
            timeout=30
        )
        
        if response.status_code in (200, 204, 404):  # 404 = already deleted
            logger.info("✓ Backend data deleted successfully (status: %s)", response.status_code)
        else:
            logger.warning("⚠ Backend delete returned status %s: %s", response.status_code, response.text)
    
    except Exception as e:
        logger.error("✗ Failed to delete backend data: %s", e)


# ============================================================================
# Summary
# ============================================================================

def _print_summary(steps: list[dict], overall_result: str, total_elapsed: float,
                   provision_ids: dict = None, consumption_result: dict = None):
    W = 80
    passed  = sum(1 for s in steps if s["result"] == "PASS")
    failed  = sum(1 for s in steps if s["result"] == "FAIL")
    skipped = sum(1 for s in steps if s["result"] == "SKIP")

    verdict_line = (
        f"  RESULT: {overall_result}  |  {passed} passed  {failed} failed  "
        f"{skipped} skipped  |  Total: {total_elapsed:.1f}s"
    )

    col_name   = 45
    col_result =  6
    col_dur    =  8

    lines = [
        "",
        "╔" + "=" * (W - 2) + "╗",
        "║" + "  E2E TEST RUN SUMMARY  (Jupiter)".center(W - 2) + "║",
        "╠" + "=" * (W - 2) + "╣",
        "║" + f"  {'STEP':<{col_name}} {'RESULT':>{col_result}}  {'TIME':>{col_dur}}".ljust(W - 2) + "║",
        "║" + "  " + "-" * (W - 4) + "  ║"[:-2] + "║",
    ]
    for s in steps:
        icon = "✓" if s["result"] == "PASS" else ("✗" if s["result"] == "FAIL" else "-")
        dur  = f"{s['duration_s']:.1f}s" if s["duration_s"] is not None else "  -"
        line = f"  {icon} {s['name']:<{col_name - 2}} {s['result']:>{col_result}}  {dur:>{col_dur}}"
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


# ============================================================================
# MAIN
# ============================================================================

def main(
    provider_config=None,
    consumer_config=None,
    backend_config=None,
    access_policy_config=None,
    usage_policy_config=None,
    asset_config=None
):
    """
    Main execution flow: Provider provisions data, Consumer consumes it.
    
    Args:
        provider_config: Optional provider connector configuration. Defaults to PROVIDER_CONNECTOR_CONFIG.
        consumer_config: Optional consumer connector configuration. Defaults to CONSUMER_CONNECTOR_CONFIG.
        backend_config: Optional backend service configuration. Defaults to BACKEND_CONFIG.
        access_policy_config: Optional access policy configuration. Defaults to ACCESS_POLICY_CONFIG.
        usage_policy_config: Optional usage policy configuration. Defaults to USAGE_POLICY_CONFIG.
        asset_config: Optional asset configuration. Defaults to ASSET_CONFIG.
    """
    # Use global configs as defaults
    if provider_config is None:
        provider_config = PROVIDER_CONNECTOR_CONFIG
    if consumer_config is None:
        consumer_config = CONSUMER_CONNECTOR_CONFIG
    if backend_config is None:
        backend_config = BACKEND_CONFIG
    if access_policy_config is None:
        access_policy_config = ACCESS_POLICY_CONFIG
    if usage_policy_config is None:
        usage_policy_config = USAGE_POLICY_CONFIG
    if asset_config is None:
        asset_config = ASSET_CONFIG
        
    logger.info(
        "\n\n%s\n%s\n%s\n%s\n%s\n%s",
        "╔" + "=" * 78 + "╗",
        "║" + " " * 78 + "║",
        "║" + "  Jupiter Connector Services - E2E Data Exchange Example".center(78) + "║",
        "║" + "  Protocol: dataspace-protocol-http (legacy DSP / Jupiter)".center(78) + "║",
        "║" + " " * 78 + "║",
        "╚" + "=" * 78 + "╝",
    )

    provision_ids      = None
    consumption_result = None
    overall_result     = "FAIL"
    run_start          = time.time()
    steps: list[dict]  = []

    def _run_step(name: str, fn):
        t0 = time.time()
        try:
            result = fn()
            steps.append({"name": name, "result": "PASS", "duration_s": time.time() - t0})
            return result
        except Exception as exc:
            steps.append({"name": name, "result": "FAIL", "duration_s": time.time() - t0})
            raise

    try:
        provider_service = initialize_provider_service(provider_config)
        consumer_service = initialize_consumer_service(consumer_config)

        _run_step("Phase 0 · Upload sample data to backend",
                  lambda: upload_sample_data_to_backend(backend_config))

        provision_ids = _run_step("Phase 1 · Provider data provision",
                                  lambda: provision_data_on_provider(
                                      provider_service,
                                      access_policy_config,
                                      usage_policy_config,
                                      asset_config,
                                      backend_config,
                                      consumer_config
                                  ))
        

        logger.info("Waiting 3 seconds for Provider EDC to process…")
        time.sleep(3)

        consumption_result = _run_step(
            "Phase 2 · Consumer data consumption (catalog→negotiate→transfer→EDR)",
            lambda: consume_data_as_consumer(
                consumer_service,
                asset_id=provision_ids["asset_id"],
                provider_config=provider_config,
                consumer_config=consumer_config
            ),
        )

        _run_step("Phase 3 · Access data with EDR",
                  lambda: access_data_with_edr(
                      dataplane_url=consumption_result["dataplane_url"],
                      access_token=consumption_result["access_token"],
                  ))

        overall_result = "PASS"

    except Exception as e:
        logger.exception("\n✗ E2E flow failed: %s", e)
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
        _print_summary(
            steps=steps,
            overall_result=overall_result,
            total_elapsed=time.time() - run_start,
            provision_ids=provision_ids,
            consumption_result=consumption_result,
        )
        sys.stdout.flush()
        
        # Cleanup (if --cleanup flag is provided)
        if _args.cleanup:
            if provision_ids:
                cleanup_provider_resources(provider_service, provision_ids)
            if backend_config.get("base_url"):
                cleanup_backend_data(backend_config)
        
        _finalize_log(overall_result)


if __name__ == "__main__":
    _parser = argparse.ArgumentParser(
        description="Jupiter E2E connector service example (legacy DSP)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  # Run with default configuration from file
  python tck_e2e_jupiter_0-10-X_detailed.py
  
  # Override provider and consumer URLs
  python tck_e2e_jupiter_0-10-X_detailed.py \\
    --provider-url https://provider-edc.example.com \\
    --consumer-url https://consumer-edc.example.com
  
  # Custom backend URL and API keys
  python tck_e2e_jupiter_0-10-X_detailed.py \\
    --backend-url https://backend.example.com/data \\
    --provider-api-key YOUR_PROVIDER_KEY \\
    --consumer-api-key YOUR_CONSUMER_KEY
        """
    )
    
    # Runtime options
    _parser.add_argument("--no-debug", action="store_false", dest="debug", 
                        help="Disable DEBUG-level logging (enabled by default)")
    _parser.add_argument("--no-cleanup", action="store_false", dest="cleanup", 
                        help="Skip cleanup of provider resources and backend data (cleanup enabled by default)")
    
    # Provider configuration
    _parser.add_argument("--provider-url", help="Provider EDC base URL")
    _parser.add_argument("--provider-api-key", help="Provider EDC API key")
    _parser.add_argument("--provider-bpn", help="Provider Business Partner Number")
    _parser.add_argument("--provider-dsp-url", help="Provider DSP endpoint URL")
    
    # Consumer configuration
    _parser.add_argument("--consumer-url", help="Consumer EDC base URL")
    _parser.add_argument("--consumer-api-key", help="Consumer EDC API key")
    _parser.add_argument("--consumer-bpn", help="Consumer Business Partner Number")
    
    # Backend configuration
    _parser.add_argument("--backend-url", help="Backend storage URL")
    _parser.add_argument("--backend-api-key", help="Backend API key (if required)")
    
    _args = _parser.parse_args()
    
    # Configure logging
    if _args.debug:
        logging.root.setLevel(logging.DEBUG)
        for _h in logging.root.handlers:
            _h.setLevel(logging.DEBUG)
        logger.info("DEBUG logging enabled")
    else:
        logger.info("DEBUG logging disabled (use without --no-debug to enable)")

    logger.warning(
        "\n⚠️  IMPORTANT: Update the PLACEHOLDER values before running!\n"
        "%s\n"
        "Required configuration:\n"
        "  1. Provider connector URL, API key, BPN, DSP URL\n"
        "  2. Consumer connector URL, API key, BPN\n"
        "  3. Backend data source URL\n"
        "\nSee the CONFIGURATION section at the top of this file.\n"
        "%s",
        "=" * 80,
        "=" * 80,
    )
    
    # Build configuration dictionaries from CLI args (override defaults if provided)
    provider_config = PROVIDER_CONNECTOR_CONFIG.copy()
    if _args.provider_url:
        provider_config["base_url"] = _args.provider_url
    if _args.provider_api_key:
        provider_config["api_key"] = _args.provider_api_key
    if _args.provider_bpn:
        provider_config["bpn"] = _args.provider_bpn
    if _args.provider_dsp_url:
        provider_config["dsp_url"] = _args.provider_dsp_url
    
    consumer_config = CONSUMER_CONNECTOR_CONFIG.copy()
    if _args.consumer_url:
        consumer_config["base_url"] = _args.consumer_url
    if _args.consumer_api_key:
        consumer_config["api_key"] = _args.consumer_api_key
    if _args.consumer_bpn:
        consumer_config["bpn"] = _args.consumer_bpn
    
    backend_config = BACKEND_CONFIG.copy()
    if _args.backend_url:
        backend_config["base_url"] = _args.backend_url
    if _args.backend_api_key:
        backend_config["api_key"] = _args.backend_api_key
    
    # Run main with CLI-provided or default configuration
    main(
        provider_config=provider_config,
        consumer_config=consumer_config,
        backend_config=backend_config
    )
