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
                dma_path="/dma",
                debug=True
            )
            yield svc


@pytest.fixture
def service_debug_false(mock_dma_adapter, mock_controllers):
    with patch("tractusx_sdk.dataspace.adapters.connector.AdapterFactory.get_dma_adapter", return_value=mock_dma_adapter):
        with patch("tractusx_sdk.dataspace.controllers.connector.ControllerFactory.get_dma_controllers_for_version") as mock_get_controllers:
            mock_get_controllers.return_value = mock_controllers
            svc = BaseConnectorProviderService(
                dataspace_version="jupiter",
                base_url="http://test",
                dma_path="/dma",
                debug=False
            )
            yield svc


@pytest.fixture
def mock_logger():
    return Mock()


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


@patch("tractusx_sdk.dataspace.models.connector.ModelFactory.get_asset_model")
def test_create_asset_debug_logging(mock_get_asset_model, mock_dma_adapter, mock_controllers):
    logger = Mock()
    service = BaseConnectorProviderService(
        dataspace_version="jupiter",
        base_url="http://test",
        dma_path="/dma",
        debug=True,
        logger=logger
    )
    service._asset_controller = Mock()
    service._asset_controller.create.return_value = Mock(status_code=200, json=lambda: {"asset": "ok"})

    mock_get_asset_model.return_value = {"mock": "asset"}

    service.create_asset(asset_id="123", base_url="http://test", dct_type="test")

    assert logger.debug.called


@patch("tractusx_sdk.dataspace.models.connector.ModelFactory.get_asset_model")
def test_create_asset_no_debug_logging(mock_get_asset_model, mock_dma_adapter, mock_controllers):
    logger = Mock()
    service = BaseConnectorProviderService(
        dataspace_version="jupiter",
        base_url="http://test",
        dma_path="/dma",
        debug=False,
        logger=logger
    )
    service._asset_controller = Mock()
    service._asset_controller.create.return_value = Mock(status_code=200, json=lambda: {"asset": "ok"})

    mock_get_asset_model.return_value = {"mock": "asset"}

    service.create_asset(asset_id="123", base_url="http://test", dct_type="test")

    logger.debug.assert_not_called()
