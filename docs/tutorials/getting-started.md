<!--

Eclipse Tractus-X - Software Development KIT

Copyright (c) 2025 LKS Next
Copyright (c) 2025 Mondragon Unibertsitatea
Copyright (c) 2025 Contributors to the Eclipse Foundation

See the NOTICE file(s) distributed with this work for additional
information regarding copyright ownership.

This work is made available under the terms of the
Creative Commons Attribution 4.0 International (CC-BY-4.0) license,
which is available at
https://creativecommons.org/licenses/by/4.0/legalcode.

SPDX-License-Identifier: CC-BY-4.0

-->
# Tractus-SDK Documentation

## Prerequisites

Before getting started with the Tractus-X SDK, ensure you have:

- **Python 3.12+** installed on your system
- **Internet connection** for downloading packages
- **Basic Python knowledge** (variables, functions, imports)
- **Text editor** or IDE for writing code

## Installation Guide

### Development Environment Setup

We recommend using a virtual environment to avoid conflicts with other Python projects:

```bash title="Create Virtual Environment"
# Create a new virtual environment
python -m venv tractux-sdk-env

# Activate the environment
# On Windows:
tractux-sdk-env\Scripts\activate
# On macOS/Linux:
source tractux-sdk-env/bin/activate
```

The Tractus-X SDK can be installed in two ways: from PyPI (recommended for most users) or from source (for developers).

=== "Install from PyPI (Recommended)"

    This is the easiest way to get started:

    ```bash
    # Install the SDK directly from PyPI (recommended for users)
    pip install tractusx-sdk
    
    # Verify the installation works
    python -c "
    try:
        from tractusx_sdk.dataspace.services import BaseConnectorService
        print('✅ SDK Ready!')
        print('BaseConnectorService imported successfully')
    except Exception as e:
        print('❌ Import failed:')
        print(f'Error: {e}')
        import traceback
        traceback.print_exc()
    "
    ```

=== "Install from Source"

    If you need the latest development version or want to contribute:

    ```bash
    # Only use this if you need the latest development version
    git clone https://github.com/eclipse-tractusx/tractusx-sdk.git
    cd tractusx-sdk
    pip install -e .
    
    # Verify installation
    python -c "
    try:
        from tractusx_sdk.dataspace.services import BaseConnectorService
        print('✅ SDK Ready!')
        print('BaseConnectorService imported successfully')
    except Exception as e:
        print('❌ Import failed:')
        print(f'Error: {e}')
        import traceback
        traceback.print_exc()
    "
    ```

!!! success "Installation Complete!"
    If you see "✅ SDK Ready!" then you're all set to continue to the next step!

!!! warning "Compatibility Notice"
    Currently this SDK is not 100% compatible and has not been tested against the `v0.11.x` connector. The issue is being worked on [here](https://github.com/eclipse-tractusx/tractusx-sdk/issues/159).


### Troubleshooting

If you encounter issues, here are common solutions:

??? question "Import Errors"
    
    **Problem**: `ModuleNotFoundError: No module named 'tractusx_sdk'`
    
    **Solutions**:
    - Ensure you activated your virtual environment
    - Reinstall the SDK: `pip uninstall tractusx-sdk && pip install tractusx-sdk`
    - Check Python version: `python --version` (should be 3.12+)

??? question "Connection Errors"
    
    **Problem**: Cannot connect to connector
    
    **Solutions**:
    - Verify you have valid connector credentials
    - Check network connectivity
    - Contact your dataspace administrator for correct configuration

### Next Steps

Now that you have the SDK installed verify it: [Create your First Asset](./create-first-asset.md)

Once you have the SDK installed and verified check the following links:

1. **📚 Explore Libraries**: Learn about the [Dataspace Library](../api-reference/dataspace-library/index.md) for connector services
2. **🔍 Read Services Documentation**: Check out [connector services](../api-reference/dataspace-library/connector/services.md) for detailed API reference
3. **📖 SDK Structure**: Understand the [SDK architecture](../core-concepts/sdk-architecture/sdk-structure-and-components.md)
4. **🤝 Join Community**: Connect with other developers in our [discussions](https://github.com/eclipse-tractusx/tractusx-sdk/discussions)

## NOTICE

This work is licensed under the [CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/legalcode).

- SPDX-License-Identifier: CC-BY-4.0
- SPDX-FileCopyrightText: 2025 Contributors to the Eclipse Foundation
- Source URL: https://github.com/eclipse-tractusx/tractusx-sdk
