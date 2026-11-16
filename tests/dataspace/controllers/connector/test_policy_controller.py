#################################################################################
# Eclipse Tractus-X - Software Development KIT
#
# Copyright (c) 2026 Contributors to the Eclipse Foundation
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

import json
from unittest import TestCase
from unittest.mock import Mock, MagicMock

from tractusx_sdk.dataspace.adapters.adapter import Adapter
from tractusx_sdk.dataspace.controllers.connector import jupiter, saturn
from tractusx_sdk.dataspace.models.connector import jupiter as jupiter_models, saturn as saturn_models
from tractusx_sdk.dataspace.models.model import BaseModel


class TestPolicyControllerUpdate(TestCase):
    """
    The Management API updates a policy definition with PUT /v3/policydefinitions/{id},
    unlike assets and contract definitions, which are updated with PUT on the collection.
    """

    def setUp(self):
        self.model = Mock(BaseModel)
        self.model.to_data = MagicMock(return_value={})

    def _controller(self, controller_cls):
        controller = controller_cls(Adapter("https://example.com"))
        controller.adapter.request = MagicMock()
        return controller

    def _flavours(self):
        return (
            (saturn.PolicyController, saturn_models),
            (jupiter.PolicyController, jupiter_models),
        )

    def test_update_puts_to_policy_id_with_full_body(self):
        for controller_cls, models in self._flavours():
            with self.subTest(controller=controller_cls.__module__):
                controller = self._controller(controller_cls)
                policy = models.PolicyModel.builder().id("policy-1").permissions([{"action": "use"}]).build()

                controller.update(policy)

                call_args = controller.adapter.request.call_args
                self.assertEqual(call_args.args[0], "put")
                self.assertEqual(call_args.args[1], "/v3/policydefinitions/policy-1")
                body = json.loads(call_args.kwargs["data"])
                self.assertEqual(body["@id"], "policy-1")
                self.assertEqual(body["@type"], "PolicyDefinition")
                self.assertIn("@context", body)
                self.assertEqual(body["policy"]["permission"], [{"action": "use"}])

    def test_update_encodes_policy_id(self):
        for controller_cls, models in self._flavours():
            with self.subTest(controller=controller_cls.__module__):
                controller = self._controller(controller_cls)
                policy = models.PolicyModel.builder().id("a/b").build()

                controller.update(policy)

                self.assertEqual(controller.adapter.request.call_args.args[1], "/v3/policydefinitions/a%2Fb")

    def test_update_rejects_invalid_id(self):
        for controller_cls, models in self._flavours():
            for oid in ("", ".."):
                with self.subTest(controller=controller_cls.__module__, oid=oid):
                    controller = self._controller(controller_cls)
                    policy = models.PolicyModel.builder().id(oid).build()

                    with self.assertRaises(ValueError):
                        controller.update(policy)

                    controller.adapter.request.assert_not_called()

    def test_other_updates_still_put_to_collection(self):
        for controller_cls, url in (
            (saturn.AssetController, "/v3/assets"),
            (jupiter.AssetController, "/v3/assets"),
            (saturn.ContractDefinitionController, "/v3/contractdefinitions"),
            (jupiter.ContractDefinitionController, "/v3/contractdefinitions"),
        ):
            with self.subTest(controller=controller_cls.__module__):
                controller = self._controller(controller_cls)

                controller.update(self.model)

                controller.adapter.request.assert_called_with("put", url, data={})
