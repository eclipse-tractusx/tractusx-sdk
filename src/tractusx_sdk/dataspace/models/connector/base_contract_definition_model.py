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

from ..model import BaseModel


class BaseContractDefinitionModel(BaseModel, ABC):
    """
    Base model class for representing a connector's contract definition.
    """

    oid: str
    access_policy_id: str
    contract_policy_id: str
    context: Optional[dict] = Field(default={
        "@vocab": "https://w3id.org/edc/v0.0.1/ns/"
    })
    assets_selector: Optional[list[dict]] = Field(default_factory=list)

    class _Builder(BaseModel._Builder):
        def id(self, oid: str):
            self._data["oid"] = oid
            return self

        def context(self, context: dict):
            self._data["context"] = context
            return self

        def access_policy_id(self, oid: str):
            self._data["access_policy_id"] = oid
            return self

        def contract_policy_id(self, oid: str):
            self._data["contract_policy_id"] = oid
            return self

        def assets_selector(self, assets_selector: list[dict]):
            self._data["assets_selector"] = assets_selector
            return self
