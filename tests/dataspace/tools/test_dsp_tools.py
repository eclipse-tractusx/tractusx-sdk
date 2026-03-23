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

"""
Tests for DspTools – policy filtering with Saturn and Jupiter catalogs.

Validates that ``filter_assets_and_policies`` correctly matches an allowed
policy list against real-world catalog responses, regardless of
constraint ordering, single-element list wrapping, or empty prohibition /
obligation fields.  Also verifies that Saturn policies are NOT accepted
for Jupiter catalogs and vice versa.
"""

import copy
import logging
import pytest

from tractusx_sdk.dataspace.tools.dsp_tools import (
    DspTools, _normalize_policy_value, _explain_policy_diff, _check_policy_structure,
)


# ── Fixtures ─────────────────────────────────────────────────────────────────

SATURN_CATALOG = {
    "@id": "2f484839-bc3a-4068-91d9-d83eef2766f6",
    "@type": "Catalog",
    "dataset": [
        {
            "@id": "ichub:asset:dtr:9foUM7pmSTrr5LZnx0NqiQ",
            "@type": "Dataset",
            "hasPolicy": [
                {
                    "@id": "aWNodWI6Y29udHJhY3Q6T0JsRjZUSF92VlI3c2YtbW9sY09Wdw==:aWNodWI6YXNzZXQ6ZHRyOjlmb1VNN3BtU1RycjVMWm54ME5xaVE=:ODVmMjgxMjgtY2QzMy00YjM3LTk3NzYtOGI0ZDFhY2MyZGU4",
                    "@type": "Offer",
                    "permission": [
                        {
                            "action": "use",
                            "constraint": [
                                {
                                    "and": [
                                        {
                                            "leftOperand": "FrameworkAgreement",
                                            "operator": "eq",
                                            "rightOperand": "DataExchangeGovernance:1.0"
                                        },
                                        {
                                            "leftOperand": "Membership",
                                            "operator": "eq",
                                            "rightOperand": "active"
                                        },
                                        {
                                            "leftOperand": "UsagePurpose",
                                            "operator": "isAnyOf",
                                            "rightOperand": "cx.core.digitalTwinRegistry:1"
                                        }
                                    ]
                                }
                            ]
                        }
                    ]
                }
            ],
            "distribution": [
                {
                    "@type": "Distribution",
                    "format": "AzureStorage-PUSH",
                    "accessService": {
                        "@id": "0cd64767-db7e-4c15-a0c7-9c8d276399d5",
                        "@type": "DataService",
                        "endpointDescription": "dspace:connector",
                        "endpointURL": "https://edc-provider-ichub-control.int.catena-x.net/api/v1/dsp/2025-1"
                    }
                },
                {
                    "@type": "Distribution",
                    "format": "HttpData-PULL",
                    "accessService": {
                        "@id": "fa2febe1-8138-4388-8ee8-d4261aebf409",
                        "@type": "DataService",
                        "endpointDescription": "dspace:connector",
                        "endpointURL": "https://edc-provider-ichub-control.int.catena-x.net/api/v1/dsp/2025-1"
                    }
                },
                {
                    "@type": "Distribution",
                    "format": "HttpData-PUSH",
                    "accessService": {
                        "@id": "7aaadc87-8778-441f-8093-9073a8663cf0",
                        "@type": "DataService",
                        "endpointDescription": "dspace:connector",
                        "endpointURL": "https://edc-provider-ichub-control.int.catena-x.net/api/v1/dsp/2025-1"
                    }
                },
                {
                    "@type": "Distribution",
                    "format": "AmazonS3-PUSH",
                    "accessService": {
                        "@id": "397f8630-6f50-4f3d-b086-92023a99981e",
                        "@type": "DataService",
                        "endpointDescription": "dspace:connector",
                        "endpointURL": "https://edc-provider-ichub-control.int.catena-x.net/api/v1/dsp/2025-1"
                    }
                },
                {
                    "@type": "Distribution",
                    "format": "ProxyHttpData-PULL",
                    "accessService": {
                        "@id": "b98c63e4-429e-40fc-bb9c-579adcbd9810",
                        "@type": "DataService",
                        "endpointDescription": "dspace:connector",
                        "endpointURL": "https://edc-provider-ichub-control.int.catena-x.net/api/v1/dsp/2025-1"
                    }
                }
            ],
            "dct:type": {
                "@id": "https://w3id.org/catenax/taxonomy#DigitalTwinRegistry"
            },
            "https://w3id.org/catenax/ontology/common#version": "3.0",
            "id": "ichub:asset:dtr:9foUM7pmSTrr5LZnx0NqiQ"
        }
    ],
    "service": [
        {
            "@id": "5d77708c-2d21-476c-9a64-f6f672cfe2c8",
            "@type": "DataService",
            "endpointDescription": "dspace:connector",
            "endpointURL": "https://edc-provider-ichub-control.int.catena-x.net/api/v1/dsp/2025-1"
        }
    ],
    "participantId": "did:web:portal-backend.int.catena-x.net:api:administration:staticdata:did:BPNL0000000093Q7",
    "@context": [
        "https://w3id.org/tractusx/auth/v1.0.0",
        "https://w3id.org/catenax/2025/9/policy/context.jsonld",
        "https://w3id.org/dspace/2025/1/context.jsonld",
        "https://w3id.org/edc/dspace/v0.0.1"
    ]
}

# Six allowed policies – same three constraints in every possible order,
# with empty prohibition/obligation lists (common user-side format).
ALLOWED_POLICIES = [
    {
        "permission": {
            "action": "use",
            "constraint": {
                "and": [
                    {
                        "leftOperand": "FrameworkAgreement",
                        "operator": "eq",
                        "rightOperand": "DataExchangeGovernance:1.0"
                    },
                    {
                        "leftOperand": "Membership",
                        "operator": "eq",
                        "rightOperand": "active"
                    },
                    {
                        "leftOperand": "UsagePurpose",
                        "operator": "isAnyOf",
                        "rightOperand": "cx.core.digitalTwinRegistry:1"
                    }
                ]
            }
        },
        "prohibition": [],
        "obligation": []
    },
    {
        "permission": {
            "action": "use",
            "constraint": {
                "and": [
                    {
                        "leftOperand": "FrameworkAgreement",
                        "operator": "eq",
                        "rightOperand": "DataExchangeGovernance:1.0"
                    },
                    {
                        "leftOperand": "UsagePurpose",
                        "operator": "isAnyOf",
                        "rightOperand": "cx.core.digitalTwinRegistry:1"
                    },
                    {
                        "leftOperand": "Membership",
                        "operator": "eq",
                        "rightOperand": "active"
                    }
                ]
            }
        },
        "prohibition": [],
        "obligation": []
    },
    {
        "permission": {
            "action": "use",
            "constraint": {
                "and": [
                    {
                        "leftOperand": "Membership",
                        "operator": "eq",
                        "rightOperand": "active"
                    },
                    {
                        "leftOperand": "FrameworkAgreement",
                        "operator": "eq",
                        "rightOperand": "DataExchangeGovernance:1.0"
                    },
                    {
                        "leftOperand": "UsagePurpose",
                        "operator": "isAnyOf",
                        "rightOperand": "cx.core.digitalTwinRegistry:1"
                    }
                ]
            }
        },
        "prohibition": [],
        "obligation": []
    },
    {
        "permission": {
            "action": "use",
            "constraint": {
                "and": [
                    {
                        "leftOperand": "Membership",
                        "operator": "eq",
                        "rightOperand": "active"
                    },
                    {
                        "leftOperand": "UsagePurpose",
                        "operator": "isAnyOf",
                        "rightOperand": "cx.core.digitalTwinRegistry:1"
                    },
                    {
                        "leftOperand": "FrameworkAgreement",
                        "operator": "eq",
                        "rightOperand": "DataExchangeGovernance:1.0"
                    }
                ]
            }
        },
        "prohibition": [],
        "obligation": []
    },
    {
        "permission": {
            "action": "use",
            "constraint": {
                "and": [
                    {
                        "leftOperand": "UsagePurpose",
                        "operator": "isAnyOf",
                        "rightOperand": "cx.core.digitalTwinRegistry:1"
                    },
                    {
                        "leftOperand": "FrameworkAgreement",
                        "operator": "eq",
                        "rightOperand": "DataExchangeGovernance:1.0"
                    },
                    {
                        "leftOperand": "Membership",
                        "operator": "eq",
                        "rightOperand": "active"
                    }
                ]
            }
        },
        "prohibition": [],
        "obligation": []
    },
    {
        "permission": {
            "action": "use",
            "constraint": {
                "and": [
                    {
                        "leftOperand": "UsagePurpose",
                        "operator": "isAnyOf",
                        "rightOperand": "cx.core.digitalTwinRegistry:1"
                    },
                    {
                        "leftOperand": "Membership",
                        "operator": "eq",
                        "rightOperand": "active"
                    },
                    {
                        "leftOperand": "FrameworkAgreement",
                        "operator": "eq",
                        "rightOperand": "DataExchangeGovernance:1.0"
                    }
                ]
            }
        },
        "prohibition": [],
        "obligation": []
    }
]


# ── Tests ────────────────────────────────────────────────────────────────────

class TestDspToolsSaturnPolicyMatching:
    """
    Tests that DspTools policy matching works with Saturn (DSP 2025-1)
    catalog responses and user-supplied allowed policy lists.
    """

    def test_filter_assets_and_policies_saturn_catalog_all_permutations(self):
        """
        Given a real Saturn catalog with a single dataset and one offer policy,
        assert that ``filter_assets_and_policies`` returns the asset with a
        valid policy when the allowed_policies list contains the same
        constraints in every possible order.
        """
        result = DspTools.filter_assets_and_policies(
            catalog=SATURN_CATALOG,
            allowed_policies=ALLOWED_POLICIES
        )

        # Exactly one asset should be returned
        assert len(result) == 1
        asset_id, policy = result[0]
        assert asset_id == "ichub:asset:dtr:9foUM7pmSTrr5LZnx0NqiQ"
        # The returned policy should contain the original offer @id
        assert policy["@id"] == (
            "aWNodWI6Y29udHJhY3Q6T0JsRjZUSF92VlI3c2YtbW9sY09Wdw==:"
            "aWNodWI6YXNzZXQ6ZHRyOjlmb1VNN3BtU1RycjVMWm54ME5xaVE=:"
            "ODVmMjgxMjgtY2QzMy00YjM3LTk3NzYtOGI0ZDFhY2MyZGU4"
        )

    def test_filter_assets_with_single_allowed_policy(self):
        """
        Even a single allowed policy (one permutation) is enough to match.
        """
        single = [ALLOWED_POLICIES[0]]
        result = DspTools.filter_assets_and_policies(
            catalog=SATURN_CATALOG,
            allowed_policies=single
        )
        assert len(result) == 1
        assert result[0][0] == "ichub:asset:dtr:9foUM7pmSTrr5LZnx0NqiQ"

    def test_each_permutation_matches_individually(self):
        """
        Each of the six constraint orderings must independently match the
        catalog policy.
        """
        catalog_policy = SATURN_CATALOG["dataset"][0]["hasPolicy"][0]
        for i, allowed in enumerate(ALLOWED_POLICIES):
            assert DspTools.is_policy_valid(
                policy=catalog_policy,
                allowed_policies=[allowed]
            ), f"Allowed policy permutation {i} did not match the catalog policy"

    def test_policy_none_accepts_everything(self):
        """
        Passing ``allowed_policies=None`` should accept any policy.
        """
        catalog_policy = SATURN_CATALOG["dataset"][0]["hasPolicy"][0]
        assert DspTools.is_policy_valid(policy=catalog_policy, allowed_policies=None) is True

    def test_policy_empty_list_rejects_everything(self):
        """
        Passing ``allowed_policies=[]`` should reject every policy.
        """
        catalog_policy = SATURN_CATALOG["dataset"][0]["hasPolicy"][0]
        assert DspTools.is_policy_valid(policy=catalog_policy, allowed_policies=[]) is False

    def test_filter_assets_empty_policies_raises(self):
        """
        An empty allowed list means no policy can match → ValueError expected.
        """
        with pytest.raises(ValueError, match="No valid"):
            DspTools.filter_assets_and_policies(
                catalog=SATURN_CATALOG,
                allowed_policies=[]
            )

    def test_filter_assets_none_catalog_raises(self):
        """
        A ``None`` catalog should raise an Exception.
        """
        with pytest.raises(Exception, match="catalog is empty"):
            DspTools.filter_assets_and_policies(catalog=None, allowed_policies=ALLOWED_POLICIES)

    def test_non_matching_policy_is_rejected(self):
        """
        A policy with a different constraint value must NOT match.
        """
        non_matching = [{
            "permission": {
                "action": "use",
                "constraint": {
                    "and": [
                        {
                            "leftOperand": "FrameworkAgreement",
                            "operator": "eq",
                            "rightOperand": "SomeOtherAgreement:2.0"
                        },
                        {
                            "leftOperand": "Membership",
                            "operator": "eq",
                            "rightOperand": "active"
                        }
                    ]
                }
            },
            "prohibition": [],
            "obligation": []
        }]
        catalog_policy = SATURN_CATALOG["dataset"][0]["hasPolicy"][0]
        assert DspTools.is_policy_valid(policy=catalog_policy, allowed_policies=non_matching) is False

    def test_constraint_order_inside_and_does_not_matter(self):
        """
        The allowed policy has constraints in order A → B → C, but the catalog
        returns them in order B → C → A.  The match must still succeed because
        constraint ordering inside ``and`` is irrelevant.
        """
        # Allowed: FrameworkAgreement → Membership → UsagePurpose
        allowed = [{
            "permission": {
                "action": "use",
                "constraint": {
                    "and": [
                        {"leftOperand": "FrameworkAgreement", "operator": "eq",
                         "rightOperand": "DataExchangeGovernance:1.0"},
                        {"leftOperand": "Membership", "operator": "eq",
                         "rightOperand": "active"},
                        {"leftOperand": "UsagePurpose", "operator": "isAnyOf",
                         "rightOperand": "cx.core.digitalTwinRegistry:1"},
                    ]
                }
            }
        }]

        # Catalog: Membership → UsagePurpose → FrameworkAgreement (different order)
        catalog_policy = {
            "@id": "offer-order-test",
            "@type": "Offer",
            "permission": [{
                "action": "use",
                "constraint": [{
                    "and": [
                        {"leftOperand": "Membership", "operator": "eq",
                         "rightOperand": "active"},
                        {"leftOperand": "UsagePurpose", "operator": "isAnyOf",
                         "rightOperand": "cx.core.digitalTwinRegistry:1"},
                        {"leftOperand": "FrameworkAgreement", "operator": "eq",
                         "rightOperand": "DataExchangeGovernance:1.0"},
                    ]
                }]
            }]
        }

        assert DspTools.is_policy_valid(
            policy=catalog_policy, allowed_policies=allowed
        ) is True, "Constraints in different order inside 'and' must still match"

    def test_constraint_order_inside_and_still_rejects_wrong_values(self):
        """
        Even though constraint order is irrelevant, the values themselves must
        still match exactly.
        """
        allowed = [{
            "permission": {
                "action": "use",
                "constraint": {
                    "and": [
                        {"leftOperand": "FrameworkAgreement", "operator": "eq",
                         "rightOperand": "DataExchangeGovernance:1.0"},
                        {"leftOperand": "Membership", "operator": "eq",
                         "rightOperand": "active"},
                    ]
                }
            }
        }]

        # Catalog has same constraints in reversed order but WRONG rightOperand
        catalog_policy = {
            "@id": "offer-order-reject",
            "@type": "Offer",
            "permission": [{
                "action": "use",
                "constraint": [{
                    "and": [
                        {"leftOperand": "Membership", "operator": "eq",
                         "rightOperand": "active"},
                        {"leftOperand": "FrameworkAgreement", "operator": "eq",
                         "rightOperand": "SomeOtherAgreement:2.0"},
                    ]
                }]
            }]
        }

        assert DspTools.is_policy_valid(
            policy=catalog_policy, allowed_policies=allowed
        ) is False, "Different rightOperand must still be rejected regardless of order"

    def test_different_usage_purpose_rejects_against_existing_catalog(self):
        """
        An allowed policy with ``UsagePurpose = cx.core.legalRequirementForThirdparty:1``
        must NOT match the catalog which contains ``cx.core.digitalTwinRegistry:1``.
        """
        allowed_with_different_purpose = [{
            "permission": {
                "action": "use",
                "constraint": {
                    "and": [
                        {"leftOperand": "UsagePurpose", "operator": "isAnyOf",
                         "rightOperand": "cx.core.legalRequirementForThirdparty:1"},
                        {"leftOperand": "FrameworkAgreement", "operator": "eq",
                         "rightOperand": "DataExchangeGovernance:1.0"},
                        {"leftOperand": "Membership", "operator": "eq",
                         "rightOperand": "active"},
                    ]
                }
            },
            "prohibition": [],
            "obligation": []
        }]
        catalog_policy = SATURN_CATALOG["dataset"][0]["hasPolicy"][0]
        assert DspTools.is_policy_valid(
            policy=catalog_policy,
            allowed_policies=allowed_with_different_purpose,
        ) is False, (
            "cx.core.legalRequirementForThirdparty:1 must not match "
            "cx.core.digitalTwinRegistry:1"
        )

    def test_different_usage_purpose_matches_when_catalog_agrees(self):
        """
        When the catalog asset also uses ``cx.core.legalRequirementForThirdparty:1``
        the allowed policy with the same value must match.
        """
        catalog_policy = {
            "@id": "offer-legal-requirement",
            "@type": "Offer",
            "permission": [
                {
                "action": "use",
                "constraint": 
                        {"leftOperand": "UsagePurpose", "operator": "isAnyOf",
                         "rightOperand": "cx.core.legalRequirementForThirdparty:1"},
                    
                
            },{
                "action": "use",
                "constraint": [{
                    "and": [
                        {"leftOperand": "FrameworkAgreement", "operator": "eq",
                         "rightOperand": "DataExchangeGovernance:1.0"},
                        {"leftOperand": "Membership", "operator": "eq",
                         "rightOperand": "active"},
                        {"leftOperand": "UsagePurpose", "operator": "isAnyOf",
                         "rightOperand": "cx.core.legalRequirementForThirdparty:1"},
                    ]
                }]
            }]
        }
        allowed = [{
            "permission": {
                "action": "use",
                "constraint": {
                    "and": [
                        {"leftOperand": "UsagePurpose", "operator": "isAnyOf",
                         "rightOperand": "cx.core.legalRequirementForThirdparty:1"},
                        {"leftOperand": "FrameworkAgreement", "operator": "eq",
                         "rightOperand": "DataExchangeGovernance:1.0"},
                        {"leftOperand": "Membership", "operator": "eq",
                         "rightOperand": "active"},
                    ]
                }
            },
            "prohibition": [],
            "obligation": []
        }]
        assert DspTools.is_policy_valid(
            policy=catalog_policy, allowed_policies=allowed
        ) is True, (
            "Catalog and config both use cx.core.legalRequirementForThirdparty:1 – must match"
        )

    def test_catalog_legal_requirement_rejected_by_digital_twin_config(self):
        """
        A catalog with ``UsagePurpose = cx.core.legalRequirementForThirdparty:1``
        must NOT match the standard ALLOWED_POLICIES which all use
        ``cx.core.digitalTwinRegistry:1``.
        """
        catalog_policy = {
            "@id": "offer-legal-vs-dtr",
            "@type": "Offer",
            "permission": [{
                "action": "use",
                "constraint": [{
                    "and": [
                        {"leftOperand": "FrameworkAgreement", "operator": "eq",
                         "rightOperand": "DataExchangeGovernance:1.0"},
                        {"leftOperand": "Membership", "operator": "eq",
                         "rightOperand": "active"},
                        {"leftOperand": "UsagePurpose", "operator": "isAnyOf",
                         "rightOperand": "cx.core.legalRequirementForThirdparty:1"},
                    ]
                }]
            }]
        }
        # All 6 ALLOWED_POLICIES have digitalTwinRegistry:1 – none should match
        assert DspTools.is_policy_valid(
            policy=catalog_policy,
            allowed_policies=ALLOWED_POLICIES,
        ) is False, (
            "Catalog legalRequirementForThirdparty:1 must not match "
            "allowed digitalTwinRegistry:1"
        )

    def test_legal_requirement_catalog_matches_legal_requirement_config(self):
        """
        End-to-end: a catalog whose asset uses
        ``UsagePurpose isAnyOf cx.core.legalRequirementForThirdparty:1``
        must be found by ``filter_assets_and_policies`` when the allowed
        config carries the same value — even though constraint order and
        list wrapping differ between catalog and config.
        """
        catalog = {
            "@id": "catalog-legal-req",
            "@type": "Catalog",
            "dataset": [{
                "@id": "asset:legal-req:1",
                "@type": "Dataset",
                "hasPolicy": [{
                    "@id": "offer:legal-req:1",
                    "@type": "Offer",
                    "permission": [{
                        "action": "use",
                        "constraint": [{
                            "and": [
                                {"leftOperand": "Membership", "operator": "eq",
                                 "rightOperand": "active"},
                                {"leftOperand": "FrameworkAgreement", "operator": "eq",
                                 "rightOperand": "DataExchangeGovernance:1.0"},
                                {"leftOperand": "UsagePurpose", "operator": "isAnyOf",
                                 "rightOperand": "cx.core.legalRequirementForThirdparty:1"},
                            ]
                        }]
                    }]
                }],
                "distribution": [{
                    "@type": "Distribution",
                    "format": "HttpData-PULL",
                    "accessService": {
                        "@id": "svc-1",
                        "@type": "DataService",
                        "endpointDescription": "dspace:connector",
                        "endpointURL": "https://example.com/api/v1/dsp/2025-1"
                    }
                }]
            }],
            "service": [{
                "@id": "svc-1",
                "@type": "DataService",
                "endpointDescription": "dspace:connector",
                "endpointURL": "https://example.com/api/v1/dsp/2025-1"
            }],
            "participantId": "did:web:example.com:BPNL000000001234",
            "@context": [
                "https://w3id.org/tractusx/auth/v1.0.0",
                "https://w3id.org/dspace/2025/1/context.jsonld"
            ]
        }
        allowed = [{
            "permission": {
                "action": "use",
                "constraint": {
                    "and": [
                        {"leftOperand": "UsagePurpose", "operator": "isAnyOf",
                         "rightOperand": "cx.core.legalRequirementForThirdparty:1"},
                        {"leftOperand": "FrameworkAgreement", "operator": "eq",
                         "rightOperand": "DataExchangeGovernance:1.0"},
                        {"leftOperand": "Membership", "operator": "eq",
                         "rightOperand": "active"},
                    ]
                }
            },
            "prohibition": [],
            "obligation": []
        }]

        result = DspTools.filter_assets_and_policies(
            catalog=catalog, allowed_policies=allowed
        )

        assert len(result) == 1
        asset_id, policy = result[0]
        assert asset_id == "asset:legal-req:1"
        assert policy["@id"] == "offer:legal-req:1"

    def test_policy_with_permission_obligation_and_prohibition(self):
        """
        A catalog policy with permissions, obligations, AND prohibitions
        must match when the allowed config specifies the same rules —
        regardless of constraint order, list wrapping, or rule ordering.
        """
        catalog_policy = {
            "@id": "offer-full-rules",
            "@type": "Offer",
            "permission": [
                {
                    "action": "use",
                    "constraint": [
                        {"leftOperand": "Membership", "operator": "eq",
                         "rightOperand": "active"}
                    ]
                },
                {
                    "action": "use",
                    "constraint": [{
                        "and": [
                            {"leftOperand": "UsagePurpose", "operator": "isAnyOf",
                             "rightOperand": ["cx.core.legalRequirementForThirdparty:1"]},
                            {"leftOperand": "FrameworkAgreement", "operator": "eq",
                             "rightOperand": "DataExchangeGovernance:1.0"},
                        ]
                    }]
                }
            ],
            "obligation": [
                {
                    "action": "use",
                    "constraint": [
                        {"leftOperand": "DataProvisioningEndDurationDays",
                         "operator": "eq", "rightOperand": "30"}
                    ]
                }
            ],
            "prohibition": [
                {
                    "action": "use",
                    "constraint": [
                        {"leftOperand": "AffiliatesRegion", "operator": "isAnyOf",
                         "rightOperand": ["cx.region.asia:1"]}
                    ]
                }
            ]
        }
        allowed = [{
            "permission": [
                {
                    "action": "use",
                    "constraint": {
                        "leftOperand": "Membership",
                        "operator": "eq",
                        "rightOperand": "active"
                    }
                },
                {
                    "action": "use",
                    "constraint": {
                        "and": [
                            {"leftOperand": "FrameworkAgreement", "operator": "eq",
                             "rightOperand": "DataExchangeGovernance:1.0"},
                            {"leftOperand": "UsagePurpose", "operator": "isAnyOf",
                             "rightOperand": "cx.core.legalRequirementForThirdparty:1"},
                        ]
                    }
                }
            ],
            "obligation": [
                {
                    "action": "use",
                    "constraint": {
                        "leftOperand": "DataProvisioningEndDurationDays",
                        "operator": "eq",
                        "rightOperand": "30"
                    }
                }
            ],
            "prohibition": [
                {
                    "action": "use",
                    "constraint": {
                        "leftOperand": "AffiliatesRegion",
                        "operator": "isAnyOf",
                        "rightOperand": "cx.region.asia:1"
                    }
                }
            ]
        }]
        assert DspTools.is_policy_valid(
            policy=catalog_policy, allowed_policies=allowed
        ) is True, "Policy with permission + obligation + prohibition must match"

    def test_policy_with_wrong_obligation_is_rejected(self):
        """
        When the obligation constraint value differs, the policy must be rejected.
        """
        catalog_policy = {
            "@id": "offer-wrong-obligation",
            "@type": "Offer",
            "permission": [{
                "action": "use",
                "constraint": [{"leftOperand": "Membership", "operator": "eq",
                                "rightOperand": "active"}]
            }],
            "obligation": [{
                "action": "use",
                "constraint": [{"leftOperand": "DataProvisioningEndDurationDays",
                                "operator": "eq", "rightOperand": "30"}]
            }]
        }
        allowed = [{
            "permission": {
                "action": "use",
                "constraint": {"leftOperand": "Membership", "operator": "eq",
                               "rightOperand": "active"}
            },
            "obligation": {
                "action": "use",
                "constraint": {"leftOperand": "DataProvisioningEndDurationDays",
                               "operator": "eq", "rightOperand": "90"}
            }
        }]
        assert DspTools.is_policy_valid(
            policy=catalog_policy, allowed_policies=allowed
        ) is False, "Obligation with rightOperand '30' must not match '90'"

    def test_policy_with_wrong_prohibition_is_rejected(self):
        """
        When the prohibition constraint value differs, the policy must be rejected.
        """
        catalog_policy = {
            "@id": "offer-wrong-prohibition",
            "@type": "Offer",
            "permission": [{
                "action": "use",
                "constraint": [{"leftOperand": "Membership", "operator": "eq",
                                "rightOperand": "active"}]
            }],
            "prohibition": [{
                "action": "use",
                "constraint": [{"leftOperand": "AffiliatesRegion",
                                "operator": "isAnyOf",
                                "rightOperand": ["cx.region.asia:1"]}]
            }]
        }
        allowed = [{
            "permission": {
                "action": "use",
                "constraint": {"leftOperand": "Membership", "operator": "eq",
                               "rightOperand": "active"}
            },
            "prohibition": {
                "action": "use",
                "constraint": {"leftOperand": "AffiliatesRegion",
                               "operator": "isAnyOf",
                               "rightOperand": "cx.region.europe:1"}
            }
        }]
        assert DspTools.is_policy_valid(
            policy=catalog_policy, allowed_policies=allowed
        ) is False, "Prohibition cx.region.asia:1 must not match cx.region.europe:1"

    def test_catalog_with_obligations_rejected_when_config_has_none(self):
        """
        A catalog policy that has obligations must NOT match an allowed config
        that omits them (empty list → key dropped → structural mismatch).
        """
        catalog_policy = {
            "@id": "offer-obligation-extra",
            "@type": "Offer",
            "permission": [{
                "action": "use",
                "constraint": [{"leftOperand": "Membership", "operator": "eq",
                                "rightOperand": "active"}]
            }],
            "obligation": [{
                "action": "use",
                "constraint": [{"leftOperand": "DataProvisioningEndDurationDays",
                                "operator": "eq", "rightOperand": "30"}]
            }]
        }
        allowed = [{
            "permission": {
                "action": "use",
                "constraint": {"leftOperand": "Membership", "operator": "eq",
                               "rightOperand": "active"}
            },
            "obligation": [],
        }]
        assert DspTools.is_policy_valid(
            policy=catalog_policy, allowed_policies=allowed
        ) is False, "Catalog with obligation must not match config without obligation"


class TestObligationAndProhibitionMatching:
    """
    Tests for obligation and prohibition matching in policy validation.

    Verifies that obligations and prohibitions get the same "any match"
    semantics as permissions: each allowed rule must be satisfied by
    at least one catalog rule, constraint order is irrelevant, and
    rightOperand arrays use subset semantics.
    """

    # ── Obligation tests ─────────────────────────────────────────────────

    def test_single_obligation_matches(self):
        """A single obligation with matching constraint must match."""
        catalog = {
            "@id": "offer-obl-1", "@type": "Offer",
            "permission": [{"action": "use",
                "constraint": [{"leftOperand": "Membership",
                                "operator": "eq", "rightOperand": "active"}]}],
            "obligation": [{"action": "use",
                "constraint": [{"leftOperand": "DataProvisioningEndDurationDays",
                                "operator": "eq", "rightOperand": "30"}]}],
        }
        allowed = [{"permission": {"action": "use",
                        "constraint": {"leftOperand": "Membership",
                                       "operator": "eq", "rightOperand": "active"}},
                    "obligation": {"action": "use",
                        "constraint": {"leftOperand": "DataProvisioningEndDurationDays",
                                       "operator": "eq", "rightOperand": "30"}}}]
        assert DspTools.is_policy_valid(policy=catalog, allowed_policies=allowed) is True

    def test_obligation_constraint_order_irrelevant(self):
        """Constraint order inside an obligation's ``and`` block must not matter."""
        catalog = {
            "@id": "offer-obl-order", "@type": "Offer",
            "permission": [{"action": "use",
                "constraint": [{"leftOperand": "Membership",
                                "operator": "eq", "rightOperand": "active"}]}],
            "obligation": [{"action": "use",
                "constraint": [{"and": [
                    {"leftOperand": "DataProvisioningEndDurationDays",
                     "operator": "eq", "rightOperand": "30"},
                    {"leftOperand": "DataRetentionPeriodDays",
                     "operator": "eq", "rightOperand": "365"},
                ]}]}],
        }
        # Allowed config has reversed constraint order
        allowed = [{"permission": {"action": "use",
                        "constraint": {"leftOperand": "Membership",
                                       "operator": "eq", "rightOperand": "active"}},
                    "obligation": {"action": "use",
                        "constraint": {"and": [
                            {"leftOperand": "DataRetentionPeriodDays",
                             "operator": "eq", "rightOperand": "365"},
                            {"leftOperand": "DataProvisioningEndDurationDays",
                             "operator": "eq", "rightOperand": "30"},
                        ]}}}]
        assert DspTools.is_policy_valid(policy=catalog, allowed_policies=allowed) is True

    def test_multiple_obligations_any_match(self):
        """
        When the catalog has multiple obligations, the allowed config only
        needs one of them to match each configured obligation.
        """
        catalog = {
            "@id": "offer-multi-obl", "@type": "Offer",
            "permission": [{"action": "use",
                "constraint": [{"leftOperand": "Membership",
                                "operator": "eq", "rightOperand": "active"}]}],
            "obligation": [
                {"action": "use",
                 "constraint": [{"leftOperand": "DataProvisioningEndDurationDays",
                                 "operator": "eq", "rightOperand": "30"}]},
                {"action": "use",
                 "constraint": [{"leftOperand": "DataRetentionPeriodDays",
                                 "operator": "eq", "rightOperand": "365"}]},
            ],
        }
        # Config only requires DataRetentionPeriodDays — should match the second
        allowed = [{"permission": {"action": "use",
                        "constraint": {"leftOperand": "Membership",
                                       "operator": "eq", "rightOperand": "active"}},
                    "obligation": {"action": "use",
                        "constraint": {"leftOperand": "DataRetentionPeriodDays",
                                       "operator": "eq", "rightOperand": "365"}}}]
        assert DspTools.is_policy_valid(policy=catalog, allowed_policies=allowed) is True

    def test_obligation_wrong_operator_rejected(self):
        """An obligation with a different operator must be rejected."""
        catalog = {
            "@id": "offer-obl-op", "@type": "Offer",
            "permission": [{"action": "use",
                "constraint": [{"leftOperand": "Membership",
                                "operator": "eq", "rightOperand": "active"}]}],
            "obligation": [{"action": "use",
                "constraint": [{"leftOperand": "DataProvisioningEndDurationDays",
                                "operator": "eq", "rightOperand": "30"}]}],
        }
        allowed = [{"permission": {"action": "use",
                        "constraint": {"leftOperand": "Membership",
                                       "operator": "eq", "rightOperand": "active"}},
                    "obligation": {"action": "use",
                        "constraint": {"leftOperand": "DataProvisioningEndDurationDays",
                                       "operator": "lteq", "rightOperand": "30"}}}]
        assert DspTools.is_policy_valid(
            policy=catalog, allowed_policies=allowed
        ) is False, "Obligation operator 'eq' must not match 'lteq'"

    def test_obligation_wrong_left_operand_rejected(self):
        """An obligation with a different leftOperand must be rejected."""
        catalog = {
            "@id": "offer-obl-left", "@type": "Offer",
            "permission": [{"action": "use",
                "constraint": [{"leftOperand": "Membership",
                                "operator": "eq", "rightOperand": "active"}]}],
            "obligation": [{"action": "use",
                "constraint": [{"leftOperand": "DataProvisioningEndDurationDays",
                                "operator": "eq", "rightOperand": "30"}]}],
        }
        allowed = [{"permission": {"action": "use",
                        "constraint": {"leftOperand": "Membership",
                                       "operator": "eq", "rightOperand": "active"}},
                    "obligation": {"action": "use",
                        "constraint": {"leftOperand": "SomeOtherObligation",
                                       "operator": "eq", "rightOperand": "30"}}}]
        assert DspTools.is_policy_valid(
            policy=catalog, allowed_policies=allowed
        ) is False, "Obligation leftOperand must match exactly"

    def test_config_with_obligation_rejected_when_catalog_has_none(self):
        """
        An allowed config that requires an obligation must NOT match a
        catalog policy that has no obligations.
        """
        catalog = {
            "@id": "offer-no-obl", "@type": "Offer",
            "permission": [{"action": "use",
                "constraint": [{"leftOperand": "Membership",
                                "operator": "eq", "rightOperand": "active"}]}],
        }
        allowed = [{"permission": {"action": "use",
                        "constraint": {"leftOperand": "Membership",
                                       "operator": "eq", "rightOperand": "active"}},
                    "obligation": {"action": "use",
                        "constraint": {"leftOperand": "DataProvisioningEndDurationDays",
                                       "operator": "eq", "rightOperand": "30"}}}]
        assert DspTools.is_policy_valid(
            policy=catalog, allowed_policies=allowed
        ) is False, "Config with obligation must not match catalog without obligation"

    # ── Prohibition tests ────────────────────────────────────────────────

    def test_single_prohibition_matches(self):
        """A single prohibition with matching constraint must match."""
        catalog = {
            "@id": "offer-proh-1", "@type": "Offer",
            "permission": [{"action": "use",
                "constraint": [{"leftOperand": "Membership",
                                "operator": "eq", "rightOperand": "active"}]}],
            "prohibition": [{"action": "use",
                "constraint": [{"leftOperand": "AffiliatesRegion",
                                "operator": "isAnyOf",
                                "rightOperand": ["cx.region.asia:1"]}]}],
        }
        allowed = [{"permission": {"action": "use",
                        "constraint": {"leftOperand": "Membership",
                                       "operator": "eq", "rightOperand": "active"}},
                    "prohibition": {"action": "use",
                        "constraint": {"leftOperand": "AffiliatesRegion",
                                       "operator": "isAnyOf",
                                       "rightOperand": "cx.region.asia:1"}}}]
        assert DspTools.is_policy_valid(policy=catalog, allowed_policies=allowed) is True

    def test_prohibition_constraint_order_irrelevant(self):
        """Constraint order inside a prohibition's ``and`` block must not matter."""
        catalog = {
            "@id": "offer-proh-order", "@type": "Offer",
            "permission": [{"action": "use",
                "constraint": [{"leftOperand": "Membership",
                                "operator": "eq", "rightOperand": "active"}]}],
            "prohibition": [{"action": "use",
                "constraint": [{"and": [
                    {"leftOperand": "AffiliatesRegion", "operator": "isAnyOf",
                     "rightOperand": ["cx.region.asia:1"]},
                    {"leftOperand": "DataUsePurpose", "operator": "eq",
                     "rightOperand": "marketing"},
                ]}]}],
        }
        allowed = [{"permission": {"action": "use",
                        "constraint": {"leftOperand": "Membership",
                                       "operator": "eq", "rightOperand": "active"}},
                    "prohibition": {"action": "use",
                        "constraint": {"and": [
                            {"leftOperand": "DataUsePurpose", "operator": "eq",
                             "rightOperand": "marketing"},
                            {"leftOperand": "AffiliatesRegion", "operator": "isAnyOf",
                             "rightOperand": "cx.region.asia:1"},
                        ]}}}]
        assert DspTools.is_policy_valid(policy=catalog, allowed_policies=allowed) is True

    def test_multiple_prohibitions_any_match(self):
        """
        When the catalog has multiple prohibitions, the allowed config's
        prohibition must match at least one of them.
        """
        catalog = {
            "@id": "offer-multi-proh", "@type": "Offer",
            "permission": [{"action": "use",
                "constraint": [{"leftOperand": "Membership",
                                "operator": "eq", "rightOperand": "active"}]}],
            "prohibition": [
                {"action": "use",
                 "constraint": [{"leftOperand": "AffiliatesRegion",
                                 "operator": "isAnyOf",
                                 "rightOperand": ["cx.region.asia:1"]}]},
                {"action": "use",
                 "constraint": [{"leftOperand": "DataUsePurpose",
                                 "operator": "eq",
                                 "rightOperand": "marketing"}]},
            ],
        }
        # Config only requires DataUsePurpose prohibition
        allowed = [{"permission": {"action": "use",
                        "constraint": {"leftOperand": "Membership",
                                       "operator": "eq", "rightOperand": "active"}},
                    "prohibition": {"action": "use",
                        "constraint": {"leftOperand": "DataUsePurpose",
                                       "operator": "eq",
                                       "rightOperand": "marketing"}}}]
        assert DspTools.is_policy_valid(policy=catalog, allowed_policies=allowed) is True

    def test_prohibition_wrong_right_operand_rejected(self):
        """A prohibition with a different rightOperand must be rejected."""
        catalog = {
            "@id": "offer-proh-right", "@type": "Offer",
            "permission": [{"action": "use",
                "constraint": [{"leftOperand": "Membership",
                                "operator": "eq", "rightOperand": "active"}]}],
            "prohibition": [{"action": "use",
                "constraint": [{"leftOperand": "AffiliatesRegion",
                                "operator": "isAnyOf",
                                "rightOperand": ["cx.region.asia:1"]}]}],
        }
        allowed = [{"permission": {"action": "use",
                        "constraint": {"leftOperand": "Membership",
                                       "operator": "eq", "rightOperand": "active"}},
                    "prohibition": {"action": "use",
                        "constraint": {"leftOperand": "AffiliatesRegion",
                                       "operator": "isAnyOf",
                                       "rightOperand": "cx.region.europe:1"}}}]
        assert DspTools.is_policy_valid(
            policy=catalog, allowed_policies=allowed
        ) is False, "Prohibition asia must not match europe"

    def test_prohibition_right_operand_subset_matching(self):
        """
        The allowed config asks for ``cx.region.asia:1``, the catalog
        prohibits ``["cx.region.asia:1", "cx.region.mena:1"]``.
        The allowed value is a subset → must match.
        """
        catalog = {
            "@id": "offer-proh-subset", "@type": "Offer",
            "permission": [{"action": "use",
                "constraint": [{"leftOperand": "Membership",
                                "operator": "eq", "rightOperand": "active"}]}],
            "prohibition": [{"action": "use",
                "constraint": [{"leftOperand": "AffiliatesRegion",
                                "operator": "isAnyOf",
                                "rightOperand": ["cx.region.asia:1",
                                                 "cx.region.mena:1"]}]}],
        }
        allowed = [{"permission": {"action": "use",
                        "constraint": {"leftOperand": "Membership",
                                       "operator": "eq", "rightOperand": "active"}},
                    "prohibition": {"action": "use",
                        "constraint": {"leftOperand": "AffiliatesRegion",
                                       "operator": "isAnyOf",
                                       "rightOperand": "cx.region.asia:1"}}}]
        assert DspTools.is_policy_valid(
            policy=catalog, allowed_policies=allowed
        ) is True, "Subset of prohibited regions must match"

    def test_config_with_prohibition_rejected_when_catalog_has_none(self):
        """
        An allowed config that requires a prohibition must NOT match a
        catalog policy that has no prohibitions.
        """
        catalog = {
            "@id": "offer-no-proh", "@type": "Offer",
            "permission": [{"action": "use",
                "constraint": [{"leftOperand": "Membership",
                                "operator": "eq", "rightOperand": "active"}]}],
        }
        allowed = [{"permission": {"action": "use",
                        "constraint": {"leftOperand": "Membership",
                                       "operator": "eq", "rightOperand": "active"}},
                    "prohibition": {"action": "use",
                        "constraint": {"leftOperand": "AffiliatesRegion",
                                       "operator": "isAnyOf",
                                       "rightOperand": "cx.region.asia:1"}}}]
        assert DspTools.is_policy_valid(
            policy=catalog, allowed_policies=allowed
        ) is False, "Config with prohibition must not match catalog without prohibition"

    def test_catalog_with_prohibition_rejected_when_config_has_none(self):
        """
        A catalog with prohibitions must NOT match a config that has no
        prohibitions (empty list → key dropped → structural mismatch).
        """
        catalog = {
            "@id": "offer-proh-vs-none", "@type": "Offer",
            "permission": [{"action": "use",
                "constraint": [{"leftOperand": "Membership",
                                "operator": "eq", "rightOperand": "active"}]}],
            "prohibition": [{"action": "use",
                "constraint": [{"leftOperand": "AffiliatesRegion",
                                "operator": "isAnyOf",
                                "rightOperand": ["cx.region.asia:1"]}]}],
        }
        allowed = [{"permission": {"action": "use",
                        "constraint": {"leftOperand": "Membership",
                                       "operator": "eq", "rightOperand": "active"}},
                    "prohibition": []}]
        assert DspTools.is_policy_valid(
            policy=catalog, allowed_policies=allowed
        ) is False, "Catalog with prohibition must not match config without prohibition"

    # ── Combined tests ───────────────────────────────────────────────────

    def test_full_policy_with_all_three_rules_end_to_end(self):
        """
        End-to-end filter_assets_and_policies with permission + obligation +
        prohibition, using the exact policy structure from the user's example.
        """
        catalog = {
            "@id": "catalog-full-rules",
            "@type": "Catalog",
            "dataset": [{
                "@id": "asset:full-rules:1",
                "@type": "Dataset",
                "hasPolicy": [{
                    "@id": "offer:full-rules:1",
                    "@type": "Offer",
                    "permission": [
                        {"action": "use",
                         "constraint": [{"leftOperand": "Membership",
                                         "operator": "eq",
                                         "rightOperand": "active"}]},
                        {"action": "use",
                         "constraint": [{"and": [
                             {"leftOperand": "UsagePurpose",
                              "operator": "isAnyOf",
                              "rightOperand": ["cx.core.legalRequirementForThirdparty:1"]},
                             {"leftOperand": "FrameworkAgreement",
                              "operator": "eq",
                              "rightOperand": "DataExchangeGovernance:1.0"},
                         ]}]},
                    ],
                    "obligation": [
                        {"action": "use",
                         "constraint": [{"leftOperand": "DataProvisioningEndDurationDays",
                                         "operator": "eq",
                                         "rightOperand": "30"}]},
                    ],
                    "prohibition": [
                        {"action": "use",
                         "constraint": [{"leftOperand": "AffiliatesRegion",
                                         "operator": "isAnyOf",
                                         "rightOperand": ["cx.region.asia:1"]}]},
                    ],
                }],
                "distribution": [{"@type": "Distribution", "format": "HttpData-PULL",
                    "accessService": {"@id": "svc-1", "@type": "DataService",
                        "endpointDescription": "dspace:connector",
                        "endpointURL": "https://example.com/api/v1/dsp/2025-1"}}],
            }],
            "service": [{"@id": "svc-1", "@type": "DataService",
                "endpointDescription": "dspace:connector",
                "endpointURL": "https://example.com/api/v1/dsp/2025-1"}],
            "participantId": "did:web:example.com:BPNL000000001234",
            "@context": ["https://w3id.org/dspace/2025/1/context.jsonld"],
        }
        allowed = [{
            "permission": [
                {"action": "use",
                 "constraint": {"leftOperand": "Membership",
                                "operator": "eq", "rightOperand": "active"}},
                {"action": "use",
                 "constraint": {"and": [
                     {"leftOperand": "FrameworkAgreement", "operator": "eq",
                      "rightOperand": "DataExchangeGovernance:1.0"},
                     {"leftOperand": "UsagePurpose", "operator": "isAnyOf",
                      "rightOperand": "cx.core.legalRequirementForThirdparty:1"},
                 ]}},
            ],
            "obligation": {"action": "use",
                "constraint": {"leftOperand": "DataProvisioningEndDurationDays",
                               "operator": "eq", "rightOperand": "30"}},
            "prohibition": {"action": "use",
                "constraint": {"leftOperand": "AffiliatesRegion",
                               "operator": "isAnyOf",
                               "rightOperand": "cx.region.asia:1"}},
        }]

        result = DspTools.filter_assets_and_policies(
            catalog=catalog, allowed_policies=allowed
        )
        assert len(result) == 1
        asset_id, policy = result[0]
        assert asset_id == "asset:full-rules:1"
        assert policy["@id"] == "offer:full-rules:1"

    def test_full_policy_rejected_when_prohibition_wrong(self):
        """
        Even when permission and obligation match, a wrong prohibition
        must cause the whole policy to be rejected.
        """
        catalog = {
            "@id": "offer-proh-mismatch", "@type": "Offer",
            "permission": [{"action": "use",
                "constraint": [{"leftOperand": "Membership",
                                "operator": "eq", "rightOperand": "active"}]}],
            "obligation": [{"action": "use",
                "constraint": [{"leftOperand": "DataProvisioningEndDurationDays",
                                "operator": "eq", "rightOperand": "30"}]}],
            "prohibition": [{"action": "use",
                "constraint": [{"leftOperand": "AffiliatesRegion",
                                "operator": "isAnyOf",
                                "rightOperand": ["cx.region.asia:1"]}]}],
        }
        allowed = [{
            "permission": {"action": "use",
                "constraint": {"leftOperand": "Membership",
                               "operator": "eq", "rightOperand": "active"}},
            "obligation": {"action": "use",
                "constraint": {"leftOperand": "DataProvisioningEndDurationDays",
                               "operator": "eq", "rightOperand": "30"}},
            "prohibition": {"action": "use",
                "constraint": {"leftOperand": "AffiliatesRegion",
                               "operator": "isAnyOf",
                               "rightOperand": "cx.region.europe:1"}},
        }]
        assert DspTools.is_policy_valid(
            policy=catalog, allowed_policies=allowed
        ) is False, "Wrong prohibition must reject even when permission+obligation match"

    def test_full_policy_rejected_when_obligation_wrong(self):
        """
        Even when permission and prohibition match, a wrong obligation
        must cause the whole policy to be rejected.
        """
        catalog = {
            "@id": "offer-obl-mismatch", "@type": "Offer",
            "permission": [{"action": "use",
                "constraint": [{"leftOperand": "Membership",
                                "operator": "eq", "rightOperand": "active"}]}],
            "obligation": [{"action": "use",
                "constraint": [{"leftOperand": "DataProvisioningEndDurationDays",
                                "operator": "eq", "rightOperand": "30"}]}],
            "prohibition": [{"action": "use",
                "constraint": [{"leftOperand": "AffiliatesRegion",
                                "operator": "isAnyOf",
                                "rightOperand": ["cx.region.asia:1"]}]}],
        }
        allowed = [{
            "permission": {"action": "use",
                "constraint": {"leftOperand": "Membership",
                               "operator": "eq", "rightOperand": "active"}},
            "obligation": {"action": "use",
                "constraint": {"leftOperand": "DataProvisioningEndDurationDays",
                               "operator": "eq", "rightOperand": "90"}},
            "prohibition": {"action": "use",
                "constraint": {"leftOperand": "AffiliatesRegion",
                               "operator": "isAnyOf",
                               "rightOperand": "cx.region.asia:1"}},
        }]
        assert DspTools.is_policy_valid(
            policy=catalog, allowed_policies=allowed
        ) is False, "Wrong obligation must reject even when permission+prohibition match"


class TestNormalizePolicyValue:
    """
    Unit tests for the ``_normalize_policy_value`` helper.
    """

    def test_strips_at_id_and_at_type(self):
        raw = {"@id": "123", "@type": "Offer", "permission": "use"}
        assert _normalize_policy_value(raw) == {"permission": "use"}

    def test_unwraps_single_element_list(self):
        raw = {"permission": [{"action": "use"}]}
        assert _normalize_policy_value(raw) == {"permission": {"action": "use"}}

    def test_drops_empty_lists(self):
        raw = {"permission": "use", "prohibition": [], "obligation": []}
        assert _normalize_policy_value(raw) == {"permission": "use"}

    def test_sorts_constraint_lists(self):
        raw = {
            "and": [
                {"leftOperand": "Z", "operator": "eq", "rightOperand": "1"},
                {"leftOperand": "A", "operator": "eq", "rightOperand": "2"},
            ]
        }
        normalized = _normalize_policy_value(raw)
        # "A" < "Z" lexicographically, so A-constraint should come first
        assert normalized["and"][0]["leftOperand"] == "A"
        assert normalized["and"][1]["leftOperand"] == "Z"

    def test_scalar_passthrough(self):
        assert _normalize_policy_value("hello") == "hello"
        assert _normalize_policy_value(42) == 42

    def test_nested_normalization(self):
        """Deep nesting should be handled recursively."""
        raw = {
            "@id": "drop-me",
            "permission": [{
                "action": "use",
                "constraint": [{
                    "and": [
                        {"leftOperand": "B", "operator": "eq", "rightOperand": "2"},
                        {"leftOperand": "A", "operator": "eq", "rightOperand": "1"},
                    ]
                }]
            }],
            "prohibition": [],
        }
        expected = {
            "permission": {
                "action": "use",
                "constraint": {
                    "and": [
                        {"leftOperand": "A", "operator": "eq", "rightOperand": "1"},
                        {"leftOperand": "B", "operator": "eq", "rightOperand": "2"},
                    ]
                }
            }
        }
        assert _normalize_policy_value(raw) == expected

    def test_value_reference_collapsed_to_string(self):
        """JSON-LD value references like ``{"@id": "odrl:use"}`` must collapse
        to the ``@id`` string value, not to ``{}``."""
        assert _normalize_policy_value({"@id": "odrl:use"}) == "odrl:use"
        assert _normalize_policy_value({"@id": "odrl:eq"}) == "odrl:eq"
        # With both @id and @type, still collapse to @id
        assert _normalize_policy_value({"@id": "cx:Membership", "@type": "Constraint"}) == "cx:Membership"

    def test_value_reference_not_collapsed_when_has_other_keys(self):
        """When a dict has @id plus meaningful keys, @id is stripped (not collapsed)."""
        raw = {"@id": "offer-1", "permission": "use"}
        assert _normalize_policy_value(raw) == {"permission": "use"}

    def test_jupiter_operator_normalization(self):
        """Jupiter-style operators with nested @id must be distinguishable."""
        eq = _normalize_policy_value({"odrl:operator": {"@id": "odrl:eq"}})
        neq = _normalize_policy_value({"odrl:operator": {"@id": "odrl:neq"}})
        assert eq != neq
        assert eq == {"odrl:operator": "odrl:eq"}
        assert neq == {"odrl:operator": "odrl:neq"}


class TestExplainPolicyDiff:
    """Tests for the ``_explain_policy_diff`` diagnostic function."""

    def test_identical_policies_no_diffs(self):
        a = {"permission": {"action": "use", "constraint": {"and": []}}}
        assert _explain_policy_diff(a, a) == []

    def test_different_action_value(self):
        catalog = {"permission": {"action": "use"}}
        allowed = {"permission": {"action": "transfer"}}
        diffs = _explain_policy_diff(catalog, allowed)
        assert len(diffs) >= 1
        joined = "\n".join(diffs)
        assert "use" in joined
        assert "transfer" in joined

    def test_missing_key_in_catalog(self):
        catalog = {"permission": {"action": "use"}}
        allowed = {"permission": {"action": "use", "constraint": "something"}}
        diffs = _explain_policy_diff(catalog, allowed)
        joined = "\n".join(diffs)
        assert "constraint" in joined
        assert "missing in catalog" in joined

    def test_extra_key_in_catalog(self):
        catalog = {"permission": {"action": "use", "extra": "value"}}
        allowed = {"permission": {"action": "use"}}
        diffs = _explain_policy_diff(catalog, allowed)
        joined = "\n".join(diffs)
        assert "extra" in joined
        assert "missing in allowed" in joined

    def test_list_length_difference(self):
        catalog = {"and": [
            {"leftOperand": "A", "operator": "eq", "rightOperand": "1"},
            {"leftOperand": "B", "operator": "eq", "rightOperand": "2"},
        ]}
        allowed = {"and": [
            {"leftOperand": "A", "operator": "eq", "rightOperand": "1"},
        ]}
        diffs = _explain_policy_diff(catalog, allowed)
        assert any("different number of constraints" in d for d in diffs)

    def test_constraint_diff_shows_triplet(self):
        """Constraint diffs must show the full leftOperand OPERATOR rightOperand triplet."""
        catalog = {"permission": {"constraint": {"and": [
            {"leftOperand": "Membership", "operator": "eq", "rightOperand": "active"},
        ]}}}
        allowed = {"permission": {"constraint": {"and": [
            {"leftOperand": "Membership", "operator": "eq", "rightOperand": "WRONG"},
        ]}}}
        diffs = _explain_policy_diff(catalog, allowed)
        joined = "\n".join(diffs)
        assert "constraint mismatch" in joined
        # Must show full triplet for catalog side
        assert "'Membership' 'eq' 'active'" in joined
        # Must show full triplet for allowed side
        assert "'Membership' 'eq' 'WRONG'" in joined
        # Must explain what specifically differs
        assert "rightOperand differs" in joined

    def test_constraint_diff_wrong_operator(self):
        """When the operator differs, it should be called out explicitly."""
        catalog = {"leftOperand": "Foo", "operator": "eq", "rightOperand": "bar"}
        allowed = {"leftOperand": "Foo", "operator": "neq", "rightOperand": "bar"}
        diffs = _explain_policy_diff(catalog, allowed)
        joined = "\n".join(diffs)
        assert "operator differs" in joined
        assert "'eq'" in joined
        assert "'neq'" in joined

    def test_constraint_diff_wrong_left_operand(self):
        """When leftOperand differs, it should be called out."""
        catalog = {"leftOperand": "Membership", "operator": "eq", "rightOperand": "active"}
        allowed = {"leftOperand": "Usage", "operator": "eq", "rightOperand": "active"}
        diffs = _explain_policy_diff(catalog, allowed)
        joined = "\n".join(diffs)
        assert "leftOperand differs" in joined
        assert "'Membership'" in joined
        assert "'Usage'" in joined

    def test_jupiter_constraint_diff(self):
        """Jupiter-style constraint diffs (after normalization) should also show triplets."""
        # After normalization, Jupiter {"@id": "odrl:eq"} becomes "odrl:eq"
        catalog = _normalize_policy_value({
            "odrl:leftOperand": {"@id": "cx-policy:Membership"},
            "odrl:operator": {"@id": "odrl:eq"},
            "odrl:rightOperand": "active",
        })
        allowed = _normalize_policy_value({
            "odrl:leftOperand": {"@id": "cx-policy:Membership"},
            "odrl:operator": {"@id": "odrl:eq"},
            "odrl:rightOperand": "WRONG",
        })
        diffs = _explain_policy_diff(catalog, allowed)
        joined = "\n".join(diffs)
        assert "constraint mismatch" in joined
        assert "rightOperand differs" in joined
        assert "'active'" in joined
        assert "'WRONG'" in joined


class TestPolicyStructureChecks:
    """Tests for structural validation of allowed policy configs."""

    def test_missing_permission(self):
        """Allowed policy without 'permission' should be flagged."""
        bad = {"action": "use"}  # permission key missing at top level
        issues = _check_policy_structure(bad, "Allowed policy")
        assert len(issues) >= 1
        joined = "\n".join(issues)
        assert "missing 'permission'" in joined

    def test_missing_constraint_inside_permission(self):
        """Permission without 'constraint' should be flagged."""
        bad = {"permission": {"action": "use"}}
        issues = _check_policy_structure(bad, "Allowed policy")
        assert len(issues) >= 1
        joined = "\n".join(issues)
        assert "missing 'constraint'" in joined

    def test_missing_action_inside_permission(self):
        """Permission without 'action' should be flagged."""
        bad = {"permission": {"constraint": {"and": []}}}
        issues = _check_policy_structure(bad, "Allowed policy")
        assert len(issues) >= 1
        joined = "\n".join(issues)
        assert "missing 'action'" in joined

    def test_well_formed_saturn_policy_no_issues(self):
        """A well-formed Saturn policy should produce no issues."""
        good = {"permission": {"action": "use", "constraint": {"and": [
            {"leftOperand": "Membership", "operator": "eq", "rightOperand": "active"},
        ]}}}
        assert _check_policy_structure(good, "Allowed policy") == []

    def test_well_formed_jupiter_policy_no_issues(self):
        """A well-formed Jupiter policy should produce no issues."""
        good = {"odrl:permission": {"odrl:action": {"@id": "odrl:use"}, "odrl:constraint": {"odrl:and": []}}}
        assert _check_policy_structure(_normalize_policy_value(good), "Allowed policy") == []

    def test_structure_issues_appear_in_is_policy_valid_logs(self, caplog):
        """Structural issues in allowed policy are surfaced in DEBUG logs."""
        policy = {
            "@id": "offer-1",
            "permission": {"action": "use", "constraint": {
                "leftOperand": "Membership", "operator": "eq", "rightOperand": "active"
            }}
        }
        # Allowed policy is malformed — missing 'permission' wrapper
        bad_allowed = [{"action": "use", "constraint": {
            "leftOperand": "Membership", "operator": "eq", "rightOperand": "active"
        }}]
        with caplog.at_level(logging.DEBUG, logger="tractusx_sdk.dataspace.tools.dsp_tools"):
            result = DspTools.is_policy_valid(policy=policy, allowed_policies=bad_allowed)
        assert result is False
        assert "config issue" in caplog.text
        assert "missing 'permission'" in caplog.text


class TestPolicyValidationLogging:
    """Verify that ``is_policy_valid`` emits detailed DEBUG logs on mismatch."""

    def test_logs_on_rejection_with_constraint_detail(self, caplog):
        """When a policy is rejected, DEBUG logs must show constraint triplet and reason."""
        catalog_policy = {
            "@id": "offer-123",
            "permission": {"action": "use", "constraint": {"and": [
                {"leftOperand": "Membership", "operator": "eq", "rightOperand": "active"},
            ]}}
        }
        allowed = [{
            "permission": {"action": "use", "constraint": {"and": [
                {"leftOperand": "Membership", "operator": "eq", "rightOperand": "WRONG"},
            ]}}
        }]
        with caplog.at_level(logging.DEBUG, logger="tractusx_sdk.dataspace.tools.dsp_tools"):
            result = DspTools.is_policy_valid(policy=catalog_policy, allowed_policies=allowed)
        assert result is False
        log_text = caplog.text
        # Must mention the policy ID
        assert "offer-123" in log_text
        # Must show the constraint triplet
        assert "'Membership' 'eq' 'active'" in log_text
        assert "'Membership' 'eq' 'WRONG'" in log_text
        # Must explain the specific difference
        assert "rightOperand differs" in log_text

    def test_logs_on_match(self, caplog):
        """On successful match, a brief success DEBUG message is emitted."""
        policy = {"permission": {"action": "use"}}
        allowed = [{"permission": {"action": "use"}}]
        with caplog.at_level(logging.DEBUG, logger="tractusx_sdk.dataspace.tools.dsp_tools"):
            result = DspTools.is_policy_valid(policy=policy, allowed_policies=allowed)
        assert result is True
        assert "matched" in caplog.text.lower()

    def test_logs_empty_allowed_list(self, caplog):
        """Empty allowed list should log a clear rejection reason."""
        policy = {"permission": {"action": "use"}}
        with caplog.at_level(logging.DEBUG, logger="tractusx_sdk.dataspace.tools.dsp_tools"):
            result = DspTools.is_policy_valid(policy=policy, allowed_policies=[])
        assert result is False
        assert "empty" in caplog.text.lower()

    def test_logs_multiple_allowed_policies_all_diffs(self, caplog):
        """When multiple allowed policies are checked, all diffs are logged."""
        catalog_policy = {
            "@id": "offer-multi",
            "permission": {"action": "use", "constraint": {"and": [
                {"leftOperand": "Membership", "operator": "eq", "rightOperand": "active"},
            ]}}
        }
        allowed = [
            {"permission": {"action": "transfer", "constraint": {"and": [
                {"leftOperand": "Membership", "operator": "eq", "rightOperand": "active"},
            ]}}},
            {"permission": {"action": "use", "constraint": {"and": [
                {"leftOperand": "Membership", "operator": "neq", "rightOperand": "active"},
            ]}}},
        ]
        with caplog.at_level(logging.DEBUG, logger="tractusx_sdk.dataspace.tools.dsp_tools"):
            result = DspTools.is_policy_valid(policy=catalog_policy, allowed_policies=allowed)
        assert result is False
        log_text = caplog.text
        # Should show diffs for both allowed policies
        assert "Allowed policy [0]" in log_text
        assert "Allowed policy [1]" in log_text
        # First should mention action mismatch
        assert "'use'" in log_text and "'transfer'" in log_text
        # Second should mention operator mismatch
        assert "operator differs" in log_text


class TestDspToolsCatalogEdgeCases:
    """Edge cases for catalog / dataset operations."""

    def test_is_catalog_empty_with_single_dataset(self):
        assert DspTools.is_catalog_empty(SATURN_CATALOG) is False

    def test_is_catalog_empty_no_dataset(self):
        assert DspTools.is_catalog_empty({}) is False

    def test_is_catalog_empty_empty_list(self):
        assert DspTools.is_catalog_empty({"dataset": []}) is True

    def test_filter_assets_empty_dataset_raises(self):
        with pytest.raises(Exception, match="empty"):
            DspTools.filter_assets_and_policies(
                catalog={"dataset": []},
                allowed_policies=ALLOWED_POLICIES
            )

    def test_filter_assets_single_dataset_dict(self):
        """When dataset is a single dict (not a list), it should still work."""
        single_dataset_catalog = copy.deepcopy(SATURN_CATALOG)
        single_dataset_catalog["dataset"] = single_dataset_catalog["dataset"][0]
        result = DspTools.filter_assets_and_policies(
            catalog=single_dataset_catalog,
            allowed_policies=ALLOWED_POLICIES
        )
        assert len(result) == 1
        assert result[0][0] == "ichub:asset:dtr:9foUM7pmSTrr5LZnx0NqiQ"

    # ── Empty / missing catalog tests (provider has not shared any asset) ─────

    def test_filter_assets_none_catalog_raises(self):
        """Passing None as the catalog must raise with an 'empty' message."""
        with pytest.raises(Exception, match="catalog is empty"):
            DspTools.filter_assets_and_policies(
                catalog=None,
                allowed_policies=ALLOWED_POLICIES,
            )

    def test_filter_assets_no_dataset_key_raises(self):
        """A catalog that contains no 'dataset' or 'dcat:dataset' key means the
        provider has not shared any asset – must raise with a clear message."""
        empty_catalog = {
            "@id": "some-catalog-id",
            "@type": "Catalog",
        }
        with pytest.raises(Exception, match="The provider did not share any matching asset"):
            DspTools.filter_assets_and_policies(
                catalog=empty_catalog,
                allowed_policies=ALLOWED_POLICIES,
            )

    def test_filter_assets_no_dataset_key_bare_dict_raises(self):
        """Completely empty dict catalog – no keys at all – must raise the
        'provider did not share' error, not a cryptic NoneType error."""
        with pytest.raises(Exception, match="The provider did not share any matching asset"):
            DspTools.filter_assets_and_policies(
                catalog={},
                allowed_policies=ALLOWED_POLICIES,
            )

    def test_filter_assets_legacy_empty_dataset_list_raises(self):
        """Legacy Jupiter-style catalog using 'dcat:dataset' key with an empty
        list must raise with a 'dataset list is empty' message."""
        empty_legacy_catalog = {
            "@id": "some-catalog-id",
            "@type": "dcat:Catalog",
            "dcat:dataset": [],
        }
        with pytest.raises(Exception, match="dataset list is empty"):
            DspTools.filter_assets_and_policies(
                catalog=empty_legacy_catalog,
                allowed_policies=ALLOWED_POLICIES,
            )

    def test_filter_assets_saturn_empty_dataset_list_raises(self):
        """Saturn-style catalog using 'dataset' key with an empty list must
        raise with a 'dataset list is empty' message."""
        empty_saturn_catalog = {
            "@id": "some-catalog-id",
            "@type": "Catalog",
            "dataset": [],
        }
        with pytest.raises(Exception, match="dataset list is empty"):
            DspTools.filter_assets_and_policies(
                catalog=empty_saturn_catalog,
                allowed_policies=ALLOWED_POLICIES,
            )

    def test_filter_assets_no_dataset_error_is_not_none_type(self):
        """Regression: missing 'dataset' key must NOT raise a NoneType / AttributeError.
        It must raise an Exception with a human-readable message."""
        catalog_without_dataset = {"@id": "abc", "@type": "Catalog", "someOtherKey": "value"}
        with pytest.raises(Exception) as exc_info:
            DspTools.filter_assets_and_policies(
                catalog=catalog_without_dataset,
                allowed_policies=ALLOWED_POLICIES,
            )
        # Ensure the error is not "NoneType" – it must be a descriptive message
        assert "NoneType" not in str(exc_info.value)
        assert "provider" in str(exc_info.value).lower() or "asset" in str(exc_info.value).lower()


# ═══════════════════════════════════════════════════════════════════════════════
# Jupiter (legacy / DSP HTTP 2024) fixtures & tests
# ═══════════════════════════════════════════════════════════════════════════════

JUPITER_CATALOG = {
    "@id": "b7e3c1a4-9f12-4567-8abc-def012345678",
    "@type": "dcat:Catalog",
    "dcat:dataset": [
        {
            "@id": "jupiter-asset:dtr:test-asset-001",
            "@type": "dcat:Dataset",
            "odrl:hasPolicy": [
                {
                    "@id": "offer-jupiter-001",
                    "@type": "odrl:Offer",
                    "odrl:permission": [
                        {
                            "odrl:action": {
                                "@id": "odrl:use"
                            },
                            "odrl:constraint": [
                                {
                                    "odrl:and": [
                                        {
                                            "odrl:leftOperand": {
                                                "@id": "cx-policy:FrameworkAgreement"
                                            },
                                            "odrl:operator": {
                                                "@id": "odrl:eq"
                                            },
                                            "odrl:rightOperand": "DataExchangeGovernance:1.0"
                                        },
                                        {
                                            "odrl:leftOperand": {
                                                "@id": "cx-policy:Membership"
                                            },
                                            "odrl:operator": {
                                                "@id": "odrl:eq"
                                            },
                                            "odrl:rightOperand": "active"
                                        },
                                        {
                                            "odrl:leftOperand": {
                                                "@id": "cx-policy:UsagePurpose"
                                            },
                                            "odrl:operator": {
                                                "@id": "odrl:eq"
                                            },
                                            "odrl:rightOperand": "cx.core.digitalTwinRegistry:1"
                                        }
                                    ]
                                }
                            ]
                        }
                    ],
                    "odrl:prohibition": [],
                    "odrl:obligation": []
                }
            ],
            "dct:type": {
                "@id": "https://w3id.org/catenax/taxonomy#DigitalTwinRegistry"
            },
            "https://w3id.org/catenax/ontology/common#version": "3.0",
            "id": "jupiter-asset:dtr:test-asset-001"
        }
    ],
    "dcat:service": [
        {
            "@id": "service-jupiter-001",
            "@type": "dcat:DataService",
            "dct:endpointUrl": "https://edc-provider.example.com/api/v1/dsp"
        }
    ],
    "participantId": "BPNL000000000T4X",
    "@context": {
        "@vocab": "https://w3id.org/edc/v0.0.1/ns/",
        "edc": "https://w3id.org/edc/v0.0.1/ns/",
        "tx": "https://w3id.org/tractusx/v0.0.1/ns/",
        "tx-auth": "https://w3id.org/tractusx/auth/",
        "cx-policy": "https://w3id.org/catenax/policy/",
        "odrl": "http://www.w3.org/ns/odrl/2/",
        "dcat": "http://www.w3.org/ns/dcat#",
        "dct": "http://purl.org/dc/terms/"
    }
}

# Jupiter allowed policies – same constraints in all 6 orderings, using
# prefixed ODRL keys (odrl:permission, odrl:leftOperand, etc.).
JUPITER_ALLOWED_POLICIES = [
    {
        "odrl:permission": {
            "odrl:action": {
                "@id": "odrl:use"
            },
            "odrl:constraint": {
                "odrl:and": [
                    {
                        "odrl:leftOperand": {"@id": "cx-policy:FrameworkAgreement"},
                        "odrl:operator": {"@id": "odrl:eq"},
                        "odrl:rightOperand": "DataExchangeGovernance:1.0"
                    },
                    {
                        "odrl:leftOperand": {"@id": "cx-policy:Membership"},
                        "odrl:operator": {"@id": "odrl:eq"},
                        "odrl:rightOperand": "active"
                    },
                    {
                        "odrl:leftOperand": {"@id": "cx-policy:UsagePurpose"},
                        "odrl:operator": {"@id": "odrl:eq"},
                        "odrl:rightOperand": "cx.core.digitalTwinRegistry:1"
                    }
                ]
            }
        },
        "odrl:prohibition": [],
        "odrl:obligation": []
    },
    {
        "odrl:permission": {
            "odrl:action": {
                "@id": "odrl:use"
            },
            "odrl:constraint": {
                "odrl:and": [
                    {
                        "odrl:leftOperand": {"@id": "cx-policy:FrameworkAgreement"},
                        "odrl:operator": {"@id": "odrl:eq"},
                        "odrl:rightOperand": "DataExchangeGovernance:1.0"
                    },
                    {
                        "odrl:leftOperand": {"@id": "cx-policy:UsagePurpose"},
                        "odrl:operator": {"@id": "odrl:eq"},
                        "odrl:rightOperand": "cx.core.digitalTwinRegistry:1"
                    },
                    {
                        "odrl:leftOperand": {"@id": "cx-policy:Membership"},
                        "odrl:operator": {"@id": "odrl:eq"},
                        "odrl:rightOperand": "active"
                    }
                ]
            }
        },
        "odrl:prohibition": [],
        "odrl:obligation": []
    },
    {
        "odrl:permission": {
            "odrl:action": {
                "@id": "odrl:use"
            },
            "odrl:constraint": {
                "odrl:and": [
                    {
                        "odrl:leftOperand": {"@id": "cx-policy:Membership"},
                        "odrl:operator": {"@id": "odrl:eq"},
                        "odrl:rightOperand": "active"
                    },
                    {
                        "odrl:leftOperand": {"@id": "cx-policy:FrameworkAgreement"},
                        "odrl:operator": {"@id": "odrl:eq"},
                        "odrl:rightOperand": "DataExchangeGovernance:1.0"
                    },
                    {
                        "odrl:leftOperand": {"@id": "cx-policy:UsagePurpose"},
                        "odrl:operator": {"@id": "odrl:eq"},
                        "odrl:rightOperand": "cx.core.digitalTwinRegistry:1"
                    }
                ]
            }
        },
        "odrl:prohibition": [],
        "odrl:obligation": []
    },
    {
        "odrl:permission": {
            "odrl:action": {
                "@id": "odrl:use"
            },
            "odrl:constraint": {
                "odrl:and": [
                    {
                        "odrl:leftOperand": {"@id": "cx-policy:Membership"},
                        "odrl:operator": {"@id": "odrl:eq"},
                        "odrl:rightOperand": "active"
                    },
                    {
                        "odrl:leftOperand": {"@id": "cx-policy:UsagePurpose"},
                        "odrl:operator": {"@id": "odrl:eq"},
                        "odrl:rightOperand": "cx.core.digitalTwinRegistry:1"
                    },
                    {
                        "odrl:leftOperand": {"@id": "cx-policy:FrameworkAgreement"},
                        "odrl:operator": {"@id": "odrl:eq"},
                        "odrl:rightOperand": "DataExchangeGovernance:1.0"
                    }
                ]
            }
        },
        "odrl:prohibition": [],
        "odrl:obligation": []
    },
    {
        "odrl:permission": {
            "odrl:action": {
                "@id": "odrl:use"
            },
            "odrl:constraint": {
                "odrl:and": [
                    {
                        "odrl:leftOperand": {"@id": "cx-policy:UsagePurpose"},
                        "odrl:operator": {"@id": "odrl:eq"},
                        "odrl:rightOperand": "cx.core.digitalTwinRegistry:1"
                    },
                    {
                        "odrl:leftOperand": {"@id": "cx-policy:FrameworkAgreement"},
                        "odrl:operator": {"@id": "odrl:eq"},
                        "odrl:rightOperand": "DataExchangeGovernance:1.0"
                    },
                    {
                        "odrl:leftOperand": {"@id": "cx-policy:Membership"},
                        "odrl:operator": {"@id": "odrl:eq"},
                        "odrl:rightOperand": "active"
                    }
                ]
            }
        },
        "odrl:prohibition": [],
        "odrl:obligation": []
    },
    {
        "odrl:permission": {
            "odrl:action": {
                "@id": "odrl:use"
            },
            "odrl:constraint": {
                "odrl:and": [
                    {
                        "odrl:leftOperand": {"@id": "cx-policy:UsagePurpose"},
                        "odrl:operator": {"@id": "odrl:eq"},
                        "odrl:rightOperand": "cx.core.digitalTwinRegistry:1"
                    },
                    {
                        "odrl:leftOperand": {"@id": "cx-policy:Membership"},
                        "odrl:operator": {"@id": "odrl:eq"},
                        "odrl:rightOperand": "active"
                    },
                    {
                        "odrl:leftOperand": {"@id": "cx-policy:FrameworkAgreement"},
                        "odrl:operator": {"@id": "odrl:eq"},
                        "odrl:rightOperand": "DataExchangeGovernance:1.0"
                    }
                ]
            }
        },
        "odrl:prohibition": [],
        "odrl:obligation": []
    }
]


# ── Jupiter tests ────────────────────────────────────────────────────────────

class TestDspToolsJupiterPolicyMatching:
    """
    Tests that DspTools policy matching works with Jupiter (legacy DSP)
    catalog responses using prefixed ODRL keys.
    """

    def test_filter_assets_jupiter_catalog_all_permutations(self):
        """
        Given a Jupiter catalog with prefixed ODRL keys
        (odrl:hasPolicy, odrl:permission, etc.), assert that all six
        constraint orderings in the allowed list match the catalog offer.
        """
        result = DspTools.filter_assets_and_policies(
            catalog=JUPITER_CATALOG,
            allowed_policies=JUPITER_ALLOWED_POLICIES
        )
        assert len(result) == 1
        asset_id, policy = result[0]
        assert asset_id == "jupiter-asset:dtr:test-asset-001"
        assert policy["@id"] == "offer-jupiter-001"

    def test_each_jupiter_permutation_matches_individually(self):
        """
        Each of the six Jupiter allowed policies must independently match
        the catalog offer.
        """
        catalog_policy = JUPITER_CATALOG["dcat:dataset"][0]["odrl:hasPolicy"][0]
        for i, allowed in enumerate(JUPITER_ALLOWED_POLICIES):
            assert DspTools.is_policy_valid(
                policy=catalog_policy,
                allowed_policies=[allowed]
            ), f"Jupiter allowed policy permutation {i} did not match"

    def test_jupiter_single_allowed_policy(self):
        """A single Jupiter allowed policy is sufficient to match."""
        result = DspTools.filter_assets_and_policies(
            catalog=JUPITER_CATALOG,
            allowed_policies=[JUPITER_ALLOWED_POLICIES[3]]
        )
        assert len(result) == 1
        assert result[0][0] == "jupiter-asset:dtr:test-asset-001"

    def test_jupiter_policy_none_accepts_everything(self):
        """allowed_policies=None must accept Jupiter policies too."""
        catalog_policy = JUPITER_CATALOG["dcat:dataset"][0]["odrl:hasPolicy"][0]
        assert DspTools.is_policy_valid(policy=catalog_policy, allowed_policies=None) is True

    def test_jupiter_policy_empty_list_rejects(self):
        """allowed_policies=[] must reject Jupiter policies."""
        catalog_policy = JUPITER_CATALOG["dcat:dataset"][0]["odrl:hasPolicy"][0]
        assert DspTools.is_policy_valid(policy=catalog_policy, allowed_policies=[]) is False

    def test_jupiter_non_matching_policy_rejected(self):
        """A Jupiter policy with different constraint values must NOT match."""
        non_matching = [{
            "odrl:permission": {
                "odrl:action": {"@id": "odrl:use"},
                "odrl:constraint": {
                    "odrl:and": [
                        {
                            "odrl:leftOperand": {"@id": "cx-policy:FrameworkAgreement"},
                            "odrl:operator": {"@id": "odrl:eq"},
                            "odrl:rightOperand": "SomeOtherFramework:9.9"
                        }
                    ]
                }
            },
            "odrl:prohibition": [],
            "odrl:obligation": []
        }]
        catalog_policy = JUPITER_CATALOG["dcat:dataset"][0]["odrl:hasPolicy"][0]
        assert DspTools.is_policy_valid(policy=catalog_policy, allowed_policies=non_matching) is False

    def test_jupiter_catalog_single_dataset_dict(self):
        """Jupiter catalog with dataset as a dict (not list) should work."""
        single = copy.deepcopy(JUPITER_CATALOG)
        single["dcat:dataset"] = single["dcat:dataset"][0]
        result = DspTools.filter_assets_and_policies(
            catalog=single,
            allowed_policies=JUPITER_ALLOWED_POLICIES
        )
        assert len(result) == 1
        assert result[0][0] == "jupiter-asset:dtr:test-asset-001"


# ── Cross-protocol rejection tests ──────────────────────────────────────────

class TestDspToolsCrossProtocolRejection:
    """
    Verifies that Saturn allowed policies do NOT match a Jupiter catalog
    and vice versa — the key formats are incompatible by design.
    """

    def test_saturn_policies_rejected_for_jupiter_catalog(self):
        """Saturn (unprefixed) allowed policies must NOT match a Jupiter (prefixed) catalog."""
        with pytest.raises(ValueError, match="No valid"):
            DspTools.filter_assets_and_policies(
                catalog=JUPITER_CATALOG,
                allowed_policies=ALLOWED_POLICIES  # Saturn-style
            )

    def test_jupiter_policies_rejected_for_saturn_catalog(self):
        """Jupiter (prefixed) allowed policies must NOT match a Saturn (unprefixed) catalog."""
        with pytest.raises(ValueError, match="No valid"):
            DspTools.filter_assets_and_policies(
                catalog=SATURN_CATALOG,
                allowed_policies=JUPITER_ALLOWED_POLICIES  # Jupiter-style
            )

    def test_single_saturn_policy_does_not_match_jupiter(self):
        """Direct is_policy_valid check: Saturn policy vs Jupiter catalog offer."""
        jupiter_offer = JUPITER_CATALOG["dcat:dataset"][0]["odrl:hasPolicy"][0]
        assert DspTools.is_policy_valid(
            policy=jupiter_offer,
            allowed_policies=[ALLOWED_POLICIES[0]]  # Saturn format
        ) is False

    def test_single_jupiter_policy_does_not_match_saturn(self):
        """Direct is_policy_valid check: Jupiter policy vs Saturn catalog offer."""
        saturn_offer = SATURN_CATALOG["dataset"][0]["hasPolicy"][0]
        assert DspTools.is_policy_valid(
            policy=saturn_offer,
            allowed_policies=[JUPITER_ALLOWED_POLICIES[0]]  # Jupiter format
        ) is False


# ═══════════════════════════════════════════════════════════════════════════════
# Wrong / mismatched policy configuration tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestSaturnWrongPolicyRejection:
    """
    Verifies that wrong Saturn policy configurations are correctly rejected
    when the catalog contains a different policy.
    """

    def _saturn_offer(self):
        return SATURN_CATALOG["dataset"][0]["hasPolicy"][0]

    # ── Wrong constraint values ──────────────────────────────────────────

    def test_wrong_framework_agreement_version(self):
        """Different FrameworkAgreement version must be rejected."""
        wrong = [{
            "permission": {
                "action": "use",
                "constraint": {
                    "and": [
                        {"leftOperand": "FrameworkAgreement", "operator": "eq",
                         "rightOperand": "DataExchangeGovernance:2.0"},  # wrong version
                        {"leftOperand": "Membership", "operator": "eq",
                         "rightOperand": "active"},
                        {"leftOperand": "UsagePurpose", "operator": "isAnyOf",
                         "rightOperand": "cx.core.digitalTwinRegistry:1"}
                    ]
                }
            }
        }]
        assert DspTools.is_policy_valid(policy=self._saturn_offer(), allowed_policies=wrong) is False

    def test_wrong_membership_value(self):
        """Different Membership value must be rejected."""
        wrong = [{
            "permission": {
                "action": "use",
                "constraint": {
                    "and": [
                        {"leftOperand": "FrameworkAgreement", "operator": "eq",
                         "rightOperand": "DataExchangeGovernance:1.0"},
                        {"leftOperand": "Membership", "operator": "eq",
                         "rightOperand": "inactive"},  # wrong
                        {"leftOperand": "UsagePurpose", "operator": "isAnyOf",
                         "rightOperand": "cx.core.digitalTwinRegistry:1"}
                    ]
                }
            }
        }]
        assert DspTools.is_policy_valid(policy=self._saturn_offer(), allowed_policies=wrong) is False

    def test_wrong_usage_purpose(self):
        """Different UsagePurpose must be rejected."""
        wrong = [{
            "permission": {
                "action": "use",
                "constraint": {
                    "and": [
                        {"leftOperand": "FrameworkAgreement", "operator": "eq",
                         "rightOperand": "DataExchangeGovernance:1.0"},
                        {"leftOperand": "Membership", "operator": "eq",
                         "rightOperand": "active"},
                        {"leftOperand": "UsagePurpose", "operator": "isAnyOf",
                         "rightOperand": "cx.core.someOtherPurpose:1"}  # wrong
                    ]
                }
            }
        }]
        assert DspTools.is_policy_valid(policy=self._saturn_offer(), allowed_policies=wrong) is False

    # ── Wrong operator ───────────────────────────────────────────────────

    def test_wrong_operator(self):
        """Using 'neq' instead of 'eq' must be rejected."""
        wrong = [{
            "permission": {
                "action": "use",
                "constraint": {
                    "and": [
                        {"leftOperand": "FrameworkAgreement", "operator": "neq",  # wrong
                         "rightOperand": "DataExchangeGovernance:1.0"},
                        {"leftOperand": "Membership", "operator": "eq",
                         "rightOperand": "active"},
                        {"leftOperand": "UsagePurpose", "operator": "isAnyOf",
                         "rightOperand": "cx.core.digitalTwinRegistry:1"}
                    ]
                }
            }
        }]
        assert DspTools.is_policy_valid(policy=self._saturn_offer(), allowed_policies=wrong) is False

    # ── Wrong action ─────────────────────────────────────────────────────

    def test_wrong_action(self):
        """Using 'transfer' instead of 'use' must be rejected."""
        wrong = [{
            "permission": {
                "action": "transfer",  # wrong
                "constraint": {
                    "and": [
                        {"leftOperand": "FrameworkAgreement", "operator": "eq",
                         "rightOperand": "DataExchangeGovernance:1.0"},
                        {"leftOperand": "Membership", "operator": "eq",
                         "rightOperand": "active"},
                        {"leftOperand": "UsagePurpose", "operator": "isAnyOf",
                         "rightOperand": "cx.core.digitalTwinRegistry:1"}
                    ]
                }
            }
        }]
        assert DspTools.is_policy_valid(policy=self._saturn_offer(), allowed_policies=wrong) is False

    # ── Missing constraint ───────────────────────────────────────────────

    def test_missing_one_constraint(self):
        """Only 2 of 3 constraints — must be rejected."""
        wrong = [{
            "permission": {
                "action": "use",
                "constraint": {
                    "and": [
                        {"leftOperand": "FrameworkAgreement", "operator": "eq",
                         "rightOperand": "DataExchangeGovernance:1.0"},
                        {"leftOperand": "Membership", "operator": "eq",
                         "rightOperand": "active"}
                        # UsagePurpose missing
                    ]
                }
            }
        }]
        assert DspTools.is_policy_valid(policy=self._saturn_offer(), allowed_policies=wrong) is False

    def test_missing_two_constraints(self):
        """Only 1 of 3 constraints — must be rejected."""
        wrong = [{
            "permission": {
                "action": "use",
                "constraint": {
                    "and": [
                        {"leftOperand": "Membership", "operator": "eq",
                         "rightOperand": "active"}
                    ]
                }
            }
        }]
        assert DspTools.is_policy_valid(policy=self._saturn_offer(), allowed_policies=wrong) is False

    # ── Extra constraint ─────────────────────────────────────────────────

    def test_extra_constraint(self):
        """4 constraints when catalog has 3 — must be rejected."""
        wrong = [{
            "permission": {
                "action": "use",
                "constraint": {
                    "and": [
                        {"leftOperand": "FrameworkAgreement", "operator": "eq",
                         "rightOperand": "DataExchangeGovernance:1.0"},
                        {"leftOperand": "Membership", "operator": "eq",
                         "rightOperand": "active"},
                        {"leftOperand": "UsagePurpose", "operator": "isAnyOf",
                         "rightOperand": "cx.core.digitalTwinRegistry:1"},
                        {"leftOperand": "ExtraConstraint", "operator": "eq",
                         "rightOperand": "surprise"}  # extra
                    ]
                }
            }
        }]
        assert DspTools.is_policy_valid(policy=self._saturn_offer(), allowed_policies=wrong) is False

    # ── Wrong leftOperand name ───────────────────────────────────────────

    def test_wrong_left_operand_name(self):
        """A typo in leftOperand must be rejected."""
        wrong = [{
            "permission": {
                "action": "use",
                "constraint": {
                    "and": [
                        {"leftOperand": "FrameworkAgreement", "operator": "eq",
                         "rightOperand": "DataExchangeGovernance:1.0"},
                        {"leftOperand": "MembershipStatus", "operator": "eq",  # wrong name
                         "rightOperand": "active"},
                        {"leftOperand": "UsagePurpose", "operator": "isAnyOf",
                         "rightOperand": "cx.core.digitalTwinRegistry:1"}
                    ]
                }
            }
        }]
        assert DspTools.is_policy_valid(policy=self._saturn_offer(), allowed_policies=wrong) is False

    # ── Completely different policy structure ─────────────────────────────

    def test_completely_different_policy(self):
        """A totally unrelated policy must be rejected."""
        wrong = [{
            "permission": {
                "action": "use",
                "constraint": {
                    "or": [  # 'or' instead of 'and'
                        {"leftOperand": "SomeField", "operator": "eq",
                         "rightOperand": "SomeValue"}
                    ]
                }
            }
        }]
        assert DspTools.is_policy_valid(policy=self._saturn_offer(), allowed_policies=wrong) is False

    def test_empty_permission(self):
        """An empty permission must be rejected."""
        wrong = [{"permission": {}}]
        assert DspTools.is_policy_valid(policy=self._saturn_offer(), allowed_policies=wrong) is False

    def test_empty_constraints(self):
        """Permission with no constraints must be rejected."""
        wrong = [{"permission": {"action": "use"}}]
        assert DspTools.is_policy_valid(policy=self._saturn_offer(), allowed_policies=wrong) is False

    # ── filter_assets_and_policies must raise for every wrong case ────────

    def test_filter_rejects_wrong_framework_version(self):
        """filter_assets_and_policies must raise ValueError when the only
        allowed policy has a wrong FrameworkAgreement version."""
        wrong = [{
            "permission": {
                "action": "use",
                "constraint": {
                    "and": [
                        {"leftOperand": "FrameworkAgreement", "operator": "eq",
                         "rightOperand": "DataExchangeGovernance:99.0"},
                        {"leftOperand": "Membership", "operator": "eq",
                         "rightOperand": "active"},
                        {"leftOperand": "UsagePurpose", "operator": "isAnyOf",
                         "rightOperand": "cx.core.digitalTwinRegistry:1"}
                    ]
                }
            }
        }]
        with pytest.raises(ValueError, match="No valid"):
            DspTools.filter_assets_and_policies(catalog=SATURN_CATALOG, allowed_policies=wrong)

    def test_filter_rejects_missing_constraint(self):
        """filter_assets_and_policies must raise when a constraint is missing."""
        wrong = [{
            "permission": {
                "action": "use",
                "constraint": {
                    "and": [
                        {"leftOperand": "FrameworkAgreement", "operator": "eq",
                         "rightOperand": "DataExchangeGovernance:1.0"},
                        {"leftOperand": "Membership", "operator": "eq",
                         "rightOperand": "active"}
                    ]
                }
            }
        }]
        with pytest.raises(ValueError, match="No valid"):
            DspTools.filter_assets_and_policies(catalog=SATURN_CATALOG, allowed_policies=wrong)

    def test_filter_rejects_extra_constraint(self):
        """filter_assets_and_policies must raise when an extra constraint is present."""
        wrong = [{
            "permission": {
                "action": "use",
                "constraint": {
                    "and": [
                        {"leftOperand": "FrameworkAgreement", "operator": "eq",
                         "rightOperand": "DataExchangeGovernance:1.0"},
                        {"leftOperand": "Membership", "operator": "eq",
                         "rightOperand": "active"},
                        {"leftOperand": "UsagePurpose", "operator": "isAnyOf",
                         "rightOperand": "cx.core.digitalTwinRegistry:1"},
                        {"leftOperand": "Bonus", "operator": "eq",
                         "rightOperand": "nope"}
                    ]
                }
            }
        }]
        with pytest.raises(ValueError, match="No valid"):
            DspTools.filter_assets_and_policies(catalog=SATURN_CATALOG, allowed_policies=wrong)


class TestJupiterWrongPolicyRejection:
    """
    Verifies that wrong Jupiter policy configurations are correctly rejected
    when the catalog contains a different policy.
    """

    def _jupiter_offer(self):
        return JUPITER_CATALOG["dcat:dataset"][0]["odrl:hasPolicy"][0]

    # ── Wrong constraint values ──────────────────────────────────────────

    def test_wrong_framework_agreement_version(self):
        """Different FrameworkAgreement version must be rejected."""
        wrong = [{
            "odrl:permission": {
                "odrl:action": {"@id": "odrl:use"},
                "odrl:constraint": {
                    "odrl:and": [
                        {"odrl:leftOperand": {"@id": "cx-policy:FrameworkAgreement"},
                         "odrl:operator": {"@id": "odrl:eq"},
                         "odrl:rightOperand": "DataExchangeGovernance:2.0"},  # wrong
                        {"odrl:leftOperand": {"@id": "cx-policy:Membership"},
                         "odrl:operator": {"@id": "odrl:eq"},
                         "odrl:rightOperand": "active"},
                        {"odrl:leftOperand": {"@id": "cx-policy:UsagePurpose"},
                         "odrl:operator": {"@id": "odrl:eq"},
                         "odrl:rightOperand": "cx.core.digitalTwinRegistry:1"}
                    ]
                }
            },
            "odrl:prohibition": [],
            "odrl:obligation": []
        }]
        assert DspTools.is_policy_valid(policy=self._jupiter_offer(), allowed_policies=wrong) is False

    def test_wrong_membership_value(self):
        """'suspended' instead of 'active' must be rejected."""
        wrong = [{
            "odrl:permission": {
                "odrl:action": {"@id": "odrl:use"},
                "odrl:constraint": {
                    "odrl:and": [
                        {"odrl:leftOperand": {"@id": "cx-policy:FrameworkAgreement"},
                         "odrl:operator": {"@id": "odrl:eq"},
                         "odrl:rightOperand": "DataExchangeGovernance:1.0"},
                        {"odrl:leftOperand": {"@id": "cx-policy:Membership"},
                         "odrl:operator": {"@id": "odrl:eq"},
                         "odrl:rightOperand": "suspended"},  # wrong
                        {"odrl:leftOperand": {"@id": "cx-policy:UsagePurpose"},
                         "odrl:operator": {"@id": "odrl:eq"},
                         "odrl:rightOperand": "cx.core.digitalTwinRegistry:1"}
                    ]
                }
            },
            "odrl:prohibition": [],
            "odrl:obligation": []
        }]
        assert DspTools.is_policy_valid(policy=self._jupiter_offer(), allowed_policies=wrong) is False

    # ── Wrong operator ───────────────────────────────────────────────────

    def test_wrong_operator(self):
        """Using 'odrl:neq' instead of 'odrl:eq' must be rejected."""
        wrong = [{
            "odrl:permission": {
                "odrl:action": {"@id": "odrl:use"},
                "odrl:constraint": {
                    "odrl:and": [
                        {"odrl:leftOperand": {"@id": "cx-policy:FrameworkAgreement"},
                         "odrl:operator": {"@id": "odrl:neq"},  # wrong
                         "odrl:rightOperand": "DataExchangeGovernance:1.0"},
                        {"odrl:leftOperand": {"@id": "cx-policy:Membership"},
                         "odrl:operator": {"@id": "odrl:eq"},
                         "odrl:rightOperand": "active"},
                        {"odrl:leftOperand": {"@id": "cx-policy:UsagePurpose"},
                         "odrl:operator": {"@id": "odrl:eq"},
                         "odrl:rightOperand": "cx.core.digitalTwinRegistry:1"}
                    ]
                }
            },
            "odrl:prohibition": [],
            "odrl:obligation": []
        }]
        assert DspTools.is_policy_valid(policy=self._jupiter_offer(), allowed_policies=wrong) is False

    # ── Wrong action ─────────────────────────────────────────────────────

    def test_wrong_action(self):
        """Using 'odrl:transfer' instead of 'odrl:use' must be rejected."""
        wrong = [{
            "odrl:permission": {
                "odrl:action": {"@id": "odrl:transfer"},  # wrong
                "odrl:constraint": {
                    "odrl:and": [
                        {"odrl:leftOperand": {"@id": "cx-policy:FrameworkAgreement"},
                         "odrl:operator": {"@id": "odrl:eq"},
                         "odrl:rightOperand": "DataExchangeGovernance:1.0"},
                        {"odrl:leftOperand": {"@id": "cx-policy:Membership"},
                         "odrl:operator": {"@id": "odrl:eq"},
                         "odrl:rightOperand": "active"},
                        {"odrl:leftOperand": {"@id": "cx-policy:UsagePurpose"},
                         "odrl:operator": {"@id": "odrl:eq"},
                         "odrl:rightOperand": "cx.core.digitalTwinRegistry:1"}
                    ]
                }
            },
            "odrl:prohibition": [],
            "odrl:obligation": []
        }]
        assert DspTools.is_policy_valid(policy=self._jupiter_offer(), allowed_policies=wrong) is False

    # ── Missing / extra constraints ──────────────────────────────────────

    def test_missing_constraint(self):
        """Only 2 of 3 constraints — must be rejected."""
        wrong = [{
            "odrl:permission": {
                "odrl:action": {"@id": "odrl:use"},
                "odrl:constraint": {
                    "odrl:and": [
                        {"odrl:leftOperand": {"@id": "cx-policy:FrameworkAgreement"},
                         "odrl:operator": {"@id": "odrl:eq"},
                         "odrl:rightOperand": "DataExchangeGovernance:1.0"},
                        {"odrl:leftOperand": {"@id": "cx-policy:Membership"},
                         "odrl:operator": {"@id": "odrl:eq"},
                         "odrl:rightOperand": "active"}
                        # UsagePurpose missing
                    ]
                }
            },
            "odrl:prohibition": [],
            "odrl:obligation": []
        }]
        assert DspTools.is_policy_valid(policy=self._jupiter_offer(), allowed_policies=wrong) is False

    def test_extra_constraint(self):
        """4 constraints when catalog has 3 — must be rejected."""
        wrong = [{
            "odrl:permission": {
                "odrl:action": {"@id": "odrl:use"},
                "odrl:constraint": {
                    "odrl:and": [
                        {"odrl:leftOperand": {"@id": "cx-policy:FrameworkAgreement"},
                         "odrl:operator": {"@id": "odrl:eq"},
                         "odrl:rightOperand": "DataExchangeGovernance:1.0"},
                        {"odrl:leftOperand": {"@id": "cx-policy:Membership"},
                         "odrl:operator": {"@id": "odrl:eq"},
                         "odrl:rightOperand": "active"},
                        {"odrl:leftOperand": {"@id": "cx-policy:UsagePurpose"},
                         "odrl:operator": {"@id": "odrl:eq"},
                         "odrl:rightOperand": "cx.core.digitalTwinRegistry:1"},
                        {"odrl:leftOperand": {"@id": "cx-policy:ExtraPolicy"},
                         "odrl:operator": {"@id": "odrl:eq"},
                         "odrl:rightOperand": "unexpected"}  # extra
                    ]
                }
            },
            "odrl:prohibition": [],
            "odrl:obligation": []
        }]
        assert DspTools.is_policy_valid(policy=self._jupiter_offer(), allowed_policies=wrong) is False

    # ── Wrong leftOperand ────────────────────────────────────────────────

    def test_wrong_left_operand(self):
        """Typo in leftOperand @id must be rejected."""
        wrong = [{
            "odrl:permission": {
                "odrl:action": {"@id": "odrl:use"},
                "odrl:constraint": {
                    "odrl:and": [
                        {"odrl:leftOperand": {"@id": "cx-policy:FrameworkAgreement"},
                         "odrl:operator": {"@id": "odrl:eq"},
                         "odrl:rightOperand": "DataExchangeGovernance:1.0"},
                        {"odrl:leftOperand": {"@id": "cx-policy:MembershipLevel"},  # wrong
                         "odrl:operator": {"@id": "odrl:eq"},
                         "odrl:rightOperand": "active"},
                        {"odrl:leftOperand": {"@id": "cx-policy:UsagePurpose"},
                         "odrl:operator": {"@id": "odrl:eq"},
                         "odrl:rightOperand": "cx.core.digitalTwinRegistry:1"}
                    ]
                }
            },
            "odrl:prohibition": [],
            "odrl:obligation": []
        }]
        assert DspTools.is_policy_valid(policy=self._jupiter_offer(), allowed_policies=wrong) is False

    # ── Completely different structure ────────────────────────────────────

    def test_or_instead_of_and(self):
        """Using 'odrl:or' instead of 'odrl:and' must be rejected."""
        wrong = [{
            "odrl:permission": {
                "odrl:action": {"@id": "odrl:use"},
                "odrl:constraint": {
                    "odrl:or": [  # wrong logical operator
                        {"odrl:leftOperand": {"@id": "cx-policy:FrameworkAgreement"},
                         "odrl:operator": {"@id": "odrl:eq"},
                         "odrl:rightOperand": "DataExchangeGovernance:1.0"},
                        {"odrl:leftOperand": {"@id": "cx-policy:Membership"},
                         "odrl:operator": {"@id": "odrl:eq"},
                         "odrl:rightOperand": "active"},
                        {"odrl:leftOperand": {"@id": "cx-policy:UsagePurpose"},
                         "odrl:operator": {"@id": "odrl:eq"},
                         "odrl:rightOperand": "cx.core.digitalTwinRegistry:1"}
                    ]
                }
            },
            "odrl:prohibition": [],
            "odrl:obligation": []
        }]
        assert DspTools.is_policy_valid(policy=self._jupiter_offer(), allowed_policies=wrong) is False

    def test_empty_permission(self):
        """Empty odrl:permission must be rejected."""
        wrong = [{"odrl:permission": {}, "odrl:prohibition": [], "odrl:obligation": []}]
        assert DspTools.is_policy_valid(policy=self._jupiter_offer(), allowed_policies=wrong) is False

    # ── filter_assets_and_policies end-to-end rejection ──────────────────

    def test_filter_rejects_wrong_jupiter_policy(self):
        """filter_assets_and_policies must raise ValueError for a wrong Jupiter policy."""
        wrong = [{
            "odrl:permission": {
                "odrl:action": {"@id": "odrl:use"},
                "odrl:constraint": {
                    "odrl:and": [
                        {"odrl:leftOperand": {"@id": "cx-policy:FrameworkAgreement"},
                         "odrl:operator": {"@id": "odrl:eq"},
                         "odrl:rightOperand": "WrongAgreement:1.0"}
                    ]
                }
            },
            "odrl:prohibition": [],
            "odrl:obligation": []
        }]
        with pytest.raises(ValueError, match="No valid"):
            DspTools.filter_assets_and_policies(catalog=JUPITER_CATALOG, allowed_policies=wrong)

    def test_filter_rejects_extra_jupiter_constraint(self):
        """filter_assets_and_policies must raise when Jupiter policy has an extra constraint."""
        wrong = [{
            "odrl:permission": {
                "odrl:action": {"@id": "odrl:use"},
                "odrl:constraint": {
                    "odrl:and": [
                        {"odrl:leftOperand": {"@id": "cx-policy:FrameworkAgreement"},
                         "odrl:operator": {"@id": "odrl:eq"},
                         "odrl:rightOperand": "DataExchangeGovernance:1.0"},
                        {"odrl:leftOperand": {"@id": "cx-policy:Membership"},
                         "odrl:operator": {"@id": "odrl:eq"},
                         "odrl:rightOperand": "active"},
                        {"odrl:leftOperand": {"@id": "cx-policy:UsagePurpose"},
                         "odrl:operator": {"@id": "odrl:eq"},
                         "odrl:rightOperand": "cx.core.digitalTwinRegistry:1"},
                        {"odrl:leftOperand": {"@id": "cx-policy:Sneaky"},
                         "odrl:operator": {"@id": "odrl:eq"},
                         "odrl:rightOperand": "extraValue"}
                    ]
                }
            },
            "odrl:prohibition": [],
            "odrl:obligation": []
        }]
        with pytest.raises(ValueError, match="No valid"):
            DspTools.filter_assets_and_policies(catalog=JUPITER_CATALOG, allowed_policies=wrong)
