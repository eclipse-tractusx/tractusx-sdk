
# Installation Guide for `tractusx-sdk`

This document will help you get started with installing and using the `tractusx-sdk` Python package.

## Prerequisites

- Python 3.12.0 or higher
- `pip` (Python package installer)

It's recommended to use a virtual environment to avoid conflicts with other packages:

```bash
python -m venv venv
source venv/bin/activate   # On Windows, use `venv\Scripts\activate`
```

## Installation

Install the package directly from PyPI:

```bash
pip install tractusx-sdk
```

## Upgrade to the Latest Version

To upgrade to the latest version of `tractusx-sdk`:

```bash
pip install --upgrade tractusx-sdk
```

## Basic Usage

Here's a quick example of how to use the SDK:

```python
from tractusx_sdk.dataspace.services.connector.v0_9_0.edc_service import ConnectorService

edc_service = ConnectorService(
    base_url="https://control.plane.url", 
    dma_path="management",
    headers={
            "X-Api-Key": "your-api-key",
            "Content-Type": "application/json"
    })

context =  {
    "edc": "https://w3id.org/edc/v0.0.1/ns/",
    "cx-common": "https://w3id.org/catenax/ontology/common#",
    "cx-taxo": "https://w3id.org/catenax/taxonomy#",
    "dct": "http://purl.org/dc/terms/"
}

data_address = { 
        "@type": "DataAddress",
        "type": "HttpData",
        "baseUrl": "<<base-url>>"
    }

properties:dict = {
        "dct:type": {
            "@id": dct_type
        }
    }

asset = ModelFactory.get_asset_model(
    connector_version="v0_9_0",
    context=context,
    oid="<<your-asset-id>>",
    properties=properties,
    private_properties=[],
    data_address=data_address
)

asset_response = self.edc_service.assets.create(obj=asset)

# Example usage
print(asset_response.json())
```

> **Note**: Replace `"your-api-key"` with your actual API key or credentials as required.

## Documentation

For more information, refer to the official documentation or README.

Here you will find more documentation regarding the usage of the SDK:

[Tractus-X Usage Documentation](./docs/user/README.md)

## Troubleshooting

- Ensure Python version is compatible
- Use `--no-cache-dir` with pip if encountering caching issues:
  ```bash
  pip install --no-cache-dir tractusx-sdk
  ```

## NOTICE

This work is licensed under the [CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/legalcode).

- SPDX-License-Identifier: CC-BY-4.0
- SPDX-FileCopyrightText: 2025 Contributors to the Eclipse Foundation
- Source URL: https://github.com/eclipse-tractusx/tractusx-sdk
