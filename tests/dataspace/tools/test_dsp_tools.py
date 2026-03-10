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

from unittest import TestCase

from tractusx_sdk.dataspace.tools.dsp_tools import DspTools


class TestIsPolicyValid(TestCase):
    """Tests for DspTools.is_policy_valid, focusing on namespace-prefix normalisation."""

    # ── allowed_policies=None / [] edge cases ──────────────────────────────────

    def test_none_allowed_policies_accepts_everything(self):
        policy = {"odrl:permission": [{"odrl:action": "use"}]}
        self.assertTrue(DspTools.is_policy_valid(policy=policy, allowed_policies=None))

    def test_empty_allowed_policies_rejects_everything(self):
        policy = {"permission": [{"action": "use"}]}
        self.assertFalse(DspTools.is_policy_valid(policy=policy, allowed_policies=[]))

    # ── exact match (no prefix difference) ────────────────────────────────────

    def test_exact_match_saturn_format(self):
        policy = {"permission": [{"action": "use"}]}
        allowed = [{"permission": [{"action": "use"}]}]
        self.assertTrue(DspTools.is_policy_valid(policy=policy, allowed_policies=allowed))

    def test_exact_match_legacy_format(self):
        policy = {"odrl:permission": [{"odrl:action": "use"}]}
        allowed = [{"odrl:permission": [{"odrl:action": "use"}]}]
        self.assertTrue(DspTools.is_policy_valid(policy=policy, allowed_policies=allowed))

    # ── cross-format matching (the bug fix) ───────────────────────────────────

    def test_catalog_odrl_prefix_allowed_saturn_format(self):
        """Catalog returns odrl:-prefixed keys; user provides Saturn (unprefixed) policy."""
        catalog_policy = {
            "@id": "policy-instance-123",
            "@type": "odrl:Offer",
            "odrl:permission": [
                {"odrl:action": "use", "odrl:constraint": {"odrl:leftOperand": "cx-policy:FrameworkAgreement", "odrl:operator": "eq", "odrl:rightOperand": "active"}}
            ],
            "odrl:obligation": [],
            "odrl:prohibition": [],
        }
        allowed_policies = [
            {
                "permission": [
                    {"action": "use", "constraint": {"leftOperand": "cx-policy:FrameworkAgreement", "operator": "eq", "rightOperand": "active"}}
                ],
                "obligation": [],
                "prohibition": [],
            }
        ]
        self.assertTrue(DspTools.is_policy_valid(policy=catalog_policy, allowed_policies=allowed_policies))

    def test_catalog_saturn_format_allowed_odrl_prefix(self):
        """Catalog returns Saturn (unprefixed) keys; user provides odrl:-prefixed allowed policy."""
        catalog_policy = {
            "@id": "policy-instance-456",
            "@type": "Set",
            "permission": [{"action": "use"}],
            "obligation": [],
        }
        allowed_policies = [
            {
                "odrl:permission": [{"odrl:action": "use"}],
                "odrl:obligation": [],
            }
        ]
        self.assertTrue(DspTools.is_policy_valid(policy=catalog_policy, allowed_policies=allowed_policies))

    def test_mixed_prefixes_no_match_on_different_values(self):
        """Even after prefix normalisation, different constraint values must not match."""
        catalog_policy = {
            "odrl:permission": [{"odrl:action": "use", "odrl:leftOperand": "A"}],
        }
        allowed_policies = [
            {"permission": [{"action": "use", "leftOperand": "B"}]},
        ]
        self.assertFalse(DspTools.is_policy_valid(policy=catalog_policy, allowed_policies=allowed_policies))

    def test_multiple_allowed_policies_one_matches(self):
        """The first matching allowed policy should return True."""
        catalog_policy = {"odrl:permission": [{"odrl:action": "use"}]}
        allowed_policies = [
            {"permission": [{"action": "read"}]},   # no match
            {"permission": [{"action": "use"}]},    # match
        ]
        self.assertTrue(DspTools.is_policy_valid(policy=catalog_policy, allowed_policies=allowed_policies))

    def test_id_and_type_are_excluded_from_comparison(self):
        """@id and @type in catalog policy must not influence comparison."""
        catalog_policy = {
            "@id": "urn:uuid:some-unique-id",
            "@type": "odrl:Offer",
            "odrl:permission": [{"odrl:action": "use"}],
        }
        allowed_policies = [
            {"permission": [{"action": "use"}]},
        ]
        self.assertTrue(DspTools.is_policy_valid(policy=catalog_policy, allowed_policies=allowed_policies))

    def test_id_and_type_in_allowed_policy_are_also_excluded(self):
        """@id and @type in user-provided allowed policies must not affect comparison."""
        catalog_policy = {"permission": [{"action": "use"}]}
        allowed_policies = [
            {"@id": "user-side-id", "@type": "Set", "permission": [{"action": "use"}]},
        ]
        self.assertTrue(DspTools.is_policy_valid(policy=catalog_policy, allowed_policies=allowed_policies))

    def test_nested_prefix_normalisation(self):
        """Prefixes inside deeply nested constraint dicts are stripped too."""
        catalog_policy = {
            "odrl:permission": [
                {
                    "odrl:action": "use",
                    "odrl:constraint": {
                        "odrl:and": [
                            {"odrl:leftOperand": "A", "odrl:operator": "eq", "odrl:rightOperand": "1"},
                            {"odrl:leftOperand": "B", "odrl:operator": "eq", "odrl:rightOperand": "2"},
                        ]
                    },
                }
            ]
        }
        allowed_policies = [
            {
                "permission": [
                    {
                        "action": "use",
                        "constraint": {
                            "and": [
                                {"leftOperand": "A", "operator": "eq", "rightOperand": "1"},
                                {"leftOperand": "B", "operator": "eq", "rightOperand": "2"},
                            ]
                        },
                    }
                ]
            }
        ]
        self.assertTrue(DspTools.is_policy_valid(policy=catalog_policy, allowed_policies=allowed_policies))


class TestFilterAssetsAndPolicies(TestCase):
    """Integration tests for filter_assets_and_policies with cross-format policy matching."""

    def _make_catalog(self, policies, dataset_key="dataset", policy_key="hasPolicy"):
        return {
            dataset_key: {
                "@id": "urn:asset:1",
                policy_key: policies,
            }
        }

    def test_saturn_catalog_matched_by_saturn_allowed_policy(self):
        catalog = self._make_catalog(
            policies={"@id": "p1", "permission": [{"action": "use"}]},
        )
        allowed = [{"permission": [{"action": "use"}]}]
        result = DspTools.filter_assets_and_policies(catalog=catalog, allowed_policies=allowed)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0][0], "urn:asset:1")

    def test_legacy_catalog_matched_by_saturn_allowed_policy(self):
        """Legacy catalog (odrl:-prefixed) can be matched by Saturn allowed policy."""
        catalog = self._make_catalog(
            policies={"@id": "p1", "odrl:permission": [{"odrl:action": "use"}]},
            dataset_key="dcat:dataset",
            policy_key="odrl:hasPolicy",
        )
        allowed = [{"permission": [{"action": "use"}]}]
        result = DspTools.filter_assets_and_policies(catalog=catalog, allowed_policies=allowed)
        self.assertEqual(len(result), 1)

    def test_no_match_returns_error(self):
        catalog = self._make_catalog(
            policies={"@id": "p1", "permission": [{"action": "use"}]},
        )
        allowed = [{"permission": [{"action": "write"}]}]
        with self.assertRaises((ValueError, RuntimeError, Exception)):
            DspTools.filter_assets_and_policies(catalog=catalog, allowed_policies=allowed)
