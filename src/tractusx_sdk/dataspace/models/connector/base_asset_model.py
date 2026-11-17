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

from abc import ABC
from typing import Optional, Self, Union
from pydantic import Field

from ..model import BaseModel


class BaseAssetModel(BaseModel, ABC):
    """
    Base model class for representing a connector's Asset.
    """

    oid: str
    data_address: dict
    context: Optional[Union[dict, list, str]] = Field(default={
        "@vocab": "https://w3id.org/edc/v0.0.1/ns/"
    })
    properties: Optional[dict] = Field(default_factory=dict)
    private_properties: Optional[dict] = Field(default_factory=dict)

    class _Builder(BaseModel._Builder):
        def id(self, oid: str) -> Self:
            self._data["oid"] = oid
            return self

        def context(self, context: dict) -> Self:
            self._data["context"] = context
            return self

        def data_address(self, data_address: dict) -> Self:
            self._data["data_address"] = data_address
            return self

        def properties(self, properties: dict) -> Self:
            self._data["properties"] = properties
            return self

        def private_properties(self, private_properties: dict) -> Self:
            self._data["private_properties"] = private_properties
            return self
