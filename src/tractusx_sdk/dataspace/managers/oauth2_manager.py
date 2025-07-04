#################################################################################
# Tractus-X - Industry Flag Service
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

from keycloak import KeycloakOpenID

class OAuth2Manager:
    
    """
    Class responsible for managing the IAM IDP Service
    """

    ## Declare variables
    keycloak_session:KeycloakOpenID
    connected:bool = False
    token:str

    clientid:str
    clientsecret:str

    def __init__(self, auth_url, realm, clientid, clientsecret):

        ## Connect to the server
        self.connect(auth_url=auth_url, realm=realm, clientid=clientid, clientsecret=clientsecret)


    def connect(self, auth_url, realm, clientid, clientsecret):

        self.connected=False
        
        ## Store credentials
        self.clientid = clientid
        self.clientsecret = clientsecret

        # Configure client
        self.keycloak_openid = KeycloakOpenID(server_url=auth_url,
                                        client_id=clientid,
                                        realm_name=realm,
                                        client_secret_key=clientsecret)

        # Get WellKnown and if not connected it will not work
        if (not self.keycloak_openid.well_known()):
            raise Exception("It was not able to access the keycloak instance!")
        
        self.connected=True
    

    def get_token(self):
        ## Check if connected
        if(not self.connected):
            raise Exception("Not connected, please execute the connect() method again before requesting a token!")

        ## Get the token from the keycloak instance
        token=self.keycloak_openid.token(self.clientid, self.clientsecret, grant_type=["client_credentials"], scope="openid profile email")
        if(token is None):
            raise Exception("It was not possible to get the token from the iam instance!")
        ## Store the token
        self.token = token
        return self.token["access_token"]
    
    def add_auth_header(self, headers=None):
        ## Check if connected
        if(not self.connected):
            raise Exception("Not connected, please execute the connect() method again before requesting a authorization header!")
        ## Initialize headers if None
        if headers is None:
            headers = {}
        ## Build token header
        headers["Authorization"] = "Bearer " + self.get_token()
        return headers
