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

# 1. Introduction and Goals

## Purpose

The **Eclipse Tractus-X SDK** is a Python-based software development kit that simplifies building dataspace-native applications, scripts, pipelines, and AI models. It abstracts the complexity of dataspace protocols and provides high-level, Pythonic APIs for common operations within the Eclipse Tractus-X ecosystem.

The SDK targets developers building:

- Data providers and consumers in the Dataspace network
- Digital twin solutions using the Asset Administration Shell (AAS)
- Supply chain transparency and traceability applications
- AI/ML pipelines consuming data from sovereign dataspaces
- Any application that needs to integrate with Eclipse Data Space Connector (EDC) or the Digital Twin Registry (DTR)

## Key Features

| Feature | Description |
|---------|-------------|
| **Dataspace Integration** | Seamless integration with EDC connectors and DSP dataspace protocols |
| **Industry Standards** | Support for use cases, AAS 3.0, SAMM semantic models |
| **Multi-Version Support** | Side-by-side support for EDC `jupiter` (v0.8.x–v0.10.x) and `saturn` (v0.11.x, DSP 2025-1) |
| **Extensible Architecture** | Modular design allowing custom extensions via the Extensions Library |
| **Developer-Friendly** | Pythonic APIs with type hints, auto-completion, and comprehensive examples |
| **Production-Ready** | Battle-tested components with built-in authentication, error handling, and retry logic |

## Quality Goals

The following quality goals drive the major architectural decisions, ordered by priority:

| Priority | Quality Goal | Scenario |
|----------|-------------|----------|
| 1 | **Correctness** | SDK operations produce results compliant with EDC and Dataspace specifications |
| 2 | **Backward Compatibility** | New minor versions do not break existing consumer code |
| 3 | **Usability** | A developer unfamiliar with EDC can execute a catalog query within 15 minutes using the getting-started guide |
| 4 | **Testability** | All public SDK methods are covered by automated tests; CI enforces coverage on every pull request |
| 5 | **Extensibility** | New EDC versions or industry use cases can be added without modifying existing stable code |

## Stakeholders

| Stakeholder | Role | Expectations |
|------------|------|-------------|
| Application Developers | Consume the SDK in their applications | Stable, documented, easy-to-use APIs |
| SDK Contributors | Extend or fix the SDK | Clear architecture, ADRs, contribution guidelines |
| Industry Core Hub Team | Primary SDK consumer project | Reliable support for DTR, EDC, and AAS operations |
| Eclipse Tractus-X Community | Governance and review | Eclipse IP compliance, open source best practices |

## NOTICE

This work is licensed under the [CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/legalcode).

- SPDX-License-Identifier: CC-BY-4.0
- SPDX-FileCopyrightText: 2026 Contributors to the Eclipse Foundation
- SPDX-FileCopyrightText: 2026 LKS Next
- Source URL: [https://github.com/eclipse-tractusx/tractusx-sdk](https://github.com/eclipse-tractusx/tractusx-sdk)
