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
# Authentication

The SDK handles authentication in two main ways: OAuth2 with Keycloak (for production environments) and simple API keys (for development or simpler setups).

Both approaches use the same interface, so you can easily switch between them or create your own custom authentication method.

## What's covered here

1. [AuthManagerInterface](#authmanagerinterface) - The basic interface all auth methods use
2. [OAuth2Manager](#oauth2manager) - For OAuth2/Keycloak authentication
3. [AuthManager](#authmanager) - For simple API key authentication

## AuthManagerInterface

All authentication managers work the same way because they follow this interface. Think of it as a contract - every auth manager needs to provide the same basic methods.

### What every auth manager needs to do

There are just two things every authentication manager has to handle:

```python
from tractusx_sdk.dataspace.managers import AuthManagerInterface
from fastapi import Request

class AuthManagerInterface:
    def add_auth_header(self, headers: dict = {}) -> dict:
        """
        Adds authentication information to HTTP headers.
        
        Args:
            headers (dict): Existing headers dictionary (optional)
            
        Returns:
            dict: Updated headers with authentication information
        """
        raise NotImplementedError("add_auth_header must be implemented by subclasses")
    
    def is_authenticated(self, request: Request) -> bool:
        """
        Checks if a request is authenticated.
        
        Args:
            request (Request): FastAPI request object to validate
            
        Returns:
            bool: True if authenticated, False otherwise
        """
        raise NotImplementedError("is_authenticated must be implemented by subclasses")
```

### Making your own auth manager

If you need something custom, just implement these two methods:

```python
class CustomAuthManager(AuthManagerInterface):
    def __init__(self, custom_token):
        self.custom_token = custom_token
    
    def add_auth_header(self, headers: dict = {}) -> dict:
        headers["X-Custom-Auth"] = self.custom_token
        return headers
    
    def is_authenticated(self, request: Request) -> bool:
        auth_header = request.headers.get("X-Custom-Auth")
        return auth_header == self.custom_token
```

### Why this approach?

Having a common interface means:

- All auth managers work the same way
- You can easily swap between OAuth2 and API keys
- Testing is simpler (just mock the interface)
- You can create custom auth methods when needed

## OAuth2Manager

This is for when you need proper OAuth2 authentication through Keycloak. It handles all the token stuff automatically.

### What it does

- Connects to Keycloak servers
- Gets and refreshes tokens automatically  
- Adds Bearer tokens to your requests
- Checks if incoming requests are valid

### How to use it

```python
from tractusx_sdk.dataspace.managers import OAuth2Manager

# Set it up with your Keycloak details
oauth_manager = OAuth2Manager(
    auth_url="https://your-keycloak.com/auth/",
    realm="your-realm",
    clientid="your-client-id",
    clientsecret="your-client-secret"
)

# It connects automatically, but you can reconnect if needed
oauth_manager.connect(auth_url, realm, clientid, clientsecret)

# Get a token
token = oauth_manager.get_token()

# Add auth to your request headers
headers = {"Content-Type": "application/json"}
authenticated_headers = oauth_manager.add_auth_header(headers)
# Now headers includes: "Authorization": "Bearer your-token"
```

### Methods you can use

| Method | What it does |
|--------|--------------|
| `connect(auth_url, realm, clientid, clientsecret)` | Connect to Keycloak |
| `get_token(scope="openid profile email")` | Get an access token |
| `add_auth_header(headers)` | Add Bearer token to your headers |
| `is_authenticated(request)` | Check if a request is valid |

### What's inside

| Property | What it is |
|----------|------------|
| `connected` | True if connected to Keycloak |
| `token` | Current token info |
| `clientid` | Your client ID |
| `clientsecret` | Your client secret |

### When things go wrong

```python
try:
    oauth_manager = OAuth2Manager(
        auth_url="https://your-keycloak.com/auth/",
        realm="your-realm",
        clientid="your-client-id",
        clientsecret="your-client-secret"
    )
    
    token = oauth_manager.get_token()
    print("Got token successfully!")
    
except ConnectionError as e:
    print(f"Can't connect to Keycloak: {e}")
except RuntimeError as e:
    print(f"Not connected: {e}")
except ValueError as e:
    print(f"Couldn't get token: {e}")
```

## AuthManager

This is the simple option - just use an API key. Good for development or when you don't need the complexity of OAuth2.

### How it works

- Uses API keys instead of tokens
- You can customize which header to use
- Can be turned off completely for testing
- Automatically adds the key to your requests

### Basic setup

```python
from tractusx_sdk.dataspace.managers import AuthManager

# Simple API key setup
auth_manager = AuthManager(
    configured_api_key="your-secret-key",
    api_key_header="X-Api-Key",
    auth_enabled=True
)

# Add the key to your request headers
headers = {"Content-Type": "application/json"}
authenticated_headers = auth_manager.add_auth_header(headers)
# Now headers includes: "X-Api-Key": "your-secret-key"

# Check if a request has the right key (for FastAPI apps)
from fastapi import Request
is_valid = auth_manager.is_authenticated(request)
```

### Available methods

| Method | What it does |
|--------|--------------|
| `is_authenticated(request)` | Checks if request has the right API key |
| `add_auth_header(headers)` | Adds API key to headers |

### Properties

| Property | What it is |
|----------|------------|
| `configured_api_key` | The API key you expect |
| `api_key_header` | Which header to use (default: "X-Api-Key") |
| `auth_enabled` | Whether auth is turned on |

### Different setups

```python
# For production - auth required
prod_auth = AuthManager(
    configured_api_key="secure-production-key",
    api_key_header="X-Api-Key",
    auth_enabled=True
)

# For development - no auth needed
dev_auth = AuthManager(
    configured_api_key="dev-key", 
    auth_enabled=False  # Skips auth checks
)

# Custom header name
custom_auth = AuthManager(
    configured_api_key="my-key",
    api_key_header="Authorization",  # Use different header
    auth_enabled=True
)
```

## Using with other services

You'll usually pass auth managers to other SDK services:

```python
from tractusx_sdk.dataspace.managers import OAuth2Manager
from tractusx_sdk.dataspace.services.discovery import DiscoveryFinderService

# Set up OAuth2
oauth_manager = OAuth2Manager(
    auth_url="https://your-keycloak.com/auth/",
    realm="CX-Central",
    clientid="your-client-id",
    clientsecret="your-client-secret"
)

# Pass it to other services
discovery_service = DiscoveryFinderService(
    url="https://discovery-finder.example.com/api/v1.0",
    oauth=oauth_manager
)

# The service handles auth automatically
discovery_urls = discovery_service.find_discovery_urls(keys=["bpn"])
```

## Tips and best practices

### Security stuff

- Use environment variables for secrets (never hardcode them)
- Always use HTTPS in production
- OAuth2 tokens get refreshed automatically
- Change API keys regularly

```python
import os

# Load from environment variables
oauth_manager = OAuth2Manager(
    auth_url=os.getenv("KEYCLOAK_URL"),
    realm=os.getenv("KEYCLOAK_REALM"),
    clientid=os.getenv("CLIENT_ID"),
    clientsecret=os.getenv("CLIENT_SECRET")
)
```

### Error handling

- Check if you're connected before making calls
- OAuth2Manager handles token expiry for you
- Plan for when auth services are down

```python
def safe_api_call(oauth_manager, api_function):
    try:
        if not oauth_manager.connected:
            print("Not connected to auth service")
            return None
        
        return api_function()
        
    except ConnectionError:
        print("Auth service is down")
        return None
    except RuntimeError as e:
        print(f"Auth problem: {e}")
        return None
```

### Performance

- Create auth managers once and reuse them
- Tokens are cached automatically
- Connection pooling is handled for you

## Common problems

### OAuth2 issues

#### Can't connect to Keycloak

- Double-check your `auth_url`
- Make sure you can reach the server from your network
- Verify the realm name exists

#### Can't get tokens

- Check your `clientid` and `clientsecret` are right
- Look at the client settings in Keycloak
- Make sure the client has the right permissions

#### Not connected errors

- Call `connect()` before doing anything else
- Check if the initial setup worked

### API key issues

#### Authentication is not enabled

- Set `auth_enabled=True` when creating the AuthManager
- This happens when you try to get headers but auth is turned off

#### Auth keeps failing

- Make sure the API key is exactly the same
- Check you're using the right header name
- Verify the key is actually being sent in requests

## Further Reading

## Further Reading

- [Discovery Services](../../api-reference/dataspace-library/discovery-services/discovery-finder-service.md) - Learn how to use authentication with discovery services
- [Connector Services](../../api-reference/dataspace-library/connector/services.md) - Using authentication with connector services
- [Dataspace Library Overview](../../api-reference/dataspace-library/index.md) - Complete overview of the dataspace library
- [Getting Started Guide](../../tutorials/getting-started.md) - Start here if you're new to the SDK

## NOTICE

This work is licensed under the [CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/legalcode).

- SPDX-License-Identifier: CC-BY-4.0
- SPDX-FileCopyrightText: 2025 Contributors to the Eclipse Foundation
- Source URL: <https://github.com/eclipse-tractusx/tractusx-sdk>
