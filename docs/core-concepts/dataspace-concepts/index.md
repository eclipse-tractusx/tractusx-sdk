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

# Dataspace Library

The **Dataspace Library** is the foundation of the Eclipse Tractus-X SDK for all dataspace interactions. It provides core connector services and integration with the Eclipse Tractus-X Connector, enabling secure, standardized data exchange in the Dataspace ecosystem.

## Overview

The Dataspace Library abstracts complex dataspace protocols and offers:

- **Connector Service Factory**: Easily create and configure connector services for different dataspace versions.
- **Consumer & Provider Services**: Interact with dataspace connectors as a data consumer or provider.
- **Connection Managers**: Handle authentication, connection lifecycle, and secure communication.
- **Controllers & Adapters**: Manage API requests and low-level HTTP communication with EDC connectors.
- **Discovery Services**: Discover available connectors and catalogs in the dataspace.
- **Models & Schemas**: Define assets, contracts, policies, and other dataspace entities.

## Architecture

The library follows a modular, layered architecture:

```text
tractusx_sdk/dataspace/
├── adapters/          # HTTP communication adapters
│   └── connector/     # Connector-specific adapters
├── controllers/       # API request handlers
│   └── connector/     # Connector API controllers
├── managers/          # Authentication and connection management
│   └── connection/    # Connection lifecycle management
├── models/            # Data models and schemas
│   ├── connection/    # Connection-related models
│   └── connector/     # Connector data models
├── services/          # High-level business logic
│   ├── connector/     # Connector service implementations
│   └── discovery/     # Discovery service integrations
└── tools/             # Utility functions and helpers
```

For a deeper dive into the SDK structure, see [SDK Structure and Components](../sdk-architecture/sdk-structure-and-components.md).

## Key Components

- **Service Factory**: Dynamically creates connector services for supported dataspace versions ([service_factory.py](https://github.com/eclipse-tractusx/tractusx-sdk/blob/main/src/tractusx_sdk/dataspace/services/connector/service_factory.py)).
- **BaseConnectorService**: Core abstraction for EDC connector interactions ([base_connector_service.py](https://github.com/eclipse-tractusx/tractusx-sdk/blob/main/src/tractusx_sdk/dataspace/services/connector/base_connector_service.py)).
- **Consumer/Provider Services**: Specialized classes for consuming and providing data ([base_connector_consumer.py](https://github.com/eclipse-tractusx/tractusx-sdk/blob/main/src/tractusx_sdk/dataspace/services/connector/base_connector_consumer.py), [base_connector_provider.py](https://github.com/eclipse-tractusx/tractusx-sdk/blob/main/src/tractusx_sdk/dataspace/services/connector/base_connector_provider.py)).
- **Discovery Services**: Find and connect to dataspace endpoints.

## Usage

To get started, install the SDK and import the connector service:

```python
from tractusx_sdk.dataspace.services import ConnectorService
```

See the [Getting Started](../../tutorials/getting-started.md) for setup instructions and first steps.

## Further Reading

- [Connector Services API Reference](../../api-reference/dataspace-library/connector/services.md)
- [SDK Structure and Components](../sdk-architecture/sdk-structure-and-components.md)
- [Tractus-X SDK Documentation](../../index.md)

## NOTICE

This work is licensed under the [CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/legalcode).

- SPDX-License-Identifier: CC-BY-4.0
- SPDX-FileCopyrightText: 2025 Contributors to the Eclipse Foundation
- Source URL: https://github.com/eclipse-tractusx/tractusx-sdk
