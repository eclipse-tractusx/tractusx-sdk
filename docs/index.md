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

Welcome to the **Eclipse Tractus-X Software Development Kit (SDK)** - your gateway to building powerful dataspace applications and services.

[![Contributors][contributors-shield]][contributors-url]
[![Stargazers][stars-shield]][stars-url]
[![Code License][license-shield]][license-url-code]
[![Non-Code License][license-shield-non-code]][license-url-non-code]
[![Latest Release][release-shield]][release-url]
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
[aas-spec-url]: https://admin-shell.io/aas/API/3/0/

## Overview of the SDK

The Tractus-X SDK is a modular Python library that provides simplified APIs and methods for interacting with dataspace infrastructure. It serves as a comprehensive toolkit for both **providing** and **consuming** data in the Tractus-X ecosystem.

### Key Features

- **🔌 Connector Integration** - Seamless interaction with Eclipse Dataspace Connectors (EDC)
- **🏭 Industry Standards** - Built-in support for industry-specific data models and standards
- **🔍 Data Discovery** - Easy exploration and discovery of available datasets
- **🛡️ Secure Access** - Automated authentication and policy management
- **📦 Modular Design** - Use only the components you need
- **🚀 Quick Start** - Get up and running in minutes with our tutorials

## Purpose and Goals

The Tractus-X SDK aims to:

- **Simplify Integration** - Provide easy-to-use abstractions over complex dataspace protocols
- **Accelerate Development** - Offer pre-built components for common dataspace operations  
- **Ensure Compatibility** - Maintain compatibility with evolving dataspace standards
- **Enable Innovation** - Provide a solid foundation for building custom dataspace applications
- **Foster Adoption** - Lower the barrier to entry for dataspace participation

### Based on Eclipse Tractus-X KITs

This SDK implements and extends functionality from official Eclipse Tractus-X KITs:

- [Connector KIT](https://eclipse-tractusx.github.io/docs-kits/category/connector-kit) - EDC connector patterns
- [Digital Twin KIT](https://eclipse-tractusx.github.io/docs-kits/category/digital-twin-kit) - Digital Twin Registry integration
- [Industry Core KIT](https://eclipse-tractusx.github.io/docs-kits/category/industry-core-kit) - Core industry data models

## Target Audience

This SDK is designed for:

### 🧑‍💻 **Developers**
- Building dataspace-enabled applications
- Integrating existing systems with Tractus-X
- Creating microservices for data exchange

### 🏢 **Organizations**
- Companies joining the Tractus-X dataspace
- System integrators implementing dataspace solutions
- Technology vendors building on Tractus-X standards

### 🎓 **Researchers & Students**
- Learning about dataspace technologies
- Experimenting with secure data exchange
- Building proof-of-concept applications

### 📊 **Data Engineers**
- Managing data assets and catalogs
- Implementing data governance policies
- Building data pipelines with dataspace sources

## Quick Links and Resources

### 🚀 **Getting Started**
- [Installation Guide](tutorials/getting-started.md) - Set up your development environment
- [First step: Creation of an asset](tutorials/getting-started.md) - Build your first dataspace application

### 📚 **Core Concepts**
- [Dataspace Library](core-concepts/dataspace-concepts/index.md) - Core connector services and Eclipse Tractus-X Connector integration
- [Industry Library](core-concepts/industry-concepts/index.md) - Digital Twin Registry and Submodel Server integration
- [Extension Library](api-reference/extension-library/semantics/semantics.md) - Use case-specific extensions and add-on functionality

### 🛠️ **Development**
- [GitHub Repository](https://github.com/eclipse-tractusx/tractusx-sdk) - Source code and issues
- [PyPI Package](https://pypi.org/project/tractusx-sdk/) - Latest releases
- [Changelog](https://github.com/eclipse-tractusx/tractusx-sdk/blob/main/CHANGELOG.md) - Version history

### 🤝 **Community**
- [Discussions](https://github.com/eclipse-tractusx/tractusx-sdk/discussions) - Ask questions and share ideas
- [Contributing Guidelines](https://github.com/eclipse-tractusx/tractusx-sdk/blob/main/CONTRIBUTING.md) - How to contribute
- [Community Meetings](https://eclipse-tractusx.github.io/community/open-meetings#Industry%20Core%20Hub%20&%20Tractus-X%20SDK%20Weekly) - Weekly developer meetings

### 📖 **Additional Resources**
- [Eclipse Tractus-X](https://eclipse-tractusx.github.io/) - Official project website
- [Tractus-X KITs](https://eclipse-tractusx.github.io/Kits) - Standard specifications

---

!!! tip "New to Dataspace Technology?"
    Start with our [Getting Started Guide](tutorials/getting-started.md) to learn the basics of dataspace interaction in just 10 minutes!

!!! info "Version Information"
    **Current Version:** 0.5.0  
    **Python Support:** 3.12+  
    **License:** Apache 2.0 (Code) / CC-BY-4.0 (Documentation)

## NOTICE

This work is licensed under the [CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/legalcode).

- SPDX-License-Identifier: CC-BY-4.0
- SPDX-FileCopyrightText: 2025 Contributors to the Eclipse Foundation
- Source URL: https://github.com/eclipse-tractusx/tractusx-sdk
