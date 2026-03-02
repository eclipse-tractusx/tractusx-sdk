<!--

Eclipse Tractus-X - Software Development KIT

Copyright (c) 2026 Mondragon Unibertsitatea
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

# Industry Library

The **Industry Library** provides comprehensive tools and services for handling essential Tractus-X dataspace components. It enables seamless integration with the Digital Twin Registry (DTR) and Submodel Server, allowing you to embed DTR logic and submodel management capabilities into your application.

## Overview

The Industry Library abstracts complex Asset Administration Shell (AAS) interactions and offers:

- **AAS Service**: Interact with the Digital Twin Registry (DTR) to manage shell and submodel descriptors.
- **Submodel Adapters**: Handle HTTP communication with different submodel server implementations.
- **Submodel Adapter Factory**: Dynamically create adapters for supported submodel server types.
- **Discovery Services**: Discover available digital twins and submodels in the dataspace.
- **Models & Schemas**: Define asset administration shells, submodels, and related AAS entities.
- **Managers**: Handle configuration, connection, and lifecycle management for AAS components.

## Architecture

The library follows a modular, layered architecture:

```text
tractusx_sdk/industry/
├── adapters/           # HTTP communication adapters
│   ├── submodel_adapter.py
│   ├── submodel_adapter_factory.py
│   └── submodel_adapters/
├── managers/           # Configuration and connection management
├── models/             # Data models and schemas
│   └── aas/            # Asset Administration Shell models (v3)
├── services/           # High-level business logic
│   ├── aas_service.py
│   └── discovery/      # Discovery service integrations
└── tools/              # Utility functions and helpers
```

For a deeper dive into the SDK structure, see [SDK Structure and Components](../sdk-architecture/sdk-structure-and-components.md).

## Key Components

- **AAS Service**: Core service for Digital Twin Registry interactions ([aas_service.py](https://github.com/eclipse-tractusx/tractusx-sdk/blob/main/src/tractusx_sdk/industry/services/aas_service.py)). Provides methods for retrieving and creating shell descriptors, submodel descriptors, and managing digital twins.
- **Submodel Adapter Factory**: Dynamically creates adapters for supported submodel server types ([submodel_adapter_factory.py](https://github.com/eclipse-tractusx/tractusx-sdk/blob/main/src/tractusx_sdk/industry/adapters/submodel_adapter_factory.py)).
- **Submodel Adapter**: Base HTTP communication adapter for submodel server interactions ([submodel_adapter.py](https://github.com/eclipse-tractusx/tractusx-sdk/blob/main/src/tractusx_sdk/industry/adapters/submodel_adapter.py)).
- **Discovery Services**: Locate and identify digital twins and submodels within the dataspace.

## Usage

To get started, install the SDK and import the AAS service:

```python
from tractusx_sdk.industry.services import AasService
```

See the [Getting Started](../../tutorials/getting-started.md) for setup instructions and first steps.

## Further Reading

- [Industry Library API Reference](../../api-reference/industry-library/dtr/services.md)
- [SDK Structure and Components](../sdk-architecture/sdk-structure-and-components.md)
- [Tractus-X SDK Documentation](../../index.md)

## NOTICE

This work is licensed under the [CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/legalcode).

- SPDX-License-Identifier: CC-BY-4.0
- SPDX-FileCopyrightText: 2025 Contributors to the Eclipse Foundation
- Source URL: https://github.com/eclipse-tractusx/tractusx-sdk
