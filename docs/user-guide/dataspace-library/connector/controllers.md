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

# Connector Controllers

This page provides a comprehensive overview of the **Connector controllers** in the Tractus-X SDK. These controllers are the main building blocks for interacting with dataspace entities managed by the Eclipse Tractus-X Connector, such as assets, contracts, policies, and transfer processes. Whether you are managing data, negotiating contracts, or monitoring connector health, connector controllers offer a unified and extensible API for all major dataspace operations. Use this guide to understand which connector controller fits your use case, how to instantiate them, and what methods are available for each type.

## Purpose

Connector Controllers provide the main interface for interacting with dataspace entities such as assets, contracts, policies, and transfer processes. They encapsulate the logic for CRUD operations, queries, and process management, abstracting the underlying HTTP/API details and ensuring consistency across dataspace versions.

Controllers are responsible for:

- Managing dataspace entities (assets, contracts, policies, etc.)
- Querying and retrieving entity details
- Orchestrating data transfer and negotiation processes

They are versioned and extensible, supporting multiple dataspace standards (e.g., "jupiter", "saturn").

## Controller Types, Supported Versions, and Methods

The following table summarizes all available controller types in the Tractus-X SDK, the dataspace protocol versions they support, and the key methods they provide. The rightmost column describes the main purpose of each controller, helping you quickly identify which controller to use for a given task.

!!! tip
    Most controllers are available for both the "jupiter" and "saturn" dataspace versions. Some advanced controllers (such as Dataplane Selector, Application Observability, Connector Discovery, and Protocol Version) are specific to the "saturn" version and provide specialized functionality for connector management and monitoring.

| Controller Type                | Supported Versions | Methods                                                                                                   | Description                                                                 |
|-------------------------------|-------------------|----------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------|
| **Asset Controller**           | Jupiter, Saturn   | `create`, `update`, `get_by_id`, `delete`, `get_all`, `query`                                            | Manages assets: create, update, retrieve, delete, and query                 |
| **Catalog Controller**         | Jupiter, Saturn   | `get_catalog`                                                                                            | Retrieves catalogs of available assets from counterparties                   |
| **Contract Agreement Controller** | Jupiter, Saturn   | `get_negotiation_by_id`, `get_by_id`, `get_all`, `query`                                               | Manages contract agreements and negotiations                                 |
| **Contract Definition Controller** | Jupiter, Saturn   | `create`, `update`, `get_by_id`, `delete`, `get_all`, `query`                                         | Manages contract definitions: create, update, retrieve, delete, and query    |
| **Contract Negotiation Controller** | Jupiter, Saturn   | `create`, `terminate_by_id`, `get_agreement_by_negotiation_id`, `get_by_id`, `get_all`, `get_state_by_id`, `query` | Handles contract negotiation lifecycle and agreement retrieval                |
| **EDR Controller**             | Jupiter, Saturn   | `get_data_address`, `refresh`, `create`, `get_all`, `delete`, `query`                                    | Manages Endpoint Data References (EDRs) for secure data access               |
| **Policy Controller**          | Jupiter, Saturn   | `create`, `update`, `get_by_id`, `delete`, `get_all`, `query`                                            | Manages policies: create, update, retrieve, delete, and query                |
| **Transfer Process Controller** | Jupiter, Saturn   | `create`, `terminate_by_id`, `deprovision_by_id`, `get_by_id`, `get_all`, `query`, `get_state_by_id`     | Orchestrates data transfer processes between dataspace participants           |
| **Dataplane Selector Controller** | Saturn           | `get_all_v3`, `get_all_v4alpha`                                                                          | Manages and queries available dataplanes for data transfer                   |
| **Application Observability Controller** | Saturn           | `get_health`, `get_liveness`                                                                             | Provides health and liveness checks for connector applications                |
| **Connector Discovery Controller** | Saturn           | `get_discover`                                                                                           | Discovers connectors and their protocol versions in the dataspace             |
| **Protocol Version Controller** | Saturn           | `get_discover`                                                                                           | Queries supported protocol versions for connectors                            |

## Instantiation & Required Attributes

Controllers are typically instantiated via the `ControllerFactory`, which selects the correct implementation for the dataspace version and entity type.

**Required attributes for instantiation:**

| Attribute           | Type                | Description                                               |
|---------------------|---------------------|-----------------------------------------------------------|
| `dataspace_version` | `str`               | Dataspace protocol version (e.g., `"jupiter"`, `"saturn"`) |
| `adapter`           | `BaseDmaAdapter`    | Adapter for HTTP/API communication                        |
| `endpoint_url`      | `str`               | API endpoint for the controller                           |
| `model`             | `Model`             | Entity model for operations (varies by controller)        |
| `kwargs`            | `dict` (optional)   | Additional parameters for customization                   |

### Example

```python
from tractusx_sdk.dataspace.controllers.connector.controller_factory import ControllerFactory
from tractusx_sdk.dataspace.adapters.connector.adapter_factory import AdapterFactory

# Instantiate the DMA adapter for the desired dataspace version and connector
my_adapter = AdapterFactory.get_dma_adapter(
    dataspace_version="jupiter",
    base_url="https://my-connector-controlplane.url",
    dma_path="/management",
    headers={"X-Api-Key": "my-api-key", "Content-Type": "application/json"}
)

# Instantiate the asset controller using the adapter
asset_controller = ControllerFactory.get_asset_controller(
    dataspace_version="jupiter",
    adapter=my_adapter
)
```

## Controller Methods Reference

| Method Name                         | Required Attributes / Parameters         | Controllers Implementing Method                | Description                                                                                   |
|--------------------------------------|-----------------------------------------|-----------------------------------------------|-----------------------------------------------------------------------------------------------|
| `create`                            | `Model`                                 | Asset, Contract Definition, Policy, Contract Negotiation, Transfer Process, EDR | Registers a new entity (asset, contract, policy, etc.)                                        |
| `update`                            | `Model`                                 | Asset, Contract Definition, Policy            | Updates metadata or properties of an existing entity                                          |
| `get_by_id`                         | `oid`                                   | Asset, Contract Definition, Policy, Contract Agreement, Contract Negotiation, Transfer Process, EDR | Retrieves details of a specific entity by its unique identifier                               |
| `delete`                            | `oid`                                   | Asset, Contract Definition, Policy, EDR       | Deletes an entity by its unique identifier                                                    |
| `get_all`                           |                                         | Asset, Contract Definition, Policy, Contract Agreement, Contract Negotiation, Transfer Process, EDR | Retrieves a list of all entities currently registered                                         |
| `query`                             | `QuerySpecModel` (optional)             | Asset, Contract Definition, Policy, Contract Agreement, Contract Negotiation, Transfer Process, EDR | Queries entities based on specific criteria                                                   |
| `get_state_by_id`                   | `oid`                                   | Contract Negotiation, Transfer Process        | Retrieves the current state of a specific entity                                              |
| `terminate_by_id`                   | `oid`, `Model`                          | Contract Negotiation, Transfer Process        | Terminates an ongoing process by its unique identifier                                        |
| `refresh`                           | `oid`                                   | EDR                                          | Refreshes the Endpoint Data Reference (EDR) for an entity                                     |
| `get_data_address`                  | `oid`                                   | EDR                                          | Retrieves the data address associated with an asset or contract                               |
| `get_catalog`                       | `CatalogModel`                          | Catalog                                      | Retrieves catalogs of available assets from counterparties                                    |
| `get_negotiation_by_id`             | `oid`                                   | Contract Agreement                           | Retrieves negotiation details for a contract agreement                                        |
| `get_agreement_by_negotiation_id`   | `oid`                                   | Contract Negotiation                         | Retrieves contract agreement by negotiation ID                                                |
| `deprovision_by_id`                 | `oid`                                   | Transfer Process                             | Deprovisions resources associated with a transfer process                                     |
| `get_all_v3`                        |                                         | Dataplane Selector (Saturn)                  | Retrieves all dataplanes (v3 API)                                                            |
| `get_all_v4alpha`                   |                                         | Dataplane Selector (Saturn)                  | Retrieves all dataplanes (v4alpha API)                                                       |
| `get_health`                        |                                         | Application Observability (Saturn)           | Provides health check for connector application                                              |
| `get_liveness`                      |                                         | Application Observability (Saturn)           | Provides liveness check for connector application                                            |
| `get_readiness`                     |                                         | Application Observability (Saturn)           | Provides readiness check for connector application                                           |
| `get_startup`                       |                                         | Application Observability (Saturn)           | Provides startup check for connector application                                             |
| `get_discover`                      | `Model`                                 | Connector Discovery, Protocol Version (Saturn)| Discovers connectors or protocol versions in the dataspace                                   |
| `evaluation_plan`                   | `oid`, `EvaluationPolicyModel`           | Policy (Saturn)                              | Evaluates a policy plan for a given policy definition                                        |
| `validate_policy`                   | `oid`                                   | Policy (Saturn)                              | Validates a policy definition                                                                |

!!! info  Note

    - `Model` refers to the specific model type for the controller (e.g., `AssetModel`, `ContractDefinitionModel`, `PolicyModel`, etc.)
    - `oid` is the unique identifier for the entity.
    - Not all controllers implement every method; see specific controller documentation for details.

## Further Reading

- [Dataspace Library Overview](../index.md)
- [SDK Structure and Components](../../sdk-structure-and-components.md)
- [Connector Services](./services.md)
- [API Reference](https://eclipse-tractusx.github.io/api-hub/)

---

## NOTICE

This work is licensed under the [CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/legalcode).

- SPDX-License-Identifier: CC-BY-4.0
- SPDX-FileCopyrightText: 2025 Contributors to the Eclipse Foundation
- Source URL: https://github.com/eclipse-tractusx/tractusx-sdk
