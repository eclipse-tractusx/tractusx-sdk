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
from unittest.mock import MagicMock, Mock

from pydantic import ValidationError

from src.tractusx_sdk.dataspace.models.connector.base_contract_negotiation_model import BaseContractNegotiationModel
from src.tractusx_sdk.dataspace.models.connector.base_policy_model import BasePolicyModel
from src.tractusx_sdk.dataspace.models.connector.model_factory import ModelFactory


class TestModelFactoryContractNegotiation(unittest.TestCase):
    def setUp(self):
        self.connector_version = "v0_9_0"
        self.context = {"key": "value"}
        self.counter_party_address = "https://counterparty.com"
        self.asset_id = "asset-id"
        self.offer_id = "offer-id"
        self.provider_id = "provider-id"
        self.offer_policy_data = {"offer_policy_key": "offer_policy_value"}
        self.policy_data = {"policy_key": "policy_value"}
        self.callback_addresses = [{"callback-address": "https://callback-address.com"}]

    def test_get_contract_negotiation_model_with_no_offer(self):
        with self.assertRaises(ValidationError):
            ModelFactory.get_contract_negotiation_model(
                connector_version=self.connector_version,
                counter_party_address=self.counter_party_address,
                offer_id=self.offer_id,
                asset_id=self.asset_id,
                provider_id=self.provider_id,
            )

    def test_get_contract_negotiation_model_with_offer_policy_model_only(self):
        policy_model = Mock(BasePolicyModel)
        policy_model.to_data = MagicMock(return_value=self.policy_data)

        model = ModelFactory.get_contract_negotiation_model(
            connector_version=self.connector_version,
            counter_party_address=self.counter_party_address,
            offer_id=self.offer_id,
            asset_id=self.asset_id,
            provider_id=self.provider_id,
            offer_policy_model=policy_model
        )

        self.assertIsInstance(model, BaseContractNegotiationModel)
        self.assertEqual(self.counter_party_address, model.counter_party_address)
        self.assertEqual(self.offer_id, model.offer_id)
        self.assertEqual(self.asset_id, model.asset_id)
        self.assertEqual(self.provider_id, model.provider_id)
        self.assertEqual(self.policy_data, model.offer_policy)

    def test_get_contract_negotiation_model_with_offer_policy_data_only(self):
        model = ModelFactory.get_contract_negotiation_model(
            connector_version=self.connector_version,
            counter_party_address=self.counter_party_address,
            offer_id=self.offer_id,
            asset_id=self.asset_id,
            provider_id=self.provider_id,
            offer_policy=self.offer_policy_data
        )

        self.assertIsInstance(model, BaseContractNegotiationModel)
        self.assertEqual(self.counter_party_address, model.counter_party_address)
        self.assertEqual(self.offer_id, model.offer_id)
        self.assertEqual(self.asset_id, model.asset_id)
        self.assertEqual(self.provider_id, model.provider_id)
        self.assertEqual(self.offer_policy_data, model.offer_policy)

    def test_get_contract_negotiation_model_with_offer_policy_model_overwrite(self):
        policy_model = Mock(BasePolicyModel)
        policy_model.to_data = MagicMock(return_value=self.policy_data)

        model = ModelFactory.get_contract_negotiation_model(
            connector_version=self.connector_version,
            counter_party_address=self.counter_party_address,
            offer_id=self.offer_id,
            asset_id=self.asset_id,
            provider_id=self.provider_id,
            offer_policy_model=policy_model,
            offer_policy=self.offer_policy_data
        )

        self.assertNotEqual(self.offer_policy_data, model.offer_policy)

    def test_get_contract_negotiation_model_without_defaults(self):
        model = ModelFactory.get_contract_negotiation_model(
            connector_version=self.connector_version,
            counter_party_address=self.counter_party_address,
            offer_id=self.offer_id,
            asset_id=self.asset_id,
            provider_id=self.provider_id,
            offer_policy=self.offer_policy_data,
            context=self.context,
            callback_addresses=self.callback_addresses
        )

        self.assertIsInstance(model, BaseContractNegotiationModel)
        self.assertEqual(self.counter_party_address, model.counter_party_address)
        self.assertEqual(self.offer_id, model.offer_id)
        self.assertEqual(self.asset_id, model.asset_id)
        self.assertEqual(self.provider_id, model.provider_id)
        self.assertEqual(self.offer_policy_data, model.offer_policy)
        self.assertEqual(self.context, model.context)
        self.assertEqual(self.callback_addresses, model.callback_addresses)
