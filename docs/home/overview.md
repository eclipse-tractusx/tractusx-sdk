# Overview

The **Eclipse Tractus-X SDK** provides a comprehensive set of tools and libraries for building dataspace native applications/scripts/pipelines/AI Models.

## What is Tractus-X SDK?

Tractus-X SDK is a Python-based software development kit that simplifies the development of applications interacting with the Eclipse Tractus-X components. It abstracts the complexity of dataspace protocols and provides high-level APIs for common operations.

## Key Features

- **Dataspace Integration**: Seamless integration with EDC connectors and dataspace protocols
- **Industry Standards**: Support for Catena-X standards and semantic models
- **Extensible Architecture**: Modular design allowing custom extensions
- **Developer-Friendly**: Pythonic APIs with comprehensive documentation
- **Production-Ready**: Battle-tested components used in real-world deployments

## Architecture

The SDK is organized into three main libraries:

### Dataspace Library
Handles core dataspace operations including:
- EDC connector integration
- Discovery services
- Asset management
- Contract negotiation
- Data transfer

### Industry Library
Provides industry-specific functionality:
- Digital Twin Registry (DTR) integration
- Submodel server capabilities
- BPN Discovery services
- AAS (Asset Administration Shell) support

### Extension Library
Offers additional capabilities:
- Semantic data handling
- Notification APIs
- Custom protocol support

## Use Cases

The Tractus-X SDK is ideal for:

- Building data providers and consumers in the Catena-X network
- Implementing digital twin solutions
- Creating supply chain transparency applications
- Developing traceability and sustainability tracking systems
- Integrating existing systems with Catena-X dataspaces

## Experimental Features

### AI & Machine Federated Learning Integration

Want to train models with dataspace data? The SDK supports experimental AI/ML workflows that let you fetch data from connectors and use it with frameworks like TensorFlow. The idea is to create industrial grade AI models by using the power of private, secure and soverign data sharing in a dataspace.

**Note**: These features aren't part of the official Catena-X standard yet and are not described as a KIT. There is already an [AI Service KIT](https://eclipse-tractusx.github.io/docs-kits/next/kits/ai-service-kit/adoption-view) which uses agents for data exchange, and explains how AI can be boosted via dataspaces. They're custom implementations to help you explore AI possibilities with dataspace data. Make sure to check compliance requirements before using them in production.

Learn more in the [AI/TensorFlow Integration Tutorial](../tutorials/ai-tensorflow-integration.md).

## Getting Started

Ready to start building? Check out our [Quick Start](quick-start.md) guide or explore the [Tutorials](../tutorials/getting-started.md) section.

## NOTICE

This work is licensed under the [CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/legalcode).

- SPDX-License-Identifier: CC-BY-4.0
- SPDX-FileCopyrightText: 2025, 2026 Contributors to the Eclipse Foundation
- SPDX-FileCopyrightText: 2025, 2026 Catena-X Automotive Network e.V.
- SPDX-FileCopyrightText: 2025, 2026 LKS Next
- SPDX-FileCopyrightText: 2025, 2026 Mondragon Unibertsitatea
- Source URL: [https://github.com/eclipse-tractusx/tractusx-sdk](https://github.com/eclipse-tractusx/tractusx-sdk)