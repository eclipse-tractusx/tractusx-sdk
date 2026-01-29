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

from requests import Response

from ...tools.http_tools import HttpTools
from ...managers import OAuth2Manager

class DiscoveryFinderService:
    
    def __init__(self, url:str, oauth:OAuth2Manager, types_key:str="types", endpoints_key:str="endpoints", 
                 endpoint_address_key:str="endpointAddress", return_type_key:str='type', verbose:bool=False):
        """
        Initialize the Discovery Finder Service with URL, OAuth, and configurable response keys.
        
        Args:
            url (str): The discovery finder URL.
            oauth (OAuth2Manager): OAuth2 manager for authentication.
            types_key (str): Key for types in discovery request (default: "types").
            endpoints_key (str): Key for endpoints in discovery response (default: "endpoints").
            endpoint_address_key (str): Key for endpoint address in discovery response (default: "endpointAddress").
            return_type_key (str): Key for return type in discovery response (default: "type").
            verbose (bool): Enable verbose debug logging (default: False).
        """
        self.url = url
        self.oauth = oauth
        self.types_key = types_key
        self.endpoints_key = endpoints_key
        self.endpoint_address_key = endpoint_address_key
        self.return_type_key = return_type_key
        self.verbose = verbose

    def find_discovery_urls(self, keys:list=["bpn"]) -> dict:
        """
        Allows you to find a discovery service urls by key.
        
        Args:
            keys (list): List of keys to search for (default: ["bpn"]).
            
        Returns:
            dict: Dictionary mapping discovery types to their endpoint URLs.
        """

        ## Check if IAM is connected
        if(not self.oauth.connected):
            raise ConnectionError("[Discovery Finder] The authentication service is not connected! Please execute the oauth.connect() method")
        
        ## Setup headers and body
        headers:dict = self.oauth.add_auth_header(headers={'Content-Type' : 'application/json'})
        body:dict = {
            self.types_key: keys
        }

        response:Response = HttpTools.do_post(url=self.url, headers=headers, json=body)
        ## In case the response code is not successfull or the response is null
        if(response is None or response.status_code != 200):
            status_code = response.status_code if response else 'None'
            error_msg = f"[Discovery Finder] Failed to get discovery service! Status: {status_code}"
            if self.verbose and response is not None:
                error_msg += f"\nURL: {self.url}"
                error_msg += f"\nRequest body: {body}"
                error_msg += f"\nResponse headers: {dict(response.headers)}"
                error_msg += f"\nResponse body: {response.text}"
            raise Exception(error_msg)
        
        data = response.json()

        if(not(self.endpoints_key in data) or len(data[self.endpoints_key]) == 0):
            raise Exception("[Discovery Finder] No endpoints were found in the discovery service for this keys!")

        # Map to every key the endpoint address
        return dict(map(lambda x: (x[self.return_type_key], x[self.endpoint_address_key]), data[self.endpoints_key]))
