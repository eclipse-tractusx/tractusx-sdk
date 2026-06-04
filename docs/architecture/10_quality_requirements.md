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

# 10. Quality Requirements

## Quality Tree

The following quality scenarios are derived from the quality goals in [Chapter 1](01_introduction_and_goals.md).

## Quality Scenarios

### Correctness

| Scenario ID | Stimulus | Response | Metric |
|-------------|---------|----------|--------|
| Q-C1 | A consumer calls `get_catalog_by_dct_type()` against a running EDC | The catalog response is deserialized into typed `CatalogOffer` objects with no data loss | All fields present in the API response are accessible on the returned model |
| Q-C2 | A consumer creates a shell descriptor in the DTR | The returned `ShellDescriptor` includes the server-assigned `id` | Round-trip create → fetch returns identical descriptor |

### Backward Compatibility

| Scenario ID | Stimulus | Response | Metric |
|-------------|---------|----------|--------|
| Q-B1 | A new minor version (e.g., `0.8.0`) is released | Existing code using `0.7.x` APIs compiles and runs without modification | Zero breaking API changes in minor releases |
| Q-B2 | A new EDC version (`neptune`) is added | Existing `jupiter` and `saturn` service code is unaffected | No changes required to existing version submodules |

### Usability

| Scenario ID | Stimulus | Response | Metric |
|-------------|---------|----------|--------|
| Q-U1 | A developer new to EDC reads the getting-started guide | They execute a successful catalog query | Achievable in under 15 minutes with the guide |
| Q-U2 | A developer uses an IDE with the SDK installed | All public service methods have type hints and appear in auto-complete | 100% of public API methods annotated with types |

### Testability

| Scenario ID | Stimulus | Response | Metric |
|-------------|---------|----------|--------|
| Q-T1 | A pull request is opened | CI runs the full test suite and reports coverage | Coverage enforced by `pytest-cov`; PRs failing coverage are blocked |
| Q-T2 | A developer writes a unit test for a service | The service can be tested without a running EDC | All adapter HTTP calls can be mocked via `requests-mock` |

### Extensibility

| Scenario ID | Stimulus | Response | Metric |
|-------------|---------|----------|--------|
| Q-E1 | A new EDC version needs to be supported | A new version submodule is added under `adapters/connector/` and `controllers/connector/` | Existing stable version submodules require zero changes |
| Q-E2 | A consumer needs custom authentication | They implement `AuthManagerInterface` and inject it into the service | No SDK source files need to be modified |

## NOTICE

This work is licensed under the [CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/legalcode).

- SPDX-License-Identifier: CC-BY-4.0
- SPDX-FileCopyrightText: 2026 Contributors to the Eclipse Foundation
- SPDX-FileCopyrightText: 2026 LKS Next
- Source URL: [https://github.com/eclipse-tractusx/tractusx-sdk](https://github.com/eclipse-tractusx/tractusx-sdk)
