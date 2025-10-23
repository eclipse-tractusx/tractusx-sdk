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
# Connector Models

The Tractus-X SDK provides a set of connector models that define the structure and semantics of all major dataspace entities. These models are used throughout the SDK to represent assets, catalogs, contracts, policies, negotiations, and more. Each model is versioned to support both "jupiter" and "saturn" dataspace protocols, ensuring compatibility and extensibility as standards evolve.

## Purpose

Connector models provide a unified way to:

- Register and manage assets and their metadata
- Discover and query catalogs and datasets
- Define, negotiate, and retire contracts
- Specify and evaluate data sharing policies
- Track and control data transfer processes

By using these models, SDK users can interact with dataspace connectors in a consistent and reliable manner, regardless of protocol version.

## Key Models

Below are the main connector models grouped by their protocol support. Saturn-specific models extend the SDK for advanced dataspace scenarios, while shared models are available for both Jupiter and Saturn connectors.

### Saturn-Specific Models

| Model Name                        | Version   | Description                                                      | Main Attributes (Type)                                                                                  |
|------------------------------------|-----------|------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------|
| `CatalogDatasetRequestModel`       | Saturn    | Request datasets from a Saturn catalog.                          | `TYPE` (str), `oid` (str), `counter_party_address` (str), `counter_party_id` (str), `protocol` (str), `context` (dict/list/str) |
| `ConnectorDiscoveryModel`          | Saturn    | Discover connector parameters for Saturn endpoints.              | `TYPE` (str), `bpnl` (str), `counter_party_address` (str), `context` (dict/list/str)                   |
| `ContractAgreementRetirementModel` | Saturn    | Retire contract agreements in Saturn dataspace.                  | `agreement_id` (str), `reason` (str), `context` (dict/list/str)                                        |
| `EvaluationPolicyModel`            | Saturn    | Request policy evaluation plans for Saturn.                      | `TYPE` (str), `policy_scope` (str), `context` (dict/list/str)                                          |

### Shared Models (Jupiter & Saturn)

These models are available for both Jupiter and Saturn dataspace connectors and cover the most common dataspace operations:

| Model Name                  | Version   | Description                                                      | Main Attributes (Type)                                                                                  |
|-----------------------------|-----------|------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------|
| `AssetModel`                | Both      | Represents a dataspace asset and its metadata.                   | `oid` (str), `data_address` (dict), `context` (dict/list/str), `properties` (dict), `private_properties` (dict) |
| `CatalogModel`              | Both      | Describes a catalog of available assets/contracts.                | `counter_party_address` (str), `counter_party_id` (str), `context` (dict/list/str), `queryspec` (`QuerySpecModel`), `protocol` (str) |
| `ContractDefinitionModel`   | Both      | Defines contract terms for asset usage.                          | `oid` (str), `access_policy_id` (str), `contract_policy_id` (str), `context` (dict/list/str), `assets_selector` (list[dict]) |
| `ContractNegotiationModel`  | Both      | Represents a contract negotiation process.                       | `counter_party_address` (str), `offer_id` (str), `offer_policy` (dict), `asset_id` (str), `provider_id` (str), `context` (dict/list/str) |
| `PolicyModel`               | Both      | Specifies permissions, prohibitions, and obligations.            | `oid` (str), `context` (dict/list/str), `permissions` (dict/list[dict]), `prohibitions` (dict/list[dict]), `obligations` (dict/list[dict]) |
| `QuerySpecModel`            | Both      | Specification for catalog queries and filtering.                  | `TYPE` (str), `context` (dict/list/str), `offset` (int), `limit` (int), `sort_order` (str), `sort_field` (str), `filter_expression` (list[dict]) |

## Model Instantiation Example

All connector models are instantiated using the builder pattern via the SDK's `ModelFactory`. This ensures that models are constructed with the correct attributes for the chosen dataspace version.

```python
from tractusx_sdk.dataspace.models.connector import ModelFactory

# Example: Create an Asset model
asset = ModelFactory.get_asset_model(
    dataspace_version="jupiter",
    oid="asset-123",
    data_address={"type": "HttpData"},
    context={"@vocab": "https://w3id.org/edc/v0.0.1/ns/"},
    properties={"name": "My Asset"}
)
```

## Model Attribute Reference

The following table summarizes the most important attributes used across connector models. Refer to the SDK API docs for full details and advanced usage.

| Attribute            | Type                | Description                                                                                  |
|----------------------|---------------------|----------------------------------------------------------------------------------------------|
| `oid`                | `str`               | Unique identifier for the model/entity                                                       |
| `data_address`       | `dict`              | Data source or endpoint information for the asset                                            |
| `context`            | `dict`/`list`/`str` | JSON-LD context for semantic annotation                                                      |
| `properties`         | `dict`              | Public metadata properties                                                                   |
| `private_properties` | `dict`              | Private metadata properties                                                                  |
| `counter_party_address` | `str`            | Address/URL of the counterparty connector                                                    |
| `counter_party_id`   | `str`               | Identifier of the counterparty                                                               |
| `queryspec`          | `QuerySpecModel`    | Query specification for catalog requests and filtering                                       |
| `offset`             | `int`               | Pagination offset for query results                                                          |
| `limit`              | `int`               | Pagination limit for query results                                                           |
| `sort_order`         | `str`               | Sort order for query results (`ASC` or `DESC`)                                               |
| `sort_field`         | `str`               | Field to sort query results by                                                               |
| `filter_expression`  | `list[dict]`        | List of filter expressions for advanced querying                                             |
| `protocol`           | `str`               | Dataspace protocol version                                                                   |
| `access_policy_id`   | `str`               | ID of the access policy for contract definition                                              |
| `contract_policy_id` | `str`               | ID of the contract policy for contract definition                                            |
| `assets_selector`    | `list[dict]`        | Selector/filter for assets in contract definition                                            |
| `offer_id`           | `str`               | ID of the contract offer                                                                     |
| `offer_policy`       | `dict`              | Policy details for the contract offer                                                        |
| `asset_id`           | `str`               | ID of the asset involved in negotiation                                                      |
| `provider_id`        | `str`               | ID of the provider connector                                                                 |
| `permissions`        | `dict`/`list[dict]` | Permissions specified in a policy                                                            |
| `prohibitions`       | `dict`/`list[dict]` | Prohibitions specified in a policy                                                           |
| `obligations`        | `dict`/`list[dict]` | Obligations specified in a policy                                                            |

## Further Reading

- [Connector Services Overview](services.md)
- [SDK Structure and Components](../../../core-concepts/sdk-architecture/sdk-structure-and-components.md)
- [Dataspace Library Overview](../index.md)
- [API Reference](https://eclipse-tractusx.github.io/api-hub/)

---

## NOTICE

This work is licensed under the [CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/legalcode).

- SPDX-License-Identifier: CC-BY-4.0
- SPDX-FileCopyrightText: 2025 Contributors to the Eclipse Foundation
- Source URL: https://github.com/eclipse-tractusx/tractusx-sdk
