# Connector Examples

This directory is reserved for connector service usage examples demonstrating provider and consumer operations with the Tractus-X SDK.

## Test Compatibility Kit (TCK)

For complete end-to-end examples of connector interactions — including asset provisioning, catalog discovery, contract negotiation, EDR token flow, and data consumption — see the **[Connector TCK](../../../../tck/connector/README.md)**.

The TCK provides 6 ready-to-run test scripts covering:

| Protocol | EDC Version | Scripts |
|----------|-------------|---------|
| **Saturn** (DSP 2025-1) | 0.11.x+ | `tck_e2e_saturn_0-11-X_detailed.py`, `tck_e2e_saturn_0-11-X_simple.py`, `*_did.py` variants |
| **Jupiter** (Legacy DSP) | 0.8.x–0.10.x | `tck_e2e_jupiter_0-10-X_detailed.py`, `tck_e2e_jupiter_0-10-X_simple.py` |

Each script demonstrates real SDK usage patterns (provider setup, consumer negotiation, data retrieval) and can serve as a reference for building your own connector integrations.

```bash
# Run all TCK tests
cd tck/connector
./run_all_tests.sh
```

See the [TCK documentation](../../../../docs/tck/index.md) for configuration and CI/CD integration guidance.

## TCK Extension Module

The TCK functionality is also available as a reusable Python module in the SDK's extensions library at `tractusx_sdk.extensions.tck.connector`. This module provides:

- **`runners`** — Pre-built test runners that orchestrate full E2E flows (provision, negotiate, consume)
- **`helpers`** — Helper functions for catalog discovery, negotiation, and data retrieval
- **`models`** — Configuration models (`TckConfig`) for defining provider/consumer/backend settings and policies

You can import and use these directly in your own test suites or integration scripts:

```python
from tractusx_sdk.extensions.tck.connector.runners import run_detailed_test
from tractusx_sdk.extensions.tck.connector.models import TckConfig
```

## NOTICE

This work is licensed under the [CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/legalcode).

- SPDX-License-Identifier: CC-BY-4.0
- SPDX-FileCopyrightText: 2025 Contributors to the Eclipse Foundation
- Source URL: <https://github.com/eclipse-tractusx/tractusx-sdk>
