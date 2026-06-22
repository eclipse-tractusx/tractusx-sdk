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

# Configuration

This page documents all configuration options available when embedding the Eclipse Tractus-X SDK into an application.

## ServiceFactory Parameters

The primary entry point for creating SDK service instances is `ServiceFactory`. All parameters are passed at instantiation time.

```python
from tractusx_sdk.dataspace.services.connector.service_factory import ServiceFactory

service = ServiceFactory.get_connector_consumer_service(
    dataspace_version="saturn",        # "jupiter" or "saturn"
    base_url="https://edc.example.com",
    dma_path="/management",
    headers={
        "Authorization": "Bearer <token>",
        "Content-Type": "application/json",
    },
    connection_manager=my_manager,     # optional, defaults to MemoryConnectionManager
    logger=my_logger,                  # optional, defaults to tractusx_sdk logger
    verbose=False,                     # optional, defaults to True; set False in production
)
```

### Parameter Reference

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `dataspace_version` | `str` | Yes | — | Protocol version: `"jupiter"` (EDC 0.8.x–0.10.x) or `"saturn"` (EDC 0.11.x+, DSP 2025-1) |
| `base_url` | `str` | Yes | — | Base URL of the EDC connector control plane (e.g., `https://edc.example.com`) |
| `dma_path` | `str` | Yes | — | Path prefix for the Management API (e.g., `"/management"`). There is no built-in default — this must always be provided. |
| `headers` | `dict` | Yes | — | HTTP headers injected into every request. Must include auth headers. |
| `connection_manager` | `ConnectionManager` | No | `MemoryConnectionManager` | Manages EDR connection state. See [Connection Managers](#connection-managers). |
| `logger` | `logging.Logger` | No | SDK default logger | Logger instance for SDK output. |
| `verbose` | `bool` | No | `True` | When `True`, logs every HTTP request and response body at DEBUG level. Set `False` in production to avoid leaking sensitive data into logs. |

## Connection Managers

The connection manager controls how the SDK stores and retrieves EDR (Endpoint Data Reference) tokens obtained after contract negotiations.

### Selecting a Connection Manager

| Manager | Persistence | When to use |
|---------|-------------|-------------|
| `MemoryConnectionManager` | In-memory (lost on restart) | Single-process apps, development, testing |
| `FileSystemConnectionManager` | JSON file on disk | Simple deployments, single-process, needs durability across restarts |
| `PostgresConnectionManager` | PostgreSQL database | Multi-process apps, containerized deployments, production |

### MemoryConnectionManager (default)

```python
from tractusx_sdk.dataspace.managers.connection.memory import MemoryConnectionManager

manager = MemoryConnectionManager(verbose=True)
```

### FileSystemConnectionManager

```python
from tractusx_sdk.dataspace.managers.connection.file_system import FileSystemConnectionManager

manager = FileSystemConnectionManager(
    path="/var/data/edr_connections.json",
    persist_interval=60,  # flush to disk every 60 seconds
)
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `path` | `str` | Path to the JSON file used to persist connections |
| `persist_interval` | `int` | Seconds between automatic disk flushes (default: 5) |

### PostgresConnectionManager

```python
from tractusx_sdk.dataspace.managers.connection.database import PostgresConnectionManager
from sqlmodel import create_engine
import os

engine = create_engine(
    os.environ["DATABASE_URL"],
    pool_size=5,
    max_overflow=10,
)

manager = PostgresConnectionManager(
    engine=engine,
    table_name="edr_connections",  # table is created automatically if absent
)
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `engine` | `sqlmodel.Engine` | SQLModel/SQLAlchemy engine pointing to a PostgreSQL instance |
| `table_name` | `str` | Table name for EDR storage (auto-created on first use) |

!!! warning "Secrets in connection strings"
    Never hardcode database credentials in source code. Inject them via environment variables:
    ```python
    import os
    engine = create_engine(os.environ["DATABASE_URL"])
    ```

## Authentication

### OAuth2Manager (recommended for production)

```python
import os
from tractusx_sdk.dataspace.managers import OAuth2Manager

auth_manager = OAuth2Manager(
    token_url=os.environ["IAM_TOKEN_URL"],       # Keycloak token endpoint
    client_id=os.environ["CLIENT_ID"],
    client_secret=os.environ["CLIENT_SECRET"],
)

headers = auth_manager.add_auth_header({
    "Content-Type": "application/json",
})
```

The `OAuth2Manager` fetches and caches the token automatically, refreshing it before expiry.

### AuthManager (development / simple setups only)

```python
import os
from tractusx_sdk.dataspace.managers import AuthManager

auth_manager = AuthManager(api_key=os.environ["EDC_API_KEY"])
headers = auth_manager.add_auth_header({"Content-Type": "application/json"})
```

!!! danger "Do not use AuthManager in production"
    `AuthManager` uses a static API key. Use `OAuth2Manager` with Keycloak for any production or internet-facing deployment.

## Logging

All SDK services accept a `logger` parameter. If omitted, a default logger named `tractusx_sdk` is used.

```python
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("my-app.sdk")

service = ServiceFactory.get_connector_consumer_service(
    dataspace_version="saturn",
    base_url="https://edc.example.com",
    dma_path="/management",
    headers=headers,
    logger=logger,
    verbose=False,  # set False to avoid logging HTTP bodies in production
)
```

Set `verbose=False` in production — `verbose=True` (the default) logs full HTTP request/response bodies which may contain sensitive data.

## Environment Variable Reference

The SDK does not read environment variables directly, but the following pattern is recommended for all operator-supplied values:

| Variable (suggested name) | Used for |
|--------------------------|---------|
| `EDC_BASE_URL` | `base_url` in `ServiceFactory` |
| `EDC_DMA_PATH` | `dma_path` in `ServiceFactory` (e.g., `"/management"`) |
| `EDC_API_KEY` | `AuthManager` (development only) |
| `IAM_TOKEN_URL` | `OAuth2Manager.token_url` |
| `CLIENT_ID` | `OAuth2Manager.client_id` |
| `CLIENT_SECRET` | `OAuth2Manager.client_secret` |
| `DATABASE_URL` | `PostgresConnectionManager` engine URL |

## NOTICE

This work is licensed under the [CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/legalcode).

- SPDX-License-Identifier: CC-BY-4.0
- SPDX-FileCopyrightText: 2026 Contributors to the Eclipse Foundation
- SPDX-FileCopyrightText: 2026 LKS Next
- Source URL: [https://github.com/eclipse-tractusx/tractusx-sdk](https://github.com/eclipse-tractusx/tractusx-sdk)
