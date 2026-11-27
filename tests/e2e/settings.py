#################################################################################
# Eclipse Tractus-X - Software Development KIT
#
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
# License for the specific language governing permissions and limitations
# under the License.
#
# SPDX-License-Identifier: Apache-2.0
#################################################################################

## This code was partially generated using artificial intelligence (AI) (Tool: Claude Code, Model: Claude Opus 5.5).
## It was reviewed and tested by a human committer.

"""Settings for the E2E suite, read from the environment.

The defaults address the dataspace that ``.github/workflows/e2e-umbrella.yml``
deploys: Tractus-X Umbrella's ``values-adopter-decentralized-identityhub``
profile plus the Tractus-X TestLab CI overrides, with every participant on its
own ``*.local`` ingress hostname. Every value can be overridden through the
environment variable named next to it, so the same tests run against any other
Saturn (DSP 2025-1) dataspace.

The management API keys have no default on purpose: the workflow passes the
ephemeral cluster's keys in, and a local run has to name its own.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field

#: Set to ``1`` to run the suite. Anything else skips every E2E test, so that
#: ``pytest tests/`` (the unit test workflow) never needs a dataspace.
ENABLE_VARIABLE = "TX_SDK_E2E"

#: Catena-X 2025-9 policy context, the one the Saturn TCK scripts use
#: (``tck/connector/tck-config.yaml``, section ``saturn``).
CATENAX_POLICY_CONTEXT: list = [
    "https://w3id.org/catenax/2025/9/policy/odrl.jsonld",
    "https://w3id.org/catenax/2025/9/policy/context.jsonld",
    {"@vocab": "https://w3id.org/edc/v0.0.1/ns/"},
]

#: DID-mode access policy: any active Catena-X member may see the offer.
ACCESS_PERMISSIONS: list = [
    {
        "action": "access",
        "constraint": {"leftOperand": "Membership", "operator": "eq", "rightOperand": "active"},
    }
]

#: Usage policy: the three credentials the workflow issues to both participants.
USAGE_PERMISSIONS: list = [
    {
        "action": "use",
        "constraint": {
            "and": [
                {"leftOperand": "Membership", "operator": "eq", "rightOperand": "active"},
                {
                    "leftOperand": "FrameworkAgreement",
                    "operator": "eq",
                    "rightOperand": "DataExchangeGovernance:1.0",
                },
                {
                    "leftOperand": "UsagePurpose",
                    "operator": "isAnyOf",
                    "rightOperand": "cx.core.industrycore:1",
                },
            ]
        },
    }
]

#: The data-plane proxy settings the TCK's ``AssetConfig`` uses by default.
PROXY_PARAMS: dict = {
    "proxyQueryParams": "true",
    "proxyPath": "true",
    "proxyMethod": "true",
    "proxyBody": "false",
}

DSP_PROTOCOL = "dataspace-protocol-http:2025-1"
DCT_TYPE = "https://w3id.org/catenax/taxonomy#Submodel"
SEMANTIC_ID = "urn:samm:io.catenax.business_partner_certificate:3.1.0#BusinessPartnerCertificate"


def _env(name: str, default: str = "") -> str:
    value = os.environ.get(name)
    return value if value not in (None, "") else default


def is_enabled() -> bool:
    """True when the E2E suite was asked for."""
    return _env(ENABLE_VARIABLE) == "1"


@dataclass(frozen=True)
class Participant:
    """One connector: where its management API is and who it is in the dataspace."""

    base_url: str
    dma_path: str
    api_key: str
    did: str
    bpn: str
    dsp_url: str = ""


@dataclass(frozen=True)
class E2ESettings:
    provider: Participant
    consumer: Participant
    backend_url: str
    dtr_base_url: str
    dtr_api_path: str
    timeout_seconds: int
    dataspace_version: str = "saturn"
    api_key_header: str = "X-Api-Key"
    missing: tuple = field(default=())

    @classmethod
    def from_env(cls) -> "E2ESettings":
        provider = Participant(
            base_url=_env("E2E_PROVIDER_MANAGEMENT_URL", "http://provider-management.local"),
            dma_path=_env("E2E_PROVIDER_DMA_PATH", "/management"),
            api_key=_env("E2E_PROVIDER_API_KEY"),
            did=_env("E2E_PROVIDER_DID", "did:web:provider.local:identityhub:BPNL000000000001"),
            bpn=_env("E2E_PROVIDER_BPN", "BPNL000000000001"),
            dsp_url=_env("E2E_PROVIDER_DSP_URL", "http://provider-dsp.local/api/v1/dsp/2025-1"),
        )
        consumer = Participant(
            base_url=_env("E2E_CONSUMER_MANAGEMENT_URL", "http://consumer-management.local"),
            dma_path=_env("E2E_CONSUMER_DMA_PATH", "/management"),
            api_key=_env("E2E_CONSUMER_API_KEY"),
            did=_env("E2E_CONSUMER_DID", "did:web:consumer.local:identityhub:BPNL000000000002"),
            bpn=_env("E2E_CONSUMER_BPN", "BPNL000000000002"),
        )
        missing = tuple(
            name
            for name, value in (
                ("E2E_PROVIDER_API_KEY", provider.api_key),
                ("E2E_CONSUMER_API_KEY", consumer.api_key),
            )
            if not value
        )
        return cls(
            provider=provider,
            consumer=consumer,
            backend_url=_env("E2E_BACKEND_URL", "http://tck-submodel.local").rstrip("/"),
            dtr_base_url=_env("E2E_DTR_BASE_URL", "http://provider-dtr.local/semantics/registry").rstrip("/"),
            dtr_api_path=_env("E2E_DTR_API_PATH", "/api/v3"),
            timeout_seconds=int(_env("E2E_TIMEOUT_SECONDS", "120")),
            missing=missing,
        )
