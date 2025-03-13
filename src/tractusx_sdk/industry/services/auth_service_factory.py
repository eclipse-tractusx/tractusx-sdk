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

import logging
from tractusx_sdk.industry.services import AuthService, KeycloakService

logger = logging.getLogger(__name__)


class AuthServiceFactory:
    """
    Factory class for creating authentication services.
    """

    @staticmethod
    def create_keycloak_service(
        auth_url: str,
        client_id: str,
        client_secret: str,
        realm: str = "default",
        grant_type: str = "client_credentials",
    ) -> AuthService | None:
        """
        Create a KeycloakService if authentication parameters are provided.

        Args:
            auth_url (str): Keycloak server URL
            client_id (str): Client ID for authentication
            client_secret (str): Client secret for authentication
            realm (str, optional): Keycloak realm name (default: "default")
            grant_type (str, optional): Grant type for authentication (default: "client_credentials")

        Returns:
            KeycloakService or None: A KeycloakService instance if all required parameters are provided,
                                     None otherwise
        """
        try:
            logger.info(
                f"Creating KeycloakService with URL: {auth_url}, client ID: {client_id}"
            )
            return KeycloakService(
                server_url=auth_url,
                client_id=client_id,
                client_secret=client_secret,
                realm=realm,
                grant_type=grant_type,
            )
        except Exception as e:
            logger.error(f"Failed to create KeycloakService: {str(e)}")
            raise e
