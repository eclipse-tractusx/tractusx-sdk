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


class BaseContractAgreementRetirementModel(BaseModel, ABC):
    """
    Base model class for representing a connector's contract agreement retirement.
    """

    agreement_id: str
    reason: str
    context: Optional[Union[dict, list, str]] = Field(default={
        "tx": "https://w3id.org/tractusx/v0.0.1/ns/",
        "edc": "https://w3id.org/edc/v0.0.1/ns/"
    })

    class _Builder(BaseModel._Builder):
        def context(self, context: dict):
            self._data["context"] = context
            return self

        def agreement_id(self, agreement_id: str):
            self._data["agreement_id"] = agreement_id
            return self

        def reason(self, reason: str):
            self._data["reason"] = reason
            return self
