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

"""``log_failure``: a failure is logged by the type of its exception, and the record points at the caller."""

import logging

import pytest

from tractusx_sdk._logging_helpers import log_failure

SECRET = "s3cr3t-value"
LOGGER = logging.getLogger("tractusx_sdk.test_logging_helpers")


def _failing():
    try:
        raise ConnectionError(f"Max retries exceeded with url: /api?access_token={SECRET}")
    except ConnectionError as error:
        return error


class TestLogFailure:

    def test_logs_the_type_of_the_exception_and_never_its_text_nor_its_traceback(self, caplog):
        with caplog.at_level(logging.DEBUG):
            log_failure(LOGGER, "Failed to reach %s (%s)", _failing(), "provider")

        (record,) = caplog.records
        assert record.getMessage() == "Failed to reach provider (ConnectionError)"
        assert record.levelno == logging.ERROR
        assert record.exc_info is None
        assert SECRET not in caplog.text

    @pytest.mark.parametrize("level", [logging.DEBUG, logging.WARNING])
    def test_the_level_is_the_one_given(self, caplog, level):
        with caplog.at_level(logging.DEBUG):
            log_failure(LOGGER, "Failed (%s)", _failing(), level=level)
        assert caplog.records[0].levelno == level

    def test_the_fields_are_the_documented_extra_and_the_urls_are_sanitised(self, caplog):
        with caplog.at_level(logging.DEBUG):
            log_failure(LOGGER, "Failed (%s)", _failing(), bpn="BPNL1", url=f"https://u:p@host/api?token={SECRET}", asset_id=None)

        record = caplog.records[0]
        assert (record.bpn, record.url) == ("BPNL1", "https://host/api")
        assert not hasattr(record, "asset_id")
        assert SECRET not in caplog.text

    def test_an_undocumented_field_is_rejected(self):
        with pytest.raises(TypeError):
            log_failure(LOGGER, "Failed (%s)", _failing(), headers={"Authorization": SECRET})

    def test_the_record_points_at_the_caller_and_not_at_the_helper(self, caplog):
        with caplog.at_level(logging.DEBUG):
            log_failure(LOGGER, "Failed (%s)", _failing())

        record = caplog.records[0]
        assert record.pathname.endswith("test_logging_helpers.py")
        assert record.funcName == "test_the_record_points_at_the_caller_and_not_at_the_helper"

    def test_nothing_is_rendered_while_the_level_is_disabled(self, caplog):
        class Unrenderable:
            def __str__(self):
                raise AssertionError("the message must stay lazy")

        with caplog.at_level(logging.CRITICAL):
            log_failure(LOGGER, "Failed %s (%s)", _failing(), Unrenderable(), level=logging.DEBUG)
        assert caplog.records == []
