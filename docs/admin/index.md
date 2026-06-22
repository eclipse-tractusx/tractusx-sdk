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

# Administrator's Guide

This guide is intended for **operators and system administrators** who deploy and run applications built on the Eclipse Tractus-X SDK.

## Scope

The Eclipse Tractus-X SDK is a **pure Python library** — it ships no Docker images, Helm charts, or server processes of its own. Operators interact with it indirectly: they configure, deploy, and operate the applications that embed the SDK (e.g., microservices from [tractusx-sdk-services](https://github.com/eclipse-tractusx/tractusx-sdk-services), or custom applications).

This guide covers everything an operator needs to know about the SDK's runtime behavior, configuration options, and operational concerns.

## Contents

| Section | Description |
|---------|-------------|
| [Configuration](configuration.md) | All configurable parameters: `ServiceFactory`, connection managers, authentication, logging |
| [Production Deployment](production-deployment.md) | Production checklist, connection manager selection, multi-process scaling |
| [Security](security.md) | Credential management, OAuth2 hardening, HTTPS enforcement |
| [Health Checks](health-checks.md) | Liveness and readiness endpoints using the SDK's observability controller |
| [Upgrade Guide](upgrade-guide.md) | How to upgrade the SDK version, migration between dataspace versions (Jupiter → Saturn) |

## Quick Reference

| Topic | Recommendation |
|-------|---------------|
| Connection state | Use `PostgresConnectionManager` for multi-process or production deployments |
| Authentication | Use `OAuth2Manager` with Keycloak in production; never use `AuthManager` (API key) in production |
| Secrets | Always inject credentials via environment variables — never hardcode them |
| Protocol version | Target `saturn` for new deployments; maintain `jupiter` only for legacy EDC compatibility |
| Documentation updates | Keep the admin guide up-to-date with every release that changes configuration or operational behavior |

## NOTICE

This work is licensed under the [CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/legalcode).

- SPDX-License-Identifier: CC-BY-4.0
- SPDX-FileCopyrightText: 2026 Contributors to the Eclipse Foundation
- SPDX-FileCopyrightText: 2026 LKS Next
- Source URL: [https://github.com/eclipse-tractusx/tractusx-sdk](https://github.com/eclipse-tractusx/tractusx-sdk)
