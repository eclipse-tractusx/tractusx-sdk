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

from src.tractusx_sdk.dataspace.models.connector.base_transfer_process_model import BaseTransferProcessModel
from src.tractusx_sdk.dataspace.models.connector.model_factory import ModelFactory


class TestModelFactoryTransferProcess(unittest.TestCase):
    def setUp(self):
        self.connector_version = "v0_9_0"
        self.counter_party_address = "https://counterparty.com"
        self.transfer_type = "dataspace-protocol-http"
        self.contract_id = "contract-id"
        self.data_destination = {"key": "value"}
        self.private_properties = {"private_key": "private_value"}
        self.callback_addresses = [{"callback-address": "https://callback-address.com"}]
        self.context = {"key": "value"}

    def test_get_transfer_process_model_with_defaults(self):
        model = ModelFactory.get_transfer_process_model(
            connector_version=self.connector_version,
            counter_party_address=self.counter_party_address,
            transfer_type=self.transfer_type,
            contract_id=self.contract_id,
            data_destination=self.data_destination
        )

        self.assertIsInstance(model, BaseTransferProcessModel)
        self.assertEqual(self.counter_party_address, model.counter_party_address)
        self.assertEqual(self.transfer_type, model.transfer_type)
        self.assertEqual(self.contract_id, model.contract_id)
        self.assertEqual(self.data_destination, model.data_destination)
        self.assertEqual({}, model.private_properties)
        self.assertEqual([], model.callback_addresses)
        self.assertEqual({
            "@vocab": "https://w3id.org/edc/v0.0.1/ns/"
        }, model.context)

    def test_get_transfer_process_model_without_defaults(self):
        model = ModelFactory.get_transfer_process_model(
            connector_version=self.connector_version,
            counter_party_address=self.counter_party_address,
            transfer_type=self.transfer_type,
            contract_id=self.contract_id,
            data_destination=self.data_destination,
            private_properties=self.private_properties,
            callback_addresses=self.callback_addresses,
            context=self.context
        )

        self.assertIsInstance(model, BaseTransferProcessModel)
        self.assertEqual(self.counter_party_address, model.counter_party_address)
        self.assertEqual(self.transfer_type, model.transfer_type)
        self.assertEqual(self.contract_id, model.contract_id)
        self.assertEqual(self.data_destination, model.data_destination)
        self.assertEqual(self.private_properties, model.private_properties)
        self.assertEqual(self.callback_addresses, model.callback_addresses)
        self.assertEqual(self.context, model.context)
