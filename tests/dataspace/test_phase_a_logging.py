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

"""The log records of the HTTP helpers, the adapters, the factories and the cache."""

import asyncio
import logging
from unittest.mock import MagicMock, patch

import pytest
import requests

from tractusx_sdk.dataspace.adapters.adapter import Adapter
from tractusx_sdk.dataspace.adapters.connector.adapter_factory import AdapterFactory
from tractusx_sdk.dataspace.adapters.connector.base_dma_adapter import BaseDmaAdapter
from tractusx_sdk.dataspace.controllers.connector.controller_factory import ControllerFactory, ControllerType
from tractusx_sdk.dataspace.controllers.connector.utils.decorators import controller_method
from tractusx_sdk.dataspace.tools import cache
from tractusx_sdk.dataspace.tools.http_tools import HttpTools

SECRET = "s3cr3t-value"
URL = "https://provider.example.com:8443/api/v1/assets"
URL_WITH_SECRETS = f"{URL}?access_token={SECRET}&session={SECRET}#{SECRET}"
SECRET_HEADERS = {"Authorization": f"Bearer {SECRET}", "X-Api-Key": SECRET}


def _dump(caplog) -> str:
    """Everything a handler could ever render out of the captured records."""
    return "\n".join(f"{r.getMessage()} {r.__dict__} {r.exc_text or ''}" for r in caplog.records)


def _records(caplog, logger_name):
    return [r for r in caplog.records if r.name == logger_name]


class TestHttpToolsLogging:
    LOGGER = "tractusx_sdk.dataspace.tools.http_tools"

    @pytest.mark.parametrize("helper, patched, method", [
        (HttpTools.do_get, "requests.get", "GET"),
        (HttpTools.do_post, "requests.post", "POST"),
        (HttpTools.do_put, "requests.put", "PUT"),
        (HttpTools.do_delete, "requests.delete", "DELETE"),
    ])
    def test_a_request_logs_its_line_and_its_outcome(self, caplog, helper, patched, method):
        with patch(patched, return_value=MagicMock(status_code=200)), caplog.at_level(logging.DEBUG):
            helper(URL, headers=SECRET_HEADERS)

        request, outcome = _records(caplog, self.LOGGER)
        assert request.levelno == logging.DEBUG
        assert request.getMessage() == f"HTTP {method} {URL}"
        assert (request.http_method, request.url) == (method, URL)
        assert outcome.levelno == logging.DEBUG
        assert outcome.status_code == 200
        assert outcome.elapsed_ms >= 0
        assert outcome.getMessage().startswith(f"HTTP {method} {URL} -> 200 in ")

    @pytest.mark.parametrize("helper, patched", [
        (HttpTools.do_get_with_session, "requests.Session.get"),
        (HttpTools.do_post_with_session, "requests.Session.post"),
        (HttpTools.do_put_with_session, "requests.Session.put"),
        (HttpTools.do_delete_with_session, "requests.Session.delete"),
    ])
    def test_the_session_helpers_are_logged_too_and_note_the_one_off_session(self, caplog, helper, patched):
        with patch(patched, return_value=MagicMock(status_code=204)), caplog.at_level(logging.DEBUG):
            helper(URL)

        messages = [r.getMessage() for r in _records(caplog, self.LOGGER)]
        assert any("No session provided" in m for m in messages)
        assert any("-> 204" in m for m in messages)

    def test_a_given_session_is_not_reported_as_missing(self, caplog):
        session = MagicMock()
        session.get.return_value = MagicMock(status_code=200)
        with caplog.at_level(logging.DEBUG):
            HttpTools.do_get_with_session(URL, session=session)
        assert not any("No session provided" in r.getMessage() for r in caplog.records)

    @pytest.mark.parametrize("status, level", [(200, logging.DEBUG), (404, logging.DEBUG), (401, logging.DEBUG),
                                               (500, logging.WARNING), (503, logging.WARNING)])
    def test_only_a_server_failure_is_a_warning(self, caplog, status, level):
        with patch("requests.get", return_value=MagicMock(status_code=status)), caplog.at_level(logging.DEBUG):
            HttpTools.do_get(URL)
        assert _records(caplog, self.LOGGER)[-1].levelno == level

    def test_a_response_without_a_status_is_still_logged(self, caplog):
        with patch("requests.get", return_value=MagicMock()), caplog.at_level(logging.DEBUG):
            HttpTools.do_get(URL)
        outcome = _records(caplog, self.LOGGER)[-1]
        assert outcome.levelno == logging.DEBUG
        assert "-> None" in outcome.getMessage()
        assert not hasattr(outcome, "status_code")

    def test_a_failure_is_logged_with_its_traceback_and_re_raised_unchanged(self, caplog):
        error = requests.ConnectionError("connection refused")
        with patch("requests.get", side_effect=error), caplog.at_level(logging.DEBUG):
            with pytest.raises(requests.ConnectionError) as raised:
                HttpTools.do_get(URL)

        assert raised.value is error
        failure = _records(caplog, self.LOGGER)[-1]
        assert failure.levelno == logging.ERROR
        assert failure.exc_info[1] is error
        assert failure.getMessage().startswith(f"HTTP GET {URL} failed after ")

    def test_nothing_secret_is_ever_logged(self, caplog):
        with patch("requests.get", return_value=MagicMock(status_code=200)), \
                patch("requests.post", side_effect=requests.ConnectionError("boom")), caplog.at_level(logging.DEBUG):
            HttpTools.do_get(URL_WITH_SECRETS, headers=SECRET_HEADERS, params={"token": SECRET})
            with pytest.raises(requests.ConnectionError):
                HttpTools.do_post(f"https://user:{SECRET}@host/x?k={SECRET}", headers=SECRET_HEADERS, json={"k": SECRET})

        assert caplog.records
        assert SECRET not in _dump(caplog)

    def test_the_tracing_of_the_call_is_unaffected(self):
        from tractusx_sdk.dataspace.tools.tracing import Tracer

        tracer = Tracer()
        with patch("requests.get", return_value=MagicMock(status_code=200, headers={}, content=b"{}", text="{}",
                                                          json=lambda: {})):
            HttpTools.do_get(URL, tracer=tracer)
        assert len(tracer.entries) == 1

    def test_proxy_notes_the_default_media_type(self, caplog):
        response = MagicMock(content=b"x", status_code=200, headers={})
        with caplog.at_level(logging.DEBUG):
            result = HttpTools.proxy(response)
        assert result.media_type == "application/json"
        assert any("defaulting to application/json" in r.getMessage() for r in caplog.records)

    def test_proxy_keeps_a_given_media_type_silently(self, caplog):
        response = MagicMock(content=b"x", status_code=200, headers={"content-type": "text/plain"})
        with caplog.at_level(logging.DEBUG):
            result = HttpTools.proxy(response)
        assert result.media_type == "text/plain"
        assert caplog.records == []

    def test_error_responses_are_logged_at_debug(self, caplog):
        with caplog.at_level(logging.DEBUG):
            HttpTools.get_error_response(status=418)
            HttpTools.get_not_authorized()
        assert [r.status_code for r in caplog.records] == [418, 401]
        assert {r.levelno for r in caplog.records} == {logging.DEBUG}


class TestAdapterLogging:
    LOGGER = "tractusx_sdk.dataspace.adapters.adapter"

    @pytest.fixture
    def adapter(self):
        adapter = Adapter(base_url="https://connector.example.com:8443/", headers=SECRET_HEADERS)
        yield adapter
        adapter.close()

    def test_creation_logs_the_url_and_the_number_of_headers_only(self, caplog):
        with caplog.at_level(logging.DEBUG):
            adapter = Adapter(base_url=f"https://user:{SECRET}@connector.example.com/api?x={SECRET}",
                              headers=SECRET_HEADERS)
        adapter.close()

        created = _records(caplog, self.LOGGER)[0]
        assert "with 2 default header(s)" in created.getMessage()
        assert created.url == "https://connector.example.com/api"
        assert SECRET not in _dump(caplog)

    def test_a_request_logs_its_line_and_its_outcome(self, adapter, caplog):
        with patch.object(adapter.session, "request", return_value=MagicMock(status_code=201)), \
                caplog.at_level(logging.DEBUG):
            adapter.post("v3/assets", json={"k": SECRET})

        request, outcome = _records(caplog, self.LOGGER)
        assert request.getMessage() == "HTTP POST https://connector.example.com:8443/v3/assets"
        assert request.adapter_type == "Adapter"
        assert (outcome.status_code, outcome.levelno) == (201, logging.DEBUG)
        assert outcome.elapsed_ms >= 0

    @pytest.mark.parametrize("status, level", [(404, logging.DEBUG), (409, logging.DEBUG), (502, logging.WARNING)])
    def test_only_a_server_failure_is_a_warning(self, adapter, caplog, status, level):
        with patch.object(adapter.session, "request", return_value=MagicMock(status_code=status)), \
                caplog.at_level(logging.DEBUG):
            adapter.get("x")
        assert _records(caplog, self.LOGGER)[-1].levelno == level

    def test_a_failure_is_logged_with_its_traceback_and_re_raised_unchanged(self, adapter, caplog):
        error = requests.Timeout("too slow")
        with patch.object(adapter.session, "request", side_effect=error), caplog.at_level(logging.DEBUG):
            with pytest.raises(requests.Timeout) as raised:
                adapter.delete("x/1")

        assert raised.value is error
        failure = _records(caplog, self.LOGGER)[-1]
        assert failure.levelno == logging.ERROR
        assert failure.exc_info[1] is error
        assert failure.http_method == "DELETE"

    def test_nothing_secret_is_ever_logged(self, adapter, caplog):
        with patch.object(adapter.session, "request", return_value=MagicMock(status_code=200)), \
                caplog.at_level(logging.DEBUG):
            adapter.get(f"x?token={SECRET}", headers=SECRET_HEADERS, params={"k": SECRET})
            adapter.post("x", data=SECRET, headers=SECRET_HEADERS)

        assert SECRET not in _dump(caplog)
        adapter_request_urls = {r.url for r in caplog.records if hasattr(r, "url")}
        assert adapter_request_urls == {"https://connector.example.com:8443/x"}

    def test_closing_is_logged(self, caplog):
        adapter = Adapter(base_url="https://x")
        with caplog.at_level(logging.DEBUG):
            adapter.close()
        assert any("Closing the session" in r.getMessage() for r in caplog.records)


class TestBaseDmaAdapterLogging:
    LOGGER = "tractusx_sdk.dataspace.adapters.connector.base_dma_adapter"

    @pytest.fixture
    def adapter(self):
        adapter = BaseDmaAdapter(base_url="https://connector.example.com", dma_path="/management")
        yield adapter
        adapter.close()

    def test_the_default_content_type_is_logged(self, adapter, caplog):
        with patch.object(adapter.session, "request", return_value=MagicMock(status_code=200)) as request, \
                caplog.at_level(logging.DEBUG):
            adapter.post("v3/assets", data="{}")

        assert request.call_args.kwargs["headers"]["Content-Type"] == "application/json"
        assert any("defaulting to application/json" in r.getMessage() for r in _records(caplog, self.LOGGER))

    def test_a_given_content_type_is_not_reported(self, adapter, caplog):
        with patch.object(adapter.session, "request", return_value=MagicMock(status_code=200)) as request, \
                caplog.at_level(logging.DEBUG):
            adapter.post("v3/assets", data="{}", headers={"content-type": "text/plain"})

        assert request.call_args.kwargs["headers"]["Content-Type"] == "text/plain"
        assert _records(caplog, self.LOGGER) == []


class TestAdapterFactoryLogging:
    LOGGER = "tractusx_sdk.dataspace.adapters.connector.adapter_factory"

    def test_creating_an_adapter_is_logged_without_credentials(self, caplog):
        with caplog.at_level(logging.DEBUG):
            adapter = AdapterFactory.get_dma_adapter(
                dataspace_version="jupiter", base_url=f"https://user:{SECRET}@connector.example.com/?k={SECRET}",
                dma_path="/management", headers=SECRET_HEADERS)
        adapter.close()

        creating, resolved = [r for r in _records(caplog, self.LOGGER)][:2]
        assert creating.getMessage() == ("Creating a DMA adapter for dataspace version jupiter "
                                         "at https://connector.example.com/ with DMA path /management")
        assert creating.dataspace_version == "jupiter"
        assert resolved.getMessage().startswith("Resolved DmaAdapter from ")
        assert SECRET not in _dump(caplog)

    def test_creating_a_dataplane_adapter_is_logged(self, caplog):
        module = MagicMock()
        with patch(f"{self.LOGGER}.import_module", return_value=module), caplog.at_level(logging.DEBUG):
            AdapterFactory.get_dataplane_adapter(dataspace_version="saturn", base_url="https://dp.example.com?k=1")

        creating, resolved = _records(caplog, self.LOGGER)
        assert creating.getMessage() == "Creating a dataplane adapter for dataspace version saturn at https://dp.example.com"
        assert resolved.adapter_type == "Dataplane"

    def test_a_missing_adapter_class_is_logged_with_its_traceback(self, caplog):
        with caplog.at_level(logging.DEBUG), pytest.raises(AttributeError):
            AdapterFactory.get_dataplane_adapter(dataspace_version="jupiter", base_url="https://dp.example.com")
        failure = _records(caplog, self.LOGGER)[-1]
        assert failure.levelno == logging.ERROR and failure.exc_info is not None
        assert failure.adapter_type == "Dataplane"

    def test_an_unsupported_version_is_logged_before_it_is_raised(self, caplog):
        with caplog.at_level(logging.DEBUG), pytest.raises(ValueError, match="Unsupported version nope"):
            AdapterFactory.get_dma_adapter(dataspace_version="nope", base_url="https://x", dma_path="/m")

        error = [r for r in _records(caplog, self.LOGGER) if r.levelno == logging.ERROR][0]
        assert error.dataspace_version == "nope"
        assert error.adapter_type == "Dma"


class TestControllerFactoryLogging:
    LOGGER = "tractusx_sdk.dataspace.controllers.connector.controller_factory"

    def test_the_resolution_of_a_controller_is_logged(self, caplog):
        adapter = BaseDmaAdapter(base_url="https://x", dma_path="/m")
        with caplog.at_level(logging.DEBUG):
            ControllerFactory.get_asset_controller(dataspace_version="jupiter", adapter=adapter)
        adapter.close()

        resolved = _records(caplog, self.LOGGER)[0]
        assert resolved.getMessage().startswith("Resolved AssetController from ")
        assert (resolved.dataspace_version, resolved.model) == ("jupiter", "Asset")

    def test_an_unsupported_version_is_logged_before_it_is_raised(self, caplog):
        with caplog.at_level(logging.DEBUG), pytest.raises(ValueError, match="Unsupported version nope"):
            ControllerFactory._get_controller_builder(ControllerType.ASSET, "nope")
        assert [r.levelno for r in _records(caplog, self.LOGGER)] == [logging.ERROR]

    def test_a_missing_controller_class_is_logged_with_its_traceback(self, caplog):
        with patch(f"{self.LOGGER}.import_module", return_value=object()), caplog.at_level(logging.DEBUG), \
                pytest.raises(AttributeError):
            ControllerFactory._get_controller_builder(ControllerType.ASSET, "jupiter")
        failure = _records(caplog, self.LOGGER)[-1]
        assert failure.levelno == logging.ERROR and failure.exc_info is not None

    def test_a_module_that_cannot_be_imported_is_logged_with_its_traceback(self, caplog):
        with patch(f"{self.LOGGER}.import_module", side_effect=ImportError("x")), caplog.at_level(logging.DEBUG), \
                pytest.raises(ImportError):
            ControllerFactory._get_controller_builder(ControllerType.ASSET, "jupiter")
        failure = _records(caplog, self.LOGGER)[-1]
        assert failure.levelno == logging.ERROR and failure.exc_info is not None


class TestControllerMethodLogging:
    LOGGER = "tractusx_sdk.dataspace.controllers.connector.utils.decorators.controller_method"

    def test_a_mixin_operation_is_logged_at_debug(self, caplog):
        from tractusx_sdk.dataspace.controllers.controller import Controller
        from tractusx_sdk.dataspace.controllers.connector.utils.mixins.base_mixins import GetControllerMixin

        class DummyController(GetControllerMixin, Controller):
            endpoint_url = "/dummy"

        adapter = MagicMock()
        with caplog.at_level(logging.DEBUG):
            DummyController(adapter).get_by_id("42")

        record = _records(caplog, self.LOGGER)[0]
        assert record.getMessage() == "Controller operation DummyController.get_by_id"
        assert record.operation == "DummyController.get_by_id"
        adapter.get.assert_called_once()

    def test_a_misuse_is_logged_before_it_is_raised(self, caplog):
        class NotAController:
            @controller_method
            def operation(self):
                return "never"

        with caplog.at_level(logging.DEBUG), pytest.raises(ValueError, match="inherits from Controller"):
            NotAController().operation()
        assert [r.levelno for r in _records(caplog, self.LOGGER)] == [logging.ERROR]


class TestCacheLogging:
    LOGGER = "tractusx_sdk.dataspace.tools.cache"

    def test_the_local_cache_reports_hits_and_misses_without_the_key(self, caplog):
        with caplog.at_level(logging.DEBUG):
            provider = cache.create_cache_provider()
            asyncio.run(provider.get("key-with-secret"))
            asyncio.run(provider.set("key-with-secret", "value-with-secret", expire=30))
            asyncio.run(provider.get("key-with-secret"))

        messages = [r.getMessage() for r in _records(caplog, self.LOGGER)]
        assert messages == [
            "Creating the cache provider for backend local",
            "Local in-memory cache initialised",
            "Local cache miss",
            "Local cache entry stored (expire=30)",
            "Local cache hit",
        ]
        assert "secret" not in _dump(caplog)

    def test_a_deletion_is_logged_without_the_key(self, caplog):
        backend = MagicMock()
        backend.delete = MagicMock(return_value=asyncio.sleep(0))
        with patch.object(cache.FastAPICache, "get_backend", return_value=backend), caplog.at_level(logging.DEBUG):
            asyncio.run(cache.LocalCache.delete(MagicMock(), "key-with-secret"))

        assert [r.getMessage() for r in _records(caplog, self.LOGGER)] == ["Local cache entry deleted"]
        assert "secret" not in _dump(caplog)

    def test_an_unknown_backend_is_logged_before_it_is_raised(self, caplog):
        with patch.object(cache, "CACHE_BACKEND", "redis"), caplog.at_level(logging.DEBUG), \
                pytest.raises(ValueError, match="Unknown CACHE_BACKEND: redis"):
            cache.create_cache_provider()
        assert [r.levelno for r in _records(caplog, self.LOGGER)] == [logging.ERROR]

    def test_a_missing_provider_is_logged_before_the_error_propagates(self, caplog):
        request = MagicMock()
        request.app.state = object()
        with caplog.at_level(logging.DEBUG), pytest.raises(AttributeError):
            cache.get_cache_provider(request)
        assert [r.levelno for r in _records(caplog, self.LOGGER)] == [logging.ERROR]

    def test_a_provider_in_the_state_is_returned_silently(self, caplog):
        request = MagicMock()
        with caplog.at_level(logging.DEBUG):
            assert cache.get_cache_provider(request) is request.app.state.cache_provider
        assert caplog.records == []
