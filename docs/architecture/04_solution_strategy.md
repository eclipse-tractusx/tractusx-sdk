<!--

Eclipse Tractus-X - Software Development KIT

Copyright (c) 2026 LKS Next
Copyright (c) 2026 Contributors to the Eclipse Foundation

See the NOTICE file(s) distributed with this work for additional
information regarding copyright ownership.

This work is made available under the terms of the
Creative Commons Attribution 4.0 International (CC-BY-4.0) license,
which is available at
https://creativecommons.org/licenses/by/4.0/legalcode.

SPDX-License-Identifier: CC-BY-4.0

-->

# 4. Solution Strategy

## Core Decisions

The following architectural decisions shape the overall solution strategy. Each decision is backed by a formal Architecture Decision Record (ADR).

### 1. Modular Three-Library Architecture

The SDK is split into three independent, cohesive libraries: **Dataspace**, **Industry**, and **Extensions**. Each library is responsible for a distinct domain and can be used independently.

This avoids a monolithic design where dataspace protocol changes would ripple into industry-specific or extension code. See [ADR-0003](../contributing/architectural-decisions/0003-sdk-module-architecture.md).

### 2. Factory + Adapter Pattern for Multi-Version Support

Each library uses a **Factory Pattern** to create version-specific service instances. Version-specific logic is isolated in submodules (e.g., `adapters/connector/jupiter/`, `adapters/connector/saturn/`). The factory selects the correct implementation at runtime based on the `dataspace_version` parameter.

This allows new EDC versions to be added without modifying existing stable code, satisfying the extensibility quality goal.

```python
# Consumer chooses the dataspace version; factory handles the rest
service = ServiceFactory.get_connector_consumer_service(
    dataspace_version="saturn",  # or "jupiter"
    base_url="https://connector.example.com",
    headers=headers,
)
```

### 3. No Persistence in the SDK

The SDK deliberately has no database or persistence layer. It provides an in-memory cache for short-lived connection state (e.g., EDR tokens), which can be disabled. All long-term storage is the responsibility of the consuming application. See [ADR-0002](../contributing/architectural-decisions/0002-data-storage-architecture.md).

This keeps the SDK stateless and testable, and avoids coupling it to any specific storage technology.

### 4. Separate Repository for Microservices

Deployable microservices that use the SDK are maintained in [tractusx-sdk-services](https://github.com/eclipse-tractusx/tractusx-sdk-services), not in this repository. The SDK itself is a pure library — it does not include FastAPI routers, Docker files, or Helm charts. See [ADR-0004](../contributing/architectural-decisions/0004-tractusx-sdk-services.md).

### 5. Layered Internal Architecture

Every library follows the same internal layer ordering:

```
Services → Controllers → Adapters → External HTTP
```

- **Services** expose the public API. Consumers call only the service layer.
- **Controllers** implement API-specific logic (URL construction, response parsing).
- **Adapters** handle raw HTTP communication (retries, headers, error mapping).

This ensures that changes to external APIs (e.g., new EDC endpoint paths) are isolated to the adapter/controller layers and do not affect service-level consumer code.

## Technology Choices

| Technology | Choice | Rationale |
|-----------|--------|-----------|
| Language | Python 3.12+ | Dominant language in data engineering and AI/ML pipelines |
| HTTP client | `httpx` / `requests` | Widely used; async support for pipeline scenarios |
| Data models | Pydantic | Type-safe serialization/deserialization with IDE support |
| Web framework (optional) | FastAPI | Used in consuming microservices (not in core SDK) |
| Build & packaging | Poetry | Reliable dependency resolution; group-based optional deps |
| Testing | pytest + pytest-cov | Industry standard; supports async tests |
| Documentation | MkDocs Material | Renders on GitHub Pages; supports Mermaid diagrams |

## NOTICE

This work is licensed under the [CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/legalcode).

- SPDX-License-Identifier: CC-BY-4.0
- SPDX-FileCopyrightText: 2026 Contributors to the Eclipse Foundation
- SPDX-FileCopyrightText: 2026 LKS Next
- Source URL: [https://github.com/eclipse-tractusx/tractusx-sdk](https://github.com/eclipse-tractusx/tractusx-sdk)
