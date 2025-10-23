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

# 4. Tractus-X SDK Services

Date: 2025-05-12

## Status

Accepted

## Discussion

https://github.com/eclipse-tractusx/tractusx-sdk/discussions/61

## Context

It was agreed that the best for the tractus-x sdk microservices that use the SDK at a specific version are to be compiled and maintained in a separated repository.
The tractus-x sdk will provide a plain code library that can be used by mutliple products.

Therefore it will not be deployable and also will not contain any type of "microservice" or "api" specification.

## Decision

Create a new respository called https://github.com/eclipse-tractusx/tractusx-sdk-services

It will store the microservices that use the SDK for a specific use case.

In this way whatever is uploaded there can still be merged to the "main" framework.

## Consequences

- It will impact in the way we maintain the repositories, having a tractusx-sdk-services repository will require more maintaince.
- It may occur that duplication of code is happening in some cases of migration to the sdk.
  - Generic functionalities shall be migrated to the SDK and not be maintained in the services layer.
  - In this way other services and products can benefit from it.

## NOTICE

This work is licensed under the [CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/legalcode).

- SPDX-License-Identifier: CC-BY-4.0
- SPDX-FileCopyrightText: 2025 Contributors to the Eclipse Foundation
- Source URL: https://github.com/eclipse-tractusx/tractusx-sdk
