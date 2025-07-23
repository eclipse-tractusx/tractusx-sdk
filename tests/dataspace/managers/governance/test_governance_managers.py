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

import pytest
import tempfile
import shutil
from tractusx_sdk.dataspace.managers.governance import (
    MemoryGovernanceManager,
    FileSystemGovernanceManager
)


class TestGovernanceManagers:
    """Test governance managers functionality"""

    @pytest.fixture
    def sample_policies(self):
        """Sample policies for testing"""
        return [
            {
                "odrl:permission": {
                    "odrl:action": {
                        "@id": "odrl:use"
                    },
                    "odrl:constraint": {
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
                                "odrl:rightOperand": "cx.core.industrycore:1"
                            }
                        ]
                    }
                },
                "odrl:prohibition": [],
                "odrl:obligation": []
            }
        ]

    @pytest.fixture
    def sample_catalog(self):
        """Sample catalog for testing"""
        return {
            "@id": "4f1bcfb2-7959-4ab7-a091-781a8c76b153",
            "@type": "dcat:Catalog",
            "dcat:dataset": [
                {
                    "@id": "ichub:asset:dtr:9foUM7pmSTrr5LZnx0NqiQ",
                    "@type": "dcat:Dataset",
                    "odrl:hasPolicy": {
                        "@id": "policy-1",
                        "@type": "odrl:Offer",
                        "odrl:permission": {
                            "odrl:action": {
                                "@id": "odrl:use"
                            },
                            "odrl:constraint": {
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
                        },
                        "odrl:prohibition": [],
                        "odrl:obligation": []
                    }
                },
                {
                    "@id": "ichub:asset:invalid:xyz",
                    "@type": "dcat:Dataset",
                    "odrl:hasPolicy": {
                        "@id": "policy-2",
                        "@type": "odrl:Offer",
                        "odrl:permission": {
                            "odrl:action": {
                                "@id": "odrl:use"
                            },
                            "odrl:constraint": {
                                "odrl:and": [
                                    {
                                        "odrl:leftOperand": {
                                            "@id": "cx-policy:FrameworkAgreement"
                                        },
                                        "odrl:operator": {
                                            "@id": "odrl:eq"
                                        },
                                        "odrl:rightOperand": "SomeOtherAgreement:1.0"
                                    }
                                ]
                            }
                        },
                        "odrl:prohibition": [],
                        "odrl:obligation": []
                    }
                }
            ]
        }

    def test_in_memory_governance_manager(self, sample_policies, sample_catalog):
        """Test in-memory governance manager"""
        manager = MemoryGovernanceManager()
        
        # Test adding policies
        hashes = []
        for policy in sample_policies:
            policy_hash = manager.add_policy(policy)
            hashes.append(policy_hash)
            assert policy_hash is not None
            assert len(policy_hash) == 64  # SHA-256 hash length
        
        # Test policy count
        assert manager.get_policy_count() == 2
        
        # Test listing hashes
        listed_hashes = manager.list_policy_hashes()
        assert len(listed_hashes) == 2
        assert all(h in listed_hashes for h in hashes)
        
        # Test policy validation
        assert manager.is_policy_valid(sample_policies[0]) is True
        assert manager.is_policy_valid(sample_policies[1]) is True
        
        # Test invalid policy
        invalid_policy = {
            "odrl:permission": {
                "odrl:action": {"@id": "odrl:use"},
                "odrl:constraint": {
                    "odrl:leftOperand": {"@id": "invalid:constraint"},
                    "odrl:operator": {"@id": "odrl:eq"},
                    "odrl:rightOperand": "invalid"
                }
            },
            "odrl:prohibition": [],
            "odrl:obligation": []
        }
        assert manager.is_policy_valid(invalid_policy) is False
        
        # Test select valid policies
        mixed_policies = sample_policies + [invalid_policy]
        valid_policies = manager.select_valid_policies(mixed_policies)
        assert len(valid_policies) == 2
        
        # Test catalog validation
        valid_assets = manager.select_valid_assets_and_policies(sample_catalog)
        assert len(valid_assets) == 1
        assert valid_assets[0][0] == "ichub:asset:dtr:9foUM7pmSTrr5LZnx0NqiQ"
        
        # Test removing policy
        assert manager.remove_policy(hashes[0]) is True
        assert manager.get_policy_count() == 1
        assert manager.remove_policy("nonexistent") is False

    def test_filesystem_governance_manager(self, sample_policies):
        """Test filesystem governance manager"""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = FileSystemGovernanceManager(temp_dir)
            
            # Test adding policies
            hashes = []
            for policy in sample_policies:
                policy_hash = manager.add_policy(policy)
                hashes.append(policy_hash)
                assert policy_hash is not None
            
            # Test policy count
            assert manager.get_policy_count() == 2
            
            # Test policy validation
            assert manager.is_policy_valid(sample_policies[0]) is True
            assert manager.is_policy_valid(sample_policies[1]) is True
            
            # Test getting policy by hash
            retrieved_policy = manager.get_policy_by_hash(hashes[0])
            assert retrieved_policy is not None
            assert manager.is_policy_valid(retrieved_policy) is True
            
            # Test removing policy
            assert manager.remove_policy(hashes[0]) is True
            assert manager.get_policy_count() == 1
            assert manager.is_policy_valid(sample_policies[0]) is False

    def test_policy_normalization(self):
        """Test policy normalization"""
        manager = MemoryGovernanceManager()
        
        # Policy with metadata
        policy_with_metadata = {
            "@id": "policy-123",
            "@type": "odrl:Offer",
            "metadata": "should be removed",
            "odrl:permission": {
                "odrl:action": {"@id": "odrl:use"}
            },
            "odrl:prohibition": [],
            "odrl:obligation": []
        }
        
        # Policy without metadata
        policy_without_metadata = {
            "odrl:permission": {
                "odrl:action": {"@id": "odrl:use"}
            },
            "odrl:prohibition": [],
            "odrl:obligation": []
        }
        
        # Both should generate the same hash after normalization
        hash1 = manager.add_policy(policy_with_metadata)
        hash2 = manager.generate_policy_hash(policy_without_metadata)
        
        assert hash1 == hash2
        assert manager.is_policy_valid(policy_without_metadata) is True

    def test_governance_manager_interface(self):
        """Test that all managers implement the same interface"""
        managers = [
            MemoryGovernanceManager(),
            FileSystemGovernanceManager()
        ]
        
        sample_policy = {
            "odrl:permission": {
                "odrl:action": {"@id": "odrl:use"}
            },
            "odrl:prohibition": [],
            "odrl:obligation": []
        }
        
        for manager in managers:
            # Test interface methods exist and work
            policy_hash = manager.add_policy(sample_policy)
            assert isinstance(policy_hash, str)
            
            assert isinstance(manager.is_policy_valid(sample_policy), bool)
            assert isinstance(manager.get_policy_count(), int)
            assert isinstance(manager.list_policy_hashes(), list)
            assert isinstance(manager.select_valid_policies([sample_policy]), list)
            
            # Clean up for filesystem manager
            if hasattr(manager, 'clear_policies'):
                manager.clear_policies()
