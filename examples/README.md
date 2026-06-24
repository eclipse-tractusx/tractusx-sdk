# Tractus-X SDK Examples

This directory contains p- **File**: `extensions/semantics/schema_to_context_translator_example.py`
- **Purpose**: Demonstrates automatic SAMM schema fetching and JSON-LD context conversion

- **Features**:
  - Automatic schema fetching from Tractus-X repository
  - SAMM to JSON-LD context transformation
  - Verifiable credential creation support

## Prerequisites

Before running any examples, ensure you have:

1. **Python Environment**: Python 3.8+ with the Tractus-X SDK installed

   ```bash
   pip install tractusx-sdk
   ```es demonstrating how to use the Tractus-X SDK for various dataspace and industry-specific operations. The examples are organized by domain and functionality to help you get started quickly.

## Overview

The Tractus-X SDK Examples showcase real-world usage patterns for:

- **Dataspace Operations**: Connector discovery and dataspace interactions
- **Industry Services**: Business Partner Number (BPN) discovery and industry-specific workflows  
- **Extensions**: Semantic model handling and schema transformations

## Directory Structure

```text
examples/
├── dataspace/           # Dataspace-related examples
│   └── services/
│       └── discovery/   # Connector discovery examples
├── industry/            # Industry-specific examples
│   └── services/
│       └── discovery/   # BPN discovery examples
└── extensions/          # SDK extension examples
    ├── semantics/       # Semantic model examples
    └── geometry/        # Geometry aspect validator examples
        └── exampleData/ # Example SingleLevelSceneNode JSON files
```

## Available Examples

### 🌐 Dataspace Examples

#### Connector Discovery

- **File**: `dataspace/services/discovery/connector_discovery_example.py`
- **Purpose**: Demonstrates how to discover and connect to EDC connectors in the dataspace
- **Features**:
  - OAuth2 authentication setup
  - Discovery finder service integration
  - Connector endpoint discovery

### 🏭 Industry Examples

#### BPN Discovery

- **File**: `industry/services/discovery/bpn_discovery_example.py`
- **Purpose**: Shows how to discover Business Partner Numbers using manufacturer part IDs
- **Features**:
  - BPN lookup by manufacturer part ID
  - Integration with discovery services
  - Industry-specific data retrieval

### 🔧 Extension Examples

#### Semantic Schema Translation

- **File**: `extensions/semantics/schema_to_context_translator_example.py`
- **Purpose**: Demonstrates automatic SAMM schema fetching and JSON-LD context conversion, and shows how to extend the SDK.
- **Features**:
  - Automatic schema fetching from Tractus-X repository
  - SAMM to JSON-LD context transformation
  - Verifiable credential creation support

#### Geometry Aspect Validator

- **File**: `extensions/geometry/geometry_aspect_validator_example.py`
- **Purpose**: Demonstrates how to validate SingleLevelSceneNode JSON files against the Catena-X schema.
- **Features**:
  - Schema loading from the official Tractus-X repository
  - Single scene node validation
  - Recursive child reference resolution and validation
  - Configurable validation levels (error, warning, info)

## Prerequisites

Before running any examples, ensure you have:

1. **Python Environment**: Python 3.8+ with the Tractus-X SDK installed
   ```bash
   pip install tractusx-sdk
   ```

2. **Configuration**: Each example requires specific configuration values:
   - OAuth2 credentials (realm, client ID, client secret)
   - Service URLs (authentication, discovery endpoints)
   - Test data (BPNs, part IDs, etc.)

3. **Network Access**: Access to the Tractus-X dataspace services and endpoints

## Running the Examples

### Configuration Setup

Most examples require you to replace placeholder values with your actual configuration:

```python
YOUR_REALM = "CX-Central"  # Your OAuth2 realm
YOUR_CLIENT_ID = "your-client-id"  # Your OAuth2 client ID  
YOUR_CLIENT_SECRET = "your-client-secret"  # Your OAuth2 client secret
YOUR_AUTH_URL = "https://your-idp.example.com/auth/"  # Authentication URL
YOUR_DISCOVERY_FINDER_URL = "https://discovery.example.com"  # Discovery service URL
```

### Execution

Navigate to the example directory and run:

```bash
# For dataspace connector discovery
cd examples/dataspace/services/discovery/
python connector_discovery_example.py

# For BPN discovery
cd examples/industry/services/discovery/
python bpn_discovery_example.py

# For semantic schema translation
cd examples/extensions/semantics/
python schema_to_context_translator_example.py

# For geometry aspect validation
cd examples/extensions/geometry/
python geometry_aspect_validator_example.py
```


## NOTICE

This work is licensed under the [CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/legalcode).

- SPDX-License-Identifier: CC-BY-4.0
- SPDX-FileCopyrightText: 2025 Contributors to the Eclipse Foundation
- Source URL: <https://github.com/eclipse-tractusx/tractusx-sdk>
