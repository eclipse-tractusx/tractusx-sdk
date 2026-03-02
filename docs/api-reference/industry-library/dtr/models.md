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
# DTR Models

The Tractus-X SDK provides a comprehensive set of Digital Twin Registry (DTR) models that define the structure and semantics of Asset Administration Shell (AAS) entities. These models are compliant with the AAS 3.0 specification and enable standardized interaction with digital twin registries in the Tractus-X ecosystem.

## Purpose

DTR models provide a unified way to:

- Define and manage Asset Administration Shell descriptors
- Register and query submodel descriptors with semantic information
- Specify asset identifiers and metadata for digital twins
- Handle endpoint information for data access
- Manage pagination and service responses

By using these models, SDK users can interact with the Digital Twin Registry in a consistent, type-safe, and specification-compliant manner.

## Key Models

Below are the main DTR models grouped by their purpose and relationship within the AAS 3.0 specification.

### Core Digital Twin Models

| Model Name           | Description                                                                  | Key Attributes                                                                                  |
|----------------------|------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------|
| `ShellDescriptor`    | Represents an Asset Administration Shell in the registry                     | `id`, `id_short`, `description`, `specific_asset_ids`, `submodel_descriptors`, `asset_kind`    |
| `SubModelDescriptor` | Describes a submodel associated with a shell                                 | `id`, `id_short`, `semantic_id`, `endpoints`, `description`, `supplemental_semantic_ids`        |
| `SpecificAssetId`    | Unique identifier for an asset with visibility control                       | `name`, `value`, `external_subject_id`, `semantic_id`                                           |

### Endpoint and Protocol Models

| Model Name                                  | Description                                                        | Key Attributes                                                           |
|---------------------------------------------|--------------------------------------------------------------------|--------------------------------------------------------------------------|
| `Endpoint`                                  | Defines access endpoints for submodels                             | `interface`, `protocol_information`                                      |
| `ProtocolInformation`                       | Protocol details for endpoint communication                        | `href`, `endpoint_protocol`, `endpoint_protocol_version`, `security_attributes` |
| `ProtocolInformationSecurityAttributes`     | Security configuration for endpoints                               | `type`, `key`, `value`                                                   |

### Reference and Semantic Models

| Model Name     | Description                                                                 | Key Attributes                           |
|----------------|-----------------------------------------------------------------------------|------------------------------------------|
| `Reference`    | Semantic reference to external concepts or specifications                   | `type`, `keys`                           |
| `ReferenceKey` | Individual key element in a reference chain                                 | `type`, `value`                          |
| `MultiLanguage`| Language-specific text for internationalization                             | `language`, `text`                       |

### Response and Pagination Models

| Model Name                            | Description                                                      | Key Attributes                                          |
|---------------------------------------|------------------------------------------------------------------|---------------------------------------------------------|
| `GetAllShellDescriptorsResponse`      | Response for querying all shell descriptors                      | `items`, `paging_metadata`                              |
| `GetSubmodelDescriptorsByAssResponse` | Response for querying submodels by shell ID                      | `result`, `paging_metadata`                             |
| `PagingMetadata`                      | Metadata for paginated responses                                 | `cursor`                                                |
| `ServiceDescription`                  | Service description and metadata                                 | `profiles`                                              |
| `Result`                              | Generic result object for error or non-standard responses        | `messages`                                              |

### Enumerations

| Enum Name                                  | Description                                   | Values                                                                    |
|--------------------------------------------|-----------------------------------------------|---------------------------------------------------------------------------|
| `AssetKind`                                | Type of asset                                 | `INSTANCE`, `TYPE`, `NOT_APPLICABLE`                                      |
| `ReferenceTypes`                           | Type of semantic reference                    | `ExternalReference`, `ModelReference`                                     |
| `ReferenceKeyTypes`                        | Type of reference key                         | `GlobalReference`, `FragmentReference`, `Submodel`, `AssetAdministrationShell`, etc. |
| `ProtocolInformationSecurityAttributesTypes` | Security attribute types                      | `NONE`, `RFC_TLSA`, `W3C_DID`                                             |
| `MessageTypeEnum`                          | Type of result message                        | `Undefined`, `Info`, `Warning`, `Error`, `Exception`                      |
| `ProfileEnum`                              | Service profile types                         | `AasxFileServerServiceSpecification`, `AssetAdministrationShellRepositoryServiceSpecification`, etc. |

## Model Details and Examples

### ShellDescriptor

The `ShellDescriptor` represents the main entry point for a digital twin in the registry.

```python
from tractusx_sdk.industry.models.aas.v3 import (
    ShellDescriptor,
    SpecificAssetId,
    SubModelDescriptor,
    AssetKind,
    Reference,
    ReferenceKey,
    ReferenceTypes,
    ReferenceKeyTypes
)

# Create specific asset identifiers
specific_asset_ids = [
    SpecificAssetId(
        name="manufacturerPartId",
        value="MPN-12345",
        external_subject_id=Reference(
            type=ReferenceTypes.EXTERNAL_REFERENCE,
            keys=[
                ReferenceKey(
                    type=ReferenceKeyTypes.GLOBAL_REFERENCE,
                    value="*"  # Public visibility
                )
            ]
        )
    ),
    SpecificAssetId(
        name="serialNumber",
        value="SN-98765-ABC",
        external_subject_id=Reference(
            type=ReferenceTypes.EXTERNAL_REFERENCE,
            keys=[
                ReferenceKey(
                    type=ReferenceKeyTypes.GLOBAL_REFERENCE,
                    value="BPNL000000000000"  # Restricted to specific BPN
                )
            ]
        )
    )
]

# Create shell descriptor
shell = ShellDescriptor(
    id="urn:uuid:12345678-1234-1234-1234-123456789012",
    id_short="MyDigitalTwin",
    description=[
        {"language": "en", "text": "Digital Twin for Product XYZ"},
        {"language": "de", "text": "Digitaler Zwilling für Produkt XYZ"}
    ],
    specific_asset_ids=specific_asset_ids,
    submodel_descriptors=[],
    asset_kind=AssetKind.INSTANCE
)
```

**Key Attributes:**

| Attribute              | Type                      | Required | Description                                                    |
|------------------------|---------------------------|----------|----------------------------------------------------------------|
| `id`                   | `str`                     | Yes      | Unique identifier (URN or UUID format)                         |
| `id_short`             | `str`                     | No       | Short human-readable identifier                                |
| `description`          | `List[MultiLanguage]`     | No       | Multi-language description                                     |
| `specific_asset_ids`   | `List[SpecificAssetId]`   | No       | Asset identifiers with visibility control                      |
| `submodel_descriptors` | `List[SubModelDescriptor]`| No       | Associated submodel descriptors                                |
| `asset_kind`           | `AssetKind`               | No       | Type of asset (INSTANCE, TYPE, or NOT_APPLICABLE)              |
| `asset_type`           | `str`                     | No       | Asset type classification                                      |

### SubModelDescriptor

The `SubModelDescriptor` defines a submodel that contains detailed information about an asset.

```python
from tractusx_sdk.industry.models.aas.v3 import (
    SubModelDescriptor,
    Endpoint,
    ProtocolInformation,
    Reference,
    ReferenceKey,
    ReferenceTypes,
    ReferenceKeyTypes
)

# Create endpoint with protocol information
endpoint = Endpoint(
    interface="SUBMODEL-3.0",
    protocol_information=ProtocolInformation(
        href="https://submodel-server.example.com/api/v3.0/submodel",
        endpoint_protocol="HTTPS",
        endpoint_protocol_version=["1.1"],
        subprotocol="DSP",
        subprotocol_body="id=123;dspEndpoint=http://example.com/dsp",
        subprotocol_body_encoding="plain"
    )
)

# Create submodel descriptor
submodel = SubModelDescriptor(
    id="urn:uuid:submodel-12345",
    id_short="PartTypeInformation",
    semantic_id=Reference(
        type=ReferenceTypes.EXTERNAL_REFERENCE,
        keys=[
            ReferenceKey(
                type=ReferenceKeyTypes.GLOBAL_REFERENCE,
                value="urn:samm:io.catenax.part_type_information:1.0.0#PartTypeInformation"
            )
        ]
    ),
    description=[
        {"language": "en", "text": "Part Type Information Submodel"}
    ],
    endpoints=[endpoint]
)
```

**Key Attributes:**

| Attribute                    | Type                   | Required | Description                                                    |
|------------------------------|------------------------|----------|----------------------------------------------------------------|
| `id`                         | `str`                  | Yes      | Unique identifier for the submodel                             |
| `id_short`                   | `str`                  | No       | Short human-readable identifier                                |
| `semantic_id`                | `Reference`            | No       | Semantic reference to aspect model specification               |
| `supplemental_semantic_ids`  | `List[Reference]`      | No       | Additional semantic references                                 |
| `description`                | `List[MultiLanguage]`  | No       | Multi-language description                                     |
| `endpoints`                  | `List[Endpoint]`       | No       | Access endpoints for submodel data                             |

### SpecificAssetId

The `SpecificAssetId` model provides identification and access control for assets.

```python
from tractusx_sdk.industry.models.aas.v3 import (
    SpecificAssetId,
    Reference,
    ReferenceKey,
    ReferenceTypes,
    ReferenceKeyTypes
)

# Public asset identifier (visible to all)
public_id = SpecificAssetId(
    name="manufacturerPartId",
    value="MPN-ABCD-1234",
    external_subject_id=Reference(
        type=ReferenceTypes.EXTERNAL_REFERENCE,
        keys=[
            ReferenceKey(
                type=ReferenceKeyTypes.GLOBAL_REFERENCE,
                value="*"
            )
        ]
    )
)

# Restricted asset identifier (visible only to specific BPN)
restricted_id = SpecificAssetId(
    name="customerPartId",
    value="CPN-XYZ-9876",
    external_subject_id=Reference(
        type=ReferenceTypes.EXTERNAL_REFERENCE,
        keys=[
            ReferenceKey(
                type=ReferenceKeyTypes.GLOBAL_REFERENCE,
                value="BPNL123456789012"
            )
        ]
    )
)
```

**Key Attributes:**

| Attribute             | Type        | Required | Description                                                          |
|-----------------------|-------------|----------|----------------------------------------------------------------------|
| `name`                | `str`       | Yes      | Name of the asset identifier type (e.g., "manufacturerPartId")       |
| `value`               | `str`       | Yes      | Value of the asset identifier                                        |
| `external_subject_id` | `Reference` | Yes      | Controls visibility (`*` = public, BPN = restricted to that partner) |
| `semantic_id`         | `Reference` | No       | Semantic reference for the identifier type                           |

### Endpoint and ProtocolInformation

Endpoints define how to access submodel data.

```python
from tractusx_sdk.industry.models.aas.v3 import (
    Endpoint,
    ProtocolInformation,
    ProtocolInformationSecurityAttributes,
    ProtocolInformationSecurityAttributesTypes
)

# Create security attributes (optional)
security_attrs = ProtocolInformationSecurityAttributes(
    type=ProtocolInformationSecurityAttributesTypes.NONE,
    key="authType",
    value="bearer"
)

# Create protocol information
protocol_info = ProtocolInformation(
    href="https://api.example.com/submodel/data",
    endpoint_protocol="HTTPS",
    endpoint_protocol_version=["1.1"],
    subprotocol="DSP",
    subprotocol_body="id=123;dspEndpoint=http://connector.example.com",
    subprotocol_body_encoding="plain",
    security_attributes=[security_attrs]
)

# Create endpoint
endpoint = Endpoint(
    interface="SUBMODEL-3.0",
    protocol_information=protocol_info
)
```

## Response Models

### GetAllShellDescriptorsResponse

Response model for querying multiple shell descriptors with pagination.

```python
response = aas_service.get_all_asset_administration_shell_descriptors(limit=50)

# Access shell descriptors
for shell in response.items:
    print(f"Shell ID: {shell.id}")
    print(f"Asset Kind: {shell.asset_kind}")

# Handle pagination
if response.paging_metadata and response.paging_metadata.cursor:
    next_page = aas_service.get_all_asset_administration_shell_descriptors(
        limit=50,
        cursor=response.paging_metadata.cursor
    )
```

### Result

Generic result object for error handling.

```python
result = aas_service.delete_asset_administration_shell_descriptor(
    aas_identifier="invalid-id"
)

if isinstance(result, Result):
    for message in result.messages:
        print(f"{message.message_type}: {message.text}")
        print(f"Code: {message.code}")
```

## Best Practices

1. **Always specify `external_subject_id`** for `SpecificAssetId` to control visibility
2. **Use semantic references** (`semantic_id`) to link submodels to standardized aspect models
3. **Provide multi-language descriptions** for better internationalization support
4. **Validate URN formats** for IDs (should follow `urn:uuid:` pattern or similar)
5. **Include endpoint information** for all submodels to enable data access
6. **Use AssetKind.INSTANCE** for physical/digital instances and **AssetKind.TYPE** for templates

## Model Validation

All models include Pydantic validation to ensure data integrity:

```python
from pydantic import ValidationError

try:
    shell = ShellDescriptor(
        id="invalid-id",  # Should be URN format
        id_short="Test"
    )
except ValidationError as e:
    print(f"Validation error: {e}")
```

## Further Reading

- [DTR Services](services.md) - Service methods for working with these models
- [Industry Library Overview](../index.md)
- [AAS Models Source Code](https://github.com/eclipse-tractusx/tractusx-sdk/blob/main/src/tractusx_sdk/industry/models/aas/v3/)

## NOTICE

This work is licensed under the [CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/legalcode).

- SPDX-License-Identifier: CC-BY-4.0
- SPDX-FileCopyrightText: 2025 Contributors to the Eclipse Foundation
- Source URL: https://github.com/eclipse-tractusx/tractusx-sdk
