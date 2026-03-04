<!--

Eclipse Tractus-X - Software Development KIT

Copyright (c) 2025 LKS Next
Copyright (c) 2025 Mondragon Unibertsitatea
Copyright (c) 2025 Contributors to the Eclipse Foundation

See the NOTICE file(s) distributed with this work for additional
information regarding copyright ownership.

This work is made available under the terms of the
Creative Commons Attribution 4.0 International (CC-BY-4.0) license,
which is available at
https://creativecommons.org/licenses/by/4.0/legalcode.

SPDX-License-Identifier: CC-BY-4.0

-->
# Other Use Cases & Applications

The Tractus-X SDK is used across multiple projects in the Eclipse Tractus-X ecosystem. This page provides an overview of repositories and applications that leverage the SDK for dataspace interactions.

## Applications Using the SDK

The following table lists all known projects and applications built with the Tractus-X SDK:

| Project | Description | Repository | SDK Usage |
|---------|-------------|------------|----------|
| **Industry Core Hub** | Lighthouse implementation for production dataspace applications. Provides backend services and frontend UI demonstrating full SDK capabilities. | [eclipse-tractusx/industry-core-hub](https://github.com/eclipse-tractusx/industry-core-hub) | Dataspace Library, Industry Library, Extensions |
| **IC Hub Backend** | Backend microservices using SDK dataspace and industry libraries for connector integration, DTR management, and data exchange. | [industry-core-hub/ichub-backend](https://github.com/eclipse-tractusx/industry-core-hub/tree/main/ichub-backend) | `tractusx_sdk.dataspace`, `tractusx_sdk.industry` |
| **IC Hub Frontend** | Web-based UI consuming SDK-powered APIs for asset management, contract negotiation, and Digital Twin operations. | [industry-core-hub/ichub-frontend](https://github.com/eclipse-tractusx/industry-core-hub/tree/main/ichub-frontend) | Via Backend APIs |
| **Tractus-X SDK Services** | Reusable microservices built with the SDK, available as standalone services or embedded in applications. | [eclipse-tractusx/tractusx-sdk-services](https://github.com/eclipse-tractusx/tractusx-sdk-services) | Full SDK |
| **DT Pull Service** | Service that automatically discovers and pulls Digital Twin shell descriptors from data providers using SDK connectors. | [tractusx-sdk-services/dt-pull-service](https://github.com/eclipse-tractusx/tractusx-sdk-services) | Industry Library, Dataspace Library |
| **Test Orchestrator** | Test agent service that validates data provision configurations for compliance with standard schemas and syntax. | [tractusx-sdk-services/test-orchestrator](https://github.com/eclipse-tractusx/tractusx-sdk-services) | Dataspace Library, Extensions (TCK) |
| **Tractus-X AAS Suite** | Integration project combining the Tractus-X SDK (EDC connector client) with the BaSyx Python SDK for AAS server implementations. | [eclipse-tractusx/aas-suite](https://github.com/eclipse-tractusx/aas-suite) | Dataspace Library (Connector) |

## SDK Library Usage by Project

### Dataspace Library

Projects using `tractusx_sdk.dataspace` for connector operations:

- ✅ Industry Core Hub Backend
- ✅ DT Pull Service
- ✅ Test Orchestrator
- ✅ Tractus-X AAS Suite

**Key Features Used:**

- Connector service factories (Jupiter/Saturn)
- Connection managers (Postgres, FileSystem, Memory)
- EDC Management API controllers
- Contract negotiation and data transfer
- Discovery services integration

### Industry Library

Projects using `tractusx_sdk.industry` for Digital Twin Registry and AAS operations:

- ✅ Industry Core Hub Backend
- ✅ DT Pull Service

**Key Features Used:**

- AAS 3.0 Shell Descriptor models
- Digital Twin Registry service client
- Submodel descriptor management
- Specific Asset ID handling

### Extensions

Projects using `tractusx_sdk.extensions` for specialized functionality:

- ✅ Test Orchestrator (TCK extension)
- ✅ Industry Core Hub (Notification API extension)

**Key Extensions:**

- **TCK (Test Compliance Kit)** - Connector validation and E2E testing
- **Notification API** - Asynchronous notification handling
- **Semantics** - Semantic model validation and conversion

## Integration Patterns

### Pattern 1: Full-Stack Application (IC Hub)

```
┌─────────────────────────────────────────┐
│         Frontend (React/Vue)            │
│  - Asset Browser                        │
│  - Contract Negotiation UI              │
│  - Digital Twin Explorer                │
└────────────┬────────────────────────────┘
             │ REST APIs
┌────────────▼────────────────────────────┐
│       Backend Services (FastAPI)        │
│  - tractusx_sdk.dataspace               │
│  - tractusx_sdk.industry                │
│  - PostgreSQL Connection Manager        │
└────────────┬────────────────────────────┘
             │
    ┌────────┴─────────┐
    │                  │
┌───▼──────┐    ┌──────▼────────┐
│   EDC    │    │      DTR      │
└──────────┘    └───────────────┘
```

### Pattern 2: Standalone Microservice

```
┌─────────────────────────────────────────┐
│      DT Pull Service (FastAPI)          │
│  - Scheduled data synchronization       │
│  - tractusx_sdk.industry (DTR)          │
│  - tractusx_sdk.dataspace (Connector)   │
└────────────┬────────────────────────────┘
             │
    ┌────────┴─────────┐
    │                  │
┌───▼──────┐    ┌──────▼────────┐
│   EDC    │    │      DTR      │
└──────────┘    └───────────────┘
```

### Pattern 3: SDK as Connector Client (AAS Suite)

```
┌─────────────────────────────────────────┐
│         BaSyx AAS Server                │
│  - AAS registry and data storage        │
│  - Submodel endpoints                   │
└────────────┬────────────────────────────┘
             │ Protected by EDC
┌────────────▼────────────────────────────┐
│    tractusx_sdk.dataspace               │
│  - Asset creation for submodels         │
│  - Policy management                    │
│  - Contract definition creation         │
└────────────┬────────────────────────────┘
             │
         ┌───▼──────┐
         │   EDC    │
         └──────────┘
```

## Use Case Add-ons (Planned)

The following use case-specific extensions are planned or in development:

| Use Case | Status | Description | Target Libraries |
|----------|--------|-------------|------------------|
| **Digital Product Passport** | Planned | Product lifecycle and sustainability data exchange | Industry + Extensions |
| **PCF Exchange** | Planned | Product Carbon Footprint calculation and sharing | Industry + Extensions |
| **Demand & Capacity** | Planned | Supply chain visibility and capacity planning | Dataspace + Extensions |
| **Quality Data Exchange** | Planned | Quality metrics, alerts, and root cause analysis | Dataspace + Extensions |
| **Traceability** | Planned | Part genealogy and supply chain traceability | Industry + Extensions |

## Contributing Your Use Case

Are you building an application with the Tractus-X SDK? We'd love to feature it here!

**To add your project to this list:**

1. Open a [GitHub Discussion](https://github.com/eclipse-tractusx/tractusx-sdk/discussions/new?category=show-and-tell)
2. Provide:
   - Project name and description
   - Repository URL (if open source)
   - Which SDK libraries you're using
   - Key features or use cases
3. Submit a pull request updating this page

**Requirements:**

- Project must use `tractusx-sdk` as a dependency
- Must be actively maintained
- Open source projects preferred (but not required)

## SDK Extension Development

Want to build a reusable extension for the SDK?

See the [Extension Development Guide](../../core-concepts/extensions-concepts/index.md) for:

- Extension structure and conventions
- How to package and distribute extensions
- Testing and validation
- Contribution guidelines

## Resources

- **SDK Repository:** [github.com/eclipse-tractusx/tractusx-sdk](https://github.com/eclipse-tractusx/tractusx-sdk)
- **SDK Services:** [github.com/eclipse-tractusx/tractusx-sdk-services](https://github.com/eclipse-tractusx/tractusx-sdk-services)
- **Industry Core Hub:** [github.com/eclipse-tractusx/industry-core-hub](https://github.com/eclipse-tractusx/industry-core-hub)
- **Community Meetings:** [Open Meetings Calendar](https://eclipse-tractusx.github.io/community/open-meetings#Industry%20Core%20Hub%20&%20Tractus-X%20SDK%20Weekly)

---

## NOTICE

This work is licensed under the [CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/legalcode).

- SPDX-License-Identifier: CC-BY-4.0
- SPDX-FileCopyrightText: 2025, 2026 Contributors to the Eclipse Foundation
- SPDX-FileCopyrightText: 2025, 2026 Catena-X Automotive Network e.V.
- SPDX-FileCopyrightText: 2025, 2026 LKS Next
- SPDX-FileCopyrightText: 2025, 2026 Mondragon Unibertsitatea
- Source URL: [https://github.com/eclipse-tractusx/tractusx-sdk](https://github.com/eclipse-tractusx/tractusx-sdk)
