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

# Security

This page describes the security practices operators must follow when deploying applications built on the Eclipse Tractus-X SDK.

## Authentication

### Use OAuth2 in Production

Always use `OAuth2Manager` with a Keycloak (or compatible OIDC) instance in production environments. `OAuth2Manager` handles token acquisition, caching, and automatic refresh.

```python
import os
from tractusx_sdk.dataspace.managers import OAuth2Manager

auth_manager = OAuth2Manager(
    token_url=os.environ["IAM_TOKEN_URL"],
    client_id=os.environ["CLIENT_ID"],
    client_secret=os.environ["CLIENT_SECRET"],
)
headers = auth_manager.add_auth_header({"Content-Type": "application/json"})
```

### Never Use Static API Keys in Production

`AuthManager` (API key-based authentication) is intended for development and testing only. Static API keys:

- Cannot be scoped or time-limited
- Are difficult to rotate without downtime
- Risk leakage via logs, environment dumps, or error messages

!!! danger
    Do not use `AuthManager` in any internet-facing or production deployment.

## Credential Management

### Environment Variables

Never hardcode credentials in source code or configuration files committed to version control. Always inject secrets at runtime:

```python
import os

token_url     = os.environ["IAM_TOKEN_URL"]
client_id     = os.environ["CLIENT_ID"]
client_secret = os.environ["CLIENT_SECRET"]
database_url  = os.environ["DATABASE_URL"]
```

### Secrets Managers

For containerized deployments, use a secrets manager to inject environment variables at runtime:

- **Kubernetes**: `Secret` objects mounted as environment variables
- **AWS**: AWS Secrets Manager + External Secrets Operator
- **HashiCorp Vault**: Vault Agent Injector or Vault Secrets Operator
- **Azure**: Azure Key Vault + CSI driver

### Credential Rotation

To rotate OAuth2 client secrets without downtime:

1. Create a new client secret in Keycloak (keep the old one active)
2. Update the `CLIENT_SECRET` environment variable in your deployment
3. Restart/redeploy the application
4. Revoke the old client secret in Keycloak

## Transport Security

All communication between the SDK and external services must use **HTTPS**. Never use plain HTTP for:

- EDC connector control plane (`base_url`)
- Keycloak token endpoint (`token_url`)
- Digital Twin Registry
- Discovery services

!!! warning
    The SDK does not enforce HTTPS at the library level — it is the operator's responsibility to ensure all configured URLs use `https://`.

## Logging and Data Exposure

The `verbose=True` option in `ServiceFactory` logs full HTTP request and response bodies. This can expose:

- Authorization tokens
- EDR endpoint URLs and access tokens
- Contract negotiation details
- Asset data

**Always set `verbose=False` in production.** Use it only in isolated development environments with non-sensitive data.

```python
service = ServiceFactory.get_connector_consumer_service(
    ...,
    verbose=False,  # must be False in production
)
```

## NOTICE

This work is licensed under the [CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/legalcode).

- SPDX-License-Identifier: CC-BY-4.0
- SPDX-FileCopyrightText: 2026 Contributors to the Eclipse Foundation
- SPDX-FileCopyrightText: 2026 LKS Next
- Source URL: [https://github.com/eclipse-tractusx/tractusx-sdk](https://github.com/eclipse-tractusx/tractusx-sdk)
