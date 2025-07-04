#################################################################################
# Eclipse Tractus-X - Software Development KIT
#
# Copyright (c) 2025 CGI Deutschland B.V. & Co. KG
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

import time

from requests import Response

from tractusx_sdk.dataspace.tools.http_tools import HttpTools

from tractusx_sdk.dataspace.managers import OAuth2Manager
from tractusx_sdk.dataspace.services.discovery import DiscoveryFinderService

      
class BpnDiscoveryService:
    
    oauth:OAuth2Manager
    bpn_discoveries:dict
    bpn_discovery_key:str
    discovery_finder_url:str
    cache_timeout_seconds:int
    
    def __init__(self, oauth:OAuth2Manager, discovery_finder_url:str, cache_timeout_seconds:int = 60 * 60 * 12):
        self.discovery_finder_url = discovery_finder_url
        self.oauth = oauth
        self.bpn_discoveries = {}
        self.cache_timeout_seconds = cache_timeout_seconds # Default 12 hours

    def get_connector_discovery_url(self, oauth:OAuth2Manager, discovery_finder_url:str, bpn_discovery_key:str="manufacturerPartId"):
        """
        Fetches the discovery URL for a given BPN identifier type.

        Args:
            oauth (OAuth2Manager): The OAuth2 manager for authentication.
            discovery_finder_url (str): The URL for the discovery finder service.
            bpn_discovery_key (str): The key used to identify the discovery type (default: "manufacturerPartId").

        Returns:
            str: The connector discovery URL for the given identifier type.

        Raises:
            Exception: If no discovery endpoint is found for the given key.
        """
        endpoints = DiscoveryFinderService.find_discovery_urls(url=discovery_finder_url, oauth=oauth, keys=[bpn_discovery_key])
        if(bpn_discovery_key not in endpoints):
          raise Exception("[Connector Discovery Service] Connector Discovery endpoint not found!")

        self.bpn_discovery_url = endpoints[bpn_discovery_key]

        return self.bpn_discovery_url

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
        discovery_url = self._get_or_update_discovery_url(bpn_discovery_key=identifier_type)

        body:dict = {
            "searchFilter": [
                {
                    "type": identifier_type,
                    "keys": keys
                }
            ]
        }
        
        headers:dict = self.oauth.add_auth_header(headers={'Content-Type' : 'application/json'})

        response = HttpTools.do_post(url=discovery_url, headers=headers, json=body)
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
        bpns = [item["value"] for item in bpns_data if "value" in item]
        return list(set(bpns)) if bpns else None
    
    def _get_or_update_discovery_url(self, bpn_discovery_key:str) -> str:
        """
        Retrieves a cached discovery URL or updates the cache if expired.

        Args:
            bpn_discovery_key (str): The identifier key for the discovery type.

        Returns:
            str: A valid discovery URL.
        """
        current_time = time.time()
        entry:dict = self.bpn_discoveries.get(bpn_discovery_key)
        # Check if the entry exists and if it is still valid
        if (
            not entry or
            (current_time - entry.get("timestamp", 0)) > self.cache_timeout_seconds
        ):
            url = self.get_connector_discovery_url(
                oauth=self.oauth,
                discovery_finder_url=self.discovery_finder_url,
                bpn_discovery_key=bpn_discovery_key
            )
            self.bpn_discoveries[bpn_discovery_key] = {
                "url": url,
                "timestamp": current_time
            }
            
        return self.bpn_discoveries[bpn_discovery_key]["url"]

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

        response = HttpTools.do_post(url=discovery_url, headers=headers, json=body)
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

        response = HttpTools.do_post(url=discovery_url, headers=headers, json=body)
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

        response = HttpTools.do_delete(url=discovery_url, headers=headers)
        if response is None:
            raise Exception("[BPN Discovery Service] No response received from the connector discovery service.")
        if response.status_code == 401:
            raise Exception("[BPN Discovery Service] Unauthorized access. Please check your clientid permissions.")
        if response.status_code != 204:
            raise Exception(f"[BPN Discovery Service] Failed to delete BPN identifier with resourceId {resource_id}.")