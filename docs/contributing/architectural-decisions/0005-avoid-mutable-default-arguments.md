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

# 5. Avoid mutable default arguments

Date: 2026-11-17

## Status

Proposed

## Context

Python evaluates default argument values when a function is defined, not each time it is called. If a mutable value such as a list, dictionary, or set is used as a default, calls can share and unexpectedly modify the same object. This can cause state to leak between calls and produce hard-to-find bugs in SDK consumers.

## Decision

SDK functions and methods must not use mutable objects as default argument values. Use an immutable default when suitable. When a mutable value is needed, use `None` as the default and create a new object inside the function.

## Consequences

This avoids unintended state sharing between calls and makes behavior more predictable for SDK consumers. Functions that need mutable defaults require a small amount of initialization in their body.

## NOTICE

This work is licensed under the [CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/legalcode).

- SPDX-License-Identifier: CC-BY-4.0
- SPDX-FileCopyrightText: 2026 Contributors to the Eclipse Foundation
- SPDX-FileCopyrightText: 2026 Catena-X Automotive Network e.V.
- SPDX-FileCopyrightText: 2026 LKS Next
- Source URL: [https://github.com/eclipse-tractusx/tractusx-sdk](https://github.com/eclipse-tractusx/tractusx-sdk)