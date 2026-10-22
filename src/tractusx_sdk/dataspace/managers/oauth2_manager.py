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

import logging

from keycloak.keycloak_openid import KeycloakOpenID
from .auth_manager_interface import AuthManagerInterface
from fastapi import Request, HTTPException
from starlette.status import HTTP_401_UNAUTHORIZED

from tractusx_sdk._logging_fields import log_extra, safe_url

# Security: this module handles client secrets, access tokens and Authorization headers.
# None of them is ever logged, not even at DEBUG: only the realm, the (sanitised) server URL,
# the outcome and the TYPE of an exception are. Exception messages and tracebacks are left out
# on purpose, since the identity provider may echo request details in them.
logger = logging.getLogger(__name__)

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

        ## Connect to the server
        self.connect(auth_url=auth_url, realm=realm, clientid=clientid, clientsecret=clientsecret)


    def connect(self, auth_url, realm, clientid, clientsecret):

        self.connected=False
        logger.debug("Connecting to the identity provider at %s (realm %s)", safe_url(auth_url), realm,
                     extra=log_extra(url=auth_url, operation="oauth2.connect"))
        
        ## Store credentials
        self.clientid = clientid
        self.clientsecret = clientsecret

        # Configure client
        self.keycloak_openid = KeycloakOpenID(server_url=auth_url,
                                        client_id=clientid,
                                        realm_name=realm,
                                        client_secret_key=clientsecret)

        # Get WellKnown and if not connected it will not work
        try:
            well_known = self.keycloak_openid.well_known()
        except Exception as exception:
            logger.error("Unable to reach the identity provider at %s (realm %s): %s", safe_url(auth_url), realm,
                         type(exception).__name__, extra=log_extra(url=auth_url, operation="oauth2.connect"))
            raise

        if (not well_known):
            logger.error("The identity provider at %s (realm %s) did not return its well-known configuration",
                         safe_url(auth_url), realm, extra=log_extra(url=auth_url, operation="oauth2.connect"))
            raise ConnectionError("Unable to access the Keycloak instance. Check the server URL, realm, and network connectivity.")
        
        self.connected=True
        logger.info("Connected to the identity provider at %s (realm %s)", safe_url(auth_url), realm,
                    extra=log_extra(url=auth_url, operation="oauth2.connect"))
    

    def get_token(self, scope:str="openid profile email"):
        ## Check if connected
        if(not self.connected):
            logger.error("A token was requested before connecting to the identity provider")
            raise RuntimeError("Not connected. Please call the connect() method before requesting a token.")

        ## Get the token from the keycloak instance
        logger.debug("Requesting a new access token (scope: %s)", scope, extra=log_extra(operation="oauth2.get_token"))
        try:
            token:dict=self.keycloak_openid.token(self.clientid, self.clientsecret, grant_type=["client_credentials"], scope=scope)
        except Exception as exception:
            logger.error("The identity provider rejected the token request: %s", type(exception).__name__,
                         extra=log_extra(operation="oauth2.get_token"))
            raise
        if(token is None):
            logger.error("The identity provider returned no token, the credentials might be incorrect",
                         extra=log_extra(operation="oauth2.get_token"))
            raise ValueError("Failed to retrieve token from IAM instance. The credentials might be incorrect.")
        ## Store the token
        self.token = token
        expires_in = token.get("expires_in") if isinstance(token, dict) else None
        logger.debug("Access token obtained (expires in %s seconds)", expires_in, extra=log_extra(operation="oauth2.get_token"))
        return self.token["access_token"]
    
    def add_auth_header(self, headers:dict=None):
        ## Check if connected
        if(not self.connected):
            logger.error("An authorization header was requested before connecting to the identity provider")
            raise RuntimeError("Not connected. Please call the connect() method before requesting an authorization header.")
        ## Initialize headers if None
        if headers is None:
            logger.debug("No headers provided, creating new ones for the authorization header")
            headers = dict()
        ## Build token header
        headers["Authorization"] = "Bearer " + self.get_token()
        logger.debug("Authorization header added", extra=log_extra(operation="oauth2.add_auth_header"))
        return headers

    def is_authenticated(self, request: Request) -> bool:
        """
        Check if the OAuth2Manager is authenticated.
        This method verifies whether the Bearer token included in the request is valid.
        :param request: FastAPI Request object.
        :return: True if authenticated, False otherwise.
        """
        if not self.connected:
            logger.error("A request was checked before connecting to the identity provider")
            raise RuntimeError("Not connected. Please call the connect() method before checking authentication.")
        
        authorization: str = request.headers.get("Authorization")
        if not authorization or not authorization.startswith("Bearer "):
            logger.warning("Request rejected: the Authorization header is missing or is not a Bearer one",
                           extra=log_extra(operation="oauth2.is_authenticated"))
            raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail="Missing or invalid Authorization header.")
        token = authorization.split(" ")[1]
        try:
            user_info = self.keycloak_openid.userinfo(token)
        except Exception as exception:
            logger.warning("Request rejected: the identity provider could not validate the bearer credential (%s)",
                           type(exception).__name__, extra=log_extra(operation="oauth2.is_authenticated"))
            raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail="Invalid or expired token.")

        authenticated = bool(user_info)
        if authenticated:
            logger.debug("Request authenticated", extra=log_extra(operation="oauth2.is_authenticated"))
        else:
            logger.warning("Request rejected: the identity provider returned no user information",
                           extra=log_extra(operation="oauth2.is_authenticated"))
        return authenticated
