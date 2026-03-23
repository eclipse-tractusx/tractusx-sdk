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

from tractusx_sdk.dataspace.models.connector.model_factory import ModelFactory


class TestContractNegotiationWithSaturnPolicy(unittest.TestCase):
    """Test that Contract Negotiation works correctly with Saturn PolicyModel context"""

    def test_contract_negotiation_with_policy_model_saturn(self):
        """Test contract negotiation using a Saturn policy model"""
        
        # Create a Saturn policy model with permissions
        policy = ModelFactory.get_policy_model(
            dataspace_version="saturn",
            oid="test-policy",
            permissions=[{
                "action": "use",
                "constraint": {
                    "leftOperand": "FrameworkAgreement",
                    "operator": "eq",
                    "rightOperand": "DataExchangeGovernance:1.0"
                }
            }]
        )
        
        # Create contract negotiation using the policy model
        contract_negotiation = ModelFactory.get_contract_negotiation_model(
            dataspace_version="saturn",
            counter_party_address="https://provider-control.plane/api/v1/dsp/2025-1",
            offer_id="offer-123",
            asset_id="asset-456",
            provider_id="BPNL000000000001",
            offer_policy_model=policy,
            protocol="dataspace-protocol-http:2025-1"
        )
        
        # Convert to JSON and parse
        data = json.loads(contract_negotiation.to_data())
        
        # Verify top-level structure
        self.assertEqual(data["@type"], "ContractRequest")
        self.assertEqual(data["counterPartyAddress"], "https://provider-control.plane/api/v1/dsp/2025-1")
        self.assertEqual(data["protocol"], "dataspace-protocol-http:2025-1")
        
        # Verify context contains ODRL contexts
        context = data["@context"]
        if isinstance(context, list):
            self.assertIn("https://w3id.org/catenax/2025/9/policy/odrl.jsonld", context)
            self.assertIn("https://w3id.org/catenax/2025/9/policy/context.jsonld", context)
        
        # Verify policy structure in contract negotiation
        policy_data = data["policy"]
        self.assertEqual(policy_data["@id"], "offer-123")
        self.assertEqual(policy_data["@type"], "odrl:Offer")
        
        # Verify assigner and target
        self.assertIn("assigner", policy_data)
        self.assertEqual(policy_data["assigner"]["@id"], "BPNL000000000001")
        self.assertIn("target", policy_data)
        self.assertEqual(policy_data["target"]["@id"], "asset-456")
        
        # Verify permissions were merged correctly
        self.assertIn("permission", policy_data)
        self.assertEqual(len(policy_data["permission"]), 1)
        self.assertEqual(policy_data["permission"][0]["action"], "use")

    def test_contract_negotiation_context_structure(self):
        """Test that contract negotiation has proper context structure from catalog"""
        
        # According to docs, contract negotiation should have ODRL context
        # when explicitly provided
        odrl_contexts = [
            "https://w3id.org/catenax/2025/9/policy/odrl.jsonld",
            "https://w3id.org/catenax/2025/9/policy/context.jsonld",
            {
                "@vocab": "https://w3id.org/edc/v0.0.1/ns/"
            }
        ]
        
        policy = ModelFactory.get_policy_model(
            dataspace_version="saturn",
            oid="test-policy",
            permissions=[{"action": "use"}]
        )
        
        # Contract negotiation needs explicit context for ODRL
        contract_negotiation = ModelFactory.get_contract_negotiation_model(
            dataspace_version="saturn",
            counter_party_address="https://provider/dsp",
            offer_id="offer-1",
            asset_id="asset-1",
            provider_id="provider-1",
            offer_policy_model=policy,
            context=odrl_contexts  # Explicitly pass ODRL context
        )
        
        data = json.loads(contract_negotiation.to_data())
        
        # Context should include ODRL contexts for Saturn when provided
        context = data["@context"]
        self.assertIsInstance(context, list)
        
        # Should have the Catena-X ODRL contexts
        for odrl_ctx_url in ["https://w3id.org/catenax/2025/9/policy/odrl.jsonld",
                              "https://w3id.org/catenax/2025/9/policy/context.jsonld"]:
            self.assertIn(odrl_ctx_url, context, 
                f"Contract negotiation context should include {odrl_ctx_url}")

    def test_catalog_request_context(self):
        """Test that catalog request has proper context structure"""
        
        catalog = ModelFactory.get_catalog_model(
            dataspace_version="saturn",
            counter_party_address="https://provider/dsp",
            counter_party_id="provider-1",
            protocol="dataspace-protocol-http:2025-1"
        )
        
        data = json.loads(catalog.to_data())
        
        # Verify basic structure
        self.assertEqual(data["@type"], "CatalogRequest")
        self.assertEqual(data["protocol"], "dataspace-protocol-http:2025-1")
        
        # Context should be present
        self.assertIn("@context", data)
        context = data["@context"]
        
        # For catalog, the default context is fine since it doesn't contain policies directly
        # The catalog RESPONSE will contain policies, but the REQUEST doesn't need ODRL context
        if isinstance(context, dict):
            self.assertIn("@vocab", context)
        elif isinstance(context, list):
            # If list, should at least have a vocab entry
            vocab_found = False
            for item in context:
                if isinstance(item, dict) and "@vocab" in item:
                    vocab_found = True
                    break
            self.assertTrue(vocab_found, "Context should contain @vocab")

    def test_contract_negotiation_preserves_custom_context(self):
        """Test that custom context in contract negotiation is preserved"""
        
        custom_context = [
            "https://w3id.org/catenax/2025/9/policy/odrl.jsonld",
            "https://w3id.org/catenax/2025/9/policy/context.jsonld",
            {
                "@vocab": "https://w3id.org/edc/v0.0.1/ns/",
                "custom": "https://example.com/custom"
            }
        ]
        
        policy = ModelFactory.get_policy_model(
            dataspace_version="saturn",
            oid="test-policy",
            context=custom_context,
            permissions=[{"action": "use"}]
        )
        
        contract_negotiation = ModelFactory.get_contract_negotiation_model(
            dataspace_version="saturn",
            counter_party_address="https://provider/dsp",
            offer_id="offer-1",
            asset_id="asset-1",
            provider_id="provider-1",
            offer_policy_model=policy,
            context=custom_context
        )
        
        data = json.loads(contract_negotiation.to_data())
        context = data["@context"]
        
        # Verify custom context is preserved
        self.assertIsInstance(context, list)
        
        # Find the dict in context and check for custom field
        custom_found = False
        for item in context:
            if isinstance(item, dict) and "custom" in item:
                custom_found = True
                self.assertEqual(item["custom"], "https://example.com/custom")
                break
        
        self.assertTrue(custom_found, "Custom context field should be preserved")


if __name__ == '__main__':
    unittest.main()
