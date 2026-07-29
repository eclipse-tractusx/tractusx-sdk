#################################################################################
# Eclipse Tractus-X - Software Development KIT
#
# Copyright (c) 2025 Contributors to the Eclipse Foundation
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
import logging
from typing import Optional

from ...tools.http_tools import HttpTools
from ...managers import OAuth2Manager
from .base_discovery_service import BaseDiscoveryService
from .discovery_finder_service import DiscoveryFinderService

class ConnectorDiscoveryService(BaseDiscoveryService):
    
    connector_discovery_key:str
    oauth:OAuth2Manager
    
    def __init__(self, oauth:OAuth2Manager, discovery_finder_service:DiscoveryFinderService, connector_discovery_key:str="bpn", 
                 cache_timeout_seconds:int = 60 * 60 * 12, verbose:bool=False, logger:Optional[logging.Logger]=None):
        """
        Initialize the Connector Discovery Service with caching functionality.
        
        Args:
            discovery_finder_service (DiscoveryFinderService): Discovery finder service instance for finding discovery URLs.
            connector_discovery_key (str): Key for connector discovery (default: "bpn").
            cache_timeout_seconds (int): Cache timeout in seconds (default: 12 hours).
            verbose (bool): Enable verbose logging (default: False).
            logger (Optional[logging.Logger]): Logger instance for logging (default: None).
        """
        self.oauth=oauth
        super().__init__(
            oauth=oauth,
            discovery_finder_service=discovery_finder_service,
            cache_timeout_seconds=cache_timeout_seconds,
            verbose=verbose,
            logger=logger
        )
        self.connector_discovery_key = connector_discovery_key

    def get_service_name(self) -> str:
        """Returns the service name for logging purposes."""
        return "Connector Discovery Service"

    def get_discovery_url(self, discovery_finder_service:DiscoveryFinderService, discovery_key:str) -> str:
        """
        Fetches the discovery URL for connector discovery.

        Args:
            discovery_finder_service (DiscoveryFinderService): Discovery finder service instance.
            discovery_key (str): Key for connector discovery.

        Returns:
            str: The connector discovery URL.

        Raises:
            Exception: If no discovery endpoint is found for the given key.
        """
        if self.verbose:
            self.logger.info(f"Fetching discovery URL for key: {discovery_key}")
        
        endpoints = discovery_finder_service.find_discovery_urls(keys=[discovery_key])
        if(discovery_key not in endpoints):
            error_msg = f"[Connector Discovery Service] Connector Discovery endpoint not found for key: {discovery_key}"
            if self.verbose:
                error_msg += f"\nAvailable endpoints: {list(endpoints.keys())}"
            raise Exception(error_msg)
        
        if self.verbose:
            self.logger.info(f"Discovery URL found: {endpoints[discovery_key]}")
        
        return endpoints[discovery_key]

    def get_connector_discovery_url(self, connector_discovery_key:str="bpn") -> str:
        """
        Legacy method for backward compatibility. Use get_discovery_url instead.
        """
        return self.get_discovery_url(self.discovery_finder_service, connector_discovery_key)

    def _get_or_update_discovery_url(self, connector_discovery_key:str=None) -> str:
        """
        Wrapper method for backward compatibility.
        
        Args:
            connector_discovery_key (str): The identifier key for the discovery type.
                                          If None, uses the instance's default key.

        Returns:
            str: A valid discovery URL.
        """
        if connector_discovery_key is None:
            connector_discovery_key = self.connector_discovery_key
        
        return super()._get_or_update_discovery_url(connector_discovery_key)

    def invalidate_cache_entry(self, connector_discovery_key: str = None) -> bool:
        """
        Invalidates a specific cache entry for a connector discovery key.
        
        Args:
            connector_discovery_key (str): The discovery key to invalidate. 
                                          If None, uses the instance's default key.
        
        Returns:
            bool: True if the entry was found and removed, False if it didn't exist.
        """
        if connector_discovery_key is None:
            connector_discovery_key = self.connector_discovery_key
        
        return super().invalidate_cache_entry(connector_discovery_key)

    def find_connector_by_bpn(self, bpn:str, bpn_key:str="bpn", connector_endpoint_key:str="connectorEndpoint") -> list | None:
        """
        Finds connector endpoints for a given BPN using the cached discovery URL.

        Args:
            bpn (str): The Business Partner Number to search for.
            bpn_key (str): The key for BPN in the response (default: "bpn").
            connector_endpoint_key (str): The key for connector endpoints in the response (default: "connectorEndpoint").

        Returns:
            list | None: List of connector endpoints for the BPN, or None if not found.

        Raises:
            Exception: If the connector discovery service request fails.
        """
        # Use cached discovery URL, refresh if necessary
        discovery_url = self._get_or_update_discovery_url()
        
        if self.verbose:
            self.logger.info(f"Finding connector for BPN: {bpn} using URL: {discovery_url}")

        body:list = [
            bpn
        ]
        
        headers:dict = self.oauth.add_auth_header(headers={'Content-Type' : 'application/json'})

        response = HttpTools.do_post(url=discovery_url, headers=headers, json=body)
        if(response is None or response.status_code != 200):
            status_code = response.status_code if response else 'None'
            error_msg = f"[Connector Discovery Service] Failed to get connector URLs! Status: {status_code}"
            if self.verbose and response is not None:
                error_msg += f"\nURL: {discovery_url}"
                error_msg += f"\nRequest body: {body}"
                error_msg += f"\nResponse headers: {dict(response.headers)}"
                error_msg += f"\nResponse body: {response.text}"
            raise Exception(error_msg)
        
        json_response:dict = response.json()
        
        if self.verbose:
            self.logger.info(f"Received {len(json_response)} connector entries")

        # Iterate over the json_response to find the connectorEndpoint for the specified BPN
        for item in json_response:
            if item.get(bpn_key) == bpn:
                endpoints = item.get(connector_endpoint_key, [])
                if self.verbose:
                    self.logger.info(f"Found {len(endpoints)} endpoint(s) for BPN {bpn}")
                return endpoints
        
        # If the BPN is not found, return None or an empty list
        if self.verbose:
            self.logger.warning(f"No connector endpoints found for BPN: {bpn}")
        return None