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
from typing import Optional, Union
from pydantic import Field

from ..model import BaseModel


class BaseCatalogDatasetRequestModel(BaseModel, ABC):
    """
    Base model class for representing a connector's catalog dataset request.
    """

    oid: str
    counter_party_address: str
    counter_party_id: str
    protocol: str = Field(default="dataspace-protocol-http")
    context: Optional[Union[dict, list, str]] = Field(default={
        "@vocab": "https://w3id.org/edc/v0.0.1/ns/"
    })

    class _Builder(BaseModel._Builder):
        def id(self, oid: str):
            self._data["oid"] = oid
            return self

        def context(self, context: dict):
            self._data["context"] = context
            return self

        def counter_party_address(self, counter_party_address: str):
            self._data["counter_party_address"] = counter_party_address
            return self

        def counter_party_id(self, counter_party_id: str):
            self._data["counter_party_id"] = counter_party_id
            return self

        def protocol(self, protocol: str):
            self._data["protocol"] = protocol
            return self