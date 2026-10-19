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

"""The log records of the submodel adapters (S3, file system, HTTP), their factory and the Digital Twin Registry service."""

import json
import logging
from unittest.mock import MagicMock, Mock, patch

import boto3
import httpx
import pytest
from botocore.exceptions import ClientError
from moto import mock_aws
from requests import HTTPError

from tractusx_sdk.dataspace.managers.auth_manager import AuthManager
from tractusx_sdk.industry.adapters.submodel_adapter_factory import SubmodelAdapterFactory
from tractusx_sdk.industry.adapters.submodel_adapters import FileSystemAdapter, HttpSubmodelAdapter, S3Adapter
from tractusx_sdk.industry.models.aas.v3 import Result
from tractusx_sdk.industry.services.aas_service import AasService

SECRET = "s3cr3t-value"
ACCESS_KEY = f"AKIA-{SECRET}"
S3 = "tractusx_sdk.industry.adapters.submodel_adapters.s3_adapter"
FS = "tractusx_sdk.industry.adapters.submodel_adapters.file_system_adapter"
HTTP = "tractusx_sdk.industry.adapters.submodel_adapters.http_submodel_adapter"
FACTORY = "tractusx_sdk.industry.adapters.submodel_adapter_factory"
AAS = "tractusx_sdk.industry.services.aas_service"
METADATA = {"path": "a/b.json", "semantic_id": "urn:sem", "submodel_id": "sm-1"}


def _dump(caplog) -> str:
    return "\n".join(f"{r.getMessage()} {r.__dict__} {r.exc_text or ''}" for r in caplog.records)


def _records(caplog, name):
    return [r for r in caplog.records if r.name == name]


def _client_error(code, message):
    return ClientError({"Error": {"Code": code, "Message": message}}, "GetObject")


@pytest.fixture
def bucket():
    with mock_aws():
        boto3.client("s3", region_name="eu-central-1").create_bucket(
            Bucket="bkt", CreateBucketConfiguration={"LocationConstraint": "eu-central-1"})
        yield "bkt"


class TestS3AdapterLogging:

    @pytest.fixture
    def adapter(self, bucket):
        return S3Adapter(bucket_name=bucket, region_name="eu-central-1", key_pattern="{path}")

    def test_the_credentials_are_never_logged_only_where_they_come_from(self, bucket, caplog):
        with caplog.at_level(logging.DEBUG):
            S3Adapter(bucket_name=bucket, region_name="eu-central-1", endpoint_url=f"https://user:{SECRET}@s3.example.com/?k={SECRET}",
                      aws_access_key_id=ACCESS_KEY, aws_secret_access_key=f"secret-{SECRET}")
        record = _records(caplog, S3)[0]
        assert record.getMessage() == ("S3 adapter initialised for bucket 'bkt' (region eu-central-1, endpoint https://s3.example.com/, "
                                       "credentials from the configuration)")
        assert record.adapter_type == "S3Adapter" and record.url == "https://s3.example.com/"
        assert SECRET not in _dump(caplog)

    def test_credentials_from_the_environment_are_noted(self, bucket, caplog):
        with caplog.at_level(logging.DEBUG):
            S3Adapter(bucket_name=bucket, region_name="eu-central-1")
        assert "credentials from the environment or the IAM role" in _records(caplog, S3)[0].getMessage()

    @pytest.mark.parametrize("kwargs", [
        {"bucket_name": " "}, {"key_pattern": " "}, {"aws_access_key_id": ACCESS_KEY},
    ])
    def test_an_invalid_configuration_is_logged_before_it_is_raised_without_the_credentials(self, bucket, caplog, kwargs):
        arguments = {"bucket_name": bucket, "region_name": "eu-central-1", **kwargs}
        with caplog.at_level(logging.DEBUG), pytest.raises(ValueError):
            S3Adapter(**arguments)
        assert _records(caplog, S3)[-1].levelno == logging.ERROR
        assert SECRET not in _dump(caplog)

    def test_a_missing_boto3_is_logged_before_it_is_raised(self, caplog):
        with patch.dict("sys.modules", {"boto3": None}), caplog.at_level(logging.DEBUG), pytest.raises(ImportError):
            S3Adapter(bucket_name="b", region_name="r")
        assert _records(caplog, S3)[-1].levelno == logging.ERROR

    def test_the_whole_lifecycle_is_logged_and_the_content_never(self, adapter, caplog):
        with caplog.at_level(logging.DEBUG):
            adapter.write_json(METADATA, {"secret": SECRET})
            assert adapter.read(METADATA) == {"secret": SECRET}
            adapter.write({"path": "raw.bin"}, f"raw-{SECRET}".encode())
            assert adapter.exists(METADATA) is True
            assert adapter.list_contents() == ["a/b.json", "raw.bin"]
            assert adapter.list_contents("a/") == ["a/b.json"]
            adapter.delete(METADATA)
            assert adapter.exists(METADATA) is False

        messages = [r.getMessage() for r in _records(caplog, S3)]
        assert any(m.startswith("S3 JSON write: bucket 'bkt', key 'a/b.json', ") and m.endswith(" bytes") for m in messages)
        assert any(m == "S3 read: bucket 'bkt', key 'a/b.json'" for m in messages)
        assert any(m.startswith("S3 write: bucket 'bkt', key 'raw.bin', ") and m.endswith(" bytes") for m in messages)
        assert any("no prefix given, listing the whole bucket" in m for m in messages)
        assert any("2 object(s) in bucket 'bkt' with prefix ''" in m for m in messages)
        assert any("1 object(s) in bucket 'bkt' with prefix 'a/'" in m for m in messages)
        assert any(m == "S3 delete: bucket 'bkt', key 'a/b.json'" for m in messages)
        assert any("does not exist in bucket 'bkt'" in m for m in messages)
        assert SECRET not in _dump(caplog)
        assert all(r.levelno == logging.DEBUG for r in _records(caplog, S3))

    def test_a_missing_object_is_an_expected_outcome_logged_at_debug(self, adapter, caplog):
        with caplog.at_level(logging.DEBUG), pytest.raises(FileNotFoundError):
            adapter.read({"path": "nope.json"})
        assert [r.levelno for r in _records(caplog, S3)] == [logging.DEBUG, logging.DEBUG]
        assert "does not exist" in _records(caplog, S3)[-1].getMessage()

    @pytest.mark.parametrize("operation, expected_exception", [
        (lambda a: a.read(METADATA), ClientError),
        (lambda a: a.exists(METADATA), ClientError),
        (lambda a: a.write(METADATA, b"x"), RuntimeError),
        (lambda a: a.write_json(METADATA, {}), RuntimeError),
        (lambda a: a.delete(METADATA), RuntimeError),
        (lambda a: a.list_contents(), RuntimeError),
    ])
    def test_a_store_failure_logs_the_error_code_only_never_the_message_nor_a_traceback(self, adapter, caplog, operation, expected_exception):
        failure = _client_error("AccessDenied", f"denied for key {ACCESS_KEY} signature {SECRET}")
        adapter.client = Mock()
        for method in ("get_object", "head_object", "put_object", "delete_object", "get_paginator"):
            getattr(adapter.client, method).side_effect = failure

        with caplog.at_level(logging.DEBUG), pytest.raises(expected_exception):
            operation(adapter)

        error = [r for r in _records(caplog, S3) if r.levelno == logging.ERROR][0]
        assert "(AccessDenied)" in error.getMessage() and error.exc_info is None
        assert SECRET not in _dump(caplog) and ACCESS_KEY not in _dump(caplog)

    def test_an_error_without_a_code_is_logged_as_unknown(self, adapter, caplog):
        adapter.client = Mock()
        adapter.client.put_object.side_effect = adapter.client_error({"Error": {}}, "PutObject")
        with caplog.at_level(logging.DEBUG), pytest.raises(RuntimeError):
            adapter.write(METADATA, b"x")
        assert "(Unknown)" in [r for r in _records(caplog, S3) if r.levelno == logging.ERROR][0].getMessage()

    @pytest.mark.parametrize("metadata, content, exception", [
        ("not a mapping", None, TypeError),
        ({"other": "x"}, None, KeyError),
        ({"path": " "}, None, ValueError),
    ])
    def test_an_unresolvable_key_is_a_warning_before_it_is_raised(self, adapter, caplog, metadata, content, exception):
        with caplog.at_level(logging.DEBUG), pytest.raises(exception):
            adapter.read(metadata)
        assert _records(caplog, S3)[-1].levelno == logging.WARNING

    def test_invalid_content_is_a_warning_before_it_is_raised(self, adapter, caplog):
        with caplog.at_level(logging.DEBUG):
            with pytest.raises(TypeError):
                adapter.write(METADATA, "not bytes")
            with pytest.raises(TypeError):
                adapter.write_json(METADATA, ["not", "a", "mapping"])
        assert [r.levelno for r in _records(caplog, S3)] == [logging.WARNING, logging.WARNING]


class TestFileSystemAdapterLogging:

    @pytest.fixture
    def adapter(self, tmp_path):
        return FileSystemAdapter(root_path=str(tmp_path), path_pattern="{path}")

    def test_the_default_pattern_is_noted(self, tmp_path, caplog):
        with caplog.at_level(logging.DEBUG):
            FileSystemAdapter(root_path=str(tmp_path))
        messages = [r.getMessage() for r in _records(caplog, FS)]
        assert messages[0] == "No path pattern given, using the default '{path}'"
        assert messages[1].startswith(f"FileSystem submodel adapter initialized at '{tmp_path}'")

    def test_an_invalid_pattern_is_logged_before_it_is_raised(self, tmp_path, caplog):
        with caplog.at_level(logging.DEBUG), pytest.raises(ValueError):
            FileSystemAdapter(root_path=str(tmp_path), path_pattern=" ")
        assert _records(caplog, FS)[-1].levelno == logging.ERROR

    def test_a_storage_path_that_cannot_be_written_is_logged_with_its_traceback(self, tmp_path, caplog):
        with patch(f"{FS}.os.access", return_value=False), caplog.at_level(logging.DEBUG), pytest.raises(PermissionError):
            FileSystemAdapter(root_path=str(tmp_path))
        record = _records(caplog, FS)[-1]
        assert record.levelno == logging.ERROR and record.exc_info is not None and record.adapter_type == "FileSystemAdapter"

    def test_a_storage_path_that_cannot_be_created_is_logged_with_its_traceback(self, tmp_path, caplog):
        with patch(f"{FS}.Path.mkdir", side_effect=OSError("disk full")), caplog.at_level(logging.DEBUG), pytest.raises(RuntimeError):
            FileSystemAdapter(root_path=str(tmp_path / "x"))
        assert _records(caplog, FS)[-1].exc_info is not None

    def test_every_operation_is_logged_by_relative_path_and_the_content_never(self, adapter, tmp_path, caplog):
        with caplog.at_level(logging.DEBUG):
            adapter.write_json({"path": "d/a.json"}, {"secret": SECRET})
            assert adapter.read({"path": "d/a.json"}) == {"secret": SECRET}
            adapter.write({"path": "d/raw.bin"}, f"raw-{SECRET}".encode())
            assert adapter.exists({"path": "d/a.json"}) is True
            assert len(adapter.list_contents("d")) == 2
            adapter.delete({"path": "d/a.json"})
            adapter.delete({"path": "d/raw.bin"})

        messages = [r.getMessage() for r in _records(caplog, FS)]
        assert "File system JSON write: 'd/a.json'" in messages
        assert "File system read: 'd/a.json'" in messages
        assert any(m.startswith("File system write: 'd/raw.bin', ") and m.endswith(" bytes") for m in messages)
        assert "File system exists: 'd/a.json' -> True" in messages
        assert "File system list: 2 file(s) in 'd'" in messages
        assert "File system delete: 'd/a.json'" in messages
        assert "Removed the empty directory 'd'" in messages
        assert SECRET not in _dump(caplog) and str(tmp_path) not in "".join(m for m in messages if "d/" in m)

    def test_an_unreadable_file_is_a_warning_with_the_path_and_never_the_content(self, adapter, tmp_path, caplog):
        (tmp_path / "bad.json").write_text(f'{{"k": "{SECRET}" oops')
        with caplog.at_level(logging.DEBUG), pytest.raises(ValueError):
            adapter.read({"path": "bad.json"})
        assert SECRET not in _dump(caplog)
        assert any(r.levelno == logging.WARNING for r in caplog.records)

    @pytest.mark.parametrize("metadata, exception", [("no mapping", TypeError), ({"other": "x"}, KeyError), ({"path": " "}, ValueError)])
    def test_an_unresolvable_path_is_a_warning_before_it_is_raised(self, adapter, caplog, metadata, exception):
        with caplog.at_level(logging.DEBUG), pytest.raises(exception):
            adapter.exists(metadata)
        assert _records(caplog, FS)[-1].levelno == logging.WARNING

    def test_invalid_content_is_a_warning_before_it_is_raised(self, adapter, caplog):
        with caplog.at_level(logging.DEBUG):
            with pytest.raises(TypeError):
                adapter.write({"path": "x"}, "text")
            with pytest.raises(TypeError):
                adapter.write_json({"path": "x"}, [1])
        assert [r.levelno for r in _records(caplog, FS)] == [logging.WARNING, logging.WARNING]


def _http_response(status=200, payload=None, text=""):
    response = Mock(status_code=status, content=b"x" if payload is not None or text else b"", text=text)
    response.json.return_value = payload
    return response


class TestHttpSubmodelAdapterLogging:
    URL = "https://user:" + SECRET + "@submodels.example.com"

    @pytest.fixture
    def adapter(self):
        adapter = HttpSubmodelAdapter(base_url=self.URL, api_path="/api", auth_type="bearer", auth_token=f"token-{SECRET}")
        adapter.client = Mock()
        return adapter

    def test_creation_logs_the_kind_of_authentication_but_never_the_token(self, caplog):
        with caplog.at_level(logging.DEBUG):
            HttpSubmodelAdapter(base_url=self.URL, auth_type="apikey", auth_key_name="X-Secret-Header", auth_token=f"token-{SECRET}",
                                verify_ssl=False)
        message = _records(caplog, HTTP)[0].getMessage()
        assert message == ("HTTP submodel adapter initialised for https://submodels.example.com "
                           "(auth: apikey, timeout: 30s, TLS verification: False)")
        assert SECRET not in _dump(caplog) and "X-Secret-Header" not in _dump(caplog)

    @pytest.mark.parametrize("kwargs", [{"auth_type": "oauth"}, {"auth_type": "apikey"}, {"url_pattern": " "}])
    def test_an_invalid_configuration_is_logged_before_it_is_raised(self, caplog, kwargs):
        with caplog.at_level(logging.DEBUG), pytest.raises(ValueError):
            HttpSubmodelAdapter(base_url="https://x.example.com", **kwargs)
        assert _records(caplog, HTTP)[-1].levelno == logging.ERROR

    def test_a_request_logs_its_line_and_outcome_with_a_sanitised_url_and_no_credentials(self, adapter, caplog):
        adapter.client.get.return_value = _http_response(200, {"k": SECRET})
        with caplog.at_level(logging.DEBUG):
            assert adapter.read(METADATA) == {"k": SECRET}

        request, outcome = [r for r in _records(caplog, HTTP) if r.getMessage().startswith("HTTP ")]
        assert request.getMessage() == "HTTP GET https://submodels.example.com/api/urn%3Asem/sm-1/submodel"
        assert (request.http_method, request.adapter_type) == ("GET", "HttpSubmodelAdapter")
        assert (outcome.status_code, outcome.levelno) == (200, logging.DEBUG) and outcome.elapsed_ms >= 0
        assert SECRET not in _dump(caplog)

    @pytest.mark.parametrize("operation, client_method, method", [
        (lambda a: a.write(METADATA, f"raw-{SECRET}".encode()), "post", "POST"),
        (lambda a: a.write_json(METADATA, {"k": SECRET}), "post", "POST"),
        (lambda a: a.delete(METADATA), "delete", "DELETE"),
        (lambda a: a.exists(METADATA), "head", "HEAD"),
    ])
    def test_every_operation_is_logged_and_the_body_never(self, adapter, caplog, operation, client_method, method):
        getattr(adapter.client, client_method).return_value = _http_response(204)
        with caplog.at_level(logging.DEBUG):
            operation(adapter)
        assert any(r.getMessage().startswith(f"HTTP {method} https://submodels.example.com/") for r in _records(caplog, HTTP))
        assert SECRET not in _dump(caplog)

    @pytest.mark.parametrize("status, raised, level", [
        (404, FileNotFoundError, logging.DEBUG),
        (400, ValueError, logging.WARNING),
        (422, ValueError, logging.WARNING),
        (401, PermissionError, logging.WARNING),
        (403, PermissionError, logging.WARNING),
        (409, RuntimeError, logging.WARNING),
    ])
    def test_a_client_error_is_logged_at_the_level_it_deserves(self, adapter, caplog, status, raised, level):
        adapter.client.get.return_value = _http_response(status, {"error": f"body {SECRET}"})
        with caplog.at_level(logging.DEBUG), pytest.raises(raised):
            adapter.read(METADATA)
        last = _records(caplog, HTTP)[-1]
        assert (last.levelno, last.status_code) == (level, status)
        # Nothing at all above what the status deserves, and never the body
        assert max(r.levelno for r in _records(caplog, HTTP)) == level
        assert SECRET not in _dump(caplog)

    def test_a_server_failure_is_a_warning_once(self, adapter, caplog):
        adapter.client.get.return_value = _http_response(503, text="down")
        with caplog.at_level(logging.DEBUG), pytest.raises(RuntimeError, match="Server error"):
            adapter.read(METADATA)
        warnings = [r for r in _records(caplog, HTTP) if r.levelno == logging.WARNING]
        assert len(warnings) == 1 and warnings[0].status_code == 503

    def test_a_connection_failure_is_logged_by_exception_type_and_converted_as_before(self, adapter, caplog):
        adapter.client.get.side_effect = httpx.ConnectError(f"cannot connect to {self.URL}?token={SECRET}")
        with caplog.at_level(logging.DEBUG), pytest.raises(ConnectionError):
            adapter.read(METADATA)
        error = [r for r in _records(caplog, HTTP) if r.levelno == logging.ERROR][0]
        assert "(ConnectError)" in error.getMessage() and error.exc_info is None
        assert SECRET not in _dump(caplog)

    def test_a_body_that_is_not_json_is_logged_by_type_only(self, adapter, caplog):
        response = _http_response(200, text="not json")
        response.json.side_effect = ValueError(f"bad {SECRET}")
        adapter.client.get.return_value = response
        with caplog.at_level(logging.DEBUG):
            assert adapter.read(METADATA) is None
        assert any("not valid JSON (ValueError)" in r.getMessage() for r in _records(caplog, HTTP))
        assert SECRET not in _dump(caplog)

    def test_a_request_without_a_token_notes_it(self, caplog):
        adapter = HttpSubmodelAdapter(base_url="https://x.example.com", auth_type="bearer")
        adapter.client = Mock()
        adapter.client.get.return_value = _http_response(200, {})
        with caplog.at_level(logging.DEBUG):
            adapter.read(METADATA)
        assert any("no token is configured" in r.getMessage() for r in _records(caplog, HTTP))

    @pytest.mark.parametrize("metadata, exception", [
        ("no mapping", TypeError), ({"semantic_id": " "}, ValueError), ({"semantic_id": 5}, TypeError), ({"semantic_id": "s"}, KeyError),
    ])
    def test_unusable_metadata_is_a_warning_before_it_is_raised(self, adapter, caplog, metadata, exception):
        with caplog.at_level(logging.DEBUG), pytest.raises(exception):
            adapter.read(metadata)
        assert _records(caplog, HTTP)[-1].levelno == logging.WARNING

    def test_invalid_content_is_a_warning_before_it_is_raised(self, adapter, caplog):
        with caplog.at_level(logging.DEBUG):
            with pytest.raises(TypeError):
                adapter.write(METADATA, "text")
            with pytest.raises(TypeError):
                adapter.write_json(METADATA, [1])
        assert [r.levelno for r in _records(caplog, HTTP)] == [logging.WARNING, logging.WARNING]


class TestSubmodelAdapterFactoryLogging:

    def test_creating_an_adapter_logs_the_names_of_the_settings_never_the_values(self, bucket, caplog):
        with caplog.at_level(logging.DEBUG):
            adapter = SubmodelAdapterFactory.from_config("s3", {
                "bucket_name": bucket, "region_name": "eu-central-1",
                "aws_access_key_id": ACCESS_KEY, "aws_secret_access_key": f"secret-{SECRET}"})
        assert isinstance(adapter, S3Adapter)

        messages = [r.getMessage() for r in _records(caplog, FACTORY)]
        assert messages[0].startswith("Resolved S3Adapter from ")
        assert messages[1] == ("Creating a 's3' adapter with the settings "
                               "['aws_access_key_id', 'aws_secret_access_key', 'bucket_name', 'region_name']")
        assert messages[-1] == "Created a 's3' adapter (S3Adapter)"
        assert SECRET not in _dump(caplog)

    @pytest.mark.parametrize("adapter_type, config, exception, expected", [
        ("file_system", "not a mapping", TypeError, "must be a mapping"),
        ("file_system", {"unknown_setting": SECRET}, ValueError, "Unsupported setting 'unknown_setting'"),
        ("file_system", {"root_path": 5}, TypeError, "should be a str, got a int"),
    ])
    def test_an_invalid_configuration_is_a_warning_before_it_is_raised(self, caplog, adapter_type, config, exception, expected):
        with caplog.at_level(logging.DEBUG), pytest.raises(exception):
            SubmodelAdapterFactory.from_config(adapter_type, config)
        assert expected in _records(caplog, FACTORY)[-1].getMessage()
        assert _records(caplog, FACTORY)[-1].levelno == logging.WARNING
        assert SECRET not in _dump(caplog)

    def test_an_unsupported_type_is_an_error_before_it_is_raised(self, caplog):
        with caplog.at_level(logging.DEBUG), pytest.raises(ValueError):
            SubmodelAdapterFactory.from_config("ftp", {})
        error = _records(caplog, FACTORY)[-1]
        assert error.levelno == logging.ERROR and "Unsupported adapter type 'ftp'" in error.getMessage()

    def test_a_missing_adapter_class_and_an_import_failure_are_logged_with_their_traceback(self, caplog):
        with patch(f"{FACTORY}.import_module", return_value=object()), caplog.at_level(logging.DEBUG), pytest.raises(AttributeError):
            SubmodelAdapterFactory.from_config("s3", {})
        assert _records(caplog, FACTORY)[-1].exc_info is not None
        caplog.clear()
        with patch(f"{FACTORY}.import_module", side_effect=ImportError("x")), caplog.at_level(logging.DEBUG), pytest.raises(ImportError):
            SubmodelAdapterFactory.from_config("s3", {})
        assert _records(caplog, FACTORY)[-1].exc_info is not None

    def test_registering_and_unregistering_are_milestones(self, caplog):
        class Custom:
            @classmethod
            def builder(cls):
                return Mock()

        try:
            with caplog.at_level(logging.DEBUG):
                SubmodelAdapterFactory.register_adapter("custom_phase_e", adapter_class=Custom)
                SubmodelAdapterFactory.register_adapter("custom_phase_e", builder_factory=lambda: Mock(), overwrite=True)
                SubmodelAdapterFactory._get_adapter_builder("custom_phase_e")
                SubmodelAdapterFactory.unregister_adapter("custom_phase_e")
                SubmodelAdapterFactory.unregister_adapter("custom_phase_e")
            messages = [(r.levelno, r.getMessage()) for r in _records(caplog, FACTORY)]
            assert (logging.INFO, "Registered the adapter type 'custom_phase_e' through the class Custom") in messages
            assert (logging.INFO, "Overwriting the registered adapter type 'custom_phase_e'") in messages
            assert (logging.INFO, "Registered the adapter type 'custom_phase_e' through a builder factory") in messages
            assert (logging.DEBUG, "The adapter type 'custom_phase_e' is not a built-in one, using its registered builder") in messages
            assert (logging.INFO, "Unregistered the adapter type 'custom_phase_e'") in messages
            assert (logging.DEBUG, "The adapter type 'custom_phase_e' was not registered, nothing to unregister") in messages
        finally:
            SubmodelAdapterFactory.unregister_adapter("custom_phase_e")

    @pytest.mark.parametrize("call, exception", [
        (lambda f: f.register_adapter("x"), ValueError),
        (lambda f: f.register_adapter("x", builder_factory=lambda: 1, adapter_class=object), ValueError),
        (lambda f: f.register_adapter("x", builder_factory=5), TypeError),
        (lambda f: f.register_adapter("x", adapter_class=object), TypeError),
        (lambda f: f.register_adapter(" "), ValueError),
    ])
    def test_an_invalid_registration_is_a_warning_before_it_is_raised(self, caplog, call, exception):
        with caplog.at_level(logging.DEBUG), pytest.raises(exception):
            call(SubmodelAdapterFactory)
        assert _records(caplog, FACTORY)[-1].levelno == logging.WARNING

    def test_registering_twice_without_overwrite_is_a_warning_before_it_is_raised(self, caplog):
        SubmodelAdapterFactory.register_adapter("twice_phase_e", builder_factory=lambda: Mock())
        try:
            with caplog.at_level(logging.DEBUG), pytest.raises(ValueError, match="already registered"):
                SubmodelAdapterFactory.register_adapter("twice_phase_e", builder_factory=lambda: Mock())
            assert _records(caplog, FACTORY)[-1].levelno == logging.WARNING
        finally:
            SubmodelAdapterFactory.unregister_adapter("twice_phase_e")


AAS_ID = "urn:uuid:11111111-1111-1111-1111-111111111111"


class TestAasServiceLogging:

    @pytest.fixture
    def service(self):
        auth = AuthManager(configured_api_key=f"key-{SECRET}", auth_enabled=True)
        return AasService(base_url=f"https://dtr.example.com?token={SECRET}", base_lookup_url="https://lookup.example.com", api_path="/api/v3",
                          auth_service=auth)

    def _response(self, status=200, payload=None):
        response = Mock(status_code=status)
        response.json.return_value = payload if payload is not None else {}
        if status >= 400:
            response.raise_for_status.side_effect = HTTPError(f"{status} for {SECRET}")
        return response

    def test_creation_logs_the_kind_of_authentication_and_never_the_key(self, service, caplog):
        with caplog.at_level(logging.DEBUG):
            AasService(base_url="https://dtr.example.com", base_lookup_url="https://l.example.com", api_path="/api",
                       auth_service=AuthManager(configured_api_key=f"key-{SECRET}", auth_enabled=True))
        messages = [r.getMessage() for r in _records(caplog, AAS)]
        assert "DTR: no session given, using a new requests.Session" in messages
        assert ("DTR service created for https://dtr.example.com/api (lookup https://l.example.com/api, "
                "authentication: AuthManager, TLS verification: True)") in messages
        assert SECRET not in _dump(caplog)

    def test_a_non_2xx_answer_is_returned_as_a_result_and_logged_at_debug_not_as_a_warning(self, service, caplog):
        error = {"messages": [{"code": "404", "messageType": "Error", "text": f"not found {SECRET}", "timestamp": "2025-01-01T00:00:00Z"}]}
        with patch(f"{AAS}.HttpTools") as http, caplog.at_level(logging.DEBUG):
            http.do_get_with_session.return_value = self._response(404, error)
            result = service.get_asset_administration_shell_descriptor_by_id(AAS_ID, bpn="BPNL000000000001")

        assert isinstance(result, Result)
        records = _records(caplog, AAS)
        called, answered = records[-2], records[-1]
        assert called.getMessage() == "DTR: get a shell descriptor"
        assert (called.aas_id, called.bpn, called.operation) == (AAS_ID, "BPNL000000000001", "aas.get_asset_administration_shell_descriptor_by_id")
        assert answered.levelno == logging.DEBUG and "returned as a Result with 1 message(s)" in answered.getMessage()
        assert [r for r in caplog.records if r.levelno >= logging.INFO] == []
        assert SECRET not in _dump(caplog)

    def test_a_successful_read_is_debug_and_a_successful_write_is_info(self, service, caplog):
        with patch(f"{AAS}.HttpTools") as http, caplog.at_level(logging.DEBUG):
            http.do_delete_with_session.return_value = self._response(204)
            http.do_get_with_session.return_value = self._response(200, {"result": []})
            assert service.delete_asset_administration_shell_descriptor(AAS_ID) is None
            with patch(f"{AAS}.ShellDescriptor", return_value="descriptor"):
                assert service.get_asset_administration_shell_descriptor_by_id(AAS_ID) == "descriptor"

        outcomes = {r.getMessage(): r.levelno for r in _records(caplog, AAS) if "succeeded" in r.getMessage()}
        assert outcomes == {"DTR: delete a shell descriptor succeeded": logging.INFO, "DTR: get a shell descriptor succeeded": logging.DEBUG}
        assert _records(caplog, AAS)[1].aas_id == AAS_ID

    def test_the_submodel_identifier_is_part_of_the_context(self, service, caplog):
        with patch(f"{AAS}.HttpTools") as http, caplog.at_level(logging.DEBUG):
            http.do_delete_with_session.return_value = self._response(204)
            service.delete_submodel_descriptor(AAS_ID, "sm-1")
        record = _records(caplog, AAS)[-1]
        assert (record.aas_id, record.submodel_id, record.levelno) == (AAS_ID, "sm-1", logging.INFO)

    def test_a_response_that_does_not_match_the_model_is_logged_with_its_traceback_and_re_raised(self, service, caplog):
        with patch(f"{AAS}.HttpTools") as http, caplog.at_level(logging.DEBUG), pytest.raises(Exception) as raised:
            http.do_get_with_session.return_value = self._response(200, {"unexpected": "shape"})
            service.get_all_asset_administration_shell_descriptors()
        failure = [r for r in _records(caplog, AAS) if r.levelno == logging.ERROR][0]
        assert failure.exc_info[1] is raised.value and failure.operation == "aas.get_all_asset_administration_shell_descriptors"

    def test_a_transport_failure_is_not_logged_a_second_time_by_the_service(self, service, caplog):
        import requests
        with patch(f"{AAS}.HttpTools") as http, caplog.at_level(logging.DEBUG), pytest.raises(requests.ConnectionError):
            http.do_get_with_session.side_effect = requests.ConnectionError("down")
            service.get_description()
        assert [r for r in _records(caplog, AAS) if r.levelno >= logging.WARNING] == []

    def test_a_bad_limit_is_logged_before_it_is_raised(self, service, caplog):
        with caplog.at_level(logging.DEBUG), pytest.raises(ValueError, match="Limit"):
            service.get_submodel_descriptors_by_aas_id(AAS_ID, limit=0)
        failure = _records(caplog, AAS)[-1]
        assert failure.levelno == logging.ERROR and failure.aas_id == AAS_ID

    def test_the_headers_are_never_logged_and_the_missing_authentication_is_noted(self, caplog):
        service = AasService(base_url="https://dtr.example.com", base_lookup_url="https://l.example.com", api_path="/api")
        with caplog.at_level(logging.DEBUG):
            assert service._prepare_headers("BPNL000000000001")["Edc-Bpn"] == "BPNL000000000001"
        assert any("no authentication service configured" in r.getMessage() for r in _records(caplog, AAS))

        caplog.clear()
        authenticated = AasService(base_url="https://dtr.example.com", base_lookup_url="https://l.example.com", api_path="/api",
                                   auth_service=AuthManager(configured_api_key=f"key-{SECRET}", auth_enabled=True))
        with caplog.at_level(logging.DEBUG):
            authenticated._prepare_headers()
        assert SECRET not in _dump(caplog)

    def test_the_decorator_keeps_the_signature_and_the_name_of_the_methods(self):
        import inspect
        method = AasService.delete_submodel_descriptor
        assert method.__name__ == "delete_submodel_descriptor"
        assert list(inspect.signature(method).parameters) == ["self", "aas_identifier", "submodel_identifier", "bpn"]
