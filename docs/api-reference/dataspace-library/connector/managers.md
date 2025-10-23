<!--

Eclipse Tractus-X - Software Development KIT

Copyright (c) 2025 LKS Next
Copyright (c) 2025 Contributors to the Eclipse Foundation

See the NOTICE file(s) distributed with this work for additional
information regarding copyright ownership.

This work is made available under the terms of the
Creative Commons Attribution 4.0 International (CC-BY-4.0) license,
which is available at
https://creativecommons.org/licenses/by/4.0/legalcode.

SPDX-License-Identifier: CC-BY-4.0

-->

# Connector Managers

Connector Managers in the Tractus-X SDK provide abstractions for connection state management, enabling flexible and robust handling of Endpoint Data Reference (EDR) lifecycles. This section guides you through the available manager types, their purposes, and how to select the right implementation for your deployment scenario.

## Alternative Connection Managers

Depending on your operational requirements, you may choose between several connection manager implementations. While `MemoryConnectionManager` is connector-specific and recommended for contract negotiation and EDR lifecycle, two alternative managers are available for different persistence needs:

- **FileSystemConnectionManager**: Persists EDR connections to disk using JSON files. Use when you need simple, file-based persistence and durability across restarts.
- **PostgresConnectionManager**: Persists EDR connections in a PostgreSQL database. Use for scalable, multi-process, or production deployments requiring robust database-backed state.

All three managers share the same interface (`add_connection`, `get_connection`, `delete_connection`, etc.), so you can switch between them depending on your deployment scenario.

## Purpose


The following managers encapsulate logic for:

- Managing EDR (Endpoint Data Reference) connection state for dataspace connectors
- Providing thread-safe, file-based, or database-backed persistence for EDR connections
- Supporting flexible deployment scenarios: in-memory (fast, ephemeral), file-based (durable), or database (scalable)
- Allowing seamless switching between connection manager implementations depending on operational requirements

Below, you'll find a comparison of the available connection managers, followed by detailed tables outlining their attributes and methods. This structure will help you quickly identify which manager best fits your needs and how to use it in your project.

## Connection Manager Comparison

| Manager Name                  | Persistence Type | Use Case / Description                                                                                   |
|-------------------------------|------------------|----------------------------------------------------------------------------------------------------------|
| `MemoryConnectionManager`     | In-memory        | Thread-safe, connector-specific. Fastest for contract negotiation and EDR lifecycle.                     |
| `FileSystemConnectionManager` | File-based (JSON)| Durable across restarts, simple deployments, local development.                                          |
| `PostgresConnectionManager`   | Database         | Scalable, multi-process, production-grade deployments.                                                    |

### Key Attributes by Manager

| Manager Name                  | Attributes                                                                                  | Methods                                                                                                    |
|-------------------------------|---------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------------|
| `MemoryConnectionManager`     | `open_connections`, `provider_id_key`, `edrs_key`, `logger`, `verbose`, `_lock`             | `add_connection()`, `get_connection()`, `get_connection_transfer_id()`, `delete_connection()`               |
| `FileSystemConnectionManager` | `file_path`, `persist_interval`, `lock`, `_stop_event`, `_last_loaded_hash`, `open_connections` | `add_connection()`, `get_connection()`, `get_connection_transfer_id()`, `delete_connection()`               |
| `PostgresConnectionManager`   | `engine`, `table_name`                                                                      | `add_connection()`, `get_connection()`, `get_connection_transfer_id()`, `delete_connection()`               |

## Manager Instantiation Example

```python
from tractusx_sdk.dataspace.managers.connection.memory import MemoryConnectionManager
from tractusx_sdk.dataspace.managers.connection.file_system import FileSystemConnectionManager
from tractusx_sdk.dataspace.managers.connection.postgres import PostgresConnectionManager

# In-memory connection manager for connector operations
connection_manager = MemoryConnectionManager(verbose=True)

# File-based connection manager
fs_connection_manager = FileSystemConnectionManager(file_path="/tmp/edr_connections.json", persist_interval=60)

# Postgres-backed connection manager
pg_connection_manager = PostgresConnectionManager(engine=my_engine, table_name="edr_connections")
```

## Method Reference

| Method                        | Required Attributes                                                                 | Manager(s)                    | Description                                                                                  |
|-------------------------------|--------------------------------------------------------------------------|-------------------------------|----------------------------------------------------------------------------------------------|
| `add_connection`            | `counter_party_id, counter_party_address, query_checksum, policy_checksum, connection_entry` | All                            | Adds a new EDR connection                                                                   |
| `get_connection`            | `counter_party_id, counter_party_address, query_checksum, policy_checksum`                  | All                            | Retrieves an EDR connection                                                                 |
| `get_connection_transfer_id`| `counter_party_id, counter_party_address, query_checksum, policy_checksum`                  | All                            | Gets the transfer process ID for a connection                                               |
| `delete_connection`         | `counter_party_id, counter_party_address, query_checksum, policy_checksum`                  | All                            | Deletes an EDR connection     |

## Attribute Reference

### MemoryConnectionManager

| Attribute              | Type      | Description                                      |
|------------------------|-----------|--------------------------------------------------|
| `open_connections`     | `dict`    | In-memory cache of EDR connections               |
| `provider_id_key`      | `str`     | Key for provider ID in connection data           |
| `edrs_key`             | `str`     | Key for EDR count in open_connections            |
| `logger`               | `Logger`  | Optional logger for debug/info output            |
| `verbose`              | `bool`    | Enables verbose logging                          |
| `_lock`                | `RLock`   | Thread lock for concurrency                      |

### FileSystemConnectionManager

| Attribute              | Type      | Description                                      |
|------------------------|-----------|--------------------------------------------------|
| `file_path`            | `str`     | Path to JSON file for file-based persistence     |
| `persist_interval`     | `int`     | Interval (seconds) for persisting to disk        |
| `lock`                 | `FileLock`| File lock for safe concurrent access             |
| `_stop_event`          | `Event`   | Threading event to stop background tasks         |
| `_last_loaded_hash`    | `Any`     | Tracks last loaded hash for file changes         |
| `open_connections`     | `dict`    | In-memory cache of EDR connections               |

### PostgresConnectionManager

| Attribute              | Type      | Description                                      |
|------------------------|-----------|--------------------------------------------------|
| `engine`               | `Engine`  | SQLAlchemy engine for database persistence       |
| `table_name`           | `str`     | Table name for storing EDR connections           |

## Further Reading

- [Connector Services Overview](services.md)
- [Connector Models](models.md)
- [SDK Structure and Components](../../../core-concepts/sdk-architecture/sdk-structure-and-components.md)
- [API Reference](https://eclipse-tractusx.github.io/api-hub/)

---

## NOTICE

This work is licensed under the [CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/legalcode).

- SPDX-License-Identifier: CC-BY-4.0
- SPDX-FileCopyrightText: 2025 Contributors to the Eclipse Foundation
- Source URL: https://github.com/eclipse-tractusx/tractusx-sdk
