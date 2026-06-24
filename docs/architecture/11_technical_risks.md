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

# 11. Technical Risks and Technical Debt

## Risks

| ID | Risk | Probability | Impact | Mitigation |
|----|------|-------------|--------|-----------|
| R-01 | **EDC API churn** — EDC releases break the SDK's adapter/controller layer with each new version | High | High | Version submodule isolation (`jupiter/`, `saturn/`) limits blast radius. CI runs compatibility tests against declared supported versions. |
| R-02 | **Windows + `uvloop` incompatibility** — `uvloop` (used by async consumers) does not support Windows; platform markers in `pyproject.toml` can fall out of sync | Medium | Medium | Platform-conditional dependencies in `pyproject.toml`. CI runs the compatibility test matrix on Linux only; Windows-specific notes in documentation. |
| R-03 | **Python 3.12+ lower-bound limits adoption** — Some organizations still run Python 3.10/3.11; forcing 3.12+ may block SDK adoption | Low | Medium | Validated via CI compatibility matrix (3.12, 3.13, 3.14-dev). Lower bound exists due to typing improvements; no plans to lower it. |
| R-04 | **In-memory EDR cache loss on restart** — The connection cache does not survive process restarts; in high-churn environments this triggers many redundant contract negotiations | Medium | Low | Documented in [ADR-0002](../contributing/architectural-decisions/0002-data-storage-architecture.md). Consuming applications can implement their own persistent cache and inject it. |
| R-05 | **Single-repository maintainer concentration** — A small number of core maintainers hold deep knowledge of the adapter layer | Medium | High | Addressed by ADR documentation, inline code comments, and community involvement in SDK weekly meetings. |

## Technical Debt

| ID | Debt Item | Effort | Priority |
|----|-----------|--------|---------|
| TD-01 | **Legacy `v0_9_0` adapter path** — Old import paths (e.g., `tractusx_sdk.dataspace.services.connector.v0_9_0`) are deprecated but still exist in the codebase for backward compatibility. Removal planned for a future major version. | Medium | Low |
| TD-02 | **`[0.3.0]` changelog entries without categories** — Some early changelog versions group entries without `### Added` / `### Fixed` headings, violating Keep A Changelog format. | Low | Low |
| TD-03 | **Missing async service variants** — The current service layer is synchronous. Async variants would benefit pipeline and FastAPI consumers. This was deprioritized in favor of correctness. | High | Medium |
| TD-04 | **Windows CI coverage gap** — The compatibility test matrix only covers Linux. Windows-specific behavior (uvloop absence, path separators) is not automatically tested. | Medium | Medium |

## NOTICE

This work is licensed under the [CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/legalcode).

- SPDX-License-Identifier: CC-BY-4.0
- SPDX-FileCopyrightText: 2026 Contributors to the Eclipse Foundation
- SPDX-FileCopyrightText: 2026 LKS Next
- Source URL: [https://github.com/eclipse-tractusx/tractusx-sdk](https://github.com/eclipse-tractusx/tractusx-sdk)
