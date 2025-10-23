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
# Connector Discovery Service

The Connector Discovery Service helps you find connector endpoints for other companies (identified by their Business Partner Numbers or BPNs) in the Tractus-X dataspace. Once you know where a partner's connector is, you can start exchanging data with them.

## How it works

This service works together with the Discovery Finder Service:

1. The Discovery Finder tells it where to look for connector information
2. It searches for connectors using a company's BPN  
3. It gives you back the connector endpoints you can use to communicate

It also caches results so you don't have to look up the same information repeatedly.

## What it does

- **Find connectors**: Give it a BPN, get back connector URLs
- **Cache results**: Remembers previous lookups to speed things up  
- **Handle authentication**: Works with OAuth2 automatically
- **Support different formats**: Adapts to various API response formats

The service makes it simple to find and connect to other participants in the dataspace without worrying about the underlying complexity.

## Available methods

| Method | Parameters | What it does |
|--------|------------|--------------|
| `find_connector_by_bpn` | `bpn: str`, `bpn_key: str="bpn"`, `connector_endpoint_key: str="connectorEndpoint"` | Finds connector endpoints for a BPN |
| `get_discovery_url` | `discovery_finder_service: DiscoveryFinderService`, `discovery_key: str` | Gets the discovery URL for a specific key |
| `invalidate_cache_entry` | `connector_discovery_key: str=None` | Clears cached results (uses default key if None) |
| `flush_cache` | None | Clears all cached discovery URLs |
| `get_cache_status` | None | Returns information about the current cache state |

## Main attributes

| Attribute/Parameter        | Type                    | Description                                                      |
|---------------------------|-------------------------|------------------------------------------------------------------|
| `oauth`                   | OAuth2Manager           | Handles authentication for requests (instance attribute)          |
| `discovery_finder_service`| DiscoveryFinderService  | Used to look up discovery endpoints (instance attribute)          |
| `connector_discovery_key` | str                     | Key used for connector discovery (default: "bpn") (instance)     |
| `cache_timeout_seconds`   | int                     | Cache timeout in seconds (default: 43200 = 12 hours) (instance)   |
| `verbose`                 | bool                    | Enables verbose logging (default: False) (instance)               |
| `logger`                  | Optional[logging.Logger]| Custom logger instance (default: None) (instance)                 |
| `bpn_key`                 | str                     | Key for BPN in API response (default: "bpn") (method param)      |
| `connector_endpoint_key`  | str                     | Key for connector endpoints in response (default: "connectorEndpoint") (method param) |

## Getting started

### What you need

Import the required components:

```python
from tractusx_sdk.dataspace.managers import OAuth2Manager
from tractusx_sdk.dataspace.services.discovery import DiscoveryFinderService, ConnectorDiscoveryService
```

### Basic setup

```python
# Set up authentication
oauth_manager = OAuth2Manager(
    realm="CX-Central",
    clientid="your-client-id",
    clientsecret="your-client-secret",
    auth_url="https://your-auth-server.com/auth/"
)
oauth_manager.connect()

# Set up discovery finder (see Discovery Finder docs for details)
discovery_finder = DiscoveryFinderService(
    url="https://your-discovery-finder.com/api/v1.0/administration/connectors/discovery/search",
    oauth=oauth_manager
)

# Create connector discovery service
connector_discovery = ConnectorDiscoveryService(
    oauth=oauth_manager,
    discovery_finder_service=discovery_finder,
    connector_discovery_key="bpn",          # Optional, defaults to "bpn"
    cache_timeout_seconds=43200,            # Optional, defaults to 12 hours
    verbose=False,                          # Optional, defaults to False
    logger=None                             # Optional, provide custom logger
)
```

## Basic usage

```python
# Find connector endpoints for a company
bpn = "BPNL000000000001"
connector_endpoints = connector_discovery.find_connector_by_bpn(bpn)

if connector_endpoints:
    print(f"Found {len(connector_endpoints)} connectors for {bpn}:")
    for endpoint in connector_endpoints:
        print(f"  - {endpoint}")
else:
    print(f"No connectors found for {bpn}")
```

If your API uses different field names in the response, you can customize them:

```python
# For APIs with different response format
connector_endpoints = connector_discovery.find_connector_by_bpn(
    bpn="BPNL000000000001",
    bpn_key="bpn",        # If response uses different BPN field name
    connector_endpoint_key="endpointUrls"   # If response uses different endpoint field name
)
```

## Working with the cache

The service caches discovery URLs to avoid repeated lookups:

```python
# Clear cached results for the default discovery key
connector_discovery.invalidate_cache_entry()

# Or clear for a specific key
connector_discovery.invalidate_cache_entry("bpn")

# Clear all cached discovery URLs
cleared_count = connector_discovery.flush_cache()
print(f"Cleared {cleared_count} cached entries")

# Check cache status
cache_info = connector_discovery.get_cache_status()
print(f"Cache contains {cache_info['total_entries']} entries")
```

## Error handling

```python
try:
    connectors = connector_discovery.find_connector_by_bpn("BPNL000000000001")
    if connectors:
        print(f"Found connectors: {connectors}")
    else:
        print("No connectors found for this BPN")
        
except ConnectionError as e:
    print(f"Authentication problem: {e}")
except Exception as e:
    print(f"Something went wrong: {e}")
```

## Common problems

### Authentication not connected

Make sure you connect to OAuth2 first:

```python
oauth_manager.connect()  # Do this before using the service
```

### Connector discovery endpoint not found

- Check your discovery finder URL is correct
- Verify the discovery key ("bpn") exists in the system

### Empty results

- The BPN might not exist in the dataspace
- The company might not have any registered connectors yet
- Try a different BPN to test if the service is working

## Debugging

Turn on verbose logging to see what's happening:

```python
connector_discovery = ConnectorDiscoveryService(
    oauth=oauth_manager,
    discovery_finder_service=discovery_finder,
    verbose=True  # This will show detailed logs
)
```

!!! tip
    - **Cache timeout**: The default 12-hour cache works for most cases, but adjust if endpoints change frequently
    - **Batch lookups**: If you need to find multiple BPNs, consider caching the discovery service instance  
    - **Error handling**: Always check if endpoints are returned before trying to use them
    - **Security**: Store OAuth2 credentials in environment variables, not in code

## Further Reading

- [Dataspace Library Overview](../index.md)
- [Discovery Finder Service](./discovery-finder-service.md)
- [Connector Services](../connector/services.md)
- [OAuth2 Authentication](../../../core-concepts/authentication-security/authentication.md)
- [API Reference](https://eclipse-tractusx.github.io/api-hub/)

## NOTICE

This work is licensed under the [CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/legalcode).

- SPDX-License-Identifier: CC-BY-4.0
- SPDX-FileCopyrightText: 2025 Contributors to the Eclipse Foundation
- Source URL: <https://github.com/eclipse-tractusx/tractusx-sdk>
