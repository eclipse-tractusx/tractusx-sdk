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

# Tools

This page provides a comprehensive overview of the **utility tools** available in the Tractus-X SDK. These tools provide essential functionality for common operations such as HTTP communication, data processing, encoding/decoding, file operations, and dataspace protocol handling. The tools are designed to be lightweight, reusable, and easy to integrate into your applications, serving as building blocks for more complex SDK functionality.

## Purpose

The Tractus-X SDK tools serve as foundational utilities that power the higher-level services and controllers. They provide:

- **HTTP Communication**: Simplified HTTP request handling with session management
- **Data Processing**: JSON manipulation, file operations, and general-purpose utilities
- **Encoding/Decoding**: URL-safe Base64 encoding for secure data transmission
- **Dataspace Protocol Support**: DSP (Dataspace Protocol) specific operations for catalog and policy handling
- **Configuration Management**: Application configuration and logging setup utilities
- **Submodel Validation**: Schema-based validation for Tractus-X submodels

These tools abstract common operations and provide consistent interfaces across the SDK, reducing code duplication and ensuring reliable functionality.

## Available Tools

### HttpTools

A comprehensive HTTP client wrapper that simplifies HTTP operations with built-in session management and FastAPI response handling.

!!! info "Key Features"
    - **HTTP Methods**: GET, POST, PUT, DELETE
    - **Session Management**: Session-based and standalone requests
    - **Response Handling**: FastAPI-compatible responses, JSON helpers
    - **URL Utilities**: Safe URL manipulation and joining
    - **Error Handling**: Standardized error/status codes

**Common Methods:**

| Method | Description | Parameters |
|--------|-------------|------------|
| `do_get()` | Perform GET request without session | `url`, `verify`, `headers`, `timeout`, `params`, `allow_redirects` |
| `do_post()` | Perform POST request without session | `url`, `data`, `verify`, `headers`, `timeout`, `json`, `allow_redirects` |
| `do_put()` | Perform PUT request without session | `url`, `data`, `verify`, `headers`, `timeout`, `json`, `allow_redirects` |
| `do_delete()` | Perform DELETE request without session | `url`, `verify`, `headers`, `timeout`, `params`, `allow_redirects` |
| `json_response()` | Create FastAPI JSON response | `data`, `status_code`, `headers` |
| `concat_into_url()` | Join URL parts safely | `*args` |
| `proxy()` | Proxy requests.Response to FastAPI Response | `response` |

**Example:**

```python
from tractusx_sdk.dataspace.tools import HttpTools

# Simple GET request
response = HttpTools.do_get(
    url="https://api.example.com/data",
    headers={"Authorization": "Bearer token"},
    timeout=30
)

# POST with JSON data
response = HttpTools.do_post(
    url="https://api.example.com/submit",
    json={"key": "value"},
    headers={"Content-Type": "application/json"}
)

# Create FastAPI JSON response
from fastapi import FastAPI
app = FastAPI()

@app.get("/endpoint")
def my_endpoint():
    data = {"message": "success", "data": [1, 2, 3]}
    return HttpTools.json_response(data, status_code=200)

# URL manipulation
full_url = HttpTools.concat_into_url(
    "https://api.example.com", 
    "v1", 
    "resources", 
    "123"
)
# Result: "https://api.example.com/v1/resources/123"
```

### DspTools

Specialized tools for handling Dataspace Protocol (DSP) operations, particularly for DCAT catalog processing and policy validation.


!!! info "Key Features"
    - **Catalog Processing**: Parse/filter DCAT catalogs by policy
    - **Policy Validation**: Validate policies against allowed lists
    - **Asset Selection**: Select valid assets by constraints
    - **Empty Catalog Detection**: Check for valid datasets

**Core Methods:**

| Method | Description | Parameters | Return Type |
|--------|-------------|------------|-------------|
| `filter_assets_and_policies()` | Filter assets and policies from catalog | `catalog`, `allowed_policies` | `list[tuple[str, dict]]` |
| `get_dataset_policy()` | Get valid policy from dataset | `dataset`, `allowed_policies` | `dict \| None` |
| `is_policy_valid()` | Check if policy is in allowed list | `policy`, `allowed_policies` | `bool` |
| `is_catalog_empty()` | Check if catalog is empty | `catalog` | `bool` |

**Example:**

```python
from tractusx_sdk.dataspace.tools import DspTools

# Define allowed policies
allowed_policies = [
    {
        "odrl:permission": [{
            "odrl:action": "odrl:use",
            "odrl:constraint": {
                "odrl:leftOperand": "BusinessPartnerNumber",
                "odrl:operator": "odrl:eq",
                "odrl:rightOperand": "BPNL000000000001"
            }
        }]
    }
]

# Process catalog and filter assets
catalog = {
    "dcat:dataset": [
        {
            "@id": "asset-1",
            "odrl:hasPolicy": {
                "@id": "policy-1",
                "@type": "odrl:Policy",
                "odrl:permission": [{
                    "odrl:action": "odrl:use",
                    "odrl:constraint": {
                        "odrl:leftOperand": "BusinessPartnerNumber",
                        "odrl:operator": "odrl:eq", 
                        "odrl:rightOperand": "BPNL000000000001"
                    }
                }]
            }
        }
    ]
}

# Filter valid assets and policies
valid_assets = DspTools.filter_assets_and_policies(
    catalog=catalog,
    allowed_policies=allowed_policies
)

for asset_id, policy in valid_assets:
    print(f"Valid asset: {asset_id} with policy: {policy['@id']}")
```

### Encoding Tools

URL-safe Base64 encoding and decoding utilities for secure data transmission in dataspace protocols.

**Functions:**

| Function | Description | Parameters | Return Type |
|----------|-------------|------------|-------------|
| `encode_as_base64_url_safe()` | Encode string as URL-safe Base64 | `string: str` | `str` |
| `decode_base64_url_safe()` | Decode URL-safe Base64 string | `encoded_string: str` | `str` |

!!! info "Key Features"
    - **URL-Safe Encoding**: Uses URL-safe Base64 alphabet
    - **Automatic Padding**: Handles padding on decode
    - **UTF-8 Support**: Full Unicode compatibility

**Example:**

```python
from tractusx_sdk.dataspace.tools import encode_as_base64_url_safe, decode_base64_url_safe

# Encode sensitive data for URL transmission
sensitive_data = "user:password@domain.com"
encoded = encode_as_base64_url_safe(sensitive_data)
print(f"Encoded: {encoded}")

# Decode received data
decoded = decode_base64_url_safe(encoded)
print(f"Decoded: {decoded}")

# Use in URL parameters
url = f"https://api.example.com/auth?token={encoded}"
```

### Operators (op)

General-purpose utility class providing file operations, JSON handling, and system utilities.

**Key Categories:**

#### JSON Operations

| Method | Description | Parameters |
|--------|-------------|------------|
| `json_string_to_object()` | Parse JSON string to Python object | `json_string` |
| `to_json()` | Convert object to JSON string | `source_object`, `indent`, `ensure_ascii` |
| `to_json_file()` | Write object to JSON file | `source_object`, `json_file_path`, `file_open_mode`, `indent` |
| `read_json_file()` | Read JSON file to Python object | `file_path`, `encoding` |

#### File Operations

| Method | Description | Parameters |
|--------|-------------|------------|
| `path_exists()` | Check if path exists | `file_path` |
| `make_dir()` | Create directory with permissions | `dir_name`, `permits` |
| `delete_dir()` | Delete directory and contents | `dir_name` |
| `copy_file()` | Copy file to destination | `file_path`, `dst` |
| `move_file()` | Move file to destination | `file_path`, `dst` |
| `to_string()` | Read file contents as string | `file_path`, `open_mode`, `encoding` |
| `load_file()` | Load file as BytesIO object | `file_path` |
| `delete_file()` | Delete file | `file_path` |

#### Timestamp Operations

| Method | Description | Parameters |
|--------|-------------|------------|
| `timestamp()` | Get current timestamp | `zone`, `string` |
| `get_filedatetime()` | Get formatted datetime for filenames | `zone` |

**Example:**

```python
from tractusx_sdk.dataspace.tools import op

# JSON operations
data = {"name": "Tractus-X", "version": "1.0", "components": ["SDK", "Services"]}

# Write to JSON file
op.to_json_file(
    source_object=data,
    json_file_path="config.json",
    indent=2
)

# Read from JSON file
loaded_data = op.read_json_file("config.json")
print(f"Loaded: {loaded_data}")

# File operations
if op.path_exists("data"):
    files = op.to_string("data/info.txt")
    print(f"File contents: {files}")
else:
    op.make_dir("data")
    op.write_to_file("Sample data", "data/info.txt")

# Timestamps for logging
current_time = op.timestamp(string=True)
log_filename = f"app_{op.get_filedatetime()}.log"
```

### Utils

Configuration and argument parsing utilities for application setup.


!!! info "Key Features"
    - **Argument Parsing**: Command-line argument support
    - **Logging Setup**: Load and configure logging
    - **App Configuration**: Load application config files
    - **Supported Arguments**: `--test-mode`, `--debug`, `--port`, `--host`

**Example:**

```python
from tractusx_sdk.dataspace.tools import get_arguments, get_app_config, get_log_config

# Parse command line arguments
args = get_arguments()
if args.debug:
    print("Debug mode enabled")

# Load application configuration
app_config = get_app_config("config/app.yaml")
database_url = app_config["database"]["url"]

# Setup logging
log_config = get_log_config("config/logging.yaml", "my-service")
import logging
logger = logging.getLogger("my-service")
logger.info("Application started")
```

### Submodel Validation Tools

Tools for validating Tractus-X submodels against their semantic schemas.

**Functions:**

| Function | Description | Parameters | Return Type |
|----------|-------------|------------|-------------|
| `submodel_schema_finder()` | Find schema for semantic ID | `semantic_id`, `link_core` | `dict` |
| `json_validator()` | Validate JSON against schema | `schema`, `json_to_validate`, `validation_type` | `dict` |

**Example:**

```python
from tractusx_sdk.dataspace.tools.validate_submodels import submodel_schema_finder, json_validator

# Validate a Tractus-X submodel
semantic_id = "urn:samm:io.catenax.part_type_information:1.0.0#PartTypeInformation"

# Get the schema for validation
schema_result = submodel_schema_finder(semantic_id)
schema = schema_result["schema"]

# Sample submodel data
submodel_data = {
    "partTypeInformation": {
        "manufacturerPartId": "ABC123",
        "partVersion": "1.0",
        "partName": "Engine Component"
    }
}

# Validate the submodel
try:
    validation_result = json_validator(
        schema=schema,
        json_to_validate=submodel_data,
        validation_type="jsonschema"
    )
    print("Validation successful:", validation_result["message"])
except Exception as e:
    print("Validation failed:", str(e))
```

!!! tip "Best Practices"
    - Use session management for repeated HTTP requests.
    - Always set timeouts and check response codes.
    - Prefer `verify=True` for SSL in production.
    - Check file/directory existence before operations.
    - Specify encoding for text files.

## Troubleshooting

??? "ConnectionError when using HttpTools"
    **Why does this happen?**
    
    This usually means there is a problem with network connectivity, SSL certificates, or timeout settings.

    **How to debug:**
    ```python
    response = HttpTools.do_get(
        url="https://api.example.com/test",
        timeout=10,
        verify=False,  # Temporarily disable SSL verification for testing
        headers={"User-Agent": "Debug Client"}
    )
    print(f"Status: {response.status_code}")
    print(f"Headers: {response.headers}")
    ```

??? "FileNotFoundError with file operations"
    **Why does this happen?**
    
    This happens when the file or directory does not exist. Always check for existence and handle missing files gracefully.

    **Safe file reading:**
    ```python
    def safe_read_config(file_path: str) -> dict:
        if not op.path_exists(file_path):
            logger.warning(f"Config file not found: {file_path}, using defaults")
            return {"default_config": True}
        try:
            return op.read_json_file(file_path)
        except Exception as e:
            logger.error(f"Failed to read config: {e}")
            return {"error": True}
    ```

??? "HTTPError in submodel validation"
    **Why does this happen?**
    
    This can occur if the semantic ID format is invalid or there is a network issue accessing the schema repository.

    **Robust submodel validation:**
    ```python
    def validate_submodel_safely(semantic_id: str, data: dict) -> bool:
        try:
            # Validate semantic ID format
            if not semantic_id.startswith("urn:samm:"):
                raise ValueError("Invalid semantic ID format")
            schema_result = submodel_schema_finder(semantic_id)
            validation_result = json_validator(schema_result["schema"], data)
            return True
        except HTTPError as e:
            logger.error(f"Schema retrieval failed: {e}")
            return False
        except Exception as e:
            logger.error(f"Validation failed: {e}")
            return False
    ```

## Further Reading

- [Dataspace Library Overview](../index.md)

## NOTICE

This work is licensed under the [CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/legalcode).

- SPDX-License-Identifier: CC-BY-4.0
- SPDX-FileCopyrightText: 2025 Contributors to the Eclipse Foundation
- Source URL: https://github.com/eclipse-tractusx/tractusx-sdk
