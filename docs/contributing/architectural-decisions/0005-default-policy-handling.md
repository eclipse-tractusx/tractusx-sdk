<!--

Eclipse Tractus-X - Software Development KIT

Copyright (c) 2026 Contributors to the Eclipse Foundation

See the NOTICE file(s) distributed with this work for additional
information regarding copyright ownership.

This work is made available under the terms of the
Creative Commons Attribution 4.0 International (CC-BY-4.0) license,
which is available at
https://creativecommons.org/licenses/by/4.0/legalcode.

SPDX-License-Identifier: CC-BY-4.0

-->

# 5. Default policy handling

Date: 2026-11-17

## Status

Accepted

## Context

Requiring policy configuration during development adds setup and maintenance overhead. A permissive default makes it easier to develop and use the SDK when no policy restrictions are required.

## Decision

Policy configuration defaults to `None`. When no policies are supplied, all policies are accepted. Consumers that require restrictions must provide the relevant policies explicitly.

## Consequences

This reduces configuration overhead for development and unrestricted use cases. The default is permissive, so consumers that need policy enforcement are responsible for supplying policy restrictions.

## NOTICE

This work is licensed under the [CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/legalcode).

- SPDX-License-Identifier: CC-BY-4.0
- SPDX-FileCopyrightText: 2026 Contributors to the Eclipse Foundation
- SPDX-FileCopyrightText: 2026 Catena-X Automotive Network e.V.
- SPDX-FileCopyrightText: 2026 LKS Next
- Source URL: [https://github.com/eclipse-tractusx/tractusx-sdk](https://github.com/eclipse-tractusx/tractusx-sdk)