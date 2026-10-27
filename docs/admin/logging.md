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

# Logging and Error Handling

This page explains how the SDK logs, how your application turns that output on, and how the SDK reports what happened in a call without making you read log lines.

## How the SDK logs

The SDK follows the conventions of a Python library:

- Every module logs through the standard [`logging`](https://docs.python.org/3/library/logging.html) module, with its own logger named after the module (for example `tractusx_sdk.dataspace.services.connector.base_connector_consumer`). All of them are children of the `tractusx_sdk` logger.
- The SDK **never prints** and **never configures logging**. A `NullHandler` is attached to the `tractusx_sdk` logger, so importing and using the SDK produces no output until *your application* sets logging up.
- There are no `verbose`, `debug` or `logger` arguments. The logging level you choose decides what you see, exactly as for any other library.
- Messages are formatted lazily (`%s` arguments), so a message below the active level costs nothing.

## Quick start

Configure logging once, at the entry point of your application, and the SDK output follows it:

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)

# More detail from the SDK only, while the rest of the application stays at INFO
logging.getLogger("tractusx_sdk").setLevel(logging.DEBUG)

# ...or silence one noisy module
logging.getLogger("tractusx_sdk.dataspace.tools.dsp_tools").setLevel(logging.WARNING)
```

!!! note "Replaces `verbose=True` and `logger=...`"
    Turning logging on used to mean passing `verbose=True` and a `logger` to every service. That is now the three lines above, once, for the whole SDK. See [Migrating from `verbose` / `debug` / `logger`](#migrating-from-verbose-debug-logger).

## What each level means

| Level | What the SDK reports there | Examples |
|-------|---------------------------|----------|
| `DEBUG` | Diagnostic detail, **including request payloads** | `[CATALOG REQUEST]`, `[NEGOTIATION REQUEST]`, `[ASSET REQUEST]` bodies; cache hits and misses; why a policy did not match; the raw discovery response |
| `INFO` | Lifecycle events you would want in an operations log | Asset, contract or policy created; negotiation and transfer state changes; "starting a new contract negotiation"; discovery cache updated |
| `WARNING` | Something was recovered from, or is risky | A catalog could not be fetched from one of several connectors; a discovery refresh failed and the cached URL is used; `policies=None` (accept any policy) |
| `ERROR` | A call failed (an exception is raised or returned as well) | Failed to create an asset; failed to send a notification; a database save or load failed |

## Logger names

| Logger | Covers |
|--------|--------|
| `tractusx_sdk` | The whole SDK |
| `tractusx_sdk.dataspace.services.connector` | Connector consumer and provider services |
| `tractusx_sdk.dataspace.services.discovery`, `tractusx_sdk.industry.services.discovery` | Discovery finder, connector discovery, BPN discovery |
| `tractusx_sdk.dataspace.managers.connection` | The EDR connection managers (memory, file system, Postgres) |
| `tractusx_sdk.dataspace.tools` | Policy matching (`dsp_tools`), submodel validation, tracing |
| `tractusx_sdk.industry.services.notifications` | Notification services (`tractusx_sdk.extensions.notification_api` for the extension copy) |
| `tractusx_sdk.industry.adapters` | Submodel adapters |
| `tractusx_sdk.extensions.semantics` | The SAMM to JSON-LD translator |

## Configuring with `dictConfig`

For anything beyond `basicConfig`, use the standard dictionary configuration. This sends the SDK to a rotating file at `INFO` and your own code to the console:

```python
import logging.config

logging.config.dictConfig({
    "version": 1,
    "disable_existing_loggers": False,   # keep the SDK loggers alive
    "formatters": {
        "default": {"format": "%(asctime)s %(levelname)s [%(name)s] %(message)s"},
    },
    "handlers": {
        "console": {"class": "logging.StreamHandler", "formatter": "default"},
        "sdk_file": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": "tractusx-sdk.log",
            "maxBytes": 10_000_000,
            "backupCount": 5,
            "formatter": "default",
        },
    },
    "loggers": {
        "tractusx_sdk": {"level": "INFO", "handlers": ["sdk_file"], "propagate": False},
    },
    "root": {"level": "INFO", "handlers": ["console"]},
})
```

!!! warning "Keep `disable_existing_loggers` set to `False`"
    The SDK creates its loggers when its modules are imported. With the default (`True`), a `dictConfig` applied after the import silences them.

## Production guidance

!!! danger "`DEBUG` logs request payloads"
    At `DEBUG` the SDK logs the requests it sends (assets, policies, contract definitions, catalog and negotiation requests) and the body of a failed catalog response. These can contain business data, BPNs and policy details. Do not enable `DEBUG` for `tractusx_sdk` in production, or route it to a restricted log. Also note that the notification services log the body of a failed notification response at `ERROR`, so it is in your logs at the default levels.

- Run the SDK at `INFO` or `WARNING` in production. Raise one logger to `DEBUG` temporarily to investigate a problem, rather than the whole SDK.
- The SDK does not log request headers, API keys or access tokens.
- To record the exact HTTP exchange of a call, with sensitive headers masked, use [Request Tracing](../core-concepts/sdk-architecture/request-tracing.md). It is separate from logging and is switched on with the `trace` flag.

## Errors are exceptions, not log lines

What the SDK learns about a call is handed back to you as a return value or an exception. You never need to parse a log message to decide what to do.

Every error the SDK raises on purpose derives from `tractusx_sdk.exceptions.TractusXSDKError`, so one `except` clause catches them all. Where an SDK error replaces a builtin exception, it still inherits from it, so existing `except` clauses keep working.

```python
from tractusx_sdk.exceptions import TractusXSDKError, CatalogRequestError, PolicyMismatchError

try:
    transfer_id = consumer.get_transfer_id(...)
except PolicyMismatchError as error:      # also a ValueError
    ...
except TractusXSDKError as error:
    ...
```

| Exception | Also a | Raised when |
|-----------|--------|-------------|
| `TractusXSDKError` | `Exception` | Base of everything below |
| `ValidationError` | `ValueError` | Input or data failed a validation rule |
| `SubmodelValidationError` | `ValidationError`, `requests.HTTPError` | A submodel does not match its JSON schema; the violations are in `.issues` |
| `SchemaError` | | Base of the schema errors |
| `InvalidSemanticIdError` | `ValidationError`, `requests.HTTPError` | A semantic id does not have the expected structure |
| `SchemaNotFoundError` | `requests.HTTPError` | The schema of a semantic id could not be retrieved or is not JSON |
| `SchemaTranslationError` | | A schema could not be translated into a JSON-LD context |
| `DiscoveryError` | | A discovery service failed |
| `DiscoveryEndpointNotFoundError` | | The discovery service does not list the endpoint |
| `DiscoveryUnauthorizedError` | | The discovery service refused the credentials (HTTP 401) |
| `ConnectionManagerError` | | A connection manager could not store or load an entry |
| `ConnectorError` | `RuntimeError` | A call to an EDC connector failed |
| `CatalogError` | `ConnectorError` | The catalog could not be obtained or holds no usable offer |
| `EmptyCatalogError` | `CatalogError` | The catalog is missing, or has no dataset |
| `PolicyMismatchError` | `CatalogError`, `ValueError` | The catalog was read and no offer had an acceptable policy |
| `CatalogRequestError` | `CatalogError`, `ConnectionError` | The connector answered the catalog request with an error, or not at all |
| `NegotiationError` | `ConnectorError` | A contract negotiation failed or was terminated |
| `TransferError` | `ConnectorError` | A transfer process failed or was terminated |
| `NotificationError` and subclasses | | Notification validation, parsing or sending failed |

The errors carry the evidence, so you do not need the logs to report a failure:

```python
try:
    catalog = consumer.get_catalog(counter_party_id=bpn, counter_party_address=dsp_url)
except CatalogRequestError as error:
    print(error.status_code)      # None when the connector did not answer
    print(error.response_body)    # the connector's answer, never part of the message
```

### Why was a policy rejected?

`PolicyMismatchError` carries the catalog that was read, the allow-list it was compared against, and an evaluation for every rejected policy:

```python
from tractusx_sdk.dataspace.tools import PolicyMismatchError

try:
    consumer.get_transfer_id(..., policies=allowed_policies)
except Exception as error:
    cause = error.__cause__
    if isinstance(cause, PolicyMismatchError):
        for evaluation in cause.evaluations:
            print(evaluation.asset_id, evaluation.policy_id, evaluation.verdict)
            for mismatch in evaluation.mismatches:
                print(f"  allowed policy [{mismatch.allowed_index}]")
                for difference in mismatch.differences:
                    print("   -", difference)
```

To ask the question directly, without a catalog, use `DspTools.evaluate_policy`. It returns a frozen `PolicyEvaluation` whose `accepted`, `verdict` (`ANY_ALLOWED`, `MATCHED`, `EMPTY_ALLOW_LIST` or `NO_MATCH`), `matched_index` and `mismatches` are the complete answer:

```python
from tractusx_sdk.dataspace.tools import DspTools

evaluation = DspTools.evaluate_policy(policy=offer_policy, allowed_policies=allowed_policies)
if not evaluation.accepted:
    print(evaluation.explain())
```

`DspTools.is_policy_valid` still returns a plain `bool`.

### Validation results

`submodel_schema_finder` and `json_validator` return dataclasses (`SchemaLookupResult`, `ValidationResult`). They still support `result["schema"]`-style access. `json_validator` raises `SubmodelValidationError` by default; pass `raise_on_error=False` to get the violations back instead:

```python
from tractusx_sdk.dataspace.tools.validate_submodels import json_validator

result = json_validator(schema, payload, raise_on_error=False)
if not result.valid:
    for issue in result.issues:          # ValidationIssue: path, message, validator, expected, invalid_value
        print(issue.path, issue.message)
```

### Geometry validation

`GeometryValidator` no longer prints. `report()` returns a `GeometryValidationReport` (`errors`, `warnings`, `infos`, `tree`), and `render_report()` returns the text that `print_results()` used to print:

```python
validator.validate_file(path)
report = validator.report()
if report.has_errors:
    print(validator.render_report())
```

## Testing your code

Use your test framework's log capture. With pytest:

```python
import logging

def test_asset_creation_is_logged(caplog):
    with caplog.at_level(logging.INFO, logger="tractusx_sdk"):
        provider.create_asset(...)
    assert "created successfully" in caplog.text
```

## Migrating from `verbose` / `debug` / `logger`

The arguments were removed in 0.9.0. Passing them raises a `TypeError`.

| Before | Now |
|--------|-----|
| `verbose=True` | `logging.getLogger("tractusx_sdk").setLevel(logging.INFO)` |
| `debug=True` (log request payloads) | `logging.getLogger("tractusx_sdk").setLevel(logging.DEBUG)` |
| `verbose=False` | Leave logging unconfigured, or `setLevel(logging.WARNING)` |
| `logger=my_logger` | Configure handlers on the `tractusx_sdk` logger or on the root logger |
| `Service.builder().verbose(True).logger(log)` | Remove both calls |
| Relying on the exception text for `verbose` details (response headers and body) | Read `error.status_code` and `error.response_body` |

## Command line tools

The Connector TCK and the geometry validator are applications, so they configure the logging of their own process. See the [TCK API Reference](../tck/connector/api-reference.md) (`--no-debug` switches `DEBUG` off).

## NOTICE

This work is licensed under the [CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/legalcode).

- SPDX-License-Identifier: CC-BY-4.0
- SPDX-FileCopyrightText: 2026 Contributors to the Eclipse Foundation
- SPDX-FileCopyrightText: 2026 LKS Next
- Source URL: [https://github.com/eclipse-tractusx/tractusx-sdk](https://github.com/eclipse-tractusx/tractusx-sdk)
