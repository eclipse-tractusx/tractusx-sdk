# Quick Start

Get up and running with Tractus-X SDK in minutes.

## Prerequisites

- Python 3.9 or higher
- pip package manager
- Basic understanding of Python and REST APIs

## Installation

Install the Tractus-X SDK using pip:

```bash
pip install tractusx-sdk
```

For local library instalation (intended for development)

```bash
git clone https://github.com/eclipse-tractusx/tractusx-sdk.git
pip install -e .
```

## Basic Usage

### 1. Import the SDK

```python
from tractusx_sdk.dataspace.services.connector.base_connector_provider import (
    BaseConnectorProviderService,
)
```

### 2. Initialize a Connector Client

```python
# Initialize connector provider service
connector = BaseConnectorProviderService(
    dataspace_version="jupiter",  # or "saturn" for newer connectors
    base_url="https://your-edc-connector.example.com",
    dma_path="/management",
    headers={
        "X-Api-Key": "your-api-key",
        "Content-Type": "application/json"
    }
)
```

### 3. Create Your First Asset

```python
# Create a simple data asset
asset = connector.create_asset(
    asset_id="my-first-asset",
    base_url="https://backend.example.com/api/data",
    dct_type="application/json",
    version="3.0"
)

print(f"Asset created: {asset['@id']}")
```

### 4. Query Assets

```python
# List all assets
response = connector.assets.get_all()
assets = response.json()
for asset in assets:
    print(f"Asset ID: {asset['@id']}")
```

## Next Steps

Now that you have the basics down, explore:

- **[Tutorials](../tutorials/getting-started.md)**: Step-by-step guides for common tasks
- **[API Reference](../api-reference/dataspace-library/index.md)**: Detailed API documentation
- **[How-to Guides](../how-to-guides/ic-hub-use-case/industry-core-hub-overview.md)**: Real-world use cases
- **[Core Concepts](../core-concepts/sdk-architecture/sdk-structure-and-components.md)**: Understanding the SDK architecture

## Need Help?

- Check our [GitHub repository](https://github.com/eclipse-tractusx/tractusx-sdk)
- Join the [Matrix chat](https://chat.eclipse.org/#/room/#automotive.tractusx:matrix.eclipse.org)
- Browse [discussions](https://github.com/eclipse-tractusx/tractusx-sdk/discussions)

## Example Projects

Explore complete example projects in the [`examples/`](https://github.com/eclipse-tractusx/tractusx-sdk/tree/main/examples) directory of the repository:

- **Dataspace Services**: EDC connector integration examples
- **Industry Services**: DTR and submodel server examples
- **Extensions**: Custom notification API examples

## NOTICE

This work is licensed under the [CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/legalcode).

- SPDX-License-Identifier: CC-BY-4.0
- SPDX-FileCopyrightText: 2025, 2026 Contributors to the Eclipse Foundation
- SPDX-FileCopyrightText: 2025, 2026 Catena-X Automotive Network e.V.
- SPDX-FileCopyrightText: 2025, 2026 LKS Next
- SPDX-FileCopyrightText: 2025, 2026 Mondragon Unibertsitatea
- Source URL: [https://github.com/eclipse-tractusx/tractusx-sdk](https://github.com/eclipse-tractusx/tractusx-sdk)