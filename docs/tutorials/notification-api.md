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

# Notification API Tutorial

This tutorial demonstrates how to send and receive notifications between Catena-X dataspace participants using the Tractus-X SDK Notification API extension.

## Overview

The Notification API enables secure, standardized communication between business partners in the Catena-X dataspace. It follows the **Industry Core Notifications** schema (`io.catenax.shared.message_header_3.0.0`) and uses the **DigitalTwinEventAPI** asset type.

### Use Cases

- **Quality Alerts**: Notify partners about quality issues
- **Supply Chain Events**: Communicate delivery updates or disruptions
- **Digital Twin Updates**: Inform partners when digital twin data changes
- **Custom Business Events**: Any standardized B2B notification

### Architecture

```
┌─────────────────┐                           ┌─────────────────┐
│   Consumer      │                           │    Provider     │
│   (Sender)      │                           │   (Receiver)    │
├─────────────────┤                           ├─────────────────┤
│ NotificationCon-│    DSP Protocol           │ Notification    │
│ sumerService    │ ◄─────────────────────►   │ Asset + Policy  │
│                 │                           │ + Contract      │
│ BaseConnector   │    Catalog/Negotiate/     │                 │
│ ConsumerService │    Transfer               │ Notification    │
└────────┬────────┘                           │ Endpoint        │
         │                                    └────────┬────────┘
         │                                             │
         │              HTTP POST                      │
         └─────────────────────────────────────────────┘
                    (via Data Plane)
```

## Prerequisites

Before starting this tutorial, ensure you have:

- **Python 3.12+** installed
- **Tractus-X SDK** installed (`pip install tractusx-sdk`)
- **Two EDC connectors** deployed (one for sending, one for receiving)
- **API credentials** for both connectors
- **A notification endpoint** URL (e.g., your backend API or webhook.site for testing)

## Part 1: Create a Notification Endpoint (Provider Side)

First, the **provider** (receiver of notifications) must set up their connector to accept notifications. This requires creating:

1. **Asset** - Defines the notification endpoint
2. **Policy** - Controls who can send notifications
3. **Contract Definition** - Makes the asset discoverable in the catalog

### Step 1: Configure Your Provider Connector

Create a file called `create_notification_asset.py`:

```python
import logging

from tractusx_sdk.dataspace.services.connector.base_connector_provider import (
    BaseConnectorProviderService,
)
from tractusx_sdk.extensions.notification_api import (
    NotificationService,
    NotificationError,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)
```

### Step 2: Set Up Configuration

```python
def main():
    """Create a notification asset in the EDC connector."""
    
    # ==========================================================================
    # Configuration - Update these values for your environment
    # ==========================================================================
    
    # Your connector settings (provider side)
    connector_base_url = "https://your-connector-controlplane.example.com"
    connector_dma_path = "/management"  # Management API path
    connector_api_key = "your-api-key"
    dataspace_version = "jupiter"  # EDC dataspace version
    
    # Notification asset settings
    asset_id = "notification-asset-001"
    policy_id = "notification-policy-001"
    contract_id = "notification-contract-001"
    
    # Your backend endpoint that will receive notifications
    notification_endpoint = "https://your-backend.example.com/api/notifications"
```

!!! tip "Testing Tip"
    For testing, you can use [webhook.site](https://webhook.site) to get a temporary endpoint URL that captures all incoming requests.

### Step 3: Create the Connector Provider Service

```python
    # Create the connector provider service
    logger.info("Creating connector provider service...")
    
    connector_provider = BaseConnectorProviderService(
        dataspace_version=dataspace_version,
        base_url=connector_base_url,
        dma_path=connector_dma_path,
        headers={
            "x-api-key": connector_api_key,
            "Content-Type": "application/json",
        },
        verbose=True,
        logger=logger,
    )
```

### Step 4: Create the Notification Service

```python
    # Create the notification service
    logger.info("Creating notification service...")
    
    notification_service = NotificationService(
        connector_provider=connector_provider,
        verbose=True,
        logger=logger,
    )
```

### Step 5: Create Asset, Policy, and Contract

```python
    try:
        # Create the notification asset
        logger.info(f"Creating notification asset '{asset_id}'...")
        
        result = notification_service.ensure_notification_asset_exists(
            asset_id=asset_id,
            notification_endpoint_url=notification_endpoint,
            version="3.0",
        )
        
        logger.info(f"Asset created: {result.get('@id', asset_id)}")
        
        # Create the policy (allow any participant to use)
        logger.info(f"Creating policy '{policy_id}'...")
        
        policy_result = connector_provider.create_policy(
            policy_id=policy_id,
            permissions=[
                {
                    "action": "odrl:use",
                }
            ],
        )
        
        logger.info(f"Policy created: {policy_result.get('@id', policy_id)}")
        
        # Create the contract definition
        logger.info(f"Creating contract definition '{contract_id}'...")
        
        contract_result = connector_provider.create_contract(
            contract_id=contract_id,
            usage_policy_id=policy_id,
            access_policy_id=policy_id,
            asset_id=asset_id,
        )
        
        logger.info(f"Contract created: {contract_result.get('@id', contract_id)}")
        
        # Summary
        logger.info("=" * 60)
        logger.info("Notification endpoint setup complete!")
        logger.info("=" * 60)
        logger.info(f"Asset ID:    {asset_id}")
        logger.info(f"Policy ID:   {policy_id}")
        logger.info(f"Contract ID: {contract_id}")
        logger.info(f"Endpoint:    {notification_endpoint}")
        logger.info("=" * 60)
        
    except NotificationError as e:
        logger.error(f"Failed to create notification asset: {e}")
        raise
    except ValueError as e:
        logger.error(f"Failed to create policy or contract: {e}")
        raise


if __name__ == "__main__":
    main()
```

### Run the Script

```bash
python create_notification_asset.py
```

Expected output:

```
2026-02-02 16:07:12,078 - __main__ - INFO - Creating notification asset 'notification-asset-001'...
2026-02-02 16:07:12,112 - __main__ - INFO - Asset created: notification-asset-001
2026-02-02 16:07:12,112 - __main__ - INFO - Creating policy 'notification-policy-001'...
2026-02-02 16:07:12,146 - __main__ - INFO - Policy created: notification-policy-001
2026-02-02 16:07:12,180 - __main__ - INFO - Creating contract definition 'notification-contract-001'...
2026-02-02 16:07:12,210 - __main__ - INFO - Contract created: notification-contract-001
============================================================
Notification endpoint setup complete!
============================================================
```

---

## Part 2: Send a Notification (Consumer Side)

Now the **consumer** (sender of notifications) can discover the provider's notification endpoint and send notifications through the dataspace.

### Step 1: Configure Your Consumer Connector

Create a file called `send_notification.py`:

```python
import logging

from tractusx_sdk.dataspace.services.connector.base_connector_consumer import (
    BaseConnectorConsumerService,
)
from tractusx_sdk.extensions.notification_api import (
    NotificationConsumerService,
    Notification,
    NotificationError,
    NotificationValidationError,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)
```

### Step 2: Set Up Configuration

```python
def main():
    """Send a notification through the dataspace."""
    
    # ==========================================================================
    # Configuration - Update these values for your environment
    # ==========================================================================
    
    # Your connector settings (consumer side)
    connector_base_url = "https://your-connector-controlplane.example.com"
    connector_dma_path = "/management"
    connector_api_key = "your-api-key"
    dataspace_version = "jupiter"
    
    # Your BPN (sender)
    sender_bpn = "BPNL000000000001"
    
    # Provider/Receiver settings
    provider_bpn = "BPNL000000000002"
    provider_dsp_url = "https://provider-connector.example.com/api/v1/dsp"
```

!!! warning "DSP Endpoint"
    The DSP endpoint path varies by connector configuration. Common paths are:
    
    - `/api/v1/dsp`
    - `/api/dsp`
    - `/dsp`
    
    Check with your connector administrator for the correct path.

### Step 3: Create the Consumer Service

```python
    # Create the connector consumer service
    logger.info("Creating connector consumer service...")
    
    connector_consumer = BaseConnectorConsumerService(
        dataspace_version=dataspace_version,
        base_url=connector_base_url,
        dma_path=connector_dma_path,
        headers={
            "x-api-key": connector_api_key,
            "Content-Type": "application/json",
        },
        verbose=True,
        logger=logger,
    )
    
    # Create the notification consumer service
    notification_service = NotificationConsumerService(
        connector_consumer=connector_consumer,
        verbose=True,
        logger=logger,
    )
```

### Step 4: Define Acceptable Policies

The consumer must specify which policies it will accept when negotiating access:

```python
    # Define acceptable policies (must match provider's offer)
    policies_to_accept = [
        {
            "odrl:permission": {
                "odrl:action": {
                    "@id": "odrl:use"
                }
            },
            "odrl:prohibition": [],
            "odrl:obligation": [],
        }
    ]
```

### Step 5: Build the Notification

```python
    # Build the notification using the builder pattern
    logger.info("Building notification...")
    
    notification = (
        Notification.builder()
        .sender_bpn(sender_bpn)
        .receiver_bpn(provider_bpn)
        .context("IndustryCore-DigitalTwinEventAPI-ConnectToParent:3.0.0")
        .information("This is a test notification from the Tractus-X SDK")
        .affected_items(["urn:uuid:12345678-1234-1234-1234-123456789012"])
        .build()
    )
    
    logger.info(f"Notification ID: {notification.header.message_id}")
    logger.info(f"From: {notification.header.sender_bpn}")
    logger.info(f"To: {notification.header.receiver_bpn}")
```

### Step 6: Send the Notification

```python
    try:
        logger.info("Sending notification...")
        
        result = notification_service.send_notification(
            provider_bpn=provider_bpn,
            provider_dsp_url=provider_dsp_url,
            notification=notification,
            policies=policies_to_accept,
            timeout=60,
        )
        
        logger.info("Notification sent successfully!")
        logger.info(f"Response: {result}")
        
        return result
        
    except NotificationValidationError as e:
        logger.error(f"Notification validation failed: {e}")
        raise
    except NotificationError as e:
        logger.error(f"Failed to send notification: {e}")
        raise


if __name__ == "__main__":
    main()
```

### Run the Script

```bash
python send_notification.py
```

Expected output:

```
2026-02-02 16:19:40,887 - __main__ - INFO - Building notification...
2026-02-02 16:19:40,887 - __main__ - INFO - Notification ID: cdad3da4-c9ba-4e98-9075-319f37367ef7
2026-02-02 16:19:40,887 - __main__ - INFO - From: BPNL000000000001
2026-02-02 16:19:40,887 - __main__ - INFO - To: BPNL000000000002
============================================================
2026-02-02 16:19:40,887 - __main__ - INFO - Sending notification...
============================================================
2026-02-02 16:19:51,255 - __main__ - INFO - Obtained notification endpoint: https://...
2026-02-02 16:19:51,761 - __main__ - INFO - Successfully sent notification cdad3da4-c9ba-4e98-9075-319f37367ef7
============================================================
2026-02-02 16:19:51,761 - __main__ - INFO - Notification sent successfully!
============================================================
```

---

## Advanced Usage

### Caching Endpoints for Multiple Notifications

If you need to send multiple notifications to the same provider, you can cache the endpoint and token:

```python
# Get endpoint once
endpoint_url, access_token = notification_service.get_notification_endpoint(
    provider_bpn=provider_bpn,
    provider_dsp_url=provider_dsp_url,
    policies=policies_to_accept,
)

# Send multiple notifications using cached credentials
for i in range(10):
    notification = (
        Notification.builder()
        .sender_bpn(sender_bpn)
        .receiver_bpn(provider_bpn)
        .context("IndustryCore-DigitalTwinEventAPI-ConnectToParent:3.0.0")
        .information(f"Notification {i + 1}")
        .build()
    )
    
    result = notification_service.send_notification_to_endpoint(
        endpoint_url=endpoint_url,
        access_token=access_token,
        notification=notification,
    )
```

### Discovering Available Notification Assets

Before sending, you can discover what notification assets a provider offers:

```python
assets = notification_service.discover_notification_assets(
    provider_bpn=provider_bpn,
    provider_dsp_url=provider_dsp_url,
    policies=policies_to_accept,
)

for asset in assets:
    print(f"Found notification asset: {asset.get('@id')}")
```

### Custom Notification Content

The notification model supports additional fields:

```python
notification = (
    Notification.builder()
    .sender_bpn(sender_bpn)
    .receiver_bpn(provider_bpn)
    .context("IndustryCore-DigitalTwinEventAPI-ConnectToParent:3.0.0")
    .information("Quality alert detected")
    .affected_items([
        "urn:uuid:part-001",
        "urn:uuid:part-002",
    ])
    .related_message_id("previous-message-uuid")  # For reply chains
    .build()
)
```

---

## Troubleshooting

### Common Errors

??? question "502 Bad Gateway"
    
    **Problem**: `ConnectionError: It was not possible to get the catalog from the EDC provider! Response code: [502]`
    
    **Solutions**:
    
    - Verify the DSP endpoint URL is correct (try `/api/v1/dsp` or `/api/dsp`)
    - Check network connectivity between connectors
    - Ensure the provider connector is running

??? question "No policies are allowed for the DCAT Catalog"
    
    **Problem**: `No policies are allowed for the DCAT Catalog!`
    
    **Solutions**:
    
    - Add the `policies_to_accept` parameter matching the provider's policy
    - Check that your policy structure matches the ODRL format

??? question "No dataset was found for the search asset"
    
    **Problem**: `No dataset was found for the search asset! It is empty!`
    
    **Solutions**:
    
    - Ensure the provider has created the asset, policy, AND contract definition
    - Verify the asset type is `https://w3id.org/catenax/taxonomy#DigitalTwinEventAPI`
    - Check that the contract definition references the correct asset ID

??? question "415 Unsupported Media Type"
    
    **Problem**: `Status code: 415`
    
    **Solutions**:
    
    - Add `"Content-Type": "application/json"` to your headers

---

## Complete Example Scripts

The complete example scripts are available in the SDK repository:

- [create_notification_asset.py](https://github.com/eclipse-tractusx/tractusx-sdk/blob/main/examples/extensions/notification_api/create_notification_asset.py)
- [send_notification.py](https://github.com/eclipse-tractusx/tractusx-sdk/blob/main/examples/extensions/notification_api/send_notification.py)

---

## Next Steps

- **📚 API Reference**: Learn more about the [Notification API Extension](../api-reference/extension-library/notification-api.md)
- **🔧 Dataspace Services**: Explore [connector services](../api-reference/dataspace-library/connector/services.md)
- **📖 Industry Core**: Understand [notification schemas](../core-concepts/industry-concepts/notifications.md)

---

## NOTICE

This work is licensed under the [CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/legalcode).

- SPDX-License-Identifier: CC-BY-4.0
- SPDX-FileCopyrightText: 2026 Contributors to the Eclipse Foundation
- SPDX-FileCopyrightText: 2026 LKS Next
- Source URL: https://github.com/eclipse-tractusx/tractusx-sdk
