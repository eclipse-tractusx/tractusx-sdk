################################################################################
#
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
################################################################################

"""
A failure of a remote call must never put the secrets of the request into the logs.

``requests`` and ``httpx`` quote the full URL, query string included, in the message of their exceptions, and a
remote service may echo the request in its error body. Every record is rendered the way a handler would (message,
extra fields, formatted traceback), so that nothing that reaches a log can hide from these tests.
"""

import logging
from importlib import import_module
from unittest.mock import MagicMock, Mock, patch

import pytest
import requests

import tractusx_sdk.dataspace.services.connector.base_connector_consumer as bcc
from tractusx_sdk.dataspace.adapters.adapter import Adapter
from tractusx_sdk.dataspace.managers.connection.memory import MemoryConnectionManager
from tractusx_sdk.dataspace.services.connector import BaseConnectorProviderService
from tractusx_sdk.dataspace.services.connector.base_connector_consumer import BaseConnectorConsumerService
from tractusx_sdk.dataspace.services.connector.saturn.connector_consumer_service import ConnectorConsumerService as SaturnConsumer
from tractusx_sdk.dataspace.services.discovery.connector_discovery_service import ConnectorDiscoveryService
from tractusx_sdk.dataspace.tools.http_tools import HttpTools
from tractusx_sdk.dataspace.tools.validate_submodels import submodel_schema_finder
from tractusx_sdk.exceptions import DiscoveryError

SECRET = "s3cr3t-value"
ADDRESS = "https://provider.example.com/dsp"
SEMANTIC_ID = "urn:samm:io.catenax.part_type_information:1.0.0#PartTypeInformation"
HTTP_TOOLS = "tractusx_sdk.dataspace.tools.http_tools"
ADAPTER = "tractusx_sdk.dataspace.adapters.adapter"


def _leaky(cls=requests.ConnectionError):
    """An exception worded like the ones of ``requests``: it quotes the URL with its query string."""
    return cls(f"HTTPConnectionPool(host='provider.example.com', port=443): Max retries exceeded with url: "
               f"/api/data?access_token={SECRET} (Caused by NewConnectionError('refused'))")


def _everything(caplog) -> str:
    """What any handler could render out of the captured records, tracebacks included."""
    formatter = logging.Formatter()
    parts = [caplog.text]
    for record in caplog.records:
        parts.append(f"{record.getMessage()} {record.__dict__}")
        if record.exc_info:
            parts.append(formatter.formatException(record.exc_info))
    return "\n".join(parts)


def _assert_clean(caplog):
    assert caplog.records
    assert SECRET not in _everything(caplog)
    assert [r for r in caplog.records if r.exc_info] == []


class TestHttpHelpers:

    @pytest.mark.parametrize("helper, patched", [
        (HttpTools.do_get, "requests.get"),
        (HttpTools.do_post, "requests.post"),
        (HttpTools.do_put, "requests.put"),
        (HttpTools.do_delete, "requests.delete"),
        (HttpTools.do_get_with_session, "requests.Session.get"),
        (HttpTools.do_post_with_session, "requests.Session.post"),
        (HttpTools.do_put_with_session, "requests.Session.put"),
        (HttpTools.do_delete_with_session, "requests.Session.delete"),
    ])
    def test_a_failing_request_logs_the_exception_type_and_never_its_text(self, caplog, helper, patched):
        error = _leaky()
        with patch(patched, side_effect=error), caplog.at_level(logging.DEBUG), pytest.raises(requests.ConnectionError) as raised:
            helper(f"https://provider.example.com/api/data?access_token={SECRET}")

        assert raised.value is error
        failure = [r for r in caplog.records if r.name == HTTP_TOOLS and "failed after" in r.getMessage()][0]
        assert failure.levelno == logging.DEBUG
        assert "(ConnectionError)" in failure.getMessage()
        assert failure.url == "https://provider.example.com/api/data"
        _assert_clean(caplog)


class TestAdapter:

    def test_a_failing_request_logs_the_exception_type_and_never_its_text(self, caplog):
        adapter = Adapter(base_url="https://connector.example.com:8443/")
        error = _leaky(requests.Timeout)
        with patch.object(adapter.session, "request", side_effect=error), caplog.at_level(logging.DEBUG), \
                pytest.raises(requests.Timeout) as raised:
            adapter.get(f"x?access_token={SECRET}")
        adapter.close()

        assert raised.value is error
        failure = [r for r in caplog.records if r.name == ADAPTER and "failed after" in r.getMessage()][0]
        assert failure.levelno == logging.DEBUG
        assert "(Timeout)" in failure.getMessage()
        _assert_clean(caplog)


@pytest.fixture(params=[BaseConnectorConsumerService, SaturnConsumer], ids=["base", "saturn"])
def consumer(request):
    if request.param is SaturnConsumer:
        service = SaturnConsumer(dataspace_version="saturn", base_url="https://control.example.com", dma_path="/management",
                                 connection_manager=MemoryConnectionManager())
    else:
        service = BaseConnectorConsumerService(dataspace_version="jupiter", base_url="https://control.example.com",
                                               dma_path="/management", connection_manager=MemoryConnectionManager())
    with patch.object(bcc.op, "wait"):
        yield service


class TestConsumer:

    def test_the_parallel_catalog_fetch_never_logs_the_text_of_the_failure(self, consumer, caplog):
        with patch.object(consumer, "get_catalog_with_filter", side_effect=_leaky()), caplog.at_level(logging.DEBUG), \
                pytest.raises(requests.ConnectionError):
            consumer.get_catalog_with_filter_parallel("BPNL1", ADDRESS, [], catalogs={})
        _assert_clean(caplog)

    def test_a_catalog_that_cannot_be_fetched_from_one_connector_never_logs_the_text_of_the_failure(self, consumer, caplog):
        with patch.object(consumer, "get_catalog_with_filter", side_effect=_leaky()), caplog.at_level(logging.DEBUG):
            result = consumer.get_catalogs_with_filter_with_bpnl("BPNL1", ["https://bad.example.com"], filter_expression=[])
        assert "error" in result["https://bad.example.com"]
        assert [r for r in caplog.records if r.levelno == logging.WARNING]
        _assert_clean(caplog)

    def test_a_failing_negotiation_poll_never_logs_the_text_of_the_failure(self, consumer, caplog):
        with patch.object(consumer, "_check_single_negotiation_state", side_effect=_leaky()), caplog.at_level(logging.DEBUG), \
                pytest.raises(TimeoutError):
            consumer._poll_negotiation_state("neg-1", ADDRESS, max_wait=3, poll_interval=1)
        _assert_clean(caplog)

    def test_a_failing_transfer_process_poll_never_logs_the_text_of_the_failure(self, consumer, caplog):
        with patch.object(consumer, "get_transfer_process", side_effect=_leaky()), caplog.at_level(logging.DEBUG), \
                pytest.raises(TimeoutError):
            consumer._wait_for_transfer_process("agr-1", ADDRESS, max_wait=3, poll_interval=1)
        _assert_clean(caplog)

    def test_the_asset_check_never_logs_the_text_of_the_failure(self, consumer, caplog):
        with patch.object(consumer, "get_catalog_with_filter", side_effect=_leaky()), caplog.at_level(logging.DEBUG), \
                pytest.raises(ConnectionError):
            consumer.assets_exists("BPNL1", ADDRESS, [])
        _assert_clean(caplog)

    def test_the_dsp_exchange_never_logs_the_text_of_the_failure(self, consumer, caplog):
        with patch.object(consumer, "_fetch_and_validate_catalog", side_effect=_leaky()), caplog.at_level(logging.DEBUG), \
                pytest.raises(requests.ConnectionError):
            consumer.negotiate_and_transfer("BPNL1", ADDRESS, [], policies=[])
        _assert_clean(caplog)

    def test_the_body_of_a_failed_catalog_request_is_never_logged(self, consumer, caplog):
        from tractusx_sdk.exceptions import CatalogRequestError
        consumer._catalog_controller = Mock()
        consumer._catalog_controller.get_catalog.return_value = Mock(status_code=503, text=f"echo {SECRET}", content=SECRET.encode())
        request = Mock(to_data=dict)
        with caplog.at_level(logging.DEBUG), pytest.raises(CatalogRequestError):
            consumer.get_catalog(request=request, counter_party_id="BPNL1", counter_party_address=ADDRESS)
        _assert_clean(caplog)


class TestProvider:

    @pytest.fixture
    def provider(self):
        provider = BaseConnectorProviderService(dataspace_version="jupiter", base_url="https://control.example.com",
                                                dma_path="/management")
        provider._asset_controller = Mock()
        provider._contract_definition_controller = Mock()
        provider._policy_controller = Mock()
        return provider

    def test_the_body_of_a_rejected_asset_is_never_logged(self, provider, caplog):
        provider._asset_controller.create.return_value = Mock(status_code=400, text=f"echo of the data address {SECRET}")
        with caplog.at_level(logging.DEBUG), pytest.raises(ValueError):
            provider.create_asset(asset_id="asset-1", base_url="https://backend.example.com", dct_type="t")
        assert any(r.levelno == logging.ERROR and r.status_code == 400 for r in caplog.records)
        _assert_clean(caplog)

    def test_the_body_of_a_rejected_contract_is_never_logged(self, provider, caplog):
        provider._contract_definition_controller.create.return_value = Mock(status_code=409, text=f"echo {SECRET}")
        with caplog.at_level(logging.DEBUG), pytest.raises(ValueError):
            provider.create_contract(contract_id="c-1", usage_policy_id="u", access_policy_id="a", asset_id="asset-1")
        assert any(r.levelno == logging.ERROR and r.status_code == 409 for r in caplog.records)
        _assert_clean(caplog)

    def test_the_body_of_a_rejected_policy_is_never_logged(self, provider, caplog):
        provider._policy_controller.create.return_value = Mock(status_code=400, text=f"echo {SECRET}")
        with caplog.at_level(logging.DEBUG), pytest.raises(ValueError):
            provider.create_policy(policy_id="p-1")
        assert any(r.levelno == logging.ERROR and r.status_code == 400 for r in caplog.records)
        _assert_clean(caplog)


class TestDiscovery:

    def test_a_failed_refresh_never_logs_the_text_of_the_failure(self, caplog):
        oauth = Mock(connected=True)
        oauth.add_auth_header.side_effect = lambda headers: headers
        finder = Mock()
        finder.find_discovery_urls.return_value = {"bpn": "https://discovery.example.com/api"}
        service = ConnectorDiscoveryService(oauth=oauth, discovery_finder_service=finder, cache_timeout_seconds=60)
        service._get_or_update_discovery_url()
        service.discovery_cache["bpn"]["timestamp"] = 0
        finder.find_discovery_urls.side_effect = DiscoveryError(f"down: https://finder.example.com/api?token={SECRET}")
        with caplog.at_level(logging.DEBUG):
            service._get_or_update_discovery_url()
        assert any(r.levelno == logging.WARNING for r in caplog.records)
        _assert_clean(caplog)


class TestSchemaFinder:

    def test_a_failing_schema_request_never_logs_the_text_of_the_failure(self, caplog):
        with patch("tractusx_sdk.dataspace.tools.validate_submodels.get", side_effect=_leaky()), caplog.at_level(logging.DEBUG), \
                pytest.raises(requests.ConnectionError):
            submodel_schema_finder(SEMANTIC_ID)
        _assert_clean(caplog)


NOTIFICATION_FLAVORS = {
    "industry": ("tractusx_sdk.industry.services.notifications", "tractusx_sdk.industry.services.notifications.notification_consumer_service",
                 "tractusx_sdk.industry.models.notifications"),
    "extension": ("tractusx_sdk.extensions.notification_api", "tractusx_sdk.extensions.notification_api.services.notification_consumer_service",
                  "tractusx_sdk.extensions.notification_api.models"),
}


class TestNotifications:

    @pytest.fixture(params=sorted(NOTIFICATION_FLAVORS))
    def flavor(self, request):
        services_package, consumer_module, models_package = NOTIFICATION_FLAVORS[request.param]
        services = import_module(services_package)
        models = import_module(models_package)
        connector = MagicMock()
        connector.do_dsp_by_dct_type.return_value = (f"https://dataplane.example.com/api?access_token={SECRET}", "edr")
        connector.get_data_plane_headers.return_value = {"Authorization": "edr"}
        notification = (models.Notification.builder().sender_bpn("BPNL000000000001").receiver_bpn("BPNL000000000002")
                        .context("IndustryCore-DigitalTwinEventAPI-ConnectToParent:3.0.0").information("content").build())
        return type("Flavor", (), {
            "consumer": services.NotificationConsumerService(connector_consumer=connector),
            "connector": connector, "notification": notification, "module": import_module(consumer_module),
            "NotificationError": services.NotificationError,
        })

    def test_a_discovery_failure_never_logs_the_text_of_the_failure(self, flavor, caplog):
        flavor.connector.get_catalog_by_dct_type.side_effect = _leaky()
        with caplog.at_level(logging.DEBUG), pytest.raises(flavor.NotificationError):
            flavor.consumer.discover_notification_assets("BPNL000000000002", ADDRESS)
        _assert_clean(caplog)

    def test_a_negotiation_failure_never_logs_the_text_of_the_failure(self, flavor, caplog):
        flavor.connector.negotiate_and_transfer.side_effect = _leaky()
        with caplog.at_level(logging.DEBUG), pytest.raises(flavor.NotificationError):
            flavor.consumer.negotiate_notification_access("BPNL000000000002", ADDRESS)
        _assert_clean(caplog)

    def test_a_failure_sending_never_logs_the_text_of_the_failure(self, flavor, caplog, monkeypatch):
        monkeypatch.setattr(flavor.module.HttpTools, "do_post", Mock(side_effect=_leaky()))
        with caplog.at_level(logging.DEBUG), pytest.raises(flavor.NotificationError):
            flavor.consumer.send_notification("BPNL000000000002", ADDRESS, flavor.notification)
        _assert_clean(caplog)

    def test_the_body_of_a_rejected_notification_is_never_logged(self, flavor, caplog, monkeypatch):
        rejected = Mock(status_code=500, text=f"echo {SECRET}", content=SECRET.encode())
        monkeypatch.setattr(flavor.module.HttpTools, "do_post", Mock(return_value=rejected))
        with caplog.at_level(logging.DEBUG), pytest.raises(flavor.NotificationError):
            flavor.consumer.send_notification("BPNL000000000002", ADDRESS, flavor.notification)
        assert any(r.levelno == logging.ERROR and getattr(r, "status_code", None) == 500 for r in caplog.records)
        assert SECRET not in _everything(caplog)

    def test_a_failure_towards_one_of_many_providers_never_logs_the_text_of_the_failure(self, flavor, caplog):
        flavor.consumer.send_notification = Mock(side_effect=_leaky())
        with caplog.at_level(logging.DEBUG):
            results = flavor.consumer.send_to_multiple_providers([{"bpn": "BPNL00000000000A", "dsp_url": ADDRESS}], flavor.notification)
        assert results["BPNL00000000000A"]["success"] is False
        _assert_clean(caplog)
