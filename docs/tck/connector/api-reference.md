<!--
Eclipse Tractus-X - Tractus-X SDK

Copyright (c) 2026 Catena-X Automotive Network e.V.
Copyright (c) 2026 Contributors to the Eclipse Foundation

See the NOTICE file(s) distributed with this work for additional
information regarding copyright ownership.

This program and the accompanying materials are made available under the
terms of the Apache License, Version 2.0 which is available at
https://www.apache.org/licenses/LICENSE-2.0.

SPDX-License-Identifier: Apache-2.0
-->

# TCK Extension API Reference

The TCK infrastructure lives in the SDK as a reusable extension module. The predefined scripts in `tck/connector/` are thin wrappers on top of it — you can import the same building blocks directly to write your own custom test cases without touching those scripts.

## Module Layout

```
src/tractusx_sdk/extensions/tck/
├── __init__.py                  # Top-level package
└── connector/
    ├── __init__.py              # Public exports (everything listed below)
    ├── models.py                # Typed configuration dataclasses
    ├── helpers.py               # Low-level building blocks
    └── runners.py               # High-level test runners (full lifecycle)
```

### Import path

```python
from tractusx_sdk.extensions.tck.connector import (
    # Configuration models
    ConnectorConfig, BackendConfig, PolicyConfig, AssetConfig,
    SimpleTckConfig, DetailedTckConfig,
    # High-level runners
    run_simple_test, run_detailed_test,
    # Low-level helpers (pick what you need)
    initialize_provider_service, initialize_consumer_service,
    upload_sample_data, provision_simple,
    consume_simple_bpnl, consume_simple_did,
    access_data_with_edr,
    cleanup_provider_resources, cleanup_backend_data,
    setup_tck_logging, finalize_log, print_summary,
    run_step, mark_skipped_phases,
    build_tck_cli_parser, apply_cli_overrides, configure_debug_logging,
    SAMPLE_ASPECT_MODEL_DATA, DEFAULT_ASSET_CONFIG,
)
```

---

## Function Quick Reference

All public exports from `tractusx_sdk.extensions.tck.connector`, grouped by category.

### Configuration Models

| Class | Description |
|-------|-------------|
| `ConnectorConfig` | EDC endpoint config (URL, API key, BPNL, DID, protocol version) |
| `BackendConfig` | Backend storage service config (URL, API key) |
| `PolicyConfig` | ODRL policy config (permissions, JSON-LD context, profile) |
| `AssetConfig` | EDC asset config with Catena-X defaults (dct_type, semantic_id, proxy_params) |
| `SimpleTckConfig` | Complete config bundle for the simple test lifecycle |
| `DetailedTckConfig` | Complete config bundle for the detailed step-by-step test lifecycle |

### Test Runners

| Function | Returns | Description |
|----------|---------|-------------|
| `run_simple_test(config, script_dir)` | `"PASS"` \| `"FAIL"` | Full simple lifecycle: CLI parsing → logging → provision → consume → cleanup |
| `run_detailed_test(config, script_dir)` | `"PASS"` \| `"FAIL"` | Full detailed lifecycle with explicit per-step output and EDR poll |

### Logging Helpers

| Function | Returns | Description |
|----------|---------|-------------|
| `setup_tck_logging(test_case_name, script_dir)` | `(logger, log_file_path)` | Create console + timestamped file logger under `logs/<name>/<date>/` |
| `finalize_log(log_file, result)` | `None` | Flush/close all handlers; rename log file with `_PASS` or `_FAIL` suffix |
| `print_header(logger, title)` | `None` | Print an 80-char `═`-bordered section heading to the log |
| `print_separator(logger, title)` | `None` | Print a 70-char `─`-bordered separator line |

### Service Initialization

| Function | Returns | Description |
|----------|---------|-------------|
| `initialize_provider_service(logger, provider_config, header_fn=None)` | `ConnectorProviderService` | Create and configure a provider connector service instance |
| `initialize_consumer_service(logger, consumer_config, header_fn=None, connection_manager=None)` | `ConnectorConsumerService` | Create and configure a consumer connector service instance |

### Backend Operations

| Function / Constant | Returns | Description |
|---------------------|---------|-------------|
| `upload_sample_data(logger, backend_config, sample_data, header_fn=None, verbose=False)` | `None` | POST sample data to the backend storage endpoint; raises on non-2xx |
| `SAMPLE_ASPECT_MODEL_DATA` | `dict` | Built-in `BusinessPartnerCertificate` sample payload ready to upload |

### Provision (Phase 1)

| Function | Returns | Description |
|----------|---------|-------------|
| `provision_simple(logger, provider, access_policy_config, usage_policy_config, asset_config, backend_config, consumer_config, header_fn=None, id_prefix="e2e")` | `dict` | Create access policy, usage policy, asset, and contract definition in one call; returns `{"asset_id", "access_policy_id", "usage_policy_id", "contract_def_id"}` |

### Consume (Phase 2)

| Function | Returns | Description |
|----------|---------|-------------|
| `consume_simple_bpnl(logger, consumer, asset_id, provider_config, accepted_policies=None, header_fn=None, verify=False)` | `Response` | Full consumer flow via BPNL discovery — catalog → negotiate → transfer → EDR in one call |
| `consume_simple_did(logger, consumer, asset_id, provider_config, accepted_policies=None, header_fn=None, verify=False)` | `Response` | Same as above but resolves the provider DSP endpoint from the DID document (no BPNL lookup) |

### Data Access (Phase 3)

| Function | Returns | Description |
|----------|---------|-------------|
| `access_data_with_edr(logger, dataplane_url, access_token, header_fn=None, path="/", verify=False)` | `Response` | GET the submodel data from the provider data plane using an EDR token |

### Cleanup

| Function | Returns | Description |
|----------|---------|-------------|
| `cleanup_provider_resources(logger, provider_service, provision_ids, header_fn=None)` | `None` | Delete contract definition, asset, usage policy, and access policy (in reverse order) |
| `cleanup_backend_data(logger, backend_config, header_fn=None, verify=False)` | `None` | DELETE the backend resource at `backend_config["base_url"]` |

### Step Tracking

| Function | Returns | Description |
|----------|---------|-------------|
| `run_step(steps, name, fn)` | result of `fn()` | Execute `fn()`, record timing and PASS/FAIL into `steps`; re-raises exceptions |
| `mark_skipped_phases(steps, all_phase_names)` | `None` | Append SKIP entries for any phases in `all_phase_names` not yet recorded in `steps` |
| `print_summary(logger, steps, overall_result, total_elapsed, title="", provision_ids=None, consumption_result=None, http_status=None)` | `None` | Print the formatted `╔═══╗` summary table with per-step results and overall verdict |

### CLI Utilities

| Function | Returns | Description |
|----------|---------|-------------|
| `build_tck_cli_parser(description, epilog="", include_did=False)` | `ArgumentParser` | Build the standard TCK argument parser with all `--provider-*`, `--consumer-*`, `--config`, and `--no-cleanup` flags |
| `configure_debug_logging(logger, debug)` | `None` | Elevate all handlers to `DEBUG` level when `debug=True` |
| `apply_cli_overrides(args, provider_config, consumer_config, backend_config)` | `(p, c, b)` | Apply parsed CLI flags onto config dicts and return modified copies (originals not mutated) |

### Constants

| Name | Type | Value / Purpose |
|------|------|-----------------|
| `SAMPLE_ASPECT_MODEL_DATA` | `dict` | Built-in `BusinessPartnerCertificate` JSON payload |
| `DEFAULT_ASSET_CONFIG` | `dict` | Default asset config dict (`dct_type`, `semantic_id`, `version`, `proxy_params`) |
| `CONTENT_TYPE_JSON` | `str` | `"application/json"` |
| `MANAGEMENT_PATH` | `str` | `"/management"` |
| `LOG_RESPONSE_SUFFIX` | `str` | `" - Response: %s"` |

---

## Configuration Models

Defined in `models.py`. All are `@dataclass` types.

---

### `ConnectorConfig`

Typed configuration for a single EDC connector endpoint (Provider **or** Consumer).

```python
@dataclass
class ConnectorConfig:
    base_url: str              # EDC Control Plane base URL
    dma_path: str = "/management"
    api_key_header: str = "X-Api-Key"
    api_key: str = ""
    dataspace_version: str = "saturn"   # "saturn" | "jupiter"
    bpn: Optional[str] = None           # for BPNL-based discovery
    did: Optional[str] = None           # for DID-based discovery
    dsp_url: Optional[str] = None       # DSP protocol endpoint
```

| `dataspace_version` | Protocol | EDC versions |
|---------------------|----------|-------------|
| `"saturn"` | `dataspace-protocol-http:2025-1` | 0.11.x+ |
| `"jupiter"` | `dataspace-protocol-http` | 0.8.x–0.10.x |

`.to_dict()` returns a plain dict with `None`-valued optional fields stripped.

---

### `BackendConfig`

Configuration for the backend data storage service.

```python
@dataclass
class BackendConfig:
    base_url: str              # Full URL including UUID path segment
    api_key_header: str = "X-Api-Key"
    api_key: str = ""
```

!!! tip
    Append `/urn:uuid:<uuid4>` to the base URL at construction time so every run gets a unique storage path.

---

### `PolicyConfig`

ODRL policy configuration.

```python
@dataclass
class PolicyConfig:
    permissions: list = field(default_factory=list)
    context: Optional[list] = None    # JSON-LD @context (required for Jupiter / DID)
    profile: Optional[str] = None     # e.g. "cx-policy:profile2405"
```

---

### `AssetConfig`

EDC Asset configuration with sensible Catena-X defaults.

```python
@dataclass
class AssetConfig:
    dct_type: str = "https://w3id.org/catenax/taxonomy#Submodel"
    semantic_id: str = "urn:samm:io.catenax.business_partner_certificate:3.1.0#BusinessPartnerCertificate"
    version: str = "1.0"
    proxy_params: dict = field(default_factory=lambda: {
        "proxyQueryParams": "true",
        "proxyPath": "true",
        "proxyMethod": "true",
        "proxyBody": "false",
    })
```

---

### `SimpleTckConfig`

Complete configuration bundle for a **simple** test (single-call consumer flow).

```python
@dataclass
class SimpleTckConfig:
    test_name: str                          # Used for log directory / file naming
    provider: ConnectorConfig
    consumer: ConnectorConfig
    backend: BackendConfig
    access_policy: PolicyConfig
    usage_policy: PolicyConfig
    asset: AssetConfig = field(default_factory=AssetConfig)
    accepted_policies: Optional[list] = None  # None = accept any offer
    sample_data: Optional[dict] = None         # None = use built-in default
    cleanup: bool = True
    discovery_mode: str = "bpnl"              # "bpnl" | "did"
    verify_ssl: bool = False
    banner_title: str = ""
    summary_title: str = ""
    config_section: str = ""                  # YAML section used with --config
```

---

### `DetailedTckConfig`

Complete configuration bundle for a **detailed** test (step-by-step flow).

```python
@dataclass
class DetailedTckConfig:
    test_name: str
    provider: ConnectorConfig
    consumer: ConnectorConfig
    backend: BackendConfig
    access_policy: PolicyConfig
    usage_policy: PolicyConfig
    asset: AssetConfig = field(default_factory=AssetConfig)
    sample_data: Optional[dict] = None
    cleanup: bool = True
    discovery_mode: str = "bpnl"              # "bpnl" | "did"
    verify_ssl: bool = False
    protocol: str = "dataspace-protocol-http:2025-1"
    negotiation_context: Optional[list] = None  # None = auto-derived from access_policy
    banner_title: str = ""
    summary_title: str = ""
    config_section: str = ""
```

---

## Test Runners

Defined in `runners.py`. These are the **recommended** entry points for most use cases — they handle the complete lifecycle from CLI parsing through log finalization.

---

### `run_simple_test(config, script_dir) → str`

Runs a complete simple TCK test. The consumer flow is executed via the SDK's `do_get_with_bpnl()` / `do_get()` convenience method.

**Lifecycle managed automatically:**

1. CLI argument parsing (`--provider-url`, `--no-cleanup`, `--config`, …)
2. Logging setup (console + timestamped file)
3. Service initialization (provider + consumer)
4. Phase 0 — upload sample data to backend
5. Phase 1 — provision (asset + policies + contract definition)
6. Phase 2 — consume via `do_get_with_bpnl` or `do_get`
7. Test summary (PASS/FAIL table)
8. Optional cleanup
9. Log file finalization (renamed with PASS/FAIL suffix)

**Arguments:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `config` | `SimpleTckConfig` | Complete test configuration |
| `script_dir` | `str` | Directory of your calling script (`os.path.dirname(__file__)`) |

**Returns:** `"PASS"` or `"FAIL"`

**Minimal usage:**

```python
import os
import uuid
from tractusx_sdk.extensions.tck.connector import (
    run_simple_test,
    ConnectorConfig, BackendConfig, PolicyConfig, SimpleTckConfig,
)

result = run_simple_test(
    config=SimpleTckConfig(
        test_name="my_saturn_simple",
        provider=ConnectorConfig(
            base_url="http://provider.example.com",
            api_key="SECRET",
            bpn="BPNL00000003PROV",
            dsp_url="http://provider.example.com/api/v1/dsp",
            dataspace_version="saturn",
        ),
        consumer=ConnectorConfig(
            base_url="http://consumer.example.com",
            api_key="SECRET",
            bpn="BPNL00000003CONS",
            dataspace_version="saturn",
        ),
        backend=BackendConfig(
            base_url=f"http://backend.example.com/api/data/urn:uuid:{uuid.uuid4()}",
        ),
        access_policy=PolicyConfig(permissions=[{
            "action": "access",
            "constraint": {
                "leftOperand": "BusinessPartnerNumber",
                "operator": "isAnyOf",
                "rightOperand": None,   # auto-filled with consumer BPN
            }
        }]),
        usage_policy=PolicyConfig(permissions=[{
            "action": "use",
            "constraint": {"and": [
                {"leftOperand": "Membership", "operator": "eq", "rightOperand": "active"},
            ]}
        }]),
        discovery_mode="bpnl",
        cleanup=True,
        config_section="saturn",
    ),
    script_dir=os.path.dirname(__file__),
)
```

---

### `run_detailed_test(config, script_dir) → str`

Runs a complete detailed TCK test with verbose step-by-step output.

**Lifecycle managed automatically** (same as simple, but Phase 2 is split into explicit sub-steps):

- Step 2.0 — discover provider (or use DID/BPNL directly)
- Step 2.1 — fetch catalog, extract offer
- Step 2.2 — negotiate contract
- Step 2.3 — poll for `FINALIZED` state → contract agreement ID
- Step 2.4 — initiate transfer process
- Step 2.5 — poll for EDR token
- Phase 3 — HTTP GET with EDR token against the data plane

**Arguments:** Same as `run_simple_test` but takes a `DetailedTckConfig`.

**Returns:** `"PASS"` or `"FAIL"`

```python
from tractusx_sdk.extensions.tck.connector import run_detailed_test, DetailedTckConfig
# ... build config ...
result = run_detailed_test(config=my_config, script_dir=os.path.dirname(__file__))
```

---

## Low-Level Helpers

Defined in `helpers.py`. Use these when the runners don't give you enough control — for example, if you want to skip a phase, inject custom behaviour between steps, or assemble a completely custom flow.

---

### Logging

#### `setup_tck_logging(test_case_name, script_dir) → (logger, log_file_path)`

Set up console + timestamped file logging. Creates `logs/<test_name>/<date>/` structure.

```python
logger, log_file = setup_tck_logging("my_test", os.path.dirname(__file__))
```

#### `finalize_log(log_file, result)`

Flush, close all handlers, and rename the log file with `_PASS` or `_FAIL` suffix.

#### `print_header(logger, title)` / `print_separator(logger, title)`

Print a 80-char / 70-char `=` bordered section heading to the log.

---

### Service Initialization

#### `initialize_provider_service(logger, provider_config, header_fn=None) → ConnectorProviderService`

Create and configure a provider connector service instance.

```python
provider = initialize_provider_service(logger, config.provider.to_dict())
```

#### `initialize_consumer_service(logger, consumer_config, header_fn=None, connection_manager=None) → ConnectorConsumerService`

Create and configure a consumer connector service instance.

```python
consumer = initialize_consumer_service(logger, config.consumer.to_dict())
```

Both functions accept a `header_fn(title)` callable for custom section formatting, and log initialization details (URL, version, BPN/DID).

---

### Backend Operations

#### `upload_sample_data(logger, backend_config, sample_data, header_fn=None, verbose=False)`

`POST` `sample_data` to `backend_config["base_url"]`. Raises on non-2xx responses.

```python
upload_sample_data(logger, backend.to_dict(), {"key": "value"})
```

Set `verbose=True` to log the full request/response bodies (used by detailed tests).

#### `SAMPLE_ASPECT_MODEL_DATA`

Built-in sample `BusinessPartnerCertificate` payload. Use as-is or copy and modify:

```python
from tractusx_sdk.extensions.tck.connector import SAMPLE_ASPECT_MODEL_DATA

my_data = {**SAMPLE_ASPECT_MODEL_DATA, "businessPartnerNumber": "BPNLXXXXXXXX"}
```

---

### Provision (Phase 1)

#### `provision_simple(logger, provider, access_policy_config, usage_policy_config, asset_config, backend_config, consumer_config, header_fn=None, id_prefix="e2e") → dict`

Create access policy, usage policy, asset, and contract definition in one call. Handles BPN/DID constraint substitution automatically.

**Returns:** `{"asset_id": …, "access_policy_id": …, "usage_policy_id": …, "contract_def_id": …}`

```python
ids = provision_simple(
    logger, provider,
    access_policy_config=config.access_policy.to_dict(),
    usage_policy_config=config.usage_policy.to_dict(),
    asset_config=config.asset.to_dict(),
    backend_config=backend.to_dict(),
    consumer_config=config.consumer.to_dict(),
    id_prefix="my-test",
)
```

---

### Consume (Phase 2)

#### `consume_simple_bpnl(logger, consumer, asset_id, provider_config, accepted_policies=None, header_fn=None, verify=False) → Response`

Call `consumer.do_get_with_bpnl()` — the SDK handles catalog discovery, negotiation, transfer, and EDR retrieval in a single call. Returns the final `requests.Response`.

```python
import time; time.sleep(3)   # give provider time to process
response = consume_simple_bpnl(logger, consumer, ids["asset_id"], provider.to_dict())
assert response.status_code == 200
```

#### `consume_simple_did(logger, consumer, asset_id, provider_config, accepted_policies=None, header_fn=None, verify=False) → Response`

Same as above but uses `consumer.do_get()` with DID-based discovery (no BPNL lookup required).

```python
response = consume_simple_did(logger, consumer, ids["asset_id"], provider.to_dict())
```

---

### Data Access (Phase 3)

#### `access_data_with_edr(logger, dataplane_url, access_token, header_fn=None, path="/", verify=False) → Response`

`GET` the data from the provider data plane using the EDR token. Logs the truncated token and full response.

```python
response = access_data_with_edr(
    logger,
    dataplane_url=edr["endpoint"],
    access_token=edr["authorization"],
)
assert response.status_code == 200
```

---

### Cleanup

#### `cleanup_provider_resources(logger, provider_service, provision_ids, header_fn=None)`

Delete contract definition, asset, usage policy, and access policy (in reverse creation order).

```python
cleanup_provider_resources(logger, provider, ids)
```

#### `cleanup_backend_data(logger, backend_config, header_fn=None, verify=False)`

`DELETE` the backend resource at `backend_config["base_url"]`.

---

### Step Tracking

#### `run_step(steps, name, fn) → result`

Execute `fn()`, record timing and PASS/FAIL into `steps`. Re-raises any exception.

```python
steps = []
ids = run_step(steps, "Phase 1 · Provision", lambda: provision_simple(...))
```

#### `mark_skipped_phases(steps, all_phase_names)`

Append `SKIP` entries for any phases in `all_phase_names` not yet recorded in `steps`.

```python
mark_skipped_phases(steps, ["Phase 0", "Phase 1", "Phase 2", "Phase 3"])
```

#### `print_summary(logger, steps, overall_result, total_elapsed, title="...", provision_ids=None, consumption_result=None, http_status=None)`

Print the formatted `╔═══╗` summary table with per-step results, overall verdict, and optional resource IDs.

---

### CLI Utilities

#### `build_tck_cli_parser(description, epilog="", include_did=False) → ArgumentParser`

Build the standard TCK argument parser. Includes `--no-debug`, `--no-cleanup`, `--config`, `--config-section`, all `--provider-*` / `--consumer-*` / `--backend-*` flags. Pass `include_did=True` to add `--provider-did` / `--consumer-did`.

```python
parser = build_tck_cli_parser("My custom TCK test", include_did=True)
args = parser.parse_args()
```

#### `configure_debug_logging(logger, debug: bool)`

Elevate all handlers to `DEBUG` level when `debug=True`.

#### `apply_cli_overrides(args, provider_config, consumer_config, backend_config) → (p, c, b)`

Apply parsed CLI fields onto config dicts. Returns copies — originals are not mutated. Useful when not using the runners but still want to respect standard CLI flags.

---

## Building a Fully Custom Test

Below is a complete example that skips the runners entirely and assembles the test phase by phase.

```python
#!/usr/bin/env python3
"""My custom Saturn TCK test — full manual flow."""

import os
import sys
import time
import uuid

from tractusx_sdk.extensions.tck.connector import (
    ConnectorConfig, BackendConfig, PolicyConfig, AssetConfig,
    setup_tck_logging, finalize_log, print_summary,
    initialize_provider_service, initialize_consumer_service,
    upload_sample_data, provision_simple, consume_simple_bpnl,
    cleanup_provider_resources, cleanup_backend_data,
    run_step, mark_skipped_phases,
    SAMPLE_ASPECT_MODEL_DATA,
)

SCRIPT_DIR = os.path.dirname(__file__)

# ── Configuration ──────────────────────────────────────────────────────────────
provider = ConnectorConfig(
    base_url="http://dataprovider-controlplane.tx.test",
    api_key="TEST2",
    bpn="BPNL00000003AYRE",
    dsp_url="http://dataprovider-controlplane.tx.test/api/v1/dsp",
    dataspace_version="saturn",
)
consumer = ConnectorConfig(
    base_url="http://dataconsumer-1-controlplane.tx.test",
    api_key="TEST1",
    bpn="BPNL00000003AZQP",
    dataspace_version="saturn",
)
backend = BackendConfig(
    base_url=f"http://dataprovider-submodelserver.tx.test/urn:uuid:{uuid.uuid4()}",
)
access_policy = PolicyConfig(permissions=[{
    "action": "access",
    "constraint": {
        "leftOperand": "BusinessPartnerNumber",
        "operator": "isAnyOf",
        "rightOperand": None,   # auto-filled with consumer BPN
    }
}])
usage_policy = PolicyConfig(permissions=[{
    "action": "use",
    "constraint": {"and": [
        {"leftOperand": "Membership", "operator": "eq", "rightOperand": "active"},
        {"leftOperand": "FrameworkAgreement", "operator": "eq", "rightOperand": "DataExchangeGovernance:1.0"},
    ]}
}])
asset = AssetConfig()

# ── Setup ──────────────────────────────────────────────────────────────────────
logger, log_file = setup_tck_logging("my_custom_test", SCRIPT_DIR)

provider_svc = initialize_provider_service(logger, provider.to_dict())
consumer_svc = initialize_consumer_service(logger, consumer.to_dict())

# ── Test phases ────────────────────────────────────────────────────────────────
steps = []
ids = None
overall = "FAIL"
t0 = time.time()

ALL_PHASES = ["Phase 0 · Upload data", "Phase 1 · Provision", "Phase 2 · Consume"]

try:
    run_step(steps, "Phase 0 · Upload data",
             lambda: upload_sample_data(logger, backend.to_dict(), SAMPLE_ASPECT_MODEL_DATA))

    ids = run_step(steps, "Phase 1 · Provision",
                   lambda: provision_simple(
                       logger, provider_svc,
                       access_policy.to_dict(), usage_policy.to_dict(),
                       asset.to_dict(), backend.to_dict(), consumer.to_dict(),
                   ))

    time.sleep(3)

    response = run_step(steps, "Phase 2 · Consume",
                        lambda: consume_simple_bpnl(
                            logger, consumer_svc, ids["asset_id"], provider.to_dict()
                        ))

    assert response.status_code == 200, f"Got HTTP {response.status_code}"
    overall = "PASS"

except Exception as exc:
    logger.exception("Test failed: %s", exc)
    mark_skipped_phases(steps, ALL_PHASES)

finally:
    print_summary(logger, steps, overall, time.time() - t0, provision_ids=ids)

    if ids:
        cleanup_provider_resources(logger, provider_svc, ids)
        cleanup_backend_data(logger, backend.to_dict())

    finalize_log(log_file, overall)

sys.exit(0 if overall == "PASS" else 1)
```

---

## Constants

| Name | Value |
|------|-------|
| `CONTENT_TYPE_JSON` | `"application/json"` |
| `MANAGEMENT_PATH` | `"/management"` |
| `LOG_RESPONSE_SUFFIX` | `" - Response: %s"` |
| `SAMPLE_ASPECT_MODEL_DATA` | Built-in `BusinessPartnerCertificate` JSON payload |
| `DEFAULT_ASSET_CONFIG` | Default asset configuration dict (`dct_type`, `semantic_id`, `version`, `proxy_params`) |

## NOTICE

This work is licensed under the [CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/legalcode).

- SPDX-License-Identifier: CC-BY-4.0
- SPDX-FileCopyrightText: 2025, 2026 Contributors to the Eclipse Foundation
- SPDX-FileCopyrightText: 2025, 2026 Catena-X Automotive Network e.V.
- SPDX-FileCopyrightText: 2025, 2026 LKS Next
- SPDX-FileCopyrightText: 2025, 2026 Mondragon Unibertsitatea
- Source URL: [https://github.com/eclipse-tractusx/tractusx-sdk](https://github.com/eclipse-tractusx/tractusx-sdk)
