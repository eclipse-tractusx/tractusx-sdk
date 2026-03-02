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

# Extensions Library

The **Extensions Library** provides extensible components and utilities for enhancing the core SDK functionality. It enables use-case-specific implementations, semantic data processing, and custom business logic integration within the Tractus-X dataspace ecosystem.

## Overview

The Extensions Library abstracts domain-specific operations and offers:

- **Semantic Extensions**: Transform SAMM (Semantic Aspect Meta Model) schemas to JSON-LD contexts for semantic data processing.
- **Schema Processing**: Handle schema validation, transformation, and context generation.
- **Extensibility Framework**: Support for custom use-case implementations (certificate management, PCF calculation, etc.).
- **JSON-LD Context Generation**: Convert aspect models into standardized JSON-LD formats for linked data processing.
- **Schema Discovery Integration**: Fetch and process semantic models from centralized repositories.

## Architecture

The library follows a modular architecture with support for multiple extension types:

```text
tractusx_sdk/extensions/
├── semantics/                          # Semantic processing extensions
│   ├── schema_to_context_translator.py # SAMM schema to JSON-LD conversion
│   └── __init__.py
├── README.md
└── __init__.py
```

For a deeper dive into the SDK structure, see [SDK Structure and Components](../sdk-architecture/sdk-structure-and-components.md).

## Key Components

- **SAMM Schema Context Translator**: Converts SAMM (Semantic Aspect Meta Model) schemas to JSON-LD contexts for semantic data processing ([schema_to_context_translator.py](https://github.com/eclipse-tractusx/tractusx-sdk/blob/main/src/tractusx_sdk/extensions/semantics/schema_to_context_translator.py)). Supports both flattened and nested JSON-LD output formats with circular reference handling.
- **Schema To Schema Flattening**: Transforms complex SAMM aspect models into JSON-LD contexts while maintaining semantic relationships.
- **Nested Context Generation**: Creates nested JSON-LD contexts for hierarchical aspect model structures.
- **Schema Reference Resolution**: Dynamically resolves and fetches schema definitions from the Eclipse Tractus-X semantic models repository.

## Use Cases

Extensions enable domain-specific implementations such as:

- **Certificate Management**: Handling product certifications and compliance data
- **Product Carbon Footprint (PCF)**: Calculating and managing carbon emissions data
- **Custom Business Logic**: Implementing domain-specific rules and validations
- **Semantic Data Processing**: Leveraging linked data for advanced data interoperability

## Usage

To get started, install the SDK and import semantic extensions:

```python
from tractusx_sdk.extensions.semantics import SammSchemaContextTranslator
```

See the [Getting Started](../../tutorials/getting-started.md) for setup instructions and first steps.

## Further Reading

- [Extensions Library API Reference](../../api-reference/extension-library/semantics/semantics.md)
- [SDK Structure and Components](../sdk-architecture/sdk-structure-and-components.md)
- [Tractus-X SDK Documentation](../../index.md)

## NOTICE

This work is licensed under the [CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/legalcode).

- SPDX-License-Identifier: CC-BY-4.0
- SPDX-FileCopyrightText: 2025 Contributors to the Eclipse Foundation
- Source URL: https://github.com/eclipse-tractusx/tractusx-sdk
