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
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# SPDX-License-Identifier: Apache-2.0
#################################################################################
"""
TCK Connector — shared configuration loader.

All 6 TCK test scripts import from this module instead of hard-coding
connectivity values.  Actual values live in ``tck_config.yaml`` next to this
file — that is the only file that needs to be edited when switching
between environments.

Usage
-----
::

    from tck_config import jupiter, saturn, saturn_did

    config = SimpleTckConfig(
        provider=jupiter.provider,
        consumer=jupiter.consumer,
        backend=jupiter.backend(),   # fresh UUID per call
        ...
    )

Sections
--------
- ``jupiter``     — EDC 0.8–0.10.x, BPNL discovery
- ``saturn``      — EDC 0.11.x+-0.12.x+,    BPNL discovery
- ``saturn_did``  — EDC 0.11.x+-0.12.x+,    DID  discovery
"""

from __future__ import annotations

import uuid as _uuid
import os as _os

try:
    import yaml as _yaml
except ImportError as exc:
    raise ImportError(
        "PyYAML is required for the TCK config loader.\n"
        "Install it with:  pip install pyyaml"
    ) from exc

from tractusx_sdk.extensions.tck.connector import (
    ConnectorConfig,
    BackendConfig,
    PolicyConfig,
)

# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

_CONFIG_PATH = _os.path.join(_os.path.dirname(__file__), "tck_config.yaml")


def _load_yaml() -> dict:
    with open(_CONFIG_PATH, "r", encoding="utf-8") as fh:
        return _yaml.safe_load(fh)


def _connector(raw: dict, dataspace_version: str) -> ConnectorConfig:
    """Build a :class:`ConnectorConfig` from a raw YAML dict."""
    return ConnectorConfig(
        base_url=raw["base_url"],
        api_key=raw.get("api_key") or "",
        dataspace_version=dataspace_version,
        bpn=raw.get("bpn") or None,
        dsp_url=raw.get("dsp_url") or None,
        did=raw.get("did") or None,
    )


def _policy(raw: dict) -> PolicyConfig:
    """Build a :class:`PolicyConfig` from a raw YAML dict."""
    return PolicyConfig(
        context=raw.get("context") or None,
        permissions=raw.get("permissions") or [],
        profile=raw.get("profile") or None,
    )


# ---------------------------------------------------------------------------
# Public section class
# ---------------------------------------------------------------------------

class TckSection:
    """
    Holds pre-built connectivity and policy objects for one protocol variant.

    Attributes
    ----------
    provider : ConnectorConfig
    consumer : ConnectorConfig
    access_policy : PolicyConfig
        Default access policy for this section (BPNL-mode for Saturn).
    access_policy_did : PolicyConfig or None
        DID-mode access policy; only present on the ``saturn`` section.
    usage_policy : PolicyConfig
    protocol : str
        DSP protocol string to pass to :class:`DetailedTckConfig`.
    negotiation_context : list
        JSON-LD negotiation context to pass to :class:`DetailedTckConfig`.

    Methods
    -------
    backend() -> BackendConfig
        Returns a :class:`BackendConfig` with a unique ``/urn:uuid:<uuid4>``
        path appended.  Call once per test run so every run gets its own
        resource URL.
    """

    def __init__(self, raw: dict, dataspace_version: str) -> None:
        self._backend_base: str = raw["backend"]["base_url"].rstrip("/")
        self._backend_api_key: str | None = raw["backend"].get("api_key") or None
        self.provider: ConnectorConfig = _connector(raw["provider"], dataspace_version)
        self.consumer: ConnectorConfig = _connector(raw["consumer"], dataspace_version)

        pol = raw.get("policies", {})
        self.protocol: str = pol.get("protocol", "")
        self.negotiation_context: list = pol.get("negotiation_context") or []
        self.access_policy: PolicyConfig = _policy(pol.get("access_policy") or {})
        self.usage_policy: PolicyConfig = _policy(pol.get("usage_policy") or {})
        _did_raw = pol.get("access_policy_did")
        self.access_policy_did: PolicyConfig | None = _policy(_did_raw) if _did_raw else None

    def backend(self) -> BackendConfig:
        """Return a BackendConfig with a fresh UUID path — unique per call."""
        return BackendConfig(
            base_url=f"{self._backend_base}/urn:uuid:{_uuid.uuid4()}",
            api_key=self._backend_api_key,
        )


# ---------------------------------------------------------------------------
# Module-level section instances  (loaded once at import time)
# ---------------------------------------------------------------------------

_raw = _load_yaml()

jupiter: TckSection = TckSection(_raw["jupiter"], dataspace_version="jupiter")
"""Jupiter (EDC 0.8–0.10.x) — BPNL discovery, protocol ``dataspace-protocol-http``."""

saturn: TckSection = TckSection(_raw["saturn"], dataspace_version="saturn")
"""Saturn (EDC 0.11.x+) — BPNL and DID discovery, protocol ``dataspace-protocol-http:2025-1``.

Both ``bpn`` and ``did`` are populated on provider/consumer.
Scripts choose discovery mode via ``discovery_mode="bpnl"`` or ``discovery_mode="did"``.
"""
