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

"""
Schema Validator for SingleLevelSceneNode

This module validates SingleLevelSceneNode files against the Catena-X schema.
This module should only be used through validateGeometry.py.
Schema: https://github.com/eclipse-tractusx/sldt-semantic-models/blob/main/io.catenax.single_level_scene_node/1.0.0/gen/SingleLevelSceneNode-schema.json
"""

import json
import logging
import time
import requests
from pathlib import Path
from typing import Dict, List, Optional, Any
from jsonschema import validate, ValidationError, SchemaError

from tractusx_sdk._logging_fields import log_extra, safe_url

logger = logging.getLogger(__name__)


class SchemaValidator:
    """Validates SingleLevelSceneNode files against the Catena-X schema"""
    
    SCHEMA_URL = "https://raw.githubusercontent.com/eclipse-tractusx/sldt-semantic-models/main/io.catenax.single_level_scene_node/1.0.0/gen/SingleLevelSceneNode-schema.json"
    
    def __init__(self):
        self.schema: Optional[Dict[Any, Any]] = None
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.infos: List[str] = []
    
    # The findings are kept as data (see GeometryValidationReport); the log only echoes them.
    def add_error(self, message: str, log_message: Optional[str] = None):
        """
        Add an error message.

        :param message: The finding, as kept in the report
        :param log_message: What the DEBUG echo says instead of ``message``, when the finding quotes
            values of the validated document, which are not logged
        """
        logger.debug("Validation error: %s", log_message or message)
        self.errors.append(message)
    
    def add_warning(self, message: str):
        """Add a warning message"""
        logger.debug("Validation warning: %s", message)
        self.warnings.append(message)
    
    def add_info(self, message: str):
        """Add an info message"""
        logger.debug("Validation info: %s", message)
        self.infos.append(message)
    
    def load_schema_from_url(self) -> bool:
        """
        Load the SingleLevelSceneNode schema from the GitHub repository.
        
        Returns:
            bool: True if schema was loaded successfully, False otherwise
        """
        logger.debug("Loading the schema from %s", safe_url(self.SCHEMA_URL), extra=log_extra(url=self.SCHEMA_URL, operation="geometry.load_schema"))
        started = time.perf_counter()
        try:
            response = requests.get(self.SCHEMA_URL, timeout=10)
            response.raise_for_status()
            
            self.schema = response.json()
            elapsed_ms = round((time.perf_counter() - started) * 1000)
            logger.debug("The schema was loaded in %d ms", elapsed_ms,
                         extra=log_extra(url=self.SCHEMA_URL, elapsed_ms=elapsed_ms, operation="geometry.load_schema"))
            return True
            
        except requests.exceptions.RequestException as e:
            # Kept in the report as data: the log says it as well, as the validation cannot go on without the schema
            logger.warning("The schema could not be loaded from %s (%s)", safe_url(self.SCHEMA_URL), type(e).__name__,
                           extra=log_extra(url=self.SCHEMA_URL, operation="geometry.load_schema"))
            self.add_error(f"Failed to load schema from URL: {e}")
            return False
        except json.JSONDecodeError as e:
            logger.warning("The schema loaded from %s is not valid JSON", safe_url(self.SCHEMA_URL),
                           extra=log_extra(url=self.SCHEMA_URL, operation="geometry.load_schema"))
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
        logger.debug("Loading the schema from the file '%s'", schema_file, extra=log_extra(operation="geometry.load_schema"))
        try:
            with open(schema_file, 'r', encoding='utf-8') as f:
                self.schema = json.load(f)
            return True
            
        except FileNotFoundError:
            logger.warning("The schema file '%s' was not found", schema_file, extra=log_extra(operation="geometry.load_schema"))
            self.add_error(f"Schema file not found: {schema_file}")
            return False
        except json.JSONDecodeError as e:
            logger.warning("The schema file '%s' is not valid JSON", schema_file, extra=log_extra(operation="geometry.load_schema"))
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
            logger.warning("'%s' cannot be validated: no schema is loaded", file_name, extra=log_extra(operation="geometry.validate"))
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
            # The message of the finding quotes the offending value, which is data of the document: it is kept in
            # the report, and the log only says where the violation is and which rule it breaks
            location = " -> ".join(str(p) for p in e.path) if e.path else "root"
            self.add_error(f"[{file_name}] Schema validation error: {e.message}",
                           log_message=f"[{file_name}] Schema validation error at '{location}' ({e.validator})")
            
            # Add detailed path information if available
            if e.path:
                path_str = " -> ".join(str(p) for p in e.path)
                self.add_error(f"  Path: {path_str}")
            
            return False
            
        except SchemaError as e:
            logger.warning("The loaded schema is not a valid JSON schema (%s)", e.validator, extra=log_extra(operation="geometry.validate"))
            self.add_error(f"Schema error: {e.message}", log_message="Schema error: the loaded schema is not valid")
            return False
    
    def has_errors(self) -> bool:
        """Check if there are any validation errors"""
        return len(self.errors) > 0
    
    def has_warnings(self) -> bool:
        """Check if there are any warnings"""
        return len(self.warnings) > 0
