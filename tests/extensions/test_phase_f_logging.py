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

"""The log records of the semantic translator, the geometry validator and the model factory."""

import json
import logging
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
import requests

from tractusx_sdk.dataspace.models.connector.model_factory import DataspaceVersionMapping, ModelFactory, ModelType
from tractusx_sdk.exceptions import InvalidSemanticIdError, SchemaNotFoundError, SchemaTranslationError
from tractusx_sdk.extensions.geometry import GeometryValidator, ValidationLevel
from tractusx_sdk.extensions.geometry.geometry_aspect_validator.schemaValidator import SchemaValidator
from tractusx_sdk.extensions.semantics.schema_to_context_translator import SammSchemaContextTranslator

SECRET = "s3cr3t-value"
TRANSLATOR = "tractusx_sdk.extensions.semantics.schema_to_context_translator"
SCHEMA_VALIDATOR = "tractusx_sdk.extensions.geometry.geometry_aspect_validator.schemaValidator"
VALIDATE_GEOMETRY = "tractusx_sdk.extensions.geometry.geometry_aspect_validator.validateGeometry"
MODEL_FACTORY = "tractusx_sdk.dataspace.models.connector.model_factory"
SEMANTIC_ID = "urn:samm:io.catenax.pcf:7.0.0#Pcf"


def _dump(caplog) -> str:
    return "\n".join(f"{r.getMessage()} {r.__dict__} {r.exc_text or ''}" for r in caplog.records)


def _records(caplog, name):
    return [r for r in caplog.records if r.name == name]


class TestTranslatorLogging:

    @pytest.fixture
    def translator(self):
        return SammSchemaContextTranslator()

    def test_a_successful_translation_is_logged_at_debug_with_the_semantic_id(self, translator, caplog):
        with caplog.at_level(logging.DEBUG):
            translator.schema_to_jsonld(SEMANTIC_ID, schema={"type": "string"})
            translator.schema_to_jsonld_nested(SEMANTIC_ID, schema={"type": "string"}, aspect_prefix="cx")
        records = _records(caplog, TRANSLATOR)
        flattened = [r for r in records if "flattened JSON-LD context with" in r.getMessage()][0]
        nested = [r for r in records if "nested JSON-LD context" in r.getMessage() and r.levelno == logging.DEBUG][0]
        assert (flattened.schema_urn, flattened.levelno) == (SEMANTIC_ID, logging.DEBUG)
        assert nested.schema_urn == SEMANTIC_ID
        assert [r for r in records if r.levelno >= logging.WARNING] == []

    def test_the_default_aspect_prefix_is_noted(self, translator, caplog):
        with caplog.at_level(logging.DEBUG):
            translator.schema_to_jsonld(SEMANTIC_ID, schema={"type": "string"}, aspect_prefix=None)
        assert any(r.getMessage() == "No aspect prefix given, using 'pcf-aspect'" for r in _records(caplog, TRANSLATOR))

    def test_an_invalid_semantic_id_is_a_warning_and_the_entry_point_says_which_id_it_was(self, translator, caplog):
        with caplog.at_level(logging.DEBUG), pytest.raises(SchemaTranslationError) as raised:
            translator.schema_to_jsonld("urn:samm:no-reference", schema={"type": "string"})
        assert isinstance(raised.value.__cause__, InvalidSemanticIdError)
        records = _records(caplog, TRANSLATOR)
        assert records[0].levelno == logging.WARNING and records[0].schema_urn == "urn:samm:no-reference"
        entry = records[-1]
        assert entry.levelno == logging.ERROR and "failed: InvalidSemanticIdError" in entry.getMessage()
        assert entry.operation == "semantics.schema_to_jsonld"

    def test_a_schema_without_a_root_node_is_an_error_before_it_is_raised(self, translator, caplog):
        with caplog.at_level(logging.DEBUG), pytest.raises(SchemaTranslationError):
            translator.schema_to_jsonld_nested(SEMANTIC_ID, schema={"no": "type"})
        messages = [r.getMessage() for r in _records(caplog, TRANSLATOR)]
        assert any("the schema has no usable root node" in m for m in messages)
        assert any("the property has no type" in m for m in messages)

    def test_a_schema_that_cannot_be_fetched_is_logged_before_it_is_wrapped(self, translator, caplog):
        with patch.object(translator, "_find_schema", side_effect=SchemaNotFoundError("404")), caplog.at_level(logging.DEBUG):
            with pytest.raises(SchemaTranslationError):
                translator.schema_to_jsonld(SEMANTIC_ID)
        records = _records(caplog, TRANSLATOR)
        assert any("could not be fetched for the translation: SchemaNotFoundError" in r.getMessage() for r in records)
        assert any(r.getMessage().startswith("Schema not provided, attempting to fetch") for r in records)

    def test_fetching_a_schema_logs_the_outcome_and_a_failure_still_returns_none(self, translator, caplog):
        with patch.object(translator, "_find_schema", return_value=Mock(schema={"type": "string"}, message="ok")), caplog.at_level(logging.DEBUG):
            assert translator.fetch_schema_from_semantic_id(SEMANTIC_ID) == {"type": "string"}
        assert [r.levelno for r in _records(caplog, TRANSLATOR)] == [logging.INFO, logging.INFO]

        caplog.clear()
        with patch.object(translator, "_find_schema", side_effect=SchemaNotFoundError("404")), caplog.at_level(logging.DEBUG):
            assert translator.fetch_schema_from_semantic_id(SEMANTIC_ID) is None
        error = _records(caplog, TRANSLATOR)[-1]
        assert (error.levelno, error.schema_urn) == (logging.ERROR, SEMANTIC_ID)

    def test_a_failure_deep_in_the_recursion_is_logged_once_with_its_traceback_and_not_once_per_level(self, translator, caplog):
        schema = {"type": "object", "properties": {"a": {"type": "object", "properties": {"b": {"type": "string"}}}}}
        with patch.object(translator, "create_simple_node", side_effect=ZeroDivisionError("boom")), caplog.at_level(logging.DEBUG):
            with pytest.raises(SchemaTranslationError):
                translator.schema_to_jsonld_nested(SEMANTIC_ID, schema=schema)

        errors = [r for r in _records(caplog, TRANSLATOR) if r.levelno >= logging.ERROR]
        origin = [r for r in errors if r.exc_info]
        assert len(origin) == 1 and origin[0].exc_info[0] is ZeroDivisionError
        assert origin[0].getMessage() == "The schema translation failed while trying to create the node"
        assert origin[0].operation == "semantics.create_the_node"
        # The origin, then the entry point that says which semantic id it was: nothing in between
        assert len(errors) == 2 and errors[-1].schema_urn == SEMANTIC_ID

    def test_the_failure_of_a_wrapped_error_is_not_logged_again(self, translator, caplog):
        with caplog.at_level(logging.DEBUG):
            translator._log_translation_failure("anything", SchemaTranslationError("already logged below"))
        assert caplog.records == []

    def test_the_silent_branches_are_traced_at_debug(self, translator, caplog):
        translator.baseSchema = {}
        with caplog.at_level(logging.DEBUG):
            assert translator.create_object_node({"type": "object"}, {}, "") is None
            assert translator.create_array_node({"type": "array"}, {}, "") is None
            assert translator.create_single_properties_context(None, "") is None
            assert translator.create_single_properties_context("not a dict", "") is None
            assert translator.create_single_properties_context({}, "") is None
            assert translator.create_node_property("k", {"no": "ref"}, "") is None
            assert translator.get_schema_ref(None, "") is None
        messages = [r.getMessage() for r in _records(caplog, TRANSLATOR)]
        for expected in ("neither 'properties' nor 'allOf'", "has no 'items'", "no properties to create a context from",
                         "not an object", "properties are empty", "has no '$ref'", "not a string"):
            assert any(expected in m for m in messages), expected
        assert {r.levelno for r in _records(caplog, TRANSLATOR)} == {logging.DEBUG}

    def test_a_circular_reference_is_traced_and_the_recursion_limit_is_a_warning(self, translator, caplog):
        import hashlib
        translator.baseSchema = {"definitions": {"node": {"type": "string"}}}
        ref = "#/definitions/node"
        looping = "/-/".join(["", hashlib.sha256(ref.encode()).hexdigest()])
        with caplog.at_level(logging.DEBUG):
            for _ in range(translator.recursionDepth + 1):
                translator.get_schema_ref(ref, looping)
        records = _records(caplog, TRANSLATOR)
        assert sum("Circular reference" in r.getMessage() for r in records) == translator.recursionDepth
        assert records[-1].levelno == logging.WARNING and "Infinite recursion" in records[-1].getMessage()


class TestGeometryValidatorLogging:
    ROOT_ID = "urn:uuid:11111111-1111-1111-1111-111111111111"
    CHILD_ID = "urn:uuid:22222222-2222-2222-2222-222222222222"

    def _write(self, directory: Path, name: str, content) -> Path:
        path = directory / name
        path.write_text(json.dumps(content))
        return path

    def test_the_schema_loaded_from_a_url_is_logged_with_its_timing(self, caplog):
        response = Mock()
        response.json.return_value = {"type": "object"}
        with patch(f"{SCHEMA_VALIDATOR}.requests.get", return_value=response), caplog.at_level(logging.DEBUG):
            assert SchemaValidator().load_schema_from_url() is True
        loading, loaded = _records(caplog, SCHEMA_VALIDATOR)
        assert loading.url == loaded.url and loaded.elapsed_ms >= 0 and loaded.operation == "geometry.load_schema"

    def test_a_schema_that_cannot_be_loaded_is_a_warning_by_exception_type_and_still_a_finding_in_the_report(self, caplog):
        validator = SchemaValidator()
        with patch(f"{SCHEMA_VALIDATOR}.requests.get", side_effect=requests.ConnectionError(f"refused {SECRET}")), caplog.at_level(logging.DEBUG):
            assert validator.load_schema_from_url() is False
        warning = [r for r in _records(caplog, SCHEMA_VALIDATOR) if r.levelno == logging.WARNING][0]
        assert "(ConnectionError)" in warning.getMessage()
        assert validator.errors and SECRET in validator.errors[0]
        assert SECRET not in "\n".join(r.getMessage() for r in _records(caplog, SCHEMA_VALIDATOR) if r.levelno >= logging.WARNING)

    def test_a_schema_that_is_not_json_is_a_warning(self, caplog):
        response = Mock()
        response.json.side_effect = json.JSONDecodeError("bad", "x", 0)
        with patch(f"{SCHEMA_VALIDATOR}.requests.get", return_value=response), caplog.at_level(logging.DEBUG):
            assert SchemaValidator().load_schema_from_url() is False
        assert [r.levelno for r in _records(caplog, SCHEMA_VALIDATOR) if "not valid JSON" in r.getMessage()] == [logging.WARNING]

    def test_a_schema_file_that_cannot_be_loaded_is_a_warning(self, tmp_path, caplog):
        broken = tmp_path / "broken.json"
        broken.write_text("{ nope")
        with caplog.at_level(logging.DEBUG):
            assert SchemaValidator().load_schema_from_file(tmp_path / "missing.json") is False
            assert SchemaValidator().load_schema_from_file(broken) is False
        warnings = [r for r in _records(caplog, SCHEMA_VALIDATOR) if r.levelno == logging.WARNING]
        assert [("was not found" in w.getMessage(), "not valid JSON" in w.getMessage()) for w in warnings] == [(True, False), (False, True)]

    def test_validating_without_a_schema_is_a_warning(self, caplog):
        with caplog.at_level(logging.DEBUG):
            assert SchemaValidator().validate_data({"catenaXId": "x"}, "root.json") is False
        assert [r.levelno for r in _records(caplog, SCHEMA_VALIDATOR) if "no schema is loaded" in r.getMessage()] == [logging.WARNING]

    def test_a_violation_is_logged_by_location_and_rule_but_its_value_stays_in_the_report_only(self, caplog):
        validator = SchemaValidator()
        validator.schema = {"type": "object", "properties": {"catenaXId": {"type": "integer"}}}
        with caplog.at_level(logging.DEBUG):
            assert validator.validate_data({"catenaXId": f"value-{SECRET}"}, "root.json") is False
        assert any(SECRET in error for error in validator.errors)
        assert any("[root.json] Schema validation error at 'catenaXId' (type)" in r.getMessage() for r in _records(caplog, SCHEMA_VALIDATOR))
        assert SECRET not in _dump(caplog)

    def test_an_invalid_schema_is_a_warning_and_its_message_is_kept_out_of_the_log(self, caplog):
        validator = SchemaValidator()
        validator.schema = {"type": 5}
        with caplog.at_level(logging.DEBUG):
            assert validator.validate_data({}, "root.json") is False
        assert any(r.levelno == logging.WARNING and "not a valid JSON schema" in r.getMessage() for r in _records(caplog, SCHEMA_VALIDATOR))

    def test_the_whole_validation_flow_is_traced_and_the_report_is_unchanged(self, tmp_path, caplog):
        schema = self._write(tmp_path, "schema.json", {"type": "object"})
        root = self._write(tmp_path, "root.json", {"catenaXId": self.ROOT_ID, "childItems": [{"catenaXId": self.CHILD_ID}]})
        self._write(tmp_path, "child.json", {"catenaXId": self.CHILD_ID})
        self._write(tmp_path, "other.json", {"no": "id"})
        validator = GeometryValidator(ValidationLevel.INFO)
        with caplog.at_level(logging.DEBUG):
            assert validator.load_schema(schema)
            validator.build_catenax_id_map(tmp_path)
            validator.validate_file(root)
            validator.validate_file(root)

        messages = [r.getMessage() for r in _records(caplog, VALIDATE_GEOMETRY)]
        assert any(m.startswith("Mapping the catenaXIds of 4 JSON file(s)") for m in messages)
        assert any("'other.json' has no catenaXId" in m for m in messages)
        assert "The map holds 2 catenaXId(s)" in messages
        assert "Validating 'root.json' (depth 0)" in messages and "Validating 'child.json' (depth 1)" in messages
        assert "The file 'root.json' was already validated, skipping it" in messages
        assert [t.depth for t in validator.report().tree] == [0, 1]
        assert {r.levelno for r in _records(caplog, VALIDATE_GEOMETRY)} == {logging.DEBUG}


class TestModelFactoryLogging:

    def test_a_model_builder_is_traced_at_debug(self, caplog):
        with caplog.at_level(logging.DEBUG):
            ModelFactory._get_model_builder(ModelType.ASSET, "jupiter")
        record = _records(caplog, MODEL_FACTORY)[-1]
        assert record.levelno == logging.DEBUG and record.getMessage().startswith("Resolved AssetModel from ")
        assert (record.dataspace_version, record.model) == ("jupiter", "Asset")

    def test_an_unsupported_version_is_an_error_before_it_is_raised(self, caplog):
        with caplog.at_level(logging.DEBUG), pytest.raises(ValueError, match="Unsupported version nope"):
            ModelFactory._get_model_builder(ModelType.ASSET, "nope")
        error = _records(caplog, MODEL_FACTORY)[-1]
        assert (error.levelno, error.dataspace_version, error.model) == (logging.ERROR, "nope", "Asset")

    def test_a_missing_class_and_an_import_failure_are_logged_with_their_traceback(self, caplog):
        with patch(f"{MODEL_FACTORY}.import_module", return_value=object()), caplog.at_level(logging.DEBUG), pytest.raises(AttributeError):
            ModelFactory._get_model_builder(ModelType.ASSET, "jupiter")
        assert _records(caplog, MODEL_FACTORY)[-1].exc_info is not None
        caplog.clear()
        with patch(f"{MODEL_FACTORY}.import_module", side_effect=ImportError("x")), caplog.at_level(logging.DEBUG), pytest.raises(ImportError):
            ModelFactory._get_model_builder(ModelType.ASSET, "jupiter")
        assert _records(caplog, MODEL_FACTORY)[-1].exc_info is not None

    def test_the_connector_discovery_model_of_jupiter_is_logged_before_it_is_refused(self, caplog):
        with caplog.at_level(logging.DEBUG), pytest.raises(NotImplementedError):
            ModelFactory.get_connector_discovery_model("jupiter", "BPNL000000000001", "https://x")
        error = _records(caplog, MODEL_FACTORY)[-1]
        assert (error.levelno, error.model) == (logging.ERROR, "ConnectorDiscovery")

    @pytest.mark.parametrize("protocol, expected", [
        ("dataspace-protocol-http", "jupiter"), ("dataspace-protocol-http:2025-1", "saturn"),
    ])
    def test_a_known_protocol_is_silent(self, caplog, protocol, expected):
        with caplog.at_level(logging.DEBUG):
            assert DataspaceVersionMapping.from_protocol(protocol).value == expected
        assert caplog.records == []

    def test_an_unknown_protocol_that_defaults_to_saturn_is_only_a_debug_record(self, caplog):
        with caplog.at_level(logging.DEBUG):
            assert DataspaceVersionMapping.from_protocol("dataspace-protocol-http:2099").value == "saturn"
        record = _records(caplog, MODEL_FACTORY)[-1]
        assert record.levelno == logging.DEBUG and record.dataspace_version == "saturn"
        assert "'dataspace-protocol-http:2099' is unknown" in record.getMessage()


class TestPureDataModelsStaySilent:

    def test_no_data_model_module_logs(self):
        """The models carry no logic worth a record: their validation errors travel in the exceptions."""
        import ast
        root = Path(__file__).resolve().parents[2] / "src" / "tractusx_sdk"
        model_dirs = [root / "dataspace/models/connector/jupiter", root / "dataspace/models/connector/saturn",
                      root / "industry/models", root / "extensions/notification_api/models"]
        offenders = []
        for directory in model_dirs:
            for path in directory.rglob("*.py"):
                tree = ast.parse(path.read_text(encoding="utf-8"))
                if any(isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr in {"getLogger"} for n in ast.walk(tree)):
                    offenders.append(str(path.relative_to(root)))
        assert offenders == []
