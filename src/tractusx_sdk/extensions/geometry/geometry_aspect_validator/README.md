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

```bash
python validateGeometry.py <root_node> [-d DIR] [-v LEVEL] [-s FILE]
```

**How it works:**
1. Loads the official Catena-X schema from GitHub (or from a local file if specified)
2. Loads the root node file
3. Validates the file against the JSON schema
4. Performs custom geometry validation checks
5. If a directory is provided, builds a map of all `catenaXId` -> file mappings
6. When validating, if a node has `childItems` with `catenaXId` references, it automatically validates those referenced files
7. Avoids circular references by tracking already validated files

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

Runnable examples with sample SingleLevelSceneNode JSON files are available in the [Tractus-X SDK repository](https://github.com/eclipse-tractusx/tractusx-sdk/tree/main/examples/extensions/geometry).

```bash
# Validate a single file
python validateGeometry.py scene.json

# Validate with child reference resolution and full output
python validateGeometry.py scene.json -d ./data/ -v info
```

## Licenses

- [Apache-2.0](https://raw.githubusercontent.com/eclipse-tractusx/tractusx-sdk/main/LICENSE) for code
- [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html) for non-code

## NOTICE

This work is licensed under the [CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/legalcode).

- SPDX-License-Identifier: CC-BY-4.0
- SPDX-FileCopyrightText: 2025 Threedy GmbH
- Source URL: https://github.com/eclipse-tractusx/tractusx-sdk
