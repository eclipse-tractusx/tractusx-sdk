
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

Here's a minimal example to get started with the SDK as a data consumer:

```python
from tractusx_sdk.dataspace.services.connector import ServiceFactory

consumer_service = ServiceFactory.get_connector_consumer_service(
    dataspace_version="saturn",  # use "jupiter" for EDC v0.8.x-v0.10.x
    base_url="https://my-connector-controlplane.url",
    dma_path="/management",
    headers={
        "X-Api-Key": "your-api-key",
        "Content-Type": "application/json"
    }
)

# Retrieve the catalog from a remote connector
catalog = consumer_service.get_catalog_by_dct_type(
    dct_type="https://w3id.org/catenax/taxonomy#DigitalTwinRegistry",
    counter_party_id="BPNL00000003AYRE",
    counter_party_address="https://provider-controlplane.url/api/v1/dsp"
)
print(catalog)
```

> **Note**: Replace `"your-api-key"`, URLs, and BPN values with your actual configuration. See the [examples/](./examples/) directory and the [full documentation](https://eclipse-tractusx.github.io/tractusx-sdk/main/) for more patterns.

## Verify Installation

After installing, confirm the package is available:

```bash
python -c "import tractusx_sdk; print(tractusx_sdk.__version__)"
```

You should see the installed version number printed without errors.

## Documentation

For more information, refer to the official documentation:

- [Full Documentation](https://eclipse-tractusx.github.io/tractusx-sdk/main/)
- [Usage Examples](./examples/)
- [README](./README.md)

## Uninstallation

To remove the package:

```bash
pip uninstall tractusx-sdk
```

## Local Development

To set up a local development environment (e.g. for contributing):

```bash
# 1. Clone the repository
git clone https://github.com/eclipse-tractusx/tractusx-sdk.git
cd tractusx-sdk

# 2. Install Poetry (if not already installed)
pip install poetry

# 3. Install all dependencies including dev and test groups
poetry install --with dev,test

# 4. Run the test suite
poetry run pytest
```

See [CONTRIBUTING.md](./CONTRIBUTING.md) for contribution guidelines.

## Troubleshooting & FAQ

**Q: `import tractusx_sdk` fails after installation.**\
A: Ensure your virtual environment is activated and that you installed into it. Run `pip show tractusx-sdk` to confirm.

**Q: Which `dataspace_version` should I use?**\
A: Use `"saturn"` for EDC `v0.11.x` (DSP 2025-1) and `"jupiter"` for EDC `v0.8.x`–`v0.10.x`.

**Q: I get authentication errors connecting to the connector.**\
A: Verify your `X-Api-Key` header value and that the connector management API URL (`base_url` + `dma_path`) is reachable from your environment.

**Q: Pip install fails with dependency conflicts.**\
A: Install in a clean virtual environment: `python -m venv .venv && source .venv/bin/activate && pip install tractusx-sdk`. If conflicts persist, check the [issues page](https://github.com/eclipse-tractusx/tractusx-sdk/issues).

**Q: Caching issues during install.**\
A: Use the `--no-cache-dir` flag:
  ```bash
  pip install --no-cache-dir tractusx-sdk
  ```

## Contact & Support

- **GitHub Issues**: [Report a bug or request a feature](https://github.com/eclipse-tractusx/tractusx-sdk/issues/new/choose)
- **GitHub Discussions**: [Ask questions or share ideas](https://github.com/eclipse-tractusx/tractusx-sdk/discussions)
- **Matrix Chat**: [Industry Core Hub Channel](https://matrix.to/#/#tractusx-industry-core-hub:matrix.eclipse.org)
- **Open Meetings**: [Tractus-X SDK Weekly](https://eclipse-tractusx.github.io/community/open-meetings#tractus-x-sdk-weekly)

## NOTICE

This work is licensed under the [CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/legalcode).

- SPDX-License-Identifier: CC-BY-4.0
- SPDX-FileCopyrightText: 2025 Contributors to the Eclipse Foundation
- Source URL: https://github.com/eclipse-tractusx/tractusx-sdk
