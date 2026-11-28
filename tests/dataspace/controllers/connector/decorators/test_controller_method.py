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
from inspect import signature

from tractusx_sdk.dataspace.controllers.connector.utils.decorators import controller_method
from tractusx_sdk.dataspace.controllers.controller import Controller
from tests.dataspace.controllers.connector.utils import (
    generic_controller_setup,
    ENDPOINT_URL,
    SampleController,
    ControllerPropertiesMixin
)


class TestControllerMethodDecorator(TestCase, ControllerPropertiesMixin):
    def setUp(self):
        generic_controller_setup(self)

    def test_decorator_no_controller(self):
        # Instantiate a template-like class
        class EmptyClass:
            endpoint_url = ENDPOINT_URL

            @controller_method
            def func(self):
                return "Hello world!"

        empty_class = EmptyClass()
        with self.assertRaises(ValueError):
            empty_class.func()

    def test_decorator_no_endpoint(self):
        # Instantiate a template-like class inheriting Controller
        class EmptyClass(Controller):
            @controller_method
            def func(self):
                return "Hello world!"

        empty_class = EmptyClass(self.adapter)
        with self.assertRaises(ValueError):
            empty_class.func()

    def test_decorator(self):
        sample_controller = SampleController(self.adapter)

        ret_val = sample_controller.func()
        self.assertEqual("Hello world!", ret_val)

    def test_decorator_preserves_function_metadata_and_signature(self):
        class TypedController(Controller):
            endpoint_url = ENDPOINT_URL

            @controller_method
            def lookup(self, oid: str, *, include_state: bool = False) -> str:
                """Look up a resource."""
                return oid

        controller = TypedController(self.adapter)

        self.assertEqual(controller.lookup.__name__, "lookup")
        self.assertEqual(controller.lookup.__doc__, "Look up a resource.")
        self.assertEqual(
            str(signature(controller.lookup)),
            "(oid: str, *, include_state: bool = False) -> str",
        )
