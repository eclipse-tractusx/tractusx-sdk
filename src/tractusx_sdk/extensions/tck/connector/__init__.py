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
TCK connector helpers for E2E testing.

Provides reusable infrastructure used across all TCK E2E connector scripts:
configuration models, test runners, logging, service initialization,
data provisioning, consumption, cleanup, test summary reporting,
and CLI argument parsing.
"""

from .helpers import (
    # Constants
    CONTENT_TYPE_JSON,
    LOG_RESPONSE_SUFFIX,
    MANAGEMENT_PATH,
    # Default data
    SAMPLE_ASPECT_MODEL_DATA,
    DEFAULT_ASSET_CONFIG,
    # Logging
    setup_tck_logging,
    finalize_log,
    print_header,
    print_separator,
    # Services
    initialize_provider_service,
    initialize_consumer_service,
    # Backend
    upload_sample_data,
    # Data access
    access_data_with_edr,
    # Cleanup
    cleanup_provider_resources,
    cleanup_backend_data,
    # Runner utilities
    run_step,
    mark_skipped_phases,
    print_summary,
    # CLI
    build_tck_cli_parser,
    apply_cli_overrides,
    configure_debug_logging,
    log_config_warning,
    # Simple flow helpers
    provision_simple,
    consume_simple_bpnl,
    consume_simple_did,
)

from .models import (
    ConnectorConfig,
    BackendConfig,
    PolicyConfig,
    AssetConfig,
    SimpleTckConfig,
    DetailedTckConfig,
)

from .runners import (
    run_simple_test,
    run_detailed_test,
)

__all__ = [
    # ── Configuration models ──────────────────────────────────────────
    "ConnectorConfig",
    "BackendConfig",
    "PolicyConfig",
    "AssetConfig",
    "SimpleTckConfig",
    "DetailedTckConfig",
    # ── Test runners ──────────────────────────────────────────────────
    "run_simple_test",
    "run_detailed_test",
    # ── Constants ─────────────────────────────────────────────────────
    "CONTENT_TYPE_JSON",
    "LOG_RESPONSE_SUFFIX",
    "MANAGEMENT_PATH",
    "SAMPLE_ASPECT_MODEL_DATA",
    "DEFAULT_ASSET_CONFIG",
    # ── Logging ───────────────────────────────────────────────────────
    "setup_tck_logging",
    "finalize_log",
    "print_header",
    "print_separator",
    # ── Services ──────────────────────────────────────────────────────
    "initialize_provider_service",
    "initialize_consumer_service",
    # ── Backend ───────────────────────────────────────────────────────
    "upload_sample_data",
    # ── Data access ───────────────────────────────────────────────────
    "access_data_with_edr",
    # ── Cleanup ───────────────────────────────────────────────────────
    "cleanup_provider_resources",
    "cleanup_backend_data",
    # ── Runner utilities ──────────────────────────────────────────────
    "run_step",
    "mark_skipped_phases",
    "print_summary",
    # ── CLI ────────────────────────────────────────────────────────────
    "build_tck_cli_parser",
    "apply_cli_overrides",
    "configure_debug_logging",
    "log_config_warning",
    # ── Simple flow helpers ───────────────────────────────────────────
    "provision_simple",
    "consume_simple_bpnl",
    "consume_simple_did",
]
