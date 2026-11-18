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

from typing import Self

from abc import abstractmethod, ABC
from pydantic import BaseModel as PydanticBaseModel


class BaseModel(PydanticBaseModel, ABC):
    @abstractmethod
    def to_data(self) -> str:
        """
        This method is intended to convert the model inheriting this class to a JSON
        representing the data that will be sent to the connector when using a policy model.

        :return: a JSON representation of the model
        """

        ## Abstract placeholder: concrete models must override this method
        not_implemented: str = NotImplemented
        return not_implemented

    @classmethod
    def builder(cls) -> "BaseModel._Builder":
        """
        This method is intended to return a builder for the model inheriting this class.
        This means that such a model should implement its own `_Builder` inner class.
        By default, the `BaseModel._Builder` class is used.

        :return: a builder for the model inheriting this class
        """
        return cls._Builder(cls)

    class _Builder:
        """
        Default _Builder class for the BaseModel.
        """

        def __init__(self, cls: "type[BaseModel]") -> None:
            self.cls = cls
            self._data: dict = {}

        def data(self, data: dict) -> Self:
            """
            This method is intended to set all the data of the model inheriting this class.

            It can be used to set all the data of the model in a single call, without the need to declare
            each builder method separately. This is useful for cases where a model may deviate from its base
            model implementation, and the base model builder methods are not sufficient to set all the necessary data.
            """

            self._data.update(data)
            return self

        def build(self) -> "BaseModel":
            """
            :return: an instance of the class inheriting the base model
            """
            return self.cls(**self._data)