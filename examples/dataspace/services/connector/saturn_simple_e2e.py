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
_run_timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
_log_dir = os.path.dirname(os.path.abspath(__file__))
_log_file = os.path.join(_log_dir, f"saturn_simple_e2e_run_{_run_timestamp}.log")
_log_format = "%(asctime)s %(levelname)s [%(name)s] %(message)s"
_file_handler = logging.FileHandler(_log_file, mode="w", encoding="utf-8")
_file_handler.setLevel(logging.INFO)
_file_handler.setFormatter(logging.Formatter(_log_format))
_console_handler = logging.StreamHandler(sys.stdout)
_console_handler.setLevel(logging.INFO)
_console_handler.setFormatter(logging.Formatter(_log_format))
logging.basicConfig(level=logging.INFO, handlers=[_console_handler, _file_handler], force=True)

# Module-level logger for this example script
logger = logging.getLogger("saturn_simple_e2e")
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

PROVIDER_CONFIG = {
    "base_url":           "https://edc-provider-ichub-control.test.io",
    "dma_path":           "/management",
    "api_key_header":     "X-Api-Key",
    "api_key":            "",
    "dataspace_version":  "saturn",
    "bpn":                "BPNL0000000093Q7",
    "dsp_url":            "https://edc-provider-ichub-control.test.io/api/v1/dsp",
}

CONSUMER_CONFIG = {
    "base_url":           "https://edc-consumer-ichub-control.test.io",
    "dma_path":           "/management",
    "api_key_header":     "X-Api-Key",
    "api_key":            "",
    "dataspace_version":  "saturn",
    "bpn":                "BPNL00000003CRHK",
}

BACKEND_CONFIG = {
    "base_url":        f"https://storage-ichub.test.io/urn:uuid:{uuid.uuid4()}",  # UUID generated fresh per test run
}

SAMPLE_DATA = SAMPLE_ASPECT_MODEL_DATA = {
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

def upload_sample_data() -> None:
    _sep("PHASE 0: Upload Sample Data to Backend")
    response = requests.post(
        BACKEND_CONFIG["base_url"],
        json=SAMPLE_DATA,
        headers={
            "Content-Type": "application/json",
        },
        verify=False,
        timeout=30,
    )
    if response.status_code not in (200, 201, 204):
        raise RuntimeError(f"Backend upload failed [{response.status_code}]: {response.text}")
    logger.info("✓ Sample data uploaded (%s)", response.status_code)


# ============================================================================
# PHASE 1 — Provider: provision asset + policies + contract definition
# ============================================================================

def provision(provider: BaseConnectorProviderService) -> dict:
    _sep("PHASE 1: Provider Data Provision")

    ts = int(time.time())
    asset_id         = f"simple-e2e-asset-{ts}"
    access_policy_id = f"simple-e2e-access-{ts}"
    usage_policy_id  = f"simple-e2e-usage-{ts}"
    contract_def_id  = f"simple-e2e-contract-{ts}"

    provider.create_policy(
        policy_id=access_policy_id,
        permissions=[{
            "action": "access",
            "constraint": {
                "leftOperand": "BusinessPartnerNumber",
                "operator":    "isAnyOf",
                "rightOperand": CONSUMER_CONFIG["bpn"],
            },
        }],
    )
    logger.info("✓ Access policy:      %s", access_policy_id)

    provider.create_policy(
        policy_id=usage_policy_id,
        permissions=[{
            "action": "use",
            "constraint": {
                "and": [
                    {"leftOperand": "Membership",         "operator": "eq",       "rightOperand": "active"},
                    {"leftOperand": "FrameworkAgreement", "operator": "eq",       "rightOperand": "DataExchangeGovernance:1.0"},
                    {"leftOperand": "UsagePurpose",       "operator": "isAnyOf",  "rightOperand": "cx.core.industrycore:1"},
                ],
            },
        }],
    )
    logger.info("✓ Usage policy:       %s", usage_policy_id)

    provider.create_asset(
        asset_id=asset_id,
        base_url=BACKEND_CONFIG["base_url"],
        dct_type="https://w3id.org/catenax/taxonomy#Submodel",
        semantic_id="urn:samm:io.catenax.business_partner_certificate:3.1.0#BusinessPartnerCertificate",
        version="1.0",
        proxy_params={
            "proxyQueryParams": "true",
            "proxyPath":        "true",
            "proxyMethod":      "true",
            "proxyBody":        "false",
        },
    )
    logger.info("✓ Asset:              %s", asset_id)

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

def consume(consumer: ConnectorConsumerService, asset_id: str) -> requests.Response:
    _sep("PHASE 2: Consumer — do_get_with_bpnl")
    logger.info("Calling do_get_with_bpnl() — SDK handles catalog → negotiate → transfer → EDR → GET")

    filter_expression = [
        consumer.get_filter_expression(
            key=ConnectorConsumerService.DEFAULT_ID_KEY,
            value=asset_id,
            operator="=",
        )
    ]

    response = consumer.do_get_with_bpnl(
        bpnl=PROVIDER_CONFIG["bpn"],
        counter_party_address=PROVIDER_CONFIG["dsp_url"],
        filter_expression=filter_expression,
        policies=ACCEPTED_POLICIES,
        path="/",
        verify=False,
    )

    logger.info("✓ Response: HTTP %s", response.status_code)
    return response


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

def main():
    _sep("Saturn Connector Services — Simple E2E")

    # Initialise provider
    provider: BaseConnectorProviderService = ServiceFactory.get_connector_provider_service(
        dataspace_version=PROVIDER_CONFIG["dataspace_version"],
        base_url=PROVIDER_CONFIG["base_url"],
        dma_path=PROVIDER_CONFIG["dma_path"],
        headers={
            PROVIDER_CONFIG["api_key_header"]: PROVIDER_CONFIG["api_key"],
            "Content-Type": "application/json",
        },
        verify_ssl=False,
        logger=logger,
    )

    # Initialise consumer
    consumer: ConnectorConsumerService = ServiceFactory.get_connector_consumer_service(
        dataspace_version=CONSUMER_CONFIG["dataspace_version"],
        base_url=CONSUMER_CONFIG["base_url"],
        dma_path=CONSUMER_CONFIG["dma_path"],
        headers={
            CONSUMER_CONFIG["api_key_header"]: CONSUMER_CONFIG["api_key"],
            "Content-Type": "application/json",
        },
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
        _run_step("Phase 0 · Upload sample data to backend", upload_sample_data)

        ids = _run_step("Phase 1 · Provider data provision",
                        lambda: provision(provider))

        logger.info("Waiting 3 s for provider EDC to process…")
        time.sleep(3)

        response = _run_step("Phase 2 · do_get_with_bpnl (catalog→negotiate→transfer→EDR→GET)",
                             lambda: consume(consumer, ids["asset_id"]))

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
        _finalize_log(overall_result)


if __name__ == "__main__":
    _parser = argparse.ArgumentParser(description="Saturn Simple E2E example")
    _parser.add_argument("--debug", action="store_true", help="Enable DEBUG-level logging (very verbose)")
    _args = _parser.parse_args()
    if _args.debug:
        logging.root.setLevel(logging.DEBUG)
        for _h in logging.root.handlers:
            _h.setLevel(logging.DEBUG)
        logger.info("DEBUG logging enabled")
    main()

