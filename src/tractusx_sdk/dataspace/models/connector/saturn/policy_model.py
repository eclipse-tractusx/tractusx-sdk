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

from json import dumps as jdumps
from typing import ClassVar
from pydantic import Field

from ..base_policy_model import BasePolicyModel


class PolicyModel(BasePolicyModel):
    TYPE: str = Field(default="PolicyDefinition", frozen=True)
    POLICY_TYPE: str = Field(default="Set", frozen=True)
    
    # Default ODRL contexts for Saturn/Tractus-X EDC compatibility
    # ClassVar indicates this is a class constant, not a Pydantic model field
    DEFAULT_ODRL_CONTEXTS: ClassVar[list[str]] = [
        "https://w3id.org/catenax/2025/9/policy/odrl.jsonld",
        "https://w3id.org/catenax/2025/9/policy/context.jsonld",
        {
            "@vocab": "https://w3id.org/edc/v0.0.1/ns/"
        }
    ]

    def to_data(self):
        """
        Converts the model to a JSON representing the data that
        will be sent to the connector when using a policy model.
        
        Saturn connector follows Tractus-X EDC v0.7.0+ specification where:
        - ODRL context must be at the top level @context, not nested
        - Policy @type is "Set" (not "odrl:Set") when ODRL context is imported
        - Context can be passed as configuration or uses defaults

        :return: a JSON representation of the model
        """
        # Build the context according to Tractus-X EDC specification
        context = self._build_context()

        data = {
            "@context": context,
            "@type": self.TYPE,
            "@id": self.oid,
            "policy": {
                "@type": self.POLICY_TYPE,
                "permission": self._normalize_constraints(self.permissions),
                "prohibition": self._normalize_constraints(self.prohibitions),
                "obligation": self._normalize_constraints(self.obligations)
            }
        }

        # DEBUG: Print what we're about to send
        import json
        print("\n" + "="*80)
        print("DEBUG: PolicyModel.to_data() - Data structure BEFORE jdumps:")
        print("="*80)
        print(json.dumps(data, indent=2))
        print("="*80 + "\n")

        result = jdumps(data)
        
        # DEBUG: Print the final JSON string
        print("\n" + "="*80)
        print("DEBUG: PolicyModel.to_data() - Final JSON string:")
        print("="*80)
        print(result)
        print("="*80 + "\n")
        
        return result
    
    def _normalize_constraints(self, items):
        """
        Recursively normalize constraint values to ensure proper JSON-LD serialization.
        
        When rightOperand is a list, each item should remain as a simple value (string/number),
        not wrapped in objects. The EDC will handle the proper ODRL formatting.
        
        :param items: permissions, prohibitions, or obligations list
        :return: normalized items
        """
        # DEBUG: Print input
        import json
        print(f"\nDEBUG _normalize_constraints - INPUT type: {type(items)}")
        print(f"DEBUG _normalize_constraints - INPUT value: {json.dumps(items, indent=2, default=str)}")
        
        if not items:
            return items
        
        if isinstance(items, dict):
            items = [items]
        
        normalized = []
        for item in items:
            if isinstance(item, dict):
                normalized_item = {}
                for key, value in item.items():
                    if key == "constraint" and isinstance(value, dict):
                        normalized_item[key] = self._normalize_constraint_dict(value)
                    else:
                        normalized_item[key] = value
                normalized.append(normalized_item)
            else:
                normalized.append(item)
        
        # DEBUG: Print output
        print(f"DEBUG _normalize_constraints - OUTPUT: {json.dumps(normalized, indent=2, default=str)}\n")
        
        return normalized
    
    def _normalize_constraint_dict(self, constraint):
        """
        Normalize a constraint dictionary, handling 'and'/'or' operators and rightOperand arrays.
        
        :param constraint: constraint dictionary
        :return: normalized constraint
        """
        import json
        print(f"\nDEBUG _normalize_constraint_dict - INPUT: {json.dumps(constraint, indent=2, default=str)}")
        
        result = {}
        for key, value in constraint.items():
            if key in ("and", "or") and isinstance(value, list):
                # Recursively normalize nested constraints
                result[key] = [self._normalize_constraint_dict(c) if isinstance(c, dict) else c for c in value]
            elif key == "rightOperand":
                # DEBUG: Check rightOperand type
                print(f"DEBUG _normalize_constraint_dict - rightOperand type: {type(value)}")
                print(f"DEBUG _normalize_constraint_dict - rightOperand value: {value}")
                print(f"DEBUG _normalize_constraint_dict - rightOperand repr: {repr(value)}")
                result[key] = value
            else:
                result[key] = value
        
        print(f"DEBUG _normalize_constraint_dict - OUTPUT: {json.dumps(result, indent=2, default=str)}\n")
        return result
    
    def _build_context(self):
        """
        Builds the @context for the policy according to Tractus-X EDC specification.
        
        The context structure should be:
        [
            "https://w3id.org/catenax/2025/9/policy/odrl.jsonld",
            "https://w3id.org/catenax/2025/9/policy/context.jsonld",
            {
                "@vocab": "https://w3id.org/edc/v0.0.1/ns/"
            }
        ]
        
        Users can:
        1. Pass a complete list with ODRL contexts already included (we preserve order)
        2. Pass a dict/string and we prepend ODRL contexts automatically
        3. Pass nothing and get the full default
        
        :return: The properly structured context
        """
        context = self.context
        
        # Case 1: User provided a list
        if isinstance(context, list):
            result_context = []
            
            # First, add ODRL contexts that are missing at the beginning
            for odrl_ctx in self.DEFAULT_ODRL_CONTEXTS:
                if odrl_ctx not in context:
                    result_context.append(odrl_ctx)
            
            # Then add all user-provided context items
            # This preserves user's explicit ordering while ensuring ODRL contexts are present
            result_context.extend(context)
            return result_context
        
        # Case 2: User provided a dict or string - prepend ODRL contexts
        elif isinstance(context, (dict, str)):
            return [
                *self.DEFAULT_ODRL_CONTEXTS,
                context
            ]
        
        # Case 3: No context provided - use complete defaults
        else:
            return [
                *self.DEFAULT_ODRL_CONTEXTS,
            ]
