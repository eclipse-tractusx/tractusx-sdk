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

## JSON Schema to JSON-LD @context from Eclipse Tractus-X Digital Product Passport Simple Wallet
## Author: Mathias Brunkow Moser
## License: Apache License, Version 2.0
## Original Source: https://github.com/eclipse-tractusx/digital-product-pass/blob/main/dpp-verification/simple-wallet/passport/sammSchemaParser.py
## Here extended and stabilized to work with any SAMM Schema from sldt-semantic-models for the Data Trust & Security KIT


import hashlib
import logging
from typing import Dict, List, Optional, Tuple, Any
from tractusx_sdk.dataspace.tools import op
from tractusx_sdk.dataspace.tools.validate_submodels import submodel_schema_finder
import copy

class SammSchemaContextTranslator:
    """
    A translator class that converts SAMM (Semantic Aspect Meta Model) schemas 
    to JSON-LD contexts for semantic data processing.
    
    This class provides functionality to transform SAMM aspect models into 
    JSON-LD contexts, supporting both flattened and nested output formats.
    It handles schema references, circular dependencies, and maintains 
    semantic information during the transformation process.
    
    Attributes:
        baseSchema (Dict[str, Any]): The base schema being processed
        rootRef (str): Root reference identifier ("#")
        refKey (str): Key for schema references ("$ref")
        path_sep (str): Path separator for schema references ("#/")
        actualPathSep (str): Actual path separator for tracking references ("/-/")
        refPathSep (str): Reference path separator ("/")
        propertiesKey (str): Key for object properties ("properties")
        logger (Optional[logging.Logger]): Logger instance for debugging
        debug (bool): Enable debug logging with detailed output
        itemKey (str): Key for array items ("items")
        schemaPrefix (str): Prefix for schema URIs ("schema")
        aspectPrefix (str): Prefix for aspect URIs ("aspect")
        allOfKey (str): Key for schema composition ("allOf")
        contextPrefix (str): JSON-LD context key ("@context")
        recursionDepth (int): Maximum recursion depth for circular reference handling
        depth (int): Current recursion depth
        initialJsonLd (Dict[str, Any]): Initial JSON-LD structure template
        contextTemplate (Dict[str, Any]): Template for context objects
    """
    
    def __init__(self, logger: Optional[logging.Logger] = None, debug: bool = False) -> None:
        """
        Initialize the SAMM Schema Context Translator.
        
        Args:
            logger (Optional[logging.Logger]): Logger instance for debugging and error reporting.
                                             If None, no logging will be performed.
            debug (bool): Enable debug logging with detailed output output. Defaults to False.
        
        Returns:
            None
        """
        self.baseSchema = {}
        self.rootRef = "#"
        self.refKey = "$ref"
        self.path_sep = "#/"
        self.actualPathSep = "/-/"
        self.refPathSep = "/"
        self.propertiesKey = "properties"
        self.logger = logger
        self.debug = debug
        self.itemKey = "items"
        self.schemaPrefix = "schema"
        self.aspectPrefix = "aspect"
        self.allOfKey = "allOf"
        self.contextPrefix = "@context"
        self.recursionDepth = 2
        self.depth = 0
        self.initialJsonLd = {
            "@version": 1.1,
            self.schemaPrefix: "https://schema.org/"
        }
        self.contextTemplate = {
            "@version": 1.1,
            "id": "@id",
            "type": "@type"
        }

    def fetch_schema_from_semantic_id(self, semantic_id: str, link_core: str = 'https://raw.githubusercontent.com/eclipse-tractusx/sldt-semantic-models/main/') -> Optional[Dict[str, Any]]:
        """
        Fetch a JSON schema using the semantic ID and the submodel schema finder.
        
        This method retrieves SAMM aspect model schemas from the Eclipse Tractus-X 
        semantic models repository using the provided semantic ID.
        
        Args:
            semantic_id (str): The semantic ID in URN format, 
                             e.g., "urn:samm:io.catenax.pcf:7.0.0#Pcf"
            link_core (str): Base URL for fetching schemas from the repository.
                           Defaults to the Eclipse Tractus-X semantic models repository.
        
        Returns:
            Optional[Dict[str, Any]]: The fetched schema dictionary if successful,
                                    None if the fetch operation failed.
        
        Raises:
            Exception: Logs error but does not raise exceptions. Returns None on failure.
        
        Example:
            >>> translator = SammSchemaContextTranslator()
            >>> schema = translator.fetch_schema_from_semantic_id(
            ...     "urn:samm:io.catenax.pcf:7.0.0#Pcf"
            ... )
            >>> if schema:
            ...     print("Schema fetched successfully")
        """
        try:
            if self.debug and self.logger:
                self.logger.info(f"Fetching schema for semantic ID: {semantic_id}")
            
            # Use the existing submodel_schema_finder from the SDK
            result = submodel_schema_finder(semantic_id, link_core=link_core)
            
            if result['status'] == 'ok':
                schema_dict = result['schema']
                if self.debug and self.logger:
                    self.logger.info(f"Successfully fetched schema: {result['message']}")
                return schema_dict
            else:
                if self.logger:
                    self.logger.error(f"Failed to fetch schema: {result.get('message', 'Unknown error')}")
                return None
                
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error fetching schema for {semantic_id}: {e}")
            return None

    def _prepare_schema_and_context(self, semantic_id: str, aspect_prefix: str, schema: Optional[Dict[str, Any]] = None, link_core: str = 'https://raw.githubusercontent.com/eclipse-tractusx/sldt-semantic-models/main/') -> Tuple[Dict[str, Any], str, Dict[str, Any], Dict[str, Any]]:
        """
        Common preparation logic for both flattened and nested JSON-LD context generation.
        
        This internal method handles the common setup steps required for both
        flattened and nested JSON-LD context generation, including schema fetching,
        validation, and initial context creation.
        
        Args:
            semantic_id (str): The semantic ID of the SAMM model in URN format
            schema (Optional[Dict[str, Any]]): The schema to convert. If None, 
                                              will auto-fetch using semantic_id.
            link_core (str): Base URL for fetching schemas. Defaults to the 
                           Eclipse Tractus-X semantic models repository.
            
        Returns:
            Tuple[Dict[str, Any], str, Dict[str, Any], Dict[str, Any]]: A tuple containing:
                - schema: The processed schema dictionary
                - aspect_name: The extracted aspect name from the semantic ID
                - jsonld_context: The created JSON-LD context node
                - response_context: The initial response context structure
        
        Raises:
            Exception: If the semantic ID is invalid, schema cannot be fetched,
                     or JSON-LD context generation fails.
        
        Note:
            This is an internal method and should not be called directly by users.
            Use schema_to_jsonld() or schema_to_jsonld_nested() instead.
        """
        # If schema is None, try to fetch it using the semantic ID
        if schema is None:
            if self.debug and self.logger:
                self.logger.info(f"Schema not provided, attempting to fetch from semantic ID: {semantic_id}")
            schema = self.fetch_schema_from_semantic_id(semantic_id, link_core=link_core)
            if schema is None:
                raise Exception(f"Could not fetch schema for semantic ID: {semantic_id}")
        
        self.baseSchema = copy.copy(schema)
        semantic_parts = semantic_id.split(self.rootRef)  
        if((len(semantic_parts) < 2) or (semantic_parts[1] == '')):
            raise Exception("Invalid semantic id, missing the model reference!")
        
        aspect_name = semantic_parts[1]
        
        if(aspect_prefix is None):
            aspect_prefix = f"{aspect_name.lower()}-aspect"
            
        self.aspectPrefix = aspect_prefix

        # Create the node context for the schema
        jsonld_context = self.create_node(property=schema)
        
        if jsonld_context is None:
            raise Exception("It was not possible to generated the json-ld!")
        
        # Start with the basic JSON-LD structure
        response_context = copy.copy(self.initialJsonLd)
        
        # Add semantic path reference
        semantic_path = semantic_parts[0]
        response_context[self.aspectPrefix] = semantic_path + self.rootRef
        
        return schema, aspect_name, jsonld_context, response_context

    def schema_to_jsonld(self, semantic_id: str, schema: Optional[Dict[str, Any]] = None, link_core: str = 'https://raw.githubusercontent.com/eclipse-tractusx/sldt-semantic-models/main/', aspect_prefix:str = "cx") -> Dict[str, Any]:
        """
        Convert a SAMM schema to a flattened JSON-LD context suitable for verifiable credentials.
        
        This method creates a flattened context where the semantic model properties are mapped
        directly at the root level of the context, rather than nested under the aspect name.
        This format is particularly suitable for verifiable credentials where the 
        credentialSubject contains the semantic model properties directly without nesting.
        
        Args:
            semantic_id (str): The semantic ID of the SAMM model in URN format,
                             e.g., "urn:samm:io.catenax.pcf:7.0.0#Pcf"
            schema (Optional[Dict[str, Any]]): The schema to convert. If None, 
                                              will auto-fetch using semantic_id.
            link_core (str): Base URL for fetching schemas. Defaults to the 
                           Eclipse Tractus-X semantic models repository.
            
        Returns:
            Dict[str, Any]: Flattened JSON-LD context with the following structure:
                {
                    "@context": {
                        "@version": 1.1,
                        "schema": "https://schema.org/",
                        "aspect-name": {"@id": "aspect:AspectName", "@type": "@id"},
                        "property1": {...},
                        "property2": {...},
                        ...
                    }
                }
        
        Raises:
            Exception: If schema conversion fails with message 
                     "It was not possible to create flattened jsonld schema"
        
        Example:
            >>> translator = SammSchemaContextTranslator()
            >>> context = translator.schema_to_jsonld(
            ...     "urn:samm:io.catenax.pcf:7.0.0#Pcf"
            ... )
            >>> print(context["@context"]["Pcf"])
        """
        try:
            schema, aspect_name, jsonld_context, response_context = self._prepare_schema_and_context(
                semantic_id, aspect_prefix, schema, link_core
            )
            
            # Add the aspect name itself as a property in the flattened context
            response_context[aspect_name] = {
                "@id": f"{self.aspectPrefix}:{aspect_name}",
                "@type": "@id"
            }
            
            # Flatten the properties to root level
            if "@context" in jsonld_context and isinstance(jsonld_context["@context"], dict):
                # Merge the properties from the nested context to the root level
                nested_context = jsonld_context["@context"]
                for key, value in nested_context.items():
                    if key in ["id", "type"] and not isinstance(value, str):
                        response_context[f"{self.aspectPrefix}:{key}"] = value
                        continue
                    response_context[key] = value
            
            # Add description if available
            if "description" in schema:
                response_context["@definition"] = schema["description"]
            
            # Add x-samm-aspect-model-urn if available at the root level
            if "x-samm-aspect-model-urn" in schema:
                response_context["@samm-urn"] = schema["x-samm-aspect-model-urn"]
                
            return {
                "@context": response_context
            }
        except:
            raise Exception("It was not possible to create flattened jsonld schema")

    def schema_to_jsonld_nested(self, semantic_id: str, schema: Optional[Dict[str, Any]] = None, link_core: str = 'https://raw.githubusercontent.com/eclipse-tractusx/sldt-semantic-models/main/',  aspect_prefix:str = "cx") -> Dict[str, Any]:
        """
        Convert a SAMM schema to a nested JSON-LD context.
        
        This method creates a nested context where the semantic model properties are grouped
        under the aspect name in the context structure. This format preserves the 
        hierarchical organization of the aspect model.
        
        Args:
            semantic_id (str): The semantic ID of the SAMM model in URN format,
                             e.g., "urn:samm:io.catenax.pcf:7.0.0#Pcf"
            schema (Optional[Dict[str, Any]]): The schema to convert. If None, 
                                              will auto-fetch using semantic_id.
            link_core (str): Base URL for fetching schemas. Defaults to the 
                           Eclipse Tractus-X semantic models repository.
            
        Returns:
            Dict[str, Any]: Nested JSON-LD context with the following structure:
                {
                    "@context": {
                        "@version": 1.1,
                        "schema": "https://schema.org/",
                        "aspect-name": "urn:aspect:reference",
                        "AspectName": {
                            "@id": "aspect:AspectName",
                            "@context": {
                                "id": "@id",
                                "type": "@type",
                                "property1": {...},
                                "property2": {...},
                                ...
                            }
                        }
                    }
                }
        
        Raises:
            Exception: If schema conversion fails with message 
                     "It was not possible to create jsonld schema"
        
        Example:
            >>> translator = SammSchemaContextTranslator()
            >>> context = translator.schema_to_jsonld_nested(
            ...     "urn:samm:io.catenax.pcf:7.0.0#Pcf"
            ... )
            >>> print(context["@context"]["Pcf"]["@context"])
        """
        try:
            schema, aspect_name, jsonld_context, response_context = self._prepare_schema_and_context(
                semantic_id, aspect_prefix, schema, link_core
            )
            
            # Create nested structure under aspect name
            jsonld_context["@id"] = ":".join([self.aspectPrefix, aspect_name])
            response_context[aspect_name] = jsonld_context
            
            # Add description if available
            if "description" in schema:
                response_context[aspect_name]["@context"]["@definition"] = schema["description"]
            
            # Add x-samm-aspect-model-urn if available at the root level
            if "x-samm-aspect-model-urn" in schema:
                response_context[aspect_name]["@context"]["@samm-urn"] = schema["x-samm-aspect-model-urn"]
                
            return {
                "@context": response_context
            }
        except:
            raise Exception("It was not possible to create jsonld schema")
    

    def expand_node(self, ref: str, actualref: str, key: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Expand a schema reference to create a complete node structure.
        
        This method resolves a schema reference and creates a complete JSON-LD node
        by recursively processing the referenced schema element. It handles circular
        reference detection and maintains a reference path for debugging.
        
        Args:
            ref (str): The schema reference to expand (e.g., "#/components/schemas/MyType")
            actualref (str): The current reference path used for circular reference detection
            key (Optional[str]): The property key associated with this node. Defaults to None.
        
        Returns:
            Optional[Dict[str, Any]]: The expanded node structure as a JSON-LD object,
                                    or None if expansion fails or circular reference detected.
        
        Raises:
            Exception: If node expansion fails with message 
                     "It was not possible to expand the node"
        
        Note:
            This is an internal method used during the schema processing pipeline.
            It maintains recursion depth tracking and reference path management.
        """
        try:
            ## Ref must not be None
            if (ref is None): return None
            ## Get expanded node
            expandedNode = self.get_schema_ref(ref=ref, actualref=actualref)
            ref_hash = hashlib.sha256(ref.encode()).hexdigest()
            newRef = self.actualPathSep.join([actualref, ref_hash])

            if(expandedNode is None): return None
            return self.create_node(property=expandedNode, actualref=newRef, key=key)
        except:
            
            raise Exception("It was not possible to expand the node")

    def create_node(self, property: Dict[str, Any], actualref: str = "", key: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Create a JSON-LD node from a schema property based on its type.
        
        This is the main node creation method that determines the type of JSON-LD node
        to create based on the schema property's type field. It delegates to specific
        creation methods for objects, arrays, and primitive values.
        
        Args:
            property (Dict[str, Any]): The schema property containing type and other metadata
            actualref (str): The current reference path for circular reference tracking.
                           Defaults to empty string.
            key (Optional[str]): The property key for this node. Defaults to None.
        
        Returns:
            Optional[Dict[str, Any]]: The created JSON-LD node structure, or None if:
                - The property is None
                - The property lacks a "type" field
                - Node creation fails for any reason
        
        Raises:
            Exception: If node creation fails with message 
                     "It was not possible to create the node"
        
        Node Types:
            - "object": Creates an object node with properties or allOf composition
            - "array": Creates an array node with @container: "@list"
            - Other types: Creates a value node with schema.org type reference
        
        Example:
            >>> property = {"type": "string", "description": "A name field"}
            >>> node = translator.create_node(property, key="name")
            >>> print(node["@type"])  # "schema:string"
        """
        try:
            ## Schema must be not none and type must be in the schema
            if (property is None) or (not "type" in property): return None
            
            ## Start by creating a simple node
            node = self.create_simple_node(property=property, key=key)

            ## If is not possible to create the simple node it is not possible to create any node
            if(node is None): return None

            propertyType = property["type"]

            if propertyType == "object":
                return self.create_object_node(property=property, node=node, actualref=actualref)
            
            if propertyType == "array":
                return self.create_array_node(property=property, node=node, actualref=actualref)
            
            return self.create_value_node(property=property, node=node)
        except:
            
            raise Exception("It was not possible to create the node")

    def create_value_node(self, property: Dict[str, Any], node: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Create a JSON-LD node for primitive value types.
        
        This method processes schema properties that represent primitive data types
        (string, number, boolean, etc.) and adds the appropriate @type annotation
        referencing schema.org types.
        
        Args:
            property (Dict[str, Any]): The schema property containing type information
            node (Dict[str, Any]): The base node structure to enhance
        
        Returns:
            Optional[Dict[str, Any]]: The enhanced node with @type annotation,
                                    or None if the property lacks a type field.
        
        Raises:
            Exception: If value node creation fails with message 
                     "It was not possible to create value node"
        
        Example:
            >>> property = {"type": "string"}
            >>> base_node = {"@id": "aspect:name"}
            >>> result = translator.create_value_node(property, base_node)
            >>> print(result["@type"])  # "schema:string"
        """
        try:
            ## If type exists add definition to the node
            if not ("type" in property): return None
            
            node["@type"] = self.schemaPrefix+":"+property["type"]
            return node
        except:
            
            raise Exception("It was not possible to create value node")
    
    
    def create_object_node(self, property: Dict[str, Any], node: Dict[str, Any], actualref: str) -> Optional[Dict[str, Any]]:
        """
        Create a JSON-LD node for object type schema properties.
        
        This method processes schema properties of type "object" and creates
        appropriate JSON-LD context structures. It handles both simple objects
        with properties and complex objects using allOf composition.
        
        Args:
            property (Dict[str, Any]): The schema property with type "object"
            node (Dict[str, Any]): The base node structure to enhance
            actualref (str): The current reference path for circular reference tracking
        
        Returns:
            Optional[Dict[str, Any]]: The enhanced node with @context containing
                                    the object's properties, or None if the object
                                    lacks both "properties" and "allOf" keys.
        
        Raises:
            Exception: If object node creation fails with message 
                     "It was not possible to create object node"
        
        Object Types:
            - Simple objects: Have a "properties" key with property definitions
            - Composed objects: Have an "allOf" key with multiple schema references
        
        Example:
            >>> property = {
            ...     "type": "object",
            ...     "properties": {
            ...         "name": {"$ref": "#/components/schemas/Name"}
            ...     }
            ... }
            >>> result = translator.create_object_node(property, base_node, "")
            >>> print("@context" in result)  # True
        """
        try:
            ## If object has not the properties or the allOf key
            if not ((self.propertiesKey in property) or (self.allOfKey in property)): return None
            
            ## If allOf keys is present then it will be required to create a context with multiple properties added
            if(self.allOfKey in property):
                all_of: list = property[self.allOfKey]
                node[self.contextPrefix] = self.create_multiple_properties_context(all_of=all_of, property=property, actualref=actualref)
                return node

            properties: dict = property[self.propertiesKey]

            node[self.contextPrefix] = self.create_single_properties_context(properties=properties, actualref=actualref)
            return node
        except:
            
            raise Exception("It was not possible to create object node")

    def create_array_node(self, property: Dict[str, Any], node: Dict[str, Any], actualref: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Create a JSON-LD node for array type schema properties.
        
        This method processes schema properties of type "array" and creates
        appropriate JSON-LD context structures with @container set to "@list"
        to indicate ordered collections.
        
        Args:
            property (Dict[str, Any]): The schema property with type "array"
            node (Dict[str, Any]): The base node structure to enhance
            actualref (Optional[str]): The current reference path for circular 
                                     reference tracking. Defaults to None.
        
        Returns:
            Optional[Dict[str, Any]]: The enhanced node with @container: "@list"
                                    and appropriate item type information,
                                    or None if the array lacks an "items" key.
        
        Raises:
            Exception: If array node creation fails with message 
                     "It was not possible to create the array node"
        
        Array Item Types:
            - Reference items: Have a "$ref" key pointing to another schema
            - Value items: Have a direct type specification
            - Mixed items: Array of different types (no specific type set)
        
        Example:
            >>> property = {
            ...     "type": "array",
            ...     "items": {"$ref": "#/components/schemas/Item"}
            ... }
            >>> result = translator.create_array_node(property, base_node)
            >>> print(result["@container"])  # "@list"
        """
        try:
            ## If array node has not the item key
            if not (self.itemKey in property): return None
            
            item = property[self.itemKey]
            node["@container"] = "@list" 

            ## If list is with different types of data, dont specify a type
            if(isinstance(item, list)):
                return node

            if not (self.refKey in item):
                return self.create_value_node(property=item, node=node)

            node[self.contextPrefix] = self.create_item_context(item=item, actualref=actualref)
            return node
        except:
            
            raise Exception("It was not possible to create the array node")


    def filter_key(self, key: str) -> str:
        """
        Clean and normalize property keys for use in JSON-LD contexts.
        
        This method removes problematic characters from property keys to ensure
        they are valid for use in JSON-LD contexts. It removes "@" symbols and
        replaces spaces with hyphens.
        
        Args:
            key (str): The original property key that may contain problematic characters
        
        Returns:
            str: The cleaned key with "@" symbols removed and spaces replaced with hyphens
        
        Transformations:
            - "@" characters are removed
            - Spaces are replaced with "-" (hyphens)
        
        Example:
            >>> translator.filter_key("@special key")
            "special-key"
            >>> translator.filter_key("normal_key")
            "normal_key"
        """
        cleanKey = key
        if ("@" in cleanKey): 
            cleanKey = cleanKey.replace("@","")
        
        if (" " in cleanKey): 
            cleanKey = cleanKey.replace(" ","-")
        
        return cleanKey


    def create_multiple_properties_context(self, all_of: List[Dict[str, Any]], property: Dict[str, Any], actualref: str) -> Dict[str, Any]:
        """
        Create a JSON-LD context from multiple schema references using allOf composition.
        
        This method processes the "allOf" schema composition pattern, which allows
        combining multiple schema references into a single object. It merges the
        contexts from all referenced schemas and adds any additional metadata
        from the parent property.
        
        Args:
            all_of (List[Dict[str, Any]]): List of schema references to combine
            property (Dict[str, Any]): The parent property containing the allOf and 
                                     potentially additional metadata
            actualref (str): The current reference path for circular reference tracking
        
        Returns:
            Dict[str, Any]: A merged JSON-LD context containing properties from all
                          referenced schemas plus any additional parent metadata
        
        Raises:
            Exception: If context creation fails with message 
                     "It was not possible to create multiple properties context"
        
        Context Merging:
            - Starts with the base context template (id, type)
            - Iterates through each allOf item and merges their contexts
            - Adds description as "@definition" if present in parent
            - Adds "x-samm-aspect-model-urn" as "@samm-urn" if present in parent
        
        Example:
            >>> all_of = [
            ...     {"$ref": "#/components/schemas/BaseType"},
            ...     {"$ref": "#/components/schemas/Extension"}
            ... ]
            >>> property = {"allOf": all_of, "description": "Combined type"}
            >>> context = translator.create_multiple_properties_context(all_of, property, "")
        """
        try:
            ## Create new context dict from template
            newContext = copy.copy(self.contextTemplate)
            
            for item in all_of:
                item_context = self.create_item_context(item=item, actualref=actualref)
                if item_context is None:
                    continue

                if not "@context" in item_context:
                    continue
                
                # Merge the properties from item_context into newContext
                newContext.update(item_context["@context"])
    
            ## Check if we need to add additional context information from parent
            needs_context_update = ("description" in property) or ("x-samm-aspect-model-urn" in property)
            
            if needs_context_update:
                ## Override the existing description from parent
                if "description" in property:
                    newContext["@definition"] = property["description"]
                
                ## Add x-samm-aspect-model-urn if present in the parent
                if "x-samm-aspect-model-urn" in property:
                    newContext["@samm-urn"] = property["x-samm-aspect-model-urn"]
            
            return newContext
        except:
            
            raise Exception("It was not possible to create multiple properties context")

    def create_single_properties_context(self, properties: Dict[str, Any], actualref: str) -> Optional[Dict[str, Any]]:
        """
        Create a JSON-LD context from a single properties object.
        
        This method processes a schema's "properties" object and creates a JSON-LD
        context by converting each property reference into an appropriate context entry.
        It handles property key filtering and reference resolution.
        
        Args:
            properties (Dict[str, Any]): The properties object from a schema containing
                                       property name to property definition mappings
            actualref (str): The current reference path for circular reference tracking
        
        Returns:
            Optional[Dict[str, Any]]: A JSON-LD context containing all valid properties,
                                    or None if:
                                    - properties is None
                                    - properties is not a dictionary
                                    - properties contains no keys
        
        Raises:
            Exception: If context creation fails with message 
                     "It was not possible to create properties context"
        
        Processing Steps:
            1. Validates the properties parameter
            2. Creates a new context from the template
            3. Iterates through each property
            4. Filters property keys for JSON-LD compatibility
            5. Creates node properties for each valid property
        
        Example:
            >>> properties = {
            ...     "name": {"$ref": "#/components/schemas/Name"},
            ...     "age": {"$ref": "#/components/schemas/Age"}
            ... }
            >>> context = translator.create_single_properties_context(properties, "")
            >>> print("name" in context and "age" in context)  # True
        """
        try:
            ## If no key is provided or node is empty
            if(properties is None): return None
            
            ## If no key is found
            if(not isinstance(properties, dict)): return None
            
            ## If no keys are provided in the properties
            if(len(properties.keys())  == 0): return None
            
            ## Create new context dict from template
            newContext = copy.copy(self.contextTemplate)
            oldProperties = copy.copy(properties)

            ## Fill the node context with the properties
            for propKey, prop in oldProperties.items():
                key:str = self.filter_key(key=propKey)
                prop = self.create_node_property(key=key, node=prop, actualref=actualref)
                if (prop is None):
                    continue

                newContext[key] = prop

            ## Add context properties to the node context
            return newContext
        except:
            
            raise Exception("It was not possible to create properties context")
        
    def create_item_context(self, item: Dict[str, Any], actualref: str) -> Optional[Dict[str, Any]]:
        """
        Create a JSON-LD context for array item types.
        
        This method processes array item definitions that contain schema references
        and creates appropriate JSON-LD contexts for the referenced types. It handles
        additional metadata like descriptions and SAMM URNs.
        
        Args:
            item (Dict[str, Any]): The array item definition containing a "$ref" key
            actualref (str): The current reference path for circular reference tracking
        
        Returns:
            Optional[Dict[str, Any]]: A JSON-LD context for the item type,
                                    or None if:
                                    - item is None
                                    - The reference cannot be resolved
        
        Raises:
            Exception: If context creation fails with message 
                     "It was not possible to create the item context"
        
        Context Enhancement:
            - Expands the reference to get the base context
            - Adds description as "@definition" if present in item
            - Adds "x-samm-aspect-model-urn" as "@samm-urn" if present in item
        
        Example:
            >>> item = {
            ...     "$ref": "#/components/schemas/Product",
            ...     "description": "A product in the catalog"
            ... }
            >>> context = translator.create_item_context(item, "")
            >>> print(context["@context"]["@definition"])  # "A product in the catalog"
        """
        try:
            ## If no key is provided or node is empty
            if(item is None): return None
            
            newContext = copy.copy(self.contextTemplate)
            ref = item[self.refKey]
            nodeItem = self.expand_node(ref=ref, actualref=actualref)

            ## If was not possible to get the reference return None
            if nodeItem is None: return None

            newContext.update(nodeItem)
            
            ## Check if we need to add additional context information
            needs_context_update = ("description" in item) or ("x-samm-aspect-model-urn" in item)
            
            if needs_context_update:
                if not ("@context" in newContext):
                    newContext["@context"] = dict()

                ## Override the existing description of ref item
                if "description" in item:
                    newContext["@context"]["@definition"] = item["description"]
                
                ## Add x-samm-aspect-model-urn if present in the item
                if "x-samm-aspect-model-urn" in item:
                    newContext["@context"]["@samm-urn"] = item["x-samm-aspect-model-urn"]

            return newContext
        except:
            
            raise Exception("It was not possible to create the item context")
        
    def create_node_property(self, key: str, node: Dict[str, Any], actualref: str) -> Optional[Dict[str, Any]]:
        """
        Create a JSON-LD property node from a schema property reference.
        
        This method processes individual property definitions within a schema's
        properties object. It resolves the property's schema reference and creates
        an appropriate JSON-LD node with any additional metadata.
        
        Args:
            key (str): The property name/key
            node (Dict[str, Any]): The property definition containing a "$ref" key
            actualref (str): The current reference path for circular reference tracking
        
        Returns:
            Optional[Dict[str, Any]]: A JSON-LD property node,
                                    or None if:
                                    - key or node is None
                                    - node lacks a "$ref" key
                                    - The reference cannot be resolved
        
        Raises:
            Exception: If property creation fails with message 
                     "It was not possible to create node property"
        
        Property Enhancement:
            - Expands the reference to get the base property structure
            - Adds description as "@definition" if present in the property
            - Adds "x-samm-aspect-model-urn" as "@samm-urn" if present in the property
        
        Example:
            >>> key = "productName"
            >>> node = {
            ...     "$ref": "#/components/schemas/ProductName",
            ...     "description": "The name of the product"
            ... }
            >>> prop = translator.create_node_property(key, node, "")
            >>> print(prop["@context"]["@definition"])  # "The name of the product"
        """
        try:
            ## If no key is provided or node is empty
            if(key is None) or (node is None): return None

            ## Ref property must exist in a property inside properties
            if not (self.refKey in node): return None

            ## Get reference from the base schema
            ref = node[self.refKey]
            nodeProperty = self.expand_node(ref=ref, actualref=actualref, key=key)

            ## If was not possible to get the reference return None
            if nodeProperty is None: return None

            ## Check if we need to add additional context information
            needs_context_update = ("description" in node) or ("x-samm-aspect-model-urn" in node)
            
            if needs_context_update:
                if not ("@context" in nodeProperty):
                    nodeProperty["@context"] = dict()

                ## Override the existing description of ref property
                if "description" in node:
                    nodeProperty["@context"]["@definition"] = node["description"]
                
                ## Add x-samm-aspect-model-urn if present in the property
                if "x-samm-aspect-model-urn" in node:
                    nodeProperty["@context"]["@samm-urn"] = node["x-samm-aspect-model-urn"]

            return nodeProperty
        except:
            
            raise Exception("It was not possible to create node property")


    def create_simple_node(self, property: Dict[str, Any], key: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Create a basic JSON-LD node structure from a schema property.
        
        This method creates the fundamental JSON-LD node structure that serves as
        the foundation for all other node types. It handles the @id assignment
        and adds metadata like descriptions and SAMM URNs to the @context.
        
        Args:
            property (Dict[str, Any]): The schema property containing metadata
            key (Optional[str]): The property key for @id generation. If None,
                               no @id will be set. Defaults to None.
        
        Returns:
            Optional[Dict[str, Any]]: A basic JSON-LD node structure containing:
                - @id: aspect-prefixed identifier (if key provided)
                - @context: metadata container (if description or SAMM URN present)
                or None if property is None
        
        Raises:
            Exception: If node creation fails with message 
                     "It was not possible to create the simple node"
        
        Metadata Handling:
            - description → @context["@definition"]
            - x-samm-aspect-model-urn → @context["@samm-urn"]
        
        Example:
            >>> property = {
            ...     "type": "string",
            ...     "description": "A simple text field",
            ...     "x-samm-aspect-model-urn": "urn:samm:example:1.0.0#TextField"
            ... }
            >>> node = translator.create_simple_node(property, "name")
            >>> print(node["@id"])  # "aspect:name"
            >>> print(node["@context"]["@definition"])  # "A simple text field"
        """
        try:
            ## If no key is provided or node is empty
            if (property is None): return None
            
            ## Create new json ld simple node
            newNode = dict()

            ## If the key is not none create a new node
            if not (key is None):
                newNode["@id"] = self.aspectPrefix+":"+key
            

            ## Check if we need to create a @context section
            needs_context = False
            
            ## If description exists add definition to the node
            if "description" in property:
                needs_context = True
            
            ## If x-samm-aspect-model-urn exists, add it to preserve semantic model information
            if "x-samm-aspect-model-urn" in property:
                needs_context = True
            
            if needs_context:
                if not ("@context" in newNode):
                    newNode["@context"] = dict()
                
                if "description" in property:
                    newNode["@context"]["@definition"] = property["description"]
                
                if "x-samm-aspect-model-urn" in property:
                    newNode["@context"]["@samm-urn"] = property["x-samm-aspect-model-urn"]

            return newNode
        except:
            
            raise Exception("It was not possible to create the simple node")

    def get_schema_ref(self, ref: str, actualref: str) -> Optional[Dict[str, Any]]:
        """
        Resolve a schema reference to retrieve the referenced schema definition.
        
        This method resolves JSON Schema references (like "#/components/schemas/MyType")
        by navigating through the base schema structure. It includes circular reference
        detection to prevent infinite recursion loops.
        
        Args:
            ref (str): The schema reference string to resolve 
                      (e.g., "#/components/schemas/ProductName")
            actualref (str): The accumulated reference path used for circular 
                           reference detection
        
        Returns:
            Optional[Dict[str, Any]]: The resolved schema definition,
                                    or None if:
                                    - ref is not a string
                                    - Circular reference detected
                                    - Reference path not found in schema
                                    - Maximum recursion depth exceeded
        
        Raises:
            Exception: If reference resolution fails with message 
                     "It was not possible to get schema reference"
        
        Circular Reference Handling:
            - Uses SHA-256 hash of reference for detection
            - Tracks recursion depth with configurable limit
            - Logs warnings when infinite recursion detected
        
        Reference Resolution:
            - Removes path separator prefix ("#/")
            - Uses attribute path navigation with "/" separator
            - Returns default value None if path not found
        
        Example:
            >>> ref = "#/components/schemas/ProductName"
            >>> resolved = translator.get_schema_ref(ref, "")
            >>> print(resolved["type"])  # "string" (or whatever the type is)
        """
        try:
            if(not isinstance(ref, str)): return None
            
            # If the actual reference is already found means we are going in a loop
            ref_hash = hashlib.sha256(ref.encode()).hexdigest()
            if not(ref_hash in actualref):     
                path = ref.removeprefix(self.path_sep) 
                return op.get_attribute(self.baseSchema, attr_path=path, path_sep=self.refPathSep, default_value=None)
            
            if(self.depth >= self.recursionDepth):
                if(self.debug and self.logger is not None):
                    self.logger.warning(f"[WARNING] Infinite recursion detected in the following path: ref[{ref}] and acumulated ref[{actualref}]!")
                self.depth=0
                return None
            
            self.depth+=1
            
            path = ref.removeprefix(self.path_sep) 

            return op.get_attribute(self.baseSchema, attr_path=path, path_sep=self.refPathSep, default_value=None)
        except:
            
            raise Exception("It was not possible to get schema reference")