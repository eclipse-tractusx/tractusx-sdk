<!--

Eclipse Tractus-X - Software Development KIT

Copyright (c) 2026 LKS Next
Copyright (c) 2026 Contributors to the Eclipse Foundation

See the NOTICE file(s) distributed with this work for additional
information regarding copyright ownership.

This work is made available under the terms of the
Creative Commons Attribution 4.0 International (CC-BY-4.0) license,
which is available at
https://creativecommons.org/licenses/by/4.0/legalcode.

SPDX-License-Identifier: CC-BY-4.0

-->

# Upgrade Guide

This page explains how to upgrade the Eclipse Tractus-X SDK in consuming applications, including migration between dataspace protocol versions.

## Versioning Policy

The SDK follows [Semantic Versioning 2.0.0](https://semver.org/):

| Version change | Meaning |
|---------------|---------|
| **Patch** (0.x.**y**) | Bug fixes, dependency security patches — safe to upgrade without code changes |
| **Minor** (0.**x**.0) | New features, new dataspace version support — backward compatible; no code changes required for existing APIs |
| **Major** (**x**.0.0) | Breaking API changes — review migration notes before upgrading |

Check the [CHANGELOG.md](../../CHANGELOG.md) `### Fixed` and `### Security` sections for patch notes, and `### Added` / `### Changed` for minor/major notes.

## Upgrading the SDK Version

### pip

```bash
pip install --upgrade tractusx-sdk==<new-version>
```

### Poetry

```bash
poetry add tractusx-sdk@<new-version>
poetry lock
poetry install
```

After upgrading:

1. Review the [CHANGELOG.md](../../CHANGELOG.md) for any `### Changed` entries affecting your usage
2. Run your test suite: `pytest`
3. Verify behavior against your target EDC connector

## Migrating from Jupiter to Saturn

The `jupiter` and `saturn` dataspace versions are **not wire-compatible**. Migration is required when upgrading from EDC 0.8.x–0.10.x to EDC 0.11.x+.

### What changes

| Area | Jupiter | Saturn |
|------|---------|--------|
| `dataspace_version` parameter | `"jupiter"` | `"saturn"` |
| DSP protocol string | `"dataspace-protocol-http"` | `"dataspace-protocol-http:2025-1"` |
| BPNL-based discovery | Manual DSP URL required | Built-in via `_with_bpnl` methods |
| Access policy left operand | `tx:BusinessPartnerNumber` | `BusinessPartnerNumber` |
| Observability controller | Not available | Available |

### Migration steps

1. **Update `dataspace_version`** in all `ServiceFactory` calls:

    ```python
    # Before
    service = ServiceFactory.get_connector_consumer_service(
        dataspace_version="jupiter", ...
    )

    # After
    service = ServiceFactory.get_connector_consumer_service(
        dataspace_version="saturn", ...
    )
    ```

2. **Switch to `_with_bpnl` methods** (recommended for both versions):

    ```python
    # Works on both Jupiter and Saturn
    response = service.do_get_with_bpnl(
        bpnl="BPNL00000003AYRE",
        filter_expression=[...],
    )
    ```

3. **Update policy definitions** — the access policy `leftOperand` changes between versions. Review any hardcoded policy JSON in your application. See the [Backward Compatibility Guide](../how-to-guides/backward-compatibility.md) for the full diff.

4. **Update your EDC connector** to v0.11.x+ — the SDK version change alone is not enough; the EDC connector itself must be upgraded.

5. **Test** against the new EDC version using the [TCK](../tck/index.md) before deploying to production.

### Running Both Versions Simultaneously

If you need to talk to both Jupiter and Saturn connectors from the same application, create separate service instances:

```python
jupiter_service = ServiceFactory.get_connector_consumer_service(
    dataspace_version="jupiter", base_url=os.environ["JUPITER_EDC_URL"], headers=headers_j,
)

saturn_service = ServiceFactory.get_connector_consumer_service(
    dataspace_version="saturn", base_url=os.environ["SATURN_EDC_URL"], headers=headers_s,
)
```

## Documentation Versioning

The SDK documentation is versioned alongside releases. All past versions are accessible via the version selector in the documentation header. When upgrading the SDK, refer to the documentation version matching your target release:

```
https://eclipse-tractusx.github.io/tractusx-sdk/<version>/
```

Documentation is automatically published on each tagged release and on every push to `main` (as the `main` development version).

## NOTICE

This work is licensed under the [CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/legalcode).

- SPDX-License-Identifier: CC-BY-4.0
- SPDX-FileCopyrightText: 2026 Contributors to the Eclipse Foundation
- SPDX-FileCopyrightText: 2026 LKS Next
- Source URL: [https://github.com/eclipse-tractusx/tractusx-sdk](https://github.com/eclipse-tractusx/tractusx-sdk)
