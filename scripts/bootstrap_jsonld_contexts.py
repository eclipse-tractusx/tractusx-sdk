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

"""Download JSON-LD contexts into a local cache for offline expansion.

Examples::

    python scripts/bootstrap_jsonld_contexts.py https://example.test/context.jsonld
    python scripts/bootstrap_jsonld_contexts.py --default-contexts

Runtime code never invokes this script or downloads contexts implicitly in
strict offline mode.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request, urlopen


DEFAULT_CONTEXTS = {
    "https://w3id.org/dspace/2025/1/context.jsonld": "dspace-context.jsonld",
    "https://w3id.org/dspace/2025/1/odrl-profile.jsonld": (
        "dspace-odrl-profile.jsonld"
    ),
    "https://w3id.org/edc/dspace/v0.0.1": "edc-dspace-context.jsonld",
    "https://w3id.org/tractusx/auth/v1.0.0": "tractusx-auth-context.jsonld",
    "https://w3id.org/catenax/2025/9/policy/context.jsonld": (
        "catenax-policy-context.jsonld"
    ),
    "https://w3id.org/catenax/2025/9/policy/odrl.jsonld": (
        "catenax-policy-odrl.jsonld"
    ),
}
ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_DIR = ROOT / "src/tractusx_sdk/extensions/semantics/contexts"


def download_json(url: str) -> dict:
    request = Request(url, headers={"Accept": "application/ld+json, application/json"})
    with urlopen(request, timeout=30) as response:
        if response.status != 200:
            raise RuntimeError(f"Unable to download {url}: HTTP {response.status}")
        return json.loads(response.read().decode("utf-8"))


def filename_for(url: str) -> str:
    path_name = Path(urlparse(url).path).name
    return path_name or "context.jsonld"


def sanitize(url: str, document: dict) -> dict:
    if url in {
        "https://w3id.org/catenax/2025/9/policy/context.jsonld",
        "https://w3id.org/catenax/2025/9/policy/odrl.jsonld",
    }:
        context = document.get("@context")
        if isinstance(context, dict):
            context.pop("odrl", None)
    return document


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("urls", nargs="*", help="JSON-LD context URLs to download")
    parser.add_argument(
        "--default-contexts",
        action="store_true",
        help="Download the SDK's built-in context set",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Directory where downloaded contexts are written",
    )
    parser.add_argument(
        "--output",
        action="append",
        metavar="URL=FILENAME",
        help="Override the output filename for a URL; may be repeated",
    )
    args = parser.parse_args()
    if args.default_contexts:
        contexts = DEFAULT_CONTEXTS
    elif args.urls:
        contexts = {url: filename_for(url) for url in args.urls}
    else:
        parser.error("provide at least one URL or use --default-contexts")

    output_names = dict(contexts)
    for output in args.output or []:
        url, separator, filename = output.partition("=")
        if not separator or url not in contexts or not filename:
            parser.error(f"invalid --output value: {output!r}; expected URL=FILENAME")
        output_names[url] = filename

    args.output_dir.mkdir(parents=True, exist_ok=True)
    for url in contexts:
        document = sanitize(url, download_json(url))
        output_path = args.output_dir / output_names[url]
        output_path.write_text(
            json.dumps(document, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        print(f"Saved {url} -> {output_path}")


if __name__ == "__main__":
    main()
