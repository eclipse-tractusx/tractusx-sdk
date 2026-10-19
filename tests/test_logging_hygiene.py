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

"""
Guards for the library-logging conventions of the SDK.

The ``NullHandler`` checks are enforced right away. The source-scanning rules
are marked ``xfail`` until the refactoring phase that satisfies each of them
lands, and lose their marker in that same phase.
"""

import ast
import logging
import os
import subprocess
import sys
from pathlib import Path

import pytest

import tractusx_sdk

SRC_ROOT = Path(tractusx_sdk.__file__).parent
ROOT_INIT = SRC_ROOT / "__init__.py"
LOG_METHODS = {"debug", "info", "warning", "error", "critical", "exception", "log"}
FLAG_NAMES = {"verbose", "debug", "logger"}


def _modules():
    for path in sorted(SRC_ROOT.rglob("*.py")):
        yield path, ast.parse(path.read_text(encoding="utf-8"))


def _rel(path: Path) -> str:
    return str(path.relative_to(SRC_ROOT))


def _is_logger_target(node: ast.expr) -> bool:
    """True for ``logger`` and ``self.logger`` (or any ``<x>.logger``)."""
    return (isinstance(node, ast.Name) and node.id == "logger") or (
        isinstance(node, ast.Attribute) and node.attr == "logger"
    )


def _log_calls(tree: ast.AST):
    for node in ast.walk(tree):
        if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                and node.func.attr in LOG_METHODS and _is_logger_target(node.func.value)):
            yield node


def _defines_module_logger(tree: ast.Module) -> bool:
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "logger" for t in node.targets):
            value = node.value
            if (isinstance(value, ast.Call) and isinstance(value.func, ast.Attribute)
                    and value.func.attr == "getLogger" and len(value.args) == 1
                    and isinstance(value.args[0], ast.Name) and value.args[0].id == "__name__"):
                return True
    return False


def _uses_logging(tree: ast.Module) -> bool:
    for node in ast.walk(tree):
        if isinstance(node, ast.Import) and any(alias.name.split(".")[0] == "logging" for alias in node.names):
            return True
        if isinstance(node, ast.ImportFrom) and (node.module or "").split(".")[0] == "logging":
            return True
        if isinstance(node, ast.Name) and node.id == "logger":
            return True
        if isinstance(node, ast.Attribute) and node.attr == "logger":
            return True
    return False


class TestNullHandler:

    def test_root_logger_of_the_sdk_has_a_null_handler(self):
        handlers = logging.getLogger("tractusx_sdk").handlers
        assert any(isinstance(handler, logging.NullHandler) for handler in handlers)

    def test_root_init_adds_exactly_one_null_handler(self):
        source = ROOT_INIT.read_text(encoding="utf-8")
        assert source.count("NullHandler()") == 1

    def test_the_sdk_does_not_configure_the_application_logging(self):
        """Only the entry point of a command line tool (a ``main`` function) may configure logging."""
        offenders = []
        for path, tree in _modules():
            for function in ast.walk(tree):
                if not isinstance(function, (ast.FunctionDef, ast.AsyncFunctionDef)) or function.name == "main":
                    continue
                if any(isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr == "basicConfig"
                       for n in ast.walk(function)):
                    offenders.append(f"{_rel(path)}:{function.name}")
        # Phase 4 moves the TCK helper behind its CLI entry point
        assert offenders == [] or all(o.startswith("extensions/tck/connector/helpers.py") for o in offenders), offenders

    def test_importing_and_logging_stays_silent_without_application_setup(self):
        code = (
            "import logging\n"
            "import tractusx_sdk\n"
            "from tractusx_sdk.dataspace.tools import DspTools\n"
            "logging.getLogger('tractusx_sdk.some.module').warning('should stay silent')\n"
        )
        result = subprocess.run(
            [sys.executable, "-c", code], capture_output=True, text=True,
            cwd=SRC_ROOT.parent, env={**os.environ, "PYTHONPATH": str(SRC_ROOT.parent)},
        )
        assert result.returncode == 0, result.stderr
        assert result.stdout == ""
        assert result.stderr == ""


class TestSourceConventions:

    @pytest.mark.xfail(reason="Phase 3: the remaining print() calls (file-system manager and adapter) are replaced", strict=False)
    def test_no_print_calls(self):
        offenders = [
            f"{_rel(path)}:{node.lineno}" for path, tree in _modules() for node in ast.walk(tree)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "print"
        ]
        assert offenders == []

    @pytest.mark.xfail(reason="Phase 4: verbose/debug/logger parameters are removed", strict=False)
    def test_no_verbose_debug_or_logger_parameters(self):
        offenders = []
        for path, tree in _modules():
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    args = node.args.posonlyargs + node.args.args + node.args.kwonlyargs
                    found = sorted(a.arg for a in args if a.arg in FLAG_NAMES)
                    if found:
                        offenders.append(f"{_rel(path)}:{node.name}({', '.join(found)})")
        assert offenders == []

    @pytest.mark.xfail(reason="Phase 3: every module gets logger = logging.getLogger(__name__)", strict=False)
    def test_modules_that_log_define_a_module_logger(self):
        offenders = [
            _rel(path) for path, tree in _modules()
            if path != ROOT_INIT and _uses_logging(tree) and not _defines_module_logger(tree)
        ]
        assert offenders == []

    @pytest.mark.xfail(reason="Phase 3: self.logger is replaced by the module logger", strict=False)
    def test_no_instance_loggers(self):
        offenders = [
            f"{_rel(path)}:{node.lineno}" for path, tree in _modules() for node in ast.walk(tree)
            if isinstance(node, ast.Attribute) and node.attr == "logger"
            and isinstance(node.value, ast.Name) and node.value.id == "self"
        ]
        assert offenders == []

    @pytest.mark.xfail(reason="Phase 3: log calls use lazy %-style arguments", strict=False)
    def test_log_calls_are_lazy(self):
        offenders = []
        for path, tree in _modules():
            for call in _log_calls(tree):
                first = call.args[0] if call.args else None
                if isinstance(first, ast.JoinedStr) or (isinstance(first, ast.BinOp)) or (
                    isinstance(first, ast.Call) and isinstance(first.func, ast.Attribute) and first.func.attr == "format"
                ):
                    offenders.append(f"{_rel(path)}:{call.lineno}")
        assert offenders == []
