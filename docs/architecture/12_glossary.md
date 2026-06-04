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

# 12. Glossary

| Term | Definition |
|------|-----------|
| **AAS** | Asset Administration Shell — the standardized digital representation of an asset in the Catena-X / IEC 63278 sense. The SDK supports AAS 3.0. |
| **ADR** | Architecture Decision Record — a short document capturing an important architectural decision, its context, and consequences. |
| **BPN** | Business Partner Number — a unique identifier for a legal entity. |
| **BPNL** | Business Partner Number Legal — the BPN variant scoped to the legal entity level (as opposed to BPNS for site or BPNA for address). |
| **CC-BY-4.0** | Creative Commons Attribution 4.0 International — the license applied to all documentation files in this project. |
| **DSP** | Dataspace Protocol — the protocol specification for secure data exchange in dataspaces. The SDK supports DSP pre-2025 (`jupiter`) and DSP 2025-1 (`saturn`). |
| **DTR** | Digital Twin Registry — the central registry for shell descriptors. Consumers query it to discover digital twins by their asset IDs or specific asset IDs. |
| **ECA** | Eclipse Contributor Agreement — the legal agreement all contributors to Eclipse Foundation projects must sign before their contributions can be accepted. |
| **EDC** | Eclipse Data Connector (previously Eclipse Dataspace Connector) — the sovereign data exchange connector used in the Tractus-X ecosystem. |
| **EDR** | Endpoint Data Reference — a short-lived token and endpoint URL issued by an EDC after a successful contract negotiation. Used to access the actual data plane. |
| **EIP** | Eclipse IP Policy — the intellectual property policy governing third-party content in Eclipse Foundation projects. |
| **Factory Pattern** | A creational design pattern where a factory class decides which concrete implementation to instantiate, based on input parameters. Used in the SDK to select version-specific service implementations. |
| **IAM** | Identity and Access Management — in the Tractus-X context, typically a Keycloak instance provided by the Portal IAM component. |
| **JSON-LD** | JSON for Linked Data — a method of encoding linked data using JSON. Used in EDC catalog responses and AAS submodel contexts. |
| **Jupiter** | The SDK internal name for the dataspace version supporting EDC v0.8.x–v0.10.x (DSP pre-2025). |
| **Keycloak** | An open-source identity and access management solution used as the IAM/IDP in deployments. |
| **OIDC** | OpenID Connect — an authentication layer on top of OAuth 2.0 used by Keycloak and the Portal IAM. |
| **PyPI** | Python Package Index — the official repository for Python packages. The SDK is published at [https://pypi.org/project/tractusx-sdk/](https://pypi.org/project/tractusx-sdk/). |
| **Pydantic** | A Python data validation library used by the SDK for all data models. Provides type-safe serialization, deserialization, and validation. |
| **SAMM** | Semantic Aspect Meta Model — the modeling language used to define semantic models (aspect models) in the semantic layer. |
| **Saturn** | The SDK internal name for the dataspace version supporting EDC v0.11.x+ (DSP 2025-1). |
| **SDK** | Software Development Kit — in this context, the `tractusx-sdk` Python package. |
| **SPDX** | Software Package Data Exchange — a standard for communicating software bill of materials, including license and copyright information. |
| **TCK** | Technology Compatibility Kit — a test suite that verifies an EDC connector's conformance with the Tractus-X protocol specifications. |
| **Tractus-X** | Eclipse Tractus-X — the open source project within the Eclipse Foundation that builds the reference implementation for the Catena-X dataspace. |
| **arc42** | A pragmatic template for software architecture documentation, available at [arc42.org](https://arc42.org/). Used as the documentation structure for this project per TRG 1.05. |

## NOTICE

This work is licensed under the [CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/legalcode).

- SPDX-License-Identifier: CC-BY-4.0
- SPDX-FileCopyrightText: 2026 Contributors to the Eclipse Foundation
- SPDX-FileCopyrightText: 2026 LKS Next
- Source URL: [https://github.com/eclipse-tractusx/tractusx-sdk](https://github.com/eclipse-tractusx/tractusx-sdk)
