#################################################################################
# Eclipse Tractus-X - Software Development KIT
#
# Copyright (c) 2025 Contributors to the Eclipse Foundation
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
## Code created partially using a LLM (Claude Sonnet 4) and reviewed by a human committer

import math
import pytest
import logging
from unittest.mock import Mock, patch
from tractusx_sdk.extensions.semantics.schema_to_context_translator import SammSchemaContextTranslator


@pytest.fixture
def translator():
    """Create a basic translator instance for testing."""
    return SammSchemaContextTranslator()


@pytest.fixture
def translator_with_logger():
    """Create a translator instance with a logger for debug testing."""
    logger = Mock(spec=logging.Logger)
    return SammSchemaContextTranslator(logger=logger, debug=True)


@pytest.fixture
def simple_schema():
    """A simple string schema for testing."""
    return {
        "type": "string",
        "description": "A simple string property"
    }


@pytest.fixture
def object_schema():
    """A simple object schema for testing."""
    return {
        "type": "object",
        "description": "A simple object",
        "properties": {
            "name": {
                "$ref": "#/components/schemas/StringProperty"
            },
            "age": {
                "$ref": "#/components/schemas/NumberProperty"
            }
        }
    }


@pytest.fixture
def array_schema():
    """A simple array schema for testing."""
    return {
        "type": "array",
        "description": "An array of strings",
        "items": {
            "$ref": "#/components/schemas/StringProperty"
        }
    }


@pytest.fixture
def complex_schema():
    """A complex schema with nested references."""
    return {
        "type": "object",
        "description": "Complex nested schema",
        "properties": {
            "basicInfo": {
                "$ref": "#/components/schemas/BasicInfo"
            },
            "items": {
                "$ref": "#/components/schemas/ItemList"
            }
        },
        "components": {
            "schemas": {
                "BasicInfo": {
                    "type": "object",
                    "properties": {
                        "name": {
                            "$ref": "#/components/schemas/StringProperty"
                        }
                    }
                },
                "ItemList": {
                    "type": "array",
                    "items": {
                        "$ref": "#/components/schemas/StringProperty"
                    }
                },
                "StringProperty": {
                    "type": "string"
                },
                "NumberProperty": {
                    "type": "number"
                }
            }
        }
    }


class TestSammSchemaContextTranslatorInit:
    """Test initialization and basic properties."""

    def test_init_default(self):
        """Test default initialization."""
        translator = SammSchemaContextTranslator()
        
        assert translator.baseSchema == {}
        assert translator.rootRef == "#"
        assert translator.refKey == "$ref"
        assert translator.path_sep == "#/"
        assert translator.actualPathSep == "/-/"
        assert translator.refPathSep == "/"
        assert translator.propertiesKey == "properties"
        assert translator.logger is None
        assert translator.debug is False
        assert translator.itemKey == "items"
        assert translator.schemaPrefix == "schema"
        assert translator.aspectPrefix == "aspect"
        assert translator.contextPrefix == "@context"
        assert translator.recursionDepth == 2
        assert translator.depth == 0

    def test_init_with_logger_and_debug(self):
        """Test initialization with logger and debug mode."""
        logger = Mock(spec=logging.Logger)
        translator = SammSchemaContextTranslator(logger=logger, debug=True)
        
        assert translator.logger == logger
        assert translator.debug is True

    def test_initial_jsonld_structure(self, translator):
        """Test the initial JSON-LD structure."""
        expected = {
            "@version": 1.1,
            "schema": "https://schema.org/"
        }
        assert translator.initialJsonLd == expected

    def test_context_template_structure(self, translator):
        """Test the context template structure."""
        expected = {
            "@version": 1.1,
            "id": "@id",
            "type": "@type"
        }
        assert translator.contextTemplate == expected


class TestSchemaToJsonLD:
    """Test the main schema_to_jsonld method."""

    def test_schema_to_jsonld_simple_string(self, translator):
        """Test converting a simple string schema to JSON-LD (flattened)."""
        semantic_id = "urn:samm:example:1.0.0#TestAspect"
        schema = {
            "type": "string",
            "description": "Test string property"
        }
        
        result = translator.schema_to_jsonld(semantic_id, schema)
        
        assert "@context" in result
        context = result["@context"]
        assert "@version" in context
        assert math.isclose(context["@version"], 1.1, rel_tol=1e-09, abs_tol=1e-09)
        assert "schema" in context
        assert context["schema"] == "https://schema.org/"
        assert "TestAspect" in context
        assert context["cx"] == "urn:samm:example:1.0.0#"
        assert "@definition" in context
        assert context["@definition"] == "Test string property"

    def test_schema_to_jsonld_with_custom_aspect_prefix(self, translator):
        """Test with nested schema method which supports custom aspect prefix."""
        semantic_id = "urn:samm:example:1.0.0#Custom"
        schema = {"type": "string"}
        
        result = translator.schema_to_jsonld_nested(semantic_id, schema)
        
        context = result["@context"]
        assert "Custom" in context
        assert context["Custom"]["@id"] == "cx:Custom"

    def test_schema_to_jsonld_invalid_semantic_id(self, translator):
        """Test with invalid semantic ID."""
        invalid_ids = [
            "invalid_semantic_id",
            "urn:samm:example:1.0.0",
            "urn:samm:example:1.0.0#",
            ""
        ]
        schema = {"type": "string"}
        
        for invalid_id in invalid_ids:
            with pytest.raises(Exception, match="It was not possible to create flattened jsonld schema"):
                translator.schema_to_jsonld(invalid_id, schema)

    def test_schema_to_jsonld_with_description(self, translator):
        """Test schema with description (flattened context)."""
        semantic_id = "urn:samm:example:1.0.0#TestAspect"
        schema = {
            "type": "string",
            "description": "Test description"
        }
        
        result = translator.schema_to_jsonld(semantic_id, schema)
        context = result["@context"]
        
        assert "TestAspect" in context
        assert context["cx"] == "urn:samm:example:1.0.0#"
        assert "@definition" in context
        assert context["@definition"] == "Test description"

    def test_schema_to_jsonld_with_conflicting_properties(self, translator):
        """Test schema with properties that conflict with JSON-LD reserved words."""
        semantic_id = "urn:samm:example:1.0.0#TestAspect"
        
        # Create a schema with property references that would create "id" and "type" context entries
        schema = {
            "type": "object",
            "description": "Schema with conflicting properties",
            "properties": {
                "identifier": {
                    "$ref": "#/components/schemas/IdProperty"
                },
                "typeField": {
                    "$ref": "#/components/schemas/TypeProperty"
                },
                "normalProp": {
                    "$ref": "#/components/schemas/StringProperty"
                }
            },
            "components": {
                "schemas": {
                    "IdProperty": {
                        "type": "string",
                        "description": "An ID property"
                    },
                    "TypeProperty": {
                        "type": "string", 
                        "description": "A type property"
                    },
                    "StringProperty": {
                        "type": "string",
                        "description": "A normal property"
                    }
                }
            }
        }
        
        result = translator.schema_to_jsonld(semantic_id, schema)
        context = result["@context"]
        
        # Verify basic structure
        assert "TestAspect" in context
        assert context["cx"] == "urn:samm:example:1.0.0#"
        assert "@definition" in context
        assert context["@definition"] == "Schema with conflicting properties"
        
        # Verify properties are present (these should be normal properties, not conflicting ones)
        assert "identifier" in context
        assert "typeField" in context
        assert "normalProp" in context
        
        # Verify the standard JSON-LD properties remain unchanged
        assert context["id"] == "@id"
        assert context["type"] == "@type"

    @patch.object(SammSchemaContextTranslator, 'create_node')
    def test_schema_to_jsonld_with_id_type_conflict_resolution(self, mock_create_node, translator):
        """Test the specific logic for handling 'id' and 'type' property conflicts."""
        semantic_id = "urn:samm:example:1.0.0#TestAspect"
        schema = {"type": "object", "description": "Test schema"}
        
        # Mock create_node to return a context that has "id" and "type" as non-string values
        # This simulates the scenario where the nested context would conflict with JSON-LD reserved words
        mock_create_node.return_value = {
            "@context": {
                "@version": 1.1,
                "id": {"@id": "aspect:id", "@type": "schema:string"},  # Non-string value that should get prefixed
                "type": {"@id": "aspect:type", "@type": "schema:string"},  # Non-string value that should get prefixed
                "normalProp": {"@id": "aspect:normalProp", "@type": "schema:string"},
                "stringValue": "this-stays-as-is"  # String value that should not get prefixed
            }
        }
        
        result = translator.schema_to_jsonld(semantic_id, schema)
        context = result["@context"]
        
        # Verify that non-string "id" and "type" properties get prefixed with aspect prefix
        assert "cx:id" in context
        assert "cx:type" in context
        assert context["cx:id"] == {"@id": "aspect:id", "@type": "schema:string"}
        assert context["cx:type"] == {"@id": "aspect:type", "@type": "schema:string"}
        
        # Verify that normal properties don't get prefixed
        assert "normalProp" in context
        assert context["normalProp"] == {"@id": "aspect:normalProp", "@type": "schema:string"}
        
        # Verify that string values don't get prefixed (even if they're named "id" or "type")
        assert "stringValue" in context
        assert context["stringValue"] == "this-stays-as-is"
        
        # Verify that the conflicting properties are NOT present as standard JSON-LD properties
        # because they were moved to prefixed versions
        assert "id" not in context
        assert "type" not in context
        
        # Verify other standard context elements are present
        assert math.isclose(context["@version"], 1.1, rel_tol=1e-09, abs_tol=1e-09)
        assert context["cx"] == "urn:samm:example:1.0.0#"
        assert context["@definition"] == "Test schema"

    @patch.object(SammSchemaContextTranslator, 'create_node')
    def test_schema_to_jsonld_without_id_type_conflicts(self, mock_create_node, translator):
        """Test that standard JSON-LD properties are preserved when there are no conflicts."""
        semantic_id = "urn:samm:example:1.0.0#TestAspect"
        schema = {"type": "object", "description": "Test schema"}
        
        # Mock create_node to return a context with standard JSON-LD id/type as strings
        # (these should not be prefixed since they are strings)
        mock_create_node.return_value = {
            "@context": {
                "@version": 1.1,
                "id": "@id",  # String value - should not get prefixed
                "type": "@type",  # String value - should not get prefixed
                "normalProp": {"@id": "aspect:normalProp", "@type": "schema:string"},
                "anotherProp": {"@id": "aspect:anotherProp", "@type": "schema:string"}
            }
        }
        
        result = translator.schema_to_jsonld(semantic_id, schema)
        context = result["@context"]
        
        # Verify that standard JSON-LD properties are present when they are strings
        assert "id" in context
        assert "type" in context
        assert context["id"] == "@id"
        assert context["type"] == "@type"
        
        # Verify that conflicting prefixed versions are NOT present
        assert "cx:id" not in context
        assert "cx:type" not in context
        
        # Verify normal properties are present
        assert "normalProp" in context
        assert "anotherProp" in context


class TestCreateNode:
    """Test the create_node method and its variations."""

    def test_create_node_string_type(self, translator):
        """Test creating a node for string type."""
        property_def = {"type": "string"}
        result = translator.create_node(property_def)
        
        assert result is not None
        assert "@type" in result
        assert result["@type"] == "schema:string"

    def test_create_node_number_type(self, translator):
        """Test creating a node for number type."""
        property_def = {"type": "number"}
        result = translator.create_node(property_def)
        
        assert result is not None
        assert "@type" in result
        assert result["@type"] == "schema:number"

    def test_create_node_no_type(self, translator):
        """Test creating a node without type returns None."""
        property_def = {"description": "No type property"}
        result = translator.create_node(property_def)
        
        assert result is None

    def test_create_node_empty_property(self, translator):
        """Test creating a node with empty property returns None."""
        result = translator.create_node(None)
        assert result is None
        
        result = translator.create_node({})
        assert result is None


class TestCreateValueNode:
    """Test the create_value_node method."""

    def test_create_value_node_string(self, translator):
        """Test creating a value node for string."""
        property_def = {"type": "string"}
        node = {}
        result = translator.create_value_node(property_def, node)
        
        assert result is not None
        assert "@type" in result
        assert result["@type"] == "schema:string"

    def test_create_value_node_boolean(self, translator):
        """Test creating a value node for boolean."""
        property_def = {"type": "boolean"}
        node = {}
        result = translator.create_value_node(property_def, node)
        
        assert result is not None
        assert "@type" in result
        assert result["@type"] == "schema:boolean"

    def test_create_value_node_no_type(self, translator):
        """Test creating a value node without type returns None."""
        property_def = {"description": "No type"}
        node = {}
        result = translator.create_value_node(property_def, node)
        
        assert result is None


class TestCreateObjectNode:
    """Test the create_object_node method."""

    @patch.object(SammSchemaContextTranslator, 'create_single_properties_context')
    def test_create_object_node_with_properties(self, mock_create_properties, translator):
        """Test creating an object node with properties."""
        mock_create_properties.return_value = {"test": "context"}
        
        property_def = {
            "type": "object",
            "properties": {
                "name": {"$ref": "#/components/schemas/StringProperty"}
            }
        }
        node = {}
        
        result = translator.create_object_node(property_def, node, "test/ref")
        
        assert result is not None
        assert "@context" in result
        assert result["@context"] == {"test": "context"}
        mock_create_properties.assert_called_once()

    def test_create_object_node_no_properties(self, translator):
        """Test creating an object node without properties returns None."""
        property_def = {"type": "object"}
        node = {}
        
        result = translator.create_object_node(property_def, node, "test/ref")
        assert result is None


class TestCreateArrayNode:
    """Test the create_array_node method."""

    def test_create_array_node_with_simple_items(self, translator):
        """Test creating an array node with simple items."""
        property_def = {
            "type": "array",
            "items": {"type": "string"}
        }
        node = {}
        
        result = translator.create_array_node(property_def, node, "test/ref")
        
        assert result is not None
        assert "@container" in result
        assert result["@container"] == "@list"
        assert "@type" in result
        assert result["@type"] == "schema:string"

    def test_create_array_node_with_list_items(self, translator):
        """Test creating an array node with list items."""
        property_def = {
            "type": "array",
            "items": []
        }
        node = {}
        
        result = translator.create_array_node(property_def, node, "test/ref")
        
        assert result is not None
        assert "@container" in result
        assert result["@container"] == "@list"

    @patch.object(SammSchemaContextTranslator, 'create_item_context')
    def test_create_array_node_with_ref_items(self, mock_create_item, translator):
        """Test creating an array node with reference items."""
        mock_create_item.return_value = {"test": "context"}
        
        property_def = {
            "type": "array",
            "items": {"$ref": "#/components/schemas/StringProperty"}
        }
        node = {}
        
        result = translator.create_array_node(property_def, node, "test/ref")
        
        assert result is not None
        assert "@container" in result
        assert result["@container"] == "@list"
        assert "@context" in result
        assert result["@context"] == {"test": "context"}

    def test_create_array_node_no_items(self, translator):
        """Test creating an array node without items returns None."""
        property_def = {"type": "array"}
        node = {}
        
        result = translator.create_array_node(property_def, node, "test/ref")
        assert result is None


class TestFilterKey:
    """Test the filter_key method."""

    def test_filter_key_with_at_symbol(self, translator):
        """Test filtering key with @ symbol."""
        result = translator.filter_key("@type")
        assert result == "type"

    def test_filter_key_with_spaces(self, translator):
        """Test filtering key with spaces."""
        result = translator.filter_key("my property")
        assert result == "my-property"

    def test_filter_key_with_both(self, translator):
        """Test filtering key with both @ and spaces."""
        result = translator.filter_key("@my property")
        assert result == "my-property"

    def test_filter_key_normal(self, translator):
        """Test filtering normal key."""
        result = translator.filter_key("normalKey")
        assert result == "normalKey"


class TestCreatePropertiesContext:
    """Test the create_single_properties_context method."""

    @patch.object(SammSchemaContextTranslator, 'create_node_property')
    def test_create_properties_context_valid(self, mock_create_node_property, translator):
        """Test creating properties context with valid properties."""
        mock_create_node_property.return_value = {"@id": "aspect:testProp"}
        
        properties = {
            "testProp": {"$ref": "#/components/schemas/StringProperty"}
        }
        
        result = translator.create_single_properties_context(properties, "test/ref")
        
        assert result is not None
        assert "@version" in result
        assert math.isclose(result["@version"], 1.1, rel_tol=1e-09, abs_tol=1e-09)
        assert "id" in result
        assert "type" in result
        assert "testProp" in result
        assert result["testProp"] == {"@id": "aspect:testProp"}

    def test_create_properties_context_empty(self, translator):
        """Test creating properties context with empty properties returns None."""
        result = translator.create_single_properties_context({}, "test/ref")
        assert result is None
        
        result = translator.create_single_properties_context(None, "test/ref")
        assert result is None

    def test_create_properties_context_invalid_type(self, translator):
        """Test creating properties context with invalid type returns None."""
        result = translator.create_single_properties_context("not_a_dict", "test/ref")
        assert result is None


class TestCreateSimpleNode:
    """Test the create_simple_node method."""

    def test_create_simple_node_with_key(self, translator):
        """Test creating simple node with key."""
        property_def = {"description": "Test property"}
        result = translator.create_simple_node(property_def, "testKey")
        
        assert result is not None
        assert "@id" in result
        assert result["@id"] == "aspect:testKey"
        assert "@context" in result
        assert "@definition" in result["@context"]
        assert result["@context"]["@definition"] == "Test property"

    def test_create_simple_node_without_key(self, translator):
        """Test creating simple node without key."""
        property_def = {"description": "Test property"}
        result = translator.create_simple_node(property_def)
        
        assert result is not None
        assert "@id" not in result
        assert "@context" in result
        assert "@definition" in result["@context"]
        assert result["@context"]["@definition"] == "Test property"

    def test_create_simple_node_no_description(self, translator):
        """Test creating simple node without description."""
        property_def = {"type": "string"}
        result = translator.create_simple_node(property_def, "testKey")
        
        assert result is not None
        assert "@id" in result
        assert result["@id"] == "aspect:testKey"
        assert "@context" not in result

    def test_create_simple_node_empty_property(self, translator):
        """Test creating simple node with empty property returns None."""
        result = translator.create_simple_node(None)
        assert result is None


class TestGetSchemaRef:
    """Test the get_schema_ref method with mocked op.get_attribute."""

    @patch('tractusx_sdk.extensions.semantics.schema_to_context_translator.op.get_attribute')
    def test_get_schema_ref_valid(self, mock_get_attribute, translator):
        """Test getting schema reference with valid path."""
        mock_get_attribute.return_value = {"type": "string"}
        translator.baseSchema = {"components": {"schemas": {"StringProperty": {"type": "string"}}}}
        
        result = translator.get_schema_ref("#/components/schemas/StringProperty", "test/ref")
        
        assert result == {"type": "string"}
        mock_get_attribute.assert_called_once_with(
            translator.baseSchema, 
            attr_path="components/schemas/StringProperty", 
            path_sep="/",
            default_value=None
        )

    def test_get_schema_ref_invalid_type(self, translator):
        """Test getting schema reference with invalid type returns None."""
        result = translator.get_schema_ref(123, "test/ref")
        assert result is None

    @patch('tractusx_sdk.extensions.semantics.schema_to_context_translator.op.get_attribute')
    def test_get_schema_ref_recursion_detection(self, mock_get_attribute, translator_with_logger):
        """Test recursion detection in get_schema_ref."""
        import hashlib
        
        mock_get_attribute.return_value = {"type": "string"}
        translator_with_logger.baseSchema = {"test": "schema"}
        
        # Test case where ref is NOT in actualref (should work normally)
        result1 = translator_with_logger.get_schema_ref("test/ref", "some/other/path")
        assert result1 == {"type": "string"}
        
        # Test case where ref hash IS in actualref and depth exceeds limit
        ref = "test/ref"
        ref_hash = hashlib.sha256(ref.encode()).hexdigest()
        actualref_with_hash = f"some/path/{ref_hash}/more"
        
        # Set depth to exceed limit
        translator_with_logger.depth = translator_with_logger.recursionDepth  # Should trigger limit
        
        result2 = translator_with_logger.get_schema_ref(ref, actualref_with_hash)
        assert result2 is None
        
        # Check that warning was logged
        translator_with_logger.logger.warning.assert_called()


class TestExpandNode:
    """Test the expand_node method."""

    @patch.object(SammSchemaContextTranslator, 'get_schema_ref')
    @patch.object(SammSchemaContextTranslator, 'create_node')
    def test_expand_node_valid(self, mock_create_node, mock_get_schema_ref, translator):
        """Test expanding a valid node reference."""
        mock_get_schema_ref.return_value = {"type": "string"}
        mock_create_node.return_value = {"@type": "schema:string"}
        
        result = translator.expand_node("#/components/schemas/StringProperty", "test/ref", "testKey")
        
        assert result == {"@type": "schema:string"}
        mock_get_schema_ref.assert_called_once_with(ref="#/components/schemas/StringProperty", actualref="test/ref")
        mock_create_node.assert_called_once()

    def test_expand_node_empty_ref(self, translator):
        """Test expanding empty reference returns None."""
        result = translator.expand_node("", "test/ref")
        assert result is None
        
        result = translator.expand_node(None, "test/ref")
        assert result is None

    @patch.object(SammSchemaContextTranslator, 'get_schema_ref')
    def test_expand_node_no_schema_found(self, mock_get_schema_ref, translator):
        """Test expanding node when no schema is found returns None."""
        mock_get_schema_ref.return_value = None
        
        result = translator.expand_node("#/components/schemas/MissingProperty", "test/ref")
        assert result is None


class TestCreateMultiplePropertiesContext:
    """Test the create_multiple_properties_context method for allOf processing."""

    @pytest.fixture
    def allof_schema(self):
        """Schema with allOf references for testing."""
        return {
            "components": {
                "schemas": {
                    "PersonalData": {
                        "type": "object",
                        "description": "Personal data schema",
                        "properties": {
                            "firstName": {
                                "type": "string",
                                "description": "First name"
                            },
                            "lastName": {
                                "type": "string",
                                "description": "Last name"
                            }
                        }
                    },
                    "ContactData": {
                        "type": "object",
                        "description": "Contact information schema",
                        "properties": {
                            "email": {
                                "type": "string",
                                "description": "Email address"
                            }
                        }
                    }
                }
            }
        }

    @patch.object(SammSchemaContextTranslator, 'create_item_context')
    def test_create_multiple_properties_context_with_parent_metadata(self, mock_create_item, translator, allof_schema):
        """Test that parent metadata is preserved in allOf processing."""
        translator.baseSchema = allof_schema
        
        # Mock the item context to simulate expanded schemas
        mock_create_item.return_value = {
            "@context": {
                "@version": 1.1,
                "id": "@id", 
                "type": "@type",
                "firstName": {
                    "@id": "aspect:firstName",
                    "@type": "schema:string"
                },
                "email": {
                    "@id": "aspect:email", 
                    "@type": "schema:string"
                }
            }
        }
        
        # allOf combining schemas  
        all_of_items = [
            {"$ref": "#/components/schemas/PersonalData"},
            {"$ref": "#/components/schemas/ContactData"}
        ]
        
        # Parent property with metadata
        parent_property = {
            "type": "object",
            "description": "Complete user profile",
            "x-samm-aspect-model-urn": "urn:samm:example:1.0.0#UserProfile",
            "allOf": all_of_items
        }
        
        result_context = translator.create_multiple_properties_context(
            all_of=all_of_items,
            property=parent_property,
            actualref=""
        )
        
        # Verify base template is preserved
        assert math.isclose(result_context["@version"], 1.1, rel_tol=1e-09, abs_tol=1e-09)
        assert result_context["id"] == "@id"
        assert result_context["type"] == "@type"
        
        # Verify parent metadata is preserved
        assert result_context["@definition"] == "Complete user profile"
        assert result_context["@samm-urn"] == "urn:samm:example:1.0.0#UserProfile"
        
        # Verify properties from allOf are merged
        assert "firstName" in result_context
        assert "email" in result_context

    @patch.object(SammSchemaContextTranslator, 'create_item_context')
    def test_create_multiple_properties_context_without_parent_metadata(self, mock_create_item, translator, allof_schema):
        """Test allOf processing without parent metadata."""
        translator.baseSchema = allof_schema
        
        # Mock simple context
        mock_create_item.return_value = {
            "@context": {
                "@version": 1.1,
                "id": "@id",
                "type": "@type",
                "firstName": {
                    "@id": "aspect:firstName",
                    "@type": "schema:string"
                }
            }
        }
        
        all_of_items = [{"$ref": "#/components/schemas/PersonalData"}]
        
        # Parent property without metadata
        parent_property = {
            "type": "object",
            "allOf": all_of_items
        }
        
        result_context = translator.create_multiple_properties_context(
            all_of=all_of_items,
            property=parent_property,
            actualref=""
        )
        
        # Verify base template is preserved
        assert math.isclose(result_context["@version"], 1.1, rel_tol=1e-09, abs_tol=1e-09)
        assert result_context["id"] == "@id"
        assert result_context["type"] == "@type"
        
        # Verify no metadata is added when not present
        assert "@definition" not in result_context
        assert "@samm-urn" not in result_context
        
        # Verify properties are still merged
        assert "firstName" in result_context

    def test_create_multiple_properties_context_empty_allof(self, translator):
        """Test allOf processing with empty allOf array."""
        all_of_items = []
        parent_property = {"type": "object", "allOf": all_of_items}
        
        result_context = translator.create_multiple_properties_context(
            all_of=all_of_items,
            property=parent_property,
            actualref=""
        )
        
        # Should still return base template
        assert math.isclose(result_context["@version"], 1.1, rel_tol=1e-09, abs_tol=1e-09)
        assert result_context["id"] == "@id"
        assert result_context["type"] == "@type"

    @patch.object(SammSchemaContextTranslator, 'create_item_context')
    def test_create_multiple_properties_context_invalid_refs(self, mock_create_item, translator, allof_schema):
        """Test allOf processing with invalid references."""
        translator.baseSchema = allof_schema
        
        # Mock return None for invalid refs, valid context for valid refs
        def mock_item_context_side_effect(item, actualref):
            if item.get("$ref") == "#/components/schemas/PersonalData":
                return {
                    "@context": {
                        "@version": 1.1,
                        "id": "@id",
                        "type": "@type",
                        "firstName": {
                            "@id": "aspect:firstName",
                            "@type": "schema:string"
                        }
                    }
                }
            return None  # For invalid refs
        
        mock_create_item.side_effect = mock_item_context_side_effect
        
        # Mix of valid and invalid references
        all_of_items = [
            {"$ref": "#/components/schemas/PersonalData"},  # Valid
            {"$ref": "#/components/schemas/NonExistent"},   # Invalid
            {"not_a_ref": "value"},                         # Not a reference
        ]
        
        parent_property = {
            "type": "object",
            "description": "Test with invalid refs",
            "allOf": all_of_items
        }
        
        result_context = translator.create_multiple_properties_context(
            all_of=all_of_items,
            property=parent_property,
            actualref=""
        )
        
        # Should still work and include parent metadata
        assert math.isclose(result_context["@version"], 1.1, rel_tol=1e-09, abs_tol=1e-09)
        assert result_context["@definition"] == "Test with invalid refs"
        
        # Should include properties from valid refs
        assert "firstName" in result_context


class TestCreateObjectNodeWithAllOf:
    """Test create_object_node method with allOf scenarios."""

    @pytest.fixture
    def allof_schema(self):
        """Schema with allOf references for testing."""
        return {
            "components": {
                "schemas": {
                    "Schema1": {
                        "type": "object",
                        "properties": {
                            "prop1": {"type": "string"}
                        }
                    },
                    "Schema2": {
                        "type": "object",
                        "properties": {
                            "prop2": {"type": "integer"}
                        }
                    }
                }
            }
        }

    @patch.object(SammSchemaContextTranslator, 'create_multiple_properties_context')
    def test_create_object_node_with_allof(self, mock_create_multiple, translator, allof_schema):
        """Test create_object_node with allOf property."""
        translator.baseSchema = allof_schema
        
        # Mock the multiple properties context creation
        mock_create_multiple.return_value = {
            "@version": 1.1,
            "id": "@id",
            "type": "@type",
            "@definition": "Combined schema",
            "@samm-urn": "urn:samm:test:1.0.0#Combined",
            "prop1": {"@id": "aspect:prop1"},
            "prop2": {"@id": "aspect:prop2"}
        }
        
        # Property with allOf
        property_def = {
            "type": "object",
            "description": "Combined schema",
            "x-samm-aspect-model-urn": "urn:samm:test:1.0.0#Combined",
            "allOf": [
                {"$ref": "#/components/schemas/Schema1"},
                {"$ref": "#/components/schemas/Schema2"}
            ]
        }
        
        node = {"@id": "test:Combined"}
        
        result = translator.create_object_node(property_def, node, "")
        
        assert result is not None
        assert "@context" in result
        context = result["@context"]
        
        # Verify parent metadata is included
        assert context["@definition"] == "Combined schema"
        assert context["@samm-urn"] == "urn:samm:test:1.0.0#Combined"
        
        # Verify base template
        assert math.isclose(context["@version"], 1.1, rel_tol=1e-09, abs_tol=1e-09)
        assert context["id"] == "@id"
        assert context["type"] == "@type"
        
        # Verify merged properties
        assert "prop1" in context
        assert "prop2" in context

    def test_create_object_node_allof_vs_properties(self, translator):
        """Test that allOf takes precedence over properties when both are present."""
        # This shouldn't happen in valid schemas, but test the behavior
        property_def = {
            "type": "object",
            "properties": {"regularProp": {"type": "string"}},
            "allOf": [{"$ref": "#/$defs/SomeSchema"}]
        }
        
        node = {"@id": "test:Mixed"}
        
        # Should use allOf path (create_multiple_properties_context)
        # and not properties path (create_single_properties_context)
        with patch.object(translator, 'create_multiple_properties_context') as mock_multi:
            with patch.object(translator, 'create_single_properties_context') as mock_single:
                mock_multi.return_value = {"test": "allof"}
                
                result = translator.create_object_node(property_def, node, "")
                
                # Should call create_multiple_properties_context, not create_single_properties_context
                mock_multi.assert_called_once()
                mock_single.assert_not_called()
                assert result["@context"] == {"test": "allof"}


class TestIntegration:
    """Integration tests using complex schemas."""

    def test_complex_schema_integration(self, translator, complex_schema):
        """Test with a complex nested schema (flattened context)."""
        semantic_id = "urn:samm:example:1.0.0#ComplexAspect"
        
        result = translator.schema_to_jsonld(semantic_id, complex_schema)
        
        assert "@context" in result
        context = result["@context"]
        assert "ComplexAspect" in context
        assert context["cx"] == "urn:samm:example:1.0.0#"
        assert "@definition" in context
        assert context["@definition"] == "Complex nested schema"

    def test_error_handling_in_main_method(self, translator):
        """Test error handling in main schema_to_jsonld method."""
        # Test with schema that will cause an error in create_node
        semantic_id = "urn:samm:example:1.0.0#TestAspect"
        invalid_schema = {"invalid": "schema"}  # No "type" field
        
        with pytest.raises(Exception, match="It was not possible to create flattened jsonld schema"):
            translator.schema_to_jsonld(semantic_id, invalid_schema)


