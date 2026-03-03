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
Simple E2E Example (DID-based): Saturn Connector Services — Data Provision and Consumption

Uses ``do_get()`` with provider DID — bypasses BPNL-based discovery.

Compatible EDC versions: 0.11.X+ (Saturn Protocol with DSP 2025-1)
Backend: simple-data-backend from Tractus-X Umbrella

For the BPNL-based version see: tck_e2e_saturn_0-11-X_simple.py
For the full step-by-step version see: tck_e2e_saturn_0-11-X_detailed_did.py
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
    test_name="tck_e2e_saturn_0-11-X_simple_did",
    provider=ConnectorConfig(
        base_url="http://dataprovider-controlplane.tx.test",
        api_key="TEST2",
        dataspace_version="saturn",
        dsp_url="http://dataprovider-controlplane.tx.test/api/v1/dsp/2025-1",
        did="did:web:portal-backend.int.catena-x.net:api:administration:staticdata:did:BPNL0000000093Q7",
    ),
    consumer=ConnectorConfig(
        base_url="http://dataconsumer-1-controlplane.tx.test",
        api_key="TEST1",
        dataspace_version="saturn",
        did="did:web:portal-backend.int.catena-x.net:api:administration:staticdata:did:BPNL00000003CRHK",
    ),
    backend=BackendConfig(
        base_url=f"https://storage-ichub.int.catena-x.net/urn:uuid:{uuid.uuid4()}",
    ),
    # Saturn DID: explicit Catena-X 2025-9 context for Membership-based access
    #
    # NOTE: BusinessPartnerDID is NOT YET ALLOWED in current EDC implementation.
    # See: https://github.com/eclipse-tractusx/tractusx-edc/issues/2614
    # PR:  https://github.com/eclipse-tractusx/tractusx-edc/pull/2615
    access_policy=PolicyConfig(
        context=[
            "https://w3id.org/catenax/2025/9/policy/odrl.jsonld",
            "https://w3id.org/catenax/2025/9/policy/context.jsonld",
            {"@vocab": "https://w3id.org/edc/v0.0.1/ns/"},
        ],
        permissions=[{
            "action": "access",
            "constraint": {
                "leftOperand": "Membership",
                "operator": "eq",
                "rightOperand": "active",
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
    discovery_mode="did",
    banner_title="Saturn Connector Services — Simple E2E (DID-based)",
    summary_title="E2E TEST RUN SUMMARY  (simple DID-based)",
)

# ============================================================================
# RUN
# ============================================================================

if __name__ == "__main__":
    run_simple_test(config, os.path.dirname(os.path.abspath(__file__)))
