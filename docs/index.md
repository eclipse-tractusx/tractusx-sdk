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
# Eclipse Tractus-X SDK Documentation

Welcome to the **Eclipse Tractus-X Software Development Kit (SDK)** - your gateway to building powerful dataspace native applications, services and AI models.

[![Contributors][contributors-shield]][contributors-url]
[![Stargazers][stars-shield]][stars-url]
[![Code License][license-shield]][license-url-code]
[![Non-Code License][license-shield-non-code]][license-url-non-code]
[![Latest Release][release-shield]][release-url]
[![PyPI Version][pypi-version-shield]][pypi-url]
[![Python Versions][pypi-python-shield]][pypi-url]
[![AAS 3.0 Compliant](https://img.shields.io/badge/AAS-3.0-blue?style=for-the-badge)][aas-spec-url]

<!-- Reference Links -->
[contributors-shield]: https://img.shields.io/github/contributors/eclipse-tractusx/tractusx-sdk.svg?style=for-the-badge
[contributors-url]: https://github.com/eclipse-tractusx/tractusx-sdk/graphs/contributors
[stars-shield]: https://img.shields.io/github/stars/eclipse-tractusx/tractusx-sdk.svg?style=for-the-badge
[stars-url]: https://github.com/eclipse-tractusx/tractusx-sdk/stargazers
[license-shield]: https://img.shields.io/github/license/eclipse-tractusx/tractusx-sdk.svg?style=for-the-badge
[license-url-code]: https://github.com/eclipse-tractusx/tractusx-sdk/blob/main/LICENSE
[license-shield-non-code]: https://img.shields.io/badge/NON--CODE%20LICENSE-CC--BY--4.0-8A2BE2?style=for-the-badge
[license-url-non-code]: https://github.com/eclipse-tractusx/tractusx-sdk/blob/main/LICENSE_non-code
[release-shield]: https://img.shields.io/github/v/release/eclipse-tractusx/tractusx-sdk.svg?style=for-the-badge
[release-url]: https://github.com/eclipse-tractusx/tractusx-sdk/releases
[pypi-version-shield]: https://img.shields.io/pypi/v/tractusx-sdk?style=for-the-badge&label=PyPI
[pypi-python-shield]: https://img.shields.io/pypi/pyversions/tractusx-sdk?style=for-the-badge
[pypi-url]: https://pypi.org/project/tractusx-sdk/
[aas-spec-url]: https://admin-shell.io/aas/API/3/0/

## Installation

The Tractus-X SDK is published on [PyPI](https://pypi.org/project/tractusx-sdk/) and requires **Python 3.12 or later**.

### Basic Installation

```bash
pip install tractusx-sdk
```

### Install a Specific Version

```bash
pip install tractusx-sdk==0.7.0rc1
```

### Verify the Installation

```python
import tractusx_sdk
print(tractusx_sdk.__version__)
```

The package index is available at [https://pypi.org/project/tractusx-sdk/](https://pypi.org/project/tractusx-sdk/).

> **Note:** It is strongly recommended to install the SDK inside a virtual environment (`venv`, `conda`, or similar) to avoid dependency conflicts.

```bash
# Create and activate a virtual environment
python3.12 -m venv .venv
source .venv/bin/activate      # macOS / Linux
.venv\Scripts\activate         # Windows

# Then install the SDK
pip install tractusx-sdk
```

---

## What is this SDK?

The Tractus-X SDK is a Python library that makes it easier to work with dataspaces. Think of it as a toolbox that handles the complicated parts of sharing and accessing data in the Tractus-X network, so you can focus on building your application.

Whether you're sharing data with partners or pulling data from providers, this SDK handles the connector setup, authentication, policies, and all the protocol details for you.

### What you get

- Work with Eclipse Dataspace Connectors without dealing with low-level APIs
- Built-in support for industry data models (parts, batteries, digital twins, etc.)
- Discover what data is available across the network
- Handle authentication and access policies automatically
- Pick only the parts you need - it's modular
- Get started fast with ready-to-run examples

## Why we built this

Working with dataspaces involves a lot of moving parts: connectors, registries, discovery services, policies, negotiations. Each component has its own API, version quirks, and protocol requirements.

We built this SDK to hide that complexity. It gives you simple Python methods that work across different EDC versions, handles backward compatibility automatically, and follows the patterns recommended by Tractus-X KITs.

The goal is simple: make it easy to join the dataspace without being a dataspace expert.

### Based on Tractus-X KITs

The SDK implements the official Tractus-X standards:

- [Connector KIT](https://eclipse-tractusx.github.io/docs-kits/category/connector-kit) - working with EDC connectors
- [Digital Twin KIT](https://eclipse-tractusx.github.io/docs-kits/category/digital-twin-kit) - digital twins and registries
- [Industry Core KIT](https://eclipse-tractusx.github.io/docs-kits/category/industry-core-kit) - industry data models

## Who is this for?

### Developers
You're building apps that need to share or access data in Tractus-X. Maybe you're connecting an existing system, building a new microservice, or just experimenting with dataspace tech.

### Companies and integrators
Your organization is joining Tractus-X, or you're implementing dataspace solutions for clients. You need something that works now and won't break when standards evolve.

### Students and researchers
You're learning about dataspaces, running experiments, or building proofs of concept. The SDK lets you focus on your ideas instead of wrestling with connector APIs.

### Data teams
You manage data catalogs, build data pipelines, or implement governance policies. The SDK gives you programmatic access to the whole dataspace infrastructure.

## Quick Links

### Getting Started
- [Installation Guide](tutorials/getting-started.md) - Set up your development environment
- [Create Your First Asset](tutorials/getting-started.md) - Start sharing data in minutes

### Learn the Concepts
- [Dataspace Library](core-concepts/dataspace-concepts/index.md) - Working with connectors and the EDC
- [Industry Library](core-concepts/industry-concepts/index.md) - Digital Twin Registry and submodel servers
- [Extension Library](api-reference/extension-library/semantics/semantics.md) - Use case-specific add-ons
- [Backward Compatibility Guide](how-to-guides/backward-compatibility.md) - Migrating between Jupiter and Saturn, handling different EDC versions

### Code and Community
- [GitHub Repository](https://github.com/eclipse-tractusx/tractusx-sdk) - Source code, issues, and discussions
- [PyPI Package](https://pypi.org/project/tractusx-sdk/) - Install via pip
- [Changelog](https://github.com/eclipse-tractusx/tractusx-sdk/blob/main/CHANGELOG.md) - What's new in each release
- [Contributing Guidelines](https://github.com/eclipse-tractusx/tractusx-sdk/blob/main/CONTRIBUTING.md) - How to contribute
- [Weekly Meetings](https://eclipse-tractusx.github.io/community/open-meetings#Industry%20Core%20Hub%20&%20Tractus-X%20SDK%20Weekly) - Join the developer community

### More Resources
- [Eclipse Tractus-X](https://eclipse-tractusx.github.io/) - Main project website
- [Tractus-X KITs](https://eclipse-tractusx.github.io/Kits) - Official specifications and standards

---

!!! tip "New to dataspaces?"
    Check out the [Getting Started Guide](tutorials/getting-started.md) - it takes about 10 minutes and shows you how the whole thing works.

!!! info "Current release: 0.7.1"
    Requires Python 3.12+  
    License: Apache 2.0 (code) / CC-BY-4.0 (docs)

## NOTICE

This work is licensed under the [CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/legalcode).

- SPDX-License-Identifier: CC-BY-4.0
- SPDX-FileCopyrightText: 2025, 2026 Contributors to the Eclipse Foundation
- SPDX-FileCopyrightText: 2025, 2026 Catena-X Automotive Network e.V.
- SPDX-FileCopyrightText: 2025, 2026 LKS Next
- SPDX-FileCopyrightText: 2025, 2026 Mondragon Unibertsitatea
- Source URL: [https://github.com/eclipse-tractusx/tractusx-sdk](https://github.com/eclipse-tractusx/tractusx-sdk)
