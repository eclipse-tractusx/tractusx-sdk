# Tractus-X SDK - Test Compliance Kits (TCKs)

This directory contains Test Compliance Kits (TCKs) for validating end-to-end connector functionality across different Eclipse Tractus-X EDC versions and deployment scenarios.

## Overview

TCKs demonstrate the complete data exchange flow:
1. **Provider**: Provisions data (Asset + Policies + Contract Definition)
2. **Consumer**: Discovers, negotiates, transfers, and accesses data
3. **Backend**: Simple data storage for testing

## Available TCK Configurations

### Saturn Protocol (EDC v0.11.x)

Saturn represents the latest DSP 2025-1 protocol with Catena-X 2025-9 policy contexts.

| TCK File | Description | Protocol | Authentication |
|----------|-------------|----------|----------------|
| `tck_e2e_saturn_0-11-X_simple_did.py` | Simple one-call using `do_get()` | DSP 2025-1 | DID-based |
| `tck_e2e_saturn_0-11-X_detailed_did.py` | Detailed step-by-step flow | DSP 2025-1 | DID-based |
| `tck_e2e_umbrella_saturn_simple_did.py` | Umbrella Helm chart (simple) | DSP 2025-1 | DID-based |
| `tck_e2e_umbrella_saturn_detailed.py` | Umbrella Helm chart (detailed) | DSP 2025-1 | DID-based |

**Saturn Configuration:**
- **Protocol**: `dataspace-protocol-http:2025-1`
- **Policy Context**: 
  - `https://w3id.org/catenax/2025/9/policy/odrl.jsonld`
  - `https://w3id.org/catenax/2025/9/policy/context.jsonld`
- **EDC Version**: 0.11.x
- **Dataspace Version**: `"saturn"`

### Jupiter Protocol (EDC v0.8.x - 0.10.x)

Jupiter represents the legacy DSP protocol with Tractus-X v1.0.0 policy contexts.

| TCK File | Description | Protocol | Authentication |
|----------|-------------|----------|----------------|
| `tck_e2e_jupiter_0-10-X_simple.py` | Simple one-call using `do_get()` | Legacy DSP | BPNL-based |
| `tck_e2e_jupiter_0-10-X_detailed.py` | Detailed step-by-step flow | Legacy DSP | BPNL-based |

**Jupiter Configuration:**
- **Protocol**: `dataspace-protocol-http`
- **Policy Context**: 
  - `https://w3id.org/tractusx/policy/v1.0.0`
  - `http://www.w3.org/ns/odrl.jsonld`
- **EDC Version**: 0.8.x - 0.10.x
- **Dataspace Version**: `"jupiter"`

## Deployment Scenarios

### 1. Standalone EDC (Industry Core Hub)

**TCKs**: `tck_e2e_saturn_0-11-X_*.py`, `tck_e2e_jupiter_0-10-X_*.py`

Standalone EDC deployments with custom configurations. Typical for:
- Development environments
- Custom infrastructure setups
- Integration testing

**Example Endpoints:**
```python
PROVIDER_CONNECTOR_CONFIG = {
    "base_url": "https://saturn-edc-provider-ichub-control.int.catena-x.net",
    "dsp_url": "https://saturn-edc-provider-ichub-control.int.catena-x.net/api/v1/dsp",
    "api_key": "ACA176440A8BDD3954...",  # Custom API key
    "bpn": "BPNL0000000093Q7",
}
```

### 2. Tractus-X Umbrella Helm Chart

**TCKs**: `tck_e2e_umbrella_saturn_*.py`

Based on: [tractus-x-umbrella](https://github.com/eclipse-tractusx/tractus-x-umbrella)

Umbrella provides a complete Catena-X data space environment including:
- EDC connectors (`tx-data-provider`, `dataconsumerOne`)
- SSI DIM Wallet Stub for identity management
- Central IDP for authentication
- Digital Twin Registry and Submodel Server
- Pre-configured test data and service accounts

**Configuration**: `values-adopter-data-exchange.yaml` (enabled components)

**Example Endpoints:**
```python
PROVIDER_CONNECTOR_CONFIG = {
    "base_url": "http://dataprovider-controlplane.tx.test",
    "dsp_url": "http://dataprovider-controlplane.tx.test/api/v1/dsp",
    "api_key": "TEST2",  # From umbrella values.yaml
    "bpn": "BPNL00000003AYRE",
    "did": "did:web:ssi-dim-wallet-stub.tx.test:BPNL00000003AYRE",
}

CONSUMER_CONNECTOR_CONFIG = {
    "base_url": "http://dataconsumer-1-controlplane.tx.test",
    "api_key": "TEST1",
    "bpn": "BPNL00000003AZQP",
    "did": "did:web:ssi-dim-wallet-stub.tx.test:BPNL00000003AZQP",
}

BACKEND_CONFIG = {
    "base_url": "http://dataprovider-submodelserver.tx.test/urn:uuid:...",
}
```

**Umbrella Components:**

| Component | BPN | DID | Management Key | Purpose |
|-----------|-----|-----|----------------|---------|
| tx-data-provider | BPNL00000003AYRE | did:web:ssi-dim-wallet-stub.tx.test:BPNL00000003AYRE | TEST2 | Data Provider |
| dataconsumerOne | BPNL00000003AZQP | did:web:ssi-dim-wallet-stub.tx.test:BPNL00000003AZQP | TEST1 | Data Consumer |

## Authentication Methods

### DID-based (Saturn / Umbrella)

Uses Decentralized Identifiers (DIDs) for participant identification. No BPNL discovery service needed.

```python
# Direct DID connection without discovery
consumer_service.do_get(
    counter_party_id="did:web:ssi-dim-wallet-stub.tx.test:BPNL00000003AYRE",
    counter_party_address="http://dataprovider-controlplane.tx.test/api/v1/dsp",
    asset_id="my-asset-id",
)
```

### BPNL-based (Jupiter / Legacy)

Uses Business Partner Number Legal Entity (BPNL) for discovery via Discovery Services.

```python
# BPNL-based discovery (requires Discovery Finder and BPN Discovery services)
consumer_service.do_get(
    bpnl="BPNL0000000093Q7",  # Triggers discovery flow
    asset_id="my-asset-id",
)
```

## Usage

### Prerequisites

1. Install the Tractus-X SDK:
   ```bash
   poetry install
   ```

2. Configure your target environment:
   - Update connector URLs in the TCK file
   - Set API keys/credentials
   - Verify network connectivity

### Running a TCK

```bash
# Simple Saturn DID-based test
python tck/connector/tck_e2e_umbrella_saturn_simple_did.py

# Detailed step-by-step test
python tck/connector/tck_e2e_umbrella_saturn_detailed.py

# Jupiter legacy protocol test
python tck/connector/tck_e2e_jupiter_0-10-X_detailed.py
```

### Test Logs

Each TCK generates timestamped logs in `logs/<tck_name>/<date>/`:
- `<time>_<tck_name>_PASS.log` - Successful test run
- `<time>_<tck_name>_FAIL.log` - Failed test run

Logs include:
- Request/response details
- Policy configurations
- Contract negotiation steps
- EDR (Endpoint Data Reference) details
- Retrieved data

## Configuration Placeholders

Before running, replace PLACEHOLDER values in TCK files:

| Configuration | Description | Example |
|---------------|-------------|---------|
| `base_url` | EDC Control Plane URL | `http://dataprovider-controlplane.tx.test` |
| `api_key` | Management API authentication key | `TEST2` (umbrella) or custom |
| `bpn` | Business Partner Number | `BPNL00000003AYRE` |
| `did` | Decentralized Identifier | `did:web:ssi-dim-wallet-stub.tx.test:BPNL00000003AYRE` |
| `dsp_url` | DSP Protocol endpoint | `http://dataprovider-controlplane.tx.test/api/v1/dsp` |

## Policy Configuration

### Saturn Policies (2025-9)

```python
ACCESS_POLICY_CONFIG = {
    "context": [
        "https://w3id.org/catenax/2025/9/policy/odrl.jsonld",
        "https://w3id.org/catenax/2025/9/policy/context.jsonld",
        {"@vocab": "https://w3id.org/edc/v0.0.1/ns/"}
    ],
    "permissions": [{
        "action": "use",
        "constraint": {
            "leftOperand": "BusinessPartnerNumber",
            "operator": "eq",
            "rightOperand": "BPNL00000003AZQP"
        }
    }]
}
```

### Jupiter Policies (v1.0.0)

```python
ACCESS_POLICY_CONFIG = {
    "context": [
        "https://w3id.org/tractusx/policy/v1.0.0",
        "http://www.w3.org/ns/odrl.jsonld",
        {
            "tx": "https://w3id.org/tractusx/v0.0.1/ns/",
            "@vocab": "https://w3id.org/edc/v0.0.1/ns/"
        }
    ],
    "permissions": [{
        "action": "use",
        "constraint": {
            "leftOperand": "tx:BusinessPartnerNumber",
            "operator": "eq",
            "rightOperand": "BPNL00000003CRHK"
        }
    }],
    "profile": "cx-policy:profile2405"
}
```

## Troubleshooting

### Common Issues

1. **Connection Refused**
   - Verify connector URLs are accessible
   - Check network connectivity
   - Confirm SSL/TLS settings (`verify_ssl=False` for self-signed certs)

2. **Authentication Failures**
   - Verify API keys match connector configuration
   - Check management endpoint authentication settings
   - Confirm service account permissions (Umbrella deployments)

3. **Discovery Failures** (BPNL-based)
   - Verify Discovery Finder is accessible
   - Check BPN Discovery service registration
   - Confirm BPNL-to-connector-URL mapping exists

4. **Policy Validation Errors**
   - Verify policy context URLs match EDC version
   - Check constraint operators (Saturn vs Jupiter differences)
   - Confirm BPN values in policies match actual participants

5. **Transfer Process Timeout**
   - Increase timeout values in requests
   - Check dataplane connectivity
   - Verify backend service availability

### Debug Mode

Enable detailed logging:
```python
provider_service = ServiceFactory.get_connector_provider_service(
    ...,
    verbose=True,  # Enable verbose HTTP logging
    debug=True,    # Enable debug-level SDK logs
    logger=logger  # Use custom logger
)
```

## References

- [Eclipse Tractus-X EDC](https://github.com/eclipse-tractusx/tractusx-edc)
- [Tractus-X Umbrella](https://github.com/eclipse-tractusx/tractus-x-umbrella)
- [Catena-X Standards](https://catena-x.net/en/standard-library)
- [DSP Protocol Specification](https://docs.internationaldataspaces.org/ids-knowledgebase/dataspace-protocol)

## License

Copyright (c) 2026 Contributors to the Eclipse Foundation

Licensed under the Apache License, Version 2.0
