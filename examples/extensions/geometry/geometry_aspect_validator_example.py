#################################################################################
# Eclipse Tractus-X - Software Development KIT
#
# Copyright (c) 2025 Threedy GmbH
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
Example usage of GeometryValidator.

This example demonstrates how to use the GeometryValidator to validate
SingleLevelSceneNode JSON files against the Catena-X schema.

The example shows:
- Loading the schema from the official Tractus-X repository
- Validating a single scene node file
- Validating a scene with child node references
- Using different validation levels (error, warning, info)

Alternatively, the validator can be run directly as a CLI tool:

  cd src/tractusx_sdk/extensions/geometry/geometry_aspect_validator/
  python validateGeometry.py <path/to/scene.json>
  python validateGeometry.py <path/to/scene.json> -d <path/to/exampleData/> -v info
"""

from pathlib import Path
from tractusx_sdk.extensions.geometry import GeometryValidator, ValidationLevel

EXAMPLE_DATA_DIR = Path(__file__).parent / "exampleData"


def example_simple_validation():
    """Validate a single scene node at error level (default)."""
    print("=== Simple Validation (error level) ===")

    validator = GeometryValidator(ValidationLevel.ERROR)

    if not validator.load_schema():
        print("Error: Could not load schema.")
        return

    validator.validate_file(EXAMPLE_DATA_DIR / "scene.json")
    validator.print_results()


def example_validation_with_children():
    """Validate a scene with child references, resolving them from the example data directory."""
    print("\n=== Validation with Child References (info level) ===")

    validator = GeometryValidator(ValidationLevel.INFO)

    if not validator.load_schema():
        print("Error: Could not load schema.")
        return

    # Build a map of catenaXId -> file for all JSON files in the directory
    # so child references can be resolved and validated recursively
    validator.build_catenax_id_map(EXAMPLE_DATA_DIR)

    validator.validate_file(EXAMPLE_DATA_DIR / "scene_with_child.json")
    validator.print_results()


def main():
    example_simple_validation()
    example_validation_with_children()


if __name__ == "__main__":
    main()
