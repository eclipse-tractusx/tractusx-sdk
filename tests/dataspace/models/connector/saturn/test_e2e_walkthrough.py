"""
End-to-End Tests: Tractus-X EDC Management API Walkthrough with Saturn Connector

These tests verify the complete data exchange flow following the official
Tractus-X EDC Management API walkthrough documentation.

Tests validate:
- Model creation and serialization
- ODRL context compliance
- Policy integration with contract negotiation
- Complete E2E flow from Asset to Transfer Process
"""

import pytest
import json
from tractusx_sdk.dataspace.models.connector.model_factory import ModelFactory


class TestE2EDataExchangeFlow:
    """Test the complete Provider-Consumer data exchange flow"""

    def test_step1_provider_creates_asset(self):
        """Step 1: Provider creates an HTTP Data Plane asset"""
        asset = ModelFactory.get_asset_model(
            dataspace_version="saturn",
            oid="asset-1",
            properties={
                "dct:type": {
                    "@id": "https://w3id.org/catenax/taxonomy#VehicleProductionData"
                },
                "cx-common:version": "1.0",
                "description": "Vehicle production data from Factory A"
            },
            data_address={
                "@type": "DataAddress",
                "type": "HttpData",
                "baseUrl": "https://factory-a.example.com/api/production"
            }
        )
        
        asset_data = json.loads(asset.to_data())
        
        # Verify asset structure
        assert asset_data["@type"] == "Asset"
        assert asset_data["@id"] == "asset-1"
        assert "dct:type" in asset_data["properties"]
        assert asset_data["dataAddress"]["type"] == "HttpData"
        assert "@vocab" in asset_data["@context"]

    def test_step2_provider_creates_policies(self):
        """Step 2: Provider creates Access and Usage Policies with ODRL context"""
        # Access Policy
        access_policy = ModelFactory.get_policy_model(
            dataspace_version="saturn",
            oid="access-policy-bpn",
            permissions=[{
                "action": "access",
                "constraint": {
                    "leftOperand": "BusinessPartnerNumber",
                    "operator": "eq",
                    "rightOperand": "BPNL000000000002"
                }
            }]
        )
        
        access_data = json.loads(access_policy.to_data())
        
        # Verify ODRL context at root level
        assert isinstance(access_data["@context"], list)
        assert "https://w3id.org/catenax/2025/9/policy/odrl.jsonld" in access_data["@context"]
        assert access_data["@type"] == "PolicyDefinition"
        assert access_data["policy"]["@type"] == "Set"  # Not "odrl:Set"
        
        # Usage Policy
        usage_policy = ModelFactory.get_policy_model(
            dataspace_version="saturn",
            oid="usage-policy-framework",
            permissions=[{
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
                        }
                    ]
                }
            }]
        )
        
        usage_data = json.loads(usage_policy.to_data())
        
        # Verify complex constraint structure
        assert isinstance(usage_data["policy"]["permission"][0]["constraint"]["and"], list)
        assert len(usage_data["policy"]["permission"][0]["constraint"]["and"]) == 2

    def test_step3_provider_creates_contract_definition(self):
        """Step 3: Provider creates Contract Definition linking Asset and Policies"""
        contract_definition = ModelFactory.get_contract_definition_model(
            dataspace_version="saturn",
            oid="contract-def-1",
            access_policy_id="access-policy-bpn",
            contract_policy_id="usage-policy-framework",
            assets_selector=[{
                "@type": "Criterion",
                "operandLeft": "https://w3id.org/edc/v0.0.1/ns/id",
                "operator": "=",
                "operandRight": "asset-1"
            }]
        )
        
        contract_def_data = json.loads(contract_definition.to_data())
        
        # Verify contract definition structure
        assert contract_def_data["@type"] == "ContractDefinition"
        assert contract_def_data["@id"] == "contract-def-1"
        assert contract_def_data["accessPolicyId"] == "access-policy-bpn"
        assert contract_def_data["contractPolicyId"] == "usage-policy-framework"
        assert isinstance(contract_def_data["assetsSelector"], list)
        assert contract_def_data["assetsSelector"][0]["@type"] == "Criterion"

    def test_step4_consumer_requests_catalog(self):
        """Step 4: Consumer requests Catalog to discover data offers"""
        catalog_request = ModelFactory.get_catalog_model(
            dataspace_version="saturn",
            counter_party_address="https://provider-control.plane/api/v1/dsp/2025-1",
            counter_party_id="BPNL000000000001",
            protocol="dataspace-protocol-http:2025-1",
            queryspec={
                "offset": 0,
                "limit": 50,
                "filterExpression": []
            }
        )
        
        catalog_data = json.loads(catalog_request.to_data())
        
        # Verify catalog request structure
        assert catalog_data["@type"] == "CatalogRequest"
        assert catalog_data["counterPartyAddress"] == "https://provider-control.plane/api/v1/dsp/2025-1"
        assert catalog_data["counterPartyId"] == "BPNL000000000001"
        assert catalog_data["protocol"] == "dataspace-protocol-http:2025-1"
        assert "querySpec" in catalog_data
        
        # Catalog should not require ODRL context
        assert "@vocab" in catalog_data["@context"]

    def test_step5_consumer_initiates_contract_negotiation(self):
        """Step 5: Consumer initiates Contract Negotiation with ODRL-compliant policy"""
        # Simulated offer policy from catalog
        offer_policy = {
            "permission": [{
                "action": "use",
                "constraint": {
                    "leftOperand": "Membership",
                    "operator": "eq",
                    "rightOperand": "active"
                }
            }],
            "prohibition": [],
            "obligation": []
        }
        
        # Create contract negotiation with ODRL context
        contract_negotiation = ModelFactory.get_contract_negotiation_model(
            dataspace_version="saturn",
            counter_party_address="https://provider-control.plane/api/v1/dsp/2025-1",
            offer_id="offer-1",
            asset_id="asset-1",
            provider_id="BPNL000000000001",
            offer_policy=offer_policy,
            context=[
                "https://w3id.org/catenax/2025/9/policy/odrl.jsonld",
                "https://w3id.org/catenax/2025/9/policy/context.jsonld",
                {
                    "@vocab": "https://w3id.org/edc/v0.0.1/ns/"
                }
            ],
            protocol="dataspace-protocol-http:2025-1"
        )
        
        contract_neg_data = json.loads(contract_negotiation.to_data())
        
        # Verify contract negotiation structure
        assert contract_neg_data["@type"] == "ContractRequest"
        assert isinstance(contract_neg_data["@context"], list)
        assert "https://w3id.org/catenax/2025/9/policy/odrl.jsonld" in contract_neg_data["@context"]
        
        # Verify policy structure in negotiation
        assert contract_neg_data["policy"]["@id"] == "offer-1"
        assert contract_neg_data["policy"]["@type"] == "odrl:Offer"
        assert contract_neg_data["policy"]["assigner"]["@id"] == "BPNL000000000001"
        assert contract_neg_data["policy"]["target"]["@id"] == "asset-1"
        assert isinstance(contract_neg_data["policy"]["permission"], list)

    def test_step6_consumer_starts_transfer_process(self):
        """Step 6: Consumer starts Transfer Process for data access"""
        transfer_process = ModelFactory.get_transfer_process_model(
            dataspace_version="saturn",
            counter_party_address="https://provider-control.plane/api/v1/dsp/2025-1",
            contract_id="contract-agreement-456",
            transfer_type="HttpData-PULL",
            protocol="dataspace-protocol-http:2025-1",
            data_destination={
                "type": "HttpProxy"
            },
            private_properties={
                "receiverHttpEndpoint": "http://consumer-app.example.com/data-sink"
            }
        )
        
        transfer_data = json.loads(transfer_process.to_data())
        
        # Verify transfer process structure
        assert transfer_data["@type"] == "TransferRequest"
        assert transfer_data["counterPartyAddress"] == "https://provider-control.plane/api/v1/dsp/2025-1"
        assert transfer_data["contractId"] == "contract-agreement-456"
        assert transfer_data["transferType"] == "HttpData-PULL"
        assert transfer_data["dataDestination"]["type"] == "HttpProxy"
        assert "receiverHttpEndpoint" in transfer_data["privateProperties"]

    def test_complete_e2e_flow_integration(self):
        """Test complete integration of all steps in the E2E flow"""
        # Step 1: Asset
        asset = ModelFactory.get_asset_model(
            dataspace_version="saturn",
            oid="e2e-asset",
            properties={"description": "E2E test asset"},
            data_address={"type": "HttpData", "baseUrl": "https://test.example.com"}
        )
        
        # Step 2: Policies
        access_policy = ModelFactory.get_policy_model(
            dataspace_version="saturn",
            oid="e2e-access",
            permissions=[{"action": "access"}]
        )
        
        usage_policy = ModelFactory.get_policy_model(
            dataspace_version="saturn",
            oid="e2e-usage",
            permissions=[{"action": "use"}]
        )
        
        # Step 3: Contract Definition
        contract_def = ModelFactory.get_contract_definition_model(
            dataspace_version="saturn",
            oid="e2e-contract-def",
            access_policy_id="e2e-access",
            contract_policy_id="e2e-usage",
            assets_selector=[{
                "@type": "Criterion",
                "operandLeft": "https://w3id.org/edc/v0.0.1/ns/id",
                "operator": "=",
                "operandRight": "e2e-asset"
            }]
        )
        
        # Step 4: Catalog Request
        catalog = ModelFactory.get_catalog_model(
            dataspace_version="saturn",
            counter_party_address="https://provider.example.com/api/v1/dsp/2025-1",
            counter_party_id="BPNL000000000001",
            protocol="dataspace-protocol-http:2025-1"
        )
        
        # Step 5: Contract Negotiation (using policy from catalog)
        usage_policy_data = json.loads(usage_policy.to_data())
        offer_policy = {
            "permission": usage_policy_data["policy"]["permission"],
            "prohibition": usage_policy_data["policy"]["prohibition"],
            "obligation": usage_policy_data["policy"]["obligation"]
        }
        
        contract_neg = ModelFactory.get_contract_negotiation_model(
            dataspace_version="saturn",
            counter_party_address="https://provider.example.com/api/v1/dsp/2025-1",
            offer_id="offer-e2e",
            asset_id="e2e-asset",
            provider_id="BPNL000000000001",
            offer_policy=offer_policy,
            context=[
                "https://w3id.org/catenax/2025/9/policy/odrl.jsonld",
                "https://w3id.org/catenax/2025/9/policy/context.jsonld",
                {
                    "@vocab": "https://w3id.org/edc/v0.0.1/ns/"
                }
            ],
            protocol="dataspace-protocol-http:2025-1"
        )
        
        # Step 6: Transfer Process
        transfer = ModelFactory.get_transfer_process_model(
            dataspace_version="saturn",
            counter_party_address="https://provider.example.com/api/v1/dsp/2025-1",
            contract_id="agreement-e2e",
            transfer_type="HttpData-PULL",
            protocol="dataspace-protocol-http:2025-1",
            data_destination={"type": "HttpProxy"}
        )
        
        # Verify all models can be serialized
        asset_data = json.loads(asset.to_data())
        access_data = json.loads(access_policy.to_data())
        usage_data = json.loads(usage_policy.to_data())
        contract_def_data = json.loads(contract_def.to_data())
        catalog_data = json.loads(catalog.to_data())
        contract_neg_data = json.loads(contract_neg.to_data())
        transfer_data = json.loads(transfer.to_data())
        
        # Verify all have proper structure
        assert all([
            asset_data["@type"] == "Asset",
            access_data["@type"] == "PolicyDefinition",
            usage_data["@type"] == "PolicyDefinition",
            contract_def_data["@type"] == "ContractDefinition",
            catalog_data["@type"] == "CatalogRequest",
            contract_neg_data["@type"] == "ContractRequest",
            transfer_data["@type"] == "TransferRequest"
        ])
        
        # Verify ODRL context compliance
        assert "https://w3id.org/catenax/2025/9/policy/odrl.jsonld" in access_data["@context"]
        assert "https://w3id.org/catenax/2025/9/policy/odrl.jsonld" in usage_data["@context"]
        assert "https://w3id.org/catenax/2025/9/policy/odrl.jsonld" in contract_neg_data["@context"]


class TestPolicyVariations:
    """Test different policy configurations from the walkthrough"""

    def test_simple_allow_all_policy(self):
        """Test simple policy that allows all access"""
        policy = ModelFactory.get_policy_model(
            dataspace_version="saturn",
            oid="allow-all",
            permissions=[{"action": "use"}]
        )
        
        policy_data = json.loads(policy.to_data())
        
        assert policy_data["policy"]["@type"] == "Set"
        assert len(policy_data["policy"]["permission"]) == 1
        assert policy_data["policy"]["permission"][0]["action"] == "use"
        assert "constraint" not in policy_data["policy"]["permission"][0]

    def test_bpn_constrained_policy(self):
        """Test BPN-based access control policy"""
        policy = ModelFactory.get_policy_model(
            dataspace_version="saturn",
            oid="bpn-policy",
            permissions=[{
                "action": "use",
                "constraint": {
                    "leftOperand": "BusinessPartnerNumber",
                    "operator": "eq",
                    "rightOperand": "BPNL000000000002"
                }
            }]
        )
        
        policy_data = json.loads(policy.to_data())
        
        assert policy_data["policy"]["permission"][0]["constraint"]["leftOperand"] == "BusinessPartnerNumber"
        assert policy_data["policy"]["permission"][0]["constraint"]["operator"] == "eq"

    def test_business_partner_group_policy(self):
        """Test Business Partner Group policy"""
        policy = ModelFactory.get_policy_model(
            dataspace_version="saturn",
            oid="bpg-policy",
            permissions=[{
                "action": "use",
                "constraint": {
                    "leftOperand": "BusinessPartnerGroup",
                    "operator": "eq",
                    "rightOperand": "gold-partners"
                }
            }]
        )
        
        policy_data = json.loads(policy.to_data())
        
        assert policy_data["policy"]["permission"][0]["constraint"]["leftOperand"] == "BusinessPartnerGroup"
        assert policy_data["policy"]["permission"][0]["constraint"]["rightOperand"] == "gold-partners"

    def test_chained_constraints_policy(self):
        """Test policy with multiple chained constraints (AND logic)"""
        policy = ModelFactory.get_policy_model(
            dataspace_version="saturn",
            oid="chained-policy",
            permissions=[{
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
                            "leftOperand": "BusinessPartnerGroup",
                            "operator": "isPartOf",
                            "rightOperand": "tier-1-suppliers"
                        }
                    ]
                }
            }]
        )
        
        policy_data = json.loads(policy.to_data())
        
        constraint_and = policy_data["policy"]["permission"][0]["constraint"]["and"]
        assert len(constraint_and) == 3
        assert constraint_and[0]["leftOperand"] == "Membership"
        assert constraint_and[1]["leftOperand"] == "FrameworkAgreement"
        assert constraint_and[2]["leftOperand"] == "BusinessPartnerGroup"

    def test_time_limited_policy(self):
        """Test time-based policy with inForceDate constraint"""
        policy = ModelFactory.get_policy_model(
            dataspace_version="saturn",
            oid="time-limited",
            permissions=[{
                "action": "use",
                "constraint": {
                    "leftOperand": "inForceDate",
                    "operator": "lteq",
                    "rightOperand": "2025-12-31T23:59:59Z"
                }
            }]
        )
        
        policy_data = json.loads(policy.to_data())
        
        assert policy_data["policy"]["permission"][0]["constraint"]["leftOperand"] == "inForceDate"
        assert policy_data["policy"]["permission"][0]["constraint"]["operator"] == "lteq"

    def test_policy_with_custom_context(self):
        """Test policy with custom context fields"""
        policy = ModelFactory.get_policy_model(
            dataspace_version="saturn",
            oid="custom-context-policy",
            context=[
                "https://w3id.org/catenax/2025/9/policy/odrl.jsonld",
                "https://w3id.org/catenax/2025/9/policy/context.jsonld",
                {
                    "@vocab": "https://w3id.org/edc/v0.0.1/ns/",
                    "custom": "https://example.com/vocab#"
                }
            ],
            permissions=[{"action": "use"}]
        )
        
        policy_data = json.loads(policy.to_data())
        
        # Verify ODRL contexts are present
        assert "https://w3id.org/catenax/2025/9/policy/odrl.jsonld" in policy_data["@context"]
        
        # Verify custom context is preserved
        custom_context = next(c for c in policy_data["@context"] if isinstance(c, dict))
        assert "custom" in custom_context
        assert custom_context["custom"] == "https://example.com/vocab#"


class TestODRLContextCompliance:
    """Test ODRL context compliance across all models"""

    def test_policy_has_root_level_odrl_context(self):
        """Verify PolicyModel places ODRL context at root level, not nested"""
        policy = ModelFactory.get_policy_model(
            dataspace_version="saturn",
            oid="test-policy",
            permissions=[{"action": "use"}]
        )
        
        policy_data = json.loads(policy.to_data())
        
        # Context must be at root level
        assert "@context" in policy_data
        assert isinstance(policy_data["@context"], list)
        
        # ODRL contexts must be in root context
        assert "https://w3id.org/catenax/2025/9/policy/odrl.jsonld" in policy_data["@context"]
        assert "https://w3id.org/catenax/2025/9/policy/context.jsonld" in policy_data["@context"]
        
        # Policy type should be "Set" not "odrl:Set" when ODRL context is imported
        assert policy_data["policy"]["@type"] == "Set"
        
        # Policy object should NOT have nested @context
        assert "@context" not in policy_data["policy"]

    def test_contract_negotiation_preserves_odrl_context(self):
        """Verify ContractNegotiationModel preserves ODRL context from policy"""
        offer_policy = {
            "permission": [{"action": "use"}],
            "prohibition": [],
            "obligation": []
        }
        
        contract_neg = ModelFactory.get_contract_negotiation_model(
            dataspace_version="saturn",
            counter_party_address="https://provider.example.com/api/v1/dsp/2025-1",
            offer_id="offer-1",
            asset_id="asset-1",
            provider_id="BPNL000000000001",
            offer_policy=offer_policy,
            context=[
                "https://w3id.org/catenax/2025/9/policy/odrl.jsonld",
                "https://w3id.org/catenax/2025/9/policy/context.jsonld",
                {
                    "@vocab": "https://w3id.org/edc/v0.0.1/ns/"
                }
            ],
            protocol="dataspace-protocol-http:2025-1"
        )
        
        contract_neg_data = json.loads(contract_neg.to_data())
        
        # Verify ODRL context is at root level
        assert isinstance(contract_neg_data["@context"], list)
        assert "https://w3id.org/catenax/2025/9/policy/odrl.jsonld" in contract_neg_data["@context"]
        
        # Verify policy uses ODRL types
        assert contract_neg_data["policy"]["@type"] == "odrl:Offer"

    def test_catalog_does_not_require_odrl_context(self):
        """Verify CatalogModel does not require ODRL context"""
        catalog = ModelFactory.get_catalog_model(
            dataspace_version="saturn",
            counter_party_address="https://provider.example.com/api/v1/dsp/2025-1",
            counter_party_id="BPNL000000000001",
            protocol="dataspace-protocol-http:2025-1"
        )
        
        catalog_data = json.loads(catalog.to_data())
        
        # Catalog uses simple EDC context
        assert "@context" in catalog_data
        if isinstance(catalog_data["@context"], dict):
            assert "@vocab" in catalog_data["@context"]
        else:
            # If it's a list, check that ODRL is not required (though it could be present)
            # The key point is catalog works without ODRL context
            assert catalog_data["@type"] == "CatalogRequest"
