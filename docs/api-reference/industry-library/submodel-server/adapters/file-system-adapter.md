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
# File System Adapter

The `FileSystemAdapter` provides local file system storage for submodel data. It implements the `SubmodelAdapter` interface and enables reading, writing, and managing JSON submodel files on disk.

## Purpose

The File System Adapter enables:

- **Local storage** of submodel data as JSON files
- **Directory-based organization** of submodels
- **File operations** (create, read, update, delete) for submodel data
- **Development and testing** with local file storage
- **Listing and browsing** submodel contents in directories

## Initialization

### Using the Factory (Recommended)

```python
from tractusx_sdk.industry.adapters import SubmodelAdapterFactory

# Create file system adapter with default root path
adapter = SubmodelAdapterFactory.get_file_system(root_path="./submodels")
```

### Using the Builder Pattern

```python
from tractusx_sdk.industry.adapters.submodel_adapters import FileSystemAdapter

adapter = (
    FileSystemAdapter.builder()
    .root_path("/data/submodels")
    .build()
)
```

### Direct Initialization

```python
from tractusx_sdk.industry.adapters.submodel_adapters import FileSystemAdapter

adapter = FileSystemAdapter(root_path="./submodels")
```

## Configuration

| Parameter   | Type  | Required | Description                                           |
|-------------|-------|----------|-------------------------------------------------------|
| `root_path` | `str` | Yes      | Root directory path where submodel files are stored   |

## Methods

### read(path: str)

Reads a JSON file and returns its content as a Python dictionary.

```python
# Read a submodel file
submodel_data = adapter.read("part-type-info/12345.json")
print(f"Part Name: {submodel_data['partName']}")
```

**Parameters:**

| Parameter | Type  | Description                                      |
|-----------|-------|--------------------------------------------------|
| `path`    | `str` | Relative path to the JSON file from root_path    |

**Returns:** Python dictionary with the JSON file content

**Raises:** 
- `FileNotFoundError` if the file doesn't exist
- `JSONDecodeError` if the file is not valid JSON

### write(path: str, content)

Writes content to a JSON file. Creates directories if they don't exist.

```python
# Write submodel data
submodel_data = {
    "id": "12345",
    "partName": "Transmission Module",
    "partType": "Gearbox"
}

adapter.write("part-type-info/12345.json", submodel_data)
```

**Parameters:**

| Parameter | Type              | Description                                      |
|-----------|-------------------|--------------------------------------------------|
| `path`    | `str`             | Relative path where the file should be written   |
| `content` | `dict` or `bytes` | Content to write (will be serialized to JSON)    |

**Returns:** None

### delete(path: str)

Deletes a file from the file system.

```python
# Delete a submodel file
adapter.delete("part-type-info/12345.json")
```

**Parameters:**

| Parameter | Type  | Description                                         |
|-----------|-------|-----------------------------------------------------|
| `path`    | `str` | Relative path to the file to delete                 |

**Returns:** None

**Raises:**
- `FileNotFoundError` if the file doesn't exist

### exists(path: str)

Checks if a file exists in the file system.

```python
# Check if submodel exists
if adapter.exists("part-type-info/12345.json"):
    data = adapter.read("part-type-info/12345.json")
else:
    print("Submodel not found")
```

**Parameters:**

| Parameter | Type  | Description                                    |
|-----------|-------|-------------------------------------------------|
| `path`    | `str` | Relative path to check                          |

**Returns:** `bool` - True if file exists, False otherwise

### list_contents(directory_path: str)

Lists all files in a directory.

```python
# List all submodel files in a directory
files = adapter.list_contents("part-type-info")
for file_path in files:
    print(f"Found: {file_path}")
```

**Parameters:**

| Parameter        | Type  | Description                                    |
|------------------|-------|------------------------------------------------|
| `directory_path` | `str` | Relative path to the directory to list         |

**Returns:** `List[str]` - List of absolute file paths in the directory

### create_directory(path: str)

Creates a new directory in the file system.

```python
# Create directory for new submodel type
adapter.create_directory("serial-part")
```

**Parameters:**

| Parameter | Type  | Description                                    |
|-----------|-------|------------------------------------------------|
| `path`    | `str` | Relative path of the directory to create       |

**Returns:** None

### delete_directory(path: str)

Deletes a directory from the file system.

```python
# Remove entire submodel category
adapter.delete_directory("obsolete-parts")
```

**Parameters:**

| Parameter | Type  | Description                                    |
|-----------|-------|------------------------------------------------|
| `path`    | `str` | Relative path of the directory to delete       |

**Returns:** None

**Warning:** This will delete the directory and all its contents.

## Complete Usage Example

```python
from tractusx_sdk.industry.adapters import SubmodelAdapterFactory
import json

# Initialize adapter
adapter = SubmodelAdapterFactory.get_file_system(root_path="./submodels")

# Create directory structure
adapter.create_directory("part-type-info")

# Write submodel data
part_data = {
    "catenaXId": "urn:uuid:12345678-1234-1234-1234-123456789012",
    "partTypeInformation": {
        "manufacturerPartId": "MPN-12345",
        "nameAtManufacturer": "Transmission Module",
        "classification": "product"
    }
}

submodel_path = "part-type-info/12345.json"
adapter.write(submodel_path, part_data)
print(f"Submodel written to {submodel_path}")

# Check if file exists
if adapter.exists(submodel_path):
    print("Submodel exists in storage")

# Read the submodel
retrieved_data = adapter.read(submodel_path)
print(f"Part ID: {retrieved_data['partTypeInformation']['manufacturerPartId']}")

# List all files in directory
all_parts = adapter.list_contents("part-type-info")
print(f"Total submodels: {len(all_parts)}")

# Delete when no longer needed
adapter.delete(submodel_path)
print("Submodel deleted")
```

## File Organization

The File System Adapter uses a hierarchical directory structure:

```
root_path/
├── part-type-info/
│   ├── 12345.json
│   ├── 67890.json
│   └── abc123.json
├── serial-part/
│   ├── SN-001.json
│   └── SN-002.json
└── batch/
    └── BATCH-2024-01.json
```

## Best Practices

1. **Organize by submodel type** - Use directories to group submodels of the same type
2. **Use meaningful file names** - Name files after asset IDs or serial numbers
3. **Handle exceptions** - Always wrap file operations in try-except blocks
4. **Check existence first** - Use `exists()` before reading to avoid errors
5. **Validate JSON** - Ensure data is valid before writing
6. **Clean up** - Delete obsolete submodel files to save space

## Error Handling

```python
try:
    data = adapter.read("non-existent-file.json")
except FileNotFoundError:
    print("Submodel file not found")
except json.JSONDecodeError:
    print("Invalid JSON in submodel file")
except PermissionError:
    print("Permission denied accessing submodel file")
```

## Thread Safety

**Note:** The File System Adapter is not thread-safe by default. If you need concurrent access, implement appropriate locking mechanisms:

```python
import threading

lock = threading.Lock()

with lock:
    adapter.write("path/file.json", data)
```

## Further Reading

- [Base Adapter Interface](base-adapter.md) - Abstract adapter definition
- [Submodel Adapter Factory](../adapters.md) - Factory for creating adapters
- [Industry Library Overview](../../index.md)
- [File System Adapter Source Code](https://github.com/eclipse-tractusx/tractusx-sdk/blob/main/src/tractusx_sdk/industry/adapters/submodel_adapters/file_system_adapter.py)

## NOTICE

This work is licensed under the [CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/legalcode).

- SPDX-License-Identifier: CC-BY-4.0
- SPDX-FileCopyrightText: 2025 Contributors to the Eclipse Foundation
- Source URL: https://github.com/eclipse-tractusx/tractusx-sdk
