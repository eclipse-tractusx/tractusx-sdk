<!--

Eclipse Tractus-X - Software Development KIT

Copyright (c) 2025 Contributors to the Eclipse Foundation

See the NOTICE file(s) distributed with this work for additional
information regarding copyright ownership.

This work is made available under the terms of the
Creative Commons Attribution 4.0 International (CC-BY-4.0) license,
which is available at
https://creativecommons.org/licenses/by/4.0/legalcode.

SPDX-License-Identifier: CC-BY-4.0

-->

<!-- 
    Template Generated using an LLM AI Agent
    Revised by an human committer
-->

# Eclipse Tractus-X Industry Software Development KIT (SDK)

Welcome to the Eclipse Tractus-X Industry Software Development KIT! This SDK is designed to provide a comprehensive set of tools and services for handling the basic components from the Tractus-X dataspace. Using this SDK you will be able to embed into your application the logic for handling the Digital Twin Registry (DTR) and the Submodel Server.  Below is an overview of the folder structure and the purpose of each directory.

## Folder Structure

```
industry/
    ├── config
    ├── managers
    ├── models
    ├── services
    ├── tests
    ├── tools
```

## Install in your local environment

1. Go to the root '/' folder
2. Run `pip install -e .`
3. It will install the SDK in your local environment
4. Import the SDK like this:

```python
   from tractusx_sdk.industry.services import AasService
```

## Run it in your local environment

1. Install requirements:

`poetry install`

2. Run the script:

```poetry run python3 src/tractusx_sdk/industry/main.py --host 0.0.0.0 --port 8000```

## Build and Deploy with Docker

1. Go to the root '/' folder

2. Build the Docker image:

```bash
docker build -t industry:latest --no-cache -f src/tractusx_sdk/industry/Dockerfile .
```

3. Run the Docker image:

```bash
docker run -p 8000:8000 industry:latest
```

### docs/
This directory contains documentation files, including user guides, API references, and other relevant documentation to help you understand and use the SDK effectively.

### scripts/
The `scripts/` directory is for standalone scripts that assist in various tasks related to the SDK. These scripts can be used for automation, setup, or other utility purposes.

### examples/
In the `examples/` directory, you'll find sample code and usage examples that demonstrate how to use the SDK. These examples are designed to help you get started quickly and understand the SDK's capabilities.

### src/
The `src/` directory contains all the source code for the SDK. It is organized into several subdirectories:

- **config/**: Configuration files and settings used throughout the SDK.
- **managers/**: Classes that handle the management of different components within the SDK and the data handling.
- **models/**: Data models and schemas that define the structure of the data used by the SDK.
- **services/**: Service classes and functions that provide the core functionality of the SDK and contact to external services.
- **tests/**: Unit and integration tests to ensure that all components of the SDK function as expected.
- **tools/**: Utility scripts and helper functions that support the development and maintenance of the SDK. Comparable to utilities.

## Getting Started

To get started with Software Development KIT, follow these steps:

1. **Installation**: Provide instructions on how to install the SDK.
2. **Configuration**: Explain how to configure the SDK using files from the `config/` directory.
3. **Usage**: Provide examples of how to use the SDK, including code snippets and explanations.

## Contributing

If you'd like to contribute to Software Development KIT, please follow the guidelines in the `CONTRIBUTING.md` file.

## Licenses

- [Apache-2.0](https://raw.githubusercontent.com/eclipse-tractusx/tractusx-sdk/main/LICENSE) for code
- [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html) for non-code
---

Thank you for using Software Development KIT! If you have any questions or need further assistance, please feel free to reach out.

## NOTICE

This work is licensed under the [CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/legalcode).

- SPDX-License-Identifier: CC-BY-4.0
- SPDX-FileCopyrightText: 2025 Contributors to the Eclipse Foundation
- Source URL: https://github.com/eclipse-tractusx/tractusx-sdk