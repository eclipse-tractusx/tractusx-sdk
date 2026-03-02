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
# Submodel Server Base Adapter

The `SubmodelAdapter` is an abstract base class that defines the interface for all submodel server adapters in the Tractus-X SDK. It provides a standardized way to interact with different storage backends for submodel data.

## Purpose

The base adapter establishes a common interface for:

- **Reading submodel data** from various storage backends
- **Writing submodel data** to storage systems
- **Deleting submodel data** when no longer needed
- **Checking existence** of submodel files or resources

By defining this abstract interface, the SDK enables pluggable storage backends without changing application code.

## Interface Definition

### Abstract Methods

All concrete adapter implementations must provide the following methods:

#### read(path: str)

Reads and returns the entire content of a submodel file.

```python
@abstractmethod
def read(self, path: str):
    """
    Return the entire content of a file
    """
    raise NotImplementedError
```

**Parameters:**

| Parameter | Type  | Description                           |
|-----------|-------|---------------------------------------|
| `path`    | `str` | Path to the file to read              |

**Returns:** File content (format depends on implementation)

#### write(path: str, content: bytes)

Writes content to a new or existing file.

```python
@abstractmethod
def write(self, path: str, content: bytes) -> None:
    """
    Write a new file
    """
    raise NotImplementedError
```

**Parameters:**

| Parameter | Type    | Description                           |
|-----------|---------|---------------------------------------|
| `path`    | `str`   | Path where the file should be written |
| `content` | `bytes` | Content to write to the file          |

**Returns:** None

#### delete(path: str)

Deletes a specific file from storage.

```python
@abstractmethod
def delete(self, path: str) -> None:
    """
    Delete a specific file
    """
    raise NotImplementedError
```

**Parameters:**

| Parameter | Type  | Description                    |
|-----------|-------|--------------------------------|
| `path`    | `str` | Path to the file to delete     |

**Returns:** None

#### exists(path: str)

Checks whether a file exists in storage.

```python
@abstractmethod
def exists(self, path: str) -> bool:
    """
    Check if a file exists
    """
    raise NotImplementedError
```

**Parameters:**

| Parameter | Type  | Description                        |
|-----------|-------|------------------------------------||
| `path`    | `str` | Path to check for existence        |

**Returns:** `bool` - True if file exists, False otherwise

## Implementing Custom Adapters

To create a custom adapter for a specific storage backend:

```python
from tractusx_sdk.industry.adapters import SubmodelAdapter

class MyCustomAdapter(SubmodelAdapter):
    
    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        # Initialize your storage connection
    
    def read(self, path: str):
        # Implement reading from your storage
        pass
    
    def write(self, path: str, content: bytes) -> None:
        # Implement writing to your storage
        pass
    
    def delete(self, path: str) -> None:
        # Implement deletion from your storage
        pass
    
    def exists(self, path: str) -> bool:
        # Implement existence check
        pass
```

## Available Implementations

The SDK provides the following built-in adapter implementations:

- **[FileSystemAdapter](file-system-adapter.md)** - Local file system storage for submodels

## Usage Pattern

Adapters are typically used through the factory pattern:

```python
from tractusx_sdk.industry.adapters import SubmodelAdapterFactory, SubmodelAdapterType

# Get a file system adapter
adapter = SubmodelAdapterFactory.get_file_system(root_path="./submodels")

# Use the adapter
if adapter.exists("part-info.json"):
    content = adapter.read("part-info.json")
else:
    adapter.write("part-info.json", content_bytes)
```

## Best Practices

1. **Always check existence** before reading files to avoid errors
2. **Handle exceptions** appropriately in your implementations
3. **Use relative paths** for portability across adapters
4. **Validate content** before writing to ensure data integrity
5. **Close resources** properly in adapters that manage connections

## Further Reading

- [File System Adapter](file-system-adapter.md) - Concrete implementation for local storage
- [Submodel Adapter Factory](../adapters.md) - Factory for creating adapter instances
- [Industry Library Overview](../../index.md)

## NOTICE

This work is licensed under the [CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/legalcode).

- SPDX-License-Identifier: CC-BY-4.0
- SPDX-FileCopyrightText: 2025 Contributors to the Eclipse Foundation
- Source URL: https://github.com/eclipse-tractusx/tractusx-sdk
