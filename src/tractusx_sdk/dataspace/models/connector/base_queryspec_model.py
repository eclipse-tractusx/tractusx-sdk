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


class BaseQuerySpecModel(BaseModel, ABC):
    """
    Base model class for representing a connector's query spec.
    """

    context: Optional[dict] = Field(default={"@vocab": "https://w3id.org/edc/v0.0.1/ns/"})
    offset: Optional[int] = Field(default=0)
    limit: Optional[int] = Field(default=10)
    sort_order: Optional[str] = Field(default="DESC", pattern="^(ASC|DESC)$")
    sort_field: Optional[str] = Field(default="")
    filter_expression: Optional[list[dict]] = Field(default_factory=list)

    class _Builder(BaseModel._Builder):
        def context(self, context: dict):
            self._data["context"] = context
            return self

        def offset(self, offset: int):
            self._data["offset"] = offset
            return self

        def limit(self, limit: int):
            self._data["limit"] = limit
            return self

        def sort_order(self, sort_order: str):
            self._data["sort_order"] = sort_order
            return self

        def sort_field(self, sort_field: str):
            self._data["sort_field"] = sort_field
            return self

        def filter_expression(self, filter_expression: list[dict]):
            self._data["filter_expression"] = filter_expression
            return self
