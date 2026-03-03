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
Test runners for TCK (Technology Compatibility Kit) E2E connector tests.

Provides high-level entry points that handle the complete lifecycle:
logging -> CLI parsing -> service init -> test phases -> summary -> cleanup -> log finalization.

Each runner takes a typed configuration dataclass and a ``script_dir`` path,
then drives the entire test run autonomously.
"""

from __future__ import annotations

import copy
import json
import os
import os
import sys
import time
import uuid as _uuid
from typing import TYPE_CHECKING

try:
    import yaml as _yaml
    _YAML_AVAILABLE = True
except ImportError:
    _YAML_AVAILABLE = False

from .helpers import (
    SAMPLE_ASPECT_MODEL_DATA,
    setup_tck_logging,
    finalize_log,
    print_header,
    print_separator,
    initialize_provider_service,
    initialize_consumer_service,
    upload_sample_data,
    access_data_with_edr,
    provision_simple,
    consume_simple_bpnl,
    consume_simple_did,
    cleanup_provider_resources,
    cleanup_backend_data,
    run_step,
    mark_skipped_phases,
    print_summary,
    build_tck_cli_parser,
    configure_debug_logging,
)

if TYPE_CHECKING:
    from .models import DetailedTckConfig, SimpleTckConfig


# ============================================================================
# CONSTANTS
# ============================================================================

_PHASE_0_NAME = "Phase 0 · Upload sample data to backend"
_PHASE_1_NAME = "Phase 1 · Provider data provision"
_PHASE_2_SIMPLE_BPNL = "Phase 2 · do_get_with_bpnl (catalog→negotiate→transfer→EDR→GET)"
_PHASE_2_SIMPLE_DID = "Phase 2 · do_get (catalog→negotiate→transfer→EDR→GET)"
_PHASE_2_DETAILED = "Phase 2 · Consumer data consumption (catalog→negotiate→transfer→EDR)"
_PHASE_3_NAME = "Phase 3 · Access data with EDR"

_VOCAB_KEY = "@vocab"
_EDC_NAMESPACE = "https://w3id.org/edc/v0.0.1/ns/"

_DEFAULT_SATURN_NEGOTIATION_CONTEXT: list = [
    "https://w3id.org/catenax/2025/9/policy/odrl.jsonld",
    "https://w3id.org/catenax/2025/9/policy/context.jsonld",
    {_VOCAB_KEY: _EDC_NAMESPACE},
]

_MAX_POLL_WAIT = 60
_POLL_INTERVAL = 2


# ============================================================================
# CLI → CONFIG HELPERS
# ============================================================================


def _load_yaml_section(yaml_path: str, section: str) -> dict:
    """Load a single section from a YAML config file.

    Args:
        yaml_path: Path to the YAML config file.
        section: Section key to load (e.g. 'jupiter', 'saturn').

    Returns:
        Raw dict for that section.

    Raises:
        ImportError: If PyYAML is not installed.
        KeyError: If the section is not found.
    """
    if not _YAML_AVAILABLE:
        raise ImportError(
            "PyYAML is required to use --config.\n"
            "Install it with: pip install pyyaml"
        )
    with open(yaml_path, "r", encoding="utf-8") as fh:
        data = _yaml.safe_load(fh)
    if section not in data:
        available = ", ".join(str(k) for k in data.keys())
        raise KeyError(
            f"Section '{section}' not found in '{yaml_path}'. "
            f"Available sections: {available}"
        )
    return data[section]


def _yaml_section_to_config(raw: dict, cfg_provider, cfg_consumer, cfg_backend,
                             cfg_access_policy, cfg_usage_policy):
    """Apply a raw YAML section dict onto existing config field objects in-place."""
    from .models import ConnectorConfig, BackendConfig, PolicyConfig

    def _mk_connector(src: dict) -> ConnectorConfig:
        return ConnectorConfig(
            base_url=src.get("base_url", ""),
            dma_path=src.get("dma_path") or "/management",
            api_key=src.get("api_key") or "",
            dataspace_version=cfg_provider.dataspace_version,
            bpn=src.get("bpn") or None,
            dsp_url=src.get("dsp_url") or None,
            did=src.get("did") or None,
        )

    def _mk_policy(src: dict) -> PolicyConfig:
        return PolicyConfig(
            context=src.get("context") or None,
            permissions=src.get("permissions") or [],
            profile=src.get("profile") or None,
        )

    new_provider = _mk_connector(raw.get("provider", {}))
    new_consumer = _mk_connector(raw.get("consumer", {}))

    backend_raw = raw.get("backend", {})
    backend_base = (backend_raw.get("base_url") or "").rstrip("/")
    new_backend = BackendConfig(
        base_url=f"{backend_base}/urn:uuid:{_uuid.uuid4()}" if backend_base else cfg_backend.base_url,
        api_key=backend_raw.get("api_key") or None,
    )

    pol = raw.get("policies", {})
    new_access = _mk_policy(pol.get("access_policy") or {})
    new_usage = _mk_policy(pol.get("usage_policy") or {})
    protocol = pol.get("protocol") or None
    negotiation_context = pol.get("negotiation_context") or None

    return new_provider, new_consumer, new_backend, new_access, new_usage, protocol, negotiation_context


def _apply_cli_to_simple_config(
    args,
    config: SimpleTckConfig,
) -> SimpleTckConfig:
    """Apply CLI argument overrides to a :class:`SimpleTckConfig`.

    Returns a deep copy — the original config is never mutated.

    If ``--config <path>`` is given, connectivity and policy values are
    reloaded from that YAML file first; individual ``--provider-url`` etc.
    args then take precedence over the YAML values.
    """
    cfg = copy.deepcopy(config)

    # ── YAML config file reload (--config) ───────────────────────────
    yaml_path = getattr(args, "config", None)
    if yaml_path:
        section = getattr(args, "config_section", None) or cfg.config_section
        if not section:
            raise ValueError(
                "--config requires --config-section (or a config_section set on the test config)."
            )
        raw = _load_yaml_section(yaml_path, section)
        (cfg.provider, cfg.consumer, cfg.backend,
         cfg.access_policy, cfg.usage_policy, _, _) = _yaml_section_to_config(
            raw, cfg.provider, cfg.consumer, cfg.backend,
            cfg.access_policy, cfg.usage_policy,
        )
        # DID-mode: prefer dsp_url_did over dsp_url when available
        if cfg.discovery_mode == "did":
            _dsp_url_did = raw.get("provider", {}).get("dsp_url_did")
            if _dsp_url_did:
                cfg.provider.dsp_url = _dsp_url_did

    # ── Individual field overrides (take precedence over YAML) ──────
    # Provider overrides
    if getattr(args, "provider_url", None):
        cfg.provider.base_url = args.provider_url
    if getattr(args, "provider_dma_path", None):
        cfg.provider.dma_path = args.provider_dma_path
    if getattr(args, "provider_api_key", None):
        cfg.provider.api_key = args.provider_api_key
    if getattr(args, "provider_bpn", None):
        cfg.provider.bpn = args.provider_bpn
    if getattr(args, "provider_dsp_url", None):
        cfg.provider.dsp_url = args.provider_dsp_url
    if getattr(args, "provider_dsp_url_did", None) and cfg.discovery_mode == "did":
        cfg.provider.dsp_url = args.provider_dsp_url_did
    if getattr(args, "provider_did", None):
        cfg.provider.did = args.provider_did

    # Consumer overrides
    if getattr(args, "consumer_url", None):
        cfg.consumer.base_url = args.consumer_url
    if getattr(args, "consumer_dma_path", None):
        cfg.consumer.dma_path = args.consumer_dma_path
    if getattr(args, "consumer_api_key", None):
        cfg.consumer.api_key = args.consumer_api_key
    if getattr(args, "consumer_bpn", None):
        cfg.consumer.bpn = args.consumer_bpn
    if getattr(args, "consumer_did", None):
        cfg.consumer.did = args.consumer_did

    # Backend overrides
    if getattr(args, "backend_url", None):
        cfg.backend.base_url = args.backend_url
    if getattr(args, "backend_api_key", None):
        cfg.backend.api_key = args.backend_api_key

    # Runtime overrides — only override if the user explicitly passed --no-cleanup
    if getattr(args, "cleanup", None) is not None:
        cfg.cleanup = args.cleanup

    return cfg


def _apply_cli_to_detailed_config(
    args,
    config: DetailedTckConfig,
) -> DetailedTckConfig:
    """Apply CLI argument overrides to a :class:`DetailedTckConfig`.

    Returns a deep copy — the original config is never mutated.

    If ``--config <path>`` is given, connectivity and policy values are
    reloaded from that YAML file first; individual ``--provider-url`` etc.
    args then take precedence over the YAML values.
    """
    cfg = copy.deepcopy(config)

    # ── YAML config file reload (--config) ───────────────────────────
    yaml_path = getattr(args, "config", None)
    if yaml_path:
        section = getattr(args, "config_section", None) or cfg.config_section
        if not section:
            raise ValueError(
                "--config requires --config-section (or a config_section set on the test config)."
            )
        raw = _load_yaml_section(yaml_path, section)
        (cfg.provider, cfg.consumer, cfg.backend,
         cfg.access_policy, cfg.usage_policy,
         new_protocol, new_negotiation_context) = _yaml_section_to_config(
            raw, cfg.provider, cfg.consumer, cfg.backend,
            cfg.access_policy, cfg.usage_policy,
        )
        # DID-mode: prefer dsp_url_did over dsp_url when available
        if cfg.discovery_mode == "did":
            _dsp_url_did = raw.get("provider", {}).get("dsp_url_did")
            if _dsp_url_did:
                cfg.provider.dsp_url = _dsp_url_did
        if new_protocol:
            cfg.protocol = new_protocol
        if new_negotiation_context:
            cfg.negotiation_context = new_negotiation_context

    # ── Individual field overrides (take precedence over YAML) ──────
    # Provider overrides
    if getattr(args, "provider_url", None):
        cfg.provider.base_url = args.provider_url
    if getattr(args, "provider_dma_path", None):
        cfg.provider.dma_path = args.provider_dma_path
    if getattr(args, "provider_api_key", None):
        cfg.provider.api_key = args.provider_api_key
    if getattr(args, "provider_bpn", None):
        cfg.provider.bpn = args.provider_bpn
    if getattr(args, "provider_dsp_url", None):
        cfg.provider.dsp_url = args.provider_dsp_url
    if getattr(args, "provider_dsp_url_did", None) and cfg.discovery_mode == "did":
        cfg.provider.dsp_url = args.provider_dsp_url_did
    if getattr(args, "provider_did", None):
        cfg.provider.did = args.provider_did

    # Consumer overrides
    if getattr(args, "consumer_url", None):
        cfg.consumer.base_url = args.consumer_url
    if getattr(args, "consumer_dma_path", None):
        cfg.consumer.dma_path = args.consumer_dma_path
    if getattr(args, "consumer_api_key", None):
        cfg.consumer.api_key = args.consumer_api_key
    if getattr(args, "consumer_bpn", None):
        cfg.consumer.bpn = args.consumer_bpn
    if getattr(args, "consumer_did", None):
        cfg.consumer.did = args.consumer_did

    # Backend overrides
    if getattr(args, "backend_url", None):
        cfg.backend.base_url = args.backend_url
    if getattr(args, "backend_api_key", None):
        cfg.backend.api_key = args.backend_api_key

    # Runtime overrides — only override if the user explicitly passed --no-cleanup
    if getattr(args, "cleanup", None) is not None:
        cfg.cleanup = args.cleanup

    return cfg


# ============================================================================
# SIMPLE RUNNER
# ============================================================================


def run_simple_test(config: SimpleTckConfig, script_dir: str) -> str:
    """Run a complete **simple** TCK E2E test.

    This is the single entry point for simple connector TCK tests.  It handles:

    1. CLI argument parsing (``--provider-url``, ``--no-cleanup``, etc.)
    2. Logging setup (console + timestamped log file)
    3. Service initialization (provider + consumer)
    4. Phase 0 — upload sample data to backend
    5. Phase 1 — provider data provision (asset + policies + contract)
    6. Phase 2 — consumer data consumption via ``do_get_with_bpnl`` or ``do_get``
    7. Test summary with PASS/FAIL result
    8. Optional cleanup of created resources
    9. Log file finalization (renamed with PASS/FAIL suffix)

    Args:
        config: Complete test configuration (:class:`SimpleTckConfig`).
        script_dir: Directory of the calling script (for log file placement).

    Returns:
        ``"PASS"`` or ``"FAIL"`` result string.
    """
    # ── 1. CLI parsing ────────────────────────────────────────────────
    parser = build_tck_cli_parser(
        description=config.test_name,
        include_did=config.discovery_mode == "did",
    )
    args = parser.parse_args()
    # Resolve --config relative to the script's own directory so that a
    # bare filename like 'tck-int-config.yaml' works regardless of cwd.
    if getattr(args, "config", None) and not os.path.isabs(args.config):
        args.config = os.path.normpath(os.path.join(script_dir, args.config))
    config = _apply_cli_to_simple_config(args, config)

    # ── 2. Logging ────────────────────────────────────────────────────
    logger, log_file = setup_tck_logging(config.test_name, script_dir)
    configure_debug_logging(logger, args.debug)

    # ── 3. Derive runtime values ──────────────────────────────────────
    provider_dict = config.provider.to_dict()
    consumer_dict = config.consumer.to_dict()
    backend_dict = config.backend.to_dict()
    access_policy_dict = config.access_policy.to_dict()
    usage_policy_dict = config.usage_policy.to_dict()
    asset_dict = config.asset.to_dict()
    sample_data = config.sample_data or SAMPLE_ASPECT_MODEL_DATA

    is_did = config.discovery_mode == "did"
    banner = config.banner_title or config.test_name
    summary_title = config.summary_title or (
        "E2E TEST RUN SUMMARY  (simple DID-based)"
        if is_did
        else "E2E TEST RUN SUMMARY  (simple)"
    )
    phase2_name = _PHASE_2_SIMPLE_DID if is_did else _PHASE_2_SIMPLE_BPNL
    all_phases = [_PHASE_0_NAME, _PHASE_1_NAME, phase2_name]

    sep = lambda title: print_separator(logger, title)
    sep(banner)

    # ── 4. Initialize services ────────────────────────────────────────
    provider = initialize_provider_service(logger, provider_dict, header_fn=sep)
    consumer = initialize_consumer_service(logger, consumer_dict, header_fn=sep)

    overall_result = "FAIL"
    run_start = time.time()
    steps: list[dict] = []
    ids = None
    http_status = None

    try:
        # Phase 0 — upload sample data
        run_step(
            steps,
            _PHASE_0_NAME,
            lambda: upload_sample_data(
                logger, backend_dict, sample_data, header_fn=sep,
            ),
        )

        # Phase 1 — provider provisions data
        ids = run_step(
            steps,
            _PHASE_1_NAME,
            lambda: provision_simple(
                logger,
                provider,
                access_policy_dict,
                usage_policy_dict,
                asset_dict,
                backend_dict,
                consumer_dict,
                header_fn=sep,
            ),
        )

        logger.info("Waiting 3 s for provider EDC to process…")
        time.sleep(3)

        # Phase 2 — consumer consumes data
        def _consume_and_validate(fn):
            resp = fn()
            if resp.status_code != 200:
                raise RuntimeError(
                    f"Unexpected HTTP {resp.status_code}: {resp.text}"
                )
            try:
                logger.info(
                    "Response body:\n%s",
                    json.dumps(resp.json(), indent=2),
                )
            except Exception:
                logger.info("Response body:\n%s", resp.text)
            return resp

        if is_did:
            consume_fn = lambda: _consume_and_validate(lambda: consume_simple_did(
                logger,
                consumer,
                ids["asset_id"],
                provider_dict,
                config.accepted_policies,
                header_fn=sep,
                verify=config.verify_ssl,
            ))
        else:
            consume_fn = lambda: _consume_and_validate(lambda: consume_simple_bpnl(
                logger,
                consumer,
                ids["asset_id"],
                provider_dict,
                config.accepted_policies,
                header_fn=sep,
                verify=config.verify_ssl,
            ))

        response = run_step(steps, phase2_name, consume_fn)

        http_status = response.status_code if response is not None else None
        overall_result = "PASS"

    except Exception as exc:
        logger.exception("✗ Simple E2E FAILED: %s", exc)
        mark_skipped_phases(steps, all_phases)

    finally:
        print_summary(
            logger,
            steps,
            overall_result=overall_result,
            total_elapsed=time.time() - run_start,
            title=summary_title,
            provision_ids=ids,
            http_status=http_status,
        )
        sys.stdout.flush()

        if config.cleanup and ids:
            cleanup_provider_resources(logger, provider, ids, header_fn=sep)
            cleanup_backend_data(logger, backend_dict, header_fn=sep, verify=config.verify_ssl)

        finalize_log(log_file, overall_result)

    return overall_result


# ============================================================================
# DETAILED RUNNER
# ============================================================================


def _derive_negotiation_context(config: DetailedTckConfig) -> list:
    """Derive the negotiation ``@context`` list from a detailed config.

    Priority:
    1. Explicit ``config.negotiation_context`` if provided.
    2. Clone ``config.access_policy.context``, ensure EDC vocab is present.
    3. Fall back to the default Saturn negotiation context.
    """
    if config.negotiation_context is not None:
        return list(config.negotiation_context)

    if config.access_policy.context:
        ctx = list(config.access_policy.context)
        has_vocab = any(isinstance(e, dict) and _VOCAB_KEY in e for e in ctx)
        if not has_vocab:
            ctx.append({_VOCAB_KEY: _EDC_NAMESPACE})
        return ctx

    return list(_DEFAULT_SATURN_NEGOTIATION_CONTEXT)


def run_detailed_test(config: DetailedTckConfig, script_dir: str) -> str:
    """Run a complete **detailed** TCK E2E test.

    This is the single entry point for detailed connector TCK tests that
    execute the full step-by-step flow with verbose logging:

    1. CLI argument parsing
    2. Logging setup
    3. Service initialization
    4. Phase 0 — upload sample data to backend (verbose)
    5. Phase 1 — provider data provision (verbose, step-by-step)
    6. Phase 2 — consumer data consumption
       (catalog -> negotiate -> transfer -> EDR, with verbose logging)
    7. Phase 3 — access data with EDR
    8. Test summary with PASS/FAIL result
    9. Optional cleanup
    10. Log file finalization

    Args:
        config: Complete test configuration (:class:`DetailedTckConfig`).
        script_dir: Directory of the calling script (for log file placement).

    Returns:
        ``"PASS"`` or ``"FAIL"`` result string.
    """
    from tractusx_sdk.dataspace.models.connector.model_factory import ModelFactory

    # ── 1. CLI parsing ────────────────────────────────────────────────
    parser = build_tck_cli_parser(
        description=config.test_name,
        include_did=config.discovery_mode == "did",
    )
    args = parser.parse_args()
    # Resolve --config relative to the script's own directory so that a
    # bare filename like 'tck-int-config.yaml' works regardless of cwd.
    if getattr(args, "config", None) and not os.path.isabs(args.config):
        args.config = os.path.normpath(os.path.join(script_dir, args.config))
    config = _apply_cli_to_detailed_config(args, config)

    # ── 2. Logging ────────────────────────────────────────────────────
    logger, log_file = setup_tck_logging(config.test_name, script_dir)
    configure_debug_logging(logger, args.debug)

    # ── 3. Derive runtime values ──────────────────────────────────────
    provider_dict = config.provider.to_dict()
    consumer_dict = config.consumer.to_dict()
    backend_dict = config.backend.to_dict()
    access_policy_dict = config.access_policy.to_dict()
    usage_policy_dict = config.usage_policy.to_dict()
    asset_dict = config.asset.to_dict()
    sample_data = config.sample_data or SAMPLE_ASPECT_MODEL_DATA

    is_did = config.discovery_mode == "did"
    banner = config.banner_title or config.test_name
    summary_title = config.summary_title or (
        "E2E TEST RUN SUMMARY  (detailed DID-based)"
        if is_did
        else "E2E TEST RUN SUMMARY  (detailed)"
    )
    negotiation_ctx = _derive_negotiation_context(config)

    hdr = lambda title: print_header(logger, title)
    hdr(banner)

    logger.warning(
        "\n⚠️  IMPORTANT: Update the PLACEHOLDER values before running!\n"
        "%s\n"
        "Required configuration:\n"
        "  1. Provider connector URL, API key, BPN/DID, DSP URL\n"
        "  2. Consumer connector URL, API key, BPN/DID\n"
        "  3. Backend data source URL\n"
        "\nSee the configuration in your TCK script.\n"
        "%s",
        "=" * 80,
        "=" * 80,
    )

    # ── 4. Initialize services ────────────────────────────────────────
    provider = initialize_provider_service(logger, provider_dict, header_fn=hdr)
    consumer = initialize_consumer_service(logger, consumer_dict, header_fn=hdr)

    overall_result = "FAIL"
    run_start = time.time()
    steps: list[dict] = []
    provision_ids = None
    consumption_result = None

    all_phases = [_PHASE_0_NAME, _PHASE_1_NAME, _PHASE_2_DETAILED, _PHASE_3_NAME]

    try:
        # ── Phase 0: Upload sample data ───────────────────────────────
        run_step(
            steps,
            _PHASE_0_NAME,
            lambda: upload_sample_data(
                logger, backend_dict, sample_data,
                header_fn=hdr, verbose=True,
            ),
        )

        # ── Phase 1: Provider provisions data (verbose) ──────────────
        provision_ids = run_step(
            steps,
            _PHASE_1_NAME,
            lambda: _provision_detailed(
                logger, provider, access_policy_dict, usage_policy_dict,
                asset_dict, backend_dict, consumer_dict, hdr,
            ),
        )

        logger.info("Waiting 3 seconds for Provider EDC to process...")
        time.sleep(3)

        # ── Phase 2: Consumer consumes data (verbose) ─────────────────
        consumption_result = run_step(
            steps,
            _PHASE_2_DETAILED,
            lambda: _consume_detailed(
                logger, consumer, provision_ids["asset_id"],
                provider_dict, consumer_dict,
                config.protocol, negotiation_ctx,
                is_did, ModelFactory, hdr,
            ),
        )

        # ── Phase 3: Access data with EDR ─────────────────────────────
        def _access_and_validate():
            resp = access_data_with_edr(
                logger,
                dataplane_url=consumption_result["dataplane_url"],
                access_token=consumption_result["access_token"],
                header_fn=hdr,
                verify=config.verify_ssl,
            )
            if resp is not None and resp.status_code != 200:
                raise RuntimeError(f"Unexpected HTTP {resp.status_code}: {resp.text}")
            return resp

        run_step(steps, _PHASE_3_NAME, _access_and_validate)

        overall_result = "PASS"

    except Exception as exc:
        logger.exception("\n✗ E2E flow failed: %s", exc)
        mark_skipped_phases(steps, all_phases)

    finally:
        total_elapsed = time.time() - run_start
        print_summary(
            logger,
            steps,
            overall_result=overall_result,
            total_elapsed=total_elapsed,
            title=summary_title,
            provision_ids=provision_ids,
            consumption_result=consumption_result,
        )
        sys.stdout.flush()

        if config.cleanup:
            if provision_ids:
                cleanup_provider_resources(logger, provider, provision_ids, header_fn=hdr)
            if backend_dict.get("base_url"):
                cleanup_backend_data(logger, backend_dict, header_fn=hdr, verify=config.verify_ssl)

        finalize_log(log_file, overall_result)

    return overall_result


# ============================================================================
# DETAILED FLOW HELPERS (internal)
# ============================================================================


def _resolve_access_permissions(
    access_policy_config: dict,
    consumer_config: dict,
) -> list:
    """Resolve access policy permissions, substituting BPN/DID constraints."""
    access_permissions = copy.deepcopy(access_policy_config.get("permissions", []))
    if not access_permissions:
        return access_permissions

    constraint = access_permissions[0].get("constraint", {})
    left_operand = constraint.get("leftOperand", "")
    if "BusinessPartnerDID" in left_operand and "did" in consumer_config:
        constraint["rightOperand"] = consumer_config["did"]
    elif constraint.get("rightOperand") is None and "bpn" in consumer_config:
        constraint["rightOperand"] = consumer_config["bpn"]

    return access_permissions


def _extract_policy_kwargs(policy_config: dict) -> dict:
    """Extract optional context/profile kwargs from a policy config."""
    kwargs: dict = {}
    for key in ("context", "profile"):
        if key in policy_config:
            kwargs[key] = policy_config[key]
    return kwargs


def _provision_detailed(
    logger,
    provider,
    access_policy_config: dict,
    usage_policy_config: dict,
    asset_config: dict,
    backend_config: dict,
    consumer_config: dict,
    header_fn,
) -> dict:
    """Phase 1 (detailed): Provision data with verbose step-by-step logging."""
    import time as _time

    header_fn("PHASE 1: Provider Data Provision")

    import uuid as _uuid
    run_id = f"{int(_time.time())}-{_uuid.uuid4().hex[:6]}"
    asset_id = f"e2e-asset-{run_id}"
    access_policy_id = f"e2e-access-policy-{run_id}"
    usage_policy_id = f"e2e-usage-policy-{run_id}"
    contract_def_id = f"e2e-contract-def-{run_id}"

    access_permissions = _resolve_access_permissions(access_policy_config, consumer_config)
    access_kwargs = _extract_policy_kwargs(access_policy_config)
    usage_kwargs = _extract_policy_kwargs(usage_policy_config)

    # Step 1.1: Create Access Policy
    logger.info("\nStep 1.1: Creating Access Policy")
    logger.info("%s", "-" * 80)
    try:
        access_policy_request = {
            "policy_id": access_policy_id,
            "permissions": access_permissions,
            **access_kwargs,
        }
        logger.info("[ACCESS POLICY REQUEST]:\n%s", json.dumps(access_policy_request, indent=2))

        access_policy_response = provider.create_policy(
            policy_id=access_policy_id,
            permissions=access_permissions,
            **access_kwargs,
        )
        logger.info("✓ Access policy created: %s", access_policy_id)
        logger.info(
            "[ACCESS POLICY RESPONSE]:\n%s",
            json.dumps(access_policy_response, indent=2),
        )
    except Exception as exc:
        logger.exception("✗ Failed to create access policy: %s", exc)
        raise

    # Step 1.2: Create Usage Policy
    logger.info("\nStep 1.2: Creating Usage Policy")
    logger.info("%s", "-" * 80)
    try:
        usage_policy_request = {
            "policy_id": usage_policy_id,
            "permissions": usage_policy_config["permissions"],
            **usage_kwargs,
        }
        logger.info("[USAGE POLICY REQUEST]:\n%s", json.dumps(usage_policy_request, indent=2))

        usage_policy_response = provider.create_policy(
            policy_id=usage_policy_id,
            permissions=usage_policy_config["permissions"],
            **usage_kwargs,
        )
        logger.info("✓ Usage policy created: %s", usage_policy_id)
        logger.info(
            "[USAGE POLICY RESPONSE]:\n%s",
            json.dumps(usage_policy_response, indent=2),
        )
    except Exception as exc:
        logger.exception("✗ Failed to create usage policy: %s", exc)
        raise

    # Step 1.3: Create Asset
    logger.info("\nStep 1.3: Creating Asset")
    logger.info("%s", "-" * 80)
    try:
        asset_request = {
            "asset_id": asset_id,
            "base_url": backend_config["base_url"],
            "dct_type": asset_config["dct_type"],
            "semantic_id": asset_config["semantic_id"],
            "version": asset_config["version"],
        }
        logger.info("[ASSET REQUEST]:\n%s", json.dumps(asset_request, indent=2))

        asset_response = provider.create_asset(
            asset_id=asset_id,
            base_url=backend_config["base_url"],
            dct_type=asset_config["dct_type"],
            semantic_id=asset_config["semantic_id"],
            version=asset_config["version"],
            proxy_params=asset_config.get("proxy_params"),
        )
        logger.info("✓ Asset created: %s", asset_id)
        logger.info(
            "[ASSET RESPONSE]:\n%s",
            json.dumps(asset_response, indent=2),
        )
    except Exception as exc:
        logger.exception("✗ Failed to create asset: %s", exc)
        raise

    # Step 1.4: Create Contract Definition
    logger.info("\nStep 1.4: Creating Contract Definition")
    logger.info("%s", "-" * 80)
    try:
        contract_request = {
            "contract_id": contract_def_id,
            "access_policy_id": access_policy_id,
            "usage_policy_id": usage_policy_id,
            "asset_id": asset_id,
        }
        logger.info("[CONTRACT DEF REQUEST]:\n%s", json.dumps(contract_request, indent=2))

        contract_def_response = provider.create_contract(
            contract_id=contract_def_id,
            usage_policy_id=usage_policy_id,
            access_policy_id=access_policy_id,
            asset_id=asset_id,
        )
        logger.info("✓ Contract definition created: %s", contract_def_id)
        logger.info("  - Asset: %s", asset_id)
        logger.info("  - Access Policy: %s", access_policy_id)
        logger.info("  - Usage Policy: %s", usage_policy_id)
        logger.info(
            "[CONTRACT DEF RESPONSE]:\n%s",
            json.dumps(contract_def_response, indent=2),
        )
    except Exception as exc:
        logger.exception("✗ Failed to create contract definition: %s", exc)
        raise

    identity_value = consumer_config.get("bpn", consumer_config.get("did", "N/A"))
    logger.info("\n%s", "=" * 80)
    logger.info("✓ Data Provision Complete!")
    logger.info("%s", "=" * 80)
    logger.info("Provider has made the data available in the dataspace:")
    logger.info("  - Asset ID: %s", asset_id)
    logger.info("  - Visible to: %s", identity_value)
    logger.info("  - Contract Terms: Active Membership + Framework Agreement")

    return {
        "asset_id": asset_id,
        "access_policy_id": access_policy_id,
        "usage_policy_id": usage_policy_id,
        "contract_def_id": contract_def_id,
    }


# ============================================================================
# CONSUME DETAILED — SUB-STEPS
# ============================================================================


def _step_discover_provider(logger, consumer_service, provider_config, is_did):
    """Step 2.0: Discover provider connector info."""
    if is_did:
        logger.info("Step 2.0: Using Provider DID directly (no BPNL discovery)")
        logger.info("%s", "-" * 80)
        logger.info("  - Provider DID: %s", provider_config.get("did", "N/A"))
        logger.info("  - DSP URL: %s", provider_config.get("dsp_url", "N/A"))
        return

    is_jupiter = provider_config.get("dataspace_version") == "jupiter"
    if is_jupiter:
        logger.info("Step 2.0: Jupiter protocol — using DSP URL directly (no discovery service)")
        logger.info("%s", "-" * 80)
        logger.info("  - BPN: %s", provider_config.get("bpn", "N/A"))
        logger.info("  - DSP URL: %s", provider_config.get("dsp_url", "N/A"))
        return

    logger.info("Step 2.0: Discovering Connector Info via BPNL")
    logger.info("%s", "-" * 80)
    try:
        discovered_address, discovered_id, discovered_protocol = (
            consumer_service.get_discovery_info(
                bpnl=provider_config["bpn"],
                counter_party_address=provider_config["dsp_url"],
            )
        )
        logger.info("✓ Connector discovery successful:")
        logger.info("  - Counter Party Address : %s", discovered_address)
        logger.info("  - Counter Party ID      : %s", discovered_id)
        logger.info("  - Protocol              : %s", discovered_protocol)
    except Exception as exc:
        logger.exception("✗ Connector discovery failed: %s", exc)
        raise


def _catalog_keys(is_prefixed: bool) -> dict:
    """Return JSON-LD key mappings based on whether catalog uses prefixed keys."""
    if is_prefixed:
        return {
            "dataset": "dcat:dataset",
            "participantId": "dspace:participantId",
            "service": "dcat:service",
            "hasPolicy": "odrl:hasPolicy",
        }
    return {
        "dataset": "dataset",
        "participantId": "participantId",
        "service": "service",
        "hasPolicy": "hasPolicy",
    }


def _extract_dsp_endpoint(catalog_data, keys, fallback_url):
    """Extract the DSP endpoint URL from catalog service metadata."""
    services = catalog_data.get(keys["service"], [])
    if isinstance(services, dict):
        services = [services]
    for service in services:
        if service.get("@type") == "DataService" and service.get("endpointURL"):
            return service["endpointURL"]
    return fallback_url


def _find_target_dataset(datasets, asset_id):
    """Locate the dataset matching *asset_id* in the catalog datasets list."""
    for dataset in datasets:
        if dataset.get("@id") == asset_id:
            return dataset
    raise ValueError(f"Asset {asset_id} not found in catalog")


def _ensure_list(value):
    """Normalise a value that may be a single dict or a list into a list."""
    if isinstance(value, dict):
        return [value]
    return value


def _step_fetch_catalog(logger, consumer_service, provider_config, asset_id, is_did):
    """Step 2.1: Discover provider catalog and extract offer info.

    Returns ``(is_prefixed, offer_policy, offer_id, participant_id, dsp_endpoint)``.
    """
    logger.info("\nStep 2.1: Discovering Provider Catalog")
    logger.info("%s", "-" * 80)
    try:
        catalog_data = _request_catalog(
            logger, consumer_service, provider_config, asset_id, is_did,
        )

        is_prefixed = "dcat:dataset" in catalog_data
        keys = _catalog_keys(is_prefixed)

        datasets = _ensure_list(catalog_data.get(keys["dataset"], []))
        logger.info("[CATALOG RESPONSE]:\n%s", json.dumps(catalog_data, indent=2))

        participant_id = catalog_data.get(
            keys["participantId"],
            provider_config.get("bpn", provider_config.get("did", "")),
        )
        logger.info("  - Participant ID from catalog: %s", participant_id)

        dsp_endpoint = _extract_dsp_endpoint(
            catalog_data, keys, provider_config["dsp_url"],
        )
        logger.info("  - DSP endpoint from catalog: %s", dsp_endpoint)

        logger.info("✓ Catalog received from Provider")
        logger.info("  - Total datasets: %s", len(datasets))

        target_dataset = _find_target_dataset(datasets, asset_id)

        has_policy = _ensure_list(target_dataset.get(keys["hasPolicy"], []))
        offer_policy = has_policy[0]
        offer_id = offer_policy["@id"]
        logger.info("  - Found asset: %s", asset_id)
        logger.info("  - Offer ID: %s", offer_id)

    except Exception as exc:
        logger.exception("✗ Failed to get catalog: %s", exc)
        raise

    return is_prefixed, offer_policy, offer_id, participant_id, dsp_endpoint


def _request_catalog(logger, consumer_service, provider_config, asset_id, is_did):
    """Issue the catalog request (DID or BPNL variant) and return raw data."""
    if is_did:
        catalog_request_params = {
            "counter_party_id": provider_config["did"],
            "counter_party_address": provider_config["dsp_url"],
            "asset_id": asset_id,
        }
        logger.info(
            "[CATALOG REQUEST]:\n%s",
            json.dumps(catalog_request_params, indent=2),
        )
        return consumer_service.get_catalog_by_asset_id(
            counter_party_id=provider_config["did"],
            counter_party_address=provider_config["dsp_url"],
            asset_id=asset_id,
        )

    catalog_request_params = {
        "bpnl": provider_config["bpn"],
        "counter_party_address": provider_config["dsp_url"],
        "asset_id": asset_id,
    }
    logger.info(
        "[CATALOG REQUEST]:\n%s",
        json.dumps(catalog_request_params, indent=2),
    )
    return consumer_service.get_catalog_by_asset_id_with_bpnl(
        bpnl=provider_config["bpn"],
        counter_party_address=provider_config["dsp_url"],
        asset_id=asset_id,
    )


def _build_offer_policy_data(offer_policy, is_prefixed):
    """Build the offer policy payload matching the catalog's prefix style."""
    if is_prefixed:
        return {
            "odrl:permission": offer_policy.get(
                "odrl:permission", offer_policy.get("permission", []),
            ),
            "odrl:prohibition": offer_policy.get(
                "odrl:prohibition", offer_policy.get("prohibition", []),
            ),
            "odrl:obligation": offer_policy.get(
                "odrl:obligation", offer_policy.get("obligation", []),
            ),
        }
    return {
        "permission": offer_policy.get("permission", []),
        "prohibition": offer_policy.get("prohibition", []),
        "obligation": offer_policy.get("obligation", []),
    }


def _step_negotiate_contract(
    logger, consumer_service, model_factory, consumer_config,
    is_prefixed, offer_policy, dsp_endpoint, offer_id, asset_id,
    participant_id, negotiation_context, protocol,
):
    """Step 2.2: Negotiate a contract and return the negotiation ID."""
    logger.info("\nStep 2.2: Negotiating Contract")
    logger.info("%s", "-" * 80)
    try:
        offer_policy_data = _build_offer_policy_data(offer_policy, is_prefixed)

        contract_negotiation = model_factory.get_contract_negotiation_model(
            dataspace_version=consumer_config["dataspace_version"],
            counter_party_address=dsp_endpoint,
            offer_id=offer_id,
            asset_id=asset_id,
            provider_id=participant_id,
            offer_policy=offer_policy_data,
            context=negotiation_context,
            protocol=protocol,
        )

        logger.info("[NEGOTIATION REQUEST]:\n%s", contract_negotiation.to_data())

        negotiation_response = consumer_service.contract_negotiations.create(
            obj=contract_negotiation,
        )

        logger.info("[NEGOTIATION RESPONSE] Status: %s", negotiation_response.status_code)
        logger.info(
            "[NEGOTIATION RESPONSE] Body:\n%s",
            json.dumps(negotiation_response.json(), indent=2),
        )

        if negotiation_response.status_code != 200:
            raise RuntimeError(
                f"Contract negotiation failed with status {negotiation_response.status_code}"
            )

        negotiation_data = negotiation_response.json()
        negotiation_id = negotiation_data.get("@id")
        logger.info("✓ Contract negotiation initiated: %s", negotiation_id)
        logger.info("  - Asset: %s", asset_id)
        logger.info("  - Provider: %s", participant_id)

    except Exception as exc:
        logger.exception("✗ Failed to negotiate contract: %s", exc)
        raise

    return negotiation_id


def _step_wait_for_agreement(logger, consumer_service, negotiation_id):
    """Step 2.3: Poll until the contract negotiation reaches FINALIZED."""
    logger.info("\nStep 2.3: Waiting for Contract Agreement")
    logger.info("%s", "-" * 80)
    elapsed = 0

    try:
        logger.info("Polling negotiation state...")
        while elapsed < _MAX_POLL_WAIT:
            time.sleep(_POLL_INTERVAL)
            elapsed += _POLL_INTERVAL
            status_response = consumer_service.contract_negotiations.get_by_id(
                negotiation_id,
            )
            if status_response.status_code != 200:
                continue

            status_data = status_response.json()
            state = status_data.get("state", status_data.get("edc:state"))
            logger.info("  Negotiation state: %s", state)

            if state == "TERMINATED":
                logger.info(
                    "[NEGOTIATION STATE RESPONSE]:\n%s",
                    json.dumps(status_data, indent=2),
                )
                raise RuntimeError("Contract negotiation was TERMINATED")

            if state == "FINALIZED":
                logger.info(
                    "[NEGOTIATION STATE RESPONSE]:\n%s",
                    json.dumps(status_data, indent=2),
                )
                contract_agreement_id = status_data.get(
                    "contractAgreementId",
                    status_data.get("edc:contractAgreementId"),
                )
                logger.info("✓ Contract Agreement finalized: %s", contract_agreement_id)
                if contract_agreement_id is None:
                    raise RuntimeError("Contract agreement ID not received")
                return contract_agreement_id

        raise TimeoutError("Contract negotiation timeout")

    except Exception as exc:
        logger.exception("\n✗ Contract negotiation failed: %s", exc)
        raise


def _step_initiate_transfer(
    logger, consumer_service, model_factory, consumer_config,
    dsp_endpoint, contract_agreement_id, protocol,
):
    """Step 2.4: Start a transfer process and return the transfer ID."""
    logger.info("\nStep 2.4: Initiating Transfer Process")
    logger.info("%s", "-" * 80)
    try:
        transfer_request = model_factory.get_transfer_process_model(
            dataspace_version=consumer_config["dataspace_version"],
            counter_party_address=dsp_endpoint,
            contract_id=contract_agreement_id,
            transfer_type="HttpData-PULL",
            protocol=protocol,
            data_destination={"type": "HttpProxy"},
        )

        logger.info("[TRANSFER REQUEST]:\n%s", transfer_request.to_data())

        transfer_response = consumer_service.transfer_processes.create(
            obj=transfer_request,
        )

        logger.info("[TRANSFER RESPONSE] Status: %s", transfer_response.status_code)
        logger.info(
            "[TRANSFER RESPONSE] Body:\n%s",
            json.dumps(transfer_response.json(), indent=2),
        )

        if transfer_response.status_code != 200:
            raise RuntimeError(
                f"Transfer process failed with status {transfer_response.status_code}"
            )

        transfer_data = transfer_response.json()
        transfer_id = transfer_data.get("@id")
        logger.info("✓ Transfer process initiated: %s", transfer_id)
        logger.info("  - Type: HttpData-PULL")
        logger.info("  - Contract: %s", contract_agreement_id)

    except Exception as exc:
        logger.exception("✗ Failed to start transfer: %s", exc)
        raise

    return transfer_id


def _step_wait_for_edr(logger, consumer_service, transfer_id):
    """Step 2.5: Poll until the EDR is available.

    Returns ``(edr_data, dataplane_url, access_token)``.
    """
    logger.info("\nStep 2.5: Waiting for EDR (Endpoint Data Reference)")
    logger.info("%s", "-" * 80)
    elapsed = 0

    try:
        logger.info("Waiting for EDR...")

        while elapsed < _MAX_POLL_WAIT:
            time.sleep(_POLL_INTERVAL)
            elapsed += _POLL_INTERVAL

            transfer_status = consumer_service.transfer_processes.get_by_id(transfer_id)
            if transfer_status.status_code != 200:
                continue

            transfer_state_data = transfer_status.json()
            state = transfer_state_data.get(
                "state", transfer_state_data.get("edc:state"),
            )
            logger.info("  Transfer state: %s", state)

            if state == "TERMINATED":
                raise RuntimeError("Transfer process was TERMINATED")

            if state not in ("STARTED", "COMPLETED"):
                continue

            edr_response = consumer_service.edrs.get_data_address(transfer_id)
            logger.info("[EDR RESPONSE] Status: %s", edr_response.status_code)
            logger.info(
                "[EDR RESPONSE] Body:\n%s",
                json.dumps(edr_response.json(), indent=2),
            )
            if edr_response.status_code == 200:
                edr_data = edr_response.json()
                logger.info("✓ EDR received!")
                dataplane_url = edr_data.get("endpoint", edr_data.get("edc:endpoint"))
                access_token = edr_data.get(
                    "authorization", edr_data.get("edc:authorization"),
                )
                logger.info("  - Endpoint: %s", dataplane_url)
                logger.info(
                    "  - Token: %s...",
                    access_token[:30] if access_token else None,
                )
                return edr_data, dataplane_url, access_token

        raise TimeoutError("EDR retrieval timeout")

    except Exception as exc:
        logger.exception("\n✗ Failed to get EDR: %s", exc)
        raise


# ============================================================================
# CONSUME DETAILED — ORCHESTRATOR
# ============================================================================


def _consume_detailed(
    logger,
    consumer_service,
    asset_id: str,
    provider_config: dict,
    consumer_config: dict,
    protocol: str,
    negotiation_context: list,
    is_did: bool,
    model_factory,
    header_fn,
) -> dict:
    """Phase 2 (detailed): Consumer discovers and consumes data (step-by-step).

    Handles both Saturn (unprefixed JSON-LD keys) and Jupiter
    (``dcat:``, ``odrl:``, ``dspace:`` prefixed keys) catalog responses.

    Returns a dict with ``edr_data``, ``dataplane_url``, ``access_token``,
    ``transfer_id``, and ``contract_agreement_id``.
    """
    header_fn("PHASE 2: Consumer Data Consumption")

    _step_discover_provider(logger, consumer_service, provider_config, is_did)

    is_prefixed, offer_policy, offer_id, participant_id, dsp_endpoint = (
        _step_fetch_catalog(
            logger, consumer_service, provider_config, asset_id, is_did,
        )
    )

    negotiation_id = _step_negotiate_contract(
        logger, consumer_service, model_factory, consumer_config,
        is_prefixed, offer_policy, dsp_endpoint, offer_id, asset_id,
        participant_id, negotiation_context, protocol,
    )

    contract_agreement_id = _step_wait_for_agreement(
        logger, consumer_service, negotiation_id,
    )

    transfer_id = _step_initiate_transfer(
        logger, consumer_service, model_factory, consumer_config,
        dsp_endpoint, contract_agreement_id, protocol,
    )

    edr_data, dataplane_url, access_token = _step_wait_for_edr(
        logger, consumer_service, transfer_id,
    )

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
        "contract_agreement_id": contract_agreement_id,
    }
