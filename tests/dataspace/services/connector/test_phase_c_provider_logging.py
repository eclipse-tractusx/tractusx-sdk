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

"""The log records of the connector provider service, the service factory and the service wiring."""

import logging
from unittest.mock import Mock, patch

import pytest

from tractusx_sdk.dataspace.managers.auth_manager import AuthManager
from tractusx_sdk.dataspace.services.connector import BaseConnectorProviderService, ServiceFactory
from tractusx_sdk.dataspace.services.connector.base_connector_service import BaseConnectorService
from tractusx_sdk.dataspace.services.connector.service_factory import ServiceType

SECRET = "s3cr3t-value"
PROVIDER = "tractusx_sdk.dataspace.services.connector.base_connector_provider"
FACTORY = "tractusx_sdk.dataspace.services.connector.service_factory"


def _dump(caplog) -> str:
    return "\n".join(f"{r.getMessage()} {r.__dict__} {r.exc_text or ''}" for r in caplog.records)


def _records(caplog, name):
    return [r for r in caplog.records if r.name == name]


@pytest.fixture
def provider():
    provider = BaseConnectorProviderService(dataspace_version="jupiter", base_url="https://control.example.com", dma_path="/management",
                                            headers={"X-Api-Key": f"api-key-{SECRET}"})
    provider._asset_controller = Mock()
    provider._contract_definition_controller = Mock()
    provider._policy_controller = Mock()
    return provider


class TestProviderLogging:

    def test_creation_is_logged(self, caplog):
        with caplog.at_level(logging.DEBUG):
            BaseConnectorProviderService(dataspace_version="jupiter", base_url="https://c.example.com", dma_path="/m",
                                         headers={"X-Api-Key": f"api-key-{SECRET}"})
        assert any("Provider service created for dataspace version jupiter" in r.getMessage() for r in _records(caplog, PROVIDER))
        assert SECRET not in _dump(caplog)

    def test_an_asset_is_logged_with_its_id_and_never_the_backend_credentials(self, provider, caplog):
        provider._asset_controller.create.return_value = Mock(status_code=200, json=lambda: {"ok": True})
        with caplog.at_level(logging.DEBUG):
            provider.create_asset(
                asset_id="asset-1", base_url=f"https://user:{SECRET}@backend.example.com/api?token={SECRET}", dct_type="t",
                headers={"X-Api-Key": f"backend-{SECRET}", "Authorization": f"Bearer {SECRET}"},
                oauth2_config={"tokenUrl": "https://idp/token", "clientId": "c", "clientSecretKey": f"vault-{SECRET}"})

        records = _records(caplog, PROVIDER)
        creating = records[0]
        assert creating.getMessage() == "Creating asset asset-1 at https://backend.example.com/api."
        assert creating.asset_id == "asset-1" and creating.url == "https://backend.example.com/api"
        assert any(r.levelno == logging.INFO and "created successfully" in r.getMessage() and r.asset_id == "asset-1" for r in records)
        assert SECRET not in _dump(caplog)

    def test_an_asset_without_a_context_notes_the_default(self, provider, caplog):
        provider._asset_controller.create.return_value = Mock(status_code=200, json=lambda: {})
        with caplog.at_level(logging.DEBUG):
            provider.create_asset(asset_id="asset-1", base_url="https://b.example.com", dct_type="t")
        assert any("No context given for asset asset-1" in r.getMessage() for r in _records(caplog, PROVIDER))

    def test_an_incomplete_oauth2_config_is_logged_before_it_is_raised(self, provider, caplog):
        with caplog.at_level(logging.DEBUG), pytest.raises(ValueError, match="OAuth2"):
            provider.create_asset(asset_id="asset-1", base_url="https://b.example.com", dct_type="t", oauth2_config={"clientId": "c"})
        error = _records(caplog, PROVIDER)[-1]
        assert (error.levelno, error.asset_id) == (logging.ERROR, "asset-1")

    def test_a_rejected_asset_is_logged_with_its_status_before_it_is_raised(self, provider, caplog):
        provider._asset_controller.create.return_value = Mock(status_code=409, text="conflict")
        with caplog.at_level(logging.DEBUG), pytest.raises(ValueError):
            provider.create_asset(asset_id="asset-1", base_url="https://b.example.com", dct_type="t")
        error = _records(caplog, PROVIDER)[-1]
        assert (error.levelno, error.asset_id, error.status_code) == (logging.ERROR, "asset-1", 409)

    def test_a_contract_is_logged_with_its_asset_and_policy(self, provider, caplog):
        provider._contract_definition_controller.create.return_value = Mock(status_code=200, json=lambda: {})
        with caplog.at_level(logging.DEBUG):
            provider.create_contract("contract-1", "usage-1", "access-1", "asset-1")
        infos = [r for r in _records(caplog, PROVIDER) if r.levelno == logging.INFO]
        assert [(r.asset_id, r.policy_id) for r in infos] == [("asset-1", "usage-1")] * 2

    def test_a_rejected_contract_is_logged_before_it_is_raised(self, provider, caplog):
        provider._contract_definition_controller.create.return_value = Mock(status_code=400, text="bad")
        with caplog.at_level(logging.DEBUG), pytest.raises(ValueError):
            provider.create_contract("contract-1", "usage-1", "access-1", "asset-1")
        error = _records(caplog, PROVIDER)[-1]
        assert (error.levelno, error.status_code, error.asset_id) == (logging.ERROR, 400, "asset-1")

    def test_a_policy_is_logged_with_its_id_and_a_rejection_before_it_is_raised(self, provider, caplog):
        provider._policy_controller.create.return_value = Mock(status_code=200, json=lambda: {})
        with caplog.at_level(logging.DEBUG):
            provider.create_policy("policy-1")
        assert [r.policy_id for r in _records(caplog, PROVIDER) if r.levelno == logging.INFO] == ["policy-1"] * 2

        caplog.clear()
        provider._policy_controller.create.return_value = Mock(status_code=500, text="boom")
        with caplog.at_level(logging.DEBUG), pytest.raises(ValueError):
            provider.create_policy("policy-1")
        error = _records(caplog, PROVIDER)[-1]
        assert (error.levelno, error.policy_id, error.status_code) == (logging.ERROR, "policy-1", 500)


class TestServiceFactoryLogging:

    def test_creating_a_service_is_a_milestone(self, caplog):
        with caplog.at_level(logging.DEBUG):
            ServiceFactory.get_connector_provider_service(dataspace_version="jupiter", base_url="https://c.example.com", dma_path="/m")
        info = [r for r in _records(caplog, FACTORY) if r.levelno == logging.INFO][0]
        assert info.getMessage() == "Creating the ConnectorProvider service for dataspace version jupiter"
        assert (info.dataspace_version, info.model) == ("jupiter", "ConnectorProvider")

    def test_an_unsupported_version_is_logged_before_it_is_raised(self, caplog):
        with caplog.at_level(logging.DEBUG), pytest.raises(ValueError):
            ServiceFactory._get_service_builder(ServiceType.CONNECTOR_CONSUMER, "nope")
        error = _records(caplog, FACTORY)[-1]
        assert (error.levelno, error.dataspace_version) == (logging.ERROR, "nope")

    def test_a_missing_service_class_and_an_import_failure_are_logged_with_their_traceback(self, caplog):
        with patch(f"{FACTORY}.import_module", return_value=object()), caplog.at_level(logging.DEBUG), pytest.raises(AttributeError):
            ServiceFactory._get_service_builder(ServiceType.CONNECTOR_CONSUMER, "jupiter")
        assert _records(caplog, FACTORY)[-1].exc_info is not None

        caplog.clear()
        with patch(f"{FACTORY}.import_module", side_effect=ImportError("x")), caplog.at_level(logging.DEBUG), pytest.raises(ImportError):
            ServiceFactory._get_service_builder(ServiceType.CONNECTOR_CONSUMER, "jupiter")
        assert _records(caplog, FACTORY)[-1].exc_info is not None


class TestServiceWiringLogging:

    def test_building_a_service_logs_the_names_of_its_settings_but_not_their_values(self, caplog):
        builder = BaseConnectorProviderService.builder()
        builder.dataspace_version("jupiter").base_url("https://c.example.com").dma_path("/m").headers({"X-Api-Key": f"api-key-{SECRET}"})
        with caplog.at_level(logging.DEBUG):
            builder.build()
        record = [r for r in caplog.records if r.name == "tractusx_sdk.dataspace.services.service"][0]
        assert record.getMessage() == "Building BaseConnectorProviderService with the settings ['base_url', 'dataspace_version', 'dma_path', 'headers']"
        assert record.dataspace_version == "jupiter"
        assert SECRET not in _dump(caplog)

    def test_the_connector_service_logs_the_kind_of_auth_manager_and_never_its_key(self, caplog):
        consumer, provider = Mock(), Mock()
        auth = AuthManager(configured_api_key=f"api-key-{SECRET}", auth_enabled=True)
        with caplog.at_level(logging.DEBUG):
            BaseConnectorService(dataspace_version="jupiter", base_url="https://c.example.com", dma_path="/m",
                                 consumer_service=consumer, provider_service=provider, auth_manager=auth)
        messages = [r.getMessage() for r in caplog.records if r.name == "tractusx_sdk.dataspace.services.connector.base_connector_service"]
        assert messages == ["[Connector Service] Adding the authentication headers of a AuthManager",
                            "[Connector Service] Connector service created for dataspace version jupiter"]
        assert SECRET not in _dump(caplog)
