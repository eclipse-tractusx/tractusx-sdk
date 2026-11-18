#################################################################################
# Tractus-X - Industry Flag Service
#
# Copyright (c) 2025,2026 LKS Next
# Copyright (c) 2025 CGI Deutschland B.V. & Co. KG
# Copyright (c) 2025,2026 Contributors to the Eclipse Foundation
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

from typing import Any
from keycloak.keycloak_openid import KeycloakOpenID
from .auth_manager_interface import AuthManagerInterface
from fastapi import Request, HTTPException
from starlette.status import HTTP_401_UNAUTHORIZED

class OAuth2Manager(AuthManagerInterface):
    
    """
    Class responsible for managing the IAM IDP Service
    """

    ## Declare variables
    keycloak_session:KeycloakOpenID
    connected:bool = False
    token:dict[str, Any]

    clientid:str
    clientsecret:str

    def __init__(self, auth_url: str, realm: str, clientid: str, clientsecret: str) -> None:

        ## Connect to the server
        self.connect(auth_url=auth_url, realm=realm, clientid=clientid, clientsecret=clientsecret)


    def connect(self, auth_url: str, realm: str, clientid: str, clientsecret: str) -> None:

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
            raise ConnectionError("Unable to access the Keycloak instance. Check the server URL, realm, and network connectivity.")
        
        self.connected=True
    

    def get_token(self, scope:str="openid profile email") -> str:
        ## Check if connected
        if(not self.connected):
            raise RuntimeError("Not connected. Please call the connect() method before requesting a token.")

        ## Get the token from the keycloak instance
        token:dict[str, Any]=self.keycloak_openid.token(self.clientid, self.clientsecret, grant_type=["client_credentials"], scope=scope)
        if(token is None):
            raise ValueError("Failed to retrieve token from IAM instance. The credentials might be incorrect.")
        ## Store the token
        self.token = token
        access_token: str = self.token["access_token"]
        return access_token
    
    def add_auth_header(self, headers:dict[str, Any] | None=None) -> dict[str, Any]:
        ## Check if connected
        if(not self.connected):
            raise RuntimeError("Not connected. Please call the connect() method before requesting an authorization header.")
        ## Initialize headers if None
        if headers is None:
            headers = dict()
        ## Build token header
        headers["Authorization"] = "Bearer " + self.get_token()
        return headers

    def is_authenticated(self, request: Request) -> bool:
        """
        Check if the OAuth2Manager is authenticated.
        This method verifies whether the Bearer token included in the request is valid.
        :param request: FastAPI Request object.
        :return: True if authenticated, False otherwise.
        """
        if not self.connected:
            raise RuntimeError("Not connected. Please call the connect() method before checking authentication.")
        
        authorization: str | None = request.headers.get("Authorization")
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail="Missing or invalid Authorization header.")
        token = authorization.split(" ")[1]
        try:
            user_info = self.keycloak_openid.userinfo(token)
            return bool(user_info)
        except Exception:
            raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail="Invalid or expired token.")
