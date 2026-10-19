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
Guards for the library-logging conventions of the SDK. Every rule is enforced.

The TCK command line runner (``extensions/tck``) is an application, not library
code: it builds one logger per run, with its own file and console handlers, and
hands it to its helpers. It is therefore allowed to take a ``logger`` argument and
to configure the logging of its own process (in ``setup_tck_logging`` and
``enable_debug_logging`` only). It is not exempt from the other rules: it takes no
``verbose`` or ``debug`` arguments and does not print.
"""

import ast
import logging
import os
import re
import subprocess
import sys
from pathlib import Path

import tractusx_sdk

SRC_ROOT = Path(tractusx_sdk.__file__).parent
REPO_ROOT = SRC_ROOT.parent.parent
ROOT_INIT = SRC_ROOT / "__init__.py"
LOG_METHODS = {"debug", "info", "warning", "error", "critical", "exception", "log"}
FLAG_NAMES = {"verbose", "debug", "logger"}
APPLICATION_PREFIXES = ("extensions/tck/",)


def _modules(include_applications: bool = False):
    for path in sorted(SRC_ROOT.rglob("*.py")):
        if not include_applications and _rel(path).startswith(APPLICATION_PREFIXES):
            continue
        yield path, ast.parse(path.read_text(encoding="utf-8"))


def _rel(path: Path) -> str:
    return path.relative_to(SRC_ROOT).as_posix()


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


def _emits_log_records(tree: ast.Module) -> bool:
    """True when the module logs, or asks for a logger. Importing ``logging`` for an annotation does not count."""
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
            continue
        if node.func.attr == "getLogger":
            return True
        if node.func.attr in LOG_METHODS and (
            _is_logger_target(node.func.value)
            or (isinstance(node.func.value, ast.Name) and node.func.value.id == "logging")
        ):
            return True
    return False


class TestNullHandler:

    def test_root_logger_of_the_sdk_has_a_null_handler(self):
        handlers = logging.getLogger("tractusx_sdk").handlers
        assert any(isinstance(handler, logging.NullHandler) for handler in handlers)

    def test_root_init_adds_exactly_one_null_handler(self):
        source = ROOT_INIT.read_text(encoding="utf-8")
        assert source.count("NullHandler()") == 1

    def test_the_library_never_configures_the_application_logging(self):
        """Handlers, levels and logging configuration belong to the application, never to the SDK."""
        configuring = {"basicConfig", "dictConfig", "fileConfig", "addHandler", "setLevel", "removeHandler"}
        offenders = []
        for path, tree in _modules():
            for function in ast.walk(tree):
                # A ``main`` function is the entry point of a command line tool: it is the application there
                if not isinstance(function, (ast.FunctionDef, ast.AsyncFunctionDef)) or function.name == "main":
                    continue
                if any(isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr in configuring
                       for n in ast.walk(function)):
                    offenders.append(f"{_rel(path)}:{function.name}")
        # The root __init__ attaches the NullHandler at module level (checked above). The only other place is a helper
        # that an application calls on purpose, to load its own logging configuration from a file.
        assert offenders == ["dataspace/tools/utils.py:get_log_config"], offenders

    def test_only_the_tck_entry_point_configures_the_process_logging(self):
        allowed = {
            "extensions/tck/connector/helpers.py:setup_tck_logging",
            "extensions/tck/connector/helpers.py:finalize_log",
            "extensions/tck/connector/helpers.py:enable_debug_logging",
        }
        configuring = {"basicConfig", "dictConfig", "fileConfig", "addHandler", "setLevel", "removeHandler"}
        offenders = set()
        for path, tree in _modules(include_applications=True):
            if not _rel(path).startswith(APPLICATION_PREFIXES):
                continue
            for function in ast.walk(tree):
                if not isinstance(function, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    continue
                for n in ast.walk(function):
                    if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr in configuring:
                        offenders.add(f"{_rel(path)}:{function.name}")
        assert offenders == allowed, offenders

    def test_nothing_calls_basic_config_with_force(self):
        """``force=True`` throws away the handlers the host application already installed."""
        offenders = [
            f"{_rel(path)}:{node.lineno}" for path, tree in _modules(include_applications=True) for node in ast.walk(tree)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "basicConfig"
            and any(k.arg == "force" for k in node.keywords)
        ]
        assert offenders == []

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

    def test_no_print_calls(self):
        offenders = [
            f"{_rel(path)}:{node.lineno}" for path, tree in _modules(include_applications=True) for node in ast.walk(tree)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "print"
        ]
        assert offenders == []

    def test_no_verbose_debug_or_logger_parameters(self):
        """No signature carries a flag for logging: the logging level decides. Only the TCK application takes a ``logger``."""
        offenders = []
        for path, tree in _modules(include_applications=True):
            allowed = {"logger"} if _rel(path).startswith(APPLICATION_PREFIXES) else set()
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    args = node.args.posonlyargs + node.args.args + node.args.kwonlyargs
                    found = sorted(a.arg for a in args if a.arg in FLAG_NAMES - allowed)
                    if found or node.name in {"verbose", "logger"} - allowed:
                        offenders.append(f"{_rel(path)}:{node.name}({', '.join(found)})")
        assert offenders == []

    def test_modules_that_log_define_a_module_logger(self):
        offenders = [
            _rel(path) for path, tree in _modules()
            if path != ROOT_INIT and _emits_log_records(tree) and not _defines_module_logger(tree)
        ]
        assert offenders == []

    def test_no_instance_loggers(self):
        offenders = [
            f"{_rel(path)}:{node.lineno}" for path, tree in _modules() for node in ast.walk(tree)
            if isinstance(node, ast.Attribute) and node.attr == "logger"
            and isinstance(node.value, ast.Name) and node.value.id == "self"
        ]
        assert offenders == []

    def test_no_instance_verbose_or_debug_flags(self):
        """Nothing is gated by ``self.verbose`` / ``self.debug``: the logging level decides what is emitted."""
        offenders = [
            f"{_rel(path)}:{node.lineno}" for path, tree in _modules() for node in ast.walk(tree)
            if isinstance(node, ast.Attribute) and node.attr in {"verbose", "debug"}
            and isinstance(node.value, ast.Name) and node.value.id == "self"
            and isinstance(node.ctx, ast.Load)
        ]
        assert offenders == []

    def test_logger_parameters_never_shadow_the_module_logger(self):
        """A ``logger`` parameter that is then logged through would silently replace the module logger."""
        offenders = []
        for path, tree in _modules():
            for function in ast.walk(tree):
                if not isinstance(function, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    continue
                params = function.args.posonlyargs + function.args.args + function.args.kwonlyargs
                if not any(a.arg == "logger" for a in params):
                    continue
                for call in _log_calls(function):
                    if isinstance(call.func.value, ast.Name):
                        offenders.append(f"{_rel(path)}:{function.name}:{call.lineno}")
        assert offenders == []

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

    def test_log_calls_do_not_swallow_the_exception_text_into_the_format(self):
        """``logger.error("... %s", e)`` is fine; ``logger.error(str(e))`` as the whole message is not diagnostic."""
        offenders = []
        for path, tree in _modules():
            for call in _log_calls(tree):
                first = call.args[0] if call.args else None
                if isinstance(first, ast.Call) and isinstance(first.func, ast.Name) and first.func.id == "str":
                    offenders.append(f"{_rel(path)}:{call.lineno}")
        assert offenders == []


class TestStructuredContext:
    """The ``extra`` of a record only carries the documented fields, and no log call receives a secret."""

    SECRET_NAME = re.compile(r"token|secret|password|passwd|authorization|api_?key|credential|cookie|headers$", re.IGNORECASE)

    @staticmethod
    def _extra_values(tree):
        for call in _log_calls(tree):
            for keyword in call.keywords:
                if keyword.arg == "extra":
                    yield call, keyword.value

    def test_extra_is_always_built_with_log_extra(self):
        """``log_extra`` knows the complete list of fields, rejects any other and sanitises the URLs."""
        offenders = []
        for path, tree in _modules():
            for call, value in self._extra_values(tree):
                is_helper = (isinstance(value, ast.Call) and isinstance(value.func, ast.Name)
                             and value.func.id == "log_extra")
                if not is_helper:
                    offenders.append(f"{_rel(path)}:{call.lineno}")
        assert offenders == []

    def test_log_extra_only_receives_documented_fields(self):
        from tractusx_sdk._logging_fields import EXTRA_FIELDS

        offenders = []
        for path, tree in _modules():
            for call, value in self._extra_values(tree):
                if isinstance(value, ast.Call):
                    unknown = [k.arg for k in value.keywords if k.arg is None or k.arg not in EXTRA_FIELDS]
                    if unknown:
                        offenders.append(f"{_rel(path)}:{call.lineno}:{unknown}")
        assert offenders == []

    def test_log_calls_are_never_given_secrets(self):
        """
        Neither a value named after a secret (token, password, headers, ...) nor an ``Authorization`` key.
        Only the size of such a value (``len(headers)``) is allowed.
        """
        offenders = []
        for path, tree in _modules():
            for call in _log_calls(tree):
                for argument in call.args[1:]:
                    measured = {
                        id(inner) for node in ast.walk(argument)
                        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "len"
                        for inner in ast.walk(node)
                    }
                    for node in ast.walk(argument):
                        if id(node) in measured:
                            continue
                        name = (node.id if isinstance(node, ast.Name) else node.attr if isinstance(node, ast.Attribute)
                                else node.value if isinstance(node, ast.Constant) and isinstance(node.value, str) else None)
                        if name and self.SECRET_NAME.search(name):
                            offenders.append(f"{_rel(path)}:{call.lineno}:{name}")
        assert offenders == []


    def test_the_auth_modules_never_log_exception_text_nor_tracebacks(self):
        """
        The identity provider may echo request details in its errors: the auth modules log the exception
        TYPE only, never its message (``%s`` of the exception) nor a traceback (``exc_info``, ``exception()``).
        """
        auth_modules = {"dataspace/managers/oauth2_manager.py", "dataspace/managers/auth_manager.py"}
        offenders = []
        for path, tree in _modules():
            if _rel(path) not in auth_modules:
                continue
            for call in _log_calls(tree):
                if call.func.attr == "exception" or any(k.arg == "exc_info" for k in call.keywords):
                    offenders.append(f"{_rel(path)}:{call.lineno}:traceback")
                handlers = {h.name for h in ast.walk(tree) if isinstance(h, ast.ExceptHandler) and h.name}
                for argument in call.args[1:]:
                    typed = {id(n) for c in ast.walk(argument)
                             if isinstance(c, ast.Call) and isinstance(c.func, ast.Name) and c.func.id == "type"
                             for n in ast.walk(c)}
                    for node in ast.walk(argument):
                        if isinstance(node, ast.Name) and node.id in handlers and id(node) not in typed:
                            offenders.append(f"{_rel(path)}:{call.lineno}:{node.id}")
        assert offenders == []


class TestDocumentationAndExamples:
    """What the documentation teaches must run: it never passes an argument the SDK removed."""

    # The Keras ``verbose=1`` of the TensorFlow tutorial does not match: only ``verbose=True|False`` does.
    REMOVED_API = re.compile(
        r"\b(verbose|debug)=(True|False)\b|\blogger=\w|\.verbose\(|\.logger\(|"
        r"configure_debug_logging|print_results\(|print_tree_structure"
    )
    # These pages show the removed arguments on purpose, to explain how to migrate away from them
    MIGRATION_PAGES = {"docs/admin/logging.md", "docs/admin/upgrade-guide.md"}

    def _documents(self):
        roots = [REPO_ROOT / "docs", REPO_ROOT / "examples", REPO_ROOT / "tck"]
        files = [REPO_ROOT / "README.md", REPO_ROOT / "INSTALL.md"]
        for root in roots:
            files.extend(p for p in root.rglob("*") if p.suffix in {".md", ".py"} and "logs" not in p.parts)
        return sorted(f for f in files if f.is_file() and f.relative_to(REPO_ROOT).as_posix() not in self.MIGRATION_PAGES)

    def test_the_repository_layout_is_the_expected_one(self):
        assert (REPO_ROOT / "docs").is_dir() and (REPO_ROOT / "examples").is_dir() and (REPO_ROOT / "README.md").is_file()
        assert len(self._documents()) > 50

    def test_no_document_or_example_uses_the_removed_api(self):
        offenders = []
        for path in self._documents():
            for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
                if self.REMOVED_API.search(line):
                    offenders.append(f"{path.relative_to(REPO_ROOT).as_posix()}:{number}: {line.strip()[:80]}")
        assert offenders == []

    def test_no_example_passes_a_logging_keyword_to_anything(self):
        offenders = []
        for path in sorted((REPO_ROOT / "examples").rglob("*.py")) + sorted((REPO_ROOT / "tck").rglob("*.py")):
            for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
                if isinstance(node, ast.Call):
                    for keyword in node.keywords:
                        if keyword.arg in FLAG_NAMES:
                            offenders.append(f"{path.relative_to(REPO_ROOT).as_posix()}:{node.lineno}:{keyword.arg}")
        assert offenders == []

    def test_the_logging_guide_exists_and_is_in_the_navigation(self):
        assert (REPO_ROOT / "docs/admin/logging.md").is_file()
        assert "admin/logging.md" in (REPO_ROOT / "mkdocs.yml").read_text(encoding="utf-8")

    def test_the_migration_pages_describe_the_removed_api(self):
        """The two pages that are exempt above must keep explaining the migration."""
        upgrade = (REPO_ROOT / "docs/admin/upgrade-guide.md").read_text(encoding="utf-8")
        logging_guide = (REPO_ROOT / "docs/admin/logging.md").read_text(encoding="utf-8")
        assert "Upgrading to 0.9.0" in upgrade and "verbose" in upgrade
        assert "Migrating from `verbose`" in logging_guide


class TestVersion:

    def test_the_version_agrees_everywhere(self):
        pyproject = re.search(r'^version = "([^"]+)"', (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"), re.M).group(1)
        declared = {
            path: re.search(r"__version__ = '([^']+)'", (REPO_ROOT / path).read_text(encoding="utf-8")).group(1)
            for path in (
                "src/tractusx_sdk/__init__.py",
                "src/tractusx_sdk/dataspace/__init__.py",
                "src/tractusx_sdk/industry/__init__.py",
                "src/tractusx_sdk/extensions/__init__.py",
            )
        }
        assert declared == {path: pyproject for path in declared}
        assert tractusx_sdk.__version__ == pyproject
