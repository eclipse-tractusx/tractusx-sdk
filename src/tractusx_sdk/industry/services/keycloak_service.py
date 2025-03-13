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
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND,
# either express or implied. See the
# License for the specific language govern in permissions and limitations
# under the License.
#
# SPDX-License-Identifier: Apache-2.0
#################################################################################

from keycloak import KeycloakOpenID
from datetime import datetime, timedelta
import logging
from tractusx_sdk.industry.services import AuthService

logger = logging.getLogger(__name__)

class KeycloakService(AuthService):
    """
    KeycloakService is a wrapper around the KeycloakOpenID class from the keycloak library.
    It provides authentication services for accessing protected resources.

    Args:
        server_url (str): The URL of the Keycloak server.
        client_id (str): The client ID of the client application.
        client_secret (str): The client secret of the client application.
        realm (str): The realm name of the Keycloak server.
        grant_type (str): The grant type to use for authentication (e.g. "client_credentials").
    """
    def __init__(
        self,
        server_url: str,
        client_id: str,
        client_secret: str,
        realm: str = "master",
        grant_type: str = "client_credentials",
    ):
        self.keycloak_openid = KeycloakOpenID(
            server_url=server_url,
            client_id=client_id,
            client_secret_key=client_secret,
            realm_name=realm,
        )
        self.grant_type = grant_type
        self.token = None
        self.token_expiry: datetime | None = None

    def get_token(self) -> str:
        """
        Get a valid access token, refreshing if necessary.
        
        Returns:
            str: The access token
        """
        # Refresh token if it has expired
        self._refresh_token()
        return self.token["access_token"]

    def is_token_valid(self) -> bool:
        """
        Check if the token has expired
        
        Returns:
            bool: True if the token has expired, False otherwise.
        """
        # Add some buffer time (30 seconds) to avoid edge cases
        buffer_time = 30
        
        if self.token is None or self.token_expiry is None:
            return True
        
        # Check if token will expire in the next 30 seconds
        return datetime.now() + timedelta(seconds=buffer_time) >= self.token_expiry

    def _refresh_token(self) -> str:
        """
        Refresh the token if it has expired.

        Returns:
            str: The access token.
            
        Raises:
            KeycloakError: If token retrieval fails
        """
        try:
            if self.token is None or self.is_token_valid():
                logger.debug("Refreshing Keycloak token")
                
                self.token = self.keycloak_openid.token(grant_type=self.grant_type)
                self.token_expiry = datetime.now() + timedelta(seconds=self.token.get("expires_in", 300))
                
                logger.debug("Token refreshed successfully")
            return self.token["access_token"]
        except Exception as e:
            logger.error(f"Failed to refresh token: {str(e)}")
            raise
