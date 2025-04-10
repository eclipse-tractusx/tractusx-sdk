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

from abc import ABC
from typing import Optional
from pydantic import Field

from .base_queryspec_model import BaseQuerySpecModel
from ..model import BaseModel


class BaseCatalogModel(BaseModel, ABC):
    """
    Base model class for representing a connector's contract negotiation.
    """

    counter_party_address: str
    counter_party_id: str
    context: Optional[dict] = Field(default={
        "@vocab": "https://w3id.org/edc/v0.0.1/ns/"
    })
    additional_scopes: Optional[list[str]] = Field(default_factory=list)
    queryspec: Optional[dict] = Field(default_factory=dict)

    class _Builder(BaseModel._Builder):
        def context(self, context: dict):
            self._data["context"] = context
            return self

        def counter_party_address(self, counter_party_address: str):
            self._data["counter_party_address"] = counter_party_address
            return self

        def counter_party_id(self, counter_party_id: str):
            self._data["counter_party_id"] = counter_party_id
            return self

        def additional_scopes(self, additional_scopes: str):
            self._data["additional_scopes"] = additional_scopes
            return self

        def queryspec_from_queryspec_model(self, queryspec: BaseQuerySpecModel):
            queryspec_data = queryspec.to_data()
            return self.queryspec(queryspec_data)

        def queryspec(self, queryspec: dict):
            self._data["queryspec"] = queryspec
            return self
