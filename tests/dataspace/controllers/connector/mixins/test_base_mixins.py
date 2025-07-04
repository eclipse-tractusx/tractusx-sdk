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
from unittest.mock import Mock, MagicMock

from tractusx_sdk.dataspace.controllers.connector.utils.mixins import (
    CreateControllerMixin,
    GetControllerMixin,
    UpdateControllerMixin,
    DeleteControllerMixin,
    GetAllControllerMixin,
    GetStateControllerMixin,
    TerminateControllerMixin
)
from tractusx_sdk.dataspace.models.model import BaseModel
from ..utils import generic_controller_setup, ControllerPropertiesMixin, SampleController


class TestCreateControllerMixin(TestCase, ControllerPropertiesMixin):
    def setUp(self):
        generic_controller_setup(self)

        self.model = Mock(BaseModel)
        self.model.to_data = MagicMock(return_value={})

    def test_mixin_create(self):
        class CustomController(CreateControllerMixin, SampleController):
            pass

        mixin = CustomController(self.adapter)
        mixin.adapter.request = MagicMock()

        mixin.create(self.model)

        mixin.adapter.request.assert_called_with("post", self.endpoint_url, data={})


class TestGetControllerMixin(TestCase, ControllerPropertiesMixin):
    def setUp(self):
        generic_controller_setup(self)

    def test_mixin_get(self):
        class CustomController(GetControllerMixin, SampleController):
            pass

        mixin = CustomController(self.adapter)
        mixin.adapter.request = MagicMock()

        oid = "test-id"
        mixin.get_by_id(oid)
        mixin.adapter.request.assert_called_with("get", f"{self.endpoint_url}/{oid}")


class TestUpdateControllerMixin(TestCase, ControllerPropertiesMixin):
    def setUp(self) -> None:
        generic_controller_setup(self)

        self.model = Mock(BaseModel)
        self.model.to_data = MagicMock(return_value={})

    def test_mixin_update(self):
        class CustomController(UpdateControllerMixin, SampleController):
            pass

        mixin = CustomController(self.adapter)
        mixin.adapter.request = MagicMock()

        mixin.update(self.model)

        mixin.adapter.request.assert_called_with("put", self.endpoint_url, data={})


class TestDeleteControllerMixin(TestCase, ControllerPropertiesMixin):
    def setUp(self):
        generic_controller_setup(self)

    def test_mixin_delete(self):
        class CustomController(DeleteControllerMixin, SampleController):
            pass

        mixin = CustomController(self.adapter)
        mixin.adapter.request = MagicMock()

        oid = "test-id"
        mixin.delete(oid)
        mixin.adapter.request.assert_called_with("delete", f"{self.endpoint_url}/{oid}")


class TestGetAllControllerMixin(TestCase, ControllerPropertiesMixin):
    def setUp(self) -> None:
        generic_controller_setup(self)

    def test_mixin_get_all(self):
        class CustomController(GetAllControllerMixin, SampleController):
            pass

        mixin = CustomController(self.adapter)
        mixin.adapter.request = MagicMock()

        mixin.get_all()

        mixin.adapter.request.assert_called_with("post", f"{self.endpoint_url}/request")


class TestGetStateControllerMixin(TestCase, ControllerPropertiesMixin):
    def setUp(self) -> None:
        generic_controller_setup(self)

    def test_mixin_get_state(self):
        class CustomController(GetStateControllerMixin, SampleController):
            pass

        mixin = CustomController(self.adapter)
        mixin.adapter.request = MagicMock()

        oid = "test-id"
        mixin.get_state_by_id(oid)
        mixin.adapter.request.assert_called_with("get", f"{self.endpoint_url}/{oid}/state")


class TestTerminateControllerMixin(TestCase, ControllerPropertiesMixin):
    def setUp(self) -> None:
        generic_controller_setup(self)
        self.model = Mock(BaseModel)
        self.model.to_data = MagicMock(return_value={})

    def test_mixin_terminate(self):
        class CustomController(TerminateControllerMixin, SampleController):
            pass

        mixin = CustomController(self.adapter)
        mixin.adapter.request = MagicMock()

        oid = "test-id"
        mixin.terminate_by_id(oid, obj=self.model)
        mixin.adapter.request.assert_called_with("post", f"{self.endpoint_url}/{oid}/terminate", data={})
