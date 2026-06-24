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

# Configuration

All six TCK scripts share a single YAML file — **`tck-config.yaml`** — as their source of truth. Edit only this file when switching environments; the scripts read it automatically at startup.

## Config File Locations

```
tck/connector/
├── tck-config.yaml          ← default (local Tractus-X Umbrella / tx.test)
├── tck_int_config.yaml      ← INT environment template (fill in <PLACEHOLDER> tokens)
└── my_custom_config.yaml    ← any additional environment you create
```

## YAML Sections

Each file contains one or more **named sections**. Every test script knows its own default section, so no extra flag is needed when using the default file.

| Section | Used by scripts | Protocol |
|---------|-----------------|----------|
| `jupiter` | `tck_e2e_jupiter_0-10-X_*.py` | `dataspace-protocol-http` |
| `saturn` | `tck_e2e_saturn_0-11-X_*.py` (all four) | `dataspace-protocol-http:2025-1` |

## Section Layout

```yaml
<section_name>:
  provider:
    base_url:    "https://your-provider-edc/management"
    dma_path:    "/management"            # default: /management
    api_key:     "<key>"
    bpn:         "BPNL..."
    dsp_url:     "https://your-provider-edc/api/v1/dsp"          # BPNL scripts
    dsp_url_did: "https://your-provider-edc/api/v1/dsp/2025-1"  # DID scripts only (saturn)
    did:         "did:web:..."            # saturn DID-mode only; ~ otherwise

  consumer:
    base_url:    "https://your-consumer-edc/management"
    dma_path:    "/management"
    api_key:     "<key>"
    bpn:         "BPNL..."
    did:         "did:web:..."            # saturn DID-mode only; ~ otherwise

  backend:
    base_url:    "https://your-backend/api/data"   # NO trailing UUID
    api_key:     "<key>"                            # ~ if no auth needed

  policies:
    protocol:            "dataspace-protocol-http"    # or :2025-1
    negotiation_context: [ ... ]                      # ODRL @context array
    access_policy:       { permissions: [...] }       # BPN / Membership rule
    access_policy_did:   { context: [...], permissions: [...] }  # saturn DID only
    usage_policy:        { permissions: [...] }       # framework / purpose rule
```

## Field Reference

### Provider / Consumer fields

| Field | Required | Description |
|-------|----------|-------------|
| `base_url` | Yes | Base URL of the EDC Management API (**without** `/management` suffix) |
| `dma_path` | No | Management API path (default: `/management`) |
| `api_key` | Yes | Management API authentication key |
| `bpn` | Yes | Business Partner Number (`BPNL…`) |
| `dsp_url` | Provider only | DSP protocol endpoint — used by BPNL-discovery scripts |
| `dsp_url_did` | Provider, Saturn only | Alternative DSP URL used by DID-discovery scripts; falls back to `dsp_url` if absent |
| `did` | Saturn DID only | Decentralized Identifier (DID) of the connector |

### Backend fields

| Field | Required | Description |
|-------|----------|-------------|
| `base_url` | Yes | Backend storage base URL — **do not** append a UUID; the test appends `/urn:uuid:<uuid4>` at runtime |
| `api_key` | No | Backend authentication key; set to `~` if not needed |

### Policy fields

| Field | Description |
|-------|-------------|
| `protocol` | DSP protocol string passed to contract negotiations |
| `negotiation_context` | ODRL `@context` array used in negotiation requests |
| `access_policy` | BPN-based (BPNL discovery) access policy permissions |
| `access_policy_did` | Membership-based (DID discovery) access policy — Saturn only |
| `usage_policy` | Framework Agreement / usage purpose policy |

!!! tip
    `access_policy.permissions[].constraint.rightOperand` for BPN-based policies is automatically set to the consumer BPN at runtime. Leave it as `~` (YAML null) in the config file.

## Example: Jupiter (Local Umbrella)

```yaml
jupiter:
  provider:
    base_url: "http://dataprovider-controlplane.tx.test"
    dma_path: "/management"
    api_key: "TEST2"
    bpn: "BPNL00000003AYRE"
    dsp_url: "http://dataprovider-controlplane.tx.test/api/v1/dsp"
    did: ~
  consumer:
    base_url: "http://dataconsumer-1-controlplane.tx.test"
    dma_path: "/management"
    api_key: "TEST1"
    bpn: "BPNL00000003AZQP"
    did: ~
  backend:
    base_url: "http://dataprovider-submodelserver.tx.test"
    api_key: ~
  policies:
    protocol: "dataspace-protocol-http"
    negotiation_context:
      - "https://w3id.org/tractusx/policy/v1.0.0"
      - "http://www.w3.org/ns/odrl.jsonld"
      - "@vocab": "https://w3id.org/edc/v0.0.1/ns/"
    access_policy:
      profile: "cx-policy:profile2405"
      context:
        - "https://w3id.org/tractusx/policy/v1.0.0"
        - "http://www.w3.org/ns/odrl.jsonld"
        - tx: "https://w3id.org/tractusx/v0.0.1/ns/"
          "@vocab": "https://w3id.org/edc/v0.0.1/ns/"
      permissions:
        - action: "use"
          constraint:
            leftOperand: "tx:BusinessPartnerNumber"
            operator: "eq"
            rightOperand: ~   # auto-set to consumer BPN at runtime
    usage_policy:
      profile: "cx-policy:profile2405"
      context:
        - "https://w3id.org/tractusx/policy/v1.0.0"
        - "http://www.w3.org/ns/odrl.jsonld"
        - "@vocab": "https://w3id.org/edc/v0.0.1/ns/"
      permissions:
        - action: "use"
          constraint:
            and:
              - leftOperand: "Membership"
                operator: "eq"
                rightOperand: "active"
              - leftOperand: "FrameworkAgreement"
                operator: "eq"
                rightOperand: "DataExchangeGovernance:1.0"
              - leftOperand: "UsagePurpose"
                operator: "eq"
                rightOperand: "cx.core.industrycore:1"
```

## Example: Saturn BPNL + DID (Local Umbrella)

```yaml
saturn:
  provider:
    base_url: "http://dataprovider-controlplane.tx.test"
    dma_path: "/management"
    api_key: "TEST2"
    bpn: "BPNL00000003AYRE"
    dsp_url: "http://dataprovider-controlplane.tx.test/api/v1/dsp"
    dsp_url_did: "http://dataprovider-controlplane.tx.test/api/v1/dsp/2025-1"
    did: "did:web:portal-backend.tx.test:api:administration:staticdata:did:BPNL00000003AYRE"
  consumer:
    base_url: "http://dataconsumer-1-controlplane.tx.test"
    dma_path: "/management"
    api_key: "TEST1"
    bpn: "BPNL00000003AZQP"
    did: "did:web:portal-backend.tx.test:api:administration:staticdata:did:BPNL00000003AZQP"
  backend:
    base_url: "http://dataprovider-submodelserver.tx.test"
    api_key: ~
  policies:
    protocol: "dataspace-protocol-http:2025-1"
    negotiation_context:
      - "https://w3id.org/catenax/2025/9/policy/odrl.jsonld"
      - "https://w3id.org/catenax/2025/9/policy/context.jsonld"
      - "@vocab": "https://w3id.org/edc/v0.0.1/ns/"
    access_policy:               # BPNL discovery
      permissions:
        - action: "access"
          constraint:
            leftOperand: "BusinessPartnerNumber"
            operator: "isAnyOf"
            rightOperand: ~      # auto-set to consumer BPN at runtime
    access_policy_did:           # DID discovery
      context:
        - "https://w3id.org/catenax/2025/9/policy/odrl.jsonld"
        - "https://w3id.org/catenax/2025/9/policy/context.jsonld"
        - "@vocab": "https://w3id.org/edc/v0.0.1/ns/"
      permissions:
        - action: "access"
          constraint:
            leftOperand: "Membership"
            operator: "eq"
            rightOperand: "active"
    usage_policy:
      permissions:
        - action: "use"
          constraint:
            and:
              - leftOperand: "Membership"
                operator: "eq"
                rightOperand: "active"
              - leftOperand: "FrameworkAgreement"
                operator: "eq"
                rightOperand: "DataExchangeGovernance:1.0"
```

## Switching Environments

=== "Option A — Edit the default config"

    ```bash
    vim tck/connector/tck-config.yaml
    ```

=== "Option B — Fill in the INT template"

    ```bash
    cp tck/connector/tck_int_config.yaml tck/connector/my_config.yaml
    vim tck/connector/my_config.yaml
    # Replace every <PLACEHOLDER> token with a real value
    ```

=== "Option C — CLI overrides (no file editing)"

    ```bash
    python tck_e2e_saturn_0-11-X_simple.py \
      --provider-url https://my-provider.example.com \
      --provider-api-key MY_KEY
    ```

    See [Running Tests → Individual field overrides](running-tests.md#individual-field-overrides) for all available flags.

## NOTICE

This work is licensed under the [CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/legalcode).

- SPDX-License-Identifier: CC-BY-4.0
- SPDX-FileCopyrightText: 2025, 2026 Contributors to the Eclipse Foundation
- SPDX-FileCopyrightText: 2025, 2026 Catena-X Automotive Network e.V.
- SPDX-FileCopyrightText: 2025, 2026 LKS Next
- SPDX-FileCopyrightText: 2025, 2026 Mondragon Unibertsitatea
- Source URL: [https://github.com/eclipse-tractusx/tractusx-sdk](https://github.com/eclipse-tractusx/tractusx-sdk)
