#################################################################################
# Eclipse Tractus-X - Software Development KIT
#
# Copyright (c) 2026 LKS Next
# Copyright (c) 2026 Contributors to the Eclipse Foundation
#
# See the NOTICE file(s) distributed with this work for additional
# information regarding copyright ownership.
#
# This program and the accompanying materials are made available under the
# terms of the Apache License, Version 2.0 which is available at
# https://www.apache.org/licenses/LICENSE-2.0.
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND,
# either express or implied. See the
# License for the specific language govern in permissions and limitations
# under the License.
#
# SPDX-License-Identifier: Apache-2.0
#################################################################################

## Code created partially using a LLM and reviewed by a human committer

"""
Example: Send a Notification through the Dataspace

This script demonstrates how to send a notification to another participant
through the Catena-X dataspace using the EDC connector.

Prerequisites:
    - A running EDC connector with management API access
    - The provider's BPN and DSP endpoint URL
    - The provider must have a DigitalTwinEventAPI asset registered

Usage:
    python send_notification.py
"""

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


def main():
    """Send a notification through the dataspace."""
    
    # ==========================================================================
    # Configuration - Update these values for your environment
    # ==========================================================================
    
    # Your connector settings (consumer side)
    connector_base_url = "https://your-connector-controlplane.example.com"
    connector_dma_path = "/management"
    connector_api_key = "your-api-key"
    dataspace_version = "jupiter"  # Available: "jupiter"
    
    # Your BPN (sender)
    sender_bpn = "BPNL000000000001"
    
    # Provider/Receiver settings
    provider_bpn = "BPNL000000000002"
    provider_dsp_url = "https://provider-connector.example.com/api/v1/dsp"
    
    # ==========================================================================
    # Create the connector consumer service
    # ==========================================================================
    
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
    
    # ==========================================================================
    # Create the notification consumer service
    # ==========================================================================
    
    logger.info("Creating notification consumer service...")
    
    notification_service = NotificationConsumerService(
        connector_consumer=connector_consumer,
        verbose=True,
        logger=logger,
    )
    
    # ==========================================================================
    # Define acceptable policies
    # ==========================================================================
    
    # This must match the policy offered by the provider
    # The provider created a simple "odrl:use" policy
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
    
    # ==========================================================================
    # Build the notification
    # ==========================================================================
    
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
    
    # ==========================================================================
    # Send the notification
    # ==========================================================================
    
    try:
        logger.info("=" * 60)
        logger.info("Sending notification...")
        logger.info("=" * 60)
        
        # Option 1: Send directly (full DSP flow)
        result = notification_service.send_notification(
            provider_bpn=provider_bpn,
            provider_dsp_url=provider_dsp_url,
            notification=notification,
            policies=policies_to_accept,
            timeout=60,
        )
        
        logger.info("=" * 60)
        logger.info("Notification sent successfully!")
        logger.info("=" * 60)
        logger.info(f"Response: {result}")
        
        return result
        
    except NotificationValidationError as e:
        logger.error(f"Notification validation failed: {e}")
        raise
    except NotificationError as e:
        logger.error(f"Failed to send notification: {e}")
        raise


def send_with_manual_endpoint():
    """
    Alternative: Send to a pre-obtained endpoint.
    
    Use this approach when you want to cache the endpoint/token
    for multiple notifications to the same provider.
    """
    
    # Configuration
    connector_base_url = "https://your-connector.com"
    connector_dma_path = "/management"  # Base path (version is added automatically)
    connector_api_key = "your-api-key"
    dataspace_version = "jupiter"  # Available: "jupiter"
    sender_bpn = "BPNL000000000001"
    provider_bpn = "BPNL000000000002"
    provider_dsp_url = "https://provider-connector.com/api/dsp"
    
    # Create services
    connector_consumer = BaseConnectorConsumerService(
        dataspace_version=dataspace_version,
        base_url=connector_base_url,
        dma_path=connector_dma_path,
        headers={
            "x-api-key": connector_api_key,
            "Content-Type": "application/json",
        },
        verbose=True,
    )
    
    notification_service = NotificationConsumerService(
        connector_consumer=connector_consumer,
        verbose=True,
    )
    
    # Step 1: Get the endpoint and token (can be cached)
    logger.info("Getting notification endpoint...")
    endpoint_url, access_token = notification_service.get_notification_endpoint(
        provider_bpn=provider_bpn,
        provider_dsp_url=provider_dsp_url,
    )
    logger.info(f"Endpoint: {endpoint_url}")
    
    # Step 2: Build and send multiple notifications using the cached endpoint
    for i in range(3):
        notification = (
            Notification.builder()
            .sender_bpn(sender_bpn)
            .receiver_bpn(provider_bpn)
            .context("IndustryCore-DigitalTwinEventAPI-ConnectToParent:3.0.0")
            .information(f"Notification {i + 1} of 3")
            .build()
        )
        
        result = notification_service.send_notification_to_endpoint(
            endpoint_url=endpoint_url,
            access_token=access_token,
            notification=notification,
        )
        
        logger.info(f"Sent notification {i + 1}: {notification.header.message_id}")


def discover_and_inspect():
    """
    Alternative: Discover notification assets before sending.
    
    Use this approach when you want to inspect available assets
    or handle providers with multiple notification endpoints.
    """
    
    # Configuration
    connector_base_url = "https://your-connector.com"
    connector_dma_path = "/management"  # Base path (version is added automatically)
    connector_api_key = "your-api-key"
    dataspace_version = "jupiter"  # Available: "jupiter"
    provider_bpn = "BPNL000000000002"
    provider_dsp_url = "https://provider-connector.com/api/dsp"
    
    # Create services
    connector_consumer = BaseConnectorConsumerService(
        dataspace_version=dataspace_version,
        base_url=connector_base_url,
        dma_path=connector_dma_path,
        headers={
            "x-api-key": connector_api_key,
            "Content-Type": "application/json",
        },
        verbose=True,
    )
    
    notification_service = NotificationConsumerService(
        connector_consumer=connector_consumer,
        verbose=True,
    )
    
    # Discover available notification assets
    logger.info("Discovering notification assets...")
    assets = notification_service.discover_notification_assets(
        provider_bpn=provider_bpn,
        provider_dsp_url=provider_dsp_url,
    )
    
    logger.info(f"Found {len(assets)} notification asset(s):")
    for asset in assets:
        logger.info(f"  - {asset.get('@id', 'unknown')}")


if __name__ == "__main__":
    main()
    
    # Uncomment to run alternative examples:
    # send_with_manual_endpoint()
    # discover_and_inspect()
