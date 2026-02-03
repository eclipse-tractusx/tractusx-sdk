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
Example: Create a Notification Asset in the EDC Connector

This script demonstrates how to create a DigitalTwinEventAPI asset
in your EDC connector to receive notifications from other participants.

It creates the complete setup:
    1. Asset - The notification endpoint
    2. Policy - Access control policy (default: allow all BPNs)
    3. Contract Definition - Links asset to policy for discovery

Prerequisites:
    - A running EDC connector with management API access
    - A notification endpoint URL where you want to receive notifications

Usage:
    python create_notification_asset.py
"""

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


def main():
    """Create a notification asset in the EDC connector."""
    
    # ==========================================================================
    # Configuration - Update these values for your environment
    # ==========================================================================
    
    # Your connector settings (provider side)
    connector_base_url = "https://your-connector-controlplane.example.com"
    connector_dma_path = "/management"
    connector_api_key = "your-api-key"
    dataspace_version = "jupiter"  # Available: "jupiter"
    
    # Notification asset settings
    asset_id = "notification-asset-001"
    policy_id = "notification-policy-001"
    contract_id = "notification-contract-001"
    notification_endpoint = "https://your-backend.example.com/api/notifications"
    
    # ==========================================================================
    # Create the connector provider service
    # ==========================================================================
    
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
    
    # ==========================================================================
    # Create the notification service
    # ==========================================================================
    
    logger.info("Creating notification service...")
    
    notification_service = NotificationService(
        connector_provider=connector_provider,
        verbose=True,
        logger=logger,
    )
    
    # ==========================================================================
    # Create the notification asset
    # ==========================================================================
    
    try:
        logger.info(f"Creating notification asset '{asset_id}'...")
        
        result = notification_service.ensure_notification_asset_exists(
            asset_id=asset_id,
            notification_endpoint_url=notification_endpoint,
            version="3.0",
            # Optional: Add proxy parameters if your backend needs them
            # proxy_params={"method": "true", "pathSegments": "true"},
            # Optional: Add headers for backend authentication
            # headers={"Authorization": "Bearer your-backend-token"},
            # Optional: Add private properties
            # private_properties={"internal-id": "my-internal-ref"},
        )
        
        logger.info(f"Asset created: {result.get('@id', asset_id)}")
        
        # ======================================================================
        # Create the policy (allow all BPNs)
        # ======================================================================
        
        logger.info(f"Creating policy '{policy_id}'...")
        
        # Default policy: allow any participant to use the asset
        # For production, you should add constraints (e.g., specific BPNs)
        policy_result = connector_provider.create_policy(
            policy_id=policy_id,
            permissions=[
                {
                    "action": "odrl:use",
                }
            ],
        )
        
        logger.info(f"Policy created: {policy_result.get('@id', policy_id)}")
        
        # ======================================================================
        # Create the contract definition
        # ======================================================================
        
        logger.info(f"Creating contract definition '{contract_id}'...")
        
        contract_result = connector_provider.create_contract(
            contract_id=contract_id,
            usage_policy_id=policy_id,
            access_policy_id=policy_id,
            asset_id=asset_id,
        )
        
        logger.info(f"Contract created: {contract_result.get('@id', contract_id)}")
        
        # ======================================================================
        # Summary
        # ======================================================================
        
        logger.info("=" * 60)
        logger.info("Notification endpoint setup complete!")
        logger.info("=" * 60)
        logger.info(f"Asset ID:    {asset_id}")
        logger.info(f"Policy ID:   {policy_id}")
        logger.info(f"Contract ID: {contract_id}")
        logger.info("Asset Type:  cx-taxo:DigitalTwinEventAPI")
        logger.info(f"Endpoint:    {notification_endpoint}")
        logger.info("=" * 60)
        logger.info("Other participants can now discover and send notifications!")
        logger.info("=" * 60)
        
        return {
            "asset": result,
            "policy": policy_result,
            "contract": contract_result,
        }
        
    except NotificationError as e:
        logger.error(f"Failed to create notification asset: {e}")
        raise
    except ValueError as e:
        logger.error(f"Failed to create policy or contract: {e}")
        raise


if __name__ == "__main__":
    main()
