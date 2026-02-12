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
# DTR Services

The Digital Twin Registry (DTR) Services provide high-level abstractions for interacting with Asset Administration Shell (AAS) registries in the Tractus-X ecosystem. These services enable managing digital twins, shell descriptors, and submodel descriptors in a standardized manner.

## Purpose

DTR Services encapsulate the complexity of AAS registry operations, offering a unified API for:

- **Querying and retrieving shell descriptors** from the Digital Twin Registry
- **Creating and updating digital twins** with their associated metadata
- **Managing submodel descriptors** for detailed asset information
- **Looking up assets** by specific asset identifiers
- **Handling pagination** for large registry queries

The services are designed to work with AAS 3.0 specifications, ensuring compatibility with Tractus-X dataspace standards.

## Key Components

- **AasService**: Core service for all Digital Twin Registry interactions
- **Shell Descriptor Management**: Create, read, update, and delete operations for shell descriptors
- **Submodel Descriptor Management**: Full CRUD operations for submodels associated with shell descriptors
- **Asset ID Lookup**: Query and manage specific asset identifiers for shell descriptors
- **Authentication Support**: Integrated OAuth2 authentication via `OAuth2Manager`

## AasService Class

### Initialization

```python
from tractusx_sdk.industry.services import AasService
from tractusx_sdk.dataspace.managers import OAuth2Manager

# Initialize OAuth2 authentication (optional but recommended)
auth_manager = OAuth2Manager(
    token_url="https://auth.example.com/token",
    client_id="your-client-id",
    client_secret="your-client-secret"
)

# Create AAS service instance
aas_service = AasService(
    base_url="https://dtr.example.com",
    base_lookup_url="https://dtr-lookup.example.com",
    api_path="/api/v3.0",
    auth_service=auth_manager,
    verify_ssl=True
)
```

### Parameters

| Parameter          | Type              | Required | Description                                                      |
|--------------------|-------------------|----------|------------------------------------------------------------------|
| `base_url`         | `str`             | Yes      | Base URL of the DTR API                                          |
| `base_lookup_url`  | `str`             | Yes      | Base URL for the DTR lookup service                              |
| `api_path`         | `str`             | Yes      | API endpoint path (e.g., `/api/v3.0`)                            |
| `auth_service`     | `OAuth2Manager`   | No       | Authentication service for obtaining access tokens               |
| `verify_ssl`       | `bool`            | No       | Whether to verify SSL certificates (default: `True`)             |
| `session`          | `requests.Session`| No       | Custom requests session (optional)                               |

## Shell Descriptor Operations

### Get All Shell Descriptors

Retrieve all Asset Administration Shell descriptors with optional filtering and pagination.

```python
from tractusx_sdk.industry.models.aas.v3 import AssetKind

# Get all shell descriptors with pagination
response = aas_service.get_all_asset_administration_shell_descriptors(
    limit=50,
    cursor=None,
    asset_kind=AssetKind.INSTANCE,
    bpn="BPNL000000000000"
)

# Access results
for shell in response.items:
    print(f"Shell ID: {shell.id}")
    print(f"ID Short: {shell.id_short}")
```

**Parameters:**

| Parameter    | Type        | Description                                                          |
|--------------|-------------|----------------------------------------------------------------------|
| `limit`      | `int`       | Maximum number of results to return (pagination)                     |
| `cursor`     | `str`       | Server-generated cursor for pagination                               |
| `asset_kind` | `AssetKind` | Filter by asset kind (e.g., `INSTANCE`, `TYPE`)                      |
| `asset_type` | `str`       | Filter by asset type (automatically BASE64-URL-encoded)              |
| `bpn`        | `str`       | Business Partner Number for authorization                            |

### Get Shell Descriptor by ID

Retrieve a specific shell descriptor by its identifier.

```python
shell_descriptor = aas_service.get_asset_administration_shell_descriptor_by_id(
    aas_identifier="urn:uuid:12345678-1234-1234-1234-123456789012",
    bpn="BPNL000000000000"
)

print(f"Shell Description: {shell_descriptor.description}")
print(f"Number of Submodels: {len(shell_descriptor.submodel_descriptors)}")
```

**Parameters:**

| Parameter        | Type  | Description                                           |
|------------------|-------|-------------------------------------------------------|
| `aas_identifier` | `str` | Unique identifier of the shell descriptor             |
| `bpn`            | `str` | Business Partner Number for authorization (optional)  |

### Create Shell Descriptor

Create a new Asset Administration Shell descriptor in the registry.

```python
from tractusx_sdk.industry.models.aas.v3 import ShellDescriptor, SpecificAssetId

# Create specific asset identifiers
specific_asset_ids = [
    SpecificAssetId(
        name="manufacturerPartId",
        value="MPN-12345",
        external_subject_id={"type": "ExternalReference", "keys": [{"type": "GlobalReference", "value": "*"}]}
    )
]

# Create shell descriptor
new_shell = ShellDescriptor(
    id="urn:uuid:new-asset-12345",
    id_short="MyAsset",
    description=[{"language": "en", "text": "My Digital Twin"}],
    specific_asset_ids=specific_asset_ids,
    submodel_descriptors=[]
)

created_shell = aas_service.create_asset_administration_shell_descriptor(
    shell_descriptor=new_shell,
    bpn="BPNL000000000000"
)
```

**Parameters:**

| Parameter          | Type               | Description                                           |
|--------------------|--------------------|-------------------------------------------------------|
| `shell_descriptor` | `ShellDescriptor`  | The shell descriptor object to create                 |
| `bpn`              | `str`              | Business Partner Number for authorization (optional)  |

### Update Shell Descriptor

Update an existing shell descriptor.

```python
# Modify the shell descriptor
shell_descriptor.id_short = "UpdatedAsset"
shell_descriptor.description = [{"language": "en", "text": "Updated Digital Twin"}]

# Update in registry
updated_shell = aas_service.update_asset_administration_shell_descriptor(
    aas_identifier=shell_descriptor.id,
    shell_descriptor=shell_descriptor,
    bpn="BPNL000000000000"
)
```

**Parameters:**

| Parameter          | Type               | Description                                           |
|--------------------|--------------------|-------------------------------------------------------|
| `aas_identifier`   | `str`              | Unique identifier of the shell descriptor to update   |
| `shell_descriptor` | `ShellDescriptor`  | The updated shell descriptor object                   |
| `bpn`              | `str`              | Business Partner Number for authorization (optional)  |

### Delete Shell Descriptor

Remove a shell descriptor from the registry.

```python
result = aas_service.delete_asset_administration_shell_descriptor(
    aas_identifier="urn:uuid:12345678-1234-1234-1234-123456789012",
    bpn="BPNL000000000000"
)

if result.success:
    print("Shell descriptor deleted successfully")
```

**Parameters:**

| Parameter        | Type  | Description                                           |
|------------------|-------|-------------------------------------------------------|
| `aas_identifier` | `str` | Unique identifier of the shell descriptor to delete   |
| `bpn`            | `str` | Business Partner Number for authorization (optional)  |

## Submodel Descriptor Operations

### Get Submodel Descriptors by AAS ID

Retrieve all submodel descriptors for a specific shell.

```python
submodels_response = aas_service.get_submodel_descriptors_by_aas_id(
    aas_identifier="urn:uuid:12345678-1234-1234-1234-123456789012",
    limit=50,
    cursor=None,
    bpn="BPNL000000000000"
)

for submodel in submodels_response.result:
    print(f"Submodel ID: {submodel.id}")
    print(f"Semantic ID: {submodel.semantic_id}")
```

**Parameters:**

| Parameter        | Type  | Description                                           |
|------------------|-------|-------------------------------------------------------|
| `aas_identifier` | `str` | Shell descriptor identifier                           |
| `limit`          | `int` | Maximum number of results (pagination)                |
| `cursor`         | `str` | Pagination cursor                                     |
| `bpn`            | `str` | Business Partner Number for authorization (optional)  |

### Get Specific Submodel Descriptor

Retrieve a specific submodel descriptor by its ID.

```python
submodel = aas_service.get_submodel_descriptor_by_ass_and_submodel_id(
    aas_identifier="urn:uuid:12345678-1234-1234-1234-123456789012",
    submodel_identifier="urn:uuid:submodel-98765",
    bpn="BPNL000000000000"
)
```

**Parameters:**

| Parameter              | Type  | Description                                           |
|------------------------|-------|-------------------------------------------------------|
| `aas_identifier`       | `str` | Shell descriptor identifier                           |
| `submodel_identifier`  | `str` | Submodel descriptor identifier                        |
| `bpn`                  | `str` | Business Partner Number for authorization (optional)  |

### Create Submodel Descriptor

Add a new submodel descriptor to a shell.

```python
from tractusx_sdk.industry.models.aas.v3 import SubModelDescriptor, Endpoint

# Create submodel descriptor
submodel = SubModelDescriptor(
    id="urn:uuid:new-submodel-12345",
    semantic_id={"type": "ExternalReference", "keys": [{"type": "GlobalReference", "value": "urn:samm:io.catenax.part_type_information:1.0.0#PartTypeInformation"}]},
    endpoints=[
        Endpoint(
            interface="SUBMODEL-3.0",
            protocol_information={
                "href": "https://submodel-server.example.com/submodels/12345",
                "endpoint_protocol": "HTTP",
                "endpoint_protocol_version": ["1.1"]
            }
        )
    ]
)

created_submodel = aas_service.create_submodel_descriptor(
    aas_identifier="urn:uuid:12345678-1234-1234-1234-123456789012",
    submodel_descriptor=submodel,
    bpn="BPNL000000000000"
)
```

### Update Submodel Descriptor

Modify an existing submodel descriptor.

```python
updated_submodel = aas_service.update_submodel_descriptor(
    aas_identifier="urn:uuid:12345678-1234-1234-1234-123456789012",
    submodel_identifier="urn:uuid:submodel-12345",
    submodel_descriptor=submodel,
    bpn="BPNL000000000000"
)
```

### Delete Submodel Descriptor

Remove a submodel descriptor from a shell.

```python
result = aas_service.delete_submodel_descriptor(
    aas_identifier="urn:uuid:12345678-1234-1234-1234-123456789012",
    submodel_identifier="urn:uuid:submodel-12345",
    bpn="BPNL000000000000"
)
```

## Asset ID Lookup Operations

### Get Assets by Shell ID

Query specific asset identifiers for a shell descriptor.

```python
asset_ids = aas_service.get_assets_ids_by_asset_administration_shell_id(
    aas_identifier="urn:uuid:12345678-1234-1234-1234-123456789012",
    bpn="BPNL000000000000"
)

for asset_id in asset_ids:
    print(f"{asset_id.name}: {asset_id.value}")
```

### Create Asset ID Links

Associate specific asset identifiers with a shell descriptor.

```python
from tractusx_sdk.industry.models.aas.v3 import SpecificAssetId

specific_asset_ids = [
    SpecificAssetId(
        name="serialNumber",
        value="SN-98765",
        external_subject_id={"type": "ExternalReference", "keys": [{"type": "GlobalReference", "value": "*"}]}
    )
]

result = aas_service.create_all_asset_ids_links_by_asset_administration_shell_id(
    aas_identifier="urn:uuid:12345678-1234-1234-1234-123456789012",
    specific_asset_ids=specific_asset_ids,
    bpn="BPNL000000000000"
)
```

### Delete Asset ID Links

Remove specific asset identifier associations.

```python
result = aas_service.delete_all_asset_ids_links_by_asset_administration_shell_id(
    aas_identifier="urn:uuid:12345678-1234-1234-1234-123456789012",
    bpn="BPNL000000000000"
)
```

## Service Description

Get the DTR service description and metadata.

```python
service_desc = aas_service.get_description()
print(f"Service Version: {service_desc}")
```

## Error Handling

All methods return either the expected response model or a `Result` object on error.

```python
response = aas_service.get_asset_administration_shell_descriptor_by_id(
    aas_identifier="invalid-id"
)

if isinstance(response, Result):
    print(f"Error: {response.messages}")
else:
    # Process successful response
    print(f"Shell ID: {response.id}")
```

## Best Practices

1. **Always use OAuth2 authentication** for production environments
2. **Handle pagination** when querying large registries using `limit` and `cursor`
3. **Validate shell descriptors** before creating or updating
4. **Use BPN filtering** to ensure proper authorization scope
5. **Check response types** to handle both success and error cases

## Further Reading

- [DTR Models](models.md) - Detailed model specifications
- [Industry Library Overview](../index.md)
- [AAS Service Source Code](https://github.com/eclipse-tractusx/tractusx-sdk/blob/main/src/tractusx_sdk/industry/services/aas_service.py)

## NOTICE

This work is licensed under the [CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/legalcode).

- SPDX-License-Identifier: CC-BY-4.0
- SPDX-FileCopyrightText: 2025 Contributors to the Eclipse Foundation
- Source URL: https://github.com/eclipse-tractusx/tractusx-sdk
