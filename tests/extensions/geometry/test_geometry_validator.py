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

import dataclasses
import json
import logging

import pytest

from tractusx_sdk.extensions.geometry import (
    GeometryValidationReport,
    GeometryValidator,
    SceneTreeNode,
    ValidationLevel,
)

ROOT_ID = "urn:uuid:11111111-1111-1111-1111-111111111111"
CHILD_ID = "urn:uuid:22222222-2222-2222-2222-222222222222"


@pytest.fixture
def schema_file(tmp_path):
    path = tmp_path / "schema.json"
    path.write_text(json.dumps({"type": "object"}))
    return path


def _write(directory, name, content):
    path = directory / name
    path.write_text(json.dumps(content))
    return path


@pytest.fixture
def scene(tmp_path):
    root = _write(tmp_path, "root.json", {"catenaXId": ROOT_ID, "childItems": [{"catenaXId": CHILD_ID}]})
    _write(tmp_path, "child.json", {"catenaXId": CHILD_ID})
    return root


def _validator(level, schema_file, directory=None):
    validator = GeometryValidator(level)
    assert validator.load_schema(schema_file)
    if directory is not None:
        validator.build_catenax_id_map(directory)
    return validator


class TestReport:

    def test_the_package_is_importable(self):
        assert GeometryValidator is not None

    def test_report_holds_every_finding_as_data(self, scene, schema_file):
        validator = _validator(ValidationLevel.ERROR, schema_file, scene.parent)
        validator.validate_file(scene)

        report = validator.report()
        assert isinstance(report, GeometryValidationReport)
        assert report.errors == ()
        assert report.infos  # collected even though the level is ERROR
        assert [(n.file_path.name, n.depth) for n in report.tree] == [("root.json", 0), ("child.json", 1)]
        assert all(isinstance(n, SceneTreeNode) for n in report.tree)
        assert report.tree[1].catenax_id == CHILD_ID
        assert report.has_errors is False

    def test_missing_file_is_an_error_in_the_report(self, tmp_path, schema_file):
        validator = _validator(ValidationLevel.ERROR, schema_file)
        validator.validate_file(tmp_path / "nope.json")

        report = validator.report()
        assert report.has_errors is True
        assert report.errors == (f"File not found: {tmp_path / 'nope.json'}",)
        assert report.tree == ()

    def test_unresolved_reference_is_a_warning(self, scene, schema_file):
        validator = _validator(ValidationLevel.WARNING, schema_file)  # no directory map: child is unknown
        validator.validate_file(scene)

        report = validator.report()
        assert report.has_warnings is True
        assert any(CHILD_ID in w and "not found" in w for w in report.warnings)

    def test_report_is_a_snapshot_and_immutable(self, scene, schema_file):
        validator = _validator(ValidationLevel.ERROR, schema_file, scene.parent)
        before = validator.report()
        validator.validate_file(scene)

        assert before.tree == ()
        assert validator.report().tree != ()
        with pytest.raises(dataclasses.FrozenInstanceError):
            before.errors = ("x",)


class TestRender:

    def test_error_level_shows_only_errors_and_summary(self, tmp_path, schema_file):
        validator = _validator(ValidationLevel.ERROR, schema_file)
        validator.validate_file(tmp_path / "nope.json")
        validator.schema_validator.add_warning("a warning")

        text = validator.render_report()
        assert "=== ERRORS ===" in text
        assert "[ERROR] File not found" in text
        assert "WARNINGS" not in text
        assert "SCENE TREE" not in text
        assert "Errors: 1" in text and "Warnings: 1" in text

    def test_warning_level_adds_warnings(self, schema_file):
        validator = _validator(ValidationLevel.WARNING, schema_file)
        validator.schema_validator.add_warning("a warning")
        validator.schema_validator.add_info("an info")

        text = validator.render_report()
        assert "[WARNING] a warning" in text
        assert "an info" not in text

    def test_info_level_adds_the_tree_and_infos(self, scene, schema_file):
        validator = _validator(ValidationLevel.INFO, schema_file, scene.parent)
        validator.validate_file(scene)

        text = validator.render_report()
        assert "=== SCENE TREE STRUCTURE ===" in text
        assert "• root.json [11111111...]" in text
        assert "└── child.json [22222222...]" in text
        assert "=== INFO ===" in text

    def test_the_level_can_be_chosen_when_rendering_a_report(self, schema_file):
        validator = _validator(ValidationLevel.ERROR, schema_file)
        validator.schema_validator.add_warning("a warning")
        report = validator.report()

        assert "a warning" not in report.render(ValidationLevel.ERROR)
        assert "a warning" in report.render(ValidationLevel.WARNING)

    def test_rendering_has_no_side_effects(self, scene, schema_file, capsys, caplog):
        validator = _validator(ValidationLevel.INFO, schema_file, scene.parent)
        validator.validate_file(scene)
        capsys.readouterr()
        caplog.clear()

        validator.render_report()

        captured = capsys.readouterr()
        assert captured.out == "" and captured.err == ""
        assert caplog.text == ""


class TestLoggingAndOutput:

    def test_validating_does_not_print(self, scene, schema_file, capsys):
        validator = _validator(ValidationLevel.INFO, schema_file, scene.parent)
        validator.validate_file(scene)

        captured = capsys.readouterr()
        assert captured.out == "" and captured.err == ""

    def test_findings_are_echoed_at_debug_level_only(self, tmp_path, schema_file, caplog):
        validator = _validator(ValidationLevel.ERROR, schema_file)
        with caplog.at_level(logging.INFO, logger="tractusx_sdk.extensions.geometry"):
            validator.validate_file(tmp_path / "nope.json")
        assert caplog.text == ""

        with caplog.at_level(logging.DEBUG, logger="tractusx_sdk.extensions.geometry"):
            validator.validate_file(tmp_path / "other.json")
        assert "File not found" in caplog.text
