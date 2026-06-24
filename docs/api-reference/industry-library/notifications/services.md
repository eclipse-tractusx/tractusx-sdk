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
# Notification Services

The Notification Services provide high-level abstractions for sending and managing Industry Core notifications through the Catena-X dataspace. They handle the complete EDC negotiation flow — catalog discovery, contract negotiation, EDR token retrieval, and notification delivery — so that consuming applications can focus on business logic.

## Purpose

Notification Services encapsulate the complexity of sending notifications through the Eclipse Dataspace Connector (EDC), offering:

- **Asset discovery** — Find `cx-taxo:DigitalTwinEventAPI` assets in provider catalogs
- **Contract negotiation** — Negotiate access to notification endpoints via EDR
- **Notification delivery** — Send validated notifications to providers
- **Multi-provider support** — Broadcast notifications to multiple providers in a single call
- **Saturn & Jupiter compatibility** — Works with both DSP 2025-1 (Saturn) and legacy (Jupiter) connectors
- **BPNL-based discovery** — Resolve connector addresses from Business Partner Numbers (Saturn)
- **Asset management** — Create and verify `DigitalTwinEventAPI` assets on provider connectors

## Key Components

| Component | Description |
|-----------|-------------|
| `NotificationConsumerService` | Consumes notification endpoints — discovers assets, negotiates contracts, sends notifications |
| `NotificationService` | Manages notification assets on the provider side — creates and verifies `DigitalTwinEventAPI` assets |
| `NotificationError` | Base exception for all notification-related errors |
| `NotificationValidationError` | Raised when notification validation fails |
| `NotificationParsingError` | Raised when incoming notification data cannot be parsed |
| `UnknownNotificationTypeError` | Raised when an unrecognized notification type is encountered |

---

## NotificationConsumerService

### Initialization

```python
from tractusx_sdk.industry.services.notifications import NotificationConsumerService
from tractusx_sdk.dataspace.services.connector import ConnectorConsumerService

# Initialize connector consumer (Jupiter or Saturn)
connector = ConnectorConsumerService(
    connector_address="https://my-connector.example.com",
    connector_id="BPNL000000000001",
    auth_manager=auth_manager,
    dataspace_version="saturn",  # or "jupiter"
)

# Create notification consumer service
notification_consumer = NotificationConsumerService(
    connector_consumer=connector,
    verbose=True,
)
```

You can also use the **builder pattern**:

```python
notification_consumer = (
    NotificationConsumerService.builder()
    .connector_consumer(connector)
    .verbose(True)
    .build()
)
```

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `connector_consumer` | `BaseConnectorConsumerService` | No | Connector consumer for EDC operations |
| `verbose` | `bool` | No | Enable verbose logging (default: `True`) |
| `logger` | `logging.Logger` | No | Custom logger instance |

---

### Discover Notification Assets

Query a provider's connector catalog for `DigitalTwinEventAPI` assets.

=== "Direct (counter-party ID)"

    ```python
    datasets = notification_consumer.discover_notification_assets(
        provider_bpn="BPNL000000000002",
        provider_dsp_url="https://provider.example.com/api/v1/dsp",
        timeout=60,
    )

    for dataset in datasets:
        print(f"Asset ID: {dataset.get('id') or dataset.get('@id')}")
    ```

=== "BPNL-based discovery (Saturn)"

    ```python
    datasets = notification_consumer.discover_notification_assets_with_bpnl(
        bpnl="BPNL000000000002",
        counter_party_address="https://provider.example.com/api/v1/dsp",
        timeout=60,
    )
    ```

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `provider_bpn` / `bpnl` | `str` | Yes | Business Partner Number of the provider |
| `provider_dsp_url` / `counter_party_address` | `str` | Yes | DSP endpoint URL of the provider connector |
| `timeout` | `int` | No | Request timeout in seconds (default: `60`) |
| `dct_type` | `str` | No | DCT type to filter (default: `cx-taxo:DigitalTwinEventAPI`) |

#### Returns

`List[Dict[str, Any]]` — List of catalog datasets matching the notification type.

---

### Negotiate Notification Access

Perform the full negotiation flow: query catalog, select asset/policy, start EDR negotiation, and wait for the EDR entry.

```python
edr_entry = notification_consumer.negotiate_notification_access(
    provider_bpn="BPNL000000000002",
    provider_dsp_url="https://provider.example.com/api/v1/dsp",
    max_retries=6,
    retry_timeout=10,
)

transfer_id = edr_entry.get("transferProcessId")
```

#### BPNL variant (Saturn)

```python
endpoint, token = notification_consumer.negotiate_notification_access_with_bpnl(
    bpnl="BPNL000000000002",
    counter_party_address="https://provider.example.com/api/v1/dsp",
)
```

---

### Get Notification Endpoint

Perform a DSP exchange to obtain the dataplane endpoint URL and authorization token.

=== "Direct"

    ```python
    endpoint, token = notification_consumer.get_notification_endpoint(
        provider_bpn="BPNL000000000002",
        provider_dsp_url="https://provider.example.com/api/v1/dsp",
    )
    ```

=== "BPNL-based (Saturn)"

    ```python
    endpoint, token = notification_consumer.get_notification_endpoint_with_bpnl(
        bpnl="BPNL000000000002",
        counter_party_address="https://provider.example.com/api/v1/dsp",
    )
    ```

#### Returns

`tuple[str, str]` — `(endpoint_url, authorization_token)`.

---

### Send Notification

Send a notification through the complete DSP flow (negotiate + deliver).

=== "Direct"

    ```python
    from tractusx_sdk.industry.models.notifications import Notification

    notification = (
        Notification.builder()
        .context("IndustryCore-DigitalTwinEventAPI-ConnectToParent:3.0.0")
        .sender_bpn("BPNL000000000001")
        .receiver_bpn("BPNL000000000002")
        .information("Part relationship update")
        .affected_items(["SN-001", "SN-002"])
        .build()
    )

    result = notification_consumer.send_notification(
        provider_bpn="BPNL000000000002",
        provider_dsp_url="https://provider.example.com/api/v1/dsp",
        notification=notification,
    )
    ```

=== "BPNL-based (Saturn)"

    ```python
    result = notification_consumer.send_notification_with_bpnl(
        bpnl="BPNL000000000002",
        counter_party_address="https://provider.example.com/api/v1/dsp",
        notification=notification,
    )
    ```

=== "Pre-obtained endpoint"

    ```python
    result = notification_consumer.send_notification_to_endpoint(
        endpoint_url=endpoint,
        access_token=token,
        notification=notification,
        endpoint_path="/notify",
    )
    ```

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `provider_bpn` / `bpnl` | `str` | Yes | Business Partner Number of the provider |
| `provider_dsp_url` / `counter_party_address` | `str` | Yes | DSP endpoint URL |
| `notification` | `Notification` | Yes | The notification to send |
| `endpoint_path` | `str` | No | Additional path appended to the dataplane endpoint |
| `policies` | `List[Dict]` | No | Allowed policies for negotiation |
| `timeout` | `int` | No | Request timeout in seconds (default: `30`) |
| `verify_ssl` | `bool` | No | Verify SSL certificates (default: `True`) |

---

### Send to Multiple Providers

Broadcast a notification to a list of providers in a single call.

```python
providers = [
    {"bpn": "BPNL000000000002", "dsp_url": "https://provider-a.example.com/dsp"},
    {"bpn": "BPNL000000000003", "dsp_url": "https://provider-b.example.com/dsp"},
]

results = notification_consumer.send_to_multiple_providers(
    providers=providers,
    notification=notification,
    stop_on_error=False,
)

for bpn, result in results.items():
    if result["success"]:
        print(f"{bpn}: sent successfully")
    else:
        print(f"{bpn}: failed — {result['error']}")
```

---

## NotificationService (Provider Side)

Manages `DigitalTwinEventAPI` assets on the connector's provider side.

### Initialization

```python
from tractusx_sdk.industry.services.notifications import NotificationService
from tractusx_sdk.dataspace.services.connector import ConnectorProviderService

connector_provider = ConnectorProviderService(
    connector_address="https://my-connector.example.com",
    auth_manager=auth_manager,
)

notification_service = NotificationService(
    connector_provider=connector_provider,
    verbose=True,
)
```

### Ensure Notification Asset Exists

Creates a `DigitalTwinEventAPI` asset if it does not already exist.

```python
asset = notification_service.ensure_notification_asset_exists(
    asset_id="notification-asset-001",
    notification_endpoint_url="https://my-app.example.com/notifications",
    version="3.0",
)
```

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `asset_id` | `str` | Yes | Unique identifier for the notification asset |
| `notification_endpoint_url` | `str` | Yes | Base URL for the notification endpoint |
| `version` | `str` | No | Asset version (default: `"3.0"`) |
| `semantic_id` | `str` | No | Optional semantic ID for the asset |
| `proxy_params` | `Dict[str, str]` | No | Proxy configuration for the data address |
| `headers` | `Dict[str, str]` | No | Headers for the data address |
| `private_properties` | `Dict[str, Any]` | No | Private properties for the asset |

---

## Error Handling

All notification operations raise typed exceptions that inherit from `NotificationError`:

```python
from tractusx_sdk.industry.services.notifications import (
    NotificationError,
    NotificationValidationError,
    NotificationParsingError,
    UnknownNotificationTypeError,
)

try:
    result = notification_consumer.send_notification(
        provider_bpn="BPNL000000000002",
        provider_dsp_url="https://provider.example.com/dsp",
        notification=notification,
    )
except NotificationValidationError as e:
    print(f"Validation failed: {e.message}")
except NotificationError as e:
    print(f"Notification error: {e.message}")
```

| Exception | Description |
|-----------|-------------|
| `NotificationError` | Base exception for all notification errors |
| `NotificationValidationError` | Missing required fields, invalid BPN format, sender equals receiver |
| `NotificationParsingError` | Incoming notification data cannot be parsed into a `Notification` model |
| `UnknownNotificationTypeError` | Unrecognized notification classification or type |

---

## Saturn vs Jupiter Compatibility

The notification services work transparently with both EDC versions:

| Feature | Jupiter (0-10-X) | Saturn (0-11-X) |
|---------|-------------------|-----------------|
| Catalog dataset key | `dcat:dataset` | `dataset` |
| Policy key prefix | `odrl:` | unprefixed |
| Discovery methods | `discover_notification_assets` | `discover_notification_assets` + `_with_bpnl` |
| DSP negotiation | `do_dsp_by_dct_type` | `do_dsp_with_bpnl` (BPNL discovery) |
| Endpoint methods | `get_notification_endpoint` | `get_notification_endpoint` + `_with_bpnl` |

The `_with_bpnl` variants use Saturn's BPNL-based connector discovery (`get_discovery_info()`) to resolve the actual connector address and protocol before performing the DSP exchange.

## NOTICE

This work is licensed under the [CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/legalcode).

- SPDX-License-Identifier: CC-BY-4.0
- SPDX-FileCopyrightText: 2025, 2026 Contributors to the Eclipse Foundation
- SPDX-FileCopyrightText: 2025, 2026 Catena-X Automotive Network e.V.
- Source URL: [https://github.com/eclipse-tractusx/tractusx-sdk](https://github.com/eclipse-tractusx/tractusx-sdk)
