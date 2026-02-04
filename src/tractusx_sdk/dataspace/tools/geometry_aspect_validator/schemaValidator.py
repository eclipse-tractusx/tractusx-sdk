"""
Schema Validator for SingleLevelSceneNode

This module validates SingleLevelSceneNode files against the Catena-X schema.
This module should only be used through validateGeometry.py.
Schema: https://github.com/eclipse-tractusx/sldt-semantic-models/blob/main/io.catenax.single_level_scene_node/1.0.0/gen/SingleLevelSceneNode-schema.json
"""

import json
import requests
from pathlib import Path
from typing import Dict, List, Optional, Any
from jsonschema import validate, ValidationError, SchemaError


class SchemaValidator:
    """Validates SingleLevelSceneNode files against the Catena-X schema"""
    
    SCHEMA_URL = "https://raw.githubusercontent.com/eclipse-tractusx/sldt-semantic-models/main/io.catenax.single_level_scene_node/1.0.0/gen/SingleLevelSceneNode-schema.json"
    
    def __init__(self):
        self.schema: Optional[Dict[Any, Any]] = None
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.infos: List[str] = []
    
    def add_error(self, message: str):
        """Add an error message"""
        self.errors.append(message)
    
    def add_warning(self, message: str):
        """Add a warning message"""
        self.warnings.append(message)
    
    def add_info(self, message: str):
        """Add an info message"""
        self.infos.append(message)
    
    def load_schema_from_url(self) -> bool:
        """
        Load the SingleLevelSceneNode schema from the GitHub repository.
        
        Returns:
            bool: True if schema was loaded successfully, False otherwise
        """
        try:
            response = requests.get(self.SCHEMA_URL, timeout=10)
            response.raise_for_status()
            
            self.schema = response.json()
            return True
            
        except requests.exceptions.RequestException as e:
            self.add_error(f"Failed to load schema from URL: {e}")
            return False
        except json.JSONDecodeError as e:
            self.add_error(f"Failed to parse schema JSON: {e}")
            return False
    
    def load_schema_from_file(self, schema_file: Path) -> bool:
        """
        Load the SingleLevelSceneNode schema from a local file.
        
        Args:
            schema_file: Path to the local schema file
            
        Returns:
            bool: True if schema was loaded successfully, False otherwise
        """
        try:
            with open(schema_file, 'r', encoding='utf-8') as f:
                self.schema = json.load(f)
            return True
            
        except FileNotFoundError:
            self.add_error(f"Schema file not found: {schema_file}")
            return False
        except json.JSONDecodeError as e:
            self.add_error(f"Failed to parse schema JSON from file: {e}")
            return False
    
    def _check_field_presence(self, data: Dict[Any, Any], file_name: str):
        """
        Check which fields are present and report on optional fields.
        
        Args:
            data: The scene node data
            file_name: Name of the file being validated
        """
        # Required fields (from schema)
        required_fields = ['catenaXId']
        
        # Optional fields (from schema)
        optional_fields = ['childItems', 'localTransform', 'boundingVolume', 'modelItems']
        
        # Check required fields
        for field in required_fields:
            if field in data:
                self.add_info(f"[{file_name}] Required field present: '{field}'")
            else:
                self.add_error(f"[{file_name}] Missing required field: '{field}'")
        
        # Check optional fields
        for field in optional_fields:
            if field in data:
                # Provide details about the field
                if field == 'childItems' and isinstance(data[field], list):
                    self.add_info(f"[{file_name}] Optional field present: '{field}' ({len(data[field])} items)")
                elif field == 'modelItems' and isinstance(data[field], list):
                    self.add_info(f"[{file_name}] Optional field present: '{field}' ({len(data[field])} items)")
                elif field == 'localTransform' and isinstance(data[field], dict):
                    if 'matrix4x4' in data[field]:
                        self.add_info(f"[{file_name}] Optional field present: '{field}' (with matrix4x4)")
                    else:
                        self.add_info(f"[{file_name}] Optional field present: '{field}'")
                elif field == 'boundingVolume' and isinstance(data[field], dict):
                    has_min = 'minPoint' in data[field]
                    has_max = 'maxPoint' in data[field]
                    self.add_info(f"[{file_name}] Optional field present: '{field}' (minPoint: {has_min}, maxPoint: {has_max})")
                else:
                    self.add_info(f"[{file_name}] Optional field present: '{field}'")
            else:
                self.add_info(f"[{file_name}] Optional field missing: '{field}'")
        
        # Check childItems structure if present
        if 'childItems' in data and isinstance(data['childItems'], list):
            for idx, child in enumerate(data['childItems']):
                if isinstance(child, dict):
                    if 'catenaXId' in child:
                        self.add_info(f"[{file_name}] childItems[{idx}] has catenaXId: {child['catenaXId']}")
                    else:
                        self.add_warning(f"[{file_name}] childItems[{idx}] missing required catenaXId")
                    
                    # Check optional fields in child
                    if 'semanticTags' in child:
                        self.add_info(f"[{file_name}] childItems[{idx}] has semanticTags")
                    if 'customTags' in child:
                        self.add_info(f"[{file_name}] childItems[{idx}] has customTags")
                    if 'localTransform' in child:
                        self.add_info(f"[{file_name}] childItems[{idx}] has localTransform")
    
    def validate_data(self, scene_node_data: Dict[Any, Any], file_name: str = "data") -> bool:
        """
        Validate a SingleLevelSceneNode data against the schema.
        
        Args:
            scene_node_data: The scene node data to validate
            file_name: Name of the file being validated (for error reporting)
            
        Returns:
            bool: True if validation passed, False otherwise
        """
        if self.schema is None:
            self.add_error("error: Schema not loaded.")
            return False
        
        # Check field presence and provide info
        # TOOD: this only applies to the Version 1.0.0 schema. If the schema changes, this has to be adjusted.
        self._check_field_presence(scene_node_data, file_name)
        
        try:
            # Validate against the schema
            validate(instance=scene_node_data, schema=self.schema)
            self.add_info(f"[{file_name}] Schema validation passed")
            return True
            
        except ValidationError as e:
            self.add_error(f"[{file_name}] Schema validation error: {e.message}")
            
            # Add detailed path information if available
            if e.path:
                path_str = " -> ".join(str(p) for p in e.path)
                self.add_error(f"  Path: {path_str}")
            
            return False
            
        except SchemaError as e:
            self.add_error(f"Schema error: {e.message}")
            return False
    
    def has_errors(self) -> bool:
        """Check if there are any validation errors"""
        return len(self.errors) > 0
    
    def has_warnings(self) -> bool:
        """Check if there are any warnings"""
        return len(self.warnings) > 0
