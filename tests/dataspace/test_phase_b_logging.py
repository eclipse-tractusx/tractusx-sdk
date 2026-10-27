#################################################################################
# Eclipse Tractus-X - Software Development KIT
#
# Copyright (c) 2026 LKS Next
# Copyright (c) 2026 Contributors to the Eclipse Foundation
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

"""The log records of the authentication, the connection managers and the discovery services."""

import logging
from unittest.mock import MagicMock, Mock, patch

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from starlette.datastructures import Headers

from tractusx_sdk.dataspace.managers.auth_manager import AuthManager
from tractusx_sdk.dataspace.managers.connection.database.postgres_connection_manager import PostgresConnectionManager
from tractusx_sdk.dataspace.managers.connection.file_system.file_system_connection_manager import FileSystemConnectionManager
from tractusx_sdk.dataspace.managers.connection.memory.memory_connection_manager import MemoryConnectionManager
from tractusx_sdk.dataspace.managers.oauth2_manager import OAuth2Manager
from tractusx_sdk.dataspace.services.discovery.connector_discovery_service import ConnectorDiscoveryService
from tractusx_sdk.dataspace.services.discovery.discovery_finder_service import DiscoveryFinderService
from tractusx_sdk.exceptions import ConnectionManagerError, DiscoveryError, DiscoveryEndpointNotFoundError
from tractusx_sdk.industry.services.discovery.bpn_discovery_service import BpnDiscoveryService

SECRET = "s3cr3t-value"
AUTH_URL = f"https://iam.example.com:8443/auth?access_token={SECRET}"
KEYCLOAK = "tractusx_sdk.dataspace.managers.oauth2_manager.KeycloakOpenID"


def _dump(caplog) -> str:
    """Everything a handler could ever render out of the captured records."""
    return "\n".join(f"{r.getMessage()} {r.__dict__} {r.exc_text or ''}" for r in caplog.records)


def _records(caplog, name):
    return [r for r in caplog.records if r.name == name]


def _request(authorization=None, **headers):
    values = dict(headers)
    if authorization is not None:
        values["Authorization"] = authorization
    return MagicMock(headers=Headers(values))


class TestOAuth2ManagerLogging:
    LOGGER = "tractusx_sdk.dataspace.managers.oauth2_manager"

    @pytest.fixture
    def keycloak(self):
        with patch(KEYCLOAK) as keycloak_cls:
            keycloak = keycloak_cls.return_value
            keycloak.well_known.return_value = {"issuer": "x"}
            keycloak.token.return_value = {"access_token": f"access-{SECRET}", "expires_in": 300}
            keycloak.userinfo.return_value = {"sub": "user"}
            yield keycloak

    @pytest.fixture
    def manager(self, keycloak):
        return OAuth2Manager(AUTH_URL, "realm-a", "client-a", f"client-secret-{SECRET}")

    def test_connecting_is_logged_with_the_realm_and_the_sanitised_url(self, keycloak, caplog):
        with caplog.at_level(logging.DEBUG):
            OAuth2Manager(AUTH_URL, "realm-a", "client-a", f"client-secret-{SECRET}")

        connecting, connected = _records(caplog, self.LOGGER)
        assert connecting.levelno == logging.DEBUG
        assert connected.levelno == logging.INFO
        assert connected.getMessage() == "Connected to the identity provider at https://iam.example.com:8443/auth (realm realm-a)"
        assert connected.url == "https://iam.example.com:8443/auth"
        assert SECRET not in _dump(caplog)

    def test_an_empty_well_known_is_logged_before_it_is_raised(self, keycloak, caplog):
        keycloak.well_known.return_value = None
        with caplog.at_level(logging.DEBUG), pytest.raises(ConnectionError):
            OAuth2Manager(AUTH_URL, "realm-a", "client-a", "secret")
        assert _records(caplog, self.LOGGER)[-1].levelno == logging.ERROR
        assert SECRET not in _dump(caplog)

    def test_a_connection_failure_logs_the_exception_type_only(self, keycloak, caplog):
        error = ConnectionRefusedError(f"refused for {SECRET}")
        keycloak.well_known.side_effect = error
        with caplog.at_level(logging.DEBUG), pytest.raises(ConnectionRefusedError) as raised:
            OAuth2Manager(AUTH_URL, "realm-a", "client-a", "secret")

        assert raised.value is error
        failure = _records(caplog, self.LOGGER)[-1]
        assert failure.levelno == logging.ERROR and failure.exc_info is None
        assert "ConnectionRefusedError" in failure.getMessage()
        assert SECRET not in _dump(caplog)

    def test_a_token_request_never_logs_the_token_nor_the_client_secret(self, manager, caplog):
        with caplog.at_level(logging.DEBUG):
            token = manager.get_token()

        assert token == f"access-{SECRET}"
        assert [r.getMessage() for r in _records(caplog, self.LOGGER)] == [
            "Requesting a new access token (scope: openid profile email)",
            "Access token obtained (expires in 300 seconds)",
        ]
        assert SECRET not in _dump(caplog)

    def test_a_rejected_token_request_logs_the_exception_type_only(self, manager, keycloak, caplog):
        error = RuntimeError(f"invalid_client {SECRET}")
        keycloak.token.side_effect = error
        with caplog.at_level(logging.DEBUG), pytest.raises(RuntimeError) as raised:
            manager.get_token()

        assert raised.value is error
        failure = _records(caplog, self.LOGGER)[-1]
        assert failure.levelno == logging.ERROR and failure.exc_info is None
        assert SECRET not in _dump(caplog)

    def test_no_token_is_logged_before_it_is_raised(self, manager, keycloak, caplog):
        keycloak.token.return_value = None
        with caplog.at_level(logging.DEBUG), pytest.raises(ValueError):
            manager.get_token()
        assert _records(caplog, self.LOGGER)[-1].levelno == logging.ERROR

    def test_using_the_manager_before_connecting_is_logged_before_it_is_raised(self, caplog):
        manager = OAuth2Manager.__new__(OAuth2Manager)
        manager.connected = False
        with caplog.at_level(logging.DEBUG):
            for call in (manager.get_token, manager.add_auth_header, lambda: manager.is_authenticated(_request())):
                with pytest.raises(RuntimeError, match="Not connected"):
                    call()
        assert [r.levelno for r in _records(caplog, self.LOGGER)] == [logging.ERROR] * 3

    def test_the_authorization_header_is_never_logged(self, manager, caplog):
        with caplog.at_level(logging.DEBUG):
            headers = manager.add_auth_header()
        assert headers["Authorization"] == f"Bearer access-{SECRET}"
        assert any(r.getMessage() == "Authorization header added" for r in caplog.records)
        assert SECRET not in _dump(caplog) and "Bearer" not in _dump(caplog)

    def test_a_missing_authorization_header_is_a_warning(self, manager, caplog):
        with caplog.at_level(logging.DEBUG), pytest.raises(HTTPException) as raised:
            manager.is_authenticated(_request())
        assert raised.value.status_code == 401
        assert _records(caplog, self.LOGGER)[-1].levelno == logging.WARNING

    def test_a_credential_that_cannot_be_validated_is_a_warning_without_its_value(self, manager, keycloak, caplog):
        keycloak.userinfo.side_effect = Exception(f"token {SECRET} expired")
        with caplog.at_level(logging.DEBUG), pytest.raises(HTTPException) as raised:
            manager.is_authenticated(_request(f"Bearer {SECRET}"))

        assert raised.value.status_code == 401
        warning = _records(caplog, self.LOGGER)[-1]
        assert warning.levelno == logging.WARNING and warning.exc_info is None
        assert "(Exception)" in warning.getMessage()
        assert SECRET not in _dump(caplog)

    def test_an_authenticated_request_is_logged_at_debug(self, manager, caplog):
        with caplog.at_level(logging.DEBUG):
            assert manager.is_authenticated(_request(f"Bearer {SECRET}")) is True
        assert _records(caplog, self.LOGGER)[-1].levelno == logging.DEBUG
        assert SECRET not in _dump(caplog)

    def test_an_empty_user_info_is_a_warning_and_returns_false(self, manager, keycloak, caplog):
        keycloak.userinfo.return_value = {}
        with caplog.at_level(logging.DEBUG):
            assert manager.is_authenticated(_request(f"Bearer {SECRET}")) is False
        assert _records(caplog, self.LOGGER)[-1].levelno == logging.WARNING
        assert SECRET not in _dump(caplog)


class TestAuthManagerLogging:
    LOGGER = "tractusx_sdk.dataspace.managers.auth_manager"
    KEY = f"api-key-{SECRET}"

    def test_a_disabled_authentication_is_noted_at_debug(self, caplog):
        with caplog.at_level(logging.DEBUG):
            manager = AuthManager(configured_api_key=self.KEY, auth_enabled=False)
            assert manager.is_authenticated(_request()) is True
        assert {r.levelno for r in _records(caplog, self.LOGGER)} == {logging.DEBUG}
        assert SECRET not in _dump(caplog)

    def test_a_missing_key_is_a_warning(self, caplog):
        manager = AuthManager(configured_api_key=self.KEY, auth_enabled=True)
        with caplog.at_level(logging.DEBUG):
            assert manager.is_authenticated(_request()) is False
        assert _records(caplog, self.LOGGER)[-1].levelno == logging.WARNING
        assert SECRET not in _dump(caplog)

    def test_a_wrong_key_is_a_warning_that_logs_neither_key(self, caplog):
        manager = AuthManager(configured_api_key=self.KEY, auth_enabled=True)
        with caplog.at_level(logging.DEBUG):
            assert manager.is_authenticated(_request(**{"X-Api-Key": "wrong-supplied-key"})) is False
        assert _records(caplog, self.LOGGER)[-1].levelno == logging.WARNING
        assert SECRET not in _dump(caplog) and "wrong-supplied-key" not in _dump(caplog)

    def test_a_valid_key_is_accepted_at_debug(self, caplog):
        manager = AuthManager(configured_api_key=self.KEY, auth_enabled=True)
        with caplog.at_level(logging.DEBUG):
            assert manager.is_authenticated(_request(**{"X-Api-Key": self.KEY})) is True
        assert _records(caplog, self.LOGGER)[-1].levelno == logging.DEBUG
        assert SECRET not in _dump(caplog)

    def test_the_header_is_added_without_logging_the_key(self, caplog):
        manager = AuthManager(configured_api_key=self.KEY, auth_enabled=True)
        with caplog.at_level(logging.DEBUG):
            assert manager.add_auth_header({"a": "b"}) == {"a": "b", "X-Api-Key": self.KEY}
        assert SECRET not in _dump(caplog)

    def test_asking_for_a_header_when_disabled_is_logged_before_it_is_raised(self, caplog):
        manager = AuthManager(configured_api_key=self.KEY, auth_enabled=False)
        with caplog.at_level(logging.DEBUG), pytest.raises(RuntimeError):
            manager.add_auth_header()
        assert _records(caplog, self.LOGGER)[-1].levelno == logging.ERROR


def _entry(transfer_id="tp-1", provider="BPNL1"):
    return {
        "@id": transfer_id, "@type": "edr", "@context": {}, "providerId": provider,
        "transferProcessId": transfer_id, "endpoint": "https://data.example.com", "authorization": f"edr-token-{SECRET}",
    }


ADDRESS = f"https://provider.example.com/dsp?token={SECRET}"
KEYS = ("BPNL1", ADDRESS, "qchk", "pchk")


class TestMemoryConnectionManagerLogging:
    LOGGER = "tractusx_sdk.dataspace.managers.connection.memory.memory_connection_manager"

    @pytest.fixture
    def manager(self):
        return MemoryConnectionManager()

    def test_adding_a_connection_logs_identifiers_but_never_the_edr(self, manager, caplog):
        with caplog.at_level(logging.DEBUG):
            manager.add_connection(*KEYS, _entry())

        added = _records(caplog, self.LOGGER)[-1]
        assert (added.counter_party_id, added.transfer_id) == ("BPNL1", "tp-1")
        assert added.counter_party_address == "https://provider.example.com/dsp"
        assert SECRET not in _dump(caplog)

    def test_replacing_an_entry_is_logged(self, manager, caplog):
        manager.add_connection(*KEYS, _entry())
        with caplog.at_level(logging.DEBUG):
            manager.add_connection(*KEYS, _entry("tp-2"))
        assert any("was replaced" in r.getMessage() for r in _records(caplog, self.LOGGER))

    def test_an_entry_without_transfer_id_is_logged_before_it_is_raised(self, manager, caplog):
        with caplog.at_level(logging.DEBUG), pytest.raises(ConnectionManagerError):
            manager.add_connection(*KEYS, {"providerId": "x"})
        error = _records(caplog, self.LOGGER)[-1]
        assert error.levelno == logging.ERROR and error.counter_party_id == "BPNL1"
        assert SECRET not in _dump(caplog)

    def test_a_hit_and_a_miss_are_logged(self, manager, caplog):
        manager.add_connection(*KEYS, _entry())
        with caplog.at_level(logging.DEBUG):
            assert manager.get_connection(*KEYS)
            assert manager.get_connection("BPNL9", ADDRESS, "q", "p") == {}
            assert manager.get_connection_transfer_id(*KEYS) == "tp-1"

        hit, miss, hit_again = _records(caplog, self.LOGGER)
        assert "Cache hit" in hit.getMessage() and hit.transfer_id == "tp-1"
        assert "Cache miss" in miss.getMessage() and not hasattr(miss, "transfer_id")
        assert "Cache hit" in hit_again.getMessage()
        assert SECRET not in _dump(caplog)

    def test_deleting_logs_every_outcome(self, manager, caplog):
        manager.add_connection(*KEYS, _entry())
        with caplog.at_level(logging.DEBUG):
            assert manager.delete_connection(*KEYS) is True
            assert manager.delete_connection(*KEYS) is False
            assert manager.delete_connection("BPNL9", ADDRESS, "q", "p") is False

        messages = [r.getMessage() for r in _records(caplog, self.LOGGER)]
        assert messages[0].startswith("[Memory Connection Manager] Deleted EDR entry")
        assert messages[1].startswith("[Memory Connection Manager] No EDR found to delete for policy checksum")
        assert messages[2].startswith("[Memory Connection Manager] No EDR found to delete for the provided keys")

    def test_clearing_by_party_logs_the_count_or_the_absence_of_matches(self, manager, caplog):
        manager.add_connection("did:web:x:BPNL1", ADDRESS, "q", "p", _entry())
        with caplog.at_level(logging.DEBUG):
            assert manager.clear_connections_by_party("BPNL1") == 1
            assert manager.clear_connections_by_party("BPNL1") == 0

        cleared, none = _records(caplog, self.LOGGER)
        assert cleared.levelno == logging.INFO and cleared.counter_party_id == "BPNL1"
        assert none.levelno == logging.DEBUG


class _ConcretePostgresConnectionManager(PostgresConnectionManager):
    """PostgresConnectionManager does not implement the abstract clear_connections_by_party, so it cannot be instantiated."""

    def clear_connections_by_party(self, counter_party_id_substring: str) -> int:
        return 0


class TestPostgresConnectionManagerLogging:
    LOGGER = "tractusx_sdk.dataspace.managers.connection.database.postgres_connection_manager"

    @pytest.fixture
    def manager(self):
        engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
        # The dynamic table pattern only supports one table name per process: the existing tests use this one
        return _ConcretePostgresConnectionManager(engine=engine, table_name="test_edr_connections")

    def test_the_whole_lifecycle_is_logged_without_the_edr(self, manager, caplog):
        with caplog.at_level(logging.DEBUG):
            manager.add_connection(*KEYS, _entry())
            manager.add_connection(*KEYS, _entry())
            assert manager.get_connection(*KEYS)
            assert manager.get_connection("BPNL9", ADDRESS, "q", "p") == {}
            assert manager.get_connection_transfer_id(*KEYS) == "tp-1"
            assert manager.get_connection_transfer_id("BPNL9", ADDRESS, "q", "p") is None
            assert manager.delete_connection(*KEYS) is True
            assert manager.delete_connection(*KEYS) is False

        messages = [r.getMessage() for r in _records(caplog, self.LOGGER)]
        assert any("A new EDR entry was saved" in m for m in messages)
        assert any("already stored" in m for m in messages)
        assert any("Found the EDR" in m for m in messages)
        assert any("No EDR stored for" in m for m in messages)
        assert any("No transfer id stored" in m for m in messages)
        assert any("Deleted EDR entry" in m for m in messages)
        assert any("No EDR found to delete" in m for m in messages)
        deleted = [r for r in _records(caplog, self.LOGGER) if "Deleted EDR entry" in r.getMessage()][0]
        assert deleted.transfer_id == "tp-1"
        assert SECRET not in _dump(caplog)

    def test_an_entry_without_transfer_id_is_logged_before_it_is_raised(self, manager, caplog):
        with caplog.at_level(logging.DEBUG), pytest.raises(ConnectionManagerError):
            manager.add_connection(*KEYS, {"providerId": "x"})
        assert _records(caplog, self.LOGGER)[-1].levelno == logging.ERROR


class TestFileSystemConnectionManagerLogging:
    LOGGER = "tractusx_sdk.dataspace.managers.connection.file_system.file_system_connection_manager"

    def test_saving_and_reloading_are_logged_and_an_unchanged_state_is_silent(self, tmp_path, caplog):
        path = str(tmp_path / "cache.json")
        with caplog.at_level(logging.DEBUG):
            manager = FileSystemConnectionManager(path=path, persist_interval=3600)
            manager.add_connection(*KEYS, _entry())
            manager._save_to_file()
            manager._save_to_file()
            manager._last_loaded_hash = None
            manager._load_if_updated()
            manager.stop()

        messages = [r.getMessage() for r in _records(caplog, self.LOGGER)]
        assert sum("Saved the connections" in m for m in messages) == 1
        assert sum("Reloaded the connections" in m for m in messages) == 1
        assert any("every 3600 seconds" in m for m in messages)
        assert any("Stopping the persistence thread" in m for m in messages)
        assert SECRET not in _dump(caplog)


@pytest.fixture
def oauth():
    oauth = Mock()
    oauth.connected = True
    oauth.add_auth_header.side_effect = lambda headers: {**headers, "Authorization": f"Bearer {SECRET}"}
    return oauth


class TestDiscoveryFinderServiceLogging:
    LOGGER = "tractusx_sdk.dataspace.services.discovery.discovery_finder_service"
    URL = f"https://finder.example.com/discovery?key={SECRET}"
    HTTP = "tractusx_sdk.dataspace.services.discovery.discovery_finder_service.HttpTools"

    def _service(self, oauth):
        return DiscoveryFinderService(url=self.URL, oauth=oauth)

    def test_a_lookup_is_logged_without_credentials(self, oauth, caplog):
        response = Mock(status_code=200)
        response.json.return_value = {"endpoints": [{"type": "bpn", "endpointAddress": "https://bpn.example.com"}]}
        with patch(self.HTTP) as http, caplog.at_level(logging.DEBUG):
            http.do_post.return_value = response
            assert self._service(oauth).find_discovery_urls(["bpn"]) == {"bpn": "https://bpn.example.com"}

        looking, found = _records(caplog, self.LOGGER)
        assert looking.url == "https://finder.example.com/discovery"
        assert "[Discovery Finder Service] Found 1 discovery endpoint(s): ['bpn']" == found.getMessage()
        assert SECRET not in _dump(caplog)

    def test_a_disconnected_oauth_is_logged_before_it_is_raised(self, oauth, caplog):
        oauth.connected = False
        with caplog.at_level(logging.DEBUG), pytest.raises(ConnectionError):
            self._service(oauth).find_discovery_urls(["bpn"])
        assert _records(caplog, self.LOGGER)[-1].levelno == logging.ERROR

    @pytest.mark.parametrize("response, status", [(Mock(status_code=503), 503), (None, None)])
    def test_an_unsuccessful_answer_is_logged_before_it_is_raised(self, oauth, caplog, response, status):
        with patch(self.HTTP) as http, caplog.at_level(logging.DEBUG), pytest.raises(DiscoveryError):
            http.do_post.return_value = response
            self._service(oauth).find_discovery_urls(["bpn"])
        error = _records(caplog, self.LOGGER)[-1]
        assert error.levelno == logging.ERROR
        assert getattr(error, "status_code", None) == status

    def test_an_answer_without_endpoints_is_logged_before_it_is_raised(self, oauth, caplog):
        response = Mock(status_code=200)
        response.json.return_value = {"endpoints": []}
        with patch(self.HTTP) as http, caplog.at_level(logging.DEBUG), pytest.raises(DiscoveryEndpointNotFoundError):
            http.do_post.return_value = response
            self._service(oauth).find_discovery_urls(["bpn"])
        assert _records(caplog, self.LOGGER)[-1].levelno == logging.ERROR


class _FakeDiscoveryService(ConnectorDiscoveryService):
    pass


class TestBaseDiscoveryServiceLogging:
    LOGGER = "tractusx_sdk.dataspace.services.discovery.base_discovery_service"
    URL = f"https://discovery.example.com/api?token={SECRET}"

    def _service(self, oauth, finder):
        return ConnectorDiscoveryService(oauth=oauth, discovery_finder_service=finder, cache_timeout_seconds=60)

    def test_a_refresh_and_a_cache_hit_never_log_the_query_string(self, oauth, caplog):
        finder = Mock()
        finder.find_discovery_urls.return_value = {"bpn": self.URL}
        service = self._service(oauth, finder)
        with caplog.at_level(logging.DEBUG):
            assert service._get_or_update_discovery_url() == self.URL
            assert service._get_or_update_discovery_url() == self.URL

        messages = [r.getMessage() for r in _records(caplog, self.LOGGER)]
        assert any("not cached yet" in m for m in messages)
        assert any("Updated cache with new discovery URL" in m for m in messages)
        assert any("Using cached discovery URL" in m for m in messages)
        assert SECRET not in _dump(caplog)

    def test_a_failed_refresh_without_a_cached_url_is_logged_before_it_is_raised(self, oauth, caplog):
        finder = Mock()
        finder.find_discovery_urls.side_effect = DiscoveryError("down")
        with caplog.at_level(logging.DEBUG), pytest.raises(DiscoveryError):
            self._service(oauth, finder)._get_or_update_discovery_url()
        assert _records(caplog, self.LOGGER)[-1].levelno == logging.ERROR

    def test_a_failed_refresh_falls_back_to_the_cached_url_with_a_warning(self, oauth, caplog):
        finder = Mock()
        finder.find_discovery_urls.return_value = {"bpn": self.URL}
        service = self._service(oauth, finder)
        service._get_or_update_discovery_url()
        service.discovery_cache["bpn"]["timestamp"] = 0
        finder.find_discovery_urls.side_effect = DiscoveryError("down")
        with caplog.at_level(logging.DEBUG):
            assert service._get_or_update_discovery_url() == self.URL
        warning = _records(caplog, self.LOGGER)[-1]
        assert warning.levelno == logging.WARNING and warning.url == "https://discovery.example.com/api"
        assert SECRET not in _dump(caplog)


class TestConnectorDiscoveryServiceLogging:
    LOGGER = "tractusx_sdk.dataspace.services.discovery.connector_discovery_service"
    HTTP = "tractusx_sdk.dataspace.services.discovery.connector_discovery_service.HttpTools"

    @pytest.fixture
    def service(self, oauth):
        service = ConnectorDiscoveryService(oauth=oauth, discovery_finder_service=Mock())
        with patch.object(ConnectorDiscoveryService, "_get_or_update_discovery_url",
                          return_value=f"https://cd.example.com/x?k={SECRET}"):
            yield service

    def _answer(self, payload, status=200):
        response = Mock(status_code=status)
        response.json.return_value = payload
        return response

    def test_found_endpoints_are_logged_at_debug(self, service, caplog):
        with patch(self.HTTP) as http, caplog.at_level(logging.DEBUG):
            http.do_post.return_value = self._answer([{"bpn": "BPNL1", "connectorEndpoint": ["a", "b"]}])
            assert service.find_connector_by_bpn("BPNL1") == ["a", "b"]

        looking, found = _records(caplog, self.LOGGER)
        assert looking.bpn == "BPNL1" and found.levelno == logging.DEBUG
        assert "Found 2 connector endpoint(s)" in found.getMessage()
        assert SECRET not in _dump(caplog)

    def test_a_bpn_without_endpoints_key_falls_back_to_an_empty_list_at_debug(self, service, caplog):
        with patch(self.HTTP) as http, caplog.at_level(logging.DEBUG):
            http.do_post.return_value = self._answer([{"bpn": "BPNL1"}])
            assert service.find_connector_by_bpn("BPNL1") == []
        assert _records(caplog, self.LOGGER)[-1].levelno == logging.DEBUG

    def test_an_unknown_bpn_is_an_expected_outcome_logged_at_debug(self, service, caplog):
        with patch(self.HTTP) as http, caplog.at_level(logging.DEBUG):
            http.do_post.return_value = self._answer([{"bpn": "OTHER", "connectorEndpoint": ["a"]}])
            assert service.find_connector_by_bpn("BPNL1") is None
        assert _records(caplog, self.LOGGER)[-1].levelno == logging.DEBUG
        assert [r for r in caplog.records if r.levelno >= logging.INFO] == []

    def test_an_unsuccessful_answer_is_logged_before_it_is_raised(self, service, caplog):
        with patch(self.HTTP) as http, caplog.at_level(logging.DEBUG), pytest.raises(DiscoveryError):
            http.do_post.return_value = self._answer([], status=500)
            service.find_connector_by_bpn("BPNL1")
        error = _records(caplog, self.LOGGER)[-1]
        assert (error.levelno, error.status_code, error.url) == (logging.ERROR, 500, "https://cd.example.com/x")
        assert SECRET not in _dump(caplog)


class TestBpnDiscoveryServiceLogging:
    LOGGER = "tractusx_sdk.industry.services.discovery.bpn_discovery_service"
    HTTP = "tractusx_sdk.industry.services.discovery.bpn_discovery_service.HttpTools"

    @pytest.fixture
    def service(self, oauth):
        service = BpnDiscoveryService(oauth=oauth, discovery_finder_service=Mock())
        with patch.object(BpnDiscoveryService, "_get_or_update_discovery_url",
                          return_value=f"https://bpn.example.com/api?k={SECRET}"):
            yield service

    def _answer(self, payload, status=200):
        response = Mock(status_code=status)
        response.json.return_value = payload
        return response

    def test_a_search_is_logged_without_the_identifiers_nor_the_query_string(self, service, caplog):
        with patch(self.HTTP) as http, caplog.at_level(logging.DEBUG):
            http.do_post_with_session.return_value = self._answer({"bpns": [{"value": "BPNL1"}]})
            assert service.find_bpns(["secret-part-id"]) == ["BPNL1"]
        assert "secret-part-id" not in _dump(caplog)

    def test_no_result_is_an_expected_outcome_logged_at_debug(self, service, caplog):
        with patch(self.HTTP) as http, caplog.at_level(logging.DEBUG):
            http.do_post_with_session.return_value = self._answer({"bpns": []})
            assert service.find_bpns(["a"]) is None
            assert service.find_bpns_multi_type([{"type": "t", "keys": ["a"]}]) is None
        assert [r for r in _records(caplog, self.LOGGER) if r.levelno >= logging.INFO] == []
        assert sum("No BPN was found" in r.getMessage() for r in _records(caplog, self.LOGGER)) == 2

    @pytest.mark.parametrize("status, expected", [(401, "Unauthorized"), (500, "Unexpected status 500")])
    def test_a_failed_answer_is_logged_before_it_is_raised(self, service, caplog, status, expected):
        with patch(self.HTTP) as http, caplog.at_level(logging.DEBUG), pytest.raises(Exception):
            http.do_post_with_session.return_value = self._answer({}, status=status)
            service.search_bpns(["a"])
        error = _records(caplog, self.LOGGER)[-1]
        assert error.levelno == logging.ERROR and error.status_code == status and expected in error.getMessage()

    def test_no_response_is_logged_before_it_is_raised(self, service, caplog):
        with patch(self.HTTP) as http, caplog.at_level(logging.DEBUG), pytest.raises(DiscoveryError):
            http.do_post_with_session.return_value = None
            service.search_bpns(["a"])
        assert _records(caplog, self.LOGGER)[-1].levelno == logging.ERROR

    @pytest.mark.parametrize("filters", [[], "x", [{"type": "t"}], [{"type": "t", "keys": []}]])
    def test_an_invalid_search_is_a_warning_before_it_is_raised(self, service, caplog, filters):
        with caplog.at_level(logging.DEBUG), pytest.raises(ValueError):
            service.search_bpns_multi_type(filters)
        assert _records(caplog, self.LOGGER)[-1].levelno == logging.WARNING

    def test_registering_and_deleting_identifiers_are_milestones(self, service, caplog):
        with patch(self.HTTP) as http, caplog.at_level(logging.DEBUG):
            http.do_post_with_session.return_value = self._answer({}, status=201)
            http.do_delete_with_session.return_value = self._answer({}, status=204)
            service.set_identifier("secret-part-id")
            service.set_multiple_identifiers(["secret-part-id", "other-secret"])
            service.delete_bpn_identifier_by_id("res-1")

        infos = [r.getMessage() for r in _records(caplog, self.LOGGER) if r.levelno == logging.INFO]
        assert len(infos) == 3 and "Registered 2 identifier(s)" in infos[1] and "'res-1'" in infos[2]
        assert "secret-part-id" not in _dump(caplog) and "other-secret" not in _dump(caplog)

    def test_the_discovery_url_resolution_is_logged(self, oauth, caplog):
        service = BpnDiscoveryService(oauth=oauth, discovery_finder_service=Mock())
        finder = Mock()
        finder.find_discovery_urls.return_value = {"k": "https://bpn.example.com" + service.base_path}
        with caplog.at_level(logging.DEBUG):
            assert service.get_discovery_url(finder, "k") == "https://bpn.example.com" + service.base_path
        assert any("already ends with the base path" in r.getMessage() for r in _records(caplog, self.LOGGER))

        finder.find_discovery_urls.return_value = {}
        with caplog.at_level(logging.DEBUG), pytest.raises(DiscoveryEndpointNotFoundError):
            service.get_discovery_url(finder, "k")
        assert _records(caplog, self.LOGGER)[-1].levelno == logging.ERROR
