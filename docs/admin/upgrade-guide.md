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

Check the [CHANGELOG.md](https://github.com/eclipse-tractusx/tractusx-sdk/blob/main/CHANGELOG.md) `### Fixed` and `### Security` sections for patch notes, and `### Added` / `### Changed` for minor/major notes.

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

1. Review the [CHANGELOG.md](https://github.com/eclipse-tractusx/tractusx-sdk/blob/main/CHANGELOG.md) for any `### Changed` entries affecting your usage
2. Run your test suite: `pytest`
3. Verify behavior against your target EDC connector

## Upgrading to 0.9.0

0.9.0 reworks logging and error handling to follow Python library conventions. It contains **breaking changes**; a `TypeError` is raised at once if you still pass a removed argument.

### 1. Remove `verbose`, `debug` and `logger`

The SDK logs through the standard `logging` module (logger `tractusx_sdk`) and the level decides what you see. Remove the arguments and configure logging once in your application (see [Logging and Error Handling](logging.md)):

=== "Before (0.8.x)"

    ```python
    service = ServiceFactory.get_connector_consumer_service(
        dataspace_version="saturn",
        base_url=base_url,
        dma_path="/management",
        headers=headers,
        logger=my_logger,
        verbose=True,
        debug=True,
    )
    ```

=== "After (0.9.0)"

    ```python
    logging.basicConfig(level=logging.INFO)
    logging.getLogger("tractusx_sdk").setLevel(logging.DEBUG)   # debug=True

    service = ServiceFactory.get_connector_consumer_service(
        dataspace_version="saturn",
        base_url=base_url,
        dma_path="/management",
        headers=headers,
    )
    ```

This applies to `ServiceFactory.get_connector_consumer_service`, `get_connector_provider_service` and `get_connector_service`; the consumer, provider and Saturn consumer services; the three discovery services; the connection managers `MemoryConnectionManager`, `PostgresConnectionManager`, `PostgresMemoryConnectionManager` and `PostgresMemoryRefreshConnectionManager`; `SammSchemaContextTranslator`; and `NotificationService` / `NotificationConsumerService` (in `industry` and in `extensions.notification_api`), whose builders also lose `.verbose()` and `.logger()`.

Also note:

- `verbose` used to be `True` by default on several services. The SDK is now silent until you configure logging.
- Positional arguments after `connection_manager` (or `headers` on the provider) moved forward, so pass `verify_ssl` and `trace` by keyword.
- The attributes `service.logger`, `service.verbose` and `service.debug` no longer exist.

### 2. Errors carry their data

A `get_catalog` failure no longer puts the response headers and body into the exception message. Read them from the error:

```python
from tractusx_sdk.exceptions import CatalogRequestError

try:
    consumer.get_catalog(counter_party_id=bpn, counter_party_address=dsp_url)
except CatalogRequestError as error:        # still a ConnectionError
    error.status_code, error.response_body
```

All the SDK's own errors now derive from `tractusx_sdk.exceptions.TractusXSDKError`. Where a bare `Exception` was raised, a typed error is raised instead, and where a builtin was raised (`ValueError`, `RuntimeError`, `ConnectionError`, `requests.HTTPError`) the new error still inherits from it, so existing handlers keep working.

### 3. Changed return types

These still behave as before for existing code:

| API | Now returns |
|-----|-------------|
| `DspTools.filter_assets_and_policies` | `list[AssetPolicySelection]`, a `NamedTuple` that still unpacks as `(asset_id, policy)` |
| `submodel_schema_finder` | `SchemaLookupResult`; `result["schema"]` still works |
| `json_validator` | `ValidationResult`; `result["status"]` still works. New `raise_on_error=False` returns the violations instead of raising |

### 4. Removed

| Removed | Use instead |
|---------|-------------|
| `GeometryValidator.print_results()` and `print_tree_structure()` | `validator.render_report()` returns the text; `validator.report()` returns a `GeometryValidationReport` |
| TCK `configure_debug_logging(logger, debug)` | `enable_debug_logging(logger)`, called only when debugging is wanted |
| TCK `upload_sample_data(..., verbose=...)` | Bodies are logged at `DEBUG` |

Code that read the DEBUG logs of `DspTools.is_policy_valid` to learn why a policy was rejected should call `DspTools.evaluate_policy`, or read `PolicyMismatchError.evaluations`.

### 5. A bug fix you may notice

With `policies=None` ("accept any policy"), the base consumer's `get_transfer_id` replaced the policies with a random UUID and then used it as the allow-list, which failed with `TypeError`. The UUID is now only the cache identity of that selection and `None` is what reaches the catalog filter.

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
