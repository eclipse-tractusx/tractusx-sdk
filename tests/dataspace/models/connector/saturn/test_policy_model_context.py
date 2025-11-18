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

import unittest
import json

from tractusx_sdk.dataspace.models.connector.saturn.policy_model import PolicyModel


class TestSaturnPolicyModelContext(unittest.TestCase):
    """Test Saturn PolicyModel context building according to Tractus-X EDC specification"""

    def test_default_context_when_none_provided(self):
        """Test that default ODRL contexts are added when no context is provided"""
        policy = PolicyModel.builder() \
            .id("test-policy") \
            .permissions([{"action": "use"}]) \
            .build()
        
        data = json.loads(policy.to_data())
        context = data["@context"]
        
        # Should be a list with ODRL contexts + default @vocab
        self.assertIsInstance(context, list)
        self.assertEqual(len(context), 3)
        self.assertEqual(context[0], "https://w3id.org/catenax/2025/9/policy/odrl.jsonld")
        self.assertEqual(context[1], "https://w3id.org/catenax/2025/9/policy/context.jsonld")
        self.assertIsInstance(context[2], dict)
        self.assertEqual(context[2]["@vocab"], "https://w3id.org/edc/v0.0.1/ns/")

    def test_context_with_dict_prepends_odrl(self):
        """Test that passing a dict context prepends ODRL contexts"""
        custom_context = {
            "@vocab": "https://w3id.org/edc/v0.0.1/ns/",
            "custom": "https://example.com/custom"
        }
        
        policy = PolicyModel.builder() \
            .id("test-policy") \
            .context(custom_context) \
            .permissions([{"action": "use"}]) \
            .build()
        
        data = json.loads(policy.to_data())
        context = data["@context"]
        
        # Should prepend ODRL contexts before user's dict
        self.assertIsInstance(context, list)
        self.assertEqual(len(context), 3)
        self.assertEqual(context[0], "https://w3id.org/catenax/2025/9/policy/odrl.jsonld")
        self.assertEqual(context[1], "https://w3id.org/catenax/2025/9/policy/context.jsonld")
        self.assertEqual(context[2], custom_context)

    def test_context_with_list_preserves_odrl_if_present(self):
        """Test that if user provides a list with ODRL contexts, they are not duplicated"""
        custom_context = [
            "https://w3id.org/catenax/2025/9/policy/odrl.jsonld",
            "https://w3id.org/catenax/2025/9/policy/context.jsonld",
            {
                "@vocab": "https://w3id.org/edc/v0.0.1/ns/",
                "custom": "https://example.com/custom"
            }
        ]
        
        policy = PolicyModel.builder() \
            .id("test-policy") \
            .context(custom_context) \
            .permissions([{"action": "use"}]) \
            .build()
        
        data = json.loads(policy.to_data())
        context = data["@context"]
        
        # Should not duplicate ODRL contexts
        self.assertIsInstance(context, list)
        self.assertEqual(len(context), 3)
        self.assertEqual(context[0], "https://w3id.org/catenax/2025/9/policy/odrl.jsonld")
        self.assertEqual(context[1], "https://w3id.org/catenax/2025/9/policy/context.jsonld")
        self.assertIsInstance(context[2], dict)
        self.assertIn("custom", context[2])

    def test_context_with_list_adds_missing_odrl(self):
        """Test that if user provides a list without ODRL contexts, they are prepended"""
        custom_context = [
            {
                "@vocab": "https://w3id.org/edc/v0.0.1/ns/",
                "custom": "https://example.com/custom"
            }
        ]
        
        policy = PolicyModel.builder() \
            .id("test-policy") \
            .context(custom_context) \
            .permissions([{"action": "use"}]) \
            .build()
        
        data = json.loads(policy.to_data())
        context = data["@context"]
        
        # Should prepend ODRL contexts
        self.assertIsInstance(context, list)
        self.assertEqual(len(context), 3)
        self.assertEqual(context[0], "https://w3id.org/catenax/2025/9/policy/odrl.jsonld")
        self.assertEqual(context[1], "https://w3id.org/catenax/2025/9/policy/context.jsonld")
        self.assertIsInstance(context[2], dict)

    def test_context_with_partial_odrl_adds_missing_ones(self):
        """Test that if only one ODRL context is present, the other is added"""
        custom_context = [
            "https://w3id.org/catenax/2025/9/policy/odrl.jsonld",
            # Missing the context.jsonld
            {
                "@vocab": "https://w3id.org/edc/v0.0.1/ns/"
            }
        ]
        
        policy = PolicyModel.builder() \
            .id("test-policy") \
            .context(custom_context) \
            .permissions([{"action": "use"}]) \
            .build()
        
        data = json.loads(policy.to_data())
        context = data["@context"]
        
        # Should add the missing ODRL context at the beginning
        self.assertIsInstance(context, list)
        self.assertEqual(len(context), 3)
        self.assertEqual(context[0], "https://w3id.org/catenax/2025/9/policy/context.jsonld")
        self.assertEqual(context[1], "https://w3id.org/catenax/2025/9/policy/odrl.jsonld")

    def test_policy_type_is_set_not_odrl_set(self):
        """Test that policy @type is 'Set' not 'odrl:Set' for Saturn/Tractus-X EDC"""
        policy = PolicyModel.builder() \
            .id("test-policy") \
            .permissions([{"action": "use"}]) \
            .build()
        
        data = json.loads(policy.to_data())
        
        # Policy type should be "Set" when ODRL context is imported at top level
        self.assertEqual(data["policy"]["@type"], "Set")

    def test_complete_policy_structure_compliance(self):
        """Test that the complete policy structure matches Tractus-X EDC specification"""
        permissions = [{
            "action": "use",
            "constraint": {
                "leftOperand": "FrameworkAgreement",
                "operator": "eq",
                "rightOperand": "DataExchangeGovernance:1.0"
            }
        }]
        
        policy = PolicyModel.builder() \
            .id("membership-deg") \
            .permissions(permissions) \
            .build()
        
        data = json.loads(policy.to_data())
        
        # Verify top-level structure
        self.assertEqual(data["@type"], "PolicyDefinition")
        self.assertEqual(data["@id"], "membership-deg")
        self.assertIn("@context", data)
        self.assertIn("policy", data)
        
        # Verify context structure
        context = data["@context"]
        self.assertIsInstance(context, list)
        self.assertIn("https://w3id.org/catenax/2025/9/policy/odrl.jsonld", context)
        self.assertIn("https://w3id.org/catenax/2025/9/policy/context.jsonld", context)
        
        # Verify policy structure
        policy_obj = data["policy"]
        self.assertEqual(policy_obj["@type"], "Set")
        self.assertEqual(policy_obj["permission"], permissions)
        
        # ODRL context should NOT be nested in policy
        self.assertNotIn("@context", policy_obj)


if __name__ == '__main__':
    unittest.main()
