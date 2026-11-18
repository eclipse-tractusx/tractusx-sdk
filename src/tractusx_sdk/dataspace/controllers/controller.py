#################################################################################
# Eclipse Tractus-X - Software Development KIT
#
# Copyright (c) 2026 LKS Next
# Copyright (c) 2025,2026 Contributors to the Eclipse Foundation
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

from typing import Generic, Self, TypeVar

from ..adapters.adapter import Adapter

AdapterT = TypeVar("AdapterT", bound=Adapter)


class Controller:
    adapter: Adapter
    endpoint_url: str

    def __init__(self, adapter: Adapter) -> None:
        self.adapter = adapter

    @classmethod
    def builder(cls) -> "Controller._Builder[Adapter]":
        """
        This method is intended to return a builder for the controller inheriting this class.
        This means that such a controller should implement its own `_Builder` inner class.
        By default, the `Controller._Builder` class is used.

        :return: a builder for the controller inheriting this class
        """
        return cls._Builder(cls)

    class _Builder(Generic[AdapterT]):
        """
        Default _Builder class for the Controller.

        Generic over the adapter type, so that controllers inheriting this class can narrow
        the adapter their builder accepts without breaking the base builder contract.
        """

        def __init__(self, cls: "type[Controller]") -> None:
            self.cls = cls
            self._data: dict = {}

        def adapter(self, adapter: AdapterT) -> Self:
            self._data["adapter"] = adapter
            return self

        def data(self, data: dict) -> Self:
            """
            This method is intended to set all the data of the controller inheriting this class.

            It can be used to set all the data of the controller in a single call, without the need to declare
            each builder method separately. This is useful for cases where a controller may deviate from its base
            controller implementation, and the base controller builder methods are not sufficient to set all the necessary data.
            """

            self._data.update(data)
            return self

        def build(self) -> "Controller":
            """
            :return: an instance of the class inheriting the base controller
            """
            return self.cls(**self._data)
