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

# 9. Architecture Decisions

This chapter indexes all Architecture Decision Records (ADRs) for the Eclipse Tractus-X SDK. ADRs follow the lightweight format described by [Michael Nygard](http://thinkrelevance.com/blog/2011/11/15/documenting-architecture-decisions).

## Index

| ADR | Title | Status | Date |
|-----|-------|--------|------|
| [ADR-0001](../contributing/architectural-decisions/0001-record-architecture-decisions.md) | Record Architecture Decisions | Accepted | 2025-02-20 |
| [ADR-0002](../contributing/architectural-decisions/0002-data-storage-architecture.md) | Data Storage Architecture | Accepted | 2025-02-20 |
| [ADR-0003](../contributing/architectural-decisions/0003-sdk-module-architecture.md) | SDK Module Architecture | Accepted | 2025-03-31 |
| [ADR-0004](../contributing/architectural-decisions/0004-tractusx-sdk-services.md) | Tractus-X SDK Services (separate repo) | Accepted | 2025-05-12 |

## Summaries

### ADR-0001 — Record Architecture Decisions

We use Architecture Decision Records to document all significant architectural choices made in this project. This ADR establishes the ADR format and toolset.

### ADR-0002 — Data Storage Architecture

The SDK defaults to an **in-memory cache** for EDR connection state. Optional persistent managers (`FileSystemConnectionManager`, `PostgresConnectionManager`) are shipped for deployments that require durability. All business-domain storage remains the responsibility of consuming applications. This keeps the SDK technology-agnostic while offering flexibility for production use cases.

### ADR-0003 — SDK Module Architecture

The SDK adopts a **modular directory structure** with `adapters`, `controllers`, `managers`, `models`, `services`, and `tools` modules. Version-specific implementations are isolated in submodules (e.g., `adapters/connector/jupiter/`). A **Factory Pattern** manages version resolution at runtime.

### ADR-0004 — Tractus-X SDK Services (Separate Repository)

Deployable microservices that use the SDK are maintained in [tractusx-sdk-services](https://github.com/eclipse-tractusx/tractusx-sdk-services), not in this repository. This keeps the SDK as a pure library and avoids coupling it to deployment infrastructure.

## Adding New ADRs

To record a new architectural decision:

1. Create a new file in `docs/contributing/architectural-decisions/` named `NNNN-short-title.md`
2. Follow the format established in ADR-0001 (Context / Decision / Consequences)
3. Add an entry to the table above

## NOTICE

This work is licensed under the [CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/legalcode).

- SPDX-License-Identifier: CC-BY-4.0
- SPDX-FileCopyrightText: 2026 Contributors to the Eclipse Foundation
- SPDX-FileCopyrightText: 2026 LKS Next
- Source URL: [https://github.com/eclipse-tractusx/tractusx-sdk](https://github.com/eclipse-tractusx/tractusx-sdk)
