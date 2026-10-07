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
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND,
# either express or implied. See the License for the specific language govern in
# permissions and limitations under the License.
#
# SPDX-License-Identifier: Apache-2.0
#################################################################################

"""Reusable JSON-LD expansion with locally resolved document contexts."""

from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
from typing import Any, Mapping

from pyld import jsonld


class OfflineContextError(RuntimeError):
    """Raised when a context cannot be resolved without network access."""


class OfflineJsonLdExpander:
    """Expand JSON-LD documents using packaged or application-provided contexts.

    Context mappings are scoped to an instance, so different connector clients
    can use different context sets without sharing mutable global state.
    """

    def __init__(
        self,
        context_dir: str | Path | None = None,
        contexts: Mapping[str, str | Path | Mapping[str, Any]] | None = None,
        allow_remote: bool = False,
    ) -> None:
        self._context_dir = Path(context_dir) if context_dir is not None else Path.cwd()
        self._contexts: dict[str, str | Path | Mapping[str, Any]] = dict(
            {} if contexts is None else contexts
        )
        self._allow_remote = allow_remote
        self._default_loader = jsonld.requests_document_loader()

    def register_context(
        self, url: str, document_or_path: str | Path | Mapping[str, Any]
    ) -> None:
        """Register or replace one remote URL with a local document or file."""
        self._contexts[url] = document_or_path

    def expand(self, document: Mapping[str, Any] | list[Any]) -> list[Any]:
        """Expand a JSON-LD document without modifying the caller's object."""
        return jsonld.expand(
            deepcopy(document),
            options={
                "processingMode": "json-ld-1.1",
                "documentLoader": self._document_loader,
            },
        )

    def expand_file(
        self, input_path: str | Path, output_path: str | Path | None = None
    ) -> list[Any]:
        """Expand a JSON file and optionally write the expanded JSON result."""
        source_path = Path(input_path)
        with source_path.open(encoding="utf-8") as source_file:
            document = json.load(source_file)

        expanded = self.expand(document)
        if output_path is not None:
            destination_path = Path(output_path)
            with destination_path.open("w", encoding="utf-8") as output_file:
                json.dump(expanded, output_file, indent=2, ensure_ascii=False)
                output_file.write("\n")
        return expanded

    def _document_loader(self, url: str, options: dict[str, Any] | None = None) -> dict[str, Any]:
        if url not in self._contexts:
            if not self._allow_remote:
                raise OfflineContextError(
                    f"Context URL is not registered for offline expansion: {url}"
                )
            print(f"Warning: resolving unmapped JSON-LD context remotely: {url}")
            return self._default_loader(url, options or {})

        source = self._contexts[url]
        if isinstance(source, Mapping):
            document = deepcopy(source)
        else:
            context_path = Path(source)
            if not context_path.is_absolute():
                context_path = self._context_dir.joinpath(str(context_path))
            if not context_path.is_file():
                raise FileNotFoundError(
                    f"Local context for {url} was not found: {context_path}"
                )
            try:
                with context_path.open(encoding="utf-8") as context_file:
                    document = json.load(context_file)
            except json.JSONDecodeError as error:
                raise ValueError(
                    f"Invalid JSON-LD context for {url}: {context_path}"
                ) from error

        return {
            "contextUrl": None,
            "documentUrl": url,
            "document": document,
        }
