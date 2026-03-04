<!--

Eclipse Tractus-X - Software Development KIT

Copyright (c) 2025 LKS Next
Copyright (c) 2025 Contributors to the Eclipse Foundation

See the NOTICE file(s) distributed with this work for additional
information regarding copyright ownership.

This work is made available under the terms of the
Creative Commons Attribution 4.0 International (CC-BY-4.0) license,
which is available at
https://creativecommons.org/licenses/by/4.0/legalcode.

SPDX-License-Identifier: CC-BY-4.0

-->
# Connector Services

The Connector Services are a central part of the Tractus-X SDK's Dataspace Library, providing high-level abstractions for interacting with Eclipse Tractus-X Connector endpoints in a dataspace. These services enable both data consumers and providers to manage assets, contracts, policies, and data transfers in a standardized, versioned manner.

## Purpose

Connector Services encapsulate the complexity of dataspace protocols, offering a unified API for:

- **Provisioning and managing assets** on Eclipse Tractus-X connectors
- **Negotiating and managing contracts** between dataspace participants
- **Defining and enforcing policies** for data sharing
- **Initiating and monitoring data transfers** across the dataspace

They are designed to work with multiple dataspace versions (e.g., "jupiter", "saturn"), ensuring compatibility and flexibility for evolving dataspace standards.

## Key Components

- **Service Factory**: Dynamically creates connector service instances for supported dataspace versions.
- **BaseConnectorService**: Core abstraction for connector interactions, exposing contract, consumer, and provider interfaces.
- **Consumer/Provider Services**: Specialized classes for consuming and providing data, tailored to dataspace version and role.
- **Controllers & Adapters**: Manage API requests and low-level HTTP communication with EDC connectors.

## Provider Connector Example

This example demonstrates how to use the provider connector service to create and publish assets to the dataspace, making them available for discovery and sharing by other participants.

```python
from tractusx_sdk.dataspace.services.connector import ServiceFactory

# Provider: Create and publish an asset
provider_connector_service = ServiceFactory.get_connector_provider_service(
    dataspace_version="jupiter",
    base_url="https://my-connector-controlplane.url",
    dma_path="/management",
    headers={"X-Api-Key": "my-api-key", "Content-Type": "application/json"},
    verbose=True
)

provider_connector_service.create_asset(
    asset_id="my-asset-id",
    base_url="https://submodel-service.url/",
    dct_type="cx-taxo:SubmodelBundle",
    version="3.0",
    semantic_id="urn:samm:io.catenax.part_type_information:1.0.0#PartTypeInformation"
)
```

For dedicated consumer and combined usage patterns, see the examples below. For even more advanced scenarios, refer to the [SDK Structure and Components](../../../core-concepts/sdk-architecture/sdk-structure-and-components.md) and [Dataspace Connector Usage](../../../api-reference/dataspace-library/legacy/edc-sdk-usage.md).

## Consumer Connector Example

Use the consumer connector service to discover catalogs, negotiate contracts, and access data from other dataspace participants:

```python
from tractusx_sdk.dataspace.services.connector import ServiceFactory

consumer_connector_service = ServiceFactory.get_connector_consumer_service(
	dataspace_version="jupiter",
	base_url="https://partner-connector.url",
	dma_path="/management",
	headers={"X-Api-Key": "my-api-key", "Content-Type": "application/json"},
	verbose=True
)

# Discover available catalogs
catalog = consumer_connector_service.get_catalog(counter_party_id="BPNL00000003AYRE")

# Negotiate contract for asset access
contract = consumer_connector_service.contracts.negotiate(
	counter_party_id="BPNL00000003AYRE",
	asset_id="partner-asset-id",
	policies=[...]
)

# Transfer data
data = consumer_connector_service.transfer(
	contract_id=contract.id,
	asset_id="partner-asset-id"
)
```

## Combined Consumer/Provider Connector Example

Instantiate both consumer and provider logic for seamless integration in one service:

```python
from tractusx_sdk.dataspace.services.connector import ServiceFactory

connector_service = ServiceFactory.get_connector_service(
	dataspace_version="jupiter",
	base_url="https://my-connector-controlplane.url",
	dma_path="/management",
	headers={"X-Api-Key": "my-api-key", "Content-Type": "application/json"},
	verbose=True
)

# Provider: Create and publish an asset
connector_service.provider.assets.create(
	asset_id="industry-asset-id",
	base_url="https://industry-data.url/",
	dct_type="cx-taxo:IndustryAsset",
	version="1.0",
	semantic_id="urn:samm:io.catenax.industry_asset:1.0.0#IndustryAsset"
)

# Consumer: Discover and access data from a partner
catalog = connector_service.consumer.get_catalog(counter_party_id="BPNL00000003AYRE")
# Negotiate contract, retrieve data, etc.
```

## Supported Features

- Asset management (create, update, delete)
- Catalog discovery and querying
- Contract definition and negotiation

## Connector Service Controller Methods & Instantiation

| Service Type                | Controller Methods (Main)                                                                 | Required Attributes for Instantiation                                                                                   |
|-----------------------------|------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------------------------|
| Consumer Connector Service  | `get_catalog`, `get_edr`, `get_endpoint_with_token`, `get_filter_expression`, `contract_negotiations`, `transfer_processes` | `dataspace_version`, `base_url`, `dma_path`, `headers`, `connection_manager`, `verbose`, `logger`                     |
| Provider Connector Service  | `create_asset`, `create_contract`, `create_policy`, `assets`, `contract_definitions`, `policies`                          | `dataspace_version`, `base_url`, `dma_path`, `headers`, `verbose`, `logger`                                           |
| Combined Connector Service  | All consumer and provider methods via `.consumer` and `.provider`                        | `dataspace_version`, `base_url`, `dma_path`, `headers`, `consumer_service`, `provider_service`, `verbose`, `logger`   |

**Supported Versions:** `jupiter`, `saturn`

**Instantiation Example:**

Consumer:
`ServiceFactory.get_connector_consumer_service(dataspace_version, base_url, dma_path, headers, connection_manager, verbose, logger)`

Provider:
`ServiceFactory.get_connector_provider_service(dataspace_version, base_url, dma_path, headers, verbose, logger)`

Combined:
`ServiceFactory.get_connector_service(dataspace_version, base_url, dma_path, headers, connection_manager, verbose, logger)`

## Connector Service Methods Reference

| Method Name                | Required Attributes                | Description                                      |
|----------------------------|------------------------------------------------|--------------------------------------------------|
| `get_catalog`              | `counter_party_id`                             | Discover available catalogs from a counterparty  |
| `get_edr`                  | `transfer_process_id`                          | Retrieve endpoint data reference                 |
| `get_endpoint_with_token`  | `asset_id`, `contract_id`                      | Get endpoint with authentication token           |
| `get_filter_expression`    | `filter_params`                                | Build filter expression for catalog queries      |
| `contract_negotiations`    | `counter_party_id`, `asset_id`, `policies`     | List or manage contract negotiations             |
| `transfer_processes`       | `contract_id`, `asset_id`                      | List or manage data transfer processes           |
| `create_asset`             | `asset_id`, `base_url`, `dct_type`, `version`, `semantic_id` | Create and publish an asset                      |
| `create_contract`          | `contract_params`                              | Create a contract definition                     |
| `create_policy`            | `policy_params`                                | Create a policy for data sharing                 |
| `assets`                   | `asset_id`, `asset_data`                       | Manage assets (CRUD operations)                  |
| `contract_definitions`     | `contract_id`, `contract_data`                 | Manage contract definitions                      |
| `policies`                 | `policy_id`, `policy_data`                     | Manage policies                                  |
| `transfer`                 | `contract_id`, `asset_id`                      | Initiate data transfer                           |

## Connector Service Instantiation Attribute Reference

| Attribute           | Type                | Description                                                                                  |
|---------------------|---------------------|----------------------------------------------------------------------------------------------|
| `dataspace_version` | `str`               | Dataspace protocol version, e.g., `"jupiter"` or `"saturn"`                                 |
| `base_url`          | `str`               | Base URL of the EDC connector control plane                                                  |
| `dma_path`          | `str`               | Path for connector management API (e.g., `/management`)                                      |
| `headers`           | `dict` (optional)   | HTTP headers for authentication and content type                                             |
| `connection_manager`| `BaseConnectionManager` (optional, consumer/combined) | Manages connector connections and state                                 |
| `verbose`           | `bool` (optional)   | Enables verbose logging                                                                     |
| `logger`            | `logging.Logger` (optional) | Custom logger instance for SDK output                                         |

## Saturn Protocol Module (DSP 2025-1)

Saturn is the second-generation connector protocol implementation in the Tractus-X SDK, targeting EDC 0.11.x+ connectors and the `dataspace-protocol-http:2025-1` specification (Catena-X 2025 release). It is a full superset of the base connector service: every method available in Jupiter is also present in Saturn, and Saturn adds a set of BPNL- and DID-aware discovery helpers.

### Saturn vs Jupiter — Key Differences

| Aspect | Jupiter (`"jupiter"`) | Saturn (`"saturn"`) |
|--------|-----------------------|----------------------|
| EDC version | 0.8.x – 0.10.x | 0.11.x+ |
| DSP protocol string | `dataspace-protocol-http` | `dataspace-protocol-http:2025-1` |
| Negotiation JSON-LD context | Tractus-X v1.0.0 + W3C ODRL | Catena-X 2025-9 context URLs |
| BPNL discovery (`_with_bpnl` methods) | ✗ Not available | ✓ Built-in |
| DID-based discovery | ✗ Not available | ✓ Built-in |
| `connector_discovery` controller | ✗ | ✓ |
| `discover_connector_protocol()` | ✗ | ✓ |
| Parallel BPNL catalog fetch | ✗ | ✓ |

### Module Structure

```
src/tractusx_sdk/dataspace/services/connector/
├── base_connector_service.py       # Shared base: .consumer, .provider, .contract_agreements
├── base_connector_consumer.py      # Shared consumer logic (catalog, EDR, DSP flows)
├── base_connector_provider.py      # Shared provider logic (assets, policies, contracts)
├── jupiter/
│   ├── connector_service.py        # Jupiter ConnectorService (nothing beyond base)
│   ├── connector_consumer_service.py
│   └── connector_provider_service.py
└── saturn/
    ├── connector_service.py        # Saturn ConnectorService (nothing beyond base)
    ├── connector_consumer_service.py   # Saturn-specific consumer extensions
    └── connector_provider_service.py   # Inherits base provider unchanged
```

### Instantiation

Use `ServiceFactory` for all versions — the factory resolves the correct implementation:

```python
from tractusx_sdk.dataspace.services.connector import ServiceFactory

# Saturn Consumer
consumer = ServiceFactory.get_connector_consumer_service(
    dataspace_version="saturn",
    base_url="https://consumer-controlplane.example.com",
    dma_path="/management",
    headers={"X-Api-Key": "my-key", "Content-Type": "application/json"},
)

# Saturn Provider
provider = ServiceFactory.get_connector_provider_service(
    dataspace_version="saturn",
    base_url="https://provider-controlplane.example.com",
    dma_path="/management",
    headers={"X-Api-Key": "my-key", "Content-Type": "application/json"},
)

# Combined (consumer + provider via .consumer / .provider)
connector = ServiceFactory.get_connector_service(
    dataspace_version="saturn",
    base_url="https://my-controlplane.example.com",
    dma_path="/management",
    headers={"X-Api-Key": "my-key", "Content-Type": "application/json"},
)
```

---

### Consumer Service — Full Function Reference

All methods below are available on instances of the Saturn `ConnectorConsumerService`. Methods marked **Saturn only** do not exist in Jupiter.

#### Properties

| Property | Returns | Description |
|----------|---------|-------------|
| `.catalogs` | `BaseDmaController` | Catalog API controller |
| `.edrs` | `BaseDmaController` | EDR (Endpoint Data Reference) controller |
| `.contract_negotiations` | `BaseDmaController` | Contract negotiation controller |
| `.transfer_processes` | `BaseDmaController` | Transfer process controller |
| `.connector_discovery` ⭐ | `BaseDmaController` | Connector Discovery controller — **Saturn only** |

#### Catalog Discovery

| Method | Key Parameters | Description |
|--------|---------------|-------------|
| `get_catalog(counter_party_id, counter_party_address, ...)` | `counter_party_id`, `counter_party_address` | Fetch the full DCAT catalog from a provider |
| `get_catalog_request(counter_party_id, counter_party_address, protocol, context)` | `counter_party_id`, `counter_party_address` | Build a raw catalog request object |
| `get_catalog_with_filter(counter_party_id, counter_party_address, filter_expression, ...)` | `filter_expression: list[dict]` | Fetch a catalog filtered by a list of expressions |
| `get_catalog_request_with_filter(counter_party_id, counter_party_address, filter_expression, ...)` | `filter_expression: list[dict]` | Build a filtered catalog request object |
| `get_catalog_by_dct_type(counter_party_id, counter_party_address, dct_type, ...)` | `dct_type: str` | Fetch catalog filtered by `dct:type` |
| `get_catalog_by_asset_id(counter_party_id, counter_party_address, asset_id, ...)` | `asset_id: str` | Fetch catalog filtered by the EDC asset ID |
| `get_catalog_with_filter_parallel(counter_party_id, counter_party_address, filter_expression, catalogs, ...)` | `catalogs: dict` | Thread-target variant — stores result in `catalogs[url]` |
| `get_catalogs_by_dct_type(counter_party_id, edcs, dct_type, ...)` | `edcs: list` | Fetch filtered catalogs from multiple EDC URLs in parallel |
| `get_catalogs_with_filter(counter_party_id, edcs, filter_expression, ...)` | `edcs: list` | Same but with a custom filter expression list |
| `get_filter_expression(key, value, operator)` | `key`, `value` | Build a single filter condition dict |
| `get_query_spec(filter_expression)` | `filter_expression: list[dict]` | Wrap filter conditions in an EDC `QuerySpec` dict |

#### BPNL-Aware Catalog Discovery ⭐ Saturn only

| Method | Key Parameters | Description |
|--------|---------------|-------------|
| `get_catalog_with_bpnl(bpnl, counter_party_address, filter_expression, namespace, context, verify)` | `bpnl: str` | Look up the provider DSP URL via BPNL, then fetch a filtered catalog |
| `get_catalog_by_dct_type_with_bpnl(bpnl, counter_party_address, dct_type, ...)` | `bpnl: str`, `dct_type: str` | Discover + filter by `dct:type` with BPNL resolution |
| `get_catalog_by_asset_id_with_bpnl(bpnl, counter_party_address, asset_id, ...)` | `bpnl: str`, `asset_id: str` | Discover + filter by asset ID with BPNL resolution |
| `get_catalog_with_filter_parallel_with_bpnl(bpnl, counter_party_address, filter_expression, catalogs, ...)` | `bpnl: str` | Thread-target BPNL-aware parallel catalog fetch |
| `get_catalogs_by_dct_type_with_bpnl(bpnl, edcs, dct_type, ...)` | `bpnl: str`, `edcs: list` | Parallel multi-EDC catalog fetch by type, with BPNL |
| `get_catalogs_with_filter_with_bpnl(bpnl, edcs, filter_expression, ...)` | `bpnl: str`, `edcs: list` | Parallel multi-EDC catalog fetch, custom filter, with BPNL |
| `get_catalogs_by_dct_type_with_bpnl_parallel(bpnl, edcs, dct_type, ...)` | `bpnl: str`, `edcs: list` | Fully async parallel variant of `get_catalogs_by_dct_type_with_bpnl` |
| `get_catalogs_with_filter_with_bpnl_parallel(bpnl, edcs, filter_expression, ...)` | `bpnl: str`, `edcs: list` | Fully async parallel variant of `get_catalogs_with_filter_with_bpnl` |

#### BPNL / DID Discovery ⭐ Saturn only

| Method | Returns | Description |
|--------|---------|-------------|
| `discover_connector_protocol(bpnl, counter_party_address, verify)` | `dict` \| `None` | Query the Connector Discovery Service for the provider entry matching a BPNL |
| `get_discovery_info(bpnl, counter_party_address, namespace, verify)` | `(address, id, protocol)` | Full resolution: returns `(dsp_url, bpnl, dt_protocol)` ready to pass to catalog/negotiation calls |

#### Contract Negotiation

| Method | Key Parameters | Description |
|--------|---------------|-------------|
| `get_edr_negotiation_request(counter_party_id, counter_party_address, target, policy, ...)` | `target: str`, `policy: dict` | Build a contract negotiation request model |
| `start_edr_negotiation(counter_party_id, counter_party_address, target, policy, ...)` | `target: str`, `policy: dict` | Start a contract/EDR negotiation; returns `negotiation_id` |
| `get_edr_negotiation_filter(negotiation_id)` | `negotiation_id: str` | Build a `QuerySpec` filter for a specific negotiation |
| `get_edr_entry(negotiation_id, verify)` | `negotiation_id: str` | Wait-free poll: returns the EDR entry dict (or `None` if not yet available) |

#### EDR & Data Plane

| Method | Key Parameters | Description |
|--------|---------------|-------------|
| `get_edr(transfer_id, verify)` | `transfer_id: str` | Retrieve the latest EDR token for a completed transfer |
| `get_endpoint_with_token(transfer_id)` | `transfer_id: str` | Returns `(dataplane_endpoint, authorization)` tuple |
| `get_data_plane_headers(access_token, content_type)` | `access_token: str` | Build `Authorization` + optional `Content-Type` header dict |

#### Transfer Negotiation

| Method | Key Parameters | Description |
|--------|---------------|-------------|
| `get_transfer_id(counter_party_id, counter_party_address, filter_expression, ...)` | `filter_expression: list[dict]` | Full negotiate-and-transfer flow; returns `transfer_id` |
| `negotiate_and_transfer(counter_party_id, counter_party_address, filter_expression, ...)` | `filter_expression: list[dict]` | Negotiate, poll for agreement, and initiate transfer; returns `transfer_id` |
| `assets_exists(counter_party_id, counter_party_address, filter_expression, ...)` | `filter_expression: list[dict]` | Returns `True` if at least one matching asset is found in the provider catalog |

#### High-Level DSP Convenience Methods

These methods wrap the full catalog → negotiate → transfer → HTTP request lifecycle in a single call.

| Method | Key Parameters | Description |
|--------|---------------|-------------|
| `do_dsp(counter_party_id, counter_party_address, filter_expression, method, ...)` | `method: str` | Full DSP flow then issues GET / POST / PUT against the data plane |
| `do_dsp_with_bpnl(bpnl, counter_party_address, filter_expression, method, ...)` ⭐ | `bpnl: str`, `method: str` | Same with BPNL resolution — **Saturn only** |
| `do_dsp_by_dct_type(counter_party_id, counter_party_address, dct_type, method, ...)` | `dct_type: str` | DSP flow filtered by `dct:type` |
| `do_dsp_by_asset_id(counter_party_id, counter_party_address, asset_id, method, ...)` | `asset_id: str` | DSP flow filtered by asset ID |
| `do_get(counter_party_id, counter_party_address, filter_expression, ...)` | `filter_expression: list[dict]` | Full DSP flow + GET data from the data plane |
| `do_get_with_bpnl(bpnl, counter_party_address, filter_expression, ...)` ⭐ | `bpnl: str` | Same with BPNL resolution — **Saturn only** |
| `do_get_by_dct_type(counter_party_id, counter_party_address, dct_type, ...)` | `dct_type: str` | GET flow filtered by `dct:type` |
| `do_get_by_asset_id(counter_party_id, counter_party_address, asset_id, ...)` | `asset_id: str` | GET flow filtered by asset ID |
| `do_post(counter_party_id, counter_party_address, filter_expression, json, ...)` | `json: dict` | Full DSP flow + POST payload to the data plane |
| `do_post_with_bpnl(bpnl, counter_party_address, filter_expression, json, ...)` ⭐ | `bpnl: str`, `json: dict` | Same with BPNL resolution — **Saturn only** |
| `do_post_by_dct_type(counter_party_id, counter_party_address, dct_type, json, ...)` | `dct_type: str` | POST flow filtered by `dct:type` |
| `do_post_by_asset_id(counter_party_id, counter_party_address, asset_id, json, ...)` | `asset_id: str` | POST flow filtered by asset ID |
| `do_put(counter_party_id, counter_party_address, filter_expression, json, ...)` | `json: dict` | Full DSP flow + PUT payload to the data plane |
| `do_put_with_bpnl(bpnl, counter_party_address, filter_expression, json, ...)` ⭐ | `bpnl: str`, `json: dict` | Same with BPNL resolution — **Saturn only** |

---

### Provider Service — Function Reference

The Saturn `ConnectorProviderService` is identical to the base. All methods are available for both `"jupiter"` and `"saturn"`.

#### Properties

| Property | Returns | Description |
|----------|---------|-------------|
| `.assets` | `BaseDmaController` | Asset API controller (CRUD) |
| `.contract_definitions` | `BaseDmaController` | Contract definition controller |
| `.policies` | `BaseDmaController` | Policy controller |

#### Shortcut Methods

| Method | Key Parameters | Description |
|--------|---------------|-------------|
| `create_asset(asset_id, base_url, dct_type, version, semantic_id, proxy_params, headers, private_properties, ...)` | `asset_id: str`, `base_url: str` | Build and POST a complete EDC asset (data address + properties + private properties) |
| `create_contract(asset_id, access_policy_id, usage_policy_id, ...)` | `asset_id: str` | Build and POST a contract definition linking an asset to access and usage policies |
| `create_policy(policy_id, permissions, ...)` | `policy_id: str` | Build and POST an ODRL policy |

---

### Saturn Consumer Service — Code Examples

#### Discover provider via BPNL and fetch asset catalog

```python
from tractusx_sdk.dataspace.services.connector import ServiceFactory

consumer = ServiceFactory.get_connector_consumer_service(
    dataspace_version="saturn",
    base_url="https://consumer-controlplane.example.com",
    dma_path="/management",
    headers={"X-Api-Key": "my-key", "Content-Type": "application/json"},
)

# Resolve DSP URL from BPNL, then fetch catalog filtered by dct:type
catalog = consumer.get_catalog_by_dct_type_with_bpnl(
    bpnl="BPNL00000003AYRE",
    dct_type="https://w3id.org/catenax/taxonomy#Submodel",
)
```

#### Full data access flow with BPNL (single call)

```python
response = consumer.do_get_with_bpnl(
    bpnl="BPNL00000003AYRE",
    filter_expression=[
        consumer.get_filter_expression(
            key="https://w3id.org/edc/v0.0.1/ns/id",
            value="urn:uuid:my-asset-id",
        )
    ],
    path="/",         # path appended to the data plane URL
    verify=False,
)

if response.status_code == 200:
    print(response.json())
```

#### Provide an asset via Saturn

```python
from tractusx_sdk.dataspace.services.connector import ServiceFactory

provider = ServiceFactory.get_connector_provider_service(
    dataspace_version="saturn",
    base_url="https://provider-controlplane.example.com",
    dma_path="/management",
    headers={"X-Api-Key": "my-key", "Content-Type": "application/json"},
)

provider.create_asset(
    asset_id="urn:uuid:my-asset",
    base_url="https://submodel-service.example.com/",
    dct_type="https://w3id.org/catenax/taxonomy#Submodel",
    semantic_id="urn:samm:io.catenax.part_type_information:1.0.0#PartTypeInformation",
    version="3.0",
)

provider.create_policy(
    policy_id="access-policy-001",
    permissions=[{"action": "access", "constraint": {
        "leftOperand": "BusinessPartnerNumber",
        "operator": "isAnyOf",
        "rightOperand": "BPNL00000003CONS",
    }}],
)

provider.create_contract(
    asset_id="urn:uuid:my-asset",
    access_policy_id="access-policy-001",
    usage_policy_id="usage-policy-001",
)
```

---

## Further Reading

- [Backward Compatibility Guide](../../../index.md#protocol-backward-compatibility-guide) - Side-by-side Jupiter vs Saturn code patterns, policy syntax migration, and version-agnostic wrappers

- [Dataspace Library Overview](../index.md)
- [SDK Structure and Components](../../../core-concepts/sdk-architecture/sdk-structure-and-components.md)
- [Connector Discovery Example](../discovery-services/connector-discovery-service.md)
- [API Reference](https://eclipse-tractusx.github.io/api-hub/)

---

## NOTICE

This work is licensed under the [CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/legalcode).

- SPDX-License-Identifier: CC-BY-4.0
- SPDX-FileCopyrightText: 2025, 2026 Contributors to the Eclipse Foundation
- SPDX-FileCopyrightText: 2025, 2026 Catena-X Automotive Network e.V.
- SPDX-FileCopyrightText: 2025, 2026 LKS Next
- SPDX-FileCopyrightText: 2025, 2026 Mondragon Unibertsitatea
- Source URL: [https://github.com/eclipse-tractusx/tractusx-sdk](https://github.com/eclipse-tractusx/tractusx-sdk)
