<!--

Eclipse Tractus-X - Software Development KIT

Copyright (c) 2025 Threedy GmbH

See the NOTICE file(s) distributed with this work for additional
information regarding copyright ownership.

This work is made available under the terms of the
Creative Commons Attribution 4.0 International (CC-BY-4.0) license,
which is available at
https://creativecommons.org/licenses/by/4.0/legalcode.

SPDX-License-Identifier: CC-BY-4.0

-->

# Geometry Validation

This tool validates geometry scene files in JSON format against the Catena-X SingleLevelSceneNode schema. The validator checks your JSON files against the official [Catena-X SingleLevelSceneNode schema version 1.0.0](https://github.com/eclipse-tractusx/sldt-semantic-models/blob/main/io.catenax.single_level_scene_node/1.0.0/gen/SingleLevelSceneNode-schema.json).

## Prerequisites

- Python 3.x
- Required Python packages:
  ```bash
  pip install -r requirements.txt
  ```

## Usage

Validate SingleLevelSceneNode files against the official Catena-X schema with automatic resolution of referenced files:

```bash
# Simple validation of a single file (loads schema from GitHub)
python validateGeometry.py exampleData/scene.json

# With directory - builds catenaXId map and validates referenced files
python validateGeometry.py exampleData/scene.json -d ./exampleData

# With local schema file
python validateGeometry.py exampleData/scene.json -s path/to/schema.json
```

**How it works:**
1. Loads the official Catena-X schema from GitHub (or from a local file if specified)
2. Loads the root node file
3. Validates the file against the JSON schema
4. Performs custom geometry validation checks
5. If a directory is provided, builds a map of all `catenaXId` -> file mappings
6. When validating, if a node has `childItems` with `catenaXId` references, it automatically validates those referenced files
7. Avoids circular references by tracking already validated files

### With Validation Level

You can adjust the validation log level to control the verbosity of the output:

```bash
python validateGeometry.py exampleData/scene.json -v warning
```

Available validation log levels:
- `error` - Show only errors
- `warning` - Show errors and warnings
- `info` - Show all information (detailed)

### Complete Example with Directory

This validates the root node and automatically follows all `catenaXId` references:

```bash
python validateGeometry.py exampleData/scene.json -d ./exampleData -v info
```

## Parameters

- `root_node` - Path to the scene file to validate (required)
- `-v`, `--validation-level` - Sets the validation level (optional, default: error)
  - `error` - Show only errors
  - `warning` - Show errors and warnings
  - `info` - Show all information (detailed)
- `-d`, `--directory` - Additional directory for more scene files (optional)
- `-s`, `--schema` - Path to local schema file (optional, loads from GitHub if not provided)

Use `-h` or `--help` to see all available options:
```bash
python validateGeometry.py --help
```

## Examples

```bash
# Basic validation with schema from GitHub
python validateGeometry.py exampleData/scene.json

# Detailed validation with info level
python validateGeometry.py exampleData/scene.json -v info

# Validation with additional directory and reference resolution
python validateGeometry.py exampleData/scene.json -d ./exampleData

# With local schema file
python validateGeometry.py exampleData/scene.json -s ./SingleLevelSceneNode-schema.json

# Combination of all options
python validateGeometry.py exampleData/scene.json -d ./exampleData -v warning -s ./schema.json

# Show help
python validateGeometry.py --help
```

## Licenses

- [Apache-2.0](https://raw.githubusercontent.com/eclipse-tractusx/tractusx-sdk/main/LICENSE) for code
- [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html) for non-code

## NOTICE

This work is licensed under the [CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/legalcode).

- SPDX-License-Identifier: CC-BY-4.0
- SPDX-FileCopyrightText: 2025 Threedy GmbH
- Source URL: https://github.com/eclipse-tractusx/tractusx-sdk
