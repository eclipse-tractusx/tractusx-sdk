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
# Extension Library API Reference

The Extension Library provides extensible components and utilities for enhancing the core Tractus-X SDK functionality. This reference documentation covers semantic processing tools, schema transformations, and custom use-case implementations available in the Extension Library.

## Overview

The Extension Library enables:

- **Semantic Data Processing** - Transform SAMM schemas to JSON-LD contexts for linked data
- **Schema Transformations** - Convert aspect models between formats
- **Use-Case Extensions** - Domain-specific implementations (PCF, certificates, etc.)
- **JSON-LD Context Generation** - Create standardized contexts for semantic interoperability

## API Components

### Semantic Extensions

Tools for processing SAMM (Semantic Aspect Meta Model) schemas and generating JSON-LD contexts.

#### SAMM Schema Context Translator
- **[Semantics API](semantics/semantics.md)** - Complete API reference
  - Schema to JSON-LD conversion (flattened and nested)
  - Automatic schema fetching from semantic repositories
  - Circular reference handling
  - Schema validation and transformation
  - Custom prefix support

## Quick Start Examples

### Converting SAMM Schema to JSON-LD

```python
from tractusx_sdk.extensions.semantics import SammSchemaContextTranslator

# Initialize translator
translator = SammSchemaContextTranslator(verbose=True)

# Convert SAMM schema to flattened JSON-LD context
context = translator.schema_to_jsonld(
    semantic_id="urn:samm:io.catenax.pcf:7.0.0#Pcf",
    aspect_prefix="cx"
)

# Use the generated context
print(context["@context"])
```

### Using Nested JSON-LD Format

```python
# Generate nested JSON-LD context with hierarchical structure
nested_context = translator.schema_to_jsonld_nested(
    semantic_id="urn:samm:io.catenax.part_type_information:1.0.0#PartTypeInformation",
    aspect_prefix="cx"
)

# Access nested properties
for key, value in nested_context.items():
    if isinstance(value, dict) and "@context" in value:
        print(f"Aspect: {key}")
        print(f"Context: {value['@context']}")
```

### Providing Custom Schema

```python
import json

# Load schema from local file
with open("my-aspect-schema.json", "r") as f:
    custom_schema = json.load(f)

# Convert custom schema
context = translator.schema_to_jsonld(
    semantic_id="urn:samm:com.example.myaspect:1.0.0#MyAspect",
    schema=custom_schema,
    aspect_prefix="example"
)
```

## Documentation Structure

```text
extension-library/
├── index.md                    # This file - API overview
└── semantics/
    └── semantics.md           # SAMM Schema Context Translator API
```

## Use Cases

The Extension Library supports various domain-specific use cases:

### Product Carbon Footprint (PCF)

```python
# Convert PCF aspect model to JSON-LD
pcf_context = translator.schema_to_jsonld(
    semantic_id="urn:samm:io.catenax.pcf:7.0.0#Pcf",
    aspect_prefix="pcf"
)

# Use context for PCF data validation and processing
pcf_data = {
    "@context": pcf_context["@context"],
    "productId": "MPN-12345",
    "carbonFootprint": {
        "value": 123.45,
        "unit": "kgCO2e"
    }
}
```

### Part Type Information

```python
# Convert Part Type Information aspect
part_context = translator.schema_to_jsonld(
    semantic_id="urn:samm:io.catenax.part_type_information:1.0.0#PartTypeInformation",
    aspect_prefix="part"
)
```

### Serial Part Typization

```python
# Convert Serial Part aspect with nested structure
serial_context = translator.schema_to_jsonld_nested(
    semantic_id="urn:samm:io.catenax.serial_part:3.0.0#SerialPart",
    aspect_prefix="serial"
)
```

## Integration Patterns

### Complete Semantic Processing Workflow

```python
from tractusx_sdk.extensions.semantics import SammSchemaContextTranslator
from tractusx_sdk.industry.services import AasService
from tractusx_sdk.dataspace.managers import OAuth2Manager
import json

# 1. Initialize services
auth_manager = OAuth2Manager(
    token_url="https://auth.example.com/token",
    client_id="your-client-id",
    client_secret="your-client-secret"
)

aas_service = AasService(
    base_url="https://dtr.example.com",
    base_lookup_url="https://dtr-lookup.example.com",
    api_path="/api/v3.0",
    auth_service=auth_manager
)

translator = SammSchemaContextTranslator(verbose=True)

# 2. Get submodel semantic ID from DTR
shell = aas_service.get_asset_administration_shell_descriptor_by_id(
    aas_identifier="urn:uuid:12345"
)

for submodel in shell.submodel_descriptors:
    # Extract semantic ID
    semantic_id = submodel.semantic_id["keys"][0]["value"]
    
    # 3. Generate JSON-LD context for this aspect
    context = translator.schema_to_jsonld(
        semantic_id=semantic_id,
        aspect_prefix="cx"
    )
    
    # 4. Fetch submodel data and add context
    # (Assuming data fetched from endpoint)
    submodel_data = {
        "@context": context["@context"],
        # ... actual submodel data
    }
    
    # 5. Validate and process with semantic context
    print(f"Processed {submodel.id_short} with context")
```

## API Conventions

### Semantic IDs

All semantic IDs must follow the URN format:

```
urn:samm:<namespace>:<aspect-name>:<version>#<AspectName>
```

Example:
```
urn:samm:io.catenax.pcf:7.0.0#Pcf
```

### Context Prefixes

Custom prefixes can be specified for aspect properties:

```python
context = translator.schema_to_jsonld(
    semantic_id="urn:samm:io.catenax.pcf:7.0.0#Pcf",
    aspect_prefix="custom"  # Use 'custom' instead of default 'cx'
)
```

### Schema Sources

Schemas can be provided in three ways:

1. **Auto-fetch from repository** (default):
   ```python
   context = translator.schema_to_jsonld(semantic_id="urn:samm:...")
   ```

2. **Custom repository URL**:
   ```python
   context = translator.schema_to_jsonld(
       semantic_id="urn:samm:...",
       link_core="https://my-repo.example.com/schemas/"
   )
   ```

3. **Explicit schema dictionary**:
   ```python
   context = translator.schema_to_jsonld(
       semantic_id="urn:samm:...",
       schema=my_schema_dict
   )
   ```

## Output Formats

### Flattened JSON-LD

Use `schema_to_jsonld()` for flat context structure:

```json
{
  "@context": {
    "@version": 1.1,
    "id": "@id",
    "type": "@type",
    "cx": "aspect-specific-uri",
    "property1": "cx:property1",
    "property2": "cx:property2"
  },
  "@definition": "Aspect description"
}
```

### Nested JSON-LD

Use `schema_to_jsonld_nested()` for hierarchical structure:

```json
{
  "AspectName": {
    "@context": {
      "@version": 1.1,
      "id": "@id",
      "type": "@type",
      "property1": {
        "@context": {
          "nestedProp1": "...",
          "nestedProp2": "..."
        }
      }
    }
  }
}
```

## Error Handling

```python
try:
    context = translator.schema_to_jsonld(
        semantic_id="urn:samm:invalid:id"
    )
except Exception as e:
    if "Could not fetch schema" in str(e):
        print("Schema not found in repository")
    elif "Invalid semantic id" in str(e):
        print("Malformed semantic ID format")
    else:
        print(f"Error: {e}")
```

## Best Practices

1. **Enable verbose logging** for debugging schema transformations
2. **Cache generated contexts** to avoid repeated API calls
3. **Validate semantic IDs** before calling translation methods
4. **Use nested format** for complex hierarchical data structures
5. **Specify custom prefixes** to avoid naming conflicts
6. **Handle circular references** - translator automatically limits recursion depth
7. **Validate output** against JSON-LD specifications

## Performance Considerations

### Schema Caching

```python
# Cache schemas for repeated use
schema_cache = {}

def get_or_fetch_schema(semantic_id):
    if semantic_id not in schema_cache:
        schema_cache[semantic_id] = translator.fetch_schema_from_semantic_id(semantic_id)
    return schema_cache[semantic_id]

# Use cached schema
context = translator.schema_to_jsonld(
    semantic_id=semantic_id,
    schema=get_or_fetch_schema(semantic_id)
)
```

### Batch Processing

```python
# Process multiple aspects efficiently
semantic_ids = [
    "urn:samm:io.catenax.pcf:7.0.0#Pcf",
    "urn:samm:io.catenax.part_type_information:1.0.0#PartTypeInformation",
    "urn:samm:io.catenax.serial_part:3.0.0#SerialPart"
]

contexts = {}
for semantic_id in semantic_ids:
    try:
        contexts[semantic_id] = translator.schema_to_jsonld(
            semantic_id=semantic_id,
            aspect_prefix="cx"
        )
    except Exception as e:
        print(f"Failed to process {semantic_id}: {e}")
```

## Advanced Features

### Circular Reference Handling

The translator automatically detects and handles circular references in schemas:

```python
# Translator has built-in recursion depth limit
translator = SammSchemaContextTranslator()
translator.recursionDepth = 3  # Adjust if needed (default: 2)

context = translator.schema_to_jsonld(semantic_id="urn:samm:...")
```

### Custom Logging

```python
import logging

# Configure custom logger
logger = logging.getLogger("SammTranslator")
logger.setLevel(logging.DEBUG)

translator = SammSchemaContextTranslator(
    logger=logger,
    verbose=True
)

context = translator.schema_to_jsonld(semantic_id="urn:samm:...")
```

## Further Reading

- [Semantics API Reference](semantics/semantics.md) - Detailed method documentation
- [Extension Concepts](../../core-concepts/extensions-concepts/index.md) - Conceptual overview
- [SDK Architecture](../../core-concepts/sdk-architecture/sdk-structure-and-components.md) - Technical architecture
- [SAMM Specification](https://eclipse-esmf.github.io/samm-specification/2.1.0/index.html) - SAMM aspect model standard
- [JSON-LD Specification](https://www.w3.org/TR/json-ld11/) - JSON-LD standard

## NOTICE

This work is licensed under the [CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/legalcode).

- SPDX-License-Identifier: CC-BY-4.0
- SPDX-FileCopyrightText: 2025 Contributors to the Eclipse Foundation
- Source URL: https://github.com/eclipse-tractusx/tractusx-sdk
