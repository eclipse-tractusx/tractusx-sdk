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


ODRL_URL     = "https://w3id.org/catenax/2025/9/policy/odrl.jsonld"
CONTEXT_URL  = "https://w3id.org/catenax/2025/9/policy/context.jsonld"
EDC_VOCAB    = "https://w3id.org/edc/v0.0.1/ns/"
ODRL_URLS    = {ODRL_URL, CONTEXT_URL}


class TestSaturnPolicyModelContext(unittest.TestCase):
    """Test Saturn PolicyModel context building according to Tractus-X EDC specification"""

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _build(self, context=None, permissions=None):
        """Build a PolicyModel and return the parsed JSON dict."""
        builder = PolicyModel.builder().id("test-policy")
        if context is not None:
            builder = builder.context(context)
        builder = builder.permissions(permissions or [{"action": "use"}])
        return json.loads(builder.build().to_data())

    def _assert_odrl_context(self, context, expected_len):
        """Assert context is a list of expected_len with both ODRL URLs present."""
        self.assertIsInstance(context, list)
        self.assertEqual(len(context), expected_len)
        self.assertIn(ODRL_URL,    context)
        self.assertIn(CONTEXT_URL, context)

    # ── Tests ─────────────────────────────────────────────────────────────────

    def test_default_context_when_none_provided(self):
        """Default ODRL contexts are added when no context is provided."""
        context = self._build()["@context"]

        self._assert_odrl_context(context, 3)
        self.assertEqual(context[0], ODRL_URL)
        self.assertEqual(context[1], CONTEXT_URL)
        self.assertIsInstance(context[2], dict)
        self.assertEqual(context[2]["@vocab"], EDC_VOCAB)

    def test_context_with_dict_prepends_odrl(self):
        """Passing a dict context prepends ODRL contexts before it."""
        custom = {"@vocab": EDC_VOCAB, "custom": "https://example.com/custom"}
        context = self._build(context=custom)["@context"]

        self._assert_odrl_context(context, 3)
        self.assertEqual(context[0], ODRL_URL)
        self.assertEqual(context[1], CONTEXT_URL)
        self.assertEqual(context[2], custom)

    def test_context_with_list_preserves_odrl_if_present(self):
        """If user provides a list with both ODRL URLs, they are not duplicated."""
        custom = [
            ODRL_URL,
            CONTEXT_URL,
            {"@vocab": EDC_VOCAB, "custom": "https://example.com/custom"},
        ]
        context = self._build(context=custom)["@context"]

        self._assert_odrl_context(context, 3)
        self.assertIsInstance(context[2], dict)
        self.assertIn("custom", context[2])

    def test_context_with_list_adds_missing_odrl(self):
        """If user list lacks both ODRL URLs, they are prepended."""
        custom = [{"@vocab": EDC_VOCAB, "custom": "https://example.com/custom"}]
        context = self._build(context=custom)["@context"]

        self._assert_odrl_context(context, 3)
        self.assertEqual(context[0], ODRL_URL)
        self.assertEqual(context[1], CONTEXT_URL)
        self.assertIsInstance(context[2], dict)

    def test_context_with_partial_odrl_adds_missing_ones(self):
        """If only one ODRL URL is present, the missing one is inserted."""
        custom = [ODRL_URL, {"@vocab": EDC_VOCAB}]
        context = self._build(context=custom)["@context"]

        self._assert_odrl_context(context, 3)
        self.assertEqual(context[0], CONTEXT_URL)
        self.assertEqual(context[1], ODRL_URL)

    def test_policy_type_is_set_not_odrl_set(self):
        """Policy @type must be 'Set' (not 'odrl:Set') when ODRL context is top-level."""
        data = self._build()
        self.assertEqual(data["policy"]["@type"], "Set")

    def test_complete_policy_structure_compliance(self):
        """Complete policy structure matches Tractus-X EDC specification."""
        permissions = [{
            "action": "use",
            "constraint": {
                "leftOperand": "FrameworkAgreement",
                "operator": "eq",
                "rightOperand": "DataExchangeGovernance:1.0",
            },
        }]

        data = json.loads(
            PolicyModel.builder()
            .id("membership-deg")
            .permissions(permissions)
            .build()
            .to_data()
        )

        # Top-level structure
        self.assertEqual(data["@type"], "PolicyDefinition")
        self.assertEqual(data["@id"],   "membership-deg")
        self.assertIn("@context", data)
        self.assertIn("policy",   data)

        # Context
        self._assert_odrl_context(data["@context"], len(data["@context"]))

        # Policy body
        policy_obj = data["policy"]
        self.assertEqual(policy_obj["@type"],      "Set")
        self.assertEqual(policy_obj["permission"], permissions)
        self.assertNotIn("@context", policy_obj)  # ODRL context must not be nested



if __name__ == '__main__':
    unittest.main()
