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

from tractusx_sdk.dataspace.tools.http_tools import HttpTools
from tractusx_sdk.dataspace.managers import OAuth2Manager
from tractusx_sdk.dataspace.services.discovery import DiscoveryFinderService
from tractusx_sdk.dataspace.services.discovery.base_discovery_service import BaseDiscoveryService
from tractusx_sdk.dataspace.tools.operators import op
import requests

class BpnDiscoveryService(BaseDiscoveryService):
    session:requests.Session
    base_path:str
    oauth:OAuth2Manager
    def __init__(self, oauth:OAuth2Manager, discovery_finder_service: DiscoveryFinderService, cache_timeout_seconds:int = 60 * 60 * 12,
                 session:requests.Session = None, base_path:str="/api/v1.0/administration/connectors/bpnDiscovery",
                 debug:bool=False, logger:Optional[logging.Logger]=None):
        """
        Initialize the BPN Discovery Service.
        
        Args:
            discovery_finder_service: DiscoveryFinderService instance for finding discovery URLs.
            cache_timeout_seconds (int): Cache timeout in seconds (default: 12 hours).
            session (requests.Session): HTTP session for connection reuse.
            base_path (str): API path to append to the base URL from discovery finder (default: "/api/v1.0/administration/connectors/bpnDiscovery").
            debug (bool): Enable debug logging with request/response bodies (default: False).
            logger (Optional[logging.Logger]): Logger instance for logging (default: None).
        """
        self.oauth = oauth
        super().__init__(
            oauth=oauth,
            discovery_finder_service=discovery_finder_service,
            cache_timeout_seconds=cache_timeout_seconds,
            debug=debug,
            logger=logger
        )
        self.session = session
        self.base_path = base_path
        if(not self.session):
            self.session = requests.Session()

    def get_service_name(self) -> str:
        """Returns the service name for logging purposes."""
        return "BPN Discovery Service"

    def get_discovery_url(self, discovery_finder_service: DiscoveryFinderService, discovery_key:str) -> str:
        """
        Fetches the discovery URL for a given BPN identifier type.

        Args:
            discovery_finder_service: DiscoveryFinderService instance for finding discovery URLs.
            discovery_key (str): The key used to identify the discovery type.

        Returns:
            str: The BPN discovery URL for the given identifier type.

        Raises:
            Exception: If no discovery endpoint is found for the given key.
        """
        endpoints = discovery_finder_service.find_discovery_urls(keys=[discovery_key])
        if(discovery_key not in endpoints):
          raise Exception("[BPN Discovery Service] BPN Discovery endpoint not found!")

        base_url:str = endpoints[discovery_key]
        
        # Remove trailing slash from base_url if present
        base_url = base_url.rstrip('/')
        # Remove leading slash from base_path if present  
        path = self.base_path.lstrip('/')
        
        if(not base_url.endswith(path)):
        # Construct the full URL
            full_url = f"{base_url}/{path}"
        else:
            full_url = base_url
        
        return full_url

    def get_bpn_discovery_url(self, bpn_discovery_key:str="manufacturerPartId"):
        """
        Legacy method for backward compatibility. Use get_discovery_url instead.
        """
        return self.get_discovery_url(self.discovery_finder_service, bpn_discovery_key)

    def search_bpns(self, keys:list, identifier_type:str="manufacturerPartId") -> list | None:
        """
        Sends a search request to the BPN discovery service.

        Args:
            keys (list): List of identifier keys to search.
            identifier_type (str): The type of the identifier (default: "manufacturerPartId").

        Returns:
            dict: The raw JSON response from the BPN discovery service.

        Raises:
            Exception: If the request fails or returns a non-200 response.
        """
        discovery_url:str = self._get_or_update_discovery_url(bpn_discovery_key=identifier_type)

        if(not discovery_url.endswith("/search")):
            discovery_url += "/search"

        body:dict = {
            "searchFilter": [
                {
                    "type": identifier_type,
                    "keys": keys
                }
            ]
        }
        
        headers:dict = self.oauth.add_auth_header(headers={'Content-Type' : 'application/json'})

        response = HttpTools.do_post_with_session(url=discovery_url, headers=headers, json=body, session=self.session)
        if response is None:
            raise Exception("[BPN Discovery Service] No response received from the connector discovery service.")
        if response.status_code == 401:
            raise Exception("[BPN Discovery Service] Unauthorized access. Please check your clientid permissions.")
        if response.status_code != 200:
            raise Exception("[BPN Discovery Service] It was not possible to get the connector urls because the connector discovery service response was not successful!")

        return response.json()

    def search_bpns_multi_type(self, search_filters:list) -> dict:
        """
        Sends a search request to the BPN discovery service with multiple identifier types and keys.

        Args:
            search_filters (list): List of search filter dictionaries, each containing:
                - type (str): The identifier type (e.g., "manufacturerPartId", "batchId", "serialNumber")
                - keys (list): List of identifier keys for this type

        Example:
            search_filters = [
                {"type": "manufacturerPartId", "keys": ["part-123", "part-456"]},
                {"type": "batchId", "keys": ["batch-001", "batch-002"]},
                {"type": "serialNumber", "keys": ["SN-789", "SN-012"]}
            ]

        Returns:
            dict: The raw JSON response from the BPN discovery service.

        Raises:
            Exception: If the request fails or returns a non-200 response.
        """
        if not search_filters or not isinstance(search_filters, list):
            raise ValueError("search_filters must be a non-empty list of filter dictionaries")
        
        # Validate search filters format
        for filter_item in search_filters:
            if not isinstance(filter_item, dict) or "type" not in filter_item or "keys" not in filter_item:
                raise ValueError("Each search filter must be a dictionary with 'type' and 'keys' fields")
            if not isinstance(filter_item["keys"], list) or not filter_item["keys"]:
                raise ValueError("Each search filter must have a non-empty 'keys' list")
        
        # Use the first identifier type to get the discovery URL
        # (assuming all types use the same discovery endpoint)
        primary_type = search_filters[0]["type"]
        discovery_url = self._get_or_update_discovery_url(bpn_discovery_key=primary_type)

        body:dict = {
            "searchFilter": search_filters
        }
        
        headers:dict = self.oauth.add_auth_header(headers={'Content-Type' : 'application/json'})

        response = HttpTools.do_post_with_session(url=discovery_url, headers=headers, json=body, session=self.session)
        if response is None:
            raise Exception("[BPN Discovery Service] No response received from the connector discovery service.")
        if response.status_code == 401:
            raise Exception("[BPN Discovery Service] Unauthorized access. Please check your clientid permissions.")
        if response.status_code != 200:
            raise Exception("[BPN Discovery Service] It was not possible to get the connector urls because the connector discovery service response was not successful!")

        return response.json()

    def find_bpns(self, keys:list, identifier_type:str="manufacturerPartId") -> list | None:
        """
        Finds and returns a list of unique BPNs corresponding to given identifier keys.

        Args:
            keys (list): List of identifier keys to resolve to BPNs.
            identifier_type (str): The type of the identifier (default: "manufacturerPartId").

        Returns:
            list | None: A list of unique BPNs or None if none found.
        """
        json_response:dict = self.search_bpns(keys=keys, identifier_type=identifier_type)
        bpns_data = json_response.get("bpns", [])
        bpns = op.extract_dict_values(array=bpns_data, key="value")
        return list(set(bpns)) if bpns else None

    def find_bpns_multi_type(self, search_filters:list) -> list | None:
        """
        Finds and returns a list of unique BPNs corresponding to multiple identifier types and keys.

        Args:
            search_filters (list): List of search filter dictionaries, each containing:
                - type (str): The identifier type (e.g., "manufacturerPartId", "batchId", "serialNumber")
                - keys (list): List of identifier keys for this type

        Example:
            search_filters = [
                {"type": "manufacturerPartId", "keys": ["part-123", "part-456"]},
                {"type": "batchId", "keys": ["batch-001", "batch-002"]}
            ]

        Returns:
            list | None: A list of unique BPNs or None if none found.
        """
        json_response:dict = self.search_bpns_multi_type(search_filters=search_filters)
        bpns_data = json_response.get("bpns", [])
        bpns = op.extract_dict_values(array=bpns_data, key="value")
        return list(set(bpns)) if bpns else None
    
    def _get_or_update_discovery_url(self, bpn_discovery_key:str="manufacturerPartId") -> str:
        """
        Wrapper method for backward compatibility.
        
        Args:
            bpn_discovery_key (str): The identifier key for the discovery type.

        Returns:
            str: A valid discovery URL.
        """
        return super()._get_or_update_discovery_url(bpn_discovery_key)

    def set_identifier(self, identifier_key: str, identifier_type:str="manufacturerPartId") -> dict:
        """
        Registers a new identifier to the authenticated user's BPN.

        Args:
            identifier_key (str): The identifier key to be associated.
            identifier_type (str): The type of identifier (default: "manufacturerPartId").

        Returns:
            dict: The response JSON with BPN association details.

        Raises:
            Exception: If creation fails.
        """
        discovery_url = self._get_or_update_discovery_url(bpn_discovery_key=identifier_type)
        headers: dict = self.oauth.add_auth_header(headers={'Content-Type': 'application/json'})
        body = {
            "type": identifier_type,
            "key": identifier_key
        }

        response = HttpTools.do_post_with_session(url=discovery_url, headers=headers, json=body, session=self.session)
        if response is None:
            raise Exception("[BPN Discovery Service] No response received from the connector discovery service.")
        if response.status_code == 401:
            raise Exception("[BPN Discovery Service] Unauthorized access. Please check your clientid permissions.")
        if response.status_code != 201:
            raise Exception("[BPN Discovery Service] Failed to create BPN identifier.")

        return response.json()

    def set_multiple_identifiers(self, identifiers: list, identifier_type:str="manufacturerPartId") -> list:
        """
        Registers multiple identifiers in a batch to the authenticated user's BPN.

        Args:
            identifiers (list): A list of identifier keys.
            identifier_type (str): The type of identifier (default: "manufacturerPartId").

        Returns:
            list: A list of responses for each identifier.

        Raises:
            Exception: If the batch creation fails.
        """
        body = [{"type": identifier_type, "key": key} for key in identifiers]

        discovery_url = self._get_or_update_discovery_url(bpn_discovery_key=identifier_type) + "/batch"
        headers: dict = self.oauth.add_auth_header(headers={'Content-Type': 'application/json'})

        response = HttpTools.do_post_with_session(url=discovery_url, headers=headers, json=body, session=self.session)
        if response is None:
            raise Exception("[BPN Discovery Service] No response received from the connector discovery service.")
        if response.status_code == 401:
            raise Exception("[BPN Discovery Service] Unauthorized access. Please check your clientid permissions.")
        if response.status_code != 201:
            raise Exception("[BPN Discovery Service] Failed to create BPN identifiers batch.")

        return response.json()

    def delete_bpn_identifier_by_id(self, resource_id: str, identifier_type:str="manufacturerPartId") -> None:
        """
        Deletes an existing BPN identifier association by its resource ID.

        Args:
            resource_id (str): The resource ID of the identifier association.
            identifier_type (str): The type of identifier (default: "manufacturerPartId").

        Raises:
            Exception: If the deletion fails.
        """
        discovery_url = self._get_or_update_discovery_url(bpn_discovery_key=identifier_type) + f"/{resource_id}"
        headers: dict = self.oauth.add_auth_header(headers={'Content-Type': 'application/json'})

        response = HttpTools.do_delete_with_session(url=discovery_url, headers=headers, session=self.session)
        if response is None:
            raise Exception("[BPN Discovery Service] No response received from the connector discovery service.")
        if response.status_code == 401:
            raise Exception("[BPN Discovery Service] Unauthorized access. Please check your clientid permissions.")
        if response.status_code != 204:
            raise Exception(f"[BPN Discovery Service] Failed to delete BPN identifier with resourceId {resource_id}.")