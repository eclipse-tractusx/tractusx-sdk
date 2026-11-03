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

"""The log records of the tools: DSP policies, schema validation, operators, encoding and tracing."""

import json
import logging
from unittest.mock import MagicMock, Mock, patch

import pytest
import requests

from tractusx_sdk.dataspace.tools import tracing
from tractusx_sdk.dataspace.tools.dsp_tools import DspTools
from tractusx_sdk.dataspace.tools.encoding_tools import decode_base64_url_safe, encode_as_base64_url_safe
from tractusx_sdk.dataspace.tools.operators import op
from tractusx_sdk.dataspace.tools.tracing import Tracer
from tractusx_sdk.dataspace.tools.validate_submodels import MAX_LOGGED_ISSUES, json_validator, submodel_schema_finder
from tractusx_sdk.exceptions import (
    EmptyCatalogError, InvalidSemanticIdError, PolicyMismatchError, SchemaNotFoundError, SubmodelValidationError,
)

SECRET = "s3cr3t-value"
DSP = "tractusx_sdk.dataspace.tools.dsp_tools"
VALIDATE = "tractusx_sdk.dataspace.tools.validate_submodels"
OPERATORS = "tractusx_sdk.dataspace.tools.operators"
ENCODING = "tractusx_sdk.dataspace.tools.encoding_tools"
TRACING = "tractusx_sdk.dataspace.tools.tracing"


def _dump(caplog) -> str:
    return "\n".join(f"{r.getMessage()} {r.__dict__} {r.exc_text or ''}" for r in caplog.records)


def _records(caplog, name):
    return [r for r in caplog.records if r.name == name]


def _policy(policy_id="policy-1", action="odrl:use"):
    return {"@id": policy_id, "@type": "odrl:Offer", "odrl:permission": {"odrl:action": {"@id": action}}}


ALLOWED = [{"odrl:permission": {"odrl:action": {"@id": "odrl:use"}}}]


class TestDspToolsLogging:

    def test_a_single_dataset_with_an_acceptable_policy_is_traced_with_its_ids(self, caplog):
        catalog = {"dcat:dataset": {"@id": "asset-1", "odrl:hasPolicy": _policy()}}
        with caplog.at_level(logging.DEBUG):
            selection = DspTools.filter_assets_and_policies(catalog, ALLOWED)
        assert selection[0].asset_id == "asset-1"

        records = _records(caplog, DSP)
        assert any("single dataset of the catalog (1 allowed policies)" in r.getMessage() for r in records)
        matched = [r for r in records if "matched allowed policy at index 0" in r.getMessage()][0]
        assert (matched.policy_id, matched.asset_id) == ("policy-1", "asset-1")

    def test_a_catalog_with_several_datasets_logs_how_many_are_acceptable(self, caplog):
        catalog = {"dcat:dataset": [
            {"@id": "a1", "odrl:hasPolicy": _policy("p1")},
            {"@id": "a2", "odrl:hasPolicy": _policy("p2", action="odrl:other")},
        ]}
        with caplog.at_level(logging.DEBUG):
            assert [s.asset_id for s in DspTools.filter_assets_and_policies(catalog, ALLOWED)] == ["a1"]
        messages = [r.getMessage() for r in _records(caplog, DSP)]
        assert any("Selecting the policies of the 2 datasets" in m for m in messages)
        assert any("1 of the 2 datasets have an acceptable policy" in m for m in messages)
        rejected = [r for r in _records(caplog, DSP) if "did not match any of the 1 allowed policies" in r.getMessage()][0]
        assert (rejected.policy_id, rejected.asset_id) == ("p2", "a2")

    @pytest.mark.parametrize("catalog, expected", [
        (None, "there is no catalog"),
        ({}, "the catalog has no dataset"),
        ({"dcat:dataset": []}, "dataset list of the catalog is empty"),
    ])
    def test_an_empty_catalog_is_traced_before_it_is_raised(self, caplog, catalog, expected):
        with caplog.at_level(logging.DEBUG), pytest.raises(EmptyCatalogError):
            DspTools.filter_assets_and_policies(catalog, ALLOWED)
        assert expected in _records(caplog, DSP)[-1].getMessage()

    def test_a_rejection_is_traced_and_carries_its_evidence_in_the_error_not_in_an_error_log(self, caplog):
        catalog = {"dcat:dataset": {"@id": "a1", "odrl:hasPolicy": _policy(action="odrl:other")}}
        with caplog.at_level(logging.DEBUG), pytest.raises(PolicyMismatchError) as raised:
            DspTools.filter_assets_and_policies(catalog, ALLOWED)
        assert raised.value.evaluations
        assert "has no acceptable policy (1 rejected)" in _records(caplog, DSP)[-1].getMessage()
        # The caller decides how loud a mismatch is: the tool never goes above DEBUG
        assert [r for r in caplog.records if r.levelno > logging.DEBUG] == []

    def test_the_meaning_of_the_allow_list_is_spelled_out(self, caplog):
        catalog = {"dcat:dataset": {"@id": "a1", "odrl:hasPolicy": _policy()}}
        with caplog.at_level(logging.DEBUG):
            DspTools.filter_assets_and_policies(catalog, None)
            with pytest.raises(PolicyMismatchError):
                DspTools.filter_assets_and_policies(catalog, [])
        messages = [r.getMessage() for r in _records(caplog, DSP)]
        assert any("no allow-list: any policy is valid" in m for m in messages)
        assert any("empty allow-list: no policy is valid" in m for m in messages)
        assert any("accepted: there is no allow-list" in m for m in messages)
        assert any("allowed_policies list is empty" in m for m in messages)

    def test_a_catalog_without_the_dataset_key_is_not_empty_and_says_so(self, caplog):
        with caplog.at_level(logging.DEBUG):
            assert DspTools.is_catalog_empty({}) is False
        assert "no dataset key" in _records(caplog, DSP)[-1].getMessage()

    def test_nothing_is_logged_above_debug_by_a_successful_selection(self, caplog):
        catalog = {"dcat:dataset": {"@id": "a1", "odrl:hasPolicy": _policy()}}
        with caplog.at_level(logging.DEBUG):
            DspTools.filter_assets_and_policies(catalog, ALLOWED)
        assert {r.levelno for r in caplog.records} == {logging.DEBUG}


class _Response:
    def __init__(self, status=200, payload=None, invalid=False):
        self.status_code = status
        self._payload, self._invalid = payload, invalid

    def json(self):
        if self._invalid:
            raise ValueError("not json")
        return self._payload


SEMANTIC_ID = "urn:samm:io.catenax.part_type_information:1.0.0#PartTypeInformation"


class TestSchemaFinderLogging:

    def test_a_malformed_semantic_id_is_a_warning_before_it_is_raised(self, caplog):
        with caplog.at_level(logging.DEBUG), pytest.raises(InvalidSemanticIdError):
            submodel_schema_finder("urn:samm")
        record = _records(caplog, VALIDATE)[-1]
        assert (record.levelno, record.schema_urn) == (logging.WARNING, "urn:samm")

    def test_a_retrieved_schema_is_logged_with_its_timing_and_a_sanitised_link(self, caplog):
        with patch(f"{VALIDATE}.get", return_value=_Response(200, {"type": "object"})), caplog.at_level(logging.DEBUG):
            result = submodel_schema_finder(SEMANTIC_ID, link_core=f"https://user:{SECRET}@raw.example.com/models/")
        assert result.schema == {"type": "object"}

        retrieving, retrieved = _records(caplog, VALIDATE)
        assert "https://raw.example.com/models/io.catenax.part_type_information/" in retrieving.getMessage()
        assert (retrieved.schema_urn, retrieved.status_code) == (SEMANTIC_ID, 200) and retrieved.elapsed_ms >= 0
        assert SECRET not in _dump(caplog)

    def test_a_schema_that_is_not_found_is_an_error_before_it_is_raised(self, caplog):
        with patch(f"{VALIDATE}.get", return_value=_Response(404)), caplog.at_level(logging.DEBUG), pytest.raises(SchemaNotFoundError):
            submodel_schema_finder(SEMANTIC_ID)
        error = _records(caplog, VALIDATE)[-1]
        assert (error.levelno, error.status_code, error.schema_urn) == (logging.ERROR, 404, SEMANTIC_ID)

    def test_a_connection_failure_is_logged_with_its_traceback_and_re_raised_unchanged(self, caplog):
        failure = requests.ConnectionError("refused")
        with patch(f"{VALIDATE}.get", side_effect=failure), caplog.at_level(logging.DEBUG), pytest.raises(requests.ConnectionError) as raised:
            submodel_schema_finder(SEMANTIC_ID)
        assert raised.value is failure
        record = _records(caplog, VALIDATE)[-1]
        assert record.levelno == logging.ERROR and record.exc_info[1] is failure and record.schema_urn == SEMANTIC_ID

    def test_a_schema_that_is_not_json_is_logged_with_its_traceback(self, caplog):
        with patch(f"{VALIDATE}.get", return_value=_Response(200, invalid=True)), caplog.at_level(logging.DEBUG), \
                pytest.raises(SchemaNotFoundError):
            submodel_schema_finder(SEMANTIC_ID)
        record = _records(caplog, VALIDATE)[-1]
        assert record.levelno == logging.ERROR and record.exc_info is not None


SCHEMA = {"type": "object", "properties": {"a": {"type": "integer"}, "b": {"type": "string"}}, "required": ["a"]}


class TestJsonValidatorLogging:

    def test_a_valid_document_is_logged_at_debug(self, caplog):
        with caplog.at_level(logging.DEBUG):
            assert json_validator(SCHEMA, {"a": 1}).valid is True
        assert [r.getMessage() for r in _records(caplog, VALIDATE)] == ["The JSON document is valid"]

    def test_the_violations_are_logged_by_path_and_rule_but_never_by_value(self, caplog):
        with caplog.at_level(logging.DEBUG), pytest.raises(SubmodelValidationError):
            json_validator(SCHEMA, {"a": f"value-{SECRET}", "b": 5})
        messages = [r.getMessage() for r in _records(caplog, VALIDATE)]
        assert "The JSON document has 2 validation issue(s)" in messages
        assert "Validation issue at 'a' (type)" in messages and "Validation issue at 'b' (type)" in messages
        assert SECRET not in _dump(caplog)

    def test_a_long_list_of_violations_is_cut(self, caplog):
        schema = {"type": "array", "items": {"type": "integer"}}
        with caplog.at_level(logging.DEBUG):
            result = json_validator(schema, ["x"] * (MAX_LOGGED_ISSUES + 5), raise_on_error=False)
        assert len(result.issues) == MAX_LOGGED_ISSUES + 5
        messages = [r.getMessage() for r in _records(caplog, VALIDATE)]
        assert sum(m.startswith("Validation issue at") for m in messages) == MAX_LOGGED_ISSUES
        assert "... and 5 more validation issue(s)" in messages
        assert any("returned in the result" in m for m in messages)

    def test_an_unsupported_validation_type_is_a_warning_because_nothing_is_validated(self, caplog):
        with caplog.at_level(logging.DEBUG):
            assert json_validator(SCHEMA, {"nothing": "checked"}, validation_type="xml").valid is True
        record = _records(caplog, VALIDATE)[-1]
        assert record.levelno == logging.WARNING and "NOT validated" in record.getMessage()
        assert not any("is valid" in r.getMessage() for r in caplog.records)


class TestOperatorsLogging:

    def test_directories_are_logged_whether_created_or_already_there(self, tmp_path, caplog):
        target = str(tmp_path / "new")
        with caplog.at_level(logging.DEBUG):
            assert op.make_dir(target) is True
            assert op.make_dir(target) is False
        assert [r.getMessage().split("'")[0] for r in _records(caplog, OPERATORS)] == ["Created the directory ", "The directory "]

    def test_deleting_a_file_logs_the_outcome(self, tmp_path, caplog):
        path = tmp_path / "f.txt"
        path.write_text("x")
        with caplog.at_level(logging.DEBUG):
            assert op.delete_file(str(path)) is True
            assert op.delete_file(str(path)) is False
        messages = [r.getMessage() for r in _records(caplog, OPERATORS)]
        assert messages[0].startswith("Deleted the file") and "does not exist, nothing to delete" in messages[1]

    def test_copying_and_moving_are_logged(self, tmp_path, caplog):
        source = tmp_path / "a.txt"
        source.write_text("x")
        with caplog.at_level(logging.DEBUG):
            op.copy_file(str(source), str(tmp_path / "b.txt"))
            op.move_file(str(tmp_path / "b.txt"), str(tmp_path / "c.txt"))
        assert [r.getMessage().split(" ")[0] for r in _records(caplog, OPERATORS)] == ["Copying", "Moving"]

    def test_writing_nothing_is_logged(self, tmp_path, caplog):
        with caplog.at_level(logging.DEBUG):
            assert op.write_to_file("", str(tmp_path / "x")) is False
            assert op.write_to_file(None, str(tmp_path / "x")) is False
        assert len(_records(caplog, OPERATORS)) == 2

    def test_a_json_file_that_cannot_be_read_is_a_warning_with_the_path_and_never_the_content(self, tmp_path, caplog):
        broken = tmp_path / "broken.json"
        broken.write_text(f'{{"key": "{SECRET}" oops')
        with caplog.at_level(logging.DEBUG):
            with pytest.raises(ValueError):
                op.read_json_file(str(broken))
            with pytest.raises(FileNotFoundError):
                op.read_json_file(str(tmp_path / "missing.json"))
        records = _records(caplog, OPERATORS)
        assert [r.levelno for r in records] == [logging.WARNING, logging.WARNING]
        assert str(broken) in records[0].getMessage() and records[0].exc_info is not None
        assert SECRET not in _dump(caplog)

    def test_a_json_file_that_can_be_read_is_silent_and_its_handle_is_closed(self, tmp_path, caplog):
        good = tmp_path / "good.json"
        good.write_text('{"a": 1}')
        with caplog.at_level(logging.DEBUG):
            assert op.read_json_file(str(good)) == {"a": 1}
        assert caplog.records == []

    @pytest.mark.parametrize("source, path, sep, expected", [
        (None, "a", ".", "no object"),
        ({"a": 1}, "a", "", "no path separator"),
        ({"a": 1}, "", ".", "path is empty"),
        ({"a": {"b": 1}}, "a.c", ".", "missing 'c'"),
    ])
    def test_every_fallback_to_the_default_value_is_logged(self, caplog, source, path, sep, expected):
        with caplog.at_level(logging.DEBUG):
            assert op.get_attribute(source, path, default_value="default", path_sep=sep) == "default"
        assert expected in _records(caplog, OPERATORS)[-1].getMessage()
        assert "default" not in [a for r in caplog.records for a in (r.args or ())]

    def test_a_found_attribute_is_silent(self, caplog):
        with caplog.at_level(logging.DEBUG):
            assert op.get_attribute({"a": {"b": 1}}, "a.b") == 1
        assert caplog.records == []

    def test_a_search_without_result_is_logged_without_the_searched_value(self, caplog):
        with caplog.at_level(logging.DEBUG):
            assert op.search_element_by_field([{"id": 1}], f"id-{SECRET}") is None
            assert op.search_element_by_field([{"id": 1}], 1) == {"id": 1}
        assert len(_records(caplog, OPERATORS)) == 1 and SECRET not in _dump(caplog)

    def test_the_pure_helpers_stay_silent(self, caplog):
        with caplog.at_level(logging.DEBUG):
            op.to_json({"a": 1})
            op.json_string_to_object('{"a": 1}')
            op.join_paths("a", "b")
            op.extract_dict_values([{"value": 1}])
            op.timestamp()
        assert caplog.records == []


class TestEncodingToolsLogging:

    def test_a_round_trip_is_silent(self, caplog):
        with caplog.at_level(logging.DEBUG):
            assert decode_base64_url_safe(encode_as_base64_url_safe(f"shell-{SECRET}")) == f"shell-{SECRET}"
        assert caplog.records == []

    @pytest.mark.parametrize("encoded", [f"!!{SECRET}!!", "/w"])
    def test_a_string_that_cannot_be_decoded_is_logged_by_its_length_only(self, caplog, encoded):
        with caplog.at_level(logging.DEBUG), pytest.raises(Exception):
            decode_base64_url_safe(encoded)
        record = _records(caplog, ENCODING)[-1]
        assert record.levelno == logging.ERROR and record.exc_info is not None
        assert "characters could not be decoded" in record.getMessage()
        assert SECRET not in record.getMessage() and not any(SECRET in str(a) for a in record.args)


@pytest.fixture
def fresh_swallowed():
    """The once-per-site memory is process wide, so each test starts without it."""
    tracing._SWALLOWED_LOGGED.clear()
    yield
    tracing._SWALLOWED_LOGGED.clear()


class _Guarded:
    @property
    def elapsed(self):
        raise RuntimeError("the response has not been read")


class TestTracingLogging:

    @pytest.fixture(autouse=True)
    def _clean(self, fresh_swallowed):
        yield

    def test_creating_a_tracer_is_logged_at_debug(self, caplog):
        with caplog.at_level(logging.DEBUG):
            Tracer(name="orders", max_entries=5)
        record = _records(caplog, TRACING)[0]
        assert record.levelno == logging.DEBUG and "Tracer 'orders' created (enabled: True, max entries: 5)" == record.getMessage()

    def test_a_swallowed_exception_is_logged_once_at_debug_with_its_traceback(self, caplog):
        with caplog.at_level(logging.DEBUG):
            for _ in range(50):
                assert tracing._safe_getattr(_Guarded(), "elapsed", None) is None
        records = _records(caplog, TRACING)
        assert len(records) == 1
        assert records[0].levelno == logging.DEBUG and records[0].exc_info[0] is RuntimeError
        assert "'elapsed' of a _Guarded could not be read for the trace" in records[0].getMessage()

    def test_each_attribute_is_a_site_of_its_own(self, caplog):
        class Both:
            @property
            def one(self):
                raise RuntimeError

            @property
            def two(self):
                raise RuntimeError

        with caplog.at_level(logging.DEBUG):
            tracing._safe_getattr(Both(), "one")
            tracing._safe_getattr(Both(), "two")
            tracing._safe_getattr(Both(), "one")
        assert len(_records(caplog, TRACING)) == 2

    def test_nothing_is_done_while_debug_is_disabled_and_the_first_occurrence_is_still_logged_later(self, caplog):
        with caplog.at_level(logging.INFO):
            tracing._safe_getattr(_Guarded(), "elapsed")
        assert caplog.records == [] and tracing._SWALLOWED_LOGGED == set()

        with caplog.at_level(logging.DEBUG):
            tracing._safe_getattr(_Guarded(), "elapsed")
        assert len(_records(caplog, TRACING)) == 1

    def test_the_other_swallowing_sites_are_logged_once_each(self, caplog):
        circular = {}
        circular["self"] = circular
        with caplog.at_level(logging.DEBUG):
            for _ in range(3):
                assert tracing._headers_to_dict(object(), True, frozenset()).keys() == {"headers"}
                assert tracing._content_type(object()) is None
                assert isinstance(tracing._json_safe(circular, 100), str)

        messages = [r.getMessage() for r in _records(caplog, TRACING)]
        assert len(messages) == 3
        assert any("have no items()" in m for m in messages)
        assert any("content type could not be read" in m for m in messages)
        assert any("could not be serialized as JSON" in m for m in messages)
        assert all(r.exc_info is not None for r in _records(caplog, TRACING))

    def test_a_non_json_response_is_logged_once_however_many_are_traced(self, caplog):
        def response():
            r = requests.Response()
            r.status_code = 200
            r._content = b"<html>not json</html>"
            r.headers["Content-Type"] = "text/html"
            return r

        tracer = Tracer()
        with caplog.at_level(logging.DEBUG):
            for _ in range(20):
                tracer.complete_entry(tracer.start_entry("GET", "https://x.example.com"), response=response())
        not_json = [r for r in _records(caplog, TRACING) if "not JSON" in r.getMessage()]
        assert len(not_json) == 1 and not_json[0].levelno == logging.DEBUG

    def test_the_whole_tracing_never_logs_above_debug_nor_a_header_value(self, caplog):
        tracer = Tracer(max_entries=2)
        response = requests.Response()
        response.status_code = 500
        response._content = b'{"error": "boom"}'
        response.headers["Content-Type"] = "application/json"
        response.headers["Set-Cookie"] = f"session={SECRET}"
        with caplog.at_level(logging.DEBUG):
            for _ in range(5):
                entry = tracer.start_entry("POST", f"https://u:{SECRET}@h.example.com/x?k={SECRET}",
                                           headers={"Authorization": f"Bearer {SECRET}"}, body={"k": SECRET})
                tracer.complete_entry(entry, response=response)
        assert {r.levelno for r in caplog.records} <= {logging.DEBUG}
        assert "Authorization" not in _dump(caplog) and f"Bearer {SECRET}" not in _dump(caplog)
        assert f"session={SECRET}" not in _dump(caplog)

    def test_the_eviction_of_the_oldest_entries_is_logged_once_per_tracer(self, caplog):
        tracer = Tracer(name="small", max_entries=2)
        with caplog.at_level(logging.DEBUG):
            for _ in range(6):
                tracer.add(Mock())
        limit = [r for r in _records(caplog, TRACING) if "reached its limit" in r.getMessage()]
        assert len(limit) == 1
        assert limit[0].getMessage() == "Tracer 'small' reached its limit of 2 entries, the oldest ones are dropped from now on"
        assert len(tracer.entries) == 2

        with caplog.at_level(logging.DEBUG):
            other = Tracer(name="other", max_entries=1)
            other.add(Mock())
            other.add(Mock())
        assert len([r for r in _records(caplog, TRACING) if "reached its limit" in r.getMessage()]) == 2

    def test_a_traced_call_with_a_bad_signature_is_logged_once_and_still_reaches_the_callee(self, caplog):
        calls = []

        @tracing.traced_http("GET")
        def helper(url, verify=True):
            calls.append(url)
            return Mock(status_code=200, headers={}, content=b"{}", text="{}", json=lambda: {})

        tracer = Tracer()
        with caplog.at_level(logging.DEBUG):
            for _ in range(3):
                with pytest.raises(TypeError):
                    helper("https://x.example.com", unexpected=True, tracer=tracer)
        assert calls == []
        bind = [r for r in _records(caplog, TRACING) if "do not match its signature" in r.getMessage()]
        assert len(bind) == 1 and bind[0].exc_info is not None

    def test_the_tracing_still_works_while_it_logs(self):
        tracer = Tracer()
        entry = tracer.start_entry("GET", "https://x.example.com")
        response = requests.Response()
        response.status_code = 200
        response._content = b'{"ok": true}'
        response.headers["Content-Type"] = "application/json"
        tracer.complete_entry(entry, response=response)
        assert entry.response["body"] == {"ok": True}
