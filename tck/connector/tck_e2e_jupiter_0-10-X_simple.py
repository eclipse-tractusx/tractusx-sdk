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
Simple E2E Example: Jupiter Connector Services — Data Provision and Consumption (BPNL)

Uses ``do_get_with_bpnl()`` with legacy DSP protocol (Jupiter / EDC 0.8-0.10.x).

Key differences from Saturn:
  - Protocol string : ``"dataspace-protocol-http"``
  - ODRL context    : Tractus-X v1.0.0 + W3C URLs
  - dataspace_version: ``"jupiter"``
  - Policy profile  : ``"cx-policy:profile2405"``

Compatible EDC versions: 0.8.0 - 0.10.X (Jupiter Protocol)
Backend: simple-data-backend from Tractus-X Umbrella

For the Saturn equivalent see: tck_e2e_saturn_0-11-X_simple.py
For the full step-by-step version see: tck_e2e_jupiter_0-10-X_detailed.py
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
    test_name="tck_e2e_jupiter_0-10-X_simple",
    provider=ConnectorConfig(
        base_url="http://dataprovider-controlplane.tx.test",
        api_key="TEST2",
        dataspace_version="jupiter",
        bpn="BPNL00000003AYRE",
        dsp_url="http://dataprovider-controlplane.tx.test/api/v1/dsp",
    ),
    consumer=ConnectorConfig(
        base_url="http://dataconsumer-1-controlplane.tx.test",
        api_key="TEST1",
        dataspace_version="jupiter",
        bpn="BPNL00000003AZQP",
    ),
    backend=BackendConfig(
        base_url=f"http://dataprovider-submodelserver.tx.test/urn:uuid:{uuid.uuid4()}",
    ),
    # Jupiter uses Tractus-X v1.0.0 + W3C ODRL JSON-LD context
    access_policy=PolicyConfig(
        context=[
            "https://w3id.org/tractusx/policy/v1.0.0",
            "http://www.w3.org/ns/odrl.jsonld",
            {
                "tx": "https://w3id.org/tractusx/v0.0.1/ns/",
                "@vocab": "https://w3id.org/edc/v0.0.1/ns/",
            },
        ],
        permissions=[{
            "action": "use",
            "constraint": {
                "leftOperand": "tx:BusinessPartnerNumber",
                "operator": "eq",
                "rightOperand": None,  # Auto-set to consumer BPN at runtime
            },
        }],
        profile="cx-policy:profile2405",
    ),
    usage_policy=PolicyConfig(
        context=[
            "https://w3id.org/tractusx/policy/v1.0.0",
            "http://www.w3.org/ns/odrl.jsonld",
            {"@vocab": "https://w3id.org/edc/v0.0.1/ns/"},
        ],
        permissions=[{
            "action": "use",
            "constraint": {
                "and": [
                    {"leftOperand": "Membership", "operator": "eq", "rightOperand": "active"},
                    {"leftOperand": "FrameworkAgreement", "operator": "eq",
                     "rightOperand": "DataExchangeGovernance:1.0"},
                    {"leftOperand": "UsagePurpose", "operator": "eq",
                     "rightOperand": "cx.core.industrycore:1"},
                ],
            },
        }],
        profile="cx-policy:profile2405",
    ),
    # accepted_policies=None → accept any policy offered by the provider
    discovery_mode="bpnl",
    banner_title="Jupiter Connector Services — Simple E2E",
    summary_title="E2E TEST RUN SUMMARY  (simple Jupiter)",
)

# ============================================================================
# RUN
# ============================================================================

if __name__ == "__main__":
    run_simple_test(config, os.path.dirname(os.path.abspath(__file__)))
