<!--

Eclipse Tractus-X - Software Development KIT

Copyright (c) 2025 LKS Next
Copyright (c) 2025 Mondragon Unibertsitatea
Copyright (c) 2025 Contributors to the Eclipse Foundation

See the NOTICE file(s) distributed with this work for additional
information regarding copyright ownership.

This work is made available under the terms of the
Creative Commons Attribution 4.0 International (CC-BY-4.0) license,
which is available at
https://creativecommons.org/licenses/by/4.0/legalcode.

SPDX-License-Identifier: CC-BY-4.0

-->
# Protocol Backward Compatibility Guide

The SDK supports two dataspace protocol generations — **Jupiter** (`"dataspace-protocol-http"`) and **Saturn** (`"dataspace-protocol-http:2025-1"`). They are **not wire-compatible**: an EDC running Jupiter cannot talk to one running Saturn without a protocol bridge. Code that targets both generations must branch on the `dataspace_version`.

This guide summarises every breaking difference and the exact code pattern to handle each one.

---

## Protocol Version at a Glance

| | Jupiter | Saturn |
|---|---------|--------|
| Target EDC | 0.8.x – 0.10.x | 0.11.x+ |
| `dataspace_version` string | `"jupiter"` | `"saturn"` |
| DSP protocol string | `"dataspace-protocol-http"` | `"dataspace-protocol-http:2025-1"` |
| BPNL discovery (`_with_bpnl` methods) | **Not available** | Built-in |
| DID discovery | **Not available** | Built-in |
| `connector_discovery` controller | **Not present** | Present |
| Policy JSON-LD context | Tractus-X v1.0.0 + W3C ODRL | Catena-X 2025-9 |
| Access policy left operand | `tx:BusinessPartnerNumber` | `BusinessPartnerNumber` |
| Negotiation `@context` | Tractus-X + W3C ODRL URLs | Catena-X 2025-9 URLs |

---

## Recommended Strategy for Backward Compatibility

!!! success "Best Practice: Use `_with_bpnl` Methods"
    **We strongly recommend using the `_with_bpnl` variants** (`get_catalog_by_dct_type_with_bpnl`, `do_get_with_bpnl`, `do_post_with_bpnl`, `do_dsp_with_bpnl`) whenever possible. These methods provide **automatic backward compatibility** because:
    
    - They work seamlessly on **Saturn** (EDC 0.11.x+) with built-in BPNL discovery
    - They gracefully handle **Jupiter** (EDC 0.8–0.10.x) by requiring manual DSP URL configuration
    - Your code remains version-agnostic and future-proof
    
    **Example:**
    ```python
    # Works on both Jupiter and Saturn
    response = consumer.do_get_with_bpnl(
        bpnl="BPNL00000003AYRE",
        filter_expression=[...],
    )
    ```

!!! warning "Version-Specific Requirements"
    If you choose to use **version-specific methods** (without `_with_bpnl`), you must adhere to strict parameter requirements:
    
    **Jupiter (EDC 0.8–0.10.x):**
    
    - **MUST** use `counter_party_id` with a **BPN** value
    - **MUST** provide `counter_party_address` (DSP URL) explicitly
    - No automatic discovery available
    
    **Saturn (EDC 0.11.x+):**
    
    - **MUST** use `counter_party_id` with a **DID** value (W3C Decentralized Identifier)
    - `counter_party_address` is optional (resolved via DID document if omitted)
    - Supports both DID-based and BPNL-based discovery
    
    **Example (version-specific):**
    
    === "Jupiter (BPN required)"
    
        ```python
        # Jupiter: counter_party_id MUST be a BPN
        response = consumer.do_get(
            counter_party_id="BPNL00000003AYRE",  # BPN
            counter_party_address="http://provider.example.com/api/v1/dsp",
            filter_expression=[...],
            protocol="dataspace-protocol-http",
        )
        ```
    
    === "Saturn (DID required)"
    
        ```python
        # Saturn: counter_party_id MUST be a DID
        response = consumer.do_get(
            counter_party_id="did:web:provider.example.com",  # DID
            counter_party_address="http://provider.example.com/api/v1/dsp/2025-1",
            filter_expression=[...],
            protocol="dataspace-protocol-http:2025-1",
        )
        ```

---

## 1. Counter-Party Resolution — `_with_bpnl` Methods (Recommended)

!!! tip "Recommended Approach"
    **Always use `_with_bpnl` methods** for maximum backward compatibility. These methods work on both Jupiter and Saturn, eliminating the need for version-specific branching in your code.

Saturn introduces `_with_bpnl` variants of every catalog and DSP method. These methods automatically query the Connector Discovery Service to resolve the provider's DSP URL from a BPNL, so the caller only needs to know the partner's BPN.

**Available `_with_bpnl` methods:**

- `get_catalog_by_dct_type_with_bpnl()`
- `do_get_with_bpnl()`
- `do_post_with_bpnl()`
- `do_put_with_bpnl()`
- `do_patch_with_bpnl()`
- `do_delete_with_bpnl()`
- `do_dsp_with_bpnl()`

### Version-Specific Parameter Requirements

!!! warning "If using version-specific methods (not recommended)"
    When **not** using `_with_bpnl` methods, you must follow these strict rules:
    
    - **Jupiter:** `counter_party_id` **MUST** be a **BPN** (Business Partner Number)
    - **Saturn:** `counter_party_id` **MUST** be a **DID** (W3C Decentralized Identifier)

=== "Recommended: _with_bpnl (works everywhere)"

    ```python
    # Works on both Jupiter and Saturn — no version branching needed
    catalog = consumer.get_catalog_by_dct_type_with_bpnl(
        bpnl="BPNL00000003AYRE",
        dct_type="https://w3id.org/catenax/taxonomy#Submodel",
    )

    response = consumer.do_get_with_bpnl(
        bpnl="BPNL00000003AYRE",
        filter_expression=[consumer.get_filter_expression(
            key="https://w3id.org/edc/v0.0.1/ns/id",
            value="urn:uuid:my-asset",
        )],
    )
    ```

=== "Jupiter only (BPN required)"

    ```python
    # Jupiter: counter_party_id MUST be a BPN
    # No discovery — caller must know the DSP URL
    catalog = consumer.get_catalog_by_dct_type(
        counter_party_id="BPNL00000003AYRE",  # BPN required
        counter_party_address="http://provider.example.com/api/v1/dsp",
        dct_type="https://w3id.org/catenax/taxonomy#Submodel",
    )

    response = consumer.do_get(
        counter_party_id="BPNL00000003AYRE",  # BPN required
        counter_party_address="http://provider.example.com/api/v1/dsp",
        filter_expression=[...],
        protocol="dataspace-protocol-http",
    )
    ```

=== "Saturn only (DID required)"

    ```python
    # Saturn: counter_party_id MUST be a DID
    # DSP URL resolved automatically from DID document
    catalog = consumer.get_catalog_by_dct_type(
        counter_party_id="did:web:provider.example.com",  # DID required
        counter_party_address="http://provider.example.com/api/v1/dsp/2025-1",
        dct_type="https://w3id.org/catenax/taxonomy#Submodel",
    )

    response = consumer.do_get(
        counter_party_id="did:web:provider.example.com",  # DID required
        counter_party_address="http://provider.example.com/api/v1/dsp/2025-1",
        filter_expression=[...],
        protocol="dataspace-protocol-http:2025-1",
    )
    ```

---

## 2. Negotiation Protocol String

When calling `start_edr_negotiation()` directly (i.e. outside the high-level `do_get` / `do_dsp` helpers), you must pass the correct `protocol` string for the target EDC version. The helpers and runners handle this automatically.

=== "Jupiter"

    ```python
    negotiation_id = consumer.start_edr_negotiation(
        counter_party_id="BPNL00000003AYRE",
        counter_party_address="http://provider.example.com/api/v1/dsp",
        target="urn:uuid:my-asset",
        policy=offer,
        protocol="dataspace-protocol-http",          # Jupiter
    )
    ```

=== "Saturn"

    ```python
    negotiation_id = consumer.start_edr_negotiation(
        counter_party_id="BPNL00000003AYRE",
        counter_party_address="http://provider.example.com/api/v1/dsp/2025-1",
        target="urn:uuid:my-asset",
        policy=offer,
        protocol="dataspace-protocol-http:2025-1",   # Saturn
    )
    ```

=== "Version-agnostic"

    ```python
    PROTOCOL = {
        "jupiter": "dataspace-protocol-http",
        "saturn":  "dataspace-protocol-http:2025-1",
    }

    negotiation_id = consumer.start_edr_negotiation(
        counter_party_id=bpnl,
        counter_party_address=dsp_url,
        target=asset_id,
        policy=offer,
        protocol=PROTOCOL[consumer.dataspace_version],
    )
    ```

---

## 3. Policy JSON-LD Context

The negotiation `@context` and the policy `@context` changed between versions. Using the wrong context causes the EDC to reject the negotiation request with a 400 error.

### Negotiation context (`context` parameter of `start_edr_negotiation` / `get_edr_negotiation_request`)

=== "Jupiter"

    ```python
    NEGOTIATION_CONTEXT = [
        "https://w3id.org/tractusx/policy/v1.0.0",
        "http://www.w3.org/ns/odrl.jsonld",
        {"@vocab": "https://w3id.org/edc/v0.0.1/ns/"},
    ]
    ```

=== "Saturn"

    ```python
    NEGOTIATION_CONTEXT = [
        "https://w3id.org/catenax/2025/9/policy/odrl.jsonld",
        "https://w3id.org/catenax/2025/9/policy/context.jsonld",
        {"@vocab": "https://w3id.org/edc/v0.0.1/ns/"},
    ]
    ```

=== "Version-agnostic"

    ```python
    NEGOTIATION_CONTEXT = {
        "jupiter": [
            "https://w3id.org/tractusx/policy/v1.0.0",
            "http://www.w3.org/ns/odrl.jsonld",
            {"@vocab": "https://w3id.org/edc/v0.0.1/ns/"},
        ],
        "saturn": [
            "https://w3id.org/catenax/2025/9/policy/odrl.jsonld",
            "https://w3id.org/catenax/2025/9/policy/context.jsonld",
            {"@vocab": "https://w3id.org/edc/v0.0.1/ns/"},
        ],
    }

    negotiation_id = consumer.start_edr_negotiation(
        ...
        context=NEGOTIATION_CONTEXT[consumer.dataspace_version],
    )
    ```

---

## 4. Access Policy Permissions — Left Operand

The BPNL constraint left operand changed between versions. Using the wrong operand causes the EDC to create the policy successfully but fail to evaluate it at negotiation time.

=== "Jupiter"

    ```python
    # Jupiter uses the Tractus-X namespace prefix: tx:BusinessPartnerNumber
    access_policy_permissions = [{
        "action": "use",
        "constraint": {
            "leftOperand": "tx:BusinessPartnerNumber",  # Jupiter
            "operator": "eq",
            "rightOperand": "BPNL00000003AZQP",         # consumer BPN
        },
    }]
    # Policy @context must include the tx: namespace
    policy_context = [
        "https://w3id.org/tractusx/policy/v1.0.0",
        "http://www.w3.org/ns/odrl.jsonld",
        {
            "tx": "https://w3id.org/tractusx/v0.0.1/ns/",
            "@vocab": "https://w3id.org/edc/v0.0.1/ns/",
        },
    ]
    ```

=== "Saturn"

    ```python
    # Saturn uses the bare operand — no namespace prefix
    access_policy_permissions = [{
        "action": "access",
        "constraint": {
            "leftOperand": "BusinessPartnerNumber",     # Saturn
            "operator": "isAnyOf",
            "rightOperand": "BPNL00000003AZQP",
        },
    }]
    # Policy @context uses Catena-X 2025-9 URLs (context is often implicit)
    policy_context = [
        "https://w3id.org/catenax/2025/9/policy/odrl.jsonld",
        "https://w3id.org/catenax/2025/9/policy/context.jsonld",
        {"@vocab": "https://w3id.org/edc/v0.0.1/ns/"},
    ]
    ```

=== "Version-agnostic"

    ```python
    def build_access_policy(version: str, consumer_bpn: str) -> dict:
        if version == "saturn":
            return {
                "permissions": [{
                    "action": "access",
                    "constraint": {
                        "leftOperand": "BusinessPartnerNumber",
                        "operator": "isAnyOf",
                        "rightOperand": consumer_bpn,
                    },
                }],
                "context": None,   # Saturn: let provider.create_policy use its default
            }
        else:
            return {
                "permissions": [{
                    "action": "use",
                    "constraint": {
                        "leftOperand": "tx:BusinessPartnerNumber",
                        "operator": "eq",
                        "rightOperand": consumer_bpn,
                    },
                }],
                "context": [
                    "https://w3id.org/tractusx/policy/v1.0.0",
                    "http://www.w3.org/ns/odrl.jsonld",
                    {
                        "tx": "https://w3id.org/tractusx/v0.0.1/ns/",
                        "@vocab": "https://w3id.org/edc/v0.0.1/ns/",
                    },
                ],
            }
    ```

---

## 5. High-Level `do_get` / `do_dsp` Flow — Recommended Pattern

!!! success "Recommended: Use `_with_bpnl` for maximum compatibility"
    The `_with_bpnl` methods eliminate version branching and work seamlessly across both Jupiter and Saturn.

### Recommended Approach (Version-Agnostic with `_with_bpnl`)

```python
from tractusx_sdk.dataspace.services.connector import ServiceFactory

def access_data(
    version: str,
    consumer_url: str,
    consumer_api_key: str,
    provider_bpn: str,
    asset_id: str,
):
    consumer = ServiceFactory.get_connector_consumer_service(
        dataspace_version=version,
        base_url=consumer_url,
        dma_path="/management",
        headers={"X-Api-Key": consumer_api_key, "Content-Type": "application/json"},
    )

    filter_expression = [
        consumer.get_filter_expression(
            key="https://w3id.org/edc/v0.0.1/ns/id",
            value=asset_id,
        )
    ]

    # Works on both Jupiter and Saturn - no version branching needed!
    return consumer.do_get_with_bpnl(
        bpnl=provider_bpn,
        filter_expression=filter_expression,
    )
```

### Alternative Approach (Manual Version Branching)

If you cannot use `_with_bpnl` methods, you must implement version-specific branching and parameter handling:

```python
from tractusx_sdk.dataspace.services.connector import ServiceFactory

def access_data(
    version: str,
    consumer_url: str,
    consumer_api_key: str,
    provider_bpn: str,
    provider_dsp_url: str,   # required for Jupiter; optional for Saturn
    asset_id: str,
):
    PROTOCOL = {
        "jupiter": "dataspace-protocol-http",
        "saturn":  "dataspace-protocol-http:2025-1",
    }

    consumer = ServiceFactory.get_connector_consumer_service(
        dataspace_version=version,
        base_url=consumer_url,
        dma_path="/management",
        headers={"X-Api-Key": consumer_api_key, "Content-Type": "application/json"},
    )

    filter_expression = [
        consumer.get_filter_expression(
            key="https://w3id.org/edc/v0.0.1/ns/id",
            value=asset_id,
        )
    ]

    if version == "saturn":
        # Saturn: counter_party_id MUST be a DID
        return consumer.do_get(
            counter_party_id="did:web:provider.example.com",  # DID required
            counter_party_address=provider_dsp_url,
            filter_expression=filter_expression,
            protocol=PROTOCOL[version],
        )
    else:
        # Jupiter: counter_party_id MUST be a BPN
        return consumer.do_get(
            counter_party_id=provider_bpn,  # BPN required
            counter_party_address=provider_dsp_url,
            filter_expression=filter_expression,
            protocol=PROTOCOL[version],
        )
```

---

## Summary Checklist — Migrating Jupiter → Saturn

When upgrading a connector from Jupiter to Saturn, work through this checklist:

- [ ] **Recommended:** Migrate to `_with_bpnl` methods for all catalog and data access operations
- [ ] Change `dataspace_version` from `"jupiter"` to `"saturn"` in `ServiceFactory` calls
- [ ] If using version-specific methods (not `_with_bpnl`): Update `counter_party_id` from BPN to DID format
- [ ] Update negotiation `context` from Tractus-X v1.0.0 + W3C ODRL to Catena-X 2025-9 URLs
- [ ] Update access policy `leftOperand` from `tx:BusinessPartnerNumber` → `BusinessPartnerNumber`
- [ ] Update access policy `action` from `"use"` → `"access"` (Saturn access policies use `"access"`)
- [ ] Update the DSP `protocol` string from `"dataspace-protocol-http"` → `"dataspace-protocol-http:2025-1"`
- [ ] Update the provider DSP URL if it has a version suffix (e.g. `/api/v1/dsp/2025-1` instead of `/api/v1/dsp`)
- [ ] Remove explicit `tx:` namespace entries from policy `@context` (no longer needed in Saturn)
- [ ] Verify that usage policy constraints (Membership, FrameworkAgreement, UsagePurpose) match the Catena-X 2025-9 operand vocabulary

!!! tip "Use the TCK to validate"
    Run the [Connector TCK](../tck/connector/index.md) against your connector after each migration step. The simple and detailed Saturn scripts confirm the full negotiate → transfer → data-access flow end-to-end.

!!! info "DID-based discovery"
    Saturn also supports DID-based discovery (no BPNL lookup, uses a W3C DID document to resolve the counterparty DSP endpoint). See the [Saturn API Reference](../api-reference/dataspace-library/connector/services.md#saturn-protocol-module-dsp-2025-1) for `discover_connector_protocol()` and `get_discovery_info()`.

---

## NOTICE

This work is licensed under the [CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/legalcode).

- SPDX-License-Identifier: CC-BY-4.0
- SPDX-FileCopyrightText: 2025, 2026 Contributors to the Eclipse Foundation
- SPDX-FileCopyrightText: 2025, 2026 Catena-X Automotive Network e.V.
- SPDX-FileCopyrightText: 2025, 2026 LKS Next
- SPDX-FileCopyrightText: 2025, 2026 Mondragon Unibertsitatea
- Source URL: [https://github.com/eclipse-tractusx/tractusx-sdk](https://github.com/eclipse-tractusx/tractusx-sdk)
