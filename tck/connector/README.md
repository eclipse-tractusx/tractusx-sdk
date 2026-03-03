# Tractus-X SDK - Test Compatibility Kit (TCK)

## Overview

The **Test Compatibility Kit (TCK)** provides comprehensive end-to-end (E2E) testing scripts to validate that Eclipse Dataspace Connector (EDC) implementations work correctly with the Tractus-X SDK. These tests verify the complete data exchange flow from provider data provision through consumer data consumption.

The TCK is designed for use with:

- **EDC**: [Eclipse Tractus-X EDC](https://github.com/eclipse-tractusx/tractusx-edc)
- **Backend**: [simple-data-backend](https://github.com/eclipse-tractusx/tractus-x-umbrella/tree/main/simple-data-backend) from Tractus-X Umbrella

The TCK supports both legacy and current EDC protocol versions:

- **Jupiter Protocol**: Legacy DSP (`dataspace-protocol-http`) for EDC v0.8.0–0.10.x
- **Saturn Protocol**: Current DSP 2025-1 (`dataspace-protocol-http:2025-1`) for EDC v0.11.x+

## Purpose

The TCK validates:
✅ **Management API Compatibility**: Asset, Policy, and Contract Definition creation  
✅ **DSP Protocol Compliance**: Catalog requests, contract negotiation, transfer processes  
✅ **ODRL Policy Enforcement**: BPN-based access control, framework agreements, usage policies  
✅ **Verifiable Credentials**: Proper dataspace onboarding and credential validation required for policy compliance  
✅ **EDR Token Flow**: Endpoint Data Reference generation and authenticated data access  
✅ **JSON-LD Context Handling**: Proper semantic web standards across protocol versions  
✅ **SDK Service Layer**: Provider and Consumer service initialization and operations  

> **Note**: These tests require both Provider and Consumer organizations to be properly onboarded in the Catena-X dataspace with valid Verifiable Credentials that satisfy the policy constraints being tested.  

## TCK Test Scripts

The TCK provides **6 test scripts** covering two protocol versions, two complexity levels, and two discovery modes:

| Script | Protocol | EDC Version | Discovery | Complexity | Purpose |
| -------- | ---------- | ------------- | ----------- | ------------ | --------- |
| `tck_e2e_saturn_0-11-X_detailed.py` | Saturn (DSP 2025-1) | 0.11.x+ | BPNL | Detailed | Step-by-step validation of each phase |
| `tck_e2e_saturn_0-11-X_simple.py` | Saturn (DSP 2025-1) | 0.11.x+ | BPNL | Simple | Single-call validation via `do_get_with_bpnl()` |
| `tck_e2e_saturn_0-11-X_detailed_did.py` | Saturn (DSP 2025-1) | 0.11.x+ | DID | Detailed | Step-by-step validation using DID-based discovery |
| `tck_e2e_saturn_0-11-X_simple_did.py` | Saturn (DSP 2025-1) | 0.11.x+ | DID | Simple | Single-call validation using DID-based discovery |
| `tck_e2e_jupiter_0-10-X_detailed.py` | Jupiter (Legacy DSP) | 0.8.x–0.10.x | BPNL | Detailed | Step-by-step validation (legacy protocol) |
| `tck_e2e_jupiter_0-10-X_simple.py` | Jupiter (Legacy DSP) | 0.8.x–0.10.x | BPNL | Simple | Single-call validation (legacy protocol) |

### Detailed vs. Simple Tests

**Detailed Tests** (`*_detailed.py`):

- Explicit control over each phase (provision, catalog, negotiate, transfer, access)
- Validates individual API responses at each step
- Comprehensive logging of all requests and responses
- Best for: Debugging, learning the flow, verifying specific behaviors

**Simple Tests** (`*_simple.py`):

- Uses SDK's `do_get_with_bpnl()` convenience method
- Entire consumer flow (catalog → negotiate → transfer → EDR → GET) in one call
- Minimal code, maximum automation
- Best for: Quick smoke tests, CI/CD integration, production usage patterns

## Test Flow

All TCK tests follow this standardized flow:

```mermaid
sequenceDiagram
    participant Backend as Backend Storage
    participant Provider as Provider EDC
    participant Consumer as Consumer EDC
    
    Note over Backend: Phase 0: Upload Sample Data
    Backend->>Backend: Store test payload (JSON)
    
    Note over Provider: Phase 1: Provider Data Provision
    Provider->>Provider: Create Access Policy (BPN-based)
    Provider->>Provider: Create Usage Policy (Framework Agreement)
    Provider->>Provider: Create Asset (backend reference)
    Provider->>Provider: Create Contract Definition
    
    Note over Consumer,Provider: Phase 2: Consumer Data Consumption
    Consumer->>Provider: Discover connector (via BPNL)
    Consumer->>Provider: Request catalog (filtered by asset ID)
    Provider-->>Consumer: Catalog with offers
    
    Consumer->>Provider: Initiate contract negotiation
    Note over Provider: State: REQUESTING → REQUESTED<br/>→ AGREED → VERIFIED → FINALIZED
    Provider-->>Consumer: Contract Agreement ID
    
    Consumer->>Provider: Start transfer process (HttpData-PULL)
    Provider-->>Consumer: Transfer Process ID
    
    Consumer->>Provider: Poll for EDR token
    Provider-->>Consumer: EDR (endpoint + authorization token)
    
    Note over Consumer,Provider: Phase 3: Data Access
    Consumer->>Provider: HTTP GET with EDR token
    Provider->>Backend: Proxy request (validate token)
    Backend-->>Provider: Data payload
    Provider-->>Consumer: Data payload
```

## Configuration

All 6 TCK scripts share a single YAML configuration file — **`tck-config.yaml`** — as their source of truth.  Edit only this file when switching environments; the scripts read it automatically at startup.

An **INT environment template** is provided in `tck_int_config.yaml`.  Fill in the `<PLACEHOLDER>` tokens and pass it to any test via `--config` (see [CLI Reference](#command-line-options)).

### Config File Structure

```
tck/connector/
├── tck-config.yaml          ← default (local umbrella / tx.test)
├── tck_int_config.yaml      ← INT environment template (fill in placeholders)
└── my_custom_config.yaml    ← any additional environment you create
```

### YAML Sections

Each YAML file contains one or more **named sections** (e.g. `jupiter`, `saturn`).  Every test script knows its own section name, so no extra flag is needed when using the default file:

| Section | Used by scripts | Protocol |
|---------|-----------------|----------|
| `jupiter` | `tck_e2e_jupiter_0-10-X_*.py` | `dataspace-protocol-http` |
| `saturn`  | `tck_e2e_saturn_0-11-X_*.py` (all 4) | `dataspace-protocol-http:2025-1` |

### Section Layout

```yaml
<section_name>:
  provider:
    base_url:  "https://your-provider-edc/management"
    api_key:   "<key>"
    bpn:       "BPNL..."
    dsp_url:     "https://your-provider-edc/api/v1/dsp"          # BPNL scripts
    dsp_url_did: "https://your-provider-edc/api/v1/dsp/2025-1"  # DID scripts only (saturn); omit if same as dsp_url
    did:       "did:web:..."   # saturn DID-mode only; set to ~ otherwise

  consumer:
    base_url:  "https://your-consumer-edc/management"
    api_key:   "<key>"
    bpn:       "BPNL..."
    did:       "did:web:..."   # saturn DID-mode only; set to ~ otherwise

  backend:
    base_url:  "https://your-backend/api/data"  # NO trailing UUID
    api_key:   "<key>"   # set to ~ if no auth needed

  policies:
    protocol:            "dataspace-protocol-http"        # or :2025-1
    negotiation_context: [ ... ]                          # ODRL @context array
    access_policy:       { permissions: [...] }           # BPN / Membership rule
    access_policy_did:   { context: [...], permissions: [...] }  # saturn DID only
    usage_policy:        { permissions: [...] }           # framework / purpose rule
```

> **Backend `base_url`**: Do NOT append a UUID here.  Each test appends `/urn:uuid:<uuid4>` at runtime so every run gets a unique resource path.

> **`dsp_url` / `dsp_url_did`**: Two separate DSP endpoint fields can be set under `provider` in the Saturn section when BPNL and DID modes use different paths.  BPNL scripts read `dsp_url`; DID scripts (`*_did.py`) read `dsp_url_did` and fall back to `dsp_url` if `dsp_url_did` is absent.  For Jupiter (BPNL only), only `dsp_url` is needed.  Do **not** include the protocol-version suffix in the Consumer `base_url` — the SDK and EDC handle it automatically.

> **BPN Format**: Must match the format registered in your Discovery Service (`BPNL` prefix for legal entities).

> **`access_policy_did`**: Only required in the `saturn` section.  Leave absent or `~` in the `jupiter` section.

## Running TCK Tests

> **💡 Quick Tips**:
>
> - **Debug logging**: Enabled by default. Use `--no-debug` to disable verbose output.
> - **Cleanup**: Enabled by default. Use `--no-cleanup` to preserve resources after test completion.
> - See [Command-Line Options](#command-line-options) for detailed information.

### Prerequisites

1. **Two EDC Connectors** (Provider and Consumer):
   - EDC Implementation: [Eclipse Tractus-X EDC](https://github.com/eclipse-tractusx/tractusx-edc)
   - For Saturn: Version 0.11.x or higher
   - For Jupiter: Version 0.8.0 – 0.10.x
   - Both accessible via HTTP/HTTPS
   - Management API enabled with authentication

2. **Backend Storage Service**:
   - Recommended: [simple-data-backend](https://github.com/eclipse-tractusx/tractus-x-umbrella/tree/main/simple-data-backend) from Tractus-X Umbrella
   - HTTP-accessible endpoint for storing test data
   - Optional API key authentication support
   - Reachable from Provider Data Plane

3. **Network Connectivity**:
   - Your machine → Provider Control Plane (Management API)
   - Your machine → Consumer Control Plane (Management API)
   - Consumer EDC → Provider EDC (DSP protocol endpoint)
   - Provider Data Plane → Backend Storage (data retrieval)

4. **Discovery Service** (Saturn only):
   - BPN-to-connector mapping registered
   - Discovery Finder and BPN Discovery services operational

5. **Dataspace Onboarding and Verifiable Credentials**:
   - Both Provider and Consumer organizations must be onboarded in the Catena-X dataspace
   - Each organization requires valid Verifiable Credentials (VCs) that satisfy the policy constraints
   - **For BPN-based policies**: Organizations must have valid BPN credentials registered with their EDC connectors
   - **For Framework Agreement policies**: Organizations must possess VCs proving membership in the required frameworks (e.g., `Traceability:1.0`)
   - **For other ODRL constraints**: Ensure VCs cover all `leftOperand` values used in your access and usage policies
   - EDC connectors must be configured with credential validation (e.g., SSI integration for VC verification)
   - Without proper credentials, contract negotiations will be rejected even if the catalog is visible

> **Important**: TCK tests assume all credential prerequisites are met. If tests fail during contract negotiation (stuck in `REQUESTING` or `TERMINATED` state), verify that both parties have valid credentials for the policies being tested.

### Step 1: Configure the Environment

**Option A — Edit the default config (local umbrella):**

```bash
# Open the shared YAML config (one file for all 6 scripts)
vim tck/connector/tck-config.yaml
```

**Option B — Fill in the INT template:**

```bash
# Copy and populate the INT template
cp tck/connector/tck_int_config.yaml tck/connector/my_config.yaml
vim tck/connector/my_config.yaml
# Replace every <PLACEHOLDER> token with a real value
```

**Option C — One-off overrides via CLI flags** (no file editing needed):

```bash
# Override individual fields directly on the command line
python tck_e2e_saturn_0-11-X_simple.py \
  --provider-url https://my-new-provider.example.com \
  --provider-api-key MY_KEY
```

### Step 2: Run the Tests

#### Run a single test

```bash
cd tck/connector

# Saturn — BPNL discovery (simple / detailed)
python tck_e2e_saturn_0-11-X_simple.py
python tck_e2e_saturn_0-11-X_detailed.py

# Saturn — DID discovery
python tck_e2e_saturn_0-11-X_simple_did.py
python tck_e2e_saturn_0-11-X_detailed_did.py

# Jupiter (legacy protocol)
python tck_e2e_jupiter_0-10-X_simple.py
python tck_e2e_jupiter_0-10-X_detailed.py
```

#### Run with a custom YAML config

```bash
# Use the INT environment template (fill in placeholders first)
python tck_e2e_saturn_0-11-X_simple.py --config my_config.yaml

# Use a section with a non-default name
python tck_e2e_saturn_0-11-X_simple.py --config my_config.yaml --config-section my_saturn
```

#### Run all 6 tests in parallel with a live dashboard

```bash
# Uses the default tck-config.yaml
./run_all_tests.sh

# Uses a custom YAML config for all 6 tests
./run_all_tests.sh --config /absolute/path/to/my_config.yaml

# Skip cleanup across all tests
./run_all_tests.sh --no-cleanup

# Combine options
./run_all_tests.sh --config my_config.yaml --no-cleanup --no-debug
```

> The shell script launches all 6 tests in parallel, streams live status in a real-time table, and writes per-test logs to
> `logs/run_all_tests/<date>/<run-id>/`.  All command-line arguments are forwarded verbatim to every test script.

#### Common single-test options

```bash
# Disable debug logging for cleaner output
python tck_e2e_saturn_0-11-X_detailed.py --no-debug

# Keep provider resources after test (useful for manual inspection)
python tck_e2e_saturn_0-11-X_detailed.py --no-cleanup

# Combine
python tck_e2e_saturn_0-11-X_detailed.py --no-debug --no-cleanup
```

### Command-Line Options

All 6 TCK test scripts and `run_all_tests.sh` share the same CLI interface.

#### Config file options

| Flag | Argument | Description |
|------|----------|-------------|
| `--config` | `PATH` | Load all connectivity and policy values from `PATH` instead of the default `tck-config.yaml`. Supports absolute and relative paths. |
| `--config-section` | `SECTION` | Section name to read from the YAML file (e.g. `jupiter`, `saturn`). Each script has a built-in default; use this flag only when your YAML uses a different section name. |

```bash
# Run against INT environment using the provided template
python tck_e2e_saturn_0-11-X_simple.py --config tck_int_config.yaml

# Use a custom section name inside your YAML
python tck_e2e_saturn_0-11-X_simple.py \
  --config my_env.yaml \
  --config-section saturn_int
```

#### Individual field overrides

These flags override individual values **after** the YAML has been loaded and are applied to every test when passed to `run_all_tests.sh`:

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
| `--provider-dsp-url-did URL` | Provider DSP URL for DID-mode scripts; overrides `--provider-dsp-url` when `discovery_mode=did` |
| `--provider-did DID` | Provider DID (DID scripts only) |
| `--consumer-did DID` | Consumer DID (DID scripts only) |

```bash
# Quick ad-hoc override without editing any file:
python tck_e2e_saturn_0-11-X_simple.py \
  --provider-url https://my-new-provider.example.com \
  --provider-api-key NEW_KEY
```

#### Execution options

**`--no-debug`**: Disable DEBUG-level logging (**debug enabled by default**)

- By default, all TCK tests run with DEBUG-level logging enabled
- This provides verbose logging for all HTTP requests and responses
- Shows detailed SDK internal operations
- To disable verbose logging and see only INFO-level messages, use `--no-debug`
- Example: `python tck_e2e_saturn_0-11-X_simple.py --no-debug`

**`--no-cleanup`**: Skip resource cleanup after test (**cleanup enabled by default**)

- By default, all TCK tests automatically clean up resources after completion
- Cleanup includes:
  - All EDC provider resources (Contract Definitions, Assets, Policies)
  - Backend test data via HTTP DELETE request
  - Resources deleted in reverse order of creation to maintain referential integrity
  - Cleanup executes in the `finally` block, ensuring it runs even if the test fails
- **Use `--no-cleanup` when**:
  - Debugging failed tests (resources should remain for investigation)
  - Inspecting created resources manually in EDC Management API
  - Running tests in production-like environments where cleanup is handled externally
  - Performing compliance audits that require resource persistence
- **Keep default cleanup when**:
  - Running repeated tests to avoid resource ID conflicts
  - Testing in CI/CD pipelines
  - Development/testing environments with limited cleanup automation
- Example: `python tck_e2e_jupiter_0-10-X_detailed.py --no-cleanup`

> **Note**: When cleanup is enabled (default), the test logs all deletion operations. Successful deletions show `✓ Deleted [ResourceType]: [ResourceID]`. Failed deletions are logged as errors but do not cause the test to fail.

### Step 3: Review Test Results

Test results are logged to timestamped files and console:

```bash
# Log file naming convention:
saturn_e2e_run_2026-02-24_140847_PASS.log
jupiter_simple_e2e_run_2026-02-24_140741_FAIL.log

# View recent test logs
ls -lt *_e2e_run_*.log | head

# Inspect a specific test run
less saturn_e2e_run_2026-02-24_140847_PASS.log

# Search for errors in failed tests
grep -i "error\|exception\|fail" jupiter_e2e_run_*_FAIL.log
```

## Log Output Format

TCK tests produce comprehensive structured logs:

### Successful Run Example

```log
2026-02-24 14:08:47,294 INFO [saturn_e2e] Logging to file: saturn_e2e_run_2026-02-24_140847.log
2026-02-24 14:08:47,425 INFO [saturn_e2e] ✓ Access Policy created: access-policy-bpn-1771938527
2026-02-24 14:08:47,520 INFO [saturn_e2e] ✓ Usage Policy created: usage-policy-framework-1771938527
2026-02-24 14:08:47,559 INFO [saturn_e2e] ✓ Asset created: vehicle-production-data-1771938527
2026-02-24 14:08:47,583 INFO [saturn_e2e] ✓ Contract Definition created: contract-def-1771938527

2026-02-24 14:08:51,583 INFO [saturn_e2e] [CATALOG RESPONSE]:
{
  "@id": "5e19371d-09dd-4616-b442-1f4ee888b052",
  "@type": "Catalog",
  "dataset": [{ ... }]
}

2026-02-24 14:08:55,691 INFO [saturn_e2e] ✓ Contract Agreement finalized: 056c594b-e344-41a0-8cc8-0737592e020b
2026-02-24 14:09:00,064 INFO [saturn_e2e] ✓ EDR received!

╔══════════════════════════════════════════════════════════════════════════════╗
║                              E2E TEST RUN SUMMARY                            ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  STEP                                          RESULT      TIME              ║
║  ──────────────────────────────────────────────────────────────────────────  ║
║  ✓ Phase 0 · Upload sample data to backend       PASS      0.1s              ║
║  ✓ Phase 1 · Provider data provision             PASS      0.2s              ║
║  ✓ Phase 2 · Consumer data consumption           PASS      9.5s              ║
║  ✓ Phase 3 · Access data with EDR                PASS      0.4s              ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  RESULT: PASS  |  4 passed  0 failed  0 skipped  |  Total: 13.2s             ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

### Structured Logging Markers

TCK tests log all HTTP requests and responses with structured markers:

- `[UPLOAD REQUEST]` / `[UPLOAD RESPONSE]`: Backend data upload
- `[CATALOG RESPONSE]`: Provider catalog with datasets and offers
- `[NEGOTIATION REQUEST]` / `[NEGOTIATION RESPONSE]`: Contract negotiation initiation
- `[NEGOTIATION STATE RESPONSE]`: Negotiation state polling
- `[TRANSFER REQUEST]` / `[TRANSFER RESPONSE]`: Transfer process initiation
- `[EDR RESPONSE]`: Endpoint Data Reference (token + endpoint)
- `[DATA RESPONSE]`: Final data payload retrieved from backend

## Interpreting Test Results

### PASS Criteria

A test is marked **PASS** when all phases complete successfully:

- ✅ Phase 0: Sample data uploaded to backend (HTTP 200)
- ✅ Phase 1: All provider resources created (policies, asset, contract definition)
- ✅ Phase 2: Consumer successfully negotiates and obtains EDR
- ✅ Phase 3: Data retrieved using EDR matches uploaded payload

### FAIL Indicators

Common failure points:

**Phase 0 Failures** (Backend Upload):
```
HTTPError: 401 Unauthorized
→ Check backend API key if authentication is required

HTTPError: 404 Not Found
→ Verify backend API base URL is correct
```

**Phase 1 Failures** (Provider Provision):
```
HTTPError: 401 Unauthorized
→ Verify Provider API key is correct

HTTPError: 409 Conflict
→ Resource ID already exists (change timestamp seed or clean up)
```

**Phase 2 Failures** (Consumer Consumption):
```
Asset not found in catalog
→ Wait longer after creating contract definition (try 5+ seconds)
→ Verify Consumer BPN is in Provider's access policy
→ Check catalog filtering (asset ID, DCT type) is correct

Contract negotiation timeout (state stuck in REQUESTING)
→ Verify Consumer can reach Provider DSP endpoint
→ Check Provider logs for negotiation errors
→ Verify ODRL context URLs match EDC version
→ Verify Consumer has valid Verifiable Credentials for the policy constraints
→ Check that both parties are properly onboarded in the dataspace

Contract negotiation TERMINATED by provider
→ Consumer lacks required Verifiable Credentials (e.g., BPN credential, Framework Agreement membership)
→ Policy constraints not satisfied (check VC claims match policy leftOperand values)
→ SSI/credential verification failed on Provider side
→ Check Provider EDC logs for credential validation errors

EDR not available after transfer (state stuck in REQUESTED)
→ Check Provider Data Plane is running
→ Verify backend URL is reachable from Provider Data Plane
→ Check backend authentication if required
```

**Phase 3 Failures** (Data Access):
```
HTTPError: 401 Unauthorized
→ EDR token expired (re-run from Phase 2)
→ Token format incorrect (check "authorization" field in EDR)

HTTPError: 403 Forbidden
→ Token validation failed on Provider side
→ Check Provider Data Plane token validation settings

HTTPError: 502 Bad Gateway
→ Provider Data Plane cannot reach backend
→ Check backend URL and authentication configuration
```

## Validation Checklist

Use this checklist to debug TCK failures:

### Provider Configuration
- [ ] Management API accessible from test machine
- [ ] API key valid and has create permissions
- [ ] BPN format matches Discovery Service registration
- [ ] DSP URL does NOT include protocol version suffix

### Consumer Configuration
- [ ] Management API accessible from test machine
- [ ] API key valid and has create permissions
- [ ] BPN registered in Discovery Service (Saturn only)
- [ ] Can reach Provider DSP endpoint over network

### Backend Configuration
- [ ] Storage API accessible from test machine
- [ ] Backend API key valid if authentication is required
- [ ] Backend accepts requests from Provider Data Plane

### Network Connectivity
- [ ] Test machine → Provider Control Plane (HTTPS)
- [ ] Test machine → Consumer Control Plane (HTTPS)
- [ ] Consumer EDC → Provider DSP endpoint (HTTPS)
- [ ] Provider Data Plane → Backend Storage (HTTPS)

### Dataspace Onboarding & Credentials
- [ ] Provider organization onboarded in Catena-X dataspace
- [ ] Consumer organization onboarded in Catena-X dataspace
- [ ] Provider has valid BPN Verifiable Credential
- [ ] Consumer has valid BPN Verifiable Credential
- [ ] Consumer has required Framework Agreement VCs (e.g., Traceability:1.0)
- [ ] All VCs contain claims matching policy constraints (leftOperand values)
- [ ] EDC connectors configured with SSI/credential validation
- [ ] Credential issuers are trusted by both parties

### Protocol Compatibility
- [ ] EDC versions match protocol (Jupiter: 0.8.x–0.10.x, Saturn: 0.11.x+)
- [ ] ODRL context URLs match EDC version
- [ ] DSP protocol string matches (Jupiter: no version suffix, Saturn: `:2025-1`)

## Advanced Usage

### Custom Test Data

Modify the `SAMPLE_ASPECT_MODEL` in the test script to use your own data:

```python
SAMPLE_ASPECT_MODEL = {
    "yourModel": "yourData",
    "customField": 12345,
    # ... your JSON payload
}
```

### Custom Policies

The TCK demonstrates common policy patterns. To test custom policies:

```python
# In provision_data_on_provider() function:
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

### Parallel Test Execution

The easiest way to run all 6 tests in parallel is the bundled shell script:

```bash
cd tck/connector

# Run all 6 tests — default config
./run_all_tests.sh

# Run all 6 tests — INT environment
./run_all_tests.sh --config tck_int_config.yaml

# Skip cleanup for all tests
./run_all_tests.sh --no-cleanup
```

The script produces a **live real-time dashboard** in the terminal, updating each test's status as it progresses through phases.  Per-test logs and a combined summary are written to:

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

To run a subset manually in parallel:

```bash
# Saturn BPNL + DID in parallel
python tck_e2e_saturn_0-11-X_detailed.py &
python tck_e2e_saturn_0-11-X_detailed_did.py &
wait

# Check results
grep "RESULT:" saturn_*_PASS.log saturn_*_FAIL.log
```

### CI/CD Integration

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
      - name: Run Saturn TCK
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

## Protocol Differences

### Jupiter vs. Saturn

| Aspect | Jupiter (0.8.x–0.10.x) | Saturn (0.11.x+) |
|--------|------------------------|------------------|
| **DSP Protocol** | `dataspace-protocol-http` | `dataspace-protocol-http:2025-1` |
| **ODRL Context** | `https://w3id.org/tractusx/auth/v1.0.0`<br>`http://www.w3.org/ns/odrl.jsonld` | `https://w3id.org/catenax/2025/9/policy/odrl.jsonld`<br>`https://w3id.org/catenax/2025/9/policy/context.jsonld` |
| **Catalog Keys** | `dcat:dataset`, `odrl:hasPolicy` (prefixed) | `dataset`, `hasPolicy` (unprefixed, or both) |
| **BPN Usage** | Direct BPNL as `counter_party_id` | DID via Discovery Service |
| **Discovery** | Not required (BPNL → DSP URL mapping manual) | Required (BPNL → DID → DSP URL) |

### Selecting the Right Protocol

- **Use Jupiter TCK** if testing EDC v0.8.x–0.10.x deployments
- **Use Saturn TCK** if testing EDC v0.11.x+ deployments
- **Run both** to ensure backward compatibility during migration

## Troubleshooting Common Issues

### SSL Certificate Verification Errors

```python
ssl.SSLCertVerificationError: certificate verify failed
```

**Solution**: Tests include `verify=False` for self-signed certificates in test environments. For production:
```python
# Pass custom CA bundle
consumer_service.get_catalog_by_asset_id_with_bpnl(..., verify="/path/to/ca-bundle.crt")
```

### JSON-LD Context Mismatches

```
KeyError: 'dcat:dataset'  # or  KeyError: 'dataset'
```

**Solution**: TCK handles both prefixed and unprefixed keys. If you encounter this, check your EDC version matches the protocol:
- Jupiter: Expects prefixed keys (`dcat:dataset`, `odrl:hasPolicy`)
- Saturn: May use unprefixed or prefixed keys (SDK handles both)

### Transfer Process Stuck in REQUESTED

```
Transfer state: REQUESTED (polling timeout)
```

**Solution**:
1. Check Provider Data Plane logs for backend connection errors
2. Verify backend API key is valid if authentication is required
3. Test backend URL accessibility from Data Plane network:
   ```bash
   curl -v https://backend.example.com/api/data
   ```

### Discovery Service Not Found (Saturn)

```
HTTPError: 404 Not Found (Discovery Finder)
```

**Solution**: Saturn requires BPN-to-connector mapping in Discovery Service:
1. Verify Discovery Finder URL is correct
2. Register Provider BPN in Discovery Service
3. Check BPN format (must match exactly, including prefix)

## Documentation References

- **Tractus-X EDC Documentation**: [Management API Walkthrough](https://github.com/eclipse-tractusx/tractusx-edc/tree/main/docs/usage/management-api-walkthrough)
- **SDK API Reference**: [Connector Services](../../docs/api-reference/dataspace-library/connector/)
- **Industry Core Hub**: [Reference Implementation](https://github.com/eclipse-tractusx/industry-core-hub)
- **DSP Specification**:
  - [Dataspace Protocol 2024-1 or 0.8](https://docs.internationaldataspaces.org/ids-knowledgebase/v/dataspace-protocol)
  - [Dataspace Protocol 2025-1](https://eclipse-dataspace-protocol-base.github.io/DataspaceProtocol/2025-1/)

## Support

For issues or questions:
- **Bug Reports**: [Open an issue](https://github.com/eclipse-tractusx/tractusx-sdk/issues)
- **SDK Documentation**: [Tractus-X SDK Docs](../../docs/)
- **Community**: Tractus-X Mailing List and Matrix channels

## NOTICE

This work is licensed under the [CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/legalcode).

- SPDX-License-Identifier: CC-BY-4.0
- SPDX-FileCopyrightText: 2026 Contributors to the Eclipse Foundation
- SPDX-FileCopyrightText: 2026 Catena-X Automotive Network e.V.
- Source URL: https://github.com/eclipse-tractusx/tractusx-sdk
