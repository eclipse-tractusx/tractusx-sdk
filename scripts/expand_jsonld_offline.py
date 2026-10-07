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

"""Expand a JSON-LD document with the SDK's offline context loader."""

from __future__ import annotations

import argparse

from tractusx_sdk.extensions.semantics import OfflineJsonLdExpander


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", help="Input JSON-LD file")
    parser.add_argument("output", help="Output expanded JSON-LD file")
    parser.add_argument(
        "--allow-remote",
        action="store_true",
        help="Resolve contexts remotely when they are not packaged or registered",
    )
    args = parser.parse_args()
    OfflineJsonLdExpander(allow_remote=args.allow_remote).expand_file(
        args.input, args.output
    )


if __name__ == "__main__":
    main()
