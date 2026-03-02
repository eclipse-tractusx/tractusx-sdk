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
# Submodel Server Adapters

The Submodel Server Adapters provide a flexible, pluggable architecture for storing and retrieving submodel data from various storage backends. The adapter pattern enables seamless switching between storage solutions without changing application code.

## Purpose

Submodel adapters enable:

- **Abstracted storage operations** - Read, write, delete, and check existence of submodel data
- **Pluggable backends** - Support for multiple storage implementations (file system, databases, cloud storage)
- **Consistent interface** - Unified API regardless of underlying storage technology
- **Easy testing** - Mock adapters for unit testing without real storage dependencies
- **Flexible deployment** - Choose storage backend based on deployment requirements

## Architecture

```text
SubmodelAdapter (Abstract Base)
        │
        ├── FileSystemAdapter (Local files)
        ├── S3Adapter (Amazon S3) [Future]
        ├── AzureBlobAdapter (Azure Blob Storage) [Future]
        └── DatabaseAdapter (SQL/NoSQL) [Future]
```

## Adapter Factory

The `SubmodelAdapterFactory` provides a centralized way to create adapter instances.

### Available Adapter Types

| Adapter Type     | Enum Value               | Description                              |
|------------------|--------------------------|------------------------------------------|
| File System      | `FILE_SYSTEM`            | Local file system storage                |

### Factory Usage

```python
from tractusx_sdk.industry.adapters import (
    SubmodelAdapterFactory,
    SubmodelAdapterType
)

# Create a file system adapter
adapter = SubmodelAdapterFactory.get_file_system(root_path="./submodels")

# Alternative: Using the internal factory method
adapter = SubmodelAdapterFactory._get_adapter_builder(
    adapter_type=SubmodelAdapterType.FILE_SYSTEM
)
```

## Common Operations

All adapters implement the following core operations:

### Read Operation

```python
# Read submodel data
submodel_data = adapter.read("part-type-info/12345.json")
print(f"Part Name: {submodel_data['partName']}")
```

### Write Operation

```python
# Write submodel data
submodel_data = {
    "id": "12345",
    "partName": "Transmission Module",
    "partType": "Gearbox"
}
adapter.write("part-type-info/12345.json", submodel_data)
```

### Delete Operation

```python
# Delete submodel data
adapter.delete("part-type-info/12345.json")
```

### Existence Check

```python
# Check if submodel exists
if adapter.exists("part-type-info/12345.json"):
    data = adapter.read("part-type-info/12345.json")
else:
    print("Submodel not found")
```

## Available Adapters

### 1. File System Adapter

Stores submodel data as JSON files on the local file system.

**Use Cases:**
- Development and testing
- Small-scale deployments
- Single-server applications
- Local data processing

**Documentation:** [File System Adapter Details](adapters/file-system-adapter.md)

**Example:**
```python
from tractusx_sdk.industry.adapters import SubmodelAdapterFactory

adapter = SubmodelAdapterFactory.get_file_system(root_path="./submodels")
```

## Adapter Selection Guide

Choose the appropriate adapter based on your requirements:

| Requirement                    | Recommended Adapter    |
|--------------------------------|------------------------|
| Local development/testing      | File System            |
| Single server deployment       | File System            |
| Distributed systems            | (Future: S3, Azure)    |
| High availability needs        | (Future: Database)     |
| Cloud-native applications      | (Future: Cloud Storage)|

## Custom Adapter Implementation

Create custom adapters by extending the `SubmodelAdapter` base class:

```python
from tractusx_sdk.industry.adapters import SubmodelAdapter

class MyCustomAdapter(SubmodelAdapter):
    
    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        self._connect()
    
    def _connect(self):
        # Initialize connection to your storage backend
        pass
    
    def read(self, path: str):
        # Implement read operation
        pass
    
    def write(self, path: str, content: bytes) -> None:
        # Implement write operation
        pass
    
    def delete(self, path: str) -> None:
        # Implement delete operation
        pass
    
    def exists(self, path: str) -> bool:
        # Implement existence check
        pass
```

### Registering Custom Adapters

To use your custom adapter with the factory:

```python
from tractusx_sdk.industry.adapters import SubmodelAdapterType
from enum import Enum

# Extend the enum
class ExtendedAdapterType(Enum):
    FILE_SYSTEM = "FileSystem"
    MY_CUSTOM = "MyCustom"

# Use your adapter
adapter = MyCustomAdapter(connection_string="...")
```

## Builder Pattern

Most adapters support the builder pattern for flexible initialization:

```python
from tractusx_sdk.industry.adapters.submodel_adapters import FileSystemAdapter

adapter = (
    FileSystemAdapter.builder()
    .root_path("/data/submodels")
    .build()
)
```

## Best Practices

1. **Use the factory** - Prefer `SubmodelAdapterFactory` over direct instantiation
2. **Configure once** - Create adapter instances at application startup
3. **Check existence** - Always verify file existence before reading
4. **Handle errors** - Implement proper exception handling for storage operations
5. **Validate data** - Ensure submodel data is valid before writing
6. **Close resources** - Properly cleanup adapter resources when done
7. **Test with mocks** - Use mock adapters for unit testing

## Error Handling

```python
from tractusx_sdk.industry.adapters import SubmodelAdapterFactory
import json

adapter = SubmodelAdapterFactory.get_file_system(root_path="./submodels")

try:
    data = adapter.read("submodel.json")
except FileNotFoundError:
    print("Submodel not found")
except json.JSONDecodeError:
    print("Invalid JSON format")
except PermissionError:
    print("Permission denied")
except Exception as e:
    print(f"Unexpected error: {e}")
```

## Integration Example

Complete example integrating adapter with DTR service:

```python
from tractusx_sdk.industry.services import AasService
from tractusx_sdk.industry.adapters import SubmodelAdapterFactory
from tractusx_sdk.dataspace.managers import OAuth2Manager

# Initialize authentication
auth_manager = OAuth2Manager(
    token_url="https://auth.example.com/token",
    client_id="client-id",
    client_secret="client-secret"
)

# Initialize DTR service
dtr_service = AasService(
    base_url="https://dtr.example.com",
    base_lookup_url="https://dtr-lookup.example.com",
    api_path="/api/v3.0",
    auth_service=auth_manager
)

# Initialize submodel storage adapter
submodel_adapter = SubmodelAdapterFactory.get_file_system(
    root_path="./submodels"
)

# Fetch shell descriptor from DTR
shell = dtr_service.get_asset_administration_shell_descriptor_by_id(
    aas_identifier="urn:uuid:12345"
)

# Store submodel data locally
for submodel_desc in shell.submodel_descriptors:
    # Fetch submodel data from endpoint (simplified)
    submodel_data = {"id": submodel_desc.id, "data": "..."}
    
    # Store locally using adapter
    file_path = f"{submodel_desc.id_short}/{submodel_desc.id}.json"
    submodel_adapter.write(file_path, submodel_data)
    print(f"Stored submodel: {file_path}")
```

## Further Reading

- [SubmodelAdapter Base Class](adapters/base-adapter.md) - Abstract interface definition
- [File System Adapter](adapters/file-system-adapter.md) - Local file storage implementation
- [Industry Library Overview](../index.md)
- [Submodel Adapter Factory Source Code](https://github.com/eclipse-tractusx/tractusx-sdk/blob/main/src/tractusx_sdk/industry/adapters/submodel_adapter_factory.py)

## NOTICE

This work is licensed under the [CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/legalcode).

- SPDX-License-Identifier: CC-BY-4.0
- SPDX-FileCopyrightText: 2025 Contributors to the Eclipse Foundation
- Source URL: https://github.com/eclipse-tractusx/tractusx-sdk
