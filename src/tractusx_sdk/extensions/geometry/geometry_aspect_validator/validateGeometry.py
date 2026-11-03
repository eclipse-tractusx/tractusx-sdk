#!/usr/bin/env python3
#################################################################################
# Eclipse Tractus-X - Software Development KIT
#
# Copyright (c) 2026 LKS Next
# Copyright (c) 2026 Contributors to the Eclipse Foundation
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

# Geometry Validation Script
# This script orchestrates validation of SingleLevelSceneNode JSON files.

import argparse
import json
import logging
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Any
from enum import Enum

try:
    from .schemaValidator import SchemaValidator
except ImportError:  # executed as a script from this directory
    from schemaValidator import SchemaValidator

logger = logging.getLogger(__name__)


class ValidationLevel(Enum):
    ERROR = 'error'
    WARNING = 'warning'
    INFO = 'info'


@dataclass(frozen=True)
class SceneTreeNode:
    """A validated file and its position in the scene tree."""

    file_path: Path
    depth: int
    catenax_id: str = 'N/A'


@dataclass(frozen=True)
class GeometryValidationReport:
    """
    The outcome of validating a scene: every finding and the tree that was walked.

    It holds all findings whatever the validation level is; the level only decides
    what :meth:`render` shows.
    """

    errors: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    infos: tuple[str, ...] = ()
    tree: tuple[SceneTreeNode, ...] = ()

    @property
    def has_errors(self) -> bool:
        return len(self.errors) > 0

    @property
    def has_warnings(self) -> bool:
        return len(self.warnings) > 0

    def render(self, validation_level: ValidationLevel = ValidationLevel.ERROR) -> str:
        """Render the report as text for the given validation level."""
        lines: List[str] = []

        # Show tree structure if level is info
        if validation_level == ValidationLevel.INFO:
            lines.extend(_render_tree(self.tree))

        # Always show errors
        if self.errors:
            lines.append('\n=== ERRORS ===')
            lines.extend(f'  [ERROR] {error}' for error in self.errors)

        # Show warnings if level is warning or info
        if validation_level in [ValidationLevel.WARNING, ValidationLevel.INFO] and self.warnings:
            lines.append('\n=== WARNINGS ===')
            lines.extend(f'  [WARNING] {warning}' for warning in self.warnings)

        # Show info only if level is info
        if validation_level == ValidationLevel.INFO and self.infos:
            lines.append('\n=== INFO ===')
            lines.extend(f'  [INFO] {info}' for info in self.infos)

        lines.append('\n=== SUMMARY ===')
        lines.append(f'  Errors: {len(self.errors)}')
        lines.append(f'  Warnings: {len(self.warnings)}')
        lines.append(f'  Infos: {len(self.infos)}')
        return '\n'.join(lines)


def _render_tree(tree: tuple[SceneTreeNode, ...]) -> List[str]:
    """Render a visual tree structure of validated files."""
    if not tree:
        return []

    lines = ['\n=== SCENE TREE STRUCTURE ===']
    for idx, node in enumerate(tree):
        depth = node.depth
        # Build the tree lines
        if depth == 0:
            prefix = '• '
            indent = ''
        else:
            # Create proper tree structure with lines
            indent_parts = []
            for d in range(1, depth):
                # Check if there will be more nodes at level d after current node
                has_more_at_level = False
                for later in tree[idx + 1:]:
                    if later.depth < d:
                        break
                    if later.depth == d:
                        has_more_at_level = True
                        break
                indent_parts.append('│   ' if has_more_at_level else '    ')

            indent = ''.join(indent_parts)

            # Check if this is the last child at current level
            is_last_at_level = True
            for later in tree[idx + 1:]:
                if later.depth < depth:
                    break
                if later.depth == depth:
                    is_last_at_level = False
                    break

            prefix = '└── ' if is_last_at_level else '├── '

        # Shorten catenaXId for display
        if node.catenax_id != 'N/A':
            short_id = node.catenax_id.split(':')[-1][:8]
            id_display = f'[{short_id}...]'
        else:
            id_display = '[No ID]'

        lines.append(f'{indent}{prefix}{node.file_path.name} {id_display}')
    return lines


class GeometryValidator:
    def __init__(self, validation_level: ValidationLevel = ValidationLevel.ERROR):
        self.validation_level = validation_level
        self.catenax_id_map: Dict[str, Path] = {}
        self.validated_files: set = set()
        self.schema_validator = SchemaValidator()
        self.tree_structure: List[tuple] = []  # Stores (file_path, depth, catenaXId) for tree visualization
    
    def load_schema(self, schema_file: Optional[Path] = None) -> bool:
        if schema_file:
            return self.schema_validator.load_schema_from_file(schema_file)
        else:
            return self.schema_validator.load_schema_from_url()
    
    def load_json_file(self, file_path: Path) -> Optional[Dict[Any, Any]]:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data
        except FileNotFoundError:
            self.schema_validator.add_error(f'File not found: {file_path}')
            return None
        except json.JSONDecodeError as e:
            self.schema_validator.add_error(f'Invalid JSON in {file_path}: {e}')
            return None
        except Exception as e:
            self.schema_validator.add_error(f'Error loading {file_path}: {e}')
            return None
    
    def build_catenax_id_map(self, directory: Path):
        if not directory.exists() or not directory.is_dir():
            self.schema_validator.add_warning(f'Cannot build map: invalid directory {directory}')
            return
        
        json_files = list(directory.glob('*.json'))
        
        for json_file in json_files:
            data = self.load_json_file(json_file)
            if data and 'catenaXId' in data:
                catenax_id = data['catenaXId']
                if catenax_id in self.catenax_id_map:
                    self.schema_validator.add_warning(f'Duplicate catenaXId "{catenax_id}" found in {json_file.name}')
                else:
                    self.catenax_id_map[catenax_id] = json_file
    
    def find_referenced_catenax_ids(self, node: Dict[Any, Any]) -> List[str]:
        referenced_ids = []
        if 'childItems' in node and isinstance(node['childItems'], list):
            for child in node['childItems']:
                if isinstance(child, dict) and 'catenaXId' in child:
                    referenced_ids.append(child['catenaXId'])
        return referenced_ids
    
    def validate_file(self, file_path: Path, depth: int = 0):
        file_key = str(file_path)
        if file_key in self.validated_files:
            return
        
        self.validated_files.add(file_key)
        
        data = self.load_json_file(file_path)
        if data is None:
            return
        
        # Store tree structure information
        catena_x_id = data.get('catenaXId', 'N/A') if data else 'N/A'
        self.tree_structure.append((file_path, depth, catena_x_id))
        
        self.schema_validator.validate_data(data, file_path.name)
        referenced_ids = self.find_referenced_catenax_ids(data)
        
        if referenced_ids:
            for catenax_id in referenced_ids:
                if catenax_id in self.catenax_id_map:
                    referenced_file = self.catenax_id_map[catenax_id]
                    self.validate_file(referenced_file, depth + 1)
                else:
                    self.schema_validator.add_warning(f'Referenced catenaXId "{catenax_id}" not found in available files')
    
    def report(self) -> GeometryValidationReport:
        """Snapshot of everything found so far. Nothing is printed or logged to build it."""
        return GeometryValidationReport(
            errors=tuple(self.schema_validator.errors),
            warnings=tuple(self.schema_validator.warnings),
            infos=tuple(self.schema_validator.infos),
            tree=tuple(SceneTreeNode(file_path, depth, catenax_id) for file_path, depth, catenax_id in self.tree_structure),
        )

    def render_report(self) -> str:
        """The report as text, for the validation level this validator was created with."""
        return self.report().render(self.validation_level)


def main():
    parser = argparse.ArgumentParser(
        description='Validate geometry nodes from SingleLevelSceneNode JSON files',
        epilog='''
Examples:
  python validateGeometry.py scene.json
  python validateGeometry.py scene.json -d ./data/ -v info

Sample data: https://github.com/eclipse-tractusx/tractusx-sdk/tree/main/examples/extensions/geometry
        ''',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        'root_node',
        type=str,
        help='Path to the root SingleLevelSceneNode JSON file to validate'
    )
    
    parser.add_argument(
        '-v', '--validation-level',
        type=str,
        choices=['error', 'warning', 'info'],
        default='error',
        metavar='LEVEL',
        help='Validation log level: error (default), warning, or info'
    )
    
    parser.add_argument(
        '-d', '--directory',
        type=str,
        default=None,
        metavar='DIR',
        help='Directory containing additional scene files for catenaXId reference resolution'
    )
    
    parser.add_argument(
        '-s', '--schema',
        type=str,
        default=None,
        metavar='FILE',
        help='Path to local schema file (if not provided, schema is loaded from GitHub)'
    )
    
    args = parser.parse_args()
    logging.basicConfig(level=logging.WARNING, format='%(levelname)s: %(message)s')
    validation_level = ValidationLevel(args.validation_level)
    validator = GeometryValidator(validation_level)
    
    schema_path = Path(args.schema) if args.schema else None
    if not validator.load_schema(schema_path):
        logger.error('Could not load schema: %s', '; '.join(validator.schema_validator.errors))
        sys.exit(1)
    
    if args.directory:
        directory_path = Path(args.directory)
        validator.build_catenax_id_map(directory_path)
    
    root_path = Path(args.root_node)
    validator.validate_file(root_path)

    # The report is the product of this command, so it goes to stdout rather than through the logger
    sys.stdout.write(validator.render_report() + '\n')
    
    sys.exit(1 if validator.schema_validator.has_errors() else 0)


if __name__ == '__main__':
    main()
