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


class BaseTransferProcessModel(BaseModel, ABC):
    """
    Base model class for representing a connector's contract negotiation.
    """

    counter_party_address: str
    transfer_type: str
    contract_id: str
    data_destination: dict
    private_properties: Optional[dict] = Field(default_factory=dict)
    callback_addresses: Optional[list[dict]] = Field(default_factory=list)
    context: Optional[Union[dict, list, str]] = Field(default={
        "@vocab": "https://w3id.org/edc/v0.0.1/ns/"
    })

    class _Builder(BaseModel._Builder):
        def context(self, context: dict) -> Self:
            self._data["context"] = context
            return self

        def counter_party_address(self, counter_party_address: str) -> Self:
            self._data["counter_party_address"] = counter_party_address
            return self

        def transfer_type(self, transfer_type: str) -> Self:
            self._data["transfer_type"] = transfer_type
            return self

        def contract_id(self, contract_id: str) -> Self:
            self._data["contract_id"] = contract_id
            return self

        def data_destination(self, data_destination: dict) -> Self:
            self._data["data_destination"] = data_destination
            return self

        def private_properties(self, private_properties: dict) -> Self:
            self._data["private_properties"] = private_properties
            return self

        def callback_addresses(self, callback_addresses: list[dict]) -> Self:
            self._data["callback_addresses"] = callback_addresses
            return self
