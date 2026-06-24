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

# Running Tests

## Step 1: Install the SDK

```bash
pip install -e .
```

## Step 2: Configure the Environment

See [Configuration](configuration.md) for how to populate `tck-config.yaml` or create a custom YAML file.

## Step 3: Run the Tests

### Run a single test

```bash
cd tck/connector

# Saturn — BPNL discovery
python tck_e2e_saturn_0-11-X_simple.py
python tck_e2e_saturn_0-11-X_detailed.py

# Saturn — DID discovery
python tck_e2e_saturn_0-11-X_simple_did.py
python tck_e2e_saturn_0-11-X_detailed_did.py

# Jupiter (legacy protocol)
python tck_e2e_jupiter_0-10-X_simple.py
python tck_e2e_jupiter_0-10-X_detailed.py
```

### Run all 6 tests in parallel (live dashboard)

```bash
cd tck/connector

# Default config
./run_all_tests.sh

# Custom YAML config
./run_all_tests.sh --config /absolute/path/to/my_config.yaml

# Skip cleanup for all tests
./run_all_tests.sh --no-cleanup

# Combine options
./run_all_tests.sh --config my_config.yaml --no-cleanup --no-debug
```

The shell script launches all six tests in parallel, streams a live status table to the terminal, and writes per-test logs to:

```
tck/connector/logs/run_all_tests/<YYYY-MM-DD>/<HHMMSS_<hex6>>/
  ├── tck_e2e_jupiter_0-10-X_detailed.log
  ├── tck_e2e_jupiter_0-10-X_simple.log
  ├── tck_e2e_saturn_0-11-X_detailed.log
  ├── tck_e2e_saturn_0-11-X_detailed_did.log
  ├── tck_e2e_saturn_0-11-X_simple.log
  ├── tck_e2e_saturn_0-11-X_simple_did.log
  └── run_summary.log
```

### Run with a custom config section

```bash
# Use a non-default section name inside your YAML
python tck_e2e_saturn_0-11-X_simple.py \
  --config my_env.yaml \
  --config-section saturn_int
```

## Command-Line Options

All six TCK scripts and `run_all_tests.sh` share the same CLI interface. All flags passed to `run_all_tests.sh` are forwarded verbatim to every test script.

### Config file options

| Flag | Argument | Description |
|------|----------|-------------|
| `--config` | `PATH` | Load connectivity and policy values from `PATH` instead of the default `tck-config.yaml` |
| `--config-section` | `SECTION` | Section name to read from the YAML file (e.g. `jupiter`, `saturn`) |

### Individual field overrides

These flags override individual values **after** the YAML has been loaded:

| Flag | Description |
|------|-------------|
| `--provider-url URL` | Provider EDC base URL (**without** `/management` suffix) |
| `--provider-dma-path PATH` | Provider Management API path (default: `/management`) |
| `--consumer-url URL` | Consumer EDC base URL (**without** `/management` suffix) |
| `--consumer-dma-path PATH` | Consumer Management API path (default: `/management`) |
| `--backend-url URL` | Backend storage base URL |
| `--provider-api-key KEY` | Provider Management API key |
| `--consumer-api-key KEY` | Consumer Management API key |
| `--provider-bpn BPN` | Provider BPN (e.g. `BPNL00000000PROV`) |
| `--consumer-bpn BPN` | Consumer BPN (e.g. `BPNL00000000CONS`) |
| `--provider-dsp-url URL` | Provider DSP endpoint URL (BPNL-mode) |
| `--provider-dsp-url-did URL` | Provider DSP URL for DID-mode scripts |
| `--provider-did DID` | Provider DID (DID scripts only) |
| `--consumer-did DID` | Consumer DID (DID scripts only) |

### Execution options

**`--no-debug`** — Disable DEBUG-level logging (debug is **enabled by default**)

- Default behaviour shows verbose HTTP request/response logs and SDK internals
- Use `--no-debug` to see only INFO-level messages

**`--no-cleanup`** — Skip resource cleanup after the test (cleanup is **enabled by default**)

- Default behaviour deletes all provider resources (Contract Definitions, Assets, Policies) and backend data in reverse creation order inside a `finally` block
- Use `--no-cleanup` when:
    - Debugging failed tests (keep resources for inspection)
    - Performing manual audits or compliance checks
    - Running in environments with external cleanup automation

!!! note
    When cleanup is active, successful deletions are logged as `✓ Deleted [ResourceType]: [ResourceID]`. Failed deletions are logged as errors but do not cause the test to fail.

## Advanced Usage

### Custom test data

Modify `SAMPLE_ASPECT_MODEL` in any test script to use your own payload:

```python
SAMPLE_ASPECT_MODEL = {
    "yourModel": "yourData",
    "customField": 12345,
}
```

### Custom policies

To test custom policies, modify the `provision_data_on_provider()` function:

```python
access_policy = provider_service.create_policy(
    policy_id=f"custom-policy-{timestamp}",
    permissions=[{
        "action": "access",
        "constraint": {
            "leftOperand": "BusinessPartnerNumber",
            "operator": "eq",
            "rightOperand": "your-value"
        }
    }]
)
```

### Manual parallel execution

```bash
cd tck/connector

# Saturn BPNL + DID in parallel
python tck_e2e_saturn_0-11-X_detailed.py &
python tck_e2e_saturn_0-11-X_detailed_did.py &
wait

# Check results
grep "RESULT:" *_PASS.log *_FAIL.log
```

## CI/CD Integration

Example GitHub Actions workflow:

```yaml
name: TCK Tests
on: [push, pull_request]

jobs:
  tck-saturn:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install -e .
      - name: Run Saturn TCK (simple)
        env:
          PROVIDER_API_KEY: ${{ secrets.PROVIDER_API_KEY }}
          CONSUMER_API_KEY: ${{ secrets.CONSUMER_API_KEY }}
        run: |
          cd tck/connector
          python tck_e2e_saturn_0-11-X_simple.py
      - name: Upload logs
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: tck-logs
          path: tck/connector/*_e2e_run_*.log
```

## NOTICE

This work is licensed under the [CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/legalcode).

- SPDX-License-Identifier: CC-BY-4.0
- SPDX-FileCopyrightText: 2025, 2026 Contributors to the Eclipse Foundation
- SPDX-FileCopyrightText: 2025, 2026 Catena-X Automotive Network e.V.
- SPDX-FileCopyrightText: 2025, 2026 LKS Next
- SPDX-FileCopyrightText: 2025, 2026 Mondragon Unibertsitatea
- Source URL: [https://github.com/eclipse-tractusx/tractusx-sdk](https://github.com/eclipse-tractusx/tractusx-sdk)
