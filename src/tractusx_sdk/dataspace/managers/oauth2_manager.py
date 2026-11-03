#################################################################################
# Tractus-X - Industry Flag Service
#
# Copyright (c) 2025 LKS NEXT
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

from keycloak.keycloak_openid import KeycloakOpenID
from keycloak.exceptions import KeycloakConnectionError
from tractusx_sdk.exceptions import AuthServiceUnavailableError
from .auth_manager_interface import AuthManagerInterface
from fastapi import Request, HTTPException
from starlette.status import HTTP_401_UNAUTHORIZED, HTTP_503_SERVICE_UNAVAILABLE

class OAuth2Manager(AuthManagerInterface):
    
    """
    Class responsible for managing the IAM IDP Service
    """

    ## Declare variables
    keycloak_session:KeycloakOpenID
    connected:bool = False
    token:dict

    clientid:str
    clientsecret:str

    def __init__(self, auth_url, realm, clientid, clientsecret):

        ## Keep the connection parameters. The Keycloak server is contacted lazily,
        ## on first use, so building the manager never blocks the host application's startup.
        self.connected = False
        self.clientid = clientid
        self.clientsecret = clientsecret
        self._connection_params = dict(auth_url=auth_url, realm=realm, clientid=clientid, clientsecret=clientsecret)

    def _ensure_connected(self, action:str):
        """
        Connect to Keycloak on first use.

        :param action: what the caller is about to do, used in the error message.
        :raises RuntimeError: if the manager has no stored connection parameters.
        :raises AuthServiceUnavailableError: if Keycloak cannot be reached (a ``ConnectionError``); the manager stays disconnected, so the next call retries.
        """
        if(self.connected):
            return

        params = getattr(self, "_connection_params", None)
        if(params is None):
            raise RuntimeError(f"Not connected. Please call the connect() method before {action}.")

        try:
            self.connect(**params)
        except (KeycloakConnectionError, ConnectionError) as e:
            raise AuthServiceUnavailableError("Unable to access the Keycloak instance. Check the server URL, realm, and network connectivity.") from e


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
            raise ConnectionError("Unable to access the Keycloak instance. Check the server URL, realm, and network connectivity.")
        
        self.connected=True
    

    def get_token(self, scope:str="openid profile email"):
        ## Connect on first use
        self._ensure_connected("requesting a token")

        ## Get the token from the keycloak instance
        token:dict=self.keycloak_openid.token(self.clientid, self.clientsecret, grant_type=["client_credentials"], scope=scope)
        if(token is None):
            raise ValueError("Failed to retrieve token from IAM instance. The credentials might be incorrect.")
        ## Store the token
        self.token = token
        return self.token["access_token"]
    
    def add_auth_header(self, headers:dict=None):
        ## Connect on first use
        self._ensure_connected("requesting an authorization header")
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
        try:
            self._ensure_connected("checking authentication")
        except AuthServiceUnavailableError as e:
            ## The problem is the Keycloak server, not the caller's credentials
            raise HTTPException(status_code=HTTP_503_SERVICE_UNAVAILABLE, detail="Authentication service unavailable.") from e

        authorization: str = request.headers.get("Authorization")
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail="Missing or invalid Authorization header.")
        token = authorization.split(" ")[1]
        try:
            user_info = self.keycloak_openid.userinfo(token)
            return bool(user_info)
        except Exception:
            raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail="Invalid or expired token.")
