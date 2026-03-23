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
Configuration models for TCK (Technology Compatibility Kit) E2E connector tests.

Typed dataclasses that replace raw dicts for safer, documented configuration
of connector endpoints, policies, assets, and test-run parameters.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


# ============================================================================
# CONNECTOR & BACKEND CONFIGURATION
# ============================================================================


@dataclass
class ConnectorConfig:
    """Typed configuration for an EDC Connector endpoint (Provider or Consumer).

    Attributes:
        base_url: EDC Control Plane base URL.
        dma_path: Management API path (default: ``/management``).
        api_key_header: HTTP header name for the API key.
        api_key: API key value.
        dataspace_version: ``"saturn"`` (EDC 0.11.x+) or ``"jupiter"`` (EDC 0.8-0.10.x).
        bpn: Business Partner Number (for BPNL-based discovery).
        did: Decentralised Identifier (for DID-based discovery).
        dsp_url: DSP protocol endpoint URL.
    """

    base_url: str
    dma_path: str = "/management"
    api_key_header: str = "X-Api-Key"
    api_key: str = ""
    dataspace_version: str = "saturn"
    bpn: Optional[str] = None
    did: Optional[str] = None
    dsp_url: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert to dict, excluding ``None``-valued optional fields.

        Optional fields (``bpn``, ``did``, ``dsp_url``) are only included
        when they have non-``None`` values so that ``"bpn" in config``
        checks behave correctly in the helpers layer.
        """
        result: dict = {
            "base_url": self.base_url,
            "dma_path": self.dma_path,
            "api_key_header": self.api_key_header,
            "api_key": self.api_key,
            "dataspace_version": self.dataspace_version,
        }
        if self.bpn is not None:
            result["bpn"] = self.bpn
        if self.did is not None:
            result["did"] = self.did
        if self.dsp_url is not None:
            result["dsp_url"] = self.dsp_url
        return result


@dataclass
class BackendConfig:
    """Typed configuration for the backend data storage service.

    Attributes:
        base_url: Backend service URL (often includes a generated UUID path).
        api_key_header: HTTP header name for the API key.
        api_key: API key value (empty string if not required).
    """

    base_url: str
    api_key_header: str = "X-Api-Key"
    api_key: str = ""

    def to_dict(self) -> dict:
        """Convert to dict."""
        return {
            "base_url": self.base_url,
            "api_key_header": self.api_key_header,
            "api_key": self.api_key,
        }


# ============================================================================
# POLICY & ASSET CONFIGURATION
# ============================================================================


@dataclass
class PolicyConfig:
    """Typed configuration for an ODRL policy.

    Attributes:
        permissions: List of ODRL permission dicts.
        context: Optional JSON-LD ``@context`` entries
            (required for Jupiter / DID policies).
        profile: Optional policy profile identifier
            (e.g. ``"cx-policy:profile2405"``).
    """

    permissions: list = field(default_factory=list)
    context: Optional[list] = None
    profile: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert to dict, excluding ``None``-valued optional fields."""
        result: dict = {"permissions": self.permissions}
        if self.context is not None:
            result["context"] = self.context
        if self.profile is not None:
            result["profile"] = self.profile
        return result


@dataclass
class AssetConfig:
    """Typed configuration for an EDC Asset.

    Attributes:
        dct_type: Dublin Core ``dct:type`` value.
        semantic_id: Semantic model identifier (URN).
        version: Asset version string.
        proxy_params: Data-plane proxy parameters dict.
    """

    dct_type: str = "https://w3id.org/catenax/taxonomy#Submodel"
    semantic_id: str = (
        "urn:samm:io.catenax.business_partner_certificate:"
        "3.1.0#BusinessPartnerCertificate"
    )
    version: str = "1.0"
    proxy_params: dict = field(
        default_factory=lambda: {
            "proxyQueryParams": "true",
            "proxyPath": "true",
            "proxyMethod": "true",
            "proxyBody": "false",
        }
    )

    def to_dict(self) -> dict:
        """Convert to dict."""
        return {
            "dct_type": self.dct_type,
            "semantic_id": self.semantic_id,
            "version": self.version,
            "proxy_params": dict(self.proxy_params),
        }


# ============================================================================
# TEST RUN CONFIGURATION
# ============================================================================


@dataclass
class SimpleTckConfig:
    """Complete configuration for a **simple** TCK E2E test.

    Bundles connector, backend, policy, and asset configs with test-run
    metadata so that the entire test is driven from a single object.

    Attributes:
        test_name: Unique name for the test case (used for log directory).
        provider: Provider connector configuration.
        consumer: Consumer connector configuration.
        backend: Backend storage configuration.
        access_policy: Access policy configuration (catalog visibility).
        usage_policy: Usage policy configuration (contract terms).
        asset: Asset configuration (defaults to standard Submodel config).
        accepted_policies: Optional list of accepted offer policies for the
            consumer.  ``None`` = accept any; ``[]`` = reject all.
        sample_data: Optional custom sample data dict to upload.
            ``None`` = use built-in default.
        cleanup: Whether to delete resources after the test run.
        discovery_mode: ``"bpnl"`` for BPN-based discovery,
            ``"did"`` for DID-based.
        verify_ssl: Whether to verify SSL certificates for HTTP requests.
            Defaults to ``False`` (suitable for INT environments with
            self-signed certificates).
        banner_title: Optional banner text.  Auto-generated if empty.
        summary_title: Test summary table title.  Auto-generated if empty.
    """

    test_name: str
    provider: ConnectorConfig
    consumer: ConnectorConfig
    backend: BackendConfig
    access_policy: PolicyConfig
    usage_policy: PolicyConfig
    asset: AssetConfig = field(default_factory=AssetConfig)
    accepted_policies: Optional[list] = None
    sample_data: Optional[dict] = None
    cleanup: bool = True
    discovery_mode: str = "bpnl"
    verify_ssl: bool = False
    banner_title: str = ""
    summary_title: str = ""
    config_section: str = ""  # YAML section name (e.g. "jupiter", "saturn") used by --config


@dataclass
class DetailedTckConfig:
    """Complete configuration for a **detailed** TCK E2E test.

    Similar to :class:`SimpleTckConfig` but includes additional parameters
    for the step-by-step detailed flow
    (catalog -> negotiate -> transfer -> EDR -> GET).

    Attributes:
        test_name: Unique name for the test case.
        provider: Provider connector configuration.
        consumer: Consumer connector configuration.
        backend: Backend storage configuration.
        access_policy: Access policy configuration.
        usage_policy: Usage policy configuration.
        asset: Asset configuration.
        sample_data: Optional custom sample data dict. ``None`` = use default.
        cleanup: Whether to delete resources after the test run.
        discovery_mode: ``"bpnl"`` or ``"did"``.
        verify_ssl: Whether to verify SSL certificates for HTTP requests.
            Defaults to ``False`` (suitable for INT environments with
            self-signed certificates).
        protocol: DSP protocol string for negotiation / transfer
            (e.g. ``"dataspace-protocol-http:2025-1"``).
        negotiation_context: ODRL ``@context`` list for contract negotiation.
            ``None`` = derive from the access policy context.
        banner_title: Optional banner text.
        summary_title: Test summary table title.
    """

    test_name: str
    provider: ConnectorConfig
    consumer: ConnectorConfig
    backend: BackendConfig
    access_policy: PolicyConfig
    usage_policy: PolicyConfig
    asset: AssetConfig = field(default_factory=AssetConfig)
    sample_data: Optional[dict] = None
    cleanup: bool = True
    discovery_mode: str = "bpnl"
    verify_ssl: bool = False
    protocol: str = "dataspace-protocol-http:2025-1"
    negotiation_context: Optional[list] = None
    banner_title: str = ""
    summary_title: str = ""
    config_section: str = ""  # YAML section name (e.g. "jupiter", "saturn") used by --config
