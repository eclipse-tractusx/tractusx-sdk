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
# BPN Discovery Service

The BPN Discovery Service enables discovering Business Partner Numbers (BPNs) for assets in the Tractus-X dataspace based on specific identifiers such as manufacturer part IDs, serial numbers, or batch IDs. This service is essential for locating and connecting with business partners in the dataspace ecosystem.

## Purpose

The BPN Discovery Service provides:

- **BPN resolution** - Find Business Partner Numbers for specific asset identifiers
- **Multi-type search** - Query multiple identifier types simultaneously
- **Identifier registration** - Register your identifiers with your BPN
- **Batch operations** - Handle multiple identifiers efficiently
- **Caching** - Improve performance with configurable cache timeout

BPNs are crucial for identifying and authorizing access to digital twins and assets in Tractus-X.

## Key Concepts

### Business Partner Number (BPN)

A BPN is a unique identifier for organizations participating in the Tractus-X dataspace (e.g., `BPNL000000000123`).

### Identifier Types

Common identifier types include:

- `manufacturerPartId` - Manufacturer's part number
- `serialNumber` - Asset serial number
- `batchId` - Batch identifier
- `partInstanceId` - Part instance identifier
- `van` - Vehicle Anonymized Number

## Initialization

```python
from tractusx_sdk.industry.services.discovery import BpnDiscoveryService
from tractusx_sdk.dataspace.services.discovery import DiscoveryFinderService
from tractusx_sdk.dataspace.managers import OAuth2Manager

# Initialize OAuth2 authentication
auth_manager = OAuth2Manager(
    token_url="https://auth.example.com/token",
    client_id="your-client-id",
    client_secret="your-client-secret"
)

# Initialize Discovery Finder Service
discovery_finder = DiscoveryFinderService(
    discovery_finder_url="https://semantics.int.catena-x.net/discoveryfinder/api/v1.0/administration/connectors/discovery",
    oauth=auth_manager
)

# Initialize BPN Discovery Service
bpn_discovery = BpnDiscoveryService(
    oauth=auth_manager,
    discovery_finder_service=discovery_finder,
    cache_timeout_seconds=43200,  # 12 hours
    base_path="/api/v1.0/administration/connectors/bpnDiscovery",
    verbose=True
)
```

### Parameters

| Parameter                  | Type                     | Required | Description                                                      |
|----------------------------|--------------------------|----------|------------------------------------------------------------------|
| `oauth`                    | `OAuth2Manager`          | Yes      | Authentication manager for API access                            |
| `discovery_finder_service` | `DiscoveryFinderService` | Yes      | Service for discovering BPN discovery endpoints                  |
| `cache_timeout_seconds`    | `int`                    | No       | Cache timeout in seconds (default: 43200 = 12 hours)             |
| `session`                  | `requests.Session`       | No       | Custom HTTP session for connection reuse                         |
| `base_path`                | `str`                    | No       | API base path (default: `/api/v1.0/administration/connectors/bpnDiscovery`) |
| `verbose`                  | `bool`                   | No       | Enable verbose logging (default: False)                          |
| `logger`                   | `logging.Logger`         | No       | Custom logger instance                                           |

## Core Operations

### Find BPNs by Identifiers

Discover BPNs for specific asset identifiers.

#### Single Type Search

```python
# Find BPNs for manufacturer part IDs
part_ids = ["MPN-12345", "MPN-67890", "MPN-ABCDE"]
bpns = bpn_discovery.find_bpns(
    keys=part_ids,
    identifier_type="manufacturerPartId"
)

# Result: ['BPNL000000000123', 'BPNL000000000456']
for bpn in bpns:
    print(f"Found BPN: {bpn}")
```

**Parameters:**

| Parameter         | Type  | Description                                                   |
|-------------------|-------|---------------------------------------------------------------|
| `keys`            | `list`| List of identifier values to search for                       |
| `identifier_type` | `str` | Type of identifier (default: `"manufacturerPartId"`)          |

**Returns:** `list` - Unique list of BPNs, or `None` if none found

#### Multi-Type Search

Search across multiple identifier types simultaneously.

```python
# Search for BPNs using multiple identifier types
search_filters = [
    {
        "type": "manufacturerPartId",
        "keys": ["MPN-12345", "MPN-67890"]
    },
    {
        "type": "serialNumber",
        "keys": ["SN-ABC-123", "SN-DEF-456"]
    },
    {
        "type": "batchId",
        "keys": ["BATCH-2024-001"]
    }
]

bpns = bpn_discovery.find_bpns_multi_type(search_filters=search_filters)
print(f"Found {len(bpns)} unique BPNs")
```

**Parameters:**

| Parameter        | Type  | Description                                                             |
|------------------|-------|-------------------------------------------------------------------------|
| `search_filters` | `list`| List of filter dictionaries with `type` and `keys` for each identifier |

**Returns:** `list` - Unique list of BPNs, or `None` if none found

### Get Raw Search Results

Get detailed search results including all metadata.

#### Single Type Search

```python
# Get full search response
response = bpn_discovery.search_bpns(
    keys=["MPN-12345", "MPN-67890"],
    identifier_type="manufacturerPartId"
)

# Response structure:
# {
#     "bpns": [
#         {
#             "type": "manufacturerPartId",
#             "key": "MPN-12345",
#             "value": "BPNL000000000123",
#             "resourceId": "resource-uuid-123"
#         },
#         ...
#     ]
# }

for bpn_entry in response["bpns"]:
    print(f"Key: {bpn_entry['key']} -> BPN: {bpn_entry['value']}")
    print(f"Resource ID: {bpn_entry['resourceId']}")
```

#### Multi-Type Search

```python
# Get full search response for multiple types
search_filters = [
    {"type": "manufacturerPartId", "keys": ["MPN-12345"]},
    {"type": "serialNumber", "keys": ["SN-ABC-123"]}
]

response = bpn_discovery.search_bpns_multi_type(search_filters=search_filters)

for bpn_entry in response["bpns"]:
    print(f"{bpn_entry['type']}: {bpn_entry['key']} -> {bpn_entry['value']}")
```

## Identifier Management

### Register Single Identifier

Associate an identifier with your BPN (requires appropriate permissions).

```python
# Register a manufacturer part ID to your BPN
result = bpn_discovery.set_identifier(
    identifier_key="MPN-NEW-12345",
    identifier_type="manufacturerPartId"
)

print(f"Registered: {result}")
# Response includes BPN association details and resource ID
```

**Parameters:**

| Parameter         | Type  | Description                                              |
|-------------------|-------|----------------------------------------------------------|
| `identifier_key`  | `str` | The identifier value to register                         |
| `identifier_type` | `str` | Type of identifier (default: `"manufacturerPartId"`)     |

**Returns:** `dict` - Response with BPN association details including resource ID

### Register Multiple Identifiers (Batch)

Register multiple identifiers efficiently in a single request.

```python
# Batch register manufacturer part IDs
part_ids = ["MPN-NEW-001", "MPN-NEW-002", "MPN-NEW-003"]

results = bpn_discovery.set_multiple_identifiers(
    identifiers=part_ids,
    identifier_type="manufacturerPartId"
)

print(f"Registered {len(results)} identifiers")
for result in results:
    print(f"Key: {result['key']} -> Resource ID: {result['resourceId']}")
```

**Parameters:**

| Parameter         | Type  | Description                                              |
|-------------------|-------|----------------------------------------------------------|
| `identifiers`     | `list`| List of identifier values to register                    |
| `identifier_type` | `str` | Type of identifier (default: `"manufacturerPartId"`)     |

**Returns:** `list` - List of responses for each registered identifier

### Delete Identifier

Remove an identifier association using its resource ID.

```python
# Delete a BPN identifier association
bpn_discovery.delete_bpn_identifier_by_id(
    resource_id="resource-uuid-123",
    identifier_type="manufacturerPartId"
)

print("Identifier association deleted")
```

**Parameters:**

| Parameter         | Type  | Description                                              |
|-------------------|-------|----------------------------------------------------------|
| `resource_id`     | `str` | The resource ID of the identifier to delete              |
| `identifier_type` | `str` | Type of identifier (default: `"manufacturerPartId"`)     |

**Returns:** None (raises exception if deletion fails)

## Complete Workflow Example

```python
from tractusx_sdk.industry.services.discovery import BpnDiscoveryService
from tractusx_sdk.dataspace.services.discovery import DiscoveryFinderService
from tractusx_sdk.dataspace.managers import OAuth2Manager
from tractusx_sdk.industry.services import AasService

# Initialize services
auth_manager = OAuth2Manager(
    token_url="https://auth.example.com/token",
    client_id="your-client-id",
    client_secret="your-client-secret"
)

discovery_finder = DiscoveryFinderService(
    discovery_finder_url="https://discovery.example.com",
    oauth=auth_manager
)

bpn_discovery = BpnDiscoveryService(
    oauth=auth_manager,
    discovery_finder_service=discovery_finder
)

# Step 1: Find BPNs for manufacturer part IDs
part_ids = ["MPN-TRANSMISSION-001", "MPN-ENGINE-002"]
bpns = bpn_discovery.find_bpns(
    keys=part_ids,
    identifier_type="manufacturerPartId"
)

print(f"Discovered BPNs: {bpns}")

# Step 2: Use BPNs to query Digital Twin Registry
aas_service = AasService(
    base_url="https://dtr.example.com",
    base_lookup_url="https://dtr-lookup.example.com",
    api_path="/api/v3.0",
    auth_service=auth_manager
)

for bpn in bpns:
    # Query shells with BPN authorization
    shells = aas_service.get_all_asset_administration_shell_descriptors(
        bpn=bpn,
        limit=10
    )
    print(f"Found {len(shells.items)} shells for BPN {bpn}")

# Step 3: Register your own identifiers (if provider)
my_part_ids = ["MPN-MY-PART-001", "MPN-MY-PART-002"]
results = bpn_discovery.set_multiple_identifiers(
    identifiers=my_part_ids,
    identifier_type="manufacturerPartId"
)
print(f"Registered {len(results)} identifiers to my BPN")
```

## Multi-Type Discovery Pattern

```python
# Complex search across multiple identifier types
search_filters = [
    {
        "type": "manufacturerPartId",
        "keys": ["MPN-12345", "MPN-67890"]
    },
    {
        "type": "serialNumber",
        "keys": ["SN-ABC-123"]
    },
    {
        "type": "batchId",
        "keys": ["BATCH-2024-Q1"]
    },
    {
        "type": "van",
        "keys": ["VAN-XYZ-789"]
    }
]

# Find all associated BPNs
bpns = bpn_discovery.find_bpns_multi_type(search_filters=search_filters)

# Get detailed results
detailed_results = bpn_discovery.search_bpns_multi_type(search_filters=search_filters)

# Process results by identifier type
for entry in detailed_results["bpns"]:
    print(f"Type: {entry['type']}")
    print(f"Key: {entry['key']}")
    print(f"BPN: {entry['value']}")
    print(f"Resource ID: {entry['resourceId']}")
    print("---")
```

## Caching

The service implements intelligent caching of discovery URLs:

```python
# First call: Fetches and caches discovery URL
bpns1 = bpn_discovery.find_bpns(keys=["MPN-1"], identifier_type="manufacturerPartId")

# Subsequent calls: Uses cached URL (faster)
bpns2 = bpn_discovery.find_bpns(keys=["MPN-2"], identifier_type="manufacturerPartId")

# Cache expires after cache_timeout_seconds (default: 12 hours)
# Then automatically refreshes on next call
```

## Error Handling

```python
try:
    bpns = bpn_discovery.find_bpns(
        keys=["INVALID-KEY"],
        identifier_type="unknownType"
    )
except Exception as e:
    if "Unauthorized" in str(e):
        print("Authentication failed - check credentials")
    elif "not found" in str(e):
        print("Discovery endpoint not available")
    else:
        print(f"Error: {e}")
```

## Best Practices

1. **Use batch operations** - Register multiple identifiers at once for efficiency
2. **Cache wisely** - Set appropriate cache timeout based on your use case
3. **Handle multiple types** - Use multi-type search when dealing with various identifier types
4. **Store resource IDs** - Keep resource IDs if you need to delete identifiers later
5. **Validate permissions** - Ensure proper OAuth scope for identifier registration
6. **Check for None** - `find_bpns()` returns `None` if no BPNs found
7. **Use unique keys** - Deduplicate identifier lists before searching

## Common Identifier Types

| Identifier Type      | Description                          | Example                           |
|----------------------|--------------------------------------|-----------------------------------|
| `manufacturerPartId` | Manufacturer's part number           | `MPN-12345`                       |
| `serialNumber`       | Asset serial number                  | `SN-ABC-123`                      |
| `batchId`            | Batch identifier                     | `BATCH-2024-001`                  |
| `partInstanceId`     | Part instance identifier             | `PI-987654`                       |
| `van`                | Vehicle Anonymized Number            | `VAN-XYZ-789`                     |

## Further Reading

- [Discovery Finder Service](../../dataspace-library/discovery-services/discovery-finder-service.md) - Underlying discovery mechanism
- [DTR Services](../dtr/services.md) - Using BPNs with Digital Twin Registry
- [Industry Library Overview](../index.md)
- [BPN Discovery Service Source Code](https://github.com/eclipse-tractusx/tractusx-sdk/blob/main/src/tractusx_sdk/industry/services/discovery/bpn_discovery_service.py)

## NOTICE

This work is licensed under the [CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/legalcode).

- SPDX-License-Identifier: CC-BY-4.0
- SPDX-FileCopyrightText: 2025 Contributors to the Eclipse Foundation
- Source URL: https://github.com/eclipse-tractusx/tractusx-sdk
