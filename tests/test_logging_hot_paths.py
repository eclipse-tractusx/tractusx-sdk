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
The logging of the hot paths costs nothing while its level is disabled: no URL is sanitised and no structured
context is built. The same paths still log what they logged once the level is enabled.
"""

import logging
from importlib import import_module
from unittest.mock import MagicMock, patch

import pytest

from tractusx_sdk.dataspace.adapters.adapter import Adapter
from tractusx_sdk.dataspace.managers.connection.memory import MemoryConnectionManager
from tractusx_sdk.dataspace.tools.http_tools import HttpTools

HELPERS = "tractusx_sdk._logging_helpers"
CONTROLLER_METHOD = "tractusx_sdk.dataspace.controllers.connector.utils.decorators.controller_method"
MEMORY_MANAGER = "tractusx_sdk.dataspace.managers.connection.memory.memory_connection_manager"
AAS_SERVICE = "tractusx_sdk.industry.services.aas_service"


@pytest.fixture
def forbid(monkeypatch):
    """Makes the building of a log record fail the test: it must not happen while the level is disabled."""

    def forbidden(*args, **kwargs):
        raise AssertionError("A log record was built while its level is disabled")

    def apply(module_name: str, *names: str):
        module = import_module(module_name)
        for name in names:
            monkeypatch.setattr(module, name, forbidden)

    return apply


class TestHttp:

    def test_a_request_builds_no_record_while_even_the_warnings_are_disabled(self, caplog, forbid):
        forbid(HELPERS, "safe_url", "log_extra")
        with patch("requests.get", return_value=MagicMock(status_code=500)), caplog.at_level(logging.ERROR):
            assert HttpTools.do_get("https://host/api?token=1").status_code == 500
        assert caplog.records == []

    def test_a_failure_builds_no_record_while_debug_is_disabled(self, caplog, forbid):
        forbid(HELPERS, "safe_url", "log_extra")
        with patch("requests.get", side_effect=ConnectionError("down")), caplog.at_level(logging.WARNING):
            with pytest.raises(ConnectionError):
                HttpTools.do_get("https://host/api?token=1")
        assert caplog.records == []

    def test_a_server_failure_is_still_a_sanitised_warning_while_debug_is_disabled(self, caplog):
        with patch("requests.get", return_value=MagicMock(status_code=503)), caplog.at_level(logging.WARNING):
            HttpTools.do_get("https://host/api?token=s3cr3t")
        (record,) = caplog.records
        assert (record.levelno, record.url, record.status_code) == (logging.WARNING, "https://host/api", 503)
        assert "s3cr3t" not in caplog.text

    def test_the_url_given_by_name_is_logged_like_the_one_given_by_position(self, caplog):
        with patch("requests.get", return_value=MagicMock(status_code=200)), caplog.at_level(logging.DEBUG):
            HttpTools.do_get(url="https://host/by-name?token=1")
            HttpTools.do_get("https://host/by-position?token=1")
        assert [r.url for r in caplog.records if r.getMessage().startswith("HTTP GET") and "->" not in r.getMessage()] == [
            "https://host/by-name", "https://host/by-position"]

    def test_the_adapter_builds_no_record_while_the_level_is_disabled(self, caplog, forbid):
        adapter = Adapter(base_url="https://connector.example.com/")
        forbid(HELPERS, "safe_url", "log_extra")
        forbid("tractusx_sdk.dataspace.adapters.adapter", "safe_url", "log_extra")
        with patch.object(adapter.session, "request", return_value=MagicMock(status_code=200)), caplog.at_level(logging.ERROR):
            adapter.get("x?token=1")
        adapter.close()
        assert caplog.records == []


class TestOtherHotPaths:

    def test_a_controller_operation_builds_no_record_while_debug_is_disabled(self, caplog, forbid):
        from tractusx_sdk.dataspace.controllers.connector.utils.mixins.base_mixins import GetControllerMixin
        from tractusx_sdk.dataspace.controllers.controller import Controller

        class DummyController(GetControllerMixin, Controller):
            endpoint_url = "/dummy"

        forbid(CONTROLLER_METHOD, "log_extra")
        with caplog.at_level(logging.INFO):
            DummyController(MagicMock()).get_by_id("42")
        assert caplog.records == []

    def test_a_cache_lookup_builds_no_record_while_debug_is_disabled(self, caplog, forbid):
        forbid(MEMORY_MANAGER, "log_extra", "safe_url")
        manager = MemoryConnectionManager()
        with caplog.at_level(logging.INFO):
            assert manager.get_connection("BPNL1", "https://cp", "q", "p") == {}
        assert caplog.records == []

    def test_a_cache_miss_is_still_logged_at_debug(self, caplog):
        manager = MemoryConnectionManager()
        with caplog.at_level(logging.DEBUG):
            manager.get_connection("BPNL1", "https://cp?token=1", "q", "p")
        miss = [r for r in caplog.records if "Cache miss" in r.getMessage()][0]
        assert miss.counter_party_address == "https://cp"

    def test_a_registry_operation_builds_no_record_while_its_level_is_disabled(self, caplog, forbid):
        aas_service = import_module(AAS_SERVICE)

        @aas_service._logged("do it")
        def operation(self, aas_identifier):
            return "ok"

        forbid(AAS_SERVICE, "log_extra")
        with caplog.at_level(logging.WARNING):
            assert operation(object(), "shell-1") == "ok"
        assert caplog.records == []

    def test_a_registry_operation_still_logs_its_identifiers_at_debug(self, caplog):
        aas_service = import_module(AAS_SERVICE)

        @aas_service._logged("do it", writes=True)
        def operation(self, aas_identifier):
            return "ok"

        with caplog.at_level(logging.DEBUG):
            operation(object(), "shell-1")
        assert [(r.levelno, r.aas_id) for r in caplog.records] == [(logging.DEBUG, "shell-1"), (logging.INFO, "shell-1")]

    def test_a_registry_operation_that_is_called_wrongly_still_raises_its_own_error(self, caplog):
        aas_service = import_module(AAS_SERVICE)

        @aas_service._logged("do it")
        def operation(self, aas_identifier):
            return "ok"

        with caplog.at_level(logging.DEBUG), pytest.raises(TypeError):
            operation(object())
