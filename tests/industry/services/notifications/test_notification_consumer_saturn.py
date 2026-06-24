#################################################################################
# Eclipse Tractus-X - Software Development KIT
#
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

"""
Tests for NotificationConsumerService Saturn compatibility.

Validates that the service works with both Saturn (DSP 2025-1, unprefixed keys)
and Jupiter (legacy, prefixed dcat:/odrl: keys), and that the _with_bpnl methods
delegate correctly.
"""

import pytest
from unittest.mock import MagicMock, patch

from tractusx_sdk.industry.services.notifications import (
    NotificationConsumerService,
    NotificationError,
)
from tractusx_sdk.industry.models.notifications import (
    Notification,
)
from tractusx_sdk.industry.constants import DIGITAL_TWIN_EVENT_API_TYPE, DCT_TYPE_KEY


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_connector():
    """Create a mock connector consumer service."""
    return MagicMock()


@pytest.fixture
def service(mock_connector):
    """Create a NotificationConsumerService with the mock connector."""
    return NotificationConsumerService(
        connector_consumer=mock_connector,
        verbose=False,
    )


@pytest.fixture
def sample_notification() -> Notification:
    """Create a sample notification for testing."""
    return (
        Notification.builder()
        .sender_bpn("BPNL000000000001")
        .receiver_bpn("BPNL000000000002")
        .context("IndustryCore-DigitalTwinEventAPI-ConnectToParent:3.0.0")
        .information("Test notification content")
        .build()
    )


# ---------------------------------------------------------------------------
# Saturn dataset extraction (discover_notification_assets)
# ---------------------------------------------------------------------------

class TestDiscoverNotificationAssetsSaturn:
    """Ensures discover_notification_assets handles Saturn catalogs (unprefixed 'dataset' key)."""

    def test_saturn_catalog_single_dataset(self, service, mock_connector):
        """Saturn catalog uses 'dataset' instead of 'dcat:dataset'."""
        mock_connector.get_catalog_by_dct_type.return_value = {
            "dataset": {
                "@id": "saturn-asset-1",
                "dct:type": {"@id": DIGITAL_TWIN_EVENT_API_TYPE},
            }
        }

        assets = service.discover_notification_assets(
            provider_bpn="BPNL000000000002",
            provider_dsp_url="https://provider.com/dsp",
        )

        assert len(assets) == 1
        assert assets[0]["@id"] == "saturn-asset-1"

    def test_saturn_catalog_multiple_datasets(self, service, mock_connector):
        """Saturn catalog with an array of datasets."""
        mock_connector.get_catalog_by_dct_type.return_value = {
            "dataset": [
                {"@id": "saturn-asset-1"},
                {"@id": "saturn-asset-2"},
                {"@id": "saturn-asset-3"},
            ]
        }

        assets = service.discover_notification_assets(
            provider_bpn="BPNL000000000002",
            provider_dsp_url="https://provider.com/dsp",
        )

        assert len(assets) == 3

    def test_saturn_catalog_empty_dataset(self, service, mock_connector):
        """Saturn catalog with empty 'dataset'."""
        mock_connector.get_catalog_by_dct_type.return_value = {
            "dataset": []
        }

        assets = service.discover_notification_assets(
            provider_bpn="BPNL000000000002",
            provider_dsp_url="https://provider.com/dsp",
        )

        assert len(assets) == 0

    def test_saturn_catalog_no_dataset_key(self, service, mock_connector):
        """Saturn catalog with neither 'dataset' nor 'dcat:dataset'."""
        mock_connector.get_catalog_by_dct_type.return_value = {
            "@type": "Catalog"
        }

        assets = service.discover_notification_assets(
            provider_bpn="BPNL000000000002",
            provider_dsp_url="https://provider.com/dsp",
        )

        assert len(assets) == 0


class TestDiscoverNotificationAssetsJupiter:
    """Ensures discover_notification_assets still works with Jupiter catalogs (prefixed 'dcat:dataset')."""

    def test_jupiter_catalog_single_dataset(self, service, mock_connector):
        """Legacy Jupiter catalog uses 'dcat:dataset'."""
        mock_connector.get_catalog_by_dct_type.return_value = {
            "dcat:dataset": {
                "@id": "jupiter-asset-1",
                "dct:type": {"@id": DIGITAL_TWIN_EVENT_API_TYPE},
            }
        }

        assets = service.discover_notification_assets(
            provider_bpn="BPNL000000000002",
            provider_dsp_url="https://provider.com/dsp",
        )

        assert len(assets) == 1
        assert assets[0]["@id"] == "jupiter-asset-1"

    def test_jupiter_catalog_multiple_datasets(self, service, mock_connector):
        """Legacy Jupiter catalog with an array of datasets."""
        mock_connector.get_catalog_by_dct_type.return_value = {
            "dcat:dataset": [
                {"@id": "jupiter-asset-1"},
                {"@id": "jupiter-asset-2"},
            ]
        }

        assets = service.discover_notification_assets(
            provider_bpn="BPNL000000000002",
            provider_dsp_url="https://provider.com/dsp",
        )

        assert len(assets) == 2


# ---------------------------------------------------------------------------
# _with_bpnl method variants
# ---------------------------------------------------------------------------

class TestDiscoverNotificationAssetsWithBpnl:
    """Tests for discover_notification_assets_with_bpnl."""

    def test_calls_get_catalog_by_dct_type_with_bpnl(self, service, mock_connector):
        """Should delegate to get_catalog_by_dct_type_with_bpnl."""
        mock_connector.get_catalog_by_dct_type_with_bpnl.return_value = {
            "dataset": [{"@id": "asset-1"}]
        }

        assets = service.discover_notification_assets_with_bpnl(
            bpnl="BPNL000000000002",
            counter_party_address="https://provider.com/dsp",
        )

        mock_connector.get_catalog_by_dct_type_with_bpnl.assert_called_once_with(
            bpnl="BPNL000000000002",
            counter_party_address="https://provider.com/dsp",
            dct_type=DIGITAL_TWIN_EVENT_API_TYPE,
            dct_type_key=DCT_TYPE_KEY,
            timeout=60,
        )
        assert len(assets) == 1
        assert assets[0]["@id"] == "asset-1"

    def test_handles_saturn_and_jupiter_catalogs(self, service, mock_connector):
        """Should extract datasets from both Saturn and Jupiter catalogs."""
        # Saturn
        mock_connector.get_catalog_by_dct_type_with_bpnl.return_value = {
            "dataset": {"@id": "saturn-asset"}
        }
        assets = service.discover_notification_assets_with_bpnl(
            bpnl="BPNL000000000002",
            counter_party_address="https://provider.com/dsp",
        )
        assert len(assets) == 1
        assert assets[0]["@id"] == "saturn-asset"

        # Jupiter
        mock_connector.get_catalog_by_dct_type_with_bpnl.return_value = {
            "dcat:dataset": {"@id": "jupiter-asset"}
        }
        assets = service.discover_notification_assets_with_bpnl(
            bpnl="BPNL000000000002",
            counter_party_address="https://provider.com/dsp",
        )
        assert len(assets) == 1
        assert assets[0]["@id"] == "jupiter-asset"

    def test_raises_notification_error_on_failure(self, service, mock_connector):
        """Should wrap errors in NotificationError."""
        mock_connector.get_catalog_by_dct_type_with_bpnl.side_effect = Exception("Discovery failed")

        with pytest.raises(NotificationError, match="Discovery failed"):
            service.discover_notification_assets_with_bpnl(
                bpnl="BPNL000000000002",
                counter_party_address="https://provider.com/dsp",
            )


class TestNegotiateNotificationAccessWithBpnl:
    """Tests for negotiate_notification_access_with_bpnl."""

    def test_calls_do_dsp_with_bpnl(self, service, mock_connector):
        """Should delegate to do_dsp_with_bpnl with the correct filter expression."""
        mock_connector.get_filter_expression.return_value = {
            "operandLeft": DCT_TYPE_KEY,
            "operator": "=",
            "operandRight": DIGITAL_TWIN_EVENT_API_TYPE,
        }
        mock_connector.do_dsp_with_bpnl.return_value = (
            "https://dataplane.com/notifications",
            "token-abc",
        )

        endpoint, token = service.negotiate_notification_access_with_bpnl(
            bpnl="BPNL000000000002",
            counter_party_address="https://provider.com/dsp",
        )

        mock_connector.do_dsp_with_bpnl.assert_called_once()
        call_kwargs = mock_connector.do_dsp_with_bpnl.call_args[1]
        assert call_kwargs["bpnl"] == "BPNL000000000002"
        assert call_kwargs["counter_party_address"] == "https://provider.com/dsp"
        assert endpoint == "https://dataplane.com/notifications"
        assert token == "token-abc"

    def test_passes_policies(self, service, mock_connector):
        """Should forward policies to do_dsp_with_bpnl."""
        mock_connector.get_filter_expression.return_value = {}
        mock_connector.do_dsp_with_bpnl.return_value = ("https://dp.com", "t")

        policies = [{"permission": {"action": "use"}}]
        service.negotiate_notification_access_with_bpnl(
            bpnl="BPN",
            counter_party_address="https://provider.com/dsp",
            policies=policies,
        )

        call_kwargs = mock_connector.do_dsp_with_bpnl.call_args[1]
        assert call_kwargs["policies"] == policies

    def test_raises_notification_error_on_failure(self, service, mock_connector):
        """Should wrap errors in NotificationError."""
        mock_connector.get_filter_expression.return_value = {}
        mock_connector.do_dsp_with_bpnl.side_effect = Exception("BPNL negotiation failed")

        with pytest.raises(NotificationError, match="BPNL negotiation failed"):
            service.negotiate_notification_access_with_bpnl(
                bpnl="BPN",
                counter_party_address="https://provider.com/dsp",
            )


class TestGetNotificationEndpointWithBpnl:
    """Tests for get_notification_endpoint_with_bpnl."""

    def test_calls_do_dsp_with_bpnl(self, service, mock_connector):
        """Should delegate to do_dsp_with_bpnl."""
        mock_connector.get_filter_expression.return_value = {}
        mock_connector.do_dsp_with_bpnl.return_value = (
            "https://dataplane.com/notifications",
            "token-xyz",
        )

        endpoint, token = service.get_notification_endpoint_with_bpnl(
            bpnl="BPNL000000000002",
            counter_party_address="https://provider.com/dsp",
        )

        assert endpoint == "https://dataplane.com/notifications"
        assert token == "token-xyz"
        mock_connector.do_dsp_with_bpnl.assert_called_once()

    def test_uses_custom_dct_type(self, service, mock_connector):
        """Should support a custom dct_type filter."""
        mock_connector.get_filter_expression.return_value = {}
        mock_connector.do_dsp_with_bpnl.return_value = ("https://dp.com", "t")

        custom_type = "https://example.com/custom#Type"
        service.get_notification_endpoint_with_bpnl(
            bpnl="BPN",
            counter_party_address="https://provider.com/dsp",
            dct_type=custom_type,
        )

        # Verify filter_expression was built with custom type
        mock_connector.get_filter_expression.assert_called_once_with(
            key=DCT_TYPE_KEY,
            value=custom_type,
            operator="=",
        )

    def test_raises_notification_error_on_failure(self, service, mock_connector):
        """Should wrap errors in NotificationError."""
        mock_connector.get_filter_expression.return_value = {}
        mock_connector.do_dsp_with_bpnl.side_effect = Exception("Endpoint failure")

        with pytest.raises(NotificationError, match="Endpoint failure"):
            service.get_notification_endpoint_with_bpnl(
                bpnl="BPN",
                counter_party_address="https://provider.com/dsp",
            )


class TestSendNotificationWithBpnl:
    """Tests for send_notification_with_bpnl."""

    def test_full_flow_delegates_to_endpoint(self, service, mock_connector, sample_notification):
        """Should negotiate via BPNL, then send to endpoint."""
        mock_connector.get_filter_expression.return_value = {}
        mock_connector.do_dsp_with_bpnl.return_value = (
            "https://dataplane.com/notifications",
            "token-abc",
        )
        mock_connector.get_data_plane_headers.return_value = {
            "Authorization": "Bearer token-abc",
            "Content-Type": "application/json",
        }

        with patch(
            "tractusx_sdk.industry.services.notifications.notification_consumer_service.HttpTools"
        ) as mock_http:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.text = '{"status": "received"}'
            mock_response.json.return_value = {"status": "received"}
            mock_http.do_post.return_value = mock_response
            mock_http.concat_into_url = lambda a, b: f"{a}/{b}" if b else a

            result = service.send_notification_with_bpnl(
                bpnl="BPNL000000000002",
                counter_party_address="https://provider.com/dsp",
                notification=sample_notification,
            )

        assert result["status"] == "received"
        mock_connector.do_dsp_with_bpnl.assert_called_once()

    def test_validates_notification(self, service, mock_connector):
        """Should validate notification before sending."""
        # Same sender and receiver → validation error
        notification = (
            Notification.builder()
            .sender_bpn("BPNL000000000001")
            .receiver_bpn("BPNL000000000001")  # Same as sender
            .context("test-context:1.0")
            .information("Test")
            .build()
        )

        from tractusx_sdk.industry.services.notifications.exceptions import NotificationValidationError

        with pytest.raises(NotificationValidationError, match="cannot be the same"):
            service.send_notification_with_bpnl(
                bpnl="BPN",
                counter_party_address="https://provider.com/dsp",
                notification=notification,
            )

    def test_raises_notification_error_on_failure(self, service, mock_connector, sample_notification):
        """Should wrap errors in NotificationError."""
        mock_connector.get_filter_expression.return_value = {}
        mock_connector.do_dsp_with_bpnl.side_effect = Exception("Send via BPNL failed")

        with pytest.raises(NotificationError, match="Send via BPNL failed"):
            service.send_notification_with_bpnl(
                bpnl="BPN",
                counter_party_address="https://provider.com/dsp",
                notification=sample_notification,
            )

    def test_passes_policies_and_endpoint_path(self, service, mock_connector, sample_notification):
        """Should forward policies through to the endpoint negotiation and append path."""
        mock_connector.get_filter_expression.return_value = {}
        mock_connector.do_dsp_with_bpnl.return_value = (
            "https://dataplane.com",
            "token",
        )
        mock_connector.get_data_plane_headers.return_value = {}

        with patch(
            "tractusx_sdk.industry.services.notifications.notification_consumer_service.HttpTools"
        ) as mock_http:
            mock_response = MagicMock()
            mock_response.status_code = 202
            mock_response.text = ""
            mock_http.do_post.return_value = mock_response
            mock_http.concat_into_url.return_value = "https://dataplane.com/receive"

            policies = [{"permission": {"action": "use"}}]
            service.send_notification_with_bpnl(
                bpnl="BPN",
                counter_party_address="https://provider.com/dsp",
                notification=sample_notification,
                endpoint_path="receive",
                policies=policies,
            )

            mock_http.concat_into_url.assert_called_with("https://dataplane.com", "receive")

        call_kwargs = mock_connector.do_dsp_with_bpnl.call_args[1]
        assert call_kwargs["policies"] == policies


# ---------------------------------------------------------------------------
# Ensure no connector → NotificationError for _with_bpnl methods
# ---------------------------------------------------------------------------

class TestWithBpnlRequiresConnector:
    """All _with_bpnl methods should raise NotificationError if no connector consumer is set."""

    def test_discover_with_bpnl_requires_connector(self):
        service = NotificationConsumerService()
        with pytest.raises(NotificationError, match="Connector consumer is required"):
            service.discover_notification_assets_with_bpnl(
                bpnl="BPN", counter_party_address="https://x.com/dsp"
            )

    def test_negotiate_with_bpnl_requires_connector(self):
        service = NotificationConsumerService()
        with pytest.raises(NotificationError, match="Connector consumer is required"):
            service.negotiate_notification_access_with_bpnl(
                bpnl="BPN", counter_party_address="https://x.com/dsp"
            )

    def test_get_endpoint_with_bpnl_requires_connector(self):
        service = NotificationConsumerService()
        with pytest.raises(NotificationError, match="Connector consumer is required"):
            service.get_notification_endpoint_with_bpnl(
                bpnl="BPN", counter_party_address="https://x.com/dsp"
            )

    def test_send_with_bpnl_requires_connector(self, sample_notification):
        service = NotificationConsumerService()
        with pytest.raises(NotificationError, match="Connector consumer is required"):
            service.send_notification_with_bpnl(
                bpnl="BPN",
                counter_party_address="https://x.com/dsp",
                notification=sample_notification,
            )
