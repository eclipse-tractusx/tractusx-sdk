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

# 8. Cross-cutting Concepts

## Authentication

The SDK provides a pluggable authentication system based on a common interface. All service calls inject authentication headers transparently.

### AuthManagerInterface

Every authentication manager implements two methods:

```python
class AuthManagerInterface:
    def add_auth_header(self, headers: dict = {}) -> dict:
        """Injects authentication into outgoing HTTP headers."""
        ...

    def is_authenticated(self, request: Request) -> bool:
        """Validates an incoming request (used in microservice mode)."""
        ...
```

### Provided Implementations

| Manager | Use Case |
|---------|----------|
| `OAuth2Manager` | Production environments with Keycloak / OIDC-compatible IAM. Handles token acquisition, caching, and refresh automatically. |
| `AuthManager` | Development environments or simple API-key-based setups. |

Custom authentication managers can be created by implementing `AuthManagerInterface`. See [Authentication & Security](../core-concepts/authentication-security/authentication.md) for full usage examples.

## Connection and EDR Cache

The SDK maintains an **in-memory cache** for EDR (Endpoint Data Reference) tokens obtained after successful contract negotiations. This avoids redundant negotiations for the same BPN + `dct:type` combination within the lifecycle of the service instance.

Key behaviors:

- Cache is keyed by `(bpnl, dct_type)` tuples
- Cache can be disabled via the `disabled=True` parameter on the connection manager
- Cache entries can be evicted per Business Partner with `clear_connections_by_party(bpnl)`
- The cache is **not persisted** — it is lost when the process restarts (see [ADR-0002](../contributing/architectural-decisions/0002-data-storage-architecture.md))

## Multi-Version Support

The SDK supports multiple EDC dataspace versions concurrently. Version selection happens at service creation time:

| `dataspace_version` | Compatible EDC | Protocol |
|--------------------|---------------|---------|
| `"jupiter"` | v0.8.x – v0.10.x | DSP (pre-2025) |
| `"saturn"` | v0.11.x+ | DSP 2025-1 |

Each version has its own set of controllers and adapters isolated under versioned submodules. The `ServiceFactory` resolves the correct implementation at runtime. Application code does not reference version-specific imports directly.

## Error Handling

- HTTP errors from external services are caught at the adapter layer and surfaced as structured exceptions with context (URL, status code, response body).
- Services log all errors using the standard Python `logging` module. The logger instance is injected at service creation time, allowing consuming applications to route SDK logs to their own logging infrastructure.
- No exceptions are silently swallowed; callers always receive an explicit error or a typed result.

## Logging

The SDK uses the standard Python `logging` module. All services accept an optional `logger` parameter:

```python
import logging
logger = logging.getLogger("my-app")

service = ServiceFactory.get_connector_consumer_service(
    ...
    logger=logger,
)
```

If no logger is provided, the SDK creates a default logger named `tractusx_sdk`.

## Data Models

All data exchanged with external services is modeled using **Pydantic** models. This provides:

- Type-safe serialization and deserialization
- Automatic validation of API responses
- IDE auto-completion for consumers
- Clear documentation of expected shapes via type annotations

## NOTICE

This work is licensed under the [CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/legalcode).

- SPDX-License-Identifier: CC-BY-4.0
- SPDX-FileCopyrightText: 2026 Contributors to the Eclipse Foundation
- SPDX-FileCopyrightText: 2026 LKS Next
- Source URL: [https://github.com/eclipse-tractusx/tractusx-sdk](https://github.com/eclipse-tractusx/tractusx-sdk)
