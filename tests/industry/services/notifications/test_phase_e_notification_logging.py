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

"""
The log records of the notification services.

The notifications exist in two near-identical packages (``industry.services.notifications`` and
``extensions.notification_api``). Every test runs against both, and a parity test checks they emit the same records.
"""

import ast
import logging
from importlib import import_module
from pathlib import Path
from unittest.mock import MagicMock, Mock

import pytest

import tractusx_sdk

SECRET = "s3cr3t-value"
ADDRESS = f"https://provider.example.com/dsp?token={SECRET}"
SAFE_ADDRESS = "https://provider.example.com/dsp"
ENDPOINT = f"https://dataplane.example.com/api?access_token={SECRET}"
SAFE_ENDPOINT = "https://dataplane.example.com/api"

FLAVORS = {
    "industry": ("tractusx_sdk.industry.services.notifications", "tractusx_sdk.industry.models.notifications"),
    "extension": ("tractusx_sdk.extensions.notification_api", "tractusx_sdk.extensions.notification_api.models"),
}


@pytest.fixture(params=sorted(FLAVORS))
def flavor(request):
    services_package, models_package = FLAVORS[request.param]
    services = import_module(services_package)
    models = import_module(models_package)
    return type("Flavor", (), {
        "name": request.param,
        "NotificationService": services.NotificationService,
        "NotificationConsumerService": services.NotificationConsumerService,
        "NotificationError": services.NotificationError,
        "NotificationValidationError": services.NotificationValidationError,
        "Notification": models.Notification,
        "consumer_logger": import_module(f"{services_package}.notification_consumer_service" if request.param == "industry"
                                         else f"{services_package}.services.notification_consumer_service").__name__,
        "service_logger": import_module(f"{services_package}.notification_service" if request.param == "industry"
                                        else f"{services_package}.services.notification_service").__name__,
    })


def _dump(caplog) -> str:
    return "\n".join(f"{r.getMessage()} {r.__dict__} {r.exc_text or ''}" for r in caplog.records)


def _records(caplog, name):
    return [r for r in caplog.records if r.name == name]


@pytest.fixture
def notification(flavor):
    return (flavor.Notification.builder().sender_bpn("BPNL000000000001").receiver_bpn("BPNL000000000002")
            .context("IndustryCore-DigitalTwinEventAPI-ConnectToParent:3.0.0").information(f"content {SECRET}").build())


@pytest.fixture
def connector():
    return MagicMock()


@pytest.fixture
def consumer(flavor, connector):
    return flavor.NotificationConsumerService(connector_consumer=connector)


def _response(status=200, text="", payload=None):
    response = Mock(status_code=status, text=text)
    response.json.return_value = payload
    return response


class TestConsumerCreationAndSetup:

    def test_creation_is_logged(self, flavor, connector, caplog):
        with caplog.at_level(logging.DEBUG):
            flavor.NotificationConsumerService(connector_consumer=connector)
            flavor.NotificationConsumerService()
        messages = [r.getMessage() for r in _records(caplog, flavor.consumer_logger)]
        assert messages == ["NotificationConsumerService created (connector consumer: MagicMock)",
                            "NotificationConsumerService created (connector consumer: none)"]

    def test_a_missing_connector_consumer_is_logged_before_it_is_raised(self, flavor, notification, caplog):
        service = flavor.NotificationConsumerService()
        with caplog.at_level(logging.DEBUG), pytest.raises(flavor.NotificationError):
            service.discover_notification_assets("BPNL000000000002", ADDRESS)
        assert _records(caplog, flavor.consumer_logger)[-1].levelno == logging.ERROR


class TestDiscovery:

    def test_discovered_assets_are_logged_with_a_sanitised_address(self, flavor, consumer, connector, caplog):
        connector.get_catalog_by_dct_type.return_value = {"dcat:dataset": [{"@id": "a1"}, {"@id": "a2"}]}
        with caplog.at_level(logging.DEBUG):
            assert len(consumer.discover_notification_assets("BPNL000000000002", ADDRESS)) == 2
        starting, found = [r for r in _records(caplog, flavor.consumer_logger) if r.levelno == logging.INFO]
        assert starting.getMessage() == f"Discovering notification assets from provider BPNL000000000002 at {SAFE_ADDRESS}"
        assert (starting.bpn, starting.counter_party_address) == ("BPNL000000000002", SAFE_ADDRESS)
        assert "Found 2 DigitalTwinEventAPI asset(s)" in found.getMessage()
        assert SECRET not in _dump(caplog)

    def test_a_discovery_failure_is_logged_with_its_traceback_and_context_and_wrapped_as_before(self, flavor, consumer, connector, caplog):
        connector.get_catalog_by_dct_type.side_effect = ConnectionError("down")
        with caplog.at_level(logging.DEBUG), pytest.raises(flavor.NotificationError, match="Failed to discover notification assets: down"):
            consumer.discover_notification_assets("BPNL000000000002", ADDRESS)
        failure = _records(caplog, flavor.consumer_logger)[-1]
        assert failure.levelno == logging.ERROR and failure.exc_info[0] is ConnectionError
        assert (failure.bpn, failure.counter_party_address) == ("BPNL000000000002", SAFE_ADDRESS)
        assert failure.operation == "notification.discover_assets"
        assert SECRET not in _dump(caplog)


class TestNegotiationAndEndpoint:

    def test_a_negotiation_is_logged_with_the_transfer_id(self, flavor, consumer, connector, caplog):
        connector.negotiate_and_transfer.return_value = {"transferProcessId": "tp-1"}
        with caplog.at_level(logging.DEBUG):
            assert consumer.negotiate_notification_access("BPNL000000000002", ADDRESS) == {"transferProcessId": "tp-1"}
        done = _records(caplog, flavor.consumer_logger)[-1]
        assert (done.transfer_id, done.bpn, done.levelno) == ("tp-1", "BPNL000000000002", logging.INFO)

    def test_a_negotiation_failure_is_logged_with_its_traceback_and_wrapped(self, flavor, consumer, connector, caplog):
        connector.negotiate_and_transfer.side_effect = TimeoutError("late")
        with caplog.at_level(logging.DEBUG), pytest.raises(flavor.NotificationError):
            consumer.negotiate_notification_access("BPNL000000000002", ADDRESS)
        failure = _records(caplog, flavor.consumer_logger)[-1]
        assert failure.exc_info[0] is TimeoutError and failure.counter_party_address == SAFE_ADDRESS

    def test_the_endpoint_is_logged_sanitised_and_the_token_never(self, flavor, consumer, connector, caplog):
        connector.do_dsp_by_dct_type.return_value = (ENDPOINT, f"edr-token-{SECRET}")
        with caplog.at_level(logging.DEBUG):
            assert consumer.get_notification_endpoint("BPNL000000000002", ADDRESS) == (ENDPOINT, f"edr-token-{SECRET}")
        obtained = _records(caplog, flavor.consumer_logger)[-1]
        assert obtained.getMessage() == f"Obtained notification endpoint: {SAFE_ENDPOINT}" and obtained.url == SAFE_ENDPOINT
        assert SECRET not in _dump(caplog)

    def test_an_endpoint_failure_is_logged_with_its_traceback(self, flavor, consumer, connector, caplog):
        connector.do_dsp_by_dct_type.side_effect = RuntimeError("no edr")
        with caplog.at_level(logging.DEBUG), pytest.raises(flavor.NotificationError):
            consumer.get_notification_endpoint("BPNL000000000002", ADDRESS)
        failure = _records(caplog, flavor.consumer_logger)[-1]
        assert failure.exc_info[0] is RuntimeError and failure.operation == "notification.get_endpoint"


class TestSending:

    def _wire(self, connector, response):
        connector.do_dsp_by_dct_type.return_value = (ENDPOINT, f"edr-token-{SECRET}")
        connector.get_data_plane_headers.return_value = {"Authorization": f"edr-token-{SECRET}"}
        return response

    def test_a_sent_notification_is_logged_with_its_message_id_and_never_its_content_nor_credentials(self, flavor, consumer, connector,
                                                                                              notification, caplog, monkeypatch):
        self._wire(connector, None)
        module = import_module(flavor.consumer_logger)
        monkeypatch.setattr(module.HttpTools, "do_post", Mock(return_value=_response(200, text='{"ok": true}', payload={"ok": True})))
        with caplog.at_level(logging.DEBUG):
            assert consumer.send_notification("BPNL000000000002", ADDRESS, notification) == {"ok": True}

        records = _records(caplog, flavor.consumer_logger)
        message_id = str(notification.header.message_id)
        sent = [r for r in records if r.getMessage().startswith("Successfully sent notification")][0]
        assert (sent.message_id, sent.status_code, sent.url) == (message_id, 200, ENDPOINT.split("?")[0].replace("?", ""))
        assert any(r.getMessage() == f"Sending notification {message_id} to endpoint {SAFE_ENDPOINT}" for r in records)
        assert SECRET not in _dump(caplog)

    @pytest.mark.parametrize("text, payload, expected", [
        ("", None, "without a body"),
        ("not json", ValueError("bad"), "is not JSON"),
    ])
    def test_the_fallback_to_the_sent_status_is_logged_at_debug(self, flavor, consumer, connector, notification, caplog, monkeypatch,
                                                                text, payload, expected):
        self._wire(connector, None)
        response = _response(200, text=text)
        if isinstance(payload, Exception):
            response.json.side_effect = payload
        monkeypatch.setattr(import_module(flavor.consumer_logger).HttpTools, "do_post", Mock(return_value=response))
        with caplog.at_level(logging.DEBUG):
            assert consumer.send_notification("BPNL000000000002", ADDRESS, notification)["status"] == "sent"
        assert any(expected in r.getMessage() and r.levelno == logging.DEBUG for r in _records(caplog, flavor.consumer_logger))

    def test_a_rejected_notification_is_logged_with_a_cut_body_and_raised_as_before(self, flavor, consumer, connector, notification, caplog,
                                                                                monkeypatch):
        self._wire(connector, None)
        monkeypatch.setattr(import_module(flavor.consumer_logger).HttpTools, "do_post",
                            Mock(return_value=_response(500, text="x" * 5000)))
        with caplog.at_level(logging.DEBUG), pytest.raises(flavor.NotificationError, match="Status code: 500"):
            consumer.send_notification("BPNL000000000002", ADDRESS, notification)
        error = [r for r in _records(caplog, flavor.consumer_logger) if r.levelno == logging.ERROR and r.status_code == 500][0]
        assert len(error.getMessage()) < 700 and error.message_id == str(notification.header.message_id)

    def test_an_unexpected_failure_is_logged_with_its_traceback_and_context_and_wrapped(self, flavor, consumer, connector, notification, caplog,
                                                                                    monkeypatch):
        self._wire(connector, None)
        monkeypatch.setattr(import_module(flavor.consumer_logger).HttpTools, "do_post", Mock(side_effect=OSError("boom")))
        with caplog.at_level(logging.DEBUG), pytest.raises(flavor.NotificationError):
            consumer.send_notification("BPNL000000000002", ADDRESS, notification)
        failures = [r for r in _records(caplog, flavor.consumer_logger) if r.exc_info]
        assert failures and failures[0].exc_info[0] is OSError
        assert failures[0].message_id == str(notification.header.message_id) and failures[0].url == SAFE_ENDPOINT
        assert SECRET not in _dump(caplog)

    def test_an_invalid_notification_is_a_warning_before_it_is_raised(self, flavor, consumer, caplog):
        invalid = flavor.Notification.builder().sender_bpn("BPNL000000000001").receiver_bpn("BPNL000000000001").context("c").build()
        with caplog.at_level(logging.DEBUG), pytest.raises(flavor.NotificationValidationError):
            consumer.send_notification("BPNL000000000002", ADDRESS, invalid)
        warning = _records(caplog, flavor.consumer_logger)[-1]
        assert warning.levelno == logging.WARNING and "cannot be the same" in warning.getMessage()
        assert warning.message_id == str(invalid.header.message_id)


class TestSendingToSeveralProviders:

    def test_the_failures_that_are_kept_in_the_result_are_logged_and_the_run_is_summarised(self, flavor, consumer, notification, caplog):
        def fake(provider_bpn, **kwargs):
            if provider_bpn == "BPNL00000000000B":
                raise RuntimeError("provider down")
            return {"ok": True}

        providers = [{"bpn": "BPNL00000000000A", "dsp_url": ADDRESS}, {"bpn": "BPNL00000000000B", "dsp_url": ADDRESS},
                     {"bpn": "BPNL00000000000C"}]
        consumer.send_notification = fake
        with caplog.at_level(logging.DEBUG):
            results = consumer.send_to_multiple_providers(providers, notification)

        assert [results[b]["success"] for b in ("BPNL00000000000A", "BPNL00000000000B", "BPNL00000000000C")] == [True, False, False]
        records = _records(caplog, flavor.consumer_logger)
        warnings = [r for r in records if r.levelno == logging.WARNING]
        assert len(warnings) == 2
        failed = [r for r in warnings if "provider down" in r.getMessage()][0]
        assert (failed.bpn, failed.counter_party_address) == ("BPNL00000000000B", SAFE_ADDRESS)
        assert any("lacks 'bpn' or 'dsp_url'" in r.getMessage() for r in warnings)
        summary = [r for r in records if r.levelno == logging.INFO][-1]
        assert summary.getMessage() == f"Notification {notification.header.message_id} was sent to 1 of 3 provider(s)"
        assert SECRET not in _dump(caplog)

    def test_stopping_on_the_first_error_is_logged(self, flavor, consumer, notification, caplog):
        consumer.send_notification = Mock(side_effect=RuntimeError("down"))
        providers = [{"bpn": "BPNL00000000000A", "dsp_url": ADDRESS}, {"bpn": "BPNL00000000000B", "dsp_url": ADDRESS}]
        with caplog.at_level(logging.DEBUG):
            results = consumer.send_to_multiple_providers(providers, notification, stop_on_error=True)
        assert list(results) == ["BPNL00000000000A"]
        assert any("stop_on_error is set" in r.getMessage() for r in _records(caplog, flavor.consumer_logger))


class TestNotificationServiceLogging:

    @pytest.fixture
    def provider(self):
        provider = MagicMock()
        provider.create_asset.return_value = {"created": True}
        return provider

    @pytest.fixture
    def service(self, flavor, provider):
        return flavor.NotificationService(connector_provider=provider)

    def test_creation_is_logged(self, flavor, provider, caplog):
        with caplog.at_level(logging.DEBUG):
            flavor.NotificationService(connector_provider=provider)
            flavor.NotificationService()
        assert [r.getMessage() for r in _records(caplog, flavor.service_logger)] == [
            "NotificationService created (connector provider: MagicMock)", "NotificationService created (connector provider: none)"]

    def test_a_missing_connector_provider_is_logged_before_it_is_raised(self, flavor, caplog):
        with caplog.at_level(logging.DEBUG), pytest.raises(flavor.NotificationError):
            flavor.NotificationService().ensure_notification_asset_exists("asset-1", ENDPOINT)
        error = _records(caplog, flavor.service_logger)[-1]
        assert (error.levelno, error.asset_id) == (logging.ERROR, "asset-1")

    def test_an_asset_that_does_not_exist_is_created_with_a_sanitised_url_and_a_noted_default(self, flavor, service, provider, caplog):
        provider.assets.get_by_id.return_value = _response(404)
        with caplog.at_level(logging.DEBUG):
            service.ensure_notification_asset_exists("asset-1", ENDPOINT)
        records = _records(caplog, flavor.service_logger)
        assert any("was not found (status 404)" in r.getMessage() and r.levelno == logging.DEBUG for r in records)
        creating = [r for r in records if r.getMessage().startswith("Creating DigitalTwinEventAPI asset")][0]
        assert creating.getMessage() == f"Creating DigitalTwinEventAPI asset 'asset-1' at {SAFE_ENDPOINT}"
        assert (creating.asset_id, creating.url) == ("asset-1", SAFE_ENDPOINT)
        assert any("using the defaults" in r.getMessage() for r in records)
        assert SECRET not in _dump(caplog)
        assert [r for r in records if r.levelno >= logging.WARNING] == []

    def test_an_existing_asset_is_logged(self, flavor, service, provider, caplog):
        provider.assets.get_by_id.return_value = _response(
            200, payload={"properties": {"dct:type": {"@id": "https://w3id.org/catenax/taxonomy#DigitalTwinEventAPI"}}})
        with caplog.at_level(logging.DEBUG):
            service.ensure_notification_asset_exists("asset-1", ENDPOINT)
        assert any(r.getMessage() == "DigitalTwinEventAPI asset 'asset-1' already exists" and r.asset_id == "asset-1"
                   for r in _records(caplog, flavor.service_logger))
        provider.create_asset.assert_not_called()

    def test_a_failed_lookup_is_a_warning_with_its_traceback_because_it_is_not_a_not_found(self, flavor, service, provider, caplog):
        provider.assets.get_by_id.side_effect = ConnectionError("connector down")
        with caplog.at_level(logging.DEBUG):
            service.ensure_notification_asset_exists("asset-1", ENDPOINT)
        warning = [r for r in _records(caplog, flavor.service_logger) if r.levelno == logging.WARNING][0]
        assert "treating it as not existing" in warning.getMessage() and warning.exc_info[0] is ConnectionError
        assert warning.asset_id == "asset-1"


class TestBothPackagesEmitTheSameRecords:
    """The two copies must stay in step: what one logs, the other logs too."""

    ROOT = Path(tractusx_sdk.__file__).parent

    @staticmethod
    def _log_signatures(path: Path) -> set:
        signatures = set()
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name)
                    and node.func.value.id == "logger" and node.args and isinstance(node.args[0], ast.Constant)):
                operation = next((kw.value for kw in node.keywords if kw.arg == "extra"), None)
                operations = sorted({k.value.value for k in ast.walk(operation) if isinstance(k, ast.keyword) and k.arg == "operation"
                                     and isinstance(k.value, ast.Constant)}) if operation is not None else []
                signatures.add((node.func.attr, node.args[0].value, tuple(operations)))
        return signatures

    def test_the_notification_service_emits_exactly_the_same_records(self):
        industry = self.ROOT / "industry/services/notifications/notification_service.py"
        extension = self.ROOT / "extensions/notification_api/services/notification_service.py"
        assert self._log_signatures(industry) == self._log_signatures(extension)

    def test_the_older_consumer_emits_nothing_the_newer_one_does_not(self):
        industry = self._log_signatures(self.ROOT / "industry/services/notifications/notification_consumer_service.py")
        extension = self._log_signatures(self.ROOT / "extensions/notification_api/services/notification_consumer_service.py")
        assert extension <= industry

    def test_what_only_the_newer_consumer_logs_belongs_to_its_bpnl_methods_and_its_dataset_extraction(self):
        industry = self._log_signatures(self.ROOT / "industry/services/notifications/notification_consumer_service.py")
        extension = self._log_signatures(self.ROOT / "extensions/notification_api/services/notification_consumer_service.py")
        only_industry = industry - extension
        assert only_industry
        # The BPNL methods exist only in the newer copy, and so does the branch of its newer dataset extraction
        explained = {"The catalog of provider %s has no dataset"}
        assert all("BPNL" in message or any("bpnl" in operation for operation in operations) or message in explained
                   for _, message, operations in only_industry), only_industry
