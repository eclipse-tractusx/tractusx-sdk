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

from requests import Response

from ...tools.http_tools import HttpTools
from ...managers import OAuth2Manager

class DiscoveryFinderService:

    @staticmethod
    def find_discovery_urls(url:str,  oauth:OAuth2Manager, keys:list=["bpn"], types_key:str="types", endpoints_key:str="endpoints", endpoint_addresses_key:str="endpointAddresses", return_type_key:str='type') -> str | None:
        """
          Allows you to find a discovery service urls by key
        """

        ## Check if IAM is connected
        if(not oauth.connected):
            raise ConnectionError("[EDC Discovery Service] The authentication service is not connected! Please execute the oauth.connect() method")
        
        ## Setup headers and body
        headers:dict = oauth.add_auth_header(headers={'Content-Type' : 'application/json'})
        body:dict = {
            types_key: keys
        }

        response:Response = HttpTools.do_post(url=url, headers=headers, json=body)
        ## In case the response code is not successfull or the response is null
        if(response is None or response.status_code != 200):
            raise Exception("[EDC Discovery Service] It was not possible to get the discovery service because the response was not successful!")
        
        data = response.json()

        if(not(endpoints_key in data) or len(data[endpoints_key]) == 0):
            raise Exception("[EDC Discovery Service] No endpoints were found in the discovery service for this keys!")

        # Map to every key the endpoint address
        return dict(map(lambda x: (x[return_type_key], x[endpoint_addresses_key]), data[endpoints_key]))

      
class ConnectorDiscoveryService:
    
    connector_discovery_url:str
    oauth:OAuth2Manager
    connector_discovery_key:str

    def __init__(self, oauth:OAuth2Manager, discovery_finder_url:str, connector_discovery_key:str="bpn"):  
        self.connector_discovery_url = self.get_connector_discovery_url(oauth=oauth, discovery_finder_url=discovery_finder_url, connector_discovery_key=connector_discovery_key)
        self.oauth = oauth

    def get_connector_discovery_url(self, oauth:OAuth2Manager, discovery_finder_url:str, connector_discovery_key:str="bpn"):


        endpoints = DiscoveryFinderService.find_discovery_urls(url=discovery_finder_url, oauth=oauth, keys=[connector_discovery_key])
        if(connector_discovery_key not in endpoints):
          raise Exception("[Connector Discovery Service] Connector Discovery endpoint not found!")
        
        self.connector_discovery_url = endpoints[connector_discovery_key]
        
        return self.connector_discovery_url

    def find_connector_by_bpn(self, bpn:str, bpn_key:str="bpn", connector_endpoint_key:str="connectorEndpoint") -> list | None:

        body:list = [
            bpn
        ]
        
        headers:dict = self.oauth.add_auth_header(headers={'Content-Type' : 'application/json'})

        response = HttpTools.do_post(url=self.connector_discovery_url, headers=headers, json=body)
        if(response is None or response.status_code != 200):
            raise Exception("[Connector Discovery Service] It was not possible to get the connector urls because the connector discovery service response was not successful!")
        
        json_response:dict = response.json()

        # Iterate over the json_response to find the connectorEndpoint for the specified BPN
        for item in json_response:
            if item.get(bpn_key) == bpn:
                return item.get(connector_endpoint_key, [])
        # If the BPN is not found, return None or an empty list
        return None