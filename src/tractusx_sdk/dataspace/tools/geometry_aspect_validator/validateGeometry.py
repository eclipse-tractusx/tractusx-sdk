#!/usr/bin/env python3
# Geometry Validation Script
# This script orchestrates validation of SingleLevelSceneNode JSON files.

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any
from enum import Enum
from schemaValidator import SchemaValidator


class ValidationLevel(Enum):
    ERROR = 'error'
    WARNING = 'warning'
    INFO = 'info'


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
    
    def print_tree_structure(self):
        """Print a visual tree structure of validated files"""
        if not self.tree_structure:
            return
        
        print('\n=== SCENE TREE STRUCTURE ===')
        for idx, (file_path, depth, catena_x_id) in enumerate(self.tree_structure):
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
                    for j in range(idx + 1, len(self.tree_structure)):
                        if self.tree_structure[j][1] < d:
                            break
                        if self.tree_structure[j][1] == d:
                            has_more_at_level = True
                            break
                    indent_parts.append('│   ' if has_more_at_level else '    ')
                
                indent = ''.join(indent_parts)
                
                # Check if this is the last child at current level
                is_last_at_level = True
                for j in range(idx + 1, len(self.tree_structure)):
                    if self.tree_structure[j][1] < depth:
                        break
                    if self.tree_structure[j][1] == depth:
                        is_last_at_level = False
                        break
                
                prefix = '└── ' if is_last_at_level else '├── '
            
            # Shorten catenaXId for display
            if catena_x_id != 'N/A':
                short_id = catena_x_id.split(':')[-1][:8]
                id_display = f'[{short_id}...]'
            else:
                id_display = '[No ID]'
            
            print(f'{indent}{prefix}{file_path.name} {id_display}')
    
    def print_results(self):
        # Show tree structure if level is info
        if self.validation_level == ValidationLevel.INFO:
            self.print_tree_structure()
        
        # Always show errors
        if self.schema_validator.errors:
            print('\n=== ERRORS ===')
            for error in self.schema_validator.errors:
                print(f'  [ERROR] {error}')
        
        # Show warnings if level is warning or info
        if self.validation_level in [ValidationLevel.WARNING, ValidationLevel.INFO]:
            if self.schema_validator.warnings:
                print('\n=== WARNINGS ===')
                for warning in self.schema_validator.warnings:
                    print(f'  [WARNING] {warning}')
        
        # Show info only if level is info
        if self.validation_level == ValidationLevel.INFO:
            if self.schema_validator.infos:
                print('\n=== INFO ===')
                for info in self.schema_validator.infos:
                    print(f'  [INFO] {info}')
        
        print(f'\n=== SUMMARY ===')
        print(f'  Errors: {len(self.schema_validator.errors)}')
        print(f'  Warnings: {len(self.schema_validator.warnings)}')
        print(f'  Infos: {len(self.schema_validator.infos)}')


def main():
    parser = argparse.ArgumentParser(
        description='Validate geometry nodes from SingleLevelSceneNode JSON files',
        epilog='''
Examples:
  python validateGeometry.py exampleData/scene.json
  python validateGeometry.py exampleData/scene.json -d ./exampleData -v info
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
    validation_level = ValidationLevel(args.validation_level)
    validator = GeometryValidator(validation_level)
    
    schema_path = Path(args.schema) if args.schema else None
    if not validator.load_schema(schema_path):
        print('\nError: Could not load schema. Exiting.')
        sys.exit(1)
    
    if args.directory:
        directory_path = Path(args.directory)
        validator.build_catenax_id_map(directory_path)
    
    root_path = Path(args.root_node)
    validator.validate_file(root_path)
    validator.print_results()
    
    sys.exit(1 if validator.schema_validator.has_errors() else 0)


if __name__ == '__main__':
    main()
