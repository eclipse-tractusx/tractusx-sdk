#################################################################################
# Eclipse Tractus-X - Software Development KIT
#
# Copyright (c) 2026 LKS Next
# Copyright (c) 2025,2026 Contributors to the Eclipse Foundation
#
# See the NOTICE file(s) distributed with this work for additional
# information regarding copyright ownership.
#
# This program and the accompanying materials are made available under the
# terms of the Apache License, Version 2.0 which is available at
# https://www.apache.org/licenses/LICENSE-2.0.
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND,
# either express or implied. See the
# License for the specific language govern in permissions and limitations
# under the License.
#
# SPDX-License-Identifier: Apache-2.0
#################################################################################


import dataclasses

import pytest
from unittest import mock
from requests import HTTPError
from tractusx_sdk.dataspace.tools.validate_submodels import (
    SchemaLookupResult,
    ValidationIssue,
    ValidationResult,
    json_validator,
    submodel_schema_finder,
)
from tractusx_sdk.exceptions import (
    InvalidSemanticIdError,
    SchemaNotFoundError,
    SubmodelValidationError,
    TractusXSDKError,
    ValidationError,
)

@pytest.fixture
def valid_semantic_id():
    # Format: urn:samm:namespace:version#aspect
    return "urn:samm:io.catenax.batch:3.0.0#Batch"

def test_submodel_schema_finder_success(valid_semantic_id):
    mock_response = mock.Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"type": "object"}

    with mock.patch("tractusx_sdk.dataspace.tools.validate_submodels.get", return_value=mock_response) as mock_get:
        result = submodel_schema_finder(valid_semantic_id)
        assert result["status"] == "ok"
        assert result["schema"] == {"type": "object"}
        assert "Submodel validation schema retrieved successfully" in result["message"]
        # Check correct URL construction
        expected_url = (
            "https://raw.githubusercontent.com/eclipse-tractusx/sldt-semantic-models/main/"
            "io.catenax.batch/3.0.0/gen/Batch-schema.json"
        )
        mock_get.assert_called_once_with(expected_url)

def test_submodel_schema_finder_invalid_semantic_id():
    # Missing version or aspect name
    invalid_id = "urn:samm:io.catenax.batch"
    with pytest.raises(HTTPError) as excinfo:
        submodel_schema_finder(invalid_id)
    assert "does not follow the correct structure" in str(excinfo.value)

def test_submodel_schema_finder_schema_not_found(valid_semantic_id):
    mock_response = mock.Mock()
    mock_response.status_code = 404

    with mock.patch("tractusx_sdk.dataspace.tools.validate_submodels.get", return_value=mock_response):
        with pytest.raises(HTTPError) as excinfo:
            submodel_schema_finder(valid_semantic_id)
        assert "Failed to obtain the required schema" in str(excinfo.value)

def test_submodel_schema_finder_invalid_json(valid_semantic_id):
    mock_response = mock.Mock()
    mock_response.status_code = 200
    mock_response.json.side_effect = Exception("Invalid JSON")

    with mock.patch("tractusx_sdk.dataspace.tools.validate_submodels.get", return_value=mock_response):
        with pytest.raises(HTTPError) as excinfo:
            submodel_schema_finder(valid_semantic_id)
        assert "not a valid json" in str(excinfo.value)

def test_submodel_schema_finder_custom_link_core(valid_semantic_id):
    mock_response = mock.Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"type": "object"}
    custom_link_core = "https://example.com/models/"

    with mock.patch("tractusx_sdk.dataspace.tools.validate_submodels.get", return_value=mock_response) as mock_get:
        submodel_schema_finder(valid_semantic_id, link_core=custom_link_core)
        expected_url = (
            "https://example.com/models/io.catenax.batch/3.0.0/gen/Batch-schema.json"
        )
        mock_get.assert_called_once_with(expected_url)


## ── Structured results and errors ───────────────────────────────────────────

SCHEMA = {
    "type": "object",
    "properties": {"name": {"type": "string"}, "age": {"type": "integer"}},
    "required": ["name"],
}


def test_schema_finder_returns_a_structured_result(valid_semantic_id):
    mock_response = mock.Mock(status_code=200)
    mock_response.json.return_value = {"type": "object"}

    with mock.patch("tractusx_sdk.dataspace.tools.validate_submodels.get", return_value=mock_response):
        result = submodel_schema_finder(valid_semantic_id)

    assert isinstance(result, SchemaLookupResult)
    assert result.schema == {"type": "object"}
    assert result.link.endswith("io.catenax.batch/3.0.0/gen/Batch-schema.json")
    # dict-style access still works for existing callers
    assert result["schema"] is result.schema
    assert result["status"] == "ok"
    assert result.get("missing", "default") == "default"
    with pytest.raises(KeyError):
        result["missing"]


def test_schema_finder_errors_are_sdk_errors_and_still_http_errors(valid_semantic_id):
    with pytest.raises(InvalidSemanticIdError) as invalid:
        submodel_schema_finder("urn:samm:io.catenax.batch")
    assert isinstance(invalid.value, (TractusXSDKError, HTTPError, ValueError))

    mock_response = mock.Mock(status_code=404)
    with mock.patch("tractusx_sdk.dataspace.tools.validate_submodels.get", return_value=mock_response):
        with pytest.raises(SchemaNotFoundError) as missing:
            submodel_schema_finder(valid_semantic_id)
    assert isinstance(missing.value, (TractusXSDKError, HTTPError))


def test_schema_finder_keeps_the_cause_of_an_invalid_json(valid_semantic_id):
    mock_response = mock.Mock(status_code=200)
    mock_response.json.side_effect = ValueError("bad json")

    with mock.patch("tractusx_sdk.dataspace.tools.validate_submodels.get", return_value=mock_response):
        with pytest.raises(SchemaNotFoundError) as raised:
            submodel_schema_finder(valid_semantic_id)
    assert isinstance(raised.value.__cause__, ValueError)


def test_json_validator_valid_document():
    result = json_validator(SCHEMA, {"name": "x", "age": 3})
    assert isinstance(result, ValidationResult)
    assert result.valid is True
    assert result.issues == ()
    assert result["status"] == "ok"
    assert "passed the validation test" in result["message"]


def test_json_validator_raises_with_structured_issues():
    with pytest.raises(SubmodelValidationError) as raised:
        json_validator(SCHEMA, {"age": "old"})

    error = raised.value
    assert isinstance(error, (TractusXSDKError, ValidationError, HTTPError, ValueError))
    assert len(error.issues) == 2
    assert all(isinstance(issue, ValidationIssue) for issue in error.issues)
    by_path = {issue.path: issue for issue in error.issues}
    assert by_path["age"].validator == "type"
    assert by_path["age"].expected == "integer"
    assert by_path["age"].invalid_value == "old"
    assert by_path["root"].validator == "required"
    assert "2 validation errors found" in str(error)


def test_json_validator_can_return_the_issues_instead_of_raising():
    result = json_validator(SCHEMA, {"age": "old"}, raise_on_error=False)
    assert result.valid is False
    assert len(result.issues) == 2
    assert result["status"] == "error"


def test_validation_issue_is_immutable_and_serialisable():
    issue = ValidationIssue(path="a.b", message="m", validator="type", expected="string", invalid_value=1)
    assert issue.as_dict() == {
        "path": "a.b", "message": "m", "validator": "type", "expected": "string", "invalid_value": 1,
    }
    with pytest.raises(dataclasses.FrozenInstanceError):
        issue.path = "other"
