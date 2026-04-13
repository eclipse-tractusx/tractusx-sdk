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

"""
Example usage of SammSchemaContextTranslator.

This example demonstrates how to use the SammSchemaContextTranslator to automatically
fetch a SAMM (Semantic Aspect Meta Model) schema from the Tractus-X repository and
convert it to a JSON-LD context object.

The example shows:
- Automatic schema fetching using semantic IDs
- Converting SAMM schemas to JSON-LD contexts
- Creating verifiable credentials with the generated contexts
- Working with real Tractus-X semantic models from the repository
"""

import json
import logging
from tractusx_sdk.extensions.semantics import SammSchemaContextTranslator


def main():
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    # Create translator instance
    translator = SammSchemaContextTranslator(logger=logger, debug=True)
    
    # Use a SerialPart semantic ID - the translator will automatically fetch the schema
    semantic_id = "urn:samm:io.catenax.pcf:7.0.0#Pcf"
    
    try:
        # The translator automatically fetches the schema and converts it to JSON-LD
        result = translator.schema_to_jsonld(semantic_id)
        output_file = "context_result.json"
        with open(output_file, 'w') as f:
            json.dump(result, f, indent=2)

    except Exception as e:
        print(f"Error: {e}"
        + f" Make sure the semantic ID is valid and the schema is available"
        + f"   Try other Tractus-X semantic IDs like:"
        + f"   - urn:samm:io.catenax.pcf:7.0.0#Pcf"
        + f"   - urn:samm:io.catenax.battery.battery_pass:6.0.0#BatteryPass")


if __name__ == "__main__":
    main()
