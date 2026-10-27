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

"""The TCK command line runner owns the logging of its process, and only of its process."""

import logging
import os
from unittest import mock

import pytest

from tractusx_sdk.extensions import tck
from tractusx_sdk.extensions.tck.connector import helpers

SDK_LOGGER = "tractusx_sdk.some.module"


class _Collector(logging.Handler):
    """Stands for a handler the host application installed before the TCK ran."""

    def __init__(self):
        super().__init__(level=logging.DEBUG)
        self.records = []

    def emit(self, record):
        self.records.append(record)


@pytest.fixture
def host_logging():
    """A root logger configured by the 'application', restored afterwards."""
    root = logging.getLogger()
    saved_handlers, saved_level = root.handlers[:], root.level
    collector = _Collector()
    root.handlers = [collector]
    root.setLevel(logging.WARNING)
    try:
        yield collector
    finally:
        for handler in helpers._tck_handlers[:]:
            handler.close()
            helpers._tck_handlers.remove(handler)
        root.handlers = saved_handlers
        root.setLevel(saved_level)


def _flush(handlers):
    for handler in handlers:
        handler.flush()


class TestSetupAndFinalize:

    def test_the_handlers_are_added_next_to_the_existing_ones(self, host_logging, tmp_path):
        before = logging.getLogger().handlers[:]
        helpers.setup_tck_logging("case", str(tmp_path))

        after = logging.getLogger().handlers
        assert host_logging in after
        assert all(handler in after for handler in before)
        assert len(helpers._tck_handlers) == 2
        assert [h for h in after if h not in before] == helpers._tck_handlers

    def test_logging_is_not_configured_through_basic_config(self, host_logging, tmp_path):
        with mock.patch.object(logging, "basicConfig", side_effect=AssertionError("basicConfig was called")):
            helpers.setup_tck_logging("case", str(tmp_path))

    def test_finalize_removes_exactly_the_handlers_it_added(self, host_logging, tmp_path):
        before = logging.getLogger().handlers[:]
        _, log_file = helpers.setup_tck_logging("case", str(tmp_path))
        helpers.finalize_log(log_file, "PASS")

        assert logging.getLogger().handlers == before
        assert helpers._tck_handlers == []

    def test_finalize_does_not_close_the_hosts_handlers(self, host_logging, tmp_path):
        _, log_file = helpers.setup_tck_logging("case", str(tmp_path))
        helpers.finalize_log(log_file, "FAIL")

        logging.getLogger("host").warning("still delivered")
        assert [r.getMessage() for r in host_logging.records if r.name == "host"] == ["still delivered"]

    def test_finalize_restores_the_root_logger_level(self, host_logging, tmp_path):
        root = logging.getLogger()
        root.setLevel(logging.WARNING)
        logger, log_file = helpers.setup_tck_logging("case", str(tmp_path))
        helpers.enable_debug_logging(logger)

        helpers.finalize_log(log_file, "PASS")

        assert root.level == logging.WARNING

    def test_the_log_file_is_renamed_with_the_result(self, host_logging, tmp_path):
        logger, log_file = helpers.setup_tck_logging("case", str(tmp_path))
        logger.info("a line")
        helpers.finalize_log(log_file, "PASS")

        final = log_file.replace(".log", "_PASS.log")
        assert not os.path.exists(log_file)
        assert os.path.exists(final)
        with open(final, encoding="utf-8") as f:
            assert "a line" in f.read()

    def test_it_returns_the_logger_of_the_test_case(self, host_logging, tmp_path):
        logger, _ = helpers.setup_tck_logging("my_case", str(tmp_path))
        assert logger.name == "my_case"


class TestDebugLevel:

    def _file_text(self, log_file):
        with open(log_file, encoding="utf-8") as f:
            return f.read()

    def test_sdk_debug_records_are_left_out_by_default(self, host_logging, tmp_path):
        _, log_file = helpers.setup_tck_logging("case", str(tmp_path))
        logging.getLogger(SDK_LOGGER).debug("payload: %s", "secret-body")
        _flush(helpers._tck_handlers)

        assert "secret-body" not in self._file_text(log_file)

    def test_enabling_debug_brings_the_sdk_records_in(self, host_logging, tmp_path):
        logger, log_file = helpers.setup_tck_logging("case", str(tmp_path))
        helpers.enable_debug_logging(logger)
        logging.getLogger(SDK_LOGGER).debug("payload: %s", "secret-body")
        _flush(helpers._tck_handlers)

        text = self._file_text(log_file)
        assert "secret-body" in text
        assert "DEBUG logging enabled" in text

    def test_enabling_debug_only_touches_the_tck_handlers(self, host_logging, tmp_path):
        logger, _ = helpers.setup_tck_logging("case", str(tmp_path))
        host_level = host_logging.level
        helpers.enable_debug_logging(logger)

        assert host_logging.level == host_level
        assert all(h.level == logging.DEBUG for h in helpers._tck_handlers)

    def test_the_cli_flag_is_kept(self):
        parser = helpers.build_tck_cli_parser("description")
        assert parser.parse_args([]).debug is True
        assert parser.parse_args(["--no-debug"]).debug is False

    def test_the_boolean_debug_configuration_function_is_gone(self):
        assert not hasattr(helpers, "configure_debug_logging")
        assert hasattr(tck.connector, "enable_debug_logging")
        assert not hasattr(tck.connector, "configure_debug_logging")


class TestUploadSampleData:

    BACKEND = {"base_url": "https://backend.example/upload", "api_key": "k"}
    DATA = {"hello": "world"}

    @pytest.fixture
    def response(self):
        with mock.patch.object(helpers.requests, "post") as post:
            post.return_value = mock.Mock(status_code=201, text='{"stored": "marker-response"}')
            yield post

    def test_the_request_is_always_announced(self, response, caplog):
        logger = logging.getLogger("tck-upload")
        with caplog.at_level(logging.INFO, logger="tck-upload"):
            helpers.upload_sample_data(logger, self.BACKEND, self.DATA, header_fn=lambda title: None)

        assert "[UPLOAD REQUEST]: POST https://backend.example/upload" in caplog.text
        assert "Sample data uploaded successfully (201)" in caplog.text

    def test_bodies_appear_at_debug_level_only(self, response, caplog):
        logger = logging.getLogger("tck-upload")
        with caplog.at_level(logging.INFO, logger="tck-upload"):
            helpers.upload_sample_data(logger, self.BACKEND, self.DATA, header_fn=lambda title: None)
        assert "marker-response" not in caplog.text
        assert '"hello": "world"' not in caplog.text

        caplog.clear()
        with caplog.at_level(logging.DEBUG, logger="tck-upload"):
            helpers.upload_sample_data(logger, self.BACKEND, self.DATA, header_fn=lambda title: None)
        assert "marker-response" in caplog.text
        assert '"hello": "world"' in caplog.text

    def test_the_data_is_posted_as_json(self, response):
        helpers.upload_sample_data(logging.getLogger("tck-upload"), self.BACKEND, self.DATA, header_fn=lambda title: None)

        kwargs = response.call_args.kwargs
        assert kwargs["json"] == self.DATA
        assert kwargs["headers"]["X-Api-Key"] == "k"

    def test_the_certificate_is_verified_by_default(self, response):
        logger = logging.getLogger("tck-upload")
        helpers.upload_sample_data(logger, self.BACKEND, self.DATA, header_fn=lambda title: None)
        assert response.call_args.kwargs["verify"] is True

    def test_the_verify_flag_reaches_the_request(self, response):
        logger = logging.getLogger("tck-upload")
        helpers.upload_sample_data(logger, self.BACKEND, self.DATA, header_fn=lambda title: None, verify=False)
        assert response.call_args.kwargs["verify"] is False

        helpers.upload_sample_data(logger, self.BACKEND, self.DATA, header_fn=lambda title: None, verify=True)
        assert response.call_args.kwargs["verify"] is True

    @pytest.mark.parametrize("removed", [{"verbose": True}, {"verbose": False}])
    def test_the_verbose_argument_is_gone(self, response, removed):
        with pytest.raises(TypeError):
            helpers.upload_sample_data(logging.getLogger("tck-upload"), self.BACKEND, self.DATA, **removed)


class TestServiceInitialisation:

    CONFIG = {
        "dataspace_version": "jupiter", "base_url": "https://c.example", "dma_path": "/management",
        "api_key_header": "X-Api-Key", "api_key": "k", "bpn": "BPNL000000000001",
    }

    @pytest.mark.parametrize("initialiser, factory_method", [
        (helpers.initialize_provider_service, "get_connector_provider_service"),
        (helpers.initialize_consumer_service, "get_connector_consumer_service"),
    ])
    def test_the_services_are_built_without_logging_arguments(self, initialiser, factory_method):
        with mock.patch.object(helpers.ServiceFactory, factory_method) as factory:
            initialiser(logging.getLogger("tck-init"), dict(self.CONFIG), header_fn=lambda title: None)

        kwargs = factory.call_args.kwargs
        assert not {"verbose", "debug", "logger"} & set(kwargs)
        assert kwargs["verify_ssl"] is False
