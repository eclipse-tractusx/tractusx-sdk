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

# 3. SDK Module Architecture

Date: 2025-03-31

## Status

Accepted

## Context

https://github.com/eclipse-tractusx/tractusx-sdk/discussions/49

In the existing Tractus-X SDK Dataspace layer, we currently find the current modules:

* `config`: Configuration files and settings used throughout the SDK.
* `managers`: Classes that handle the management of different components within the SDK and the data handling.
* `models`: Data models and schemas that define the structure of the data used by the SDK.
* `services`: Service classes and functions that provide the core functionality of the SDK and contact to external
  services.
* `tools`: Utility scripts and helper functions that support the development and maintenance of the SDK.
  Comparable to utilities.

As the Tractus-X SDK will be used for interactions between quite a few different APIs, the following modules will be
included, in addition to the already existing ones:

* An `adapters` module, to handle HTTP requests to those APIs that will be supported.
* A `controllers` module, which implements logic specific to the API contexts of the supported APIs.

Being able to handle multiple different versions for the same application is also a requirement of the SDK, which means
we must also create a submodule for each of the supported application versions, in each SDK module that was listed
above. In example, the following must be possible:

```python
from tractusx_sdk.dataspace.adapters.connector.v0_9_0 import DmaAdapter as DmaAdapterV0_9_0
from tractusx_sdk.dataspace.adapters.connector.v0_10_0 import DmaAdapter as DmaAdapterV0_10_0
```

As such, it was also decided to implement a factory pattern for each module, which will allow for easier management of
the different versions and classes.

## Decision

Based on the context provided above, the Tractus-X SDK will implement the following directory structure:

```
.
├── src/
│   ├── dataspace/
│   │   ├── adapters/
│   │   │   ├── base_adapter.py
│   │   │   ├── ... other common adapters
│   │   │   └── connector/
│   │   │       ├── adapter_factory.py                        # Adapter Factory
│   │   │       ├── base_dma_adapter.py                       # Abstract Base Class
│   │   │       ├── base_dataplane_adapter.py                 # Abstract Base Class
│   │   │       ├── ... other connector base adapters
│   │   │       ├── v0.9.0/
│   │   │       │   └── ... 0.9.0 version specific adapters   # Concrete implementation
│   │   │       ├── vX.Y.Z/
│   │   │       │   └── ... X.Y.Z version specific adapters   # Concrete implementation
│   │   │       └── ... other connector versions' adapters/
│   │   ├── config/
│   │   │   └── ... same approach
│   │   ├── controllers/
│   │   │   └── ... same approach
│   │   ├── managers/
│   │   │   └── ... same approach
│   │   ├── models/
│   │   │   └── ...
│   │   ├── services/
│   │   │   └── ...
│   │   └── tools/
│   │       └── ...
│   ├── industry/
│   │   └── ...
│   └── extensions/
│       └── ...
└── tests/
    ├── dataspace/
    │   └── ... same approach as above
    ├── industry/
    │   └── ...
    └── extensions/
        └── ...
```

## Consequences

- The factory pattern will be used to create the entities, which will allow for easy extension and modification of the
  SDK in the future.
    - Conversely, the factory pattern will need to be able to dynamically load the correct modules, based on the
      required version.

## NOTICE

This work is licensed under the [CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/legalcode).

- SPDX-License-Identifier: CC-BY-4.0
- SPDX-FileCopyrightText: 2025 Contributors to the Eclipse Foundation
- Source URL: https://github.com/eclipse-tractusx/tractusx-sdk
