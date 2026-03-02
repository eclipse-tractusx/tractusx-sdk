<!--

Eclipse Tractus-X - Software Development KIT

Copyright (c) 2026 Mondragon Unibertsitatea
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
# Industry Library API Reference

The Industry Library provides comprehensive APIs for managing digital twins, submodels, and asset administration shells in the Tractus-X ecosystem. This reference documentation covers all services, models, adapters, and utilities available in the Industry Library.

## Overview

The Industry Library enables:

- **Digital Twin Management** - Create, query, and manage Asset Administration Shells (AAS)
- **Submodel Operations** - Handle submodel descriptors and data storage
- **Business Partner Discovery** - Locate BPNs for assets using various identifiers
- **Extensible Storage** - Pluggable adapters for different storage backends

## API Components

### Digital Twin Registry (DTR)

Interact with the Digital Twin Registry to manage shell and submodel descriptors.

#### Services
- **[AAS Service](dtr/services.md)** - Core service for Digital Twin Registry operations
  - Shell descriptor CRUD operations
  - Submodel descriptor management
  - Asset ID lookup and linking
  - Pagination and filtering

#### Models
- **[DTR Models](dtr/models.md)** - AAS 3.0 compliant data models
  - Shell Descriptor - Digital twin representation
  - Submodel Descriptor - Detailed asset information
  - Specific Asset ID - Unique identifiers with visibility control
  - Endpoint & Protocol Information - Data access configuration
  - Reference models - Semantic references

### Submodel Server

Store and retrieve submodel data using flexible storage adapters.

#### Adapters
- **[Submodel Adapters Overview](submodel-server/adapters.md)** - Storage adapter architecture
  - Factory pattern for adapter creation
  - Common operations (read, write, delete, exists)
  - Custom adapter implementation guide

- **[Base Adapter](submodel-server/adapters/base-adapter.md)** - Abstract adapter interface
  - Interface definition
  - Required methods
  - Implementation guidelines

- **[File System Adapter](submodel-server/adapters/file-system-adapter.md)** - Local file storage
  - JSON file operations
  - Directory management
  - Usage examples

### Discovery Services

Locate business partners and assets in the dataspace.

#### BPN Discovery
- **[BPN Discovery Service](discovery-services/bpn-discovery.md)** - Business Partner Number resolution
  - Find BPNs by identifier (single/multi-type)
  - Register identifiers to your BPN
  - Batch operations for efficiency
  - Caching and performance optimization

## Quick Start Examples

### Working with Digital Twin Registry

```python
from tractusx_sdk.industry.services import AasService
from tractusx_sdk.industry.models.aas.v3 import ShellDescriptor, AssetKind
from tractusx_sdk.dataspace.managers import OAuth2Manager

# Initialize authentication
auth_manager = OAuth2Manager(
    token_url="https://auth.example.com/token",
    client_id="your-client-id",
    client_secret="your-client-secret"
)

# Create AAS service
aas_service = AasService(
    base_url="https://dtr.example.com",
    base_lookup_url="https://dtr-lookup.example.com",
    api_path="/api/v3.0",
    auth_service=auth_manager
)

# Query shell descriptors
shells = aas_service.get_all_asset_administration_shell_descriptors(
    limit=50,
    asset_kind=AssetKind.INSTANCE
)
```

### Using Submodel Adapters

```python
from tractusx_sdk.industry.adapters import SubmodelAdapterFactory

# Create file system adapter
adapter = SubmodelAdapterFactory.get_file_system(root_path="./submodels")

# Write submodel data
submodel_data = {
    "id": "12345",
    "partName": "Transmission Module"
}
adapter.write("part-type-info/12345.json", submodel_data)

# Read submodel data
data = adapter.read("part-type-info/12345.json")
```

### Discovering Business Partners

```python
from tractusx_sdk.industry.services.discovery import BpnDiscoveryService
from tractusx_sdk.dataspace.services.discovery import DiscoveryFinderService

# Initialize services
discovery_finder = DiscoveryFinderService(
    discovery_finder_url="https://discovery.example.com",
    oauth=auth_manager
)

bpn_discovery = BpnDiscoveryService(
    oauth=auth_manager,
    discovery_finder_service=discovery_finder
)

# Find BPNs for manufacturer part IDs
bpns = bpn_discovery.find_bpns(
    keys=["MPN-12345", "MPN-67890"],
    identifier_type="manufacturerPartId"
)
```

## Documentation Structure

```text
industry-library/
├── index.md                           # This file - API overview
├── dtr/                               # Digital Twin Registry
│   ├── services.md                    # AAS Service API reference
│   └── models.md                      # AAS 3.0 models documentation
├── submodel-server/                   # Submodel storage
│   ├── adapters.md                    # Adapter overview and factory
│   └── adapters/
│       ├── base-adapter.md            # Abstract base interface
│       └── file-system-adapter.md     # File system implementation
├── discovery-services/                # Discovery APIs
│   └── bpn-discovery.md               # BPN Discovery Service
└── legacy/                            # Legacy documentation
    ├── dtr-sdk-usage.md               # Old DTR examples
    └── submodel-server-sdk-usage.md   # Old submodel examples
```

## Integration Patterns

### Complete Digital Twin Workflow

```python
# 1. Discover business partner
bpns = bpn_discovery.find_bpns(
    keys=["MPN-TRANSMISSION-001"],
    identifier_type="manufacturerPartId"
)

# 2. Query Digital Twin Registry
for bpn in bpns:
    shells = aas_service.get_all_asset_administration_shell_descriptors(
        bpn=bpn,
        limit=10
    )
    
    # 3. Process each digital twin
    for shell in shells.items:
        print(f"Shell: {shell.id}")
        
        # 4. Get submodel descriptors
        submodels = aas_service.get_submodel_descriptors_by_aas_id(
            aas_identifier=shell.id,
            bpn=bpn
        )
        
        # 5. Store submodel data locally
        for submodel in submodels.result:
            # Fetch and store submodel data
            data = {"id": submodel.id, "semantic_id": submodel.semantic_id}
            adapter.write(f"{submodel.id_short}/{submodel.id}.json", data)
```

## API Conventions

### Authentication

All services require OAuth2 authentication via `OAuth2Manager`:

```python
from tractusx_sdk.dataspace.managers import OAuth2Manager

auth_manager = OAuth2Manager(
    token_url="https://auth.example.com/token",
    client_id="your-client-id",
    client_secret="your-client-secret"
)
```

### Error Handling

Services return either the expected model or a `Result` object on error:

```python
response = aas_service.get_asset_administration_shell_descriptor_by_id(
    aas_identifier="urn:uuid:12345"
)

if isinstance(response, Result):
    # Handle error
    for message in response.messages:
        print(f"Error: {message.text}")
else:
    # Process successful response
    print(f"Shell ID: {response.id}")
```

### Pagination

Services support pagination for large result sets:

```python
# First page
response = aas_service.get_all_asset_administration_shell_descriptors(limit=50)

# Next page using cursor
if response.paging_metadata and response.paging_metadata.cursor:
    next_response = aas_service.get_all_asset_administration_shell_descriptors(
        limit=50,
        cursor=response.paging_metadata.cursor
    )
```

## Best Practices

1. **Reuse service instances** - Create services once at application startup
2. **Use BPN filtering** - Always specify BPN for proper authorization scope
3. **Handle pagination** - Process large result sets with cursor-based pagination
4. **Validate models** - Leverage Pydantic validation for data integrity
5. **Cache discovery URLs** - Configure appropriate cache timeout for BPN discovery
6. **Use adapters** - Prefer factory pattern over direct adapter instantiation
7. **Check existence** - Always verify resource existence before reading

## Migration Guide

If you're migrating from legacy SDK versions, see:

- [Legacy DTR Usage](legacy/dtr-sdk-usage.md)
- [Legacy Submodel Server Usage](legacy/submodel-server-sdk-usage.md)

## Further Reading

- [Industry Core Concepts](../../core-concepts/industry-concepts/index.md) - Conceptual overview
- [SDK Architecture](../../core-concepts/sdk-architecture/sdk-structure-and-components.md) - Technical architecture
- [Getting Started Tutorial](../../tutorials/getting-started.md) - Step-by-step guide
- [Dataspace Library API](../dataspace-library/index.md) - Connector and discovery APIs

## NOTICE

This work is licensed under the [CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/legalcode).

- SPDX-License-Identifier: CC-BY-4.0
- SPDX-FileCopyrightText: 2025 Contributors to the Eclipse Foundation
- Source URL: https://github.com/eclipse-tractusx/tractusx-sdk
