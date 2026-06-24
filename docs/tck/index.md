<!--
Eclipse Tractus-X - Tractus-X SDK

Copyright (c) 2026 Catena-X Automotive Network e.V.
Copyright (c) 2026 Contributors to the Eclipse Foundation

See the NOTICE file(s) distributed with this work for additional
information regarding copyright ownership.

This program and the accompanying materials are made available under the
terms of the Apache License, Version 2.0 which is available at
https://www.apache.org/licenses/LICENSE-2.0.

SPDX-License-Identifier: Apache-2.0
-->

# Test Compatibility Kit (TCK)

The **Test Compatibility Kit (TCK)** provides end-to-end (E2E) testing scripts that validate EDC implementations against the Tractus-X SDK. They ensure that the complete data exchange flow works correctly — from provider data provision through consumer data consumption — across multiple protocol versions.

## Available TCK Suites

| Suite | Target | Versions | Status |
|-------|--------|--------|--------|
| [Connector TCK](connector/index.md) | [Eclipse Tractus-X Dataspace Connector (TX-EDC)](https://github.com/eclipse-tractusx/tractusx-edc) | `jupiter` (< 0.10.0) <br> `saturn` (>0.11.0) | Available |

## What the TCK Validates

- **Management API Compatibility** — Asset, Policy, and Contract Definition creation
- **DSP Protocol Compliance** — Catalog requests, contract negotiation, transfer processes
- **ODRL Policy Enforcement** — BPN-based access control, framework agreements, usage policies
- **Verifiable Credentials** — Proper dataspace onboarding and credential validation
- **EDR Token Flow** — Endpoint Data Reference generation and authenticated data access
- **JSON-LD Context Handling** — Semantic web standards across protocol versions
- **SDK Service Layer** — Provider and Consumer service initialization and operations

## Quick Links

- [Connector TCK Overview](connector/index.md)
- [Configuration Reference](connector/configuration.md)
- [Running Tests](connector/running-tests.md)
- [Interpreting Results](connector/interpreting-results.md)

## Demo

<video controls width="100%" style="border-radius: 8px; margin: 1rem 0;">
  <source src="../assets/videos/tck-demo.mov" type="video/mp4">
  Your browser does not support the video tag. Download the demo:
  <a href="../assets/videos/tck-demo.mov">tck-demo.mov</a>
</video>

## Source

TCK scripts are located in the [`tck/connector/`](https://github.com/eclipse-tractusx/tractusx-sdk/tree/main/tck/connector) directory of the repository.

---

!!! note
    TCK tests require both Provider and Consumer organizations to be properly onboarded in the Catena-X dataspace with valid Verifiable Credentials that satisfy all policy constraints being tested.

## NOTICE

This work is licensed under the [CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/legalcode).

- SPDX-License-Identifier: CC-BY-4.0
- SPDX-FileCopyrightText: 2025, 2026 Contributors to the Eclipse Foundation
- SPDX-FileCopyrightText: 2025, 2026 Catena-X Automotive Network e.V.
- SPDX-FileCopyrightText: 2025, 2026 LKS Next
- SPDX-FileCopyrightText: 2025, 2026 Mondragon Unibertsitatea
- Source URL: [https://github.com/eclipse-tractusx/tractusx-sdk](https://github.com/eclipse-tractusx/tractusx-sdk)
