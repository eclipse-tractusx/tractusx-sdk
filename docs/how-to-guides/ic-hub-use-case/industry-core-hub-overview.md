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
# Industry Core Hub Use Case

The [Industry Core Hub](https://github.com/eclipse-tractusx/industry-core-hub) is a **lighthouse implementation** that demonstrates how to build a semi production-ready (incubating state) application using the Eclipse Tractus-X SDK. It serves as a reference architecture and practical example for organizations joining dataspaces built with Eclipse Tractus-X technologies.

## Overview

The Industry Core Hub showcases the complete SDK capabilities in a real-world application context:

- **Data Provision & Consumption** - Full end-to-end dataspace workflows
- **Digital Twin Management** - AAS 3.0 compliant Digital Twin Registry integration
- **Connector Integration** - Automated EDC asset creation and policy management
- **Microservices Architecture** - Modular backend services with SDK libraries
- **Web-Based UI** - Modern frontend consuming SDK-powered APIs

## Architecture

The Industry Core Hub is built on a **modular microservices architecture** that separates concerns and demonstrates best practices for SDK adoption:

### Backend Services

The [IC-Hub Backend](https://github.com/eclipse-tractusx/industry-core-hub/tree/main/ichub-backend) demonstrates how to use the SDK's dataspace and industry libraries in your application:

**Key Components:**

- **Dataspace Foundation** - Uses `tractusx_sdk.dataspace` for EDC connector operations
- **Industry Foundation** - Uses `tractusx_sdk.industry` for Digital Twin Registry and AAS management
- **Connection Management** - Implements PostgreSQL-backed connection managers for production use
- **API Layer** - Exposes RESTful APIs built on top of SDK services

**Example SDK Usage in Backend:**

```python
from tractusx_sdk.dataspace.services.connector import ServiceFactory
from tractusx_sdk.industry.services import AasService

# Connector service for data exchange
connector_service = ServiceFactory.get_connector_service(
    dataspace_version="saturn",
    base_url=config.connector_url,
    dma_path="/management",
    headers={"X-Api-Key": config.api_key},
    connection_manager=postgres_connection_manager,
)

# AAS service for Digital Twin management
aas_service = AasService(
    base_url=config.dtr_url,
    api_path="/api/v3",
)
```

### Frontend Application

The [IC-Hub Frontend](https://github.com/eclipse-tractusx/industry-core-hub/tree/main/ichub-frontend) demonstrates how to build a user interface that consumes SDK-powered backend APIs:

**Key Features:**

- Asset catalog browsing and search
- Digital Twin shell descriptor creation and management
- Contract negotiation workflow visualization
- Data transfer monitoring and access
- Policy configuration and compliance checking

## Use Case Extensions

The Industry Core Hub architecture is designed to support **use case add-ons** - domain-specific extensions that leverage the SDK foundation:

- **Digital Product Passport (DPP)** - Product lifecycle data exchange
- **PCF (Product Carbon Footprint)** - Carbon emissions tracking
- **Demand & Capacity Management** - Supply chain visibility
- **Quality Data Exchange** - Quality metrics and alerts

Each add-on is built as a separate module that uses the shared SDK libraries provided by the core platform.

## How the IC Hub Uses the SDK

### 1. Data Provision Workflow

```python
# Create an asset in the EDC
connector_service.provider.create_asset(
    asset_id="part-12345-data",
    base_url="https://backend.example.com/data",
    dct_type="cx-taxo:SubmodelBundle",
    version="3.0",
    semantic_id="urn:samm:io.catenax.part_type_information:1.0.0#PartTypeInformation",
    headers={"X-Api-Key": backend_api_key},
)

# Create access policy
policy_id = connector_service.provider.create_policy(
    policy_id="bpn-policy-001",
    permissions=[{
        "action": "access",
        "constraint": {
            "leftOperand": "BusinessPartnerNumber",
            "operator": "isAnyOf",
            "rightOperand": "BPNL00000003CRHK",
        },
    }],
)

# Create contract definition
connector_service.provider.create_contract_definition(
    contract_definition_id="contract-001",
    access_policy_id=policy_id,
    contract_policy_id=policy_id,
    assets_selector=[{"@id": "part-12345-data"}],
)
```

### 2. Data Consumption Workflow

```python
# Discover and consume data (Saturn with BPNL discovery)
response = connector_service.consumer.do_get_with_bpnl(
    bpnl="BPNL00000003AYRE",
    filter_expression=[connector_service.consumer.get_filter_expression(
        key="https://w3id.org/edc/v0.0.1/ns/id",
        value="part-12345-data",
    )],
    path="/shell-descriptors",
)

data = response.json()
```

### 3. Digital Twin Management

```python
from tractusx_sdk.industry.models.aas.v3 import ShellDescriptor, MultiLanguage, SpecificAssetId

# Create a shell descriptor
shell = ShellDescriptor(
    id="urn:uuid:550e8400-e29b-41d4-a716-446655440000",
    idShort="BatteryShell001",
    displayName=[MultiLanguage(language="en", text="Battery Component")],
    assetKind="Instance",
    globalAssetId="urn:uuid:battery-global-id",
    specificAssetIds=[
        SpecificAssetId(
            name="manufacturerPartId",
            value="BAT-12345-ABC",
        ),
    ],
)

aas_service.create_asset_administration_shell_descriptor(shell)
```

## Getting Started with IC Hub

### Installation

```bash
# Clone the repository
git clone https://github.com/eclipse-tractusx/industry-core-hub.git
cd industry-core-hub

# Install backend dependencies
cd ichub-backend
pip install tractusx-sdk
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your connector URLs, API keys, BPNs

# Run the backend
python main.py
```

### Configuration

The IC Hub requires configuration for:

- **EDC Connector** - Provider and/or Consumer EDC endpoints
- **Digital Twin Registry** - DTR API endpoint
- **Discovery Services** - Discovery Finder, BPN Discovery, Connector Discovery
- **Connection Manager** - Database connection for EDR caching (postgresql database deployed via helm charts)

See the [IC Hub Deployment Configuration](https://github.com/eclipse-tractusx/industry-core-hub/blob/main/charts/industry-core-hub/README.md) for detailed setup instructions.

## Key Learnings from IC Hub

!!! tip "Semi Production Best Practices"
    The Industry Core Hub demonstrates several semi production-ready patterns:
    
    - **PostgreSQL Connection Manager** for persistent EDR caching
    - **Error handling and retry logic** for connector operations
    - **Logging and observability** with structured logs
    - **Configuration management** with environment variables and secrets
    - **API versioning** for backward compatibility

!!! info "Extensibility"
    The IC Hub architecture is designed to be extended:
    - Add new use case modules without modifying core services
    - Plug in custom connection managers or discovery adapters
    - Override SDK defaults with application-specific behavior
    - Integrate with existing enterprise systems via API layer

## Resources

- **Repository:** [github.com/eclipse-tractusx/industry-core-hub](https://github.com/eclipse-tractusx/industry-core-hub)
- **Documentation:** [IC-Hub Docs](https://github.com/eclipse-tractusx/industry-core-hub/tree/main/docs)
- **Architecture Decisions:** [ADRs](https://github.com/eclipse-tractusx/industry-core-hub/tree/main/docs/architecture/decision-records)
- **Deployment Guide:** [Kubernetes Deployment](https://github.com/eclipse-tractusx/industry-core-hub/blob/main/charts/industry-core-hub/README.md)

## Community

Join the weekly Industry Core Hub & Tractus-X SDK meetings to discuss use cases, share feedback, and collaborate:

- **Meeting Link:** [Open Meetings Calendar](https://eclipse-tractusx.github.io/community/open-meetings#Industry%20Core%20Hub%20&%20Tractus-X%20SDK%20Weekly)
- **Matrix Chat (shared with IC-Hub):** [#tractusx-industry-core-hub:matrix.eclipse.org](https://matrix.to/#/#tractusx-industry-core-hub:matrix.eclipse.org)
- **GitHub Discussions:** [SDK Discussions](https://github.com/eclipse-tractusx/tractusx-sdk/discussions)

---

## NOTICE

This work is licensed under the [CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/legalcode).

- SPDX-License-Identifier: CC-BY-4.0
- SPDX-FileCopyrightText: 2025, 2026 Contributors to the Eclipse Foundation
- SPDX-FileCopyrightText: 2025, 2026 Catena-X Automotive Network e.V.
- SPDX-FileCopyrightText: 2025, 2026 LKS Next
- SPDX-FileCopyrightText: 2025, 2026 Mondragon Unibertsitatea
- Source URL: [https://github.com/eclipse-tractusx/tractusx-sdk](https://github.com/eclipse-tractusx/tractusx-sdk)
