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
Detailed E2E Example: Saturn Connector Services — Data Provision and Consumption (BPNL)

Executes the full step-by-step flow with verbose logging:
  Phase 1: Create policies + asset + contract definition
  Phase 2: Catalog → negotiate → transfer → EDR (step-by-step)
  Phase 3: Access data using EDR token

Compatible EDC versions: 0.11.X+ (Saturn Protocol with DSP 2025-1)
Backend: simple-data-backend from Tractus-X Umbrella

For the DID-based variant see: tck_e2e_saturn_0-11-X_detailed_did.py
For the simplified one-call version see: tck_e2e_saturn_0-11-X_simple.py
"""

import os

from tck_config import saturn
from tractusx_sdk.extensions.tck.connector import (
    DetailedTckConfig,
    run_detailed_test,
)

# ============================================================================
# TEST CONFIGURATION
# ============================================================================

config = DetailedTckConfig(
    test_name="tck_e2e_saturn_0-11-X_detailed",
    provider=saturn.provider,
    consumer=saturn.consumer,
    backend=saturn.backend(),
    access_policy=saturn.access_policy,
    usage_policy=saturn.usage_policy,
    protocol=saturn.protocol,
    negotiation_context=saturn.negotiation_context,
    discovery_mode="bpnl",
    banner_title="Saturn Connector Services — Detailed E2E",
)

# ============================================================================
# RUN
# ============================================================================

if __name__ == "__main__":
    run_detailed_test(config, os.path.dirname(os.path.abspath(__file__)))
