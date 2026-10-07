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

import json
from pathlib import Path

import pytest

from tractusx_sdk.extensions.semantics import (
    OfflineContextError,
    OfflineJsonLdExpander,
)


CONTEXT_URL = "https://example.test/context.jsonld"


def test_expand_uses_registered_context_without_mutating_document() -> None:
    document = {"@context": CONTEXT_URL, "name": "catalog"}
    context = {"@context": {"name": "https://schema.org/name"}}
    expander = OfflineJsonLdExpander(contexts={CONTEXT_URL: context})

    expanded = expander.expand(document)

    assert document["@context"] == CONTEXT_URL
    assert expanded == [
        {
            "https://schema.org/name": [{"@value": "catalog"}],
        }
    ]
    assert context == {"@context": {"name": "https://schema.org/name"}}


def test_loader_returns_pyld_document_envelope() -> None:
    context = {"@context": {"name": "https://schema.org/name"}}
    expander = OfflineJsonLdExpander(contexts={CONTEXT_URL: context})

    loaded = expander._document_loader(CONTEXT_URL)

    assert loaded == {
        "contextUrl": None,
        "documentUrl": CONTEXT_URL,
        "document": context,
    }


def test_strict_mode_rejects_unregistered_context() -> None:
    unknown_url = "https://example.test/unregistered.jsonld"
    expander = OfflineJsonLdExpander(contexts={})

    with pytest.raises(OfflineContextError, match="not registered"):
        expander._document_loader(unknown_url)


def test_expand_file_writes_expanded_document(tmp_path: Path) -> None:
    input_path = tmp_path / "input.json"
    output_path = tmp_path / "output.json"
    input_path.write_text(
        json.dumps({"@context": CONTEXT_URL, "name": "catalog"}),
        encoding="utf-8",
    )
    expander = OfflineJsonLdExpander(
        contexts={CONTEXT_URL: {"@context": {"name": "https://schema.org/name"}}}
    )

    result = expander.expand_file(input_path, output_path)

    assert json.loads(output_path.read_text(encoding="utf-8")) == result
