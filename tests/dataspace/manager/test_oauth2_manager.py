#################################################################################
# Eclipse Tractus-X - Software Development KIT
#
# Copyright (c) 2025 LKS NEXT
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

import unittest
from unittest.mock import Mock
from fastapi import Request, HTTPException
from keycloak.exceptions import KeycloakConnectionError
from tractusx_sdk.exceptions import AuthServiceUnavailableError, TractusXSDKError
from starlette.datastructures import Headers
from tractusx_sdk.dataspace.managers.oauth2_manager import OAuth2Manager
from unittest.mock import patch, MagicMock

class TestOAuth2Manager(unittest.TestCase):

    def setUp(self):
        self.auth_url = "http://example.com/auth"
        self.realm = "test_realm"
        self.clientid = "test_client"
        self.clientsecret = "test_secret"

    @patch("tractusx_sdk.dataspace.managers.oauth2_manager.KeycloakOpenID")
    def test_connect_successful(self, mock_keycloak_cls):

        mock_keycloak = MagicMock()
        mock_keycloak.well_known.return_value = True
        mock_keycloak_cls.return_value = mock_keycloak

        manager = OAuth2Manager.__new__(OAuth2Manager)

        manager.connect(
            auth_url=self.auth_url,
            realm=self.realm,
            clientid=self.clientid,
            clientsecret=self.clientsecret
        )

        self.assertTrue(manager.connected)
        self.assertEqual(manager.clientid, self.clientid)
        self.assertEqual(manager.clientsecret, self.clientsecret)
        mock_keycloak_cls.assert_called_once_with(
            server_url=self.auth_url,
            client_id=self.clientid,
            realm_name=self.realm,
            client_secret_key=self.clientsecret
        )
        mock_keycloak.well_known.assert_called_once()

    @patch("tractusx_sdk.dataspace.managers.oauth2_manager.KeycloakOpenID")
    def test_connect_fails_when_well_known_false(self, mock_keycloak_cls):

        mock_keycloak = MagicMock()
        mock_keycloak.well_known.return_value = False
        mock_keycloak_cls.return_value = mock_keycloak

        manager = OAuth2Manager.__new__(OAuth2Manager)

        with self.assertRaises(ConnectionError) as exc:
            manager.connect(
                auth_url=self.auth_url,
                realm=self.realm,
                clientid=self.clientid,
                clientsecret=self.clientsecret
            )
        self.assertIn("Unable to access the Keycloak instance", str(exc.exception))
        self.assertFalse(getattr(manager, "connected", False))

    @patch("tractusx_sdk.dataspace.managers.oauth2_manager.KeycloakOpenID")
    def test_get_token_success(self, mock_keycloak_cls):

        mock_keycloak = MagicMock()
        mock_token = {"access_token": "abc123", "refresh_token": "def456"}
        mock_keycloak.token.return_value = mock_token
        mock_keycloak.well_known.return_value = True
        mock_keycloak_cls.return_value = mock_keycloak

        manager = OAuth2Manager(self.auth_url, self.realm, self.clientid, self.clientsecret)
        manager.connected = True
        manager.keycloak_openid = mock_keycloak

        token = manager.get_token()

        self.assertEqual(token, "abc123")
        self.assertEqual(manager.token, mock_token)
        mock_keycloak.token.assert_called_once_with(
            self.clientid,
            self.clientsecret,
            grant_type=["client_credentials"],
            scope="openid profile email"
        )

    @patch("tractusx_sdk.dataspace.managers.oauth2_manager.KeycloakOpenID")
    def test_get_token_not_connected_raises(self, mock_keycloak_cls):

        manager = OAuth2Manager.__new__(OAuth2Manager)
        manager.connected = False

        with self.assertRaises(RuntimeError) as exc:
            manager.get_token()
        self.assertIn("Not connected", str(exc.exception))

    @patch("tractusx_sdk.dataspace.managers.oauth2_manager.KeycloakOpenID")
    def test_get_token_returns_none_raises(self, mock_keycloak_cls):
 
        mock_keycloak = MagicMock()
        mock_keycloak.token.return_value = None
        manager = OAuth2Manager.__new__(OAuth2Manager)
        manager.connected = True
        manager.keycloak_openid = mock_keycloak
        manager.clientid = self.clientid
        manager.clientsecret = self.clientsecret

        with self.assertRaises(ValueError) as exc:
            manager.get_token()
        self.assertIn("Failed to retrieve token", str(exc.exception))

    @patch("tractusx_sdk.dataspace.managers.oauth2_manager.KeycloakOpenID")
    def test_add_auth_header_success_with_none_headers(self, mock_keycloak_cls):

        mock_keycloak = MagicMock()
        mock_keycloak.token.return_value = {"access_token": "abc123"}
        mock_keycloak.well_known.return_value = True
        mock_keycloak_cls.return_value = mock_keycloak

        manager = OAuth2Manager(self.auth_url, self.realm, self.clientid, self.clientsecret)
        manager.connected = True
        manager.keycloak_openid = mock_keycloak

        headers = manager.add_auth_header({})

        self.assertIn("Authorization", headers)
        self.assertEqual(headers["Authorization"], "Bearer abc123")

    @patch("tractusx_sdk.dataspace.managers.oauth2_manager.KeycloakOpenID")
    def test_add_auth_header_success_with_existing_headers(self, mock_keycloak_cls):

        mock_keycloak = MagicMock()
        mock_keycloak.token.return_value = {"access_token": "xyz789"}
        mock_keycloak.well_known.return_value = True
        mock_keycloak_cls.return_value = mock_keycloak

        manager = OAuth2Manager(self.auth_url, self.realm, self.clientid, self.clientsecret)
        manager.connected = True
        manager.keycloak_openid = mock_keycloak
        existing_headers = {"X-Test": "value"}

        headers = manager.add_auth_header(existing_headers.copy())

        self.assertIn("Authorization", headers)
        self.assertEqual(headers["Authorization"], "Bearer xyz789")
        self.assertEqual(headers["X-Test"], "value")

    def test_add_auth_header_not_connected_raises(self):
        manager = OAuth2Manager.__new__(OAuth2Manager)
        manager.connected = False

        with self.assertRaises(RuntimeError) as exc:
            manager.add_auth_header()
        self.assertIn("Not connected", str(exc.exception))

    @patch("tractusx_sdk.dataspace.managers.oauth2_manager.KeycloakOpenID")
    def test_is_authenticated_success(self, mock_keycloak_cls):
        # Setup
        mock_keycloak = MagicMock()
        mock_keycloak.userinfo.return_value = {"sub": "user1"}
        mock_keycloak_cls.return_value = mock_keycloak

        manager = OAuth2Manager.__new__(OAuth2Manager)
        manager.connected = True
        manager.keycloak_openid = mock_keycloak

        headers = Headers({"Authorization": "Bearer validtoken"})
        request = Mock(spec=Request)
        request.headers = headers

        result = manager.is_authenticated(request)
        self.assertTrue(result)
        mock_keycloak.userinfo.assert_called_once_with("validtoken")

    def test_is_authenticated_not_connected_raises(self):
        manager = OAuth2Manager.__new__(OAuth2Manager)
        manager.connected = False

        request = Mock(spec=Request)
        request.headers = Headers({"Authorization": "Bearer sometoken"})

        with self.assertRaises(RuntimeError) as exc:
            manager.is_authenticated(request)
        self.assertIn("Not connected", str(exc.exception))

    @patch("tractusx_sdk.dataspace.managers.oauth2_manager.KeycloakOpenID")
    def test_is_authenticated_missing_authorization_header_raises(self, mock_keycloak_cls):
        manager = OAuth2Manager.__new__(OAuth2Manager)
        manager.connected = True
        manager.keycloak_openid = MagicMock()

        request = Mock(spec=Request)
        request.headers = Headers({})

        with self.assertRaises(HTTPException) as exc:
            manager.is_authenticated(request)
        self.assertEqual(exc.exception.status_code, 401)
        self.assertIn("Missing or invalid Authorization header", exc.exception.detail)

    @patch("tractusx_sdk.dataspace.managers.oauth2_manager.KeycloakOpenID")
    def test_is_authenticated_invalid_authorization_header_raises(self, mock_keycloak_cls):
        manager = OAuth2Manager.__new__(OAuth2Manager)
        manager.connected = True
        manager.keycloak_openid = MagicMock()

        request = Mock(spec=Request)
        request.headers = Headers({"Authorization": "Basic sometoken"})

        with self.assertRaises(HTTPException) as exc:
            manager.is_authenticated(request)
        self.assertEqual(exc.exception.status_code, 401)
        self.assertIn("Missing or invalid Authorization header", exc.exception.detail)

    @patch("tractusx_sdk.dataspace.managers.oauth2_manager.KeycloakOpenID")
    def test_is_authenticated_userinfo_raises_exception(self, mock_keycloak_cls):
        mock_keycloak = MagicMock()
        mock_keycloak.userinfo.side_effect = Exception("Token error")
        mock_keycloak_cls.return_value = mock_keycloak

        manager = OAuth2Manager.__new__(OAuth2Manager)
        manager.connected = True
        manager.keycloak_openid = mock_keycloak

        headers = Headers({"Authorization": "Bearer invalidtoken"})
        request = Mock(spec=Request)
        request.headers = headers

        with self.assertRaises(HTTPException) as exc:
            manager.is_authenticated(request)
        self.assertEqual(exc.exception.status_code, 401)
        self.assertIn("Invalid or expired token", exc.exception.detail)

    @patch("tractusx_sdk.dataspace.managers.oauth2_manager.KeycloakOpenID")
    def test_is_authenticated_userinfo_returns_empty_dict(self, mock_keycloak_cls):
        mock_keycloak = MagicMock()
        mock_keycloak.userinfo.return_value = {}
        mock_keycloak_cls.return_value = mock_keycloak

        manager = OAuth2Manager.__new__(OAuth2Manager)
        manager.connected = True
        manager.keycloak_openid = mock_keycloak

        headers = Headers({"Authorization": "Bearer validtoken"})
        request = Mock(spec=Request)
        request.headers = headers

        result = manager.is_authenticated(request)
        self.assertFalse(result)


    # Lazy initialization (issue #269): the constructor must not contact Keycloak.

    def test_init_with_unreachable_server_does_not_block_or_raise(self):
        # Closed local port: before the fix the constructor raised KeycloakConnectionError here.
        manager = OAuth2Manager("http://127.0.0.1:9/", self.realm, self.clientid, self.clientsecret)

        self.assertFalse(manager.connected)

    @patch("tractusx_sdk.dataspace.managers.oauth2_manager.KeycloakOpenID")
    def test_init_does_not_contact_keycloak(self, mock_keycloak_cls):
        manager = OAuth2Manager(self.auth_url, self.realm, self.clientid, self.clientsecret)

        self.assertFalse(manager.connected)
        mock_keycloak_cls.assert_not_called()

    @patch("tractusx_sdk.dataspace.managers.oauth2_manager.KeycloakOpenID")
    def test_get_token_connects_on_first_use(self, mock_keycloak_cls):
        mock_keycloak = MagicMock()
        mock_keycloak.well_known.return_value = True
        mock_keycloak.token.return_value = {"access_token": "abc123"}
        mock_keycloak_cls.return_value = mock_keycloak

        manager = OAuth2Manager(self.auth_url, self.realm, self.clientid, self.clientsecret)
        self.assertEqual(manager.get_token(), "abc123")
        self.assertEqual(manager.get_token(), "abc123")

        self.assertTrue(manager.connected)
        mock_keycloak.well_known.assert_called_once()

    @patch("tractusx_sdk.dataspace.managers.oauth2_manager.KeycloakOpenID")
    def test_get_token_unreachable_raises_auth_service_error_and_retries(self, mock_keycloak_cls):
        mock_keycloak = MagicMock()
        mock_keycloak.well_known.side_effect = KeycloakConnectionError("down")
        mock_keycloak_cls.return_value = mock_keycloak

        manager = OAuth2Manager(self.auth_url, self.realm, self.clientid, self.clientsecret)

        with self.assertRaises(AuthServiceUnavailableError) as exc:
            manager.get_token()
        # Still a ConnectionError and an SDK error, so existing handlers keep working.
        self.assertIsInstance(exc.exception, ConnectionError)
        self.assertIsInstance(exc.exception, TractusXSDKError)
        self.assertIsInstance(exc.exception.__cause__, KeycloakConnectionError)
        self.assertFalse(manager.connected)

        # Keycloak comes back: the next call connects instead of staying failed.
        mock_keycloak.well_known.side_effect = None
        mock_keycloak.well_known.return_value = True
        mock_keycloak.token.return_value = {"access_token": "abc123"}
        self.assertEqual(manager.get_token(), "abc123")
        self.assertEqual(mock_keycloak.well_known.call_count, 2)

    @patch("tractusx_sdk.dataspace.managers.oauth2_manager.KeycloakOpenID")
    def test_empty_well_known_on_first_use_raises_auth_service_error(self, mock_keycloak_cls):
        mock_keycloak = MagicMock()
        mock_keycloak.well_known.return_value = False
        mock_keycloak_cls.return_value = mock_keycloak

        manager = OAuth2Manager(self.auth_url, self.realm, self.clientid, self.clientsecret)

        with self.assertRaises(AuthServiceUnavailableError):
            manager.get_token()
        self.assertFalse(manager.connected)

    @patch("tractusx_sdk.dataspace.managers.oauth2_manager.KeycloakOpenID")
    def test_is_authenticated_unreachable_returns_503(self, mock_keycloak_cls):
        mock_keycloak = MagicMock()
        mock_keycloak.well_known.side_effect = KeycloakConnectionError("down")
        mock_keycloak_cls.return_value = mock_keycloak

        manager = OAuth2Manager(self.auth_url, self.realm, self.clientid, self.clientsecret)

        request = Mock(spec=Request)
        request.headers = Headers({"Authorization": "Bearer validtoken"})

        with self.assertRaises(HTTPException) as exc:
            manager.is_authenticated(request)
        self.assertEqual(exc.exception.status_code, 503)


if __name__ == "__main__":
    unittest.main()
