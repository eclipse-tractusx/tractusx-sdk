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

## Further Reading

- [Dataspace Library Overview](../index.md)
- [SDK Structure and Components](../../../core-concepts/sdk-architecture/sdk-structure-and-components.md)
- [Connector Discovery Example](../discovery-services/connector-discovery-service.md)
- [API Reference](https://eclipse-tractusx.github.io/api-hub/)

---

## NOTICE

This work is licensed under the [CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/legalcode).

- SPDX-License-Identifier: CC-BY-4.0
- SPDX-FileCopyrightText: 2025 Contributors to the Eclipse Foundation
- Source URL: https://github.com/eclipse-tractusx/tractusx-sdk
