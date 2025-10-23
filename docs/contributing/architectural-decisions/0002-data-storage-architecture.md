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

# 2. Data Storage Architecture

Date: 2025-02-20

## Status

Accepted

## Context


From the experience from a data provider with many different products to offer, a SQL database is really critical for supporting the different complex queries that need to be performed.
However this Tractus-X SDK implementation does not requires persistence at all, since the persistance is located in the service that contain the original data (Digital Twin Registry, EDC, etc.)

The Tractus-X SDK will have a memory/cache mechanism so it can store just the operations that were performed in a short time, and this data format:


```py


class ConnectorService:

    memory_cache: dict

    def __init__(self, disabled=true):
        self.memory_cache = {}
    
    # EXAMPLE
    def add_connection(self, edc_url, bpn, dct_type, policies):
        self.memory_cache[bpn] = {}
        self.memory_cache[bpn][edc_url] = dct_type
        ...

```

The persistence layer will be done in the Use Case applications or in the Industry Core Hub Backend using whatever they want.

They can decide which technology (SQL or NO-SQL).

## Decision

The Tractus-X SDK will provide an in memory cache for the Microservice Server (FAST-API) but it can be disabled per parameters.
The Storage Architecture will not be specified in the SDK, need to be specified in the application that uses it.

## Consequences

- Applications need to implement their own persistence layer
- If the application services (EDC, DTR, and data storage) are down then we can't know what was registered and when.

## NOTICE

This work is licensed under the [CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/legalcode).

- SPDX-License-Identifier: CC-BY-4.0
- SPDX-FileCopyrightText: 2025 Contributors to the Eclipse Foundation
- Source URL: https://github.com/eclipse-tractusx/tractusx-sdk
