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
Simple E2E Example: Saturn Connector Services — Data Provision and Consumption (BPNL)

Uses ``do_get_with_bpnl()`` to collapse the entire consumer flow
(catalog -> negotiate -> transfer -> EDR -> GET) into a single SDK call.

Compatible EDC versions: 0.11.X+ (Saturn Protocol with DSP 2025-1)
Backend: simple-data-backend from Tractus-X Umbrella

For the DID-based variant see: tck_e2e_saturn_0-11-X_simple_did.py
For the full step-by-step version see: tck_e2e_saturn_0-11-X_detailed.py
"""

import os
import uuid

from tractusx_sdk.extensions.tck.connector import (
    ConnectorConfig,
    BackendConfig,
    PolicyConfig,
    SimpleTckConfig,
    run_simple_test,
)

# ============================================================================
# TEST CONFIGURATION
# ============================================================================

config = SimpleTckConfig(
    test_name="tck_e2e_saturn_0-11-X_simple",
    provider=ConnectorConfig(
        base_url="http://dataprovider-controlplane.tx.test",
        api_key="TEST2",
        dataspace_version="saturn",
        bpn="BPNL00000003AYRE",
        dsp_url="http://dataprovider-controlplane.tx.test/api/v1/dsp",
    ),
    consumer=ConnectorConfig(
        base_url="http://dataconsumer-1-controlplane.tx.test",
        api_key="TEST1",
        dataspace_version="saturn",
        bpn="BPNL00000003AZQP",
    ),
    backend=BackendConfig(
        base_url=f"http://dataprovider-submodelserver.tx.test/urn:uuid:{uuid.uuid4()}",
    ),
    # NOTE: Saturn (Catena-X 2025-9) uses implicit default context — no "context" key needed
    access_policy=PolicyConfig(
        permissions=[{
            "action": "access",
            "constraint": {
                "leftOperand": "BusinessPartnerNumber",
                "operator": "isAnyOf",
                "rightOperand": None,  # Auto-set to consumer BPN at runtime
            },
        }],
    ),
    usage_policy=PolicyConfig(
        permissions=[{
            "action": "use",
            "constraint": {
                "and": [
                    {"leftOperand": "Membership", "operator": "eq", "rightOperand": "active"},
                    {"leftOperand": "FrameworkAgreement", "operator": "eq",
                     "rightOperand": "DataExchangeGovernance:1.0"},
                    {"leftOperand": "UsagePurpose", "operator": "isAnyOf",
                     "rightOperand": "cx.core.industrycore:1"},
                ],
            },
        }],
    ),
    # accepted_policies=None → accept any policy offered by the provider
    discovery_mode="bpnl",
    banner_title="Saturn Connector Services — Simple E2E",
)

# ============================================================================
# RUN
# ============================================================================

if __name__ == "__main__":
    run_simple_test(config, os.path.dirname(os.path.abspath(__file__)))
