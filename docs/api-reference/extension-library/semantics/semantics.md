<!--

Eclipse Tractus-X - Software Development KIT

Copyright (c) 2026 Mondragon Unibertsitatea
Copyright (c) 2025 LKS Next
Copyright (c) 2025 Contributors to the Eclipse Foundation

See the NOTICE file(s) distributed with this work for additional
information regarding copyright ownership.

This work is made available under the terms of the
Creative Commons Attribution 4.0 International (CC-BY-4.0) license,
which is available at
https://creativecommons.org/licenses/by/4.0/legalcode.

SPDX-License-Identifier: CC-BY-4.0

-->
# SAMM Schema Context Translator

The `SammSchemaContextTranslator` class converts SAMM (Semantic Aspect Meta Model) schemas to JSON-LD contexts for semantic data processing. It enables transformation of aspect models into standardized JSON-LD formats, supporting both flattened and nested output structures.

## Purpose

The SAMM Schema Context Translator enables:

- **Schema to JSON-LD conversion** - Transform SAMM aspect models to JSON-LD contexts
- **Automatic schema fetching** - Retrieve schemas from semantic repositories
- **Circular reference handling** - Detect and manage schema circular dependencies
- **Multiple output formats** - Generate flattened or nested JSON-LD structures
- **Semantic preservation** - Maintain semantic information during transformation

## Class Overview

### Initialization

```python
from tractusx_sdk.extensions.semantics import SammSchemaContextTranslator
import logging

# Basic initialization
translator = SammSchemaContextTranslator()

# With custom logger
logger = logging.getLogger("MyApp")
translator = SammSchemaContextTranslator(
    logger=logger,
    verbose=True
)
```

### Parameters

| Parameter | Type                   | Required | Description                                      |
|-----------|------------------------|----------|--------------------------------------------------|
| `logger`  | `logging.Logger`       | No       | Logger instance for debugging and error reporting|
| `verbose` | `bool`                 | No       | Enable verbose logging output (default: False)   |

### Class Attributes

| Attribute         | Type               | Description                                          |
|-------------------|--------------------|------------------------------------------------------|
| `baseSchema`      | `Dict[str, Any]`   | The base schema being processed                      |
| `recursionDepth`  | `int`              | Maximum recursion depth for circular references (default: 2) |
| `depth`           | `int`              | Current recursion depth                              |
| `logger`          | `logging.Logger`   | Logger instance                                      |
| `verbose`         | `bool`             | Verbose logging flag                                 |

## Core Methods

### fetch_schema_from_semantic_id()

Fetches a JSON schema from the semantic repository using a semantic ID.

```python
# Fetch schema from default repository
schema = translator.fetch_schema_from_semantic_id(
    semantic_id="urn:samm:io.catenax.pcf:7.0.0#Pcf"
)

# Fetch from custom repository
schema = translator.fetch_schema_from_semantic_id(
    semantic_id="urn:samm:io.catenax.pcf:7.0.0#Pcf",
    link_core="https://my-repo.example.com/schemas/"
)

if schema:
    print(f"Schema fetched: {schema['$schema']}")
else:
    print("Schema fetch failed")
```

**Parameters:**

| Parameter     | Type  | Required | Description                                                      |
|---------------|-------|----------|------------------------------------------------------------------|
| `semantic_id` | `str` | Yes      | Semantic ID in URN format (e.g., `urn:samm:...#AspectName`)      |
| `link_core`   | `str` | No       | Base URL for schema repository (default: Eclipse Tractus-X repo) |

**Returns:** `Optional[Dict[str, Any]]` - Schema dictionary or None if fetch fails

**Example Semantic IDs:**
- `urn:samm:io.catenax.pcf:7.0.0#Pcf`
- `urn:samm:io.catenax.part_type_information:1.0.0#PartTypeInformation`
- `urn:samm:io.catenax.serial_part:3.0.0#SerialPart`
- `urn:samm:io.catenax.batch:3.0.0#Batch`

### schema_to_jsonld()

Converts a SAMM schema to a flattened JSON-LD context.

```python
# Auto-fetch and convert to flattened JSON-LD
context = translator.schema_to_jsonld(
    semantic_id="urn:samm:io.catenax.pcf:7.0.0#Pcf",
    aspect_prefix="pcf"
)

print(context["@context"])
# Output:
# {
#   "@version": 1.1,
#   "id": "@id",
#   "type": "@type",
#   "pcf": "<aspect-uri>",
#   "property1": "pcf:property1",
#   "property2": "pcf:property2"
# }
```

**Parameters:**

| Parameter      | Type                  | Required | Description                                              |
|----------------|-----------------------|----------|----------------------------------------------------------|
| `semantic_id`  | `str`                 | Yes      | Semantic ID in URN format                                |
| `schema`       | `Dict[str, Any]`      | No       | Provide schema directly (skips auto-fetch)               |
| `link_core`    | `str`                 | No       | Base URL for schema repository                           |
| `aspect_prefix`| `str`                 | No       | Prefix for aspect properties (default: `"cx"`)           |

**Returns:** `Dict[str, Any]` - JSON-LD context dictionary with flattened structure

**Output Structure:**
```json
{
  "@context": {
    "@version": 1.1,
    "id": "@id",
    "type": "@type",
    "schema": "https://schema.org/",
    "<prefix>": "<aspect-uri>",
    "property1": "<prefix>:property1",
    "property2": {
      "@id": "<prefix>:property2",
      "@type": "<datatype>"
    }
  },
  "@definition": "Aspect description"
}
```

### schema_to_jsonld_nested()

Converts a SAMM schema to a nested JSON-LD context with hierarchical structure.

```python
# Generate nested JSON-LD context
nested_context = translator.schema_to_jsonld_nested(
    semantic_id="urn:samm:io.catenax.part_type_information:1.0.0#PartTypeInformation",
    aspect_prefix="part"
)

# Access nested structure
for aspect_name, aspect_data in nested_context.items():
    print(f"Aspect: {aspect_name}")
    if "@context" in aspect_data:
        print(f"Context keys: {list(aspect_data['@context'].keys())}")
```

**Parameters:**

| Parameter      | Type             | Required | Description                                              |
|----------------|------------------|----------|----------------------------------------------------------|
| `semantic_id`  | `str`            | Yes      | Semantic ID in URN format                                |
| `schema`       | `Dict[str, Any]` | No       | Provide schema directly (skips auto-fetch)               |
| `link_core`    | `str`            | No       | Base URL for schema repository                           |
| `aspect_prefix`| `str`            | No       | Prefix for aspect properties (default: `"cx"`)           |

**Returns:** `Dict[str, Any]` - JSON-LD context dictionary with nested structure

**Output Structure:**
```json
{
  "AspectName": {
    "@context": {
      "@version": 1.1,
      "id": "@id",
      "type": "@type",
      "property1": "<prefix>:property1",
      "complexProperty": {
        "@id": "<prefix>:complexProperty",
        "@context": {
          "nestedProp1": "<prefix>:nestedProp1",
          "nestedProp2": "<prefix>:nestedProp2"
        }
      }
    },
    "@definition": "Aspect description"
  }
}
```

## Complete Usage Examples

### Example 1: Product Carbon Footprint

```python
from tractusx_sdk.extensions.semantics import SammSchemaContextTranslator
import json

# Initialize translator
translator = SammSchemaContextTranslator(verbose=True)

# Generate PCF context
pcf_context = translator.schema_to_jsonld(
    semantic_id="urn:samm:io.catenax.pcf:7.0.0#Pcf",
    aspect_prefix="pcf"
)

# Create PCF data with context
pcf_data = {
    "@context": pcf_context["@context"],
    "id": "urn:uuid:12345",
    "productId": "MPN-TRANSMISSION-001",
    "pcfValue": {
        "value": 123.45,
        "unit": "kgCO2e"
    },
    "declaredUnit": "piece",
    "productMassPerDeclaredUnit": 15.5
}

# Save as JSON-LD
with open("pcf-data.jsonld", "w") as f:
    json.dump(pcf_data, f, indent=2)

print("PCF data with semantic context saved")
```

### Example 2: Part Type Information with Nested Context

```python
# Generate nested context for hierarchical data
part_context = translator.schema_to_jsonld_nested(
    semantic_id="urn:samm:io.catenax.part_type_information:1.0.0#PartTypeInformation",
    aspect_prefix="part"
)

# Create part data with nested structure
part_data = {
    "PartTypeInformation": {
        "@context": part_context["PartTypeInformation"]["@context"],
        "manufacturerPartId": "MPN-12345",
        "nameAtManufacturer": "Transmission Module",
        "classification": "product",
        "partVersion": "1.0"
    }
}

print(json.dumps(part_data, indent=2))
```

### Example 3: Batch Processing Multiple Aspects

```python
import logging

# Configure logging
logger = logging.getLogger("AspectProcessor")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)

# Initialize translator with logger
translator = SammSchemaContextTranslator(logger=logger, verbose=True)

# Define aspects to process
aspects = [
    ("urn:samm:io.catenax.pcf:7.0.0#Pcf", "pcf"),
    ("urn:samm:io.catenax.part_type_information:1.0.0#PartTypeInformation", "part"),
    ("urn:samm:io.catenax.serial_part:3.0.0#SerialPart", "serial"),
    ("urn:samm:io.catenax.batch:3.0.0#Batch", "batch")
]

# Process all aspects
contexts = {}
for semantic_id, prefix in aspects:
    try:
        logger.info(f"Processing {semantic_id}")
        context = translator.schema_to_jsonld(
            semantic_id=semantic_id,
            aspect_prefix=prefix
        )
        contexts[prefix] = context
        logger.info(f"Successfully processed {prefix}")
    except Exception as e:
        logger.error(f"Failed to process {semantic_id}: {e}")

print(f"Processed {len(contexts)} aspect contexts")
```

### Example 4: Custom Schema Repository

```python
# Use custom schema repository
custom_repo = "https://my-company.example.com/semantic-models/"

context = translator.schema_to_jsonld(
    semantic_id="urn:samm:com.example.custom:1.0.0#CustomAspect",
    link_core=custom_repo,
    aspect_prefix="custom"
)

print(f"Fetched from: {custom_repo}")
print(f"Context generated: {list(context['@context'].keys())}")
```

### Example 5: Providing Pre-loaded Schema

```python
import json

# Load schema from file
with open("my-aspect-schema.json", "r") as f:
    my_schema = json.load(f)

# Convert without auto-fetching
context = translator.schema_to_jsonld(
    semantic_id="urn:samm:com.example.myaspect:1.0.0#MyAspect",
    schema=my_schema,  # Provide schema directly
    aspect_prefix="my"
)

print("Context generated from local schema")
```

## Advanced Features

### Circular Reference Detection

The translator automatically detects and handles circular references:

```python
# Adjust recursion depth if needed
translator = SammSchemaContextTranslator()
translator.recursionDepth = 3  # Increase from default 2

# Convert schema with potential circular references
context = translator.schema_to_jsonld(
    semantic_id="urn:samm:io.catenax.complex:1.0.0#ComplexAspect",
    aspect_prefix="complex"
)
```

### Schema Caching Strategy

```python
class CachedTranslator:
    def __init__(self):
        self.translator = SammSchemaContextTranslator()
        self.schema_cache = {}
        self.context_cache = {}
    
    def get_context(self, semantic_id, aspect_prefix="cx"):
        cache_key = f"{semantic_id}:{aspect_prefix}"
        
        if cache_key not in self.context_cache:
            # Fetch schema if not cached
            if semantic_id not in self.schema_cache:
                self.schema_cache[semantic_id] = \
                    self.translator.fetch_schema_from_semantic_id(semantic_id)
            
            # Generate context
            self.context_cache[cache_key] = self.translator.schema_to_jsonld(
                semantic_id=semantic_id,
                schema=self.schema_cache[semantic_id],
                aspect_prefix=aspect_prefix
            )
        
        return self.context_cache[cache_key]

# Use cached translator
cached_translator = CachedTranslator()
context1 = cached_translator.get_context("urn:samm:io.catenax.pcf:7.0.0#Pcf")
context2 = cached_translator.get_context("urn:samm:io.catenax.pcf:7.0.0#Pcf")  # From cache
```

## Error Handling

### Common Errors and Solutions

```python
try:
    context = translator.schema_to_jsonld(
        semantic_id="urn:samm:io.catenax.unknown:1.0.0#Unknown"
    )
except Exception as e:
    error_msg = str(e)
    
    if "Could not fetch schema" in error_msg:
        print("Schema not found in repository")
        print("Solution: Check semantic ID format or repository URL")
    
    elif "Invalid semantic id" in error_msg:
        print("Malformed semantic ID")
        print("Solution: Use format urn:samm:<namespace>:<name>:<version>#<AspectName>")
    
    elif "missing the model reference" in error_msg:
        print("Semantic ID missing aspect name after #")
        print("Solution: Add aspect name after # symbol")
    
    else:
        print(f"Unexpected error: {e}")
```

### Validation

```python
def validate_semantic_id(semantic_id: str) -> bool:
    """Validate semantic ID format before processing."""
    parts = semantic_id.split("#")
    if len(parts) != 2 or not parts[1]:
        return False
    
    urn_parts = parts[0].split(":")
    if len(urn_parts) < 4 or urn_parts[0] != "urn" or urn_parts[1] != "samm":
        return False
    
    return True

# Use validation
semantic_id = "urn:samm:io.catenax.pcf:7.0.0#Pcf"
if validate_semantic_id(semantic_id):
    context = translator.schema_to_jsonld(semantic_id=semantic_id)
else:
    print(f"Invalid semantic ID: {semantic_id}")
```

## Best Practices

1. **Enable verbose mode during development** for better debugging
2. **Cache fetched schemas** to reduce API calls and improve performance
3. **Validate semantic IDs** before processing to catch errors early
4. **Use custom loggers** to integrate with your application's logging system
5. **Handle exceptions gracefully** - schema fetching can fail
6. **Choose appropriate format** - flattened for simple data, nested for hierarchical
7. **Store generated contexts** - reuse them across multiple data instances
8. **Test with sample data** before deploying to production

## Performance Tips

1. **Pre-fetch commonly used schemas** at application startup
2. **Implement context caching** to avoid repeated transformations
3. **Use batch processing** for multiple aspects
4. **Adjust recursion depth** based on schema complexity
5. **Consider memory usage** when caching many large schemas

## Integration with Other SDK Components

### With DTR Service

```python
from tractusx_sdk.extensions.semantics import SammSchemaContextTranslator
from tractusx_sdk.industry.services import AasService
from tractusx_sdk.dataspace.managers import OAuth2Manager

# Initialize services
auth_manager = OAuth2Manager(
    token_url="https://auth.example.com/token",
    client_id="client-id",
    client_secret="secret"
)

aas_service = AasService(
    base_url="https://dtr.example.com",
    base_lookup_url="https://dtr-lookup.example.com",
    api_path="/api/v3.0",
    auth_service=auth_manager
)

translator = SammSchemaContextTranslator()

# Get shell from DTR
shell = aas_service.get_asset_administration_shell_descriptor_by_id(
    aas_identifier="urn:uuid:12345"
)

# Generate contexts for all submodels
for submodel in shell.submodel_descriptors:
    semantic_id = submodel.semantic_id["keys"][0]["value"]
    context = translator.schema_to_jsonld(semantic_id=semantic_id)
    print(f"Generated context for {submodel.id_short}")
```

## Further Reading

- [Extension Library Overview](../index.md) - Main extension library documentation
- [Extension Concepts](../../../core-concepts/extensions-concepts/index.md) - Conceptual overview
- [SAMM Specification](https://eclipse-esmf.github.io/samm-specification/2.1.0/index.html) - Official SAMM documentation
- [JSON-LD 1.1](https://www.w3.org/TR/json-ld11/) - JSON-LD specification
- [Tractus-X Semantic Models](https://github.com/eclipse-tractusx/sldt-semantic-models) - Official semantic model repository
- [Schema Source Code](https://github.com/eclipse-tractusx/tractusx-sdk/blob/main/src/tractusx_sdk/extensions/semantics/schema_to_context_translator.py)

## NOTICE

This work is licensed under the [CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/legalcode).

- SPDX-License-Identifier: CC-BY-4.0
- SPDX-FileCopyrightText: 2025 Contributors to the Eclipse Foundation
- Source URL: https://github.com/eclipse-tractusx/tractusx-sdk
