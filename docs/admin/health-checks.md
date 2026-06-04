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

# Health Checks

The Eclipse Tractus-X SDK provides access to the EDC connector's built-in health, liveness, and readiness endpoints via the `ApplicationObservabilityController`. This is available for the `saturn` dataspace version only.

## Available Endpoints

| Method | EDC Endpoint | Purpose |
|--------|-------------|---------|
| `get_health` | `GET /api/check/health` | Overall health of the connector application |
| `get_liveness` | `GET /api/check/liveness` | Whether the connector process is alive |

!!! note
    These methods call the **EDC connector's** health endpoints — they report on the EDC's health, not the health of your application. Use them to include EDC reachability as a component in your application's own health probe.

## Usage

The `ApplicationObservabilityController` is accessed via the `ControllerFactory`:

```python
from tractusx_sdk.dataspace.controllers.connector.controller_factory import ControllerFactory
from tractusx_sdk.dataspace.adapters.connector.adapter_factory import AdapterFactory

adapter = AdapterFactory.get_dma_adapter(
    dataspace_version="saturn",
    base_url=os.environ["EDC_BASE_URL"],
    dma_path="/management",
    headers=headers,
)

observability_controller = ControllerFactory.get_application_observability_controller(
    dataspace_version="saturn",
    adapter=adapter,
)

health = observability_controller.get_health()
liveness = observability_controller.get_liveness()
```

## Jupiter Version Limitation

The `ApplicationObservabilityController` is only available for `dataspace_version="saturn"`. For applications targeting `jupiter`, implement health checks by attempting a lightweight call (e.g., listing assets with a limit of 1) and treating a successful response as a healthy signal.

## NOTICE

This work is licensed under the [CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/legalcode).

- SPDX-License-Identifier: CC-BY-4.0
- SPDX-FileCopyrightText: 2026 Contributors to the Eclipse Foundation
- SPDX-FileCopyrightText: 2026 LKS Next
- Source URL: [https://github.com/eclipse-tractusx/tractusx-sdk](https://github.com/eclipse-tractusx/tractusx-sdk)
