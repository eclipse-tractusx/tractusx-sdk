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

# 2. Architecture Constraints

## Technical Constraints

| Constraint | Rationale |
|-----------|-----------|
| **Python ≥ 3.12** | The SDK uses modern Python typing features and relies on libraries that require 3.12+. Compatibility with 3.13 and 3.14 is continuously validated via CI. |
| **No persistence layer** | The SDK is a pure library. All state management and persistence is the responsibility of the consuming application (see [ADR-0002](../contributing/architectural-decisions/0002-data-storage-architecture.md)). |
| **No deployable artifacts** | The SDK does not ship Docker images, Helm charts, or any deployment manifests. Microservices built on top of the SDK are maintained in the separate [tractusx-sdk-services](https://github.com/eclipse-tractusx/tractusx-sdk-services) repository (see [ADR-0004](../contributing/architectural-decisions/0004-tractusx-sdk-services.md)). |
| **HTTP/REST only** | All external integrations (EDC, DTR, Discovery services) communicate via HTTP REST. No message broker or gRPC dependencies. |
| **OS independence** | The SDK must run on Linux, macOS, and Windows. Platform-specific dependencies (e.g., `uvloop`) are made optional with compatible fallbacks. |
| **Poetry for dependency management** | Dependencies are declared in `pyproject.toml` using [Poetry](https://python-poetry.org/) groups (`dev`, `test`, `docs`). |

## Organizational Constraints

| Constraint | Rationale |
|-----------|-----------|
| **Eclipse Foundation governance** | The project is governed by the [Eclipse Foundation Development Process](https://www.eclipse.org/projects/dev_process/). All significant decisions must be transparent and community-driven. |
| **Eclipse Contributor Agreement (ECA)** | All contributors must electronically sign the [ECA](https://www.eclipse.org/legal/ECA.php) before their contributions can be merged. |
| **Eclipse IP Policy** | All third-party dependencies must be reviewed and approved under the *Eclipse IP Policy*. Dependency reviews are tracked in `DEPENDENCIES_TRACTUS-X_SDK`. |
| **Public development** | All development happens in the open on GitHub. No private branches or closed-door decisions. |
| **Semantic versioning** | Releases follow [Semantic Versioning 2.0.0](https://semver.org/). Breaking changes require a major version bump. |

## Legal Constraints

| Constraint | Description |
|-----------|-------------|
| **Apache License 2.0** | All SDK source code is licensed under Apache-2.0. |
| **CC-BY-4.0** | All documentation files (`.md`) are licensed under Creative Commons Attribution 4.0. |

## NOTICE

This work is licensed under the [CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/legalcode).

- SPDX-License-Identifier: CC-BY-4.0
- SPDX-FileCopyrightText: 2026 Contributors to the Eclipse Foundation
- SPDX-FileCopyrightText: 2026 LKS Next
- Source URL: [https://github.com/eclipse-tractusx/tractusx-sdk](https://github.com/eclipse-tractusx/tractusx-sdk)
