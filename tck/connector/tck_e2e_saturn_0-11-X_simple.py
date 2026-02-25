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
Simple E2E Example: Saturn Connector Services - Data Provision and Consumption

This is a simplified version of the full E2E example that uses do_get_with_bpnl()
to collapse the entire consumer flow (catalog → negotiate → transfer → EDR → GET)
into a single SDK call.

Flow:
1. Provider provisions data (Asset + Policies + Contract Definition)
2. Consumer calls do_get_with_bpnl() — SDK handles everything internally
3. Print the response

For the full step-by-step version see: saturn_e2e_connector_service.py
"""

import argparse
import time
import json
import logging
import os
import sys
import uuid
import requests
from datetime import datetime

from tractusx_sdk.dataspace.services.connector import ServiceFactory
from tractusx_sdk.dataspace.services.connector.base_connector_provider import BaseConnectorProviderService
from tractusx_sdk.dataspace.services.connector.saturn.connector_consumer_service import ConnectorConsumerService

# Configure logging to both console and timestamped log file
_test_case_name = "tck_e2e_saturn_0-11-X_simple"
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

# Module-level logger for this example script
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
# CONFIGURATION - Replace with your actual values
# ============================================================================
# This TCK is designed for Eclipse Tractus-X EDC (https://github.com/eclipse-tractusx/tractusx-edc)
# Compatible EDC versions: 0.11.X+ (Saturn Protocol with DSP 2025-1)
#
# Backend: Uses simple-data-backend from Tractus-X Umbrella
#          https://github.com/eclipse-tractusx/tractus-x-umbrella/tree/main/simple-data-backend


PROVIDER_CONFIG = {
    "base_url":           "http://dataprovider-controlplane.tx.test",
    "dma_path":           "/management",
    "api_key_header":     "X-Api-Key",
    "api_key":            "TEST2",
    "dataspace_version":  "saturn",
    "bpn":                "BPNL00000003AYRE",
    "dsp_url":            "http://dataprovider-controlplane.tx.test/api/v1/dsp",
}

CONSUMER_CONFIG = {
    "base_url":           "http://dataconsumer-1-controlplane.tx.test",
    "dma_path":           "/management",
    "api_key_header":     "X-Api-Key",
    "api_key":            "TEST1",
    "dataspace_version":  "saturn",
    "bpn":                "BPNL00000003AZQP",
}

BACKEND_CONFIG = {
    "base_url":        f"http://dataprovider-submodelserver.tx.test/urn:uuid:{uuid.uuid4()}",  # Umbrella Submodel Server with UUID generated fresh per test run
    "api_key_header": "X-Api-Key",  # Optional: API key header name (if backend requires authentication)
    "api_key":         "",  # Optional: API key (leave empty if not needed)
}

# ============================================================================
# POLICY & ASSET CONFIGURATION
# ============================================================================
# NOTE: Saturn (Catena-X 2025-9) uses implicit default context - no "context" key needed

ACCESS_POLICY_CONFIG = {
    "permissions": [{
        "action": "access",
        "constraint": {
            "leftOperand": "BusinessPartnerNumber",
            "operator": "isAnyOf",
            "rightOperand": None  # Will be set to CONSUMER_CONFIG["bpn"] at runtime
        }
    }]
}

USAGE_POLICY_CONFIG = {
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
                    "operator": "isAnyOf",
                    "rightOperand": "cx.core.industrycore:1"
                }
            ]
        }
    }]
}

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

SAMPLE_DATA = SAMPLE_ASPECT_MODEL_DATA = {
    "businessPartnerNumber": "BPNL0000000093Q7",
    "enclosedSites": [
        {
            "areaOfApplication": "Development, Marketing und Sales and also Procurement for interior components",
            "enclosedSiteBpn": "BPNL0000000093Q7"
        }
    ],
    "registrationNumber": "12 198 54182 TMS",
    "uploader": "BPNL0000000093Q7",
    "document": {
        "documentID": "UUID--123456789",
        "creationDate": "2024-08-23T13:19:00.280+02:00",
        "contentType": "application/pdf",
        "contentBase64": "iVBORw0KGgoAAdsfwerTETEfdgd"
    },
    "validator": {
        "validatorName": "Data service provider X",
        "validatorBpn": "BPNL0000000093Q7"
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


# Accepted usage policies — controls which catalog offer policies are accepted:
#
#   None  → accept ANY policy the provider offers (no filtering).
#   []    → reject every policy; negotiation will always fail.
#   [...] → only negotiate contracts whose offer policy matches one of the
#            entries below (exact dict comparison, minus @id and @type).
#
# Example — restrict to the specific Catena-X constraints provisioned above:
#   ACCEPTED_POLICIES = [{
#       "permission": [{"action": "use", "constraint": {"and": [
#           {"leftOperand": "Membership",         "operator": "eq",      "rightOperand": "active"},
#           {"leftOperand": "FrameworkAgreement", "operator": "eq",      "rightOperand": "DataExchangeGovernance:1.0"},
#           {"leftOperand": "UsagePurpose",       "operator": "isAnyOf", "rightOperand": "cx.core.industrycore:1"},
#       ]}}],
#       "prohibition": [], "obligation": []
#   }]
ACCEPTED_POLICIES = None  # None = accept any policy offered by the provider


# ============================================================================
# HELPERS
# ============================================================================

def _sep(title: str = ""):
    if title:
        logger.info("\n%s\n  %s\n%s", "=" * 70, title, "=" * 70)
    else:
        logger.info("\n%s", "=" * 70)


# ============================================================================
# PHASE 0 — Upload sample data to backend storage
# ============================================================================

def upload_sample_data(backend_config=None) -> None:
    if backend_config is None:
        backend_config = BACKEND_CONFIG
        
    _sep("PHASE 0: Upload Sample Data to Backend")
    
    headers = {"Content-Type": "application/json"}
    
    # Add API key if provided
    if backend_config.get("api_key"):
        headers[backend_config.get("api_key_header", "X-Api-Key")] = backend_config["api_key"]
    
    logger.info("[UPLOAD REQUEST]: POST %s", backend_config["base_url"])
    response = requests.post(
        backend_config["base_url"],
        json=SAMPLE_DATA,
        headers=headers,
        verify=False,
        timeout=30,
    )
    if response.status_code not in (200, 201, 204):
        raise RuntimeError(f"Backend upload failed [{response.status_code}]: {response.text}")
    logger.info("✓ Sample data uploaded (%s)", response.status_code)


# ============================================================================
# PHASE 1 — Provider: provision asset + policies + contract definition
# ============================================================================

def provision(
    provider: BaseConnectorProviderService,
    access_policy_config=None,
    usage_policy_config=None,
    asset_config=None,
    backend_config=None,
    consumer_config=None
) -> dict:
    """
    Phase 1: Provider provisions data by creating Asset, Policies, and Contract Definition.
    
    Args:
        provider: Initialized provider service
        access_policy_config: Optional access policy config. If None, uses ACCESS_POLICY_CONFIG.
        usage_policy_config: Optional usage policy config. If None, uses USAGE_POLICY_CONFIG.
        asset_config: Optional asset config. If None, uses ASSET_CONFIG.
        backend_config: Optional backend config. If None, uses BACKEND_CONFIG.
        consumer_config: Optional consumer config (for BPN). If None, uses CONSUMER_CONFIG.
    
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
        consumer_config = CONSUMER_CONFIG
    
    _sep("PHASE 1: Provider Data Provision")

    ts = int(time.time())
    asset_id         = f"simple-e2e-asset-{ts}"
    access_policy_id = f"simple-e2e-access-{ts}"
    usage_policy_id  = f"simple-e2e-usage-{ts}"
    contract_def_id  = f"simple-e2e-contract-{ts}"

    # Set consumer BPN in access policy
    access_permissions = access_policy_config["permissions"].copy()
    access_permissions[0]["constraint"]["rightOperand"] = consumer_config["bpn"]

    logger.info("[ACCESS POLICY REQUEST]: Creating policy %s", access_policy_id)
    provider.create_policy(
        policy_id=access_policy_id,
        permissions=access_permissions
    )
    logger.info("✓ Access policy:      %s", access_policy_id)

    logger.info("[USAGE POLICY REQUEST]: Creating policy %s", usage_policy_id)
    provider.create_policy(
        policy_id=usage_policy_id,
        permissions=usage_policy_config["permissions"]
    )
    logger.info("✓ Usage policy:       %s", usage_policy_id)

    logger.info("[ASSET REQUEST]: Creating asset %s", asset_id)
    provider.create_asset(
        asset_id=asset_id,
        base_url=backend_config["base_url"],
        dct_type=asset_config["dct_type"],
        semantic_id=asset_config["semantic_id"],
        version=asset_config["version"],
        proxy_params=asset_config["proxy_params"]
    )
    logger.info("✓ Asset:              %s", asset_id)

    logger.info("[CONTRACT DEFINITION REQUEST]: Creating contract %s", contract_def_id)
    provider.create_contract(
        contract_id=contract_def_id,
        usage_policy_id=usage_policy_id,
        access_policy_id=access_policy_id,
        asset_id=asset_id,
    )
    logger.info("✓ Contract def:       %s", contract_def_id)

    return {
        "asset_id":         asset_id,
        "access_policy_id": access_policy_id,
        "usage_policy_id":  usage_policy_id,
        "contract_def_id":  contract_def_id,
    }


# ============================================================================
# PHASE 2 — Consumer: do_get_with_bpnl does everything in one call
# ============================================================================

def consume(
    consumer: ConnectorConsumerService,
    asset_id: str,
    provider_config=None,
    accepted_policies=None
) -> requests.Response:
    """
    Phase 2: Consumer discovers and consumes data using do_get_with_bpnl.
    
    Args:
        consumer: Initialized consumer service
        asset_id: The asset ID to consume
        provider_config: Optional provider config (for BPN, DSP URL). If None, uses PROVIDER_CONFIG.
        accepted_policies: Optional accepted policies. If None, uses ACCEPTED_POLICIES.
    
    Returns:
        requests.Response: Response from the data source
    """
    if provider_config is None:
        provider_config = PROVIDER_CONFIG
    if accepted_policies is None:
        accepted_policies = ACCEPTED_POLICIES
    
    _sep("PHASE 2: Consumer — do_get_with_bpnl")
    logger.info("Calling do_get_with_bpnl() — SDK handles catalog → negotiate → transfer → EDR → GET")

    filter_expression = [
        consumer.get_filter_expression(
            key=ConnectorConsumerService.DEFAULT_ID_KEY,
            value=asset_id,
            operator="=",
        )
    ]

    logger.info("[DO_GET REQUEST]: BPNL=%s, asset_id=%s, path=/", provider_config["bpn"], asset_id)
    response = consumer.do_get_with_bpnl(
        bpnl=provider_config["bpn"],
        counter_party_address=provider_config["dsp_url"],
        filter_expression=filter_expression,
        policies=accepted_policies,
        path="/",
        verify=False,
    )

    logger.info("✓ Response: HTTP %s", response.status_code)
    return response


# ============================================================================
# CLEANUP
# ============================================================================

def cleanup_provider_resources(provider_service, provision_ids):
    """
    Cleanup: Delete all created resources from Provider.
    
    Args:
        provider_service: Initialized ConnectorProviderService
        provision_ids: Dict containing resource IDs to delete
    """
    _sep("CLEANUP: Deleting Provider Resources")
    
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


def cleanup_backend_data(backend_config=None):
    """
    Cleanup: Delete test data from backend storage.
    
    Args:
        backend_config: Backend configuration dict (defaults to BACKEND_CONFIG)
    """
    if backend_config is None:
        backend_config = BACKEND_CONFIG
        
    _sep("CLEANUP: Deleting Backend Data")
    
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
# SUMMARY
# ============================================================================

def _print_summary(steps: list[dict], overall_result: str, total_elapsed: float,
                   ids: dict = None, http_status: int = None):
    W = 80
    passed  = sum(1 for s in steps if s["result"] == "PASS")
    failed  = sum(1 for s in steps if s["result"] == "FAIL")
    skipped = sum(1 for s in steps if s["result"] == "SKIP")

    verdict = f"  RESULT: {overall_result}  |  {passed} passed  {failed} failed  {skipped} skipped  |  Total: {total_elapsed:.1f}s"

    col_name = 45
    col_res  =  6
    col_dur  =  8

    lines = [
        "",
        "╔" + "=" * (W - 2) + "╗",
        "║" + "  E2E TEST RUN SUMMARY  (simple)".center(W - 2) + "║",
        "╠" + "=" * (W - 2) + "╣",
        "║" + f"  {'STEP':<{col_name}} {'RESULT':>{col_res}}  {'TIME':>{col_dur}}".ljust(W - 2) + "║",
        "║" + "  " + "-" * (W - 6) + "  ║"[:-2] + "║",
    ]
    for s in steps:
        icon = "✓" if s["result"] == "PASS" else ("✗" if s["result"] == "FAIL" else "-")
        dur  = f"{s['duration_s']:.1f}s" if s["duration_s"] is not None else "  -"
        line = f"  {icon} {s['name']:<{col_name - 2}} {s['result']:>{col_res}}  {dur:>{col_dur}}"
        lines.append("║" + line.ljust(W - 2) + "║")
    lines += [
        "╠" + "=" * (W - 2) + "╣",
        "║" + verdict.ljust(W - 2) + "║",
        "╚" + "=" * (W - 2) + "╝",
    ]
    if ids or http_status is not None:
        lines += ["", "  Resource IDs", "  " + "-" * 60]
    if ids:
        lines += [
            f"  Asset ID      : {ids.get('asset_id', '-')}",
            f"  Access Policy : {ids.get('access_policy_id', '-')}",
            f"  Usage Policy  : {ids.get('usage_policy_id', '-')}",
            f"  Contract Def  : {ids.get('contract_def_id', '-')}",
        ]
    if http_status is not None:
        lines.append(f"  Data HTTP     : {http_status}")
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
    asset_config=None,
    accepted_policies=None
):
    """
    Main execution flow: Provider provisions data, Consumer consumes it.
    
    Args:
        provider_config: Optional provider connector configuration. Defaults to PROVIDER_CONFIG.
        consumer_config: Optional consumer connector configuration. Defaults to CONSUMER_CONFIG.
        backend_config: Optional backend service configuration. Defaults to BACKEND_CONFIG.
        access_policy_config: Optional access policy configuration. Defaults to ACCESS_POLICY_CONFIG.
        usage_policy_config: Optional usage policy configuration. Defaults to USAGE_POLICY_CONFIG.
        asset_config: Optional asset configuration. Defaults to ASSET_CONFIG.
        accepted_policies: Optional accepted policies. Defaults to ACCEPTED_POLICIES.
    """
    # Use global configs as defaults
    if provider_config is None:
        provider_config = PROVIDER_CONFIG
    if consumer_config is None:
        consumer_config = CONSUMER_CONFIG
    if backend_config is None:
        backend_config = BACKEND_CONFIG
    if access_policy_config is None:
        access_policy_config = ACCESS_POLICY_CONFIG
    if usage_policy_config is None:
        usage_policy_config = USAGE_POLICY_CONFIG
    if asset_config is None:
        asset_config = ASSET_CONFIG
    if accepted_policies is None:
        accepted_policies = ACCEPTED_POLICIES
    
    _sep("Saturn Connector Services — Simple E2E")

    # Initialise provider
    provider: BaseConnectorProviderService = ServiceFactory.get_connector_provider_service(
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

    # Initialise consumer
    consumer: ConnectorConsumerService = ServiceFactory.get_connector_consumer_service(
        dataspace_version=consumer_config["dataspace_version"],
        base_url=consumer_config["base_url"],
        dma_path=consumer_config["dma_path"],
        headers={
            consumer_config["api_key_header"]: consumer_config["api_key"],
            "Content-Type": "application/json",
        },
        verbose=True,
        debug=True,
        verify_ssl=False,
        logger=logger,
    )

    overall_result = "FAIL"
    run_start      = time.time()
    steps: list[dict] = []
    ids        = None
    http_status = None

    def _run_step(name: str, fn):
        t0 = time.time()
        try:
            result = fn()
            steps.append({"name": name, "result": "PASS", "duration_s": time.time() - t0})
            return result
        except Exception:
            steps.append({"name": name, "result": "FAIL", "duration_s": time.time() - t0})
            raise

    try:
        _run_step("Phase 0 · Upload sample data to backend", lambda: upload_sample_data(backend_config))

        ids = _run_step("Phase 1 · Provider data provision",
                        lambda: provision(
                            provider,
                            access_policy_config,
                            usage_policy_config,
                            asset_config,
                            backend_config,
                            consumer_config
                        ))

        logger.info("Waiting 3 s for provider EDC to process…")
        time.sleep(3)

        response = _run_step("Phase 2 · do_get_with_bpnl (catalog→negotiate→transfer→EDR→GET)",
                             lambda: consume(consumer, ids["asset_id"], provider_config, accepted_policies))

        http_status = response.status_code
        if response.status_code == 200:
            try:
                logger.info("Response body:\n%s", json.dumps(response.json(), indent=2))
            except Exception:
                logger.info("Response body:\n%s", response.text)
            overall_result = "PASS"
        else:
            raise RuntimeError(f"Unexpected HTTP {response.status_code}: {response.text}")

    except Exception as e:
        logger.exception("✗ Simple E2E FAILED: %s", e)
        all_phases = [
            "Phase 0 · Upload sample data to backend",
            "Phase 1 · Provider data provision",
            "Phase 2 · do_get_with_bpnl (catalog→negotiate→transfer→EDR→GET)",
        ]
        done = {s["name"] for s in steps}
        for phase in all_phases:
            if phase not in done:
                steps.append({"name": phase, "result": "SKIP", "duration_s": None})

    finally:
        _print_summary(
            steps=steps,
            overall_result=overall_result,
            total_elapsed=time.time() - run_start,
            ids=ids,
            http_status=http_status,
        )
        sys.stdout.flush()
        
        # Optional cleanup
        if _args.cleanup and ids:
            cleanup_provider_resources(provider, ids)
            cleanup_backend_data(backend_config)
        
        _finalize_log(overall_result)


if __name__ == "__main__":
    _parser = argparse.ArgumentParser(
        description="Saturn Simple E2E example",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  # Run with default configuration from file
  python tck_e2e_saturn_0-11-X_simple.py
  
  # Override provider and consumer URLs
  python tck_e2e_saturn_0-11-X_simple.py \\
    --provider-url https://provider-edc.example.com \\
    --consumer-url https://consumer-edc.example.com
  
  # Custom backend URL and API keys
  python tck_e2e_saturn_0-11-X_simple.py \\
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
    
    # Build configuration dictionaries from CLI args (override defaults if provided)
    provider_config = PROVIDER_CONFIG.copy()
    if _args.provider_url:
        provider_config["base_url"] = _args.provider_url
    if _args.provider_api_key:
        provider_config["api_key"] = _args.provider_api_key
    if _args.provider_bpn:
        provider_config["bpn"] = _args.provider_bpn
    if _args.provider_dsp_url:
        provider_config["dsp_url"] = _args.provider_dsp_url
    
    consumer_config = CONSUMER_CONFIG.copy()
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

