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
Reusable helpers for TCK (Technology Compatibility Kit) E2E connector tests.

This module consolidates common infrastructure used across all TCK E2E scripts:
logging, service initialization, backend upload, cleanup, test summary, CLI parsing,
and simplified provisioning/consumption flows.
"""

import argparse
import json
import logging
import os
import sys
import time
from datetime import datetime
from typing import Callable, Optional

import requests

from tractusx_sdk.dataspace.services.connector import ServiceFactory
from tractusx_sdk.dataspace.services.connector.base_connector_provider import (
    BaseConnectorProviderService,
)

# ============================================================================
# CONSTANTS
# ============================================================================

CONTENT_TYPE_JSON = "application/json"
LOG_RESPONSE_SUFFIX = " - Response: %s"
MANAGEMENT_PATH = "/management"

# ============================================================================
# DEFAULT DATA — Shared across all TCK scripts
# ============================================================================

SAMPLE_ASPECT_MODEL_DATA = {
    "businessPartnerNumber": "BPNL0000000093Q7",
    "enclosedSites": [
        {
            "areaOfApplication": (
                "Development, Marketing und Sales and also "
                "Procurement for interior components"
            ),
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
        "validatorBpn": "BPNL0000000093Q7",
    },
    "validUntil": "2026-01-24",
    "validFrom": "2023-01-25",
    "trustLevel": "none",
    "type": {
        "certificateVersion": "2015",
        "certificateType": "ISO9001",
    },
    "areaOfApplication": (
        "Development, Marketing und Sales and also "
        "Procurement for interior components"
    ),
    "issuer": {
        "issuerName": "TÜV",
        "issuerBpn": "BPNL133631123120",
    },
}

DEFAULT_ASSET_CONFIG = {
    "dct_type": "https://w3id.org/catenax/taxonomy#Submodel",
    "semantic_id": (
        "urn:samm:io.catenax.business_partner_certificate:"
        "3.1.0#BusinessPartnerCertificate"
    ),
    "version": "1.0",
    "proxy_params": {
        "proxyQueryParams": "true",
        "proxyPath": "true",
        "proxyMethod": "true",
        "proxyBody": "false",
    },
}

# ============================================================================
# LOGGING
# ============================================================================


def setup_tck_logging(
    test_case_name: str,
    script_dir: str,
) -> tuple:
    """
    Set up TCK logging with console + timestamped file handlers.

    Args:
        test_case_name: Name of the test case (used for log directory and file names).
        script_dir: Directory of the calling script (for log file placement).

    Returns:
        Tuple of (logger, log_file_path).
    """
    now = datetime.now()
    run_date = now.strftime("%Y-%m-%d")
    run_time = now.strftime("%H%M%S")
    log_dir = os.path.join(script_dir, "logs", test_case_name, run_date)
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, f"{run_time}_{test_case_name}.log")
    log_format = "%(asctime)s %(levelname)s [%(name)s] %(message)s"

    file_handler = logging.FileHandler(log_file, mode="w", encoding="utf-8")
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(logging.Formatter(log_format))

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(logging.Formatter(log_format))

    logging.basicConfig(
        level=logging.INFO,
        handlers=[console_handler, file_handler],
        force=True,
    )

    logger = logging.getLogger(test_case_name)
    logger.info("Logging to file: %s", log_file)
    return logger, log_file


def finalize_log(log_file: str, result: str):
    """Flush and close log handlers, then rename log file with PASS or FAIL result."""
    for handler in logging.root.handlers[:]:
        handler.flush()
        handler.close()
    final_log = log_file.replace(".log", f"_{result}.log")
    os.rename(log_file, final_log)
    sys.stdout.write(f"Log saved as: {final_log}\n")
    sys.stdout.flush()


def print_header(logger: logging.Logger, title: str):
    """Log section header with 80-char ``=`` border (detailed style)."""
    logger.info("\n%s\n  %s\n%s", "=" * 80, title, "=" * 80)


def print_separator(logger: logging.Logger, title: str = ""):
    """Log separator line with 70-char ``=`` border (simple style)."""
    if title:
        logger.info("\n%s\n  %s\n%s", "=" * 70, title, "=" * 70)
    else:
        logger.info("\n%s", "=" * 70)


# ============================================================================
# SERVICE INITIALIZATION
# ============================================================================


def initialize_provider_service(
    logger: logging.Logger,
    provider_config: dict,
    header_fn: Optional[Callable] = None,
):
    """
    Initialize the Provider Connector Service.

    Args:
        logger: Logger instance.
        provider_config: Provider connector configuration dict.
        header_fn: Function ``(title) -> None`` to print section header.
            Defaults to :func:`print_header`.

    Returns:
        ConnectorProviderService instance.
    """
    if header_fn is None:
        def header_fn(title):
            print_header(logger, title)

    header_fn("Initializing Provider Connector Service")

    provider_headers = {
        provider_config["api_key_header"]: provider_config["api_key"],
        "Content-Type": CONTENT_TYPE_JSON,
    }

    provider_service = ServiceFactory.get_connector_provider_service(
        dataspace_version=provider_config["dataspace_version"],
        base_url=provider_config["base_url"],
        dma_path=provider_config["dma_path"],
        headers=provider_headers,
        verbose=True,
        debug=True,
        verify_ssl=False,
        logger=logger,
    )

    identity_value = provider_config.get("bpn", provider_config.get("did", "N/A"))
    identity_label = "BPN" if "bpn" in provider_config else "DID"

    logger.info("✓ Provider service initialized")
    logger.info("  - Base URL: %s", provider_config["base_url"])
    logger.info("  - Dataspace Version: %s", provider_config["dataspace_version"])
    logger.info("  - %s: %s", identity_label, identity_value)

    return provider_service


def initialize_consumer_service(
    logger: logging.Logger,
    consumer_config: dict,
    header_fn: Optional[Callable] = None,
    connection_manager=None,
):
    """
    Initialize the Consumer Connector Service.

    Args:
        logger: Logger instance.
        consumer_config: Consumer connector configuration dict.
        header_fn: Function ``(title) -> None`` to print section header.
            Defaults to :func:`print_header`.
        connection_manager: Optional connection manager for EDR caching.

    Returns:
        ConnectorConsumerService instance.
    """
    if header_fn is None:
        def header_fn(title):
            print_header(logger, title)

    header_fn("Initializing Consumer Connector Service")

    consumer_headers = {
        consumer_config["api_key_header"]: consumer_config["api_key"],
        "Content-Type": CONTENT_TYPE_JSON,
    }

    consumer_service = ServiceFactory.get_connector_consumer_service(
        dataspace_version=consumer_config["dataspace_version"],
        base_url=consumer_config["base_url"],
        dma_path=consumer_config["dma_path"],
        headers=consumer_headers,
        connection_manager=connection_manager,
        verbose=True,
        debug=True,
        verify_ssl=False,
        logger=logger,
    )

    identity_value = consumer_config.get("bpn", consumer_config.get("did", "N/A"))
    identity_label = "BPN" if "bpn" in consumer_config else "DID"

    logger.info("✓ Consumer service initialized")
    logger.info("  - Base URL: %s", consumer_config["base_url"])
    logger.info("  - Dataspace Version: %s", consumer_config["dataspace_version"])
    logger.info("  - %s: %s", identity_label, identity_value)

    return consumer_service


# ============================================================================
# BACKEND DATA OPERATIONS
# ============================================================================


def upload_sample_data(
    logger: logging.Logger,
    backend_config: dict,
    sample_data: dict,
    header_fn: Optional[Callable] = None,
    verbose: bool = False,
):
    """
    Upload sample aspect model data to backend storage.

    Args:
        logger: Logger instance.
        backend_config: Backend configuration dict.
        sample_data: Sample data dict to upload.
        header_fn: Function ``(title) -> None`` to print section header.
        verbose: If True, log request/response bodies (detailed mode).
    """
    if header_fn is None:
        def header_fn(title):
            print_header(logger, title)

    header_fn("PHASE 0: Uploading Sample Data to Backend Storage")

    headers = {"Content-Type": CONTENT_TYPE_JSON}
    if backend_config.get("api_key"):
        headers[backend_config.get("api_key_header", "X-Api-Key")] = backend_config["api_key"]

    if verbose:
        payload = json.dumps(sample_data, indent=2)
        logger.info(
            "Uploading BusinessPartnerCertificate aspect model to: %s",
            backend_config["base_url"],
        )
        logger.info("[UPLOAD REQUEST]:\n%s", payload)

    try:
        if verbose:
            response = requests.post(
                backend_config["base_url"],
                data=json.dumps(sample_data, indent=2),
                headers=headers,
                verify=True,
                timeout=30,
            )
        else:
            logger.info("[UPLOAD REQUEST]: POST %s", backend_config["base_url"])
            response = requests.post(
                backend_config["base_url"],
                json=sample_data,
                headers=headers,
                verify=True,
                timeout=30,
            )

        if verbose:
            logger.info("[UPLOAD RESPONSE] Status: %s", response.status_code)
            logger.info("[UPLOAD RESPONSE] Body:\n%s", response.text)

        if response.status_code not in (200, 201, 204):
            raise RuntimeError(
                f"Backend upload failed with status {response.status_code}: {response.text}"
            )

        logger.info("✓ Sample data uploaded successfully (%s)", response.status_code)
    except Exception as exc:
        logger.exception("✗ Failed to upload sample data: %s", exc)
        raise


# ============================================================================
# DATA ACCESS
# ============================================================================


def access_data_with_edr(
    logger: logging.Logger,
    dataplane_url: str,
    access_token: str,
    header_fn: Optional[Callable] = None,
    path: str = "/",
    verify: bool = False,
):
    """
    Access data using EDR (Endpoint Data Reference).

    Args:
        logger: Logger instance.
        dataplane_url: The data plane endpoint from EDR.
        access_token: The authorization token from EDR.
        header_fn: Function ``(title) -> None`` to print section header.
        path: Optional path to append to the endpoint.
        verify: Whether to verify SSL certificates. Defaults to False.

    Returns:
        ``requests.Response`` from the data plane.
    """
    if header_fn is None:
        def header_fn(title):
            print_header(logger, title)

    header_fn("PHASE 3: Accessing Data with EDR")

    try:
        logger.info("Making request to: %s%s", dataplane_url, path)
        data_request_params = {
            "method": "GET",
            "url": f"{dataplane_url}{path}",
            "headers": {
                "Authorization": (
                    access_token[:50] + "..."
                    if access_token and len(access_token) > 50
                    else access_token
                )
            },
        }
        logger.info("[DATA ACCESS REQUEST]:\n%s", json.dumps(data_request_params, indent=2))

        response = requests.get(
            f"{dataplane_url}{path}",
            headers={"Authorization": access_token},
            verify=verify,
            timeout=30,
        )
        logger.info("✓ Response received: HTTP %s", response.status_code)

        if response.status_code == 200:
            logger.info(
                "  - Content-Type: %s",
                response.headers.get("Content-Type", "unknown"),
            )
            logger.info("  - Content-Length: %s bytes", len(response.content))
            try:
                logger.info("[DATA RESPONSE]:\n%s", json.dumps(response.json(), indent=2))
            except Exception:
                logger.info("[DATA RESPONSE (raw)]:\n%s", response.text)
        else:
            logger.error("✗ Request failed: %s", response.text)

        return response

    except Exception as exc:
        logger.exception("✗ Failed to access data: %s", exc)
        raise


# ============================================================================
# CLEANUP
# ============================================================================


def cleanup_provider_resources(
    logger: logging.Logger,
    provider_service,
    provision_ids: dict,
    header_fn: Optional[Callable] = None,
):
    """
    Delete all created resources from Provider (in reverse order of creation).

    Args:
        logger: Logger instance.
        provider_service: Initialized ConnectorProviderService.
        provision_ids: Dict containing resource IDs to delete.
        header_fn: Function ``(title) -> None`` to print section header.
    """
    if header_fn is None:
        def header_fn(title):
            print_header(logger, title)

    header_fn("CLEANUP: Deleting Provider Resources")

    resources = [
        ("Contract Definition", provision_ids["contract_def_id"], provider_service.contract_definitions),
        ("Asset", provision_ids["asset_id"], provider_service.assets),
        ("Usage Policy", provision_ids["usage_policy_id"], provider_service.policies),
        ("Access Policy", provision_ids["access_policy_id"], provider_service.policies),
    ]

    for resource_type, resource_id, controller in resources:
        try:
            controller.delete(resource_id)
            logger.info("✓ Deleted %s: %s", resource_type, resource_id)
        except Exception as exc:
            logger.error("✗ Failed to delete %s %s: %s", resource_type, resource_id, exc)


def cleanup_backend_data(
    logger: logging.Logger,
    backend_config: dict,
    header_fn: Optional[Callable] = None,
    verify: bool = False,
):
    """
    Delete test data from backend storage.

    Args:
        logger: Logger instance.
        backend_config: Backend configuration dict.
        header_fn: Function ``(title) -> None`` to print section header.
        verify: Whether to verify SSL certificates. Defaults to False.
    """
    if header_fn is None:
        def header_fn(title):
            print_header(logger, title)

    header_fn("CLEANUP: Deleting Backend Data")

    try:
        headers: dict = {}
        if backend_config.get("api_key"):
            headers[backend_config.get("api_key_header", "X-Api-Key")] = backend_config["api_key"]

        logger.info("Deleting data from backend: %s", backend_config["base_url"])
        response = requests.delete(
            backend_config["base_url"],
            headers=headers if headers else None,
            verify=verify,
            timeout=30,
        )

        if response.status_code in (200, 204, 404):
            logger.info("✓ Backend data deleted successfully (status: %s)", response.status_code)
        else:
            logger.warning(
                "⚠ Backend delete returned status %s: %s",
                response.status_code,
                response.text,
            )

    except Exception as exc:
        logger.error("✗ Failed to delete backend data: %s", exc)


# ============================================================================
# TEST RUNNER UTILITIES
# ============================================================================


def run_step(steps: list, name: str, fn: Callable):
    """
    Execute a test step function, record timing and PASS/FAIL.

    Args:
        steps: List to append step results to.
        name: Name of the step.
        fn: Callable to execute.

    Returns:
        Result of *fn()* if successful.

    Raises:
        Exception: Re-raises any exception from *fn()*.
    """
    t0 = time.time()
    try:
        result = fn()
        steps.append({"name": name, "result": "PASS", "duration_s": time.time() - t0})
        return result
    except Exception:
        steps.append({"name": name, "result": "FAIL", "duration_s": time.time() - t0})
        raise


def mark_skipped_phases(steps: list, all_phase_names: list):
    """Mark any phases not yet recorded in *steps* as ``SKIP``."""
    completed = {s["name"] for s in steps}
    for phase in all_phase_names:
        if phase not in completed:
            steps.append({"name": phase, "result": "SKIP", "duration_s": None})


def print_summary(
    logger: logging.Logger,
    steps: list,
    overall_result: str,
    total_elapsed: float,
    title: str = "E2E TEST RUN SUMMARY",
    provision_ids: Optional[dict] = None,
    consumption_result: Optional[dict] = None,
    http_status: Optional[int] = None,
):
    """
    Print a formatted test summary table.

    Args:
        logger: Logger instance.
        steps: List of step dicts with ``name``, ``result``, ``duration_s``.
        overall_result: Overall ``PASS`` / ``FAIL`` result string.
        total_elapsed: Total elapsed time in seconds.
        title: Summary table title header.
        provision_ids: Optional dict with ``asset_id``, ``access_policy_id``, etc.
        consumption_result: Optional dict with ``contract_agreement_id``, ``transfer_id``, etc.
        http_status: Optional HTTP status code (for simple mode).
    """
    w = 80
    passed = sum(1 for s in steps if s["result"] == "PASS")
    failed = sum(1 for s in steps if s["result"] == "FAIL")
    skipped = sum(1 for s in steps if s["result"] == "SKIP")

    verdict = (
        f"  RESULT: {overall_result}  |  {passed} passed  {failed} failed  "
        f"{skipped} skipped  |  Total: {total_elapsed:.1f}s"
    )

    col_name = 45
    col_res = 6
    col_dur = 8

    lines = [
        "",
        "╔" + "=" * (w - 2) + "╗",
        "║" + f"  {title}".center(w - 2) + "║",
        "╠" + "=" * (w - 2) + "╣",
        "║"
        + f"  {'STEP':<{col_name}} {'RESULT':>{col_res}}  {'TIME':>{col_dur}}".ljust(w - 2)
        + "║",
        "║" + "  " + "-" * (w - 6) + "  ║"[:-2] + "║",
    ]
    for s in steps:
        is_pass = s["result"] == "PASS"
        is_fail = s["result"] == "FAIL"
        if is_pass:
            icon = "✓"
        elif is_fail:
            icon = "✗"
        else:
            icon = "-"
        dur = f"{s['duration_s']:.1f}s" if s["duration_s"] is not None else "  -"
        line = f"  {icon} {s['name']:<{col_name - 2}} {s['result']:>{col_res}}  {dur:>{col_dur}}"
        lines.append("║" + line.ljust(w - 2) + "║")
    lines += [
        "╠" + "=" * (w - 2) + "╣",
        "║" + verdict.ljust(w - 2) + "║",
        "╚" + "=" * (w - 2) + "╝",
    ]

    has_resources = provision_ids or consumption_result or http_status is not None
    if has_resources:
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
    if http_status is not None:
        lines.append(f"  Data HTTP         : {http_status}")
    lines.append("")
    logger.info("\n".join(lines))


# ============================================================================
# CLI UTILITIES
# ============================================================================


def build_tck_cli_parser(
    description: str,
    epilog: str = "",
    include_did: bool = False,
) -> argparse.ArgumentParser:
    """
    Build the standard TCK CLI argument parser.

    Args:
        description: Parser description text.
        epilog: Optional epilog text with examples.
        include_did: If True, add ``--provider-did`` / ``--consumer-did`` options.

    Returns:
        Configured ``ArgumentParser``.
    """
    parser = argparse.ArgumentParser(
        description=description,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=epilog,
    )
    # Runtime options
    parser.add_argument(
        "--no-debug",
        action="store_false",
        dest="debug",
        help="Disable DEBUG-level logging (enabled by default)",
    )
    parser.add_argument(
        "--no-cleanup",
        action="store_false",
        dest="cleanup",
        help="Skip cleanup of provider resources and backend data (cleanup enabled by default)",
    )
    # Provider configuration
    parser.add_argument("--provider-url", help="Provider EDC base URL")
    parser.add_argument("--provider-api-key", help="Provider EDC API key")
    parser.add_argument("--provider-bpn", help="Provider Business Partner Number")
    parser.add_argument("--provider-dsp-url", help="Provider DSP endpoint URL")
    # Consumer configuration
    parser.add_argument("--consumer-url", help="Consumer EDC base URL")
    parser.add_argument("--consumer-api-key", help="Consumer EDC API key")
    parser.add_argument("--consumer-bpn", help="Consumer Business Partner Number")
    # Backend configuration
    parser.add_argument("--backend-url", help="Backend storage URL")
    parser.add_argument("--backend-api-key", help="Backend API key (if required)")

    if include_did:
        parser.add_argument(
            "--provider-did",
            help="Provider DID (e.g., did:web:provider.example.com)",
        )
        parser.add_argument(
            "--consumer-did",
            help="Consumer DID (e.g., did:web:consumer.example.com)",
        )

    return parser


def apply_cli_overrides(
    args,
    provider_config: dict,
    consumer_config: dict,
    backend_config: dict,
) -> tuple:
    """
    Apply CLI argument overrides to configuration dicts.

    Args:
        args: Parsed ``argparse.Namespace``.
        provider_config: Provider configuration dict (will be copied).
        consumer_config: Consumer configuration dict (will be copied).
        backend_config: Backend configuration dict (will be copied).

    Returns:
        Tuple of ``(provider_config, consumer_config, backend_config)`` copies.
    """
    p_cfg = provider_config.copy()
    c_cfg = consumer_config.copy()
    b_cfg = backend_config.copy()

    if getattr(args, "provider_url", None):
        p_cfg["base_url"] = args.provider_url
    if getattr(args, "provider_api_key", None):
        p_cfg["api_key"] = args.provider_api_key
    if getattr(args, "provider_bpn", None):
        p_cfg["bpn"] = args.provider_bpn
    if getattr(args, "provider_dsp_url", None):
        p_cfg["dsp_url"] = args.provider_dsp_url
    if getattr(args, "provider_did", None):
        p_cfg["did"] = args.provider_did

    if getattr(args, "consumer_url", None):
        c_cfg["base_url"] = args.consumer_url
    if getattr(args, "consumer_api_key", None):
        c_cfg["api_key"] = args.consumer_api_key
    if getattr(args, "consumer_bpn", None):
        c_cfg["bpn"] = args.consumer_bpn
    if getattr(args, "consumer_did", None):
        c_cfg["did"] = args.consumer_did

    if getattr(args, "backend_url", None):
        b_cfg["base_url"] = args.backend_url
    if getattr(args, "backend_api_key", None):
        b_cfg["api_key"] = args.backend_api_key

    return p_cfg, c_cfg, b_cfg


def configure_debug_logging(logger: logging.Logger, debug: bool):
    """Configure debug logging level based on CLI flag."""
    if debug:
        logging.root.setLevel(logging.DEBUG)
        for h in logging.root.handlers:
            h.setLevel(logging.DEBUG)
        logger.info("DEBUG logging enabled")
    else:
        logger.info("DEBUG logging disabled (use without --no-debug to enable)")


def log_config_warning(logger: logging.Logger):
    """Log the standard configuration warning."""
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


# ============================================================================
# SIMPLE FLOW HELPERS
# ============================================================================


def provision_simple(
    logger: logging.Logger,
    provider: BaseConnectorProviderService,
    access_policy_config: dict,
    usage_policy_config: dict,
    asset_config: dict,
    backend_config: dict,
    consumer_config: dict,
    header_fn: Optional[Callable] = None,
    id_prefix: str = "e2e",
) -> dict:
    """
    Phase 1 (simple): Provider provisions data.

    Creates asset, access/usage policies, and contract definition.
    Handles ``context``/``profile`` if present in policy configs.
    Handles BPN and DID identity substitution in access policy constraints.

    Args:
        logger: Logger instance.
        provider: Initialized provider service.
        access_policy_config: Access policy configuration.
        usage_policy_config: Usage policy configuration.
        asset_config: Asset configuration.
        backend_config: Backend configuration.
        consumer_config: Consumer configuration (for BPN/DID).
        header_fn: Function ``(title) -> None`` to print section header.
        id_prefix: Prefix for generated resource IDs.

    Returns:
        Dict with ``asset_id``, ``access_policy_id``, ``usage_policy_id``, ``contract_def_id``.
    """
    if header_fn is None:
        def header_fn(title):
            print_separator(logger, title)

    header_fn("PHASE 1: Provider Data Provision")

    ts = int(time.time())
    asset_id = f"simple-{id_prefix}-asset-{ts}"
    access_policy_id = f"simple-{id_prefix}-access-{ts}"
    usage_policy_id = f"simple-{id_prefix}-usage-{ts}"
    contract_def_id = f"simple-{id_prefix}-contract-{ts}"

    # Handle constraint substitution (BPN or DID)
    access_permissions = [p.copy() for p in access_policy_config["permissions"]]
    constraint = access_permissions[0].get("constraint", {})
    left_operand = constraint.get("leftOperand", "")
    if "BusinessPartnerDID" in left_operand and "did" in consumer_config:
        constraint["rightOperand"] = consumer_config["did"]
    elif constraint.get("rightOperand") is None and "bpn" in consumer_config:
        constraint["rightOperand"] = consumer_config["bpn"]

    # Build optional policy kwargs (context / profile)
    access_kwargs: dict = {}
    if "context" in access_policy_config:
        access_kwargs["context"] = access_policy_config["context"]
    if "profile" in access_policy_config:
        access_kwargs["profile"] = access_policy_config["profile"]

    usage_kwargs: dict = {}
    if "context" in usage_policy_config:
        usage_kwargs["context"] = usage_policy_config["context"]
    if "profile" in usage_policy_config:
        usage_kwargs["profile"] = usage_policy_config["profile"]

    logger.info("[ACCESS POLICY REQUEST]: Creating policy %s", access_policy_id)
    provider.create_policy(
        policy_id=access_policy_id,
        permissions=access_permissions,
        **access_kwargs,
    )
    logger.info("✓ Access policy:      %s", access_policy_id)

    logger.info("[USAGE POLICY REQUEST]: Creating policy %s", usage_policy_id)
    provider.create_policy(
        policy_id=usage_policy_id,
        permissions=usage_policy_config["permissions"],
        **usage_kwargs,
    )
    logger.info("✓ Usage policy:       %s", usage_policy_id)

    logger.info("[ASSET REQUEST]: Creating asset %s", asset_id)
    provider.create_asset(
        asset_id=asset_id,
        base_url=backend_config["base_url"],
        dct_type=asset_config["dct_type"],
        semantic_id=asset_config["semantic_id"],
        version=asset_config["version"],
        proxy_params=asset_config["proxy_params"],
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
        "asset_id": asset_id,
        "access_policy_id": access_policy_id,
        "usage_policy_id": usage_policy_id,
        "contract_def_id": contract_def_id,
    }


def consume_simple_bpnl(
    logger: logging.Logger,
    consumer,
    asset_id: str,
    provider_config: dict,
    accepted_policies=None,
    header_fn: Optional[Callable] = None,
    verify: bool = False,
):
    """
    Phase 2 (simple / BPNL): Consumer calls ``do_get_with_bpnl`` — SDK handles everything.

    Args:
        logger: Logger instance.
        consumer: Initialized consumer service.
        asset_id: The asset ID to consume.
        provider_config: Provider config with ``bpn`` and ``dsp_url``.
        accepted_policies: Optional accepted policies list.
        header_fn: Function ``(title) -> None`` to print section header.
        verify: Whether to verify SSL certificates. Defaults to False.

    Returns:
        ``requests.Response`` from the data source.
    """
    if header_fn is None:
        def header_fn(title):
            print_separator(logger, title)

    header_fn("PHASE 2: Consumer — do_get_with_bpnl")
    logger.info(
        "Calling do_get_with_bpnl() — SDK handles catalog → negotiate → transfer → EDR → GET"
    )

    filter_expression = [
        consumer.get_filter_expression(
            key=consumer.DEFAULT_ID_KEY,
            value=asset_id,
            operator="=",
        )
    ]

    logger.info(
        "[DO_GET REQUEST]: BPNL=%s, asset_id=%s, path=/",
        provider_config["bpn"],
        asset_id,
    )
    response = consumer.do_get_with_bpnl(
        bpnl=provider_config["bpn"],
        counter_party_address=provider_config["dsp_url"],
        filter_expression=filter_expression,
        policies=accepted_policies,
        path="/",
        verify=verify,
    )

    logger.info("✓ Response: HTTP %s", response.status_code)
    return response


def consume_simple_did(
    logger: logging.Logger,
    consumer,
    asset_id: str,
    provider_config: dict,
    accepted_policies=None,
    header_fn: Optional[Callable] = None,
    verify: bool = False,
):
    """
    Phase 2 (simple / DID): Consumer calls ``do_get`` with DID — SDK handles everything.

    Args:
        logger: Logger instance.
        consumer: Initialized consumer service.
        asset_id: The asset ID to consume.
        provider_config: Provider config with ``did`` and ``dsp_url``.
        accepted_policies: Optional accepted policies list.
        header_fn: Function ``(title) -> None`` to print section header.
        verify: Whether to verify SSL certificates. Defaults to False.

    Returns:
        ``requests.Response`` from the data source.
    """
    if header_fn is None:
        def header_fn(title):
            print_separator(logger, title)

    header_fn("PHASE 2: Consumer — do_get (DID-based)")
    logger.info(
        "Calling do_get() — SDK handles catalog → negotiate → transfer → EDR → GET"
    )
    logger.info("No BPNL discovery needed — using provider DID directly")

    filter_expression = [
        consumer.get_filter_expression(
            key=consumer.DEFAULT_ID_KEY,
            value=asset_id,
            operator="=",
        )
    ]

    logger.info(
        "[DO_GET REQUEST]: counter_party_id=%s, asset_id=%s, path=/",
        provider_config["did"],
        asset_id,
    )
    response = consumer.do_get(
        counter_party_id=provider_config["did"],
        counter_party_address=provider_config["dsp_url"],
        filter_expression=filter_expression,
        policies=accepted_policies,
        path="/",
        verify=verify,
    )

    logger.info("✓ Response: HTTP %s", response.status_code)
    return response
