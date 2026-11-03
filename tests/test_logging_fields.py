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

"""The helpers building the structured context of the log records."""

import logging
import re

import pytest

from tractusx_sdk._logging_fields import EXTRA_FIELDS, http_status, log_extra, safe_url

RESERVED = set(vars(logging.makeLogRecord({}))) | {"message", "asctime"}
SECRET_LIKE = re.compile(r"token|secret|password|passwd|authorization|api_?key|credential|cookie", re.IGNORECASE)


class TestSafeUrl:

    @pytest.mark.parametrize("url, expected", [
        ("https://host/api/v1?token=abc&x=1", "https://host/api/v1"),
        ("https://host:8443/api#frag", "https://host:8443/api"),
        ("https://user:secret@host/api", "https://host/api"),
        ("https://user@host:81/api?x=1", "https://host:81/api"),
        ("https://host/api;jsessionid=abc123/next", "https://host/api/next"),
        ("https://host/api?a=1;jsessionid=abc", "https://host/api"),
        ("https://[::1]:8080/api?x=1", "https://[::1]:8080/api"),
        ("/relative/path?x=1", "/relative/path"),
        ("https://host/api", "https://host/api"),
    ])
    def test_removes_everything_that_could_carry_a_secret(self, url, expected):
        assert safe_url(url) == expected

    def test_none_stays_none(self):
        assert safe_url(None) is None

    def test_an_invalid_url_never_raises_nor_echoes_the_input(self):
        result = safe_url("https://[bad-host?token=abc")
        assert result == "<invalid-url>"

    def test_is_idempotent(self):
        once = safe_url("https://u:p@host/a?x=1")
        assert safe_url(once) == once


class TestHttpStatus:

    def test_returns_the_status_code(self):
        assert http_status(type("R", (), {"status_code": 404})()) == 404

    @pytest.mark.parametrize("response", [None, object(), type("R", (), {"status_code": "200"})(),
                                          type("R", (), {"status_code": True})()])
    def test_returns_none_when_there_is_no_usable_status(self, response):
        assert http_status(response) is None


class TestLogExtra:

    def test_leaves_out_the_fields_that_are_none(self):
        assert log_extra(asset_id="a1", bpn=None) == {"asset_id": "a1"}

    def test_url_fields_are_sanitised(self):
        extra = log_extra(url="https://h/p?token=1", counter_party_address="https://u:p@cp/dsp?x=1")
        assert extra == {"url": "https://h/p", "counter_party_address": "https://cp/dsp"}

    def test_zero_values_are_kept(self):
        assert log_extra(elapsed_ms=0, status_code=0) == {"elapsed_ms": 0, "status_code": 0}

    def test_unknown_fields_are_rejected(self):
        with pytest.raises(TypeError):
            log_extra(headers={"Authorization": "x"})

    def test_no_field_collides_with_a_reserved_log_record_attribute(self):
        assert EXTRA_FIELDS.isdisjoint(RESERVED)

    def test_no_field_is_named_after_a_secret(self):
        assert [field for field in EXTRA_FIELDS if SECRET_LIKE.search(field)] == []

    def test_the_extra_can_be_attached_to_a_record(self, caplog):
        with caplog.at_level(logging.DEBUG):
            logging.getLogger("tractusx_sdk.test").debug("x", extra=log_extra(**{f: "v" for f in EXTRA_FIELDS}))
        assert {f for f in EXTRA_FIELDS if hasattr(caplog.records[0], f)} == set(EXTRA_FIELDS)
