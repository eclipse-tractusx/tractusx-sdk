#################################################################################
# Eclipse Tractus-X - Software Development KIT
#
# Copyright (c) 2025,2026 LKS NEXT
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
## Code created partially using a LLM and reviewed by a human committer

import logging

import pytest
from unittest.mock import Mock, patch
from tractusx_sdk.dataspace.services.connector import BaseConnectorProviderService
from tractusx_sdk.dataspace.controllers.connector.controller_factory import ControllerType


@pytest.fixture
def mock_dma_adapter():
    return Mock()


@pytest.fixture
def mock_controllers():
    asset_controller = Mock()
    contract_definition_controller = Mock()
    policy_controller = Mock()
    return {
        ControllerType.ASSET: asset_controller,
        ControllerType.CONTRACT_DEFINITION: contract_definition_controller,
        ControllerType.POLICY: policy_controller
    }


@pytest.fixture
def service(mock_dma_adapter, mock_controllers):
    with patch("tractusx_sdk.dataspace.adapters.connector.AdapterFactory.get_dma_adapter", return_value=mock_dma_adapter):
        with patch("tractusx_sdk.dataspace.controllers.connector.ControllerFactory.get_dma_controllers_for_version") as mock_get_controllers:
            mock_get_controllers.return_value = mock_controllers
            svc = BaseConnectorProviderService(
                dataspace_version="jupiter",
                base_url="http://test",
                dma_path="/dma"
            )
            yield svc


@pytest.mark.parametrize("removed", [{"verbose": True}, {"debug": True}, {"logger": logging.getLogger("x")}])
def test_the_removed_logging_arguments_are_rejected(removed):
    with pytest.raises(TypeError):
        BaseConnectorProviderService(dataspace_version="jupiter", base_url="http://test", dma_path="/dma", **removed)


@patch("tractusx_sdk.dataspace.models.connector.ModelFactory.get_asset_model")
def test_create_asset_success(mock_get_asset_model, service):
    mock_response = Mock(status_code=200)
    mock_response.json.return_value = {"asset": "ok"}
    service._asset_controller.create.return_value = mock_response

    mock_get_asset_model.return_value = {"mock": "asset"}

    result = service.create_asset(asset_id="123", base_url="http://test", dct_type="test")

    assert result == {"asset": "ok"}
    service._asset_controller.create.assert_called_once()


@patch("tractusx_sdk.dataspace.models.connector.ModelFactory.get_asset_model")
def test_create_asset_failure_raises(mock_get_asset_model, service):
    mock_response = Mock(status_code=400, text="Bad Request")
    service._asset_controller.create.return_value = mock_response
    mock_get_asset_model.return_value = {"mock": "asset"}

    with pytest.raises(ValueError, match="Failed to create asset"):
        service.create_asset(asset_id="123", base_url="http://test", dct_type="test")


@patch("tractusx_sdk.dataspace.models.connector.ModelFactory.get_contract_definition_model")
def test_create_contract_success(mock_get_contract_model, service):
    mock_response = Mock(status_code=200)
    mock_response.json.return_value = {"contract": "ok"}
    service._contract_definition_controller.create.return_value = mock_response

    mock_get_contract_model.return_value = {"mock": "contract"}

    result = service.create_contract(
        contract_id="contract1",
        usage_policy_id="usage",
        access_policy_id="access",
        asset_id="asset"
    )
    assert result == {"contract": "ok"}
    service._contract_definition_controller.create.assert_called_once()


@patch("tractusx_sdk.dataspace.models.connector.ModelFactory.get_contract_definition_model")
def test_create_contract_failure_raises(mock_get_contract_model, service):
    mock_response = Mock(status_code=400)
    service._contract_definition_controller.create.return_value = mock_response
    mock_get_contract_model.return_value = {"mock": "contract"}

    with pytest.raises(ValueError, match="Failed to create contract"):
        service.create_contract(
            contract_id="contract1",
            usage_policy_id="usage",
            access_policy_id="access",
            asset_id="asset"
        )


@patch("tractusx_sdk.dataspace.models.connector.ModelFactory.get_policy_model")
def test_create_policy_success(mock_get_policy_model, service):
    mock_response = Mock(status_code=200)
    mock_response.json.return_value = {"policy": "ok"}
    service._policy_controller.create.return_value = mock_response

    mock_get_policy_model.return_value = {"mock": "policy"}

    result = service.create_policy(policy_id="policy1")
    assert result == {"policy": "ok"}
    service._policy_controller.create.assert_called_once()


@patch("tractusx_sdk.dataspace.models.connector.ModelFactory.get_policy_model")
def test_create_policy_failure_raises(mock_get_policy_model, service):
    mock_response = Mock(status_code=400)
    service._policy_controller.create.return_value = mock_response
    mock_get_policy_model.return_value = {"mock": "policy"}

    with pytest.raises(ValueError, match="Failed to create policy"):
        service.create_policy(policy_id="policy1")


PROVIDER_LOGGER = "tractusx_sdk.dataspace.services.connector.base_connector_provider"


@patch("tractusx_sdk.dataspace.models.connector.ModelFactory.get_asset_model")
def test_create_asset_logs_at_info_level(mock_get_asset_model, service, caplog):
    service._asset_controller = Mock()
    service._asset_controller.create.return_value = Mock(status_code=200, json=lambda: {"asset": "ok"})
    mock_get_asset_model.return_value = {"mock": "asset"}

    with caplog.at_level(logging.INFO, logger=PROVIDER_LOGGER):
        service.create_asset(asset_id="123", base_url="http://test", dct_type="test")

    assert "Creating asset 123 at http://test." in caplog.text
    assert "Asset 123 created successfully." in caplog.text


@patch("tractusx_sdk.dataspace.models.connector.ModelFactory.get_asset_model")
def test_create_asset_is_silent_when_the_level_is_above_info(mock_get_asset_model, service, caplog):
    service._asset_controller = Mock()
    service._asset_controller.create.return_value = Mock(status_code=200, json=lambda: {"asset": "ok"})
    mock_get_asset_model.return_value = {"mock": "asset"}

    with caplog.at_level(logging.WARNING, logger=PROVIDER_LOGGER):
        service.create_asset(asset_id="123", base_url="http://test", dct_type="test")

    assert caplog.text == ""


@patch("tractusx_sdk.dataspace.models.connector.ModelFactory.get_asset_model")
def test_create_asset_request_summary_is_logged_only_at_debug_level_and_never_the_payload(mock_get_asset_model, service, caplog):
    service._asset_controller = Mock()
    service._asset_controller.create.return_value = Mock(status_code=200, json=lambda: {"asset": "ok"})
    asset = Mock()
    asset.to_data.return_value = {"payload": "visible"}
    mock_get_asset_model.return_value = asset

    with caplog.at_level(logging.INFO, logger=PROVIDER_LOGGER):
        service.create_asset(asset_id="123", base_url="http://test", dct_type="test")
    assert "[ASSET REQUEST]" not in caplog.text

    caplog.clear()
    with caplog.at_level(logging.DEBUG, logger=PROVIDER_LOGGER):
        service.create_asset(asset_id="123", base_url="http://test", dct_type="test",
                             headers={"X-Api-Key": "backend-s3cr3t"},
                             oauth2_config={"tokenUrl": "https://idp/token", "clientId": "c", "clientSecretKey": "vault-ref-s3cr3t"})
    assert "[ASSET REQUEST]: asset 123, data address type HttpData, 1 backend header(s), OAuth2: True" in caplog.text
    # The data address holds the backend credentials: the payload is never logged
    asset.to_data.assert_not_called()
    assert "s3cr3t" not in "\n".join(f"{r.getMessage()} {r.__dict__}" for r in caplog.records)


@patch("tractusx_sdk.dataspace.models.connector.ModelFactory.get_asset_model")
def test_create_asset_failure_is_logged_as_an_error(mock_get_asset_model, service, caplog):
    service._asset_controller.create.return_value = Mock(status_code=400, text="Bad Request")
    mock_get_asset_model.return_value = {"mock": "asset"}

    with caplog.at_level(logging.ERROR, logger=PROVIDER_LOGGER):
        with pytest.raises(ValueError, match="Failed to create asset"):
            service.create_asset(asset_id="123", base_url="http://test", dct_type="test")

    assert "Failed to create asset 123: Bad Request" in caplog.text


@patch("tractusx_sdk.dataspace.models.connector.ModelFactory.get_asset_model")
def test_create_asset_with_dct_subject(mock_get_asset_model, service):
    """create_asset passes dct:subject as a property when dct_subject is provided."""
    captured_properties = {}

    def capture_call(**kwargs):
        captured_properties.update(kwargs.get("properties", {}))
        return Mock(to_data=lambda: "{}")

    mock_get_asset_model.side_effect = capture_call
    mock_response = Mock(status_code=200)
    mock_response.json.return_value = {"@id": "123"}
    service._asset_controller.create.return_value = mock_response

    service.create_asset(
        asset_id="123",
        base_url="http://test",
        dct_type="cx-taxo:CCMAPI",
        dct_subject="cx-taxo:CompanyCertificateManagementNotificationApi",
    )

    assert captured_properties["dct:type"] == {"@id": "cx-taxo:CCMAPI"}
    assert captured_properties["dct:subject"] == {"@id": "cx-taxo:CompanyCertificateManagementNotificationApi"}


@patch("tractusx_sdk.dataspace.models.connector.ModelFactory.get_asset_model")
def test_create_asset_without_dct_subject_omits_property(mock_get_asset_model, service):
    """When dct_subject is not provided, dct:subject is absent from the properties."""
    captured_properties = {}

    def capture_call(**kwargs):
        captured_properties.update(kwargs.get("properties", {}))
        return Mock(to_data=lambda: "{}")

    mock_get_asset_model.side_effect = capture_call
    mock_response = Mock(status_code=200)
    mock_response.json.return_value = {"@id": "123"}
    service._asset_controller.create.return_value = mock_response

    service.create_asset(
        asset_id="123",
        base_url="http://test",
        dct_type="cx-taxo:SubmodelBundle",
    )

    assert "dct:subject" not in captured_properties


@patch("tractusx_sdk.dataspace.models.connector.ModelFactory.get_asset_model")
def test_create_asset_dct_subject_without_dct_type(mock_get_asset_model, service):
    """dct_subject can be set independently of dct_type."""
    captured_properties = {}

    def capture_call(**kwargs):
        captured_properties.update(kwargs.get("properties", {}))
        return Mock(to_data=lambda: "{}")

    mock_get_asset_model.side_effect = capture_call
    mock_response = Mock(status_code=200)
    mock_response.json.return_value = {"@id": "123"}
    service._asset_controller.create.return_value = mock_response

    service.create_asset(
        asset_id="123",
        base_url="http://test",
        dct_subject="cx-taxo:CompanyCertificateManagementNotificationApi",
    )

    assert "dct:type" not in captured_properties
    assert captured_properties["dct:subject"] == {"@id": "cx-taxo:CompanyCertificateManagementNotificationApi"}


@patch("tractusx_sdk.dataspace.models.connector.ModelFactory.get_asset_model")
def test_create_asset_with_oauth2_config(mock_get_asset_model, service):
    mock_response = Mock(status_code=200)
    mock_response.json.return_value = {"asset": "ok"}
    service._asset_controller.create.return_value = mock_response

    mock_get_asset_model.return_value = {"mock": "asset"}

    oauth2_config = {
        "tokenUrl": "https://keycloak.example.com/token",
        "clientId": "my-client-id",
        "clientSecretKey": "my-vault-secret-key"
    }

    result = service.create_asset(
        asset_id="123",
        base_url="http://test",
        dct_type="test",
        oauth2_config=oauth2_config
    )

    assert result == {"asset": "ok"}
    service._asset_controller.create.assert_called_once()

    # Verify the data_address passed to ModelFactory includes OAuth2 config
    call_kwargs = mock_get_asset_model.call_args[1]
    data_address = call_kwargs["data_address"]
    assert data_address["edc:oauth2:tokenUrl"] == "https://keycloak.example.com/token"
    assert data_address["edc:oauth2:clientId"] == "my-client-id"
    assert data_address["edc:oauth2:clientSecretKey"] == "my-vault-secret-key"


@patch("tractusx_sdk.dataspace.models.connector.ModelFactory.get_asset_model")
def test_create_asset_with_oauth2_config_without_secret(mock_get_asset_model, service):
    mock_response = Mock(status_code=200)
    mock_response.json.return_value = {"asset": "ok"}
    service._asset_controller.create.return_value = mock_response

    mock_get_asset_model.return_value = {"mock": "asset"}

    # Provide tokenUrl and clientId, omit clientSecretKey (optional)
    oauth2_config = {
        "tokenUrl": "https://keycloak.example.com/token",
        "clientId": "my-client-id",
        "scope": "openid profile"
    }

    result = service.create_asset(
        asset_id="123",
        base_url="http://test",
        dct_type="test",
        oauth2_config=oauth2_config
    )

    assert result == {"asset": "ok"}

    # Verify only provided OAuth2 fields are in data_address
    call_kwargs = mock_get_asset_model.call_args[1]
    data_address = call_kwargs["data_address"]
    assert data_address["edc:oauth2:tokenUrl"] == "https://keycloak.example.com/token"
    assert data_address["edc:oauth2:clientId"] == "my-client-id"
    assert data_address["edc:oauth2:scope"] == "openid profile"


@patch("tractusx_sdk.dataspace.models.connector.ModelFactory.get_asset_model")
def test_create_asset_with_oauth2_config_missing_required_fields_raises(mock_get_asset_model, service):
    mock_response = Mock(status_code=200)
    mock_response.json.return_value = {"asset": "ok"}
    service._asset_controller.create.return_value = mock_response

    mock_get_asset_model.return_value = {"mock": "asset"}

    with pytest.raises(ValueError, match="require at least 'tokenUrl' and 'clientId'"):
        service.create_asset(
            asset_id="123",
            base_url="http://test",
            dct_type="test",
            oauth2_config={"clientId": "my-client-id"}
        )

    with pytest.raises(ValueError, match="require at least 'tokenUrl' and 'clientId'"):
        service.create_asset(
            asset_id="123",
            base_url="http://test",
            dct_type="test",
            oauth2_config={"tokenUrl": "https://keycloak.example.com/token"}
        )


@patch("tractusx_sdk.dataspace.models.connector.ModelFactory.get_asset_model")
def test_create_asset_with_oauth2_config_empty_required_fields_raises(mock_get_asset_model, service):
    """Empty 'tokenUrl' or 'clientId' values are rejected, not only missing keys."""
    mock_response = Mock(status_code=200)
    mock_response.json.return_value = {"asset": "ok"}
    service._asset_controller.create.return_value = mock_response

    mock_get_asset_model.return_value = {"mock": "asset"}

    with pytest.raises(ValueError, match="require at least 'tokenUrl' and 'clientId'"):
        service.create_asset(
            asset_id="123",
            base_url="http://test",
            dct_type="test",
            oauth2_config={"tokenUrl": "", "clientId": "my-client-id"}
        )

    with pytest.raises(ValueError, match="require at least 'tokenUrl' and 'clientId'"):
        service.create_asset(
            asset_id="123",
            base_url="http://test",
            dct_type="test",
            oauth2_config={"tokenUrl": "https://keycloak.example.com/token", "clientId": ""}
        )
