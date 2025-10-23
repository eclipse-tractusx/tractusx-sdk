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
# Discovery Finder Service

The Discovery Finder Service helps you locate other discovery services in the Tractus-X dataspace. Think of it as a phone book for finding the right service endpoints based on what you're looking for.

## What it does

When you need to find a specific type of discovery service (like BPN discovery or part ID discovery), the Discovery Finder Service tells you where to find it. Instead of hardcoding URLs, you can dynamically discover the current endpoints.

**How it works:**

1. Ask the Discovery Finder for a specific discovery type (e.g., "bpn")
2. Get back the URL where that service is running  
3. Use that URL with other services like ConnectorDiscoveryService

This is especially useful because service endpoints can change, and the Discovery Finder keeps track of the current locations.

## What you can do with it

The service supports different types of discoveries:

- **BPN Discovery**: Find connector endpoints for Business Partner Numbers
- **Part ID Discovery**: Locate services for manufacturer part identification  
- **Custom Types**: Works with any discovery type that gets added to the system

You can also ask for multiple discovery types at once instead of making separate requests.

## Setting it up

The service handles OAuth2 authentication automatically once you provide the credentials, and it's flexible enough to work with different API response formats if needed.

## Core Methods

| Method Name | Parameters | Description | Return Type |
|-------------|------------|-------------|-------------|
| `find_discovery_urls` | `keys: list = ["bpn"]` | Finds discovery service URLs for specified types | `dict` |

## Getting started

First, import what you need:

```python
from tractusx_sdk.dataspace.managers import OAuth2Manager
from tractusx_sdk.dataspace.services.discovery import DiscoveryFinderService
```

Then set up the service with your OAuth2 credentials:

```python
# Set up authentication
oauth_manager = OAuth2Manager(
    realm="CX-Central",
    clientid="your-client-id",
    clientsecret="your-client-secret", 
    auth_url="https://your-auth-server.com"
)
oauth_manager.connect()

# Create the discovery finder
discovery_finder = DiscoveryFinderService(
    url="https://your-discovery-finder.com/api/v1.0/administration/connectors/discovery/search",
    oauth=oauth_manager
)
```

## Basic usage

```python
# Find discovery URLs for common types
discovery_urls = discovery_finder.find_discovery_urls(keys=["bpn", "manufacturerPartId"])
print(discovery_urls)  # {'bpn': '...', 'manufacturerPartId': '...'}
```

## Error handling

Things can go wrong, so wrap your calls in try/catch blocks:

```python
try:
    discovery_urls = discovery_finder.find_discovery_urls(keys=["bpn"])
    print(f"BPN Discovery URL: {discovery_urls['bpn']}")
    
except ConnectionError as e:
    print(f"Authentication error: {e}")
    print("Make sure OAuth2 is connected with oauth_manager.connect()")
    
except Exception as e:
    print(f"Something went wrong: {e}")
```

## Using with other services

The Discovery Finder is often used with ConnectorDiscoveryService:

```python
from tractusx_sdk.dataspace.services.discovery import ConnectorDiscoveryService

# Pass the discovery finder to connector discovery
connector_discovery = ConnectorDiscoveryService(
    oauth=oauth_manager,
    discovery_finder_service=discovery_finder,
    connector_discovery_key="bpn"
)

# Now find connector endpoints for a BPN
endpoints = connector_discovery.find_connector_by_bpn("BPNL000000000001")
print(endpoints)
```

## Common problems

### Authentication not connected

Make sure you call `oauth_manager.connect()` first:

```python
oauth_manager.connect()  # Do this before using discovery_finder
```

### Response was not successful

- Check your discovery finder URL is correct
- Verify your OAuth2 credentials
- Make sure the service is running and accessible

### No endpoints found

- Double-check the discovery type names (e.g., "bpn", not "BPN")
- The discovery services might not be registered yet
- Try a different discovery type to test

!!! tip
    - **Cache the results** - Discovery URLs don't change often, so you can cache them
    - **Batch requests** - Ask for multiple discovery types at once instead of separate calls  
    - **Reuse instances** - Create one Discovery Finder and use it throughout your app
    - **Use environment variables** - Store OAuth2 credentials securely
    - **Check authentication** - Make sure OAuth2 is connected before making requests

## Further Reading

- [Dataspace Library Overview](../index.md)
- [Connector Discovery Service](./connector-discovery-service.md)
- [BPN Discovery Service](../../industry-library/discovery-services/bpn-discovery.md)
- [OAuth2 Authentication](../../../core-concepts/authentication-security/authentication.md)
- [API Reference](https://eclipse-tractusx.github.io/api-hub/)

## NOTICE

This work is licensed under the [CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/legalcode).

- SPDX-License-Identifier: CC-BY-4.0
- SPDX-FileCopyrightText: 2025 Contributors to the Eclipse Foundation
- Source URL: <https://github.com/eclipse-tractusx/tractusx-sdk>
