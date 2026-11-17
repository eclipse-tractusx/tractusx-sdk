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
- A failure is logged by the **type** of its exception (`... failed (ConnectError)`), never by its message or its traceback, because those quote the full URL and may echo what the remote service received. The exception itself is still raised, with its evidence: see [Errors are exceptions, not log lines](#errors-are-exceptions-not-log-lines).

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
| `DEBUG` | Diagnostic detail: every HTTP request line and its outcome, state transitions and polling progress, cache hits and misses, the default or fallback used in place of a missing value, the **catalog and negotiation request bodies**, and the detail of every failure that is also raised or reported further up | `HTTP GET https://.../shell-descriptors -> 200 in 41 ms`; `HTTP POST https://.../catalog failed after 12 ms (ConnectError)`; `Polling the state of negotiation [...], attempt 10`; `Local cache miss`; why a policy did not match; a request rejected by an authentication manager; a base64 string that could not be decoded; a notification that could not be sent to one of several providers |
| `INFO` | Lifecycle events you would want in an operations log | Asset, contract, policy created; negotiation started; negotiation and transfer state changes; DSP exchange completed; a notification sent to `n` of `m` providers; shell and submodel descriptors created, updated or deleted; adapters registered; services created |
| `WARNING` | Something was recovered from, or is risky | A server failure (5xx); a catalog could not be fetched from one of several connectors; a discovery refresh failed and the cached URL is used; `policies=None` (accept any policy); a negotiation that cannot start (the call returns `None`); a state poll that keeps failing; a provider skipped for lacking its `bpn` or `dsp_url`; **TLS verification is off** (see [TLS verification](#tls-verification)) |
| `ERROR` | A call failed and the SDK reports it here, or the SDK was configured or called wrongly | The failure of `negotiate_and_transfer`, of one of the parallel catalog requests, of a store or an identity provider; an unsupported dataspace version, an unsupported adapter type, a missing bucket name, a connector that was not given to a notification service |

Three rules keep the levels honest:

- **An expected outcome is never above `DEBUG`.** A `404` (for example when checking whether a submodel exists before creating it), a BPN that has no connector registered yet, an object missing from a store, a request rejected by an authentication manager or an undecodable input are normal answers, not alerts. The call returns or raises as it always did, and the caller decides whether it matters.
- **A failure is one `ERROR`, not one per layer.** The inner layers of a call (the HTTP request, the controller, the state machine) log what they saw at `DEBUG` and let the exception travel. It is logged at `ERROR` once, where the SDK reports it: the outermost operation (for example `negotiate_and_transfer`), the wrapper of a thread whose failure would otherwise be lost, or the place where a wrong configuration or argument is detected. A failed negotiation is therefore one `ERROR` line, however deep in the SDK it failed, and an error that the caller handles does not page anyone. A failure that is kept in a result (one provider out of several) is `DEBUG` too, and the run is summarised at `INFO`.
- **A polling loop does not log every iteration.** The first attempt and then one in ten are logged (`attempt 1`, `attempt 10`, `attempt 20`...), so a negotiation that polls once per second for a minute produces a handful of lines, not sixty. A *change* of state is always logged. A state poll that fails is a `WARNING` once in a while and `DEBUG` otherwise.

### TLS verification

The dataplane requests of the connector consumer (`do_get`, `do_post`, `do_put` and their `_by_asset_id` / `_by_dct_type` variants) do not verify the TLS certificate of the dataplane unless the caller says so. When a call gives no `verify`, the SDK logs this `WARNING`, **once per process**:

```text
[Connector Service] No 'verify' given: the TLS certificate of the dataplane is NOT verified by default. Pass verify=True (or the path of a CA bundle) to verify it. This is logged once per process
```

Pass `verify=True` (or the path of a CA bundle) to the call to verify the certificate, and the warning does not appear.

## Logger names

| Logger | Covers |
|--------|--------|
| `tractusx_sdk` | The whole SDK |
| `tractusx_sdk.dataspace.tools.http_tools`, `tractusx_sdk.dataspace.adapters.adapter` | Every HTTP request of the SDK (request line and outcome) |
| `tractusx_sdk.dataspace.services.connector` | Connector consumer and provider services, the DSP state machine |
| `tractusx_sdk.dataspace.services.discovery`, `tractusx_sdk.industry.services.discovery` | Discovery finder, connector discovery, BPN discovery |
| `tractusx_sdk.dataspace.managers.connection` | The EDR connection managers (memory, file system, Postgres) |
| `tractusx_sdk.dataspace.managers.oauth2_manager`, `...auth_manager` | Authentication (see [What is never logged](#what-is-never-logged)) |
| `tractusx_sdk.dataspace.tools` | Policy matching (`dsp_tools`), submodel validation, tracing, cache, file and encoding helpers |
| `tractusx_sdk.industry.services.aas_service` | The Digital Twin Registry service |
| `tractusx_sdk.industry.services.notifications` | Notification services (`tractusx_sdk.extensions.notification_api` for the extension copy) |
| `tractusx_sdk.industry.adapters` | Submodel adapters (S3, file system, HTTP) and their factory |
| `tractusx_sdk.extensions.semantics` | The SAMM to JSON-LD translator |
| `tractusx_sdk.extensions.geometry` | The geometry validator |

## Structured context (`extra`)

Beyond the message, a record carries named fields, so a structured handler can filter and group on them (`transfer_id == "..."`) without parsing text. The message still states the key facts, so a plain-text handler loses nothing.

The fields come from one fixed list. The SDK builds them through a single helper that accepts only these names, so a record never carries a field outside the table:

| Field | Meaning |
|-------|---------|
| `asset_id` | An asset (connector asset, notification asset, dataset) |
| `policy_id` | A policy (`@id` of an offer, or the id of a policy being created) |
| `negotiation_id`, `agreement_id`, `transfer_id`, `edr_id` | The identifiers of the DSP exchange |
| `bpn` | A Business Partner Number |
| `counter_party_id`, `counter_party_address` | The counter party of an exchange and its DSP address |
| `aas_id`, `submodel_id` | A shell and a submodel of the Digital Twin Registry |
| `message_id` | A notification |
| `dataspace_version` | `jupiter` or `saturn` |
| `http_method`, `url`, `status_code`, `elapsed_ms` | An HTTP request and its outcome |
| `adapter_type`, `model`, `schema_urn`, `operation` | The component or the model involved, the semantic id of a schema, and the operation (`consumer.get_transfer_id`, `aas.create_submodel_descriptor`...) |

A field that does not apply to a record is left out, and the names do not collide with the attributes Python reserves on a log record (`name`, `module`, `message`...).

The `operation` is `<area>.<step>` and comes from a fixed list (`LogOperations`, private to the SDK), so you can filter on it without fearing a variant spelling: `operation == "consumer.get_catalog"`.

The values of the fields are safe to write to a log file: the URL fields go through `safe_url`, and the control characters (line breaks, escape sequences) of every value are escaped, so a value that comes from a remote party, such as the id of an asset, cannot forge a line of your log. In the same way, the free text a remote party sends is logged with `%r`, quoted and escaped.

To see the fields, use a handler that renders them. This one writes JSON lines, which any log platform can index:

```python
import json
import logging

# The fields of the SDK (see the table above)
SDK_FIELDS = (
    "asset_id", "policy_id", "negotiation_id", "agreement_id", "transfer_id", "edr_id", "bpn",
    "counter_party_id", "counter_party_address", "aas_id", "submodel_id", "message_id", "dataspace_version",
    "http_method", "url", "status_code", "elapsed_ms", "adapter_type", "model", "schema_urn", "operation",
)


class JsonFormatter(logging.Formatter):
    def format(self, record):
        entry = {"time": self.formatTime(record), "level": record.levelname, "logger": record.name, "message": record.getMessage()}
        entry.update({field: getattr(record, field) for field in SDK_FIELDS if hasattr(record, field)})
        if record.exc_info:
            entry["exception"] = self.formatException(record.exc_info)
        return json.dumps(entry)


handler = logging.StreamHandler()
handler.setFormatter(JsonFormatter())
logging.getLogger("tractusx_sdk").addHandler(handler)
```

```json
{"level": "INFO", "logger": "tractusx_sdk.dataspace.services.connector.base_connector_consumer", "message": "Contract negotiation [a1] started for asset [urn:uuid:...] with [BPNL000000000001]", "negotiation_id": "a1", "asset_id": "urn:uuid:...", "policy_id": "p1", "counter_party_id": "BPNL000000000001", "counter_party_address": "https://provider.example.com/dsp", "operation": "consumer.start_edr_negotiation"}
```

## What is never logged

The SDK handles credentials and business data, and its logs are built so they cannot leak either. These guarantees hold at **every** level, `DEBUG` included, and tests enforce them:

- **No credentials.** Request and response headers, API keys, access tokens, client secrets, the EDR `authorization` value, S3 access keys and the key the SDK itself is configured with are never logged. The `Authorization` header of a request is never part of a record. Where a service is configured with credentials (the OAuth2 manager, the API key manager, the S3 and HTTP submodel adapters, the adapter factory) the log says *what kind* of credential is used (`credentials from the environment or the IAM role`, `auth: bearer`), never its value, and the factory logs the *names* of the settings it receives, not their values.
- **URLs are stripped.** Every URL is logged through `safe_url`: only the scheme, host, port and path are kept. The user information (`user:password@`), the query string, the fragment and path parameters (`;jsessionid=...`) are removed, because any of them can carry a token or a session id. `https://user:pw@host/api?token=abc` is logged as `https://host/api`.
- **No payloads of stored or validated data.** The content of a submodel read from or written to S3, a file or an HTTP service is never logged, only its size. A validation reports *where* a document violates a schema (`path` and rule), never the offending value. The data address of an asset (which holds the headers and OAuth2 settings of your backend) is never logged: asset creation logs a one-line summary.
- **No response bodies.** The body of a response is never logged, whatever its status code: the status code is. When you need the body of an error, read `error.response_body` from the exception the call raises.
- **No exception text where it could echo a secret.** The identity provider, the object store, the connectors and the submodel services may repeat details of the request in their errors. In the modules that talk to them the SDK logs the *type* of the exception (`ConnectError`) or the store's error code (`AccessDenied`), never its message or traceback.
- **No forged lines.** A value that comes from a remote party cannot break out of its log line: its control characters are escaped.
- **Cache keys** are not logged, because callers are free to build them from sensitive data.

What can still appear at `DEBUG`, as described in [Production guidance](#production-guidance): the catalog and negotiation request bodies (policies, filters, BPNs) and the policy comparison details.

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
    At `DEBUG` the SDK logs the catalog and negotiation requests it sends (with their policies, filters and BPNs) and the details of why a policy did not match. These can contain business data. Do not enable `DEBUG` for `tractusx_sdk` in production, or route it to a restricted log. Response bodies, credentials, headers and the data of your submodels are not part of this, at any level: see [What is never logged](#what-is-never-logged).

- Run the SDK at `INFO` or `WARNING` in production. Raise one logger to `DEBUG` temporarily to investigate a problem, rather than the whole SDK. To follow only the HTTP traffic, raise `tractusx_sdk.dataspace.tools.http_tools` and `tractusx_sdk.dataspace.adapters.adapter`.
- The SDK does not log request headers, API keys or access tokens, at any level.
- Alert on `ERROR`: it is one line per failed operation, not one per layer. A `WARNING` about TLS verification means the application never passed `verify` to a dataplane request: pass `verify=True` (or the path of a CA bundle).
- Index the [structured fields](#structured-context-extra) rather than parsing messages: `transfer_id`, `negotiation_id` and `bpn` follow an exchange across the logs of a service.
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
| `debug=True` (detailed diagnostics; request and response payloads are never logged) | `logging.getLogger("tractusx_sdk").setLevel(logging.DEBUG)` |
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
